package tt.twin_scheduler;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.domain.DFService;
import jade.domain.FIPAException;
import jade.domain.FIPAAgentManagement.DFAgentDescription;
import jade.domain.FIPAAgentManagement.ServiceDescription;
import jade.domain.FIPAAgentManagement.FailureException;
import jade.domain.FIPAAgentManagement.NotUnderstoodException;
import jade.domain.FIPAAgentManagement.RefuseException;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;
import jade.proto.ContractNetResponder;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;

public class MachineAgentCNP extends Agent {
    
    // Clase interna para representar operaciones programadas
    private static class ScheduledOperation {
        String jobId;
        int operationIndex;
        double startTime;
        double endTime;
        
        ScheduledOperation(String jobId, int operationIndex, double startTime, double endTime) {
            this.jobId = jobId;
            this.operationIndex = operationIndex;
            this.startTime = startTime;
            this.endTime = endTime;
        }
        
        @Override
        public String toString() {
            return String.format("Job%s_Op%d [%.2f-%.2f]", jobId, operationIndex, startTime, endTime);
        }
    }
    
    private int machineId = -1;
    private String status = "IDLE"; // IDLE, BUSY, FAILED
    private List<ScheduledOperation> schedule = new ArrayList<>();
    private double currentSimulationTime = 0.0;

    @Override
    protected void setup() {
        Object[] args = getArguments();
        if (args != null && args.length > 0) {
            this.machineId = Integer.parseInt(args[0].toString());
        }
        
        // Registrar servicio en el DF
        DFAgentDescription dfd = new DFAgentDescription();
        dfd.setName(getAID());
        ServiceDescription sd = new ServiceDescription();
        sd.setType("manufacturing-machine");
        sd.setName("machine-" + machineId);
        dfd.addServices(sd);
        try {
            DFService.register(this, dfd);
        } catch (FIPAException fe) {
            fe.printStackTrace();
        }

        // Habilitar comunicación O2A (Object-to-Agent) para recibir eventos desde MainJADE
        setEnabledO2ACommunication(true, 0);
        
        System.out.println("MachineAgentCNP " + getLocalName() + " (ID: " + machineId + ") listo y esperando eventos.");

        // Comportamiento para recibir eventos de SimPy (Mirroring)
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

        // Comportamiento para responder a negociaciones (CNP)
        MessageTemplate template = MessageTemplate.and(
                MessageTemplate.MatchProtocol(jade.domain.FIPANames.InteractionProtocol.FIPA_CONTRACT_NET),
                MessageTemplate.MatchPerformative(ACLMessage.CFP) );

        addBehaviour(new ContractNetResponder(this, template) {
            @Override
            protected ACLMessage handleCfp(ACLMessage cfp) throws NotUnderstoodException, RefuseException {
                // System.out.println("Agente " + getLocalName() + ": CFP recibido de " + cfp.getSender().getName());
                
                if ("FAILED".equals(status)) {
                    throw new RefuseException("Machine is FAILED");
                }
                
                // MEJORA #1 y #2: Calcular tiempo disponible y enviar propuesta con tiempo estimado
                try {
                    // Parsear el CFP para obtener current_time y duration
                    Gson gson = new Gson();
                    JsonObject cfpContent = gson.fromJson(cfp.getContent(), JsonObject.class);
                    double currentTime = cfpContent.has("current_time") ? cfpContent.get("current_time").getAsDouble() : currentSimulationTime;
                    double duration = cfpContent.has("duration") ? cfpContent.get("duration").getAsDouble() : 10.0;
                    
                    // Actualizar tiempo de simulación
                    currentSimulationTime = currentTime;
                    
                    // Calcular próximo tiempo disponible
                    double nextAvailableTime = getNextAvailableTime(currentTime);
                    double expectedStart = Math.max(currentTime, nextAvailableTime);
                    double expectedEnd = expectedStart + duration;
                    
                    // Crear propuesta con tiempos estimados
                    ACLMessage propose = cfp.createReply();
                    propose.setPerformative(ACLMessage.PROPOSE);
                    
                    JsonObject proposal = new JsonObject();
                    proposal.addProperty("machine_id", machineId);
                    proposal.addProperty("expected_start", expectedStart);
                    proposal.addProperty("expected_end", expectedEnd);
                    proposal.addProperty("current_status", status);
                    
                    propose.setContent(proposal.toString());
                    
                    // Log para debugging
                    if (!status.equals("IDLE")) {
                        System.out.println("[CNP] " + getLocalName() + " (" + status + ") propone iniciar en t=" + String.format("%.2f", expectedStart));
                    }
                    
                    return propose;
                    
                } catch (Exception e) {
                    System.err.println("[ERROR] " + getLocalName() + " error al procesar CFP: " + e.getMessage());
                    throw new RefuseException("Error processing CFP");
                }
            }

            @Override
            protected ACLMessage handleAcceptProposal(ACLMessage cfp, ACLMessage propose, ACLMessage accept) throws FailureException {
                // MEJORA #5: Validar disponibilidad real antes de confirmar
                try {
                    Gson gson = new Gson();
                    JsonObject acceptContent = gson.fromJson(accept.getContent(), JsonObject.class);
                    
                    String jobId = acceptContent.get("job_id").getAsString();
                    int operationIndex = acceptContent.get("operation_index").getAsInt();
                    double expectedStart = acceptContent.get("expected_start").getAsDouble();
                    double expectedEnd = acceptContent.get("expected_end").getAsDouble();
                    
                    // Verificar que el slot de tiempo sigue disponible
                    if (!isTimeSlotAvailable(expectedStart, expectedEnd, currentSimulationTime)) {
                        ACLMessage failure = accept.createReply();
                        failure.setPerformative(ACLMessage.FAILURE);
                        JsonObject error = new JsonObject();
                        error.addProperty("error", "Time slot no longer available - race condition detected");
                        failure.setContent(error.toString());
                        System.out.println("[CONFLICT] " + getLocalName() + " rechaza Job" + jobId + " - slot ocupado");
                        return failure;
                    }
                    
                    // Agregar al schedule
                    ScheduledOperation scheduledOp = new ScheduledOperation(jobId, operationIndex, expectedStart, expectedEnd);
                    schedule.add(scheduledOp);
                    
                    // Ordenar schedule por startTime
                    schedule.sort((a, b) -> Double.compare(a.startTime, b.startTime));
                    
                    System.out.println("[SCHEDULE] " + getLocalName() + " agrega: " + scheduledOp + " | Total ops: " + schedule.size());
                    
                    ACLMessage inform = accept.createReply();
                    inform.setPerformative(ACLMessage.INFORM);
                    JsonObject confirmation = new JsonObject();
                    confirmation.addProperty("status", "confirmed");
                    confirmation.addProperty("machine_id", machineId);
                    confirmation.addProperty("expected_start", expectedStart);
                    confirmation.addProperty("expected_end", expectedEnd);
                    inform.setContent(confirmation.toString());
                    
                    return inform;
                    
                } catch (Exception e) {
                    System.err.println("[ERROR] " + getLocalName() + " error en handleAcceptProposal: " + e.getMessage());
                    throw new FailureException("Error confirming operation");
                }
            }

            @Override
            protected void handleRejectProposal(ACLMessage cfp, ACLMessage propose, ACLMessage reject) {
                // System.out.println("Agente " + getLocalName() + ": Propuesta RECHAZADA");
            }
        });
    }
    
    /**
     * MEJORA #1: Calcular el próximo tiempo en que la máquina estará disponible
     */
    private double getNextAvailableTime(double currentTime) {
        // Limpiar operaciones pasadas del schedule
        schedule.removeIf(op -> op.endTime <= currentTime);
        
        if (schedule.isEmpty()) {
            return currentTime; // Disponible inmediatamente
        }
        
        // Retornar el endTime de la última operación programada
        ScheduledOperation lastOp = schedule.get(schedule.size() - 1);
        return lastOp.endTime;
    }
    
    /**
     * MEJORA #5: Verificar si un slot de tiempo está disponible
     */
    private boolean isTimeSlotAvailable(double start, double end, double currentTime) {
        // Limpiar operaciones pasadas
        schedule.removeIf(op -> op.endTime <= currentTime);
        
        // Verificar solapamiento con operaciones existentes
        for (ScheduledOperation op : schedule) {
            // Hay conflicto si los intervalos se solapan
            if (!(end <= op.startTime || start >= op.endTime)) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Remover una operación específica del schedule (cuando se completa o falla)
     */
    private void removeFromSchedule(String jobId, int operationIndex) {
        boolean removed = schedule.removeIf(op -> 
            op.jobId.equals(jobId) && op.operationIndex == operationIndex
        );
        
        if (removed) {
            System.out.println("[SCHEDULE] " + getLocalName() + " removió Job" + jobId + "_Op" + operationIndex + " | Ops restantes: " + schedule.size());
        }
    }

    @Override
    protected void takeDown() {
        try {
            DFService.deregister(this);
        } catch (FIPAException fe) {
            fe.printStackTrace();
        }
    }

    private void processEvent(String jsonEvent) {
        try {
            Gson gson = new Gson();
            JsonObject event = gson.fromJson(jsonEvent, JsonObject.class);
            String type = event.has("event_type") ? event.get("event_type").getAsString() : "unknown";
            
            String oldStatus = this.status;
            
            // Actualizar currentSimulationTime si viene en el evento
            if (event.has("time")) {
                currentSimulationTime = event.get("time").getAsDouble();
            }
            
            switch (type) {
                case "MACHINE_STARTED":
                    this.status = "BUSY";
                    break;
                case "MACHINE_FINISHED":
                    this.status = "IDLE";
                    // Remover del schedule la operación que finalizó
                    if (event.has("job_id") && event.has("operation_index")) {
                        String jobId = event.get("job_id").getAsString();
                        int opIndex = event.get("operation_index").getAsInt();
                        removeFromSchedule(jobId, opIndex);
                    }
                    break;
                case "MACHINE_REPAIRED":
                    this.status = "IDLE";
                    break;
                case "MACHINE_FAILED":
                    this.status = "FAILED";
                    // Limpiar schedule cuando falla la máquina
                    if (!schedule.isEmpty()) {
                        System.out.println("[FAILURE] " + getLocalName() + " limpia schedule de " + schedule.size() + " operaciones pendientes");
                        schedule.clear();
                    }
                    break;
            }
            
            if (!oldStatus.equals(this.status)) {
                System.out.println(">> [ESPEJO] " + getLocalName() + " cambio estado: " + oldStatus + " -> " + this.status + " (Evento: " + type + ")");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
