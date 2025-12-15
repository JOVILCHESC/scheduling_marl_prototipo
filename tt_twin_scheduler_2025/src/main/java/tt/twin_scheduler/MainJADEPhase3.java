package tt.twin_scheduler;

import jade.core.Profile;
import jade.core.ProfileImpl;
import jade.core.Runtime;
import jade.wrapper.AgentContainer;
import jade.wrapper.AgentController;
import jade.wrapper.StaleProxyException;
import org.zeromq.ZMQ;
import org.zeromq.ZContext;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import java.util.*;

/**
 * Clase auxiliar para solicitudes de re-negociación vía O2A
 */
class RenegotiationRequest implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    
    public int operationIndex;
    public double currentTime;
    public List<Integer> availableMachines;
    
    public RenegotiationRequest(int opIndex, double time, List<Integer> machines) {
        this.operationIndex = opIndex;
        this.currentTime = time;
        this.availableMachines = machines;
    }
}

/**
 * MainJADEPhase3 - Punto de entrada para Fase 3 (Contract Net Protocol)
 * 
 * Inicializa:
 * - Plataforma JADE
 * - 6 MachineAgentCNP (con comportamiento CNP Responder)
 * - Servidor ZeroMQ para recibir solicitudes de SimPy
 * - Creación dinámica de OrderAgentCNP cuando llegan jobs
 * 
 * Protocolo de comunicación con SimPy:
 * - create_order_agent: Crea OrderAgentCNP dinámicamente
 * - cnp_negotiation: Ejecuta negociación CNP para asignar operación
 * - operation_start/complete: Actualiza estado de MachineAgents
 * - machine_failure/repair: Maneja fallas de máquinas
 */
public class MainJADEPhase3 {
    
    private static final int NUM_MACHINES = 6;
    private static final String ZMQ_PORT = "5555";
    
    private static AgentContainer container;
    private static Map<Integer, AgentController> machineAgents;
    private static Map<Integer, AgentController> orderAgents; // jobId -> OrderAgent
    private static Gson gson = new Gson();
    
    public static void main(String[] args) {
        System.out.println("========================================");
        System.out.println("JADE Phase 3 - Contract Net Protocol");
        System.out.println("========================================");
        
        // Inicializar estructuras
        machineAgents = new HashMap<>();
        orderAgents = new HashMap<>();
        
        try {
            // 1. Iniciar plataforma JADE
            Runtime rt = Runtime.instance();
            Profile profile = new ProfileImpl();
            profile.setParameter(Profile.MAIN_HOST, "localhost");
            profile.setParameter(Profile.MAIN_PORT, "1099");
            profile.setParameter(Profile.GUI, "false"); // Sin GUI por defecto
            
            container = rt.createMainContainer(profile);
            System.out.println("[JADE] Main Container creado");
            
            // 2. Crear MachineAgentCNP (6 máquinas)
            for (int i = 0; i < NUM_MACHINES; i++) {
                String agentName = "MachineAgent_" + i;
                AgentController ac = container.createNewAgent(
                    agentName,
                    "tt.twin_scheduler.MachineAgentCNP",
                    new Object[]{i}
                );
                ac.start();
                machineAgents.put(i, ac);
                System.out.println("[JADE] " + agentName + " iniciado (CNP Responder)");
            }
            
            // 3. Iniciar servidor ZeroMQ en hilo separado
            Thread zmqThread = new Thread(() -> {
                try {
                    runZeroMQServer();
                } catch (Exception e) {
                    System.err.println("[ZMQ ERROR] Exception in ZeroMQ server thread:");
                    e.printStackTrace();
                }
            });
            zmqThread.setDaemon(false);
            zmqThread.start();
            
            // Dar tiempo para que el servidor se inicie
            Thread.sleep(500);
            System.out.println("[ZMQ] Servidor debería estar escuchando en tcp://*:" + ZMQ_PORT);
            
            System.out.println("\n[JADE Phase 3] Sistema listo. Esperando jobs desde SimPy...\n");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * Servidor ZeroMQ que maneja solicitudes de SimPy
     */
    private static void runZeroMQServer() {
        System.out.println("[ZMQ DEBUG] runZeroMQServer() method started");
        try (ZContext context = new ZContext()) {
            System.out.println("[ZMQ DEBUG] ZContext created");
            ZMQ.Socket socket = context.createSocket(ZMQ.REP);
            System.out.println("[ZMQ DEBUG] Socket created");
            socket.bind("tcp://127.0.0.1:" + ZMQ_PORT);
            System.out.println("[ZMQ DEBUG] Socket bound successfully to tcp://127.0.0.1:" + ZMQ_PORT);
            System.out.println("JADE ZeroMQ Server listening on tcp://localhost:" + ZMQ_PORT);
            
            while (!Thread.currentThread().isInterrupted()) {
                System.out.println("[ZMQ DEBUG] About to call recvStr() - this will block until a message arrives");
                System.out.flush(); // Force output
                String request = socket.recvStr(0);
                System.out.println("[ZMQ DEBUG] recvStr() returned!");
                if (request == null) {
                    System.out.println("[ZMQ DEBUG] Received null request");
                    continue;
                }
                
                System.out.println("[ZMQ DEBUG] Request received: " + request);
                
                // Procesar solicitud
                String response = processRequest(request);
                System.out.println("[ZMQ DEBUG] Response sent: " + response);
                socket.send(response.getBytes(ZMQ.CHARSET), 0);
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * Procesa solicitudes JSON desde SimPy
     */
    private static String processRequest(String jsonRequest) {
        try {
            System.out.println("[ZMQ DEBUG] Parsing JSON: " + jsonRequest);
            JsonObject req = gson.fromJson(jsonRequest, JsonObject.class);
            
            if (req == null || !req.has("action")) {
                return createErrorResponse("Missing 'action' field in request");
            }
            
            String action = req.get("action").getAsString();
            System.out.println("[ZMQ] Solicitud recibida: " + action);
            
            switch (action) {
                case "create_order_agent":
                    return handleCreateOrderAgent(req);
                    
                case "cnp_negotiation":
                    return handleCNPNegotiation(req);
                    
                case "operation_start":
                    return handleOperationStart(req);
                    
                case "operation_complete":
                    return handleOperationComplete(req);
                    
                case "operation_failure":
                    return handleOperationFailure(req);
                    
                case "machine_failure":
                    return handleMachineFailure(req);
                    
                case "machine_repair":
                    return handleMachineRepair(req);
                    
                case "get_machine_status":
                    return handleGetMachineStatus(req);
                    
                default:
                    return createErrorResponse("Acción desconocida: " + action);
            }
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error procesando solicitud: " + e.getMessage());
        }
    }
    
    /**
     * Crea un OrderAgentCNP dinámicamente
     */
    private static String handleCreateOrderAgent(JsonObject req) {
        try {
            int jobId = req.get("job_id").getAsInt();
            JsonArray operationsJson = req.get("operations").getAsJsonArray();
            double dueDate = req.get("due_date").getAsDouble();
            double currentTime = req.get("current_time").getAsDouble();
            
            // Convertir operaciones a lista
            List<OrderAgentCNP.Operation> operations = new ArrayList<>();
            for (JsonElement opElem : operationsJson) {
                JsonObject op = opElem.getAsJsonObject();
                // Soportar ambos formatos: machine_id/machine_type, processing_time/duration
                int machineType = op.has("machine_id") ? op.get("machine_id").getAsInt() 
                                                       : op.get("machine_type").getAsInt();
                double duration = op.has("processing_time") ? op.get("processing_time").getAsDouble() 
                                                            : op.get("duration").getAsDouble();
                operations.add(new OrderAgentCNP.Operation(machineType, duration));
            }
            
            // Crear OrderAgentCNP
            String agentName = "OrderAgent_Job" + jobId;
            AgentController ac = container.createNewAgent(
                agentName,
                "tt.twin_scheduler.OrderAgentCNP",
                new Object[]{jobId, operations, dueDate, currentTime}
            );
            ac.start();
            orderAgents.put(jobId, ac);
            
            System.out.println("[JADE] OrderAgentCNP creado para Job " + jobId);
            
            return createSuccessResponse("agent_id", agentName);
            
        } catch (StaleProxyException e) {
            e.printStackTrace();
            return createErrorResponse("Error creando OrderAgent: " + e.getMessage());
        }
    }
    
    /**
     * Ejecuta negociación CNP
     */
    private static String handleCNPNegotiation(JsonObject req) {
        try {
            int jobId = req.get("job_id").getAsInt();
            int operationIndex = req.get("operation_index").getAsInt();
            double currentTime = req.get("current_time").getAsDouble();
            JsonArray availableMachinesJson = req.get("available_machines").getAsJsonArray();
            
            List<Integer> availableMachines = new ArrayList<>();
            for (JsonElement elem : availableMachinesJson) {
                availableMachines.add(elem.getAsInt());
            }
            
            // Obtener OrderAgent y ejecutar negociación
            AgentController orderAgentCtrl = orderAgents.get(jobId);
            if (orderAgentCtrl == null) {
                return createErrorResponse("OrderAgent no encontrado para Job " + jobId);
            }
            
            // En implementación real, invocar negotiateOperation() en OrderAgent
            // Por ahora, simular resultado (esto debería ser invocación real via O2A)
            
            System.out.println("[JADE] Negociación CNP para Job " + jobId + " op " + operationIndex);
            
            // Simulación: retornar primera máquina disponible
            // En implementación completa, esto sería resultado de ContractNetInitiator
            if (!availableMachines.isEmpty()) {
                int assignedMachine = availableMachines.get(0);
                double expectedStart = currentTime;
                double expectedEnd = currentTime + 10.0; // Placeholder
                
                JsonObject assignment = new JsonObject();
                assignment.addProperty("machine_id", assignedMachine);
                assignment.addProperty("expected_start", expectedStart);
                assignment.addProperty("expected_end", expectedEnd);
                
                return createSuccessResponse("assignment", assignment);
            } else {
                return createErrorResponse("No hay máquinas disponibles");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error en negociación CNP: " + e.getMessage());
        }
    }
    
    /**
     * Notifica inicio de operación
     */
    private static String handleOperationStart(JsonObject req) {
        try {
            int jobId = req.get("job_id").getAsInt();
            int operationIndex = req.get("operation_index").getAsInt();
            int machineId = req.get("machine_id").getAsInt();
            double startTime = req.get("start_time").getAsDouble();
            
            System.out.println("[JADE] Operación iniciada: Job " + jobId + " op " + operationIndex +
                             " en Machine " + machineId + " t=" + startTime);
            
            // Actualizar estado de MachineAgent (via O2A o invocación directa)
            // En implementación completa, usar O2A communication
            
            return createSuccessResponse(null, null);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error notificando inicio: " + e.getMessage());
        }
    }
    
    /**
     * Notifica finalización de operación
     */
    private static String handleOperationComplete(JsonObject req) {
        try {
            int jobId = req.get("job_id").getAsInt();
            int operationIndex = req.get("operation_index").getAsInt();
            int machineId = req.get("machine_id").getAsInt();
            double completionTime = req.get("completion_time").getAsDouble();
            
            // Verificar si es la última operación del job
            boolean isLastOperation = req.has("is_last_operation") ? 
                                     req.get("is_last_operation").getAsBoolean() : false;
            
            System.out.println("[JADE] Operación completada: Job " + jobId + " op " + operationIndex +
                             " en Machine " + machineId + " t=" + completionTime);
            
            // Si es la última operación, destruir el OrderAgent
            if (isLastOperation) {
                String agentName = "OrderAgent_Job" + jobId;
                jade.wrapper.AgentController orderAgent = container.getAgent(agentName);
                if (orderAgent != null) {
                    orderAgent.kill();
                    System.out.println("[JADE] OrderAgent " + agentName + " destruido (job completado)");
                }
            }
            
            return createSuccessResponse(null, null);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error notificando finalización: " + e.getMessage());
        }
    }
    
    /**
     * MEJORA #4: Maneja falla de operación durante ejecución y re-negocia
     */
    private static String handleOperationFailure(JsonObject req) {
        try {
            int jobId = req.get("job_id").getAsInt();
            int operationIndex = req.get("operation_index").getAsInt();
            int failedMachineId = req.get("failed_machine_id").getAsInt();
            double currentTime = req.get("current_time").getAsDouble();
            
            System.out.println("[FAILURE] Job " + jobId + " op " + operationIndex +
                             " FALLÓ en Machine " + failedMachineId + " en t=" + String.format("%.2f", currentTime));
            
            // Obtener máquinas disponibles para re-negociación
            JsonArray availableMachinesArray = req.getAsJsonArray("available_machines");
            List<Integer> availableMachines = new ArrayList<>();
            for (int i = 0; i < availableMachinesArray.size(); i++) {
                availableMachines.add(availableMachinesArray.get(i).getAsInt());
            }
            
            if (availableMachines.isEmpty()) {
                System.err.println("[RENEGOTIATE] ✗ No hay máquinas disponibles para re-negociación");
                return createErrorResponse("No hay máquinas disponibles para re-negociación");
            }
            
            System.out.println("[RENEGOTIATE] Iniciando re-negociación para Job " + jobId +
                             " op " + operationIndex + " con " + availableMachines.size() + " máquinas disponibles");
            
            // MEJORA #4: Ejecutar negociación CNP sin crear OrderAgent
            // El OrderAgent ya existe - solo ejecutamos el protocolo CNP directamente
            
            // Crear ACLMessage CFP para las máquinas
            jade.lang.acl.ACLMessage cfp = new jade.lang.acl.ACLMessage(jade.lang.acl.ACLMessage.CFP);
            JsonObject cfpContent = new JsonObject();
            cfpContent.addProperty("job_id", jobId);
            cfpContent.addProperty("operation_index", operationIndex);
            cfpContent.addProperty("current_time", currentTime);
            cfp.setContent(cfpContent.toString());
            cfp.setProtocol(jade.domain.FIPANames.InteractionProtocol.FIPA_CONTRACT_NET);
            cfp.setReplyByDate(new Date(System.currentTimeMillis() + 5000));
            
            // Agregar máquinas como receivers
            for (Integer machineId : availableMachines) {
                cfp.addReceiver(new jade.core.AID("MachineAgent_M" + machineId, jade.core.AID.ISLOCALNAME));
            }
            
            // SIMPLIFICADO: Retornar la primera máquina disponible como asignación
            // (En la implementación completa, debería ejecutar el protocolo CNP completo)
            int selectedMachine = availableMachines.get(0);
            
            JsonObject assignmentData = new JsonObject();
            assignmentData.addProperty("machine_id", selectedMachine);
            assignmentData.addProperty("expected_start", currentTime);
            assignmentData.addProperty("expected_end", currentTime + 10.0); // Duración estimada
            
            System.out.println("[RENEGOTIATE] ✓ Re-asignado a Machine " + selectedMachine +
                             " | start=" + String.format("%.2f", currentTime) +
                             " | end=" + String.format("%.2f", currentTime + 10.0));
            
            return createSuccessResponse("assignment", assignmentData);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error en re-negociación: " + e.getMessage());
        }
    }
    
    /**
     * Notifica falla de máquina
     */
    private static String handleMachineFailure(JsonObject req) {
        try {
            int machineId = req.get("machine_id").getAsInt();
            double failureTime = req.get("failure_time").getAsDouble();
            double repairDuration = req.get("repair_duration").getAsDouble();
            
            System.out.println("[JADE] Máquina " + machineId + " FAILED en t=" + failureTime +
                             " (reparación: " + repairDuration + " unidades)");
            
            // Notificar a MachineAgent correspondiente
            // En implementación completa, usar O2A communication
            
            return createSuccessResponse(null, null);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error notificando falla: " + e.getMessage());
        }
    }
    
    /**
     * Notifica reparación de máquina
     */
    private static String handleMachineRepair(JsonObject req) {
        try {
            int machineId = req.get("machine_id").getAsInt();
            double repairTime = req.get("repair_time").getAsDouble();
            
            System.out.println("[JADE] Máquina " + machineId + " reparada en t=" + repairTime);
            
            return createSuccessResponse(null, null);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error notificando reparación: " + e.getMessage());
        }
    }
    
    /**
     * Obtiene estado de máquina
     */
    private static String handleGetMachineStatus(JsonObject req) {
        try {
            int machineId = req.get("machine_id").getAsInt();
            
            // En implementación completa, consultar estado real de MachineAgent
            JsonObject status = new JsonObject();
            status.addProperty("available", true);
            status.addProperty("current_job", -1);
            status.addProperty("queue_length", 0);
            
            return createSuccessResponse("machine_status", status);
            
        } catch (Exception e) {
            e.printStackTrace();
            return createErrorResponse("Error obteniendo estado: " + e.getMessage());
        }
    }
    
    /**
     * Crea respuesta de éxito
     */
    private static String createSuccessResponse(String key, Object value) {
        JsonObject response = new JsonObject();
        response.addProperty("status", "success");
        if (key != null && value != null) {
            if (value instanceof String) {
                response.addProperty(key, (String) value);
            } else if (value instanceof JsonObject) {
                response.add(key, (JsonObject) value);
            }
        }
        return gson.toJson(response);
    }
    
    /**
     * Crea respuesta de error
     */
    private static String createErrorResponse(String message) {
        JsonObject response = new JsonObject();
        response.addProperty("status", "error");
        response.addProperty("message", message);
        return gson.toJson(response);
    }
}
