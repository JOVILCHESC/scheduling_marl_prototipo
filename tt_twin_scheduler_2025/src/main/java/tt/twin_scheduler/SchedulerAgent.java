// package tt_twin_scheduler.src;
package tt.twin_scheduler;

import jade.core.Agent;

public class SchedulerAgent extends Agent {
    @Override
    protected void setup() {
        System.out.println("SchedulerAgent listo!");
        // Inicializar Q-table y parámetros
        QLearning.getInstance().loadQTable();
    }

    // --- Q-learning estático (singleton para acceso desde MainJADE) ---
    public static class QLearning {
        private static QLearning instance;
        // Q-table: estado -> (acción -> valor Q)
        private java.util.HashMap<String, java.util.HashMap<Integer, Double>> qTable = new java.util.HashMap<>();
        // Parámetros
        private double alpha = 0.1; // tasa de aprendizaje
        private double gamma = 0.95; // factor de descuento
        private double epsilon = 0.1; // prob exploración

        private QLearning() {}
        public static QLearning getInstance() {
            if (instance == null) instance = new QLearning();
            return instance;
        }

        // Serializa el estado a una representación compacta y numérica.
        // Devuelve un string con estadísticas de la cola: longitud, min, mean, max.
        public String serializeState(int machineId, int currentJob, java.util.List<Integer> queueJobIds, java.util.List<Double> queueDurations) {
            int n = queueDurations == null ? 0 : queueDurations.size();
            double min = 0.0, mean = 0.0, max = 0.0;
            if (n > 0) {
                min = Double.POSITIVE_INFINITY;
                max = Double.NEGATIVE_INFINITY;
                double sum = 0.0;
                for (Double d : queueDurations) {
                    double v = d == null ? 0.0 : d.doubleValue();
                    sum += v;
                    if (v < min) min = v;
                    if (v > max) max = v;
                }
                mean = sum / n;
            }
            // Formato compacto: M{machineId}:len={n}:min={min:.2f}:mean={mean:.2f}:max={max:.2f}
            return String.format("M%d:len=%d:min=%.2f:mean=%.2f:max=%.2f", machineId, n, min, mean, max);
        }

        // Elegir acción (índice del job en la cola) usando epsilon-greedy
        public int selectAction(String state, java.util.List<Integer> possibleActions) {
            if (Math.random() < epsilon) {
                // Exploración
                return possibleActions.get((int)(Math.random()*possibleActions.size()));
            }
            // Explotación: elegir acción con mayor Q
            java.util.HashMap<Integer, Double> qRow = qTable.getOrDefault(state, new java.util.HashMap<>());
            double maxQ = Double.NEGATIVE_INFINITY;
            int bestAction = possibleActions.get(0);
            for (int a : possibleActions) {
                double q = qRow.getOrDefault(a, 0.0);
                if (q > maxQ) { maxQ = q; bestAction = a; }
            }
            return bestAction;
        }

        // Actualizar Q-table
        public void updateQ(String state, int action, double reward, String nextState, java.util.List<Integer> nextActions) {
            java.util.HashMap<Integer, Double> qRow = qTable.getOrDefault(state, new java.util.HashMap<>());
            double q = qRow.getOrDefault(action, 0.0);
            // Q-learning update
            double maxQNext = 0.0;
            if (nextActions != null && !nextActions.isEmpty()) {
                java.util.HashMap<Integer, Double> qNextRow = qTable.getOrDefault(nextState, new java.util.HashMap<>());
                for (int a : nextActions) {
                    maxQNext = Math.max(maxQNext, qNextRow.getOrDefault(a, 0.0));
                }
            }
            double newQ = q + alpha * (reward + gamma * maxQNext - q);
            qRow.put(action, newQ);
            qTable.put(state, qRow);
        }

        // Guardar Q-table a disco
        public void saveQTable() {
            try (java.io.ObjectOutputStream out = new java.io.ObjectOutputStream(new java.io.FileOutputStream("qtable.ser"))) {
                out.writeObject(qTable);
            } catch (Exception e) { e.printStackTrace(); }
        }
        // Cargar Q-table de disco
        public void loadQTable() {
            try (java.io.ObjectInputStream in = new java.io.ObjectInputStream(new java.io.FileInputStream("qtable.ser"))) {
                qTable = (java.util.HashMap<String, java.util.HashMap<Integer, Double>>) in.readObject();
            } catch (Exception e) { /* Si no existe, se ignora */ }
        }
    }

    // --- Métodos públicos para MainJADE ---
    // Decidir acción dado el estado (wrapper para /decide)
    public static int decideJob(int machineId, int currentJob, java.util.List<Integer> queueJobIds, java.util.List<Double> queueDurations) {
        String state = QLearning.getInstance().serializeState(machineId, currentJob, queueJobIds, queueDurations);
        java.util.List<Integer> actions = new java.util.ArrayList<>();
        for (int i = 0; i < queueJobIds.size(); i++) actions.add(i);
        return QLearning.getInstance().selectAction(state, actions);
    }

    // Actualizar Q-table con feedback (wrapper para /feedback)
    public static void feedback(int machineId, int currentJob, java.util.List<Integer> queueJobIds, java.util.List<Double> queueDurations, int action, double reward, String nextState, java.util.List<Integer> nextActions) {
        String state = QLearning.getInstance().serializeState(machineId, currentJob, queueJobIds, queueDurations);
        QLearning.getInstance().updateQ(state, action, reward, nextState, nextActions);
        QLearning.getInstance().saveQTable();
    }
}
