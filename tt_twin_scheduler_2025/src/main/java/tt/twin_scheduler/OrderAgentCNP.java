package tt.twin_scheduler;

import jade.core.Agent;
import jade.core.AID;
import jade.lang.acl.ACLMessage;
import jade.proto.ContractNetInitiator;
import jade.domain.FIPANames;
import java.util.*;

/**
 * OrderAgentCNP - Agente que representa una orden/job en la Fase 3 (CNP)
 * 
 * Responsabilidades:
 * - Recibir especificación de job desde SimPy vía ZeroMQ
 * - Iniciar negociación CNP para cada operación del job
 * - Enviar CFP (Call For Proposal) a MachineAgents disponibles
 * - Evaluar propuestas recibidas
 * - Aceptar mejor propuesta y rechazar las demás
 * - Notificar asignación resultante a SimPy
 * 
 * Protocolo CNP:
 * 1. CFP → MachineAgents disponibles
 * 2. Recibir Proposals/Refuse
 * 3. Evaluar propuestas (mejor tiempo estimado de finalización)
 * 4. Accept mejor propuesta, Reject demás
 * 5. Retornar asignación a SimPy
 */
public class OrderAgentCNP extends Agent {
    
    // Datos del job
    private int jobId;
    private List<Operation> operations;
    private double dueDate;
    private double arrivalTime;
    
    // Estado de negociación
    private int currentOperationIndex = 0;
    private Map<Integer, MachineAssignment> assignments; // operationIndex -> assignment
    
    // Referencia a MachineAgents disponibles
    private List<AID> availableMachineAgents;
    
    /**
     * Clase interna para representar operaciones del job
     */
    public static class Operation {
        public int machineType;  // Tipo de máquina requerida (0-5)
        public double duration;  // Duración de procesamiento
        
        public Operation(int machineType, double duration) {
            this.machineType = machineType;
            this.duration = duration;
        }
    }
    
    /**
     * Clase interna para almacenar asignaciones
     */
    public static class MachineAssignment {
        public int machineId;
        public double expectedStart;
        public double expectedEnd;
        
        public MachineAssignment(int machineId, double expectedStart, double expectedEnd) {
            this.machineId = machineId;
            this.expectedStart = expectedStart;
            this.expectedEnd = expectedEnd;
        }
    }
    
    @Override
    protected void setup() {
        System.out.println("[OrderAgentCNP] " + getLocalName() + " iniciado");
        
        // Inicializar estructuras
        assignments = new HashMap<>();
        availableMachineAgents = new ArrayList<>();
        
        // Los argumentos vienen desde ZeroMQ cuando se crea el agente
        Object[] args = getArguments();
        if (args != null && args.length >= 4) {
            jobId = (Integer) args[0];
            operations = (List<Operation>) args[1];
            dueDate = (Double) args[2];
            arrivalTime = (Double) args[3];
            
            System.out.println("[OrderAgentCNP] Job " + jobId + " tiene " + operations.size() + 
                             " operaciones, due_date=" + dueDate);
        } else {
            System.err.println("[OrderAgentCNP] Error: Argumentos insuficientes");
            doDelete();
        }
        
        // NOTA: Re-negociación simplificada - se maneja directamente desde MainJADEPhase3.handleOperationFailure()
        // que llama a handleCNPNegotiation(), evitando complejidad de O2A communication
    }
    
    /**
     * Inicia negociación CNP para una operación específica
     * Llamado desde ZeroMQ cuando SimPy está listo para asignar operación
     * 
     * @param operationIndex Índice de operación a negociar
     * @param currentTime Tiempo actual de simulación
     * @param availableMachineIds IDs de máquinas disponibles
     * @return MachineAssignment con resultado de negociación
     */
    public MachineAssignment negotiateOperation(int operationIndex, double currentTime, 
                                                List<Integer> availableMachineIds) {
        
        if (operationIndex >= operations.size()) {
            System.err.println("[OrderAgentCNP] Índice de operación inválido: " + operationIndex);
            return null;
        }
        
        this.currentOperationIndex = operationIndex;
        Operation op = operations.get(operationIndex);
        
        System.out.println("[OrderAgentCNP] Job " + jobId + " negocia operación " + operationIndex +
                         " (machineType=" + op.machineType + ", duration=" + op.duration + ")");
        
        // Construir lista de MachineAgents disponibles que coincidan con el tipo requerido
        availableMachineAgents.clear();
        for (Integer machineId : availableMachineIds) {
            // Asumimos que machineId corresponde al tipo (0-5)
            if (machineId == op.machineType) {
                AID machineAID = new AID("MachineAgent_" + machineId, AID.ISLOCALNAME);
                availableMachineAgents.add(machineAID);
            }
        }
        
        if (availableMachineAgents.isEmpty()) {
            System.err.println("[OrderAgentCNP] No hay MachineAgents disponibles para tipo " + op.machineType);
            return null;
        }
        
        // Crear CFP (Call For Proposal)
        ACLMessage cfp = new ACLMessage(ACLMessage.CFP);
        for (AID machineAID : availableMachineAgents) {
            cfp.addReceiver(machineAID);
        }
        
        cfp.setProtocol(FIPANames.InteractionProtocol.FIPA_CONTRACT_NET);
        cfp.setReplyByDate(new Date(System.currentTimeMillis() + 2000)); // 2 segundos timeout
        
        // Contenido del CFP: JSON con detalles de la operación
        String cfpContent = String.format(
            "{\"job_id\": %d, \"operation_index\": %d, \"machine_type\": %d, " +
            "\"duration\": %.2f, \"current_time\": %.2f, \"due_date\": %.2f}",
            jobId, operationIndex, op.machineType, op.duration, currentTime, dueDate
        );
        cfp.setContent(cfpContent);
        
        // Iniciar comportamiento CNP Initiator
        CNPInitiatorBehaviour cnpBehaviour = new CNPInitiatorBehaviour(this, cfp);
        addBehaviour(cnpBehaviour);
        
        // Esperar resultado de negociación (bloqueante para sincronizar con SimPy)
        return cnpBehaviour.waitForResult(5000); // 5 segundos timeout
    }
    
    /**
     * Comportamiento CNP Initiator - Maneja protocolo Contract Net
     */
    private class CNPInitiatorBehaviour extends ContractNetInitiator {
        
        private MachineAssignment bestAssignment = null;
        private final Object lock = new Object();
        private boolean completed = false;
        
        public CNPInitiatorBehaviour(Agent a, ACLMessage cfp) {
            super(a, cfp);
        }
        
        @Override
        protected void handlePropose(ACLMessage propose, Vector acceptances) {
            System.out.println("[OrderAgentCNP] Propuesta recibida de " + propose.getSender().getLocalName() +
                             ": " + propose.getContent());
        }
        
        @Override
        protected void handleRefuse(ACLMessage refuse) {
            System.out.println("[OrderAgentCNP] Rechazo recibido de " + refuse.getSender().getLocalName());
        }
        
        @Override
        protected void handleAllResponses(Vector responses, Vector acceptances) {
            System.out.println("[OrderAgentCNP] Evaluando " + responses.size() + " respuestas");
            
            // MEJORA #3: Función objetiva explícita para selección de mejor propuesta
            List<ProposalEvaluation> validProposals = new ArrayList<>();
            
            // Paso 1: Recolectar y evaluar todas las propuestas válidas
            for (Object obj : responses) {
                ACLMessage msg = (ACLMessage) obj;
                
                if (msg.getPerformative() == ACLMessage.PROPOSE) {
                    try {
                        String content = msg.getContent();
                        int machineId = extractInt(content, "machine_id");
                        double expectedStart = extractDouble(content, "expected_start");
                        double expectedEnd = extractDouble(content, "expected_end");
                        
                        // Calcular score según función objetiva
                        double score = calculateObjectiveScore(expectedStart, expectedEnd);
                        
                        validProposals.add(new ProposalEvaluation(
                            msg, machineId, expectedStart, expectedEnd, score
                        ));
                        
                        System.out.println("[CNP-EVAL] Machine " + machineId +
                                         " | start=" + String.format("%.2f", expectedStart) +
                                         " | end=" + String.format("%.2f", expectedEnd) +
                                         " | score=" + String.format("%.2f", score));
                        
                    } catch (Exception e) {
                        System.err.println("[OrderAgentCNP] Error parseando propuesta: " + e.getMessage());
                    }
                }
            }
            
            // Paso 2: Seleccionar mejor propuesta según score (menor es mejor)
            if (!validProposals.isEmpty()) {
                ProposalEvaluation bestProposal = selectBestProposal(validProposals);
                bestAssignment = new MachineAssignment(
                    bestProposal.machineId, 
                    bestProposal.expectedStart, 
                    bestProposal.expectedEnd
                );
                
                System.out.println("[CNP-DECISION] ✓ Seleccionada Machine " + bestAssignment.machineId +
                                 " | expected_end=" + String.format("%.2f", bestAssignment.expectedEnd) +
                                 " | score=" + String.format("%.2f", bestProposal.score));
                
                // Paso 3: Generar mensajes de aceptación/rechazo
                for (Object obj : responses) {
                    ACLMessage msg = (ACLMessage) obj;
                    ACLMessage reply;
                    
                    if (msg == bestProposal.message) {
                        // Aceptar mejor propuesta
                        reply = msg.createReply();
                        reply.setPerformative(ACLMessage.ACCEPT_PROPOSAL);
                        
                        // Enviar detalles completos en ACCEPT
                        String acceptContent = String.format(
                            "{\"job_id\": %d, \"operation_index\": %d, " +
                            "\"expected_start\": %.2f, \"expected_end\": %.2f}",
                            jobId, currentOperationIndex, 
                            bestAssignment.expectedStart, bestAssignment.expectedEnd
                        );
                        reply.setContent(acceptContent);
                        System.out.println("[CNP] ACCEPT → " + msg.getSender().getLocalName());
                        
                    } else if (msg.getPerformative() == ACLMessage.PROPOSE) {
                        // Rechazar demás propuestas
                        reply = msg.createReply();
                        reply.setPerformative(ACLMessage.REJECT_PROPOSAL);
                        reply.setContent("{\"reason\": \"mejor propuesta seleccionada\"}");
                        // System.out.println("[CNP] REJECT → " + msg.getSender().getLocalName());
                    } else {
                        // Refuse no requiere respuesta
                        continue;
                    }
                    
                    acceptances.add(reply);
                }
            } else {
                System.err.println("[OrderAgentCNP] ✗ No se recibieron propuestas válidas");
            }
            
            // Marcar como completado
            synchronized (lock) {
                completed = true;
                lock.notify();
            }
        }
        
        /**
         * MEJORA #3: Función objetiva para evaluar propuestas
         * 
         * Estrategia: Minimizar tiempo de finalización (Earliest Completion Time)
         * Considera:
         * - Tiempo de finalización esperado (peso 70%)
         * - Penalización por tardiness si excede due date (peso 30%)
         * 
         * @return score (menor es mejor)
         */
        private double calculateObjectiveScore(double expectedStart, double expectedEnd) {
            Operation currentOp = operations.get(currentOperationIndex);
            
            // Componente 1: Tiempo de finalización (minimizar completion time)
            double completionScore = expectedEnd;
            
            // Componente 2: Penalización por tardiness
            double tardinessScore = 0.0;
            if (expectedEnd > dueDate) {
                double tardiness = expectedEnd - dueDate;
                tardinessScore = tardiness * 2.0; // Factor de penalización
            }
            
            // Score total (ponderado)
            double totalScore = (completionScore * 0.7) + (tardinessScore * 0.3);
            
            return totalScore;
        }
        
        /**
         * MEJORA #3: Seleccionar mejor propuesta según score
         */
        private ProposalEvaluation selectBestProposal(List<ProposalEvaluation> proposals) {
            ProposalEvaluation best = proposals.get(0);
            
            for (ProposalEvaluation proposal : proposals) {
                if (proposal.score < best.score) {
                    best = proposal;
                }
            }
            
            return best;
        }
        
        /**
         * Clase auxiliar para almacenar evaluación de propuestas
         */
        private class ProposalEvaluation {
            ACLMessage message;
            int machineId;
            double expectedStart;
            double expectedEnd;
            double score;
            
            ProposalEvaluation(ACLMessage msg, int machineId, double start, double end, double score) {
                this.message = msg;
                this.machineId = machineId;
                this.expectedStart = start;
                this.expectedEnd = end;
                this.score = score;
            }
        }
        
        @Override
        protected void handleInform(ACLMessage inform) {
            System.out.println("[OrderAgentCNP] INFORM recibido de " + inform.getSender().getLocalName() +
                             ": " + inform.getContent());
        }
        
        @Override
        protected void handleFailure(ACLMessage failure) {
            System.err.println("[OrderAgentCNP] FAILURE recibido de " + failure.getSender().getLocalName());
        }
        
        /**
         * Espera resultado de negociación (uso desde ZeroMQ handler)
         */
        public MachineAssignment waitForResult(long timeout) {
            synchronized (lock) {
                if (!completed) {
                    try {
                        lock.wait(timeout);
                    } catch (InterruptedException e) {
                        System.err.println("[OrderAgentCNP] Timeout esperando resultado CNP");
                    }
                }
            }
            return bestAssignment;
        }
        
        // Métodos auxiliares para parsing simple de JSON
        private int extractInt(String json, String key) {
            String pattern = "\"" + key + "\":\\s*(\\d+)";
            java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
            java.util.regex.Matcher m = p.matcher(json);
            if (m.find()) {
                return Integer.parseInt(m.group(1));
            }
            throw new IllegalArgumentException("Key not found: " + key);
        }
        
        private double extractDouble(String json, String key) {
            String pattern = "\"" + key + "\":\\s*([0-9.]+)";
            java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
            java.util.regex.Matcher m = p.matcher(json);
            if (m.find()) {
                return Double.parseDouble(m.group(1));
            }
            throw new IllegalArgumentException("Key not found: " + key);
        }
    }
    
    @Override
    protected void takeDown() {
        System.out.println("[OrderAgentCNP] " + getLocalName() + " terminado para Job " + jobId);
    }
}
