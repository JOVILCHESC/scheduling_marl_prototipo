// package tt_twin_scheduler.src;
package tt.twin_scheduler;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import jade.core.Profile;
import jade.core.ProfileImpl;
import jade.core.Runtime;
import jade.wrapper.AgentController;
import jade.wrapper.ContainerController;
import org.zeromq.SocketType;
import org.zeromq.ZContext;
import org.zeromq.ZMQ;

public class MainJADE {
    private static final int ZMQ_PORT = 5555;
    // Toggle this to switch between Mirroring (false) and CNP Negotiation (true)
    public static final boolean USE_CNP = false;
    private static java.util.Map<Integer, AgentController> machineAgents = new java.util.HashMap<>();

    private static ContainerController mainContainer;

    public static void main(String[] args) throws Exception {

        // Start ZeroMQ server in a separate thread
        new Thread(() -> startZmqServer(ZMQ_PORT)).start();

        Runtime rt = Runtime.instance();
        Profile p = new ProfileImpl();
        p.setParameter(Profile.GUI, "true");

        mainContainer = rt.createMainContainer(p);

        try {
            // Crear 6 agentes de máquina (IDs 0-5)
            for (int i = 0; i < 6; i++) {
                String agentClass = USE_CNP ? "tt.twin_scheduler.MachineAgentCNP" : "tt.twin_scheduler.MachineAgent";
                AgentController machine = mainContainer.createNewAgent(
                        "machine-" + i,
                        agentClass,
                        new Object[]{i}
                );
                machine.start();
                machineAgents.put(i, machine);
            }

            AgentController scheduler = mainContainer.createNewAgent(
                    "scheduler",
                    "tt.twin_scheduler.SchedulerAgent",
                    null
            );

            scheduler.start();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void startZmqServer(int port) {
        try (ZContext context = new ZContext()) {
            ZMQ.Socket socket = context.createSocket(SocketType.REP);
            socket.bind("tcp://*:" + port);
            System.out.println("JADE ZeroMQ Server listening on tcp://localhost:" + port);

            Gson gson = new Gson();

            while (!Thread.currentThread().isInterrupted()) {
                // Block until a message is received
                byte[] reply = socket.recv(0);
                String requestStr = new String(reply, ZMQ.CHARSET);
                // System.out.println("[ZMQ] Received: " + requestStr); // Verbose off

                JsonObject req = gson.fromJson(requestStr, JsonObject.class);
                String type = req.has("type") ? req.get("type").getAsString() : "unknown";
                JsonObject resp = new JsonObject();

                if ("decide".equals(type)) {
                    handleDecide(req, resp);
                } else if ("feedback".equals(type)) {
                    handleFeedback(req, resp);
                } else if ("event".equals(type)) {
                    handleEvent(req, resp);
                } else {
                    resp.addProperty("error", "Unknown request type: " + type);
                }

                String responseStr = gson.toJson(resp);
                socket.send(responseStr.getBytes(ZMQ.CHARSET), 0);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void handleDecide(JsonObject req, JsonObject resp) {
        int machineId = req.has("machine_id") ? req.get("machine_id").getAsInt() : 0;
        int currentJob = req.has("current_job") ? req.get("current_job").getAsInt() : -1;
        java.util.List<Integer> queueJobIds = new java.util.ArrayList<>();
        java.util.List<Double> queueDurations = new java.util.ArrayList<>();
        if (req.has("queue") && req.get("queue").isJsonArray()) {
            JsonArray queue = req.getAsJsonArray("queue");
            for (JsonElement el : queue) {
                JsonObject job = el.getAsJsonObject();
                queueJobIds.add(job.has("job_id") ? job.get("job_id").getAsInt() : -1);
                queueDurations.add(job.has("next_op_duration") ? job.get("next_op_duration").getAsDouble() : 0.0);
            }
        }

        int selectedIdx = 0;
        if (!queueJobIds.isEmpty()) {
            selectedIdx = tt.twin_scheduler.SchedulerAgent.decideJob(machineId, currentJob, queueJobIds, queueDurations);
        }
        Integer selectedJob = !queueJobIds.isEmpty() ? queueJobIds.get(selectedIdx) : null;

        if (selectedJob != null) {
            resp.addProperty("selected_job", selectedJob);
        } else {
            resp.addProperty("allow", true);
        }
    }

    private static void handleFeedback(JsonObject req, JsonObject resp) {
        int machineId = req.has("machine_id") ? req.get("machine_id").getAsInt() : 0;
        int currentJob = req.has("current_job") ? req.get("current_job").getAsInt() : -1;
        java.util.List<Integer> queueJobIds = new java.util.ArrayList<>();
        java.util.List<Double> queueDurations = new java.util.ArrayList<>();
        if (req.has("queue") && req.get("queue").isJsonArray()) {
            JsonArray queue = req.getAsJsonArray("queue");
            for (JsonElement el : queue) {
                JsonObject job = el.getAsJsonObject();
                queueJobIds.add(job.has("job_id") ? job.get("job_id").getAsInt() : -1);
                queueDurations.add(job.has("next_op_duration") ? job.get("next_op_duration").getAsDouble() : 0.0);
            }
        }
        int action = req.has("action") ? req.get("action").getAsInt() : 0;
        double reward = req.has("reward") ? req.get("reward").getAsDouble() : 0.0;
        String nextState = req.has("next_state") ? req.get("next_state").getAsString() : null;
        java.util.List<Integer> nextActions = new java.util.ArrayList<>();
        if (req.has("next_actions") && req.get("next_actions").isJsonArray()) {
            JsonArray arr = req.getAsJsonArray("next_actions");
            for (JsonElement el : arr) nextActions.add(el.getAsInt());
        }
        tt.twin_scheduler.SchedulerAgent.feedback(machineId, currentJob, queueJobIds, queueDurations, action, reward, nextState, nextActions);

        resp.addProperty("ok", true);
    }

    private static void handleEvent(JsonObject req, JsonObject resp) {
        String eventType = req.has("event_type") ? req.get("event_type").getAsString() : "unknown";
        // System.out.println("[JADE MIRROR] Event Received: " + eventType + " | Payload: " + req.toString());
        
        try {
            if ("ORDER_ARRIVED".equals(eventType)) {
                int jobId = req.get("job_id").getAsInt();
                double dueDate = req.get("due_date").getAsDouble();
                String ops = req.get("operations").toString();
                
                String agentClass = USE_CNP ? "tt.twin_scheduler.OrderAgentCNP" : "tt.twin_scheduler.OrderAgent";
                AgentController ac = mainContainer.createNewAgent(
                        "order-" + jobId,
                        agentClass,
                        new Object[]{jobId, ops, dueDate}
                );
                ac.start();
            } else if ("JOB_COMPLETED".equals(eventType)) {
                int jobId = req.get("job_id").getAsInt();
                AgentController ac = mainContainer.getAgent("order-" + jobId);
                if (ac != null) {
                    ac.kill();
                }
            }
        } catch (Exception e) {
            // e.printStackTrace(); // Puede fallar si el agente ya no existe o nombre duplicado
        }

        // Despachar a agentes de máquina si corresponde
        if (req.has("machine_id")) {
            int mid = req.get("machine_id").getAsInt();
            AgentController ac = machineAgents.get(mid);
            if (ac != null) {
                try {
                    ac.putO2AObject(req.toString(), false);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }

        // Despachar a agentes de orden si corresponde (para mantener estado en Mirroring)
        if (req.has("job_id")) {
            int jid = req.get("job_id").getAsInt();
            try {
                // Intentar obtener el agente de orden. Nota: getAgent puede no funcionar si no se guardó referencia.
                // En JADE estándar ContainerController.getAgent devuelve un AgentController.
                AgentController acOrder = mainContainer.getAgent("order-" + jid);
                if (acOrder != null) {
                    acOrder.putO2AObject(req.toString(), false);
                }
            } catch (Exception e) {
                // Ignorar si el agente no existe o falla (ej. ya murió)
            }
        }
        
        resp.addProperty("status", "ok");
    }
}