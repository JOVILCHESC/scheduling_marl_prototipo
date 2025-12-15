package tt.twin_scheduler;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class OrderAgent extends Agent {
    private int jobId;
    private String operations;
    private double dueDate;
    private String status = "CREATED"; // CREATED, PROCESSING, COMPLETED

    @Override
    protected void setup() {
        Object[] args = getArguments();
        if (args != null && args.length > 0) {
            this.jobId = (Integer) args[0];
            this.operations = (String) args[1];
            this.dueDate = (Double) args[2];
        }
        
        setEnabledO2ACommunication(true, 0);
        System.out.println("OrderAgent " + getLocalName() + " (Job " + jobId + ") CREATED [Mirroring Mode]");
        
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
            
            switch (type) {
                case "MACHINE_STARTED":
                    // Si el evento es de inicio y corresponde a este job
                    if (event.has("job_id") && event.get("job_id").getAsInt() == this.jobId) {
                        this.status = "PROCESSING";
                    }
                    break;
                case "JOB_COMPLETED":
                    this.status = "COMPLETED";
                    break;
            }
            
            if (!oldStatus.equals(this.status)) {
                System.out.println(String.format(">> [MIRROR O%d] Status: %s -> %s", jobId, oldStatus, this.status));
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void takeDown() {
        System.out.println("OrderAgent " + getLocalName() + " terminating (Final Status: " + status + ").");
    }
}
