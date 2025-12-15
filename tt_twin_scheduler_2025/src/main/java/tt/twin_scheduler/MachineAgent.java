package tt.twin_scheduler;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class MachineAgent extends Agent {
    private int machineId;
    private String status = "IDLE"; // IDLE, BUSY, FAILED
    private int currentJobId = -1;

    @Override
    protected void setup() {
        Object[] args = getArguments();
        if (args != null && args.length > 0) {
            this.machineId = (Integer) args[0];
        }
        
        // Habilitar O2A para recibir actualizaciones del gemelo físico
        setEnabledO2ACommunication(true, 0);

        System.out.println("MachineAgent " + getLocalName() + " (ID: " + machineId + ") READY [Mirroring Mode]");

        addBehaviour(new CyclicBehaviour(this) {
            @Override
            public void action() {
                Object obj = myAgent.getO2AObject();
                if (obj != null) {
                    if (obj instanceof String) {
                        processEvent((String) obj);
                    }
                } else {
                    block();
                }
            }
        });
    }

    private void processEvent(String jsonEvent) {
        try {
            Gson gson = new Gson();
            JsonObject event = gson.fromJson(jsonEvent, JsonObject.class);
            String type = event.has("event_type") ? event.get("event_type").getAsString() : "unknown";
            
            String oldStatus = this.status;
            int oldJob = this.currentJobId;

            switch (type) {
                case "MACHINE_STARTED": // Inicio de trabajo
                    this.status = "BUSY";
                    if (event.has("job_id")) {
                        this.currentJobId = event.get("job_id").getAsInt();
                    }
                    break;
                case "MACHINE_FINISHED": // Fin de trabajo normal
                    this.status = "IDLE";
                    this.currentJobId = -1;
                    break;
                case "MACHINE_FAILED": // Rotura de máquina
                    this.status = "FAILED";
                    // Mantenemos el job ID si falló con un trabajo dentro, o -1 si estaba libre
                    break;
                case "MACHINE_REPAIRED": // Reparación completada
                    this.status = "IDLE";
                    // Asumimos que al repararse queda libre (o reanuda, depende de la lógica de simulación)
                    // Por simplicidad del mirror, lo dejamos IDLE hasta nuevo aviso
                    this.currentJobId = -1; 
                    break;
            }

            // Solo imprimir si hubo cambio de estado relevante
            if (!oldStatus.equals(this.status) || oldJob != this.currentJobId) {
                System.out.println(String.format(">> [MIRROR M%d] Estado: %s -> %s | Job: %d -> %d", 
                    machineId, oldStatus, this.status, oldJob, this.currentJobId));
            }

        } catch (Exception e) {
            System.err.println("Error procesando evento en MachineAgent " + machineId + ": " + e.getMessage());
        }
    }
}
