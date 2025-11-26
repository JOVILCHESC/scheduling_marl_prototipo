// package tt_twin_scheduler.src;
package tt.twin_scheduler;

import jade.core.Profile;
import jade.core.ProfileImpl;
import jade.core.Runtime;
import jade.wrapper.AgentController;
import jade.wrapper.ContainerController;

public class MainJADE {
    public static void main(String[] args) {

        Runtime rt = Runtime.instance();
        Profile p = new ProfileImpl();
        p.setParameter(Profile.GUI, "true");

        ContainerController cc = rt.createMainContainer(p);

        try {
            AgentController machine = cc.createNewAgent(
                    "machine",
                    "tt.twin_scheduler.MachineAgent",
                    null
            );
            AgentController scheduler = cc.createNewAgent(
                    "scheduler",
                    "tt.twin_scheduler.SchedulerAgent",
                    null
            );

            machine.start();
            scheduler.start();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
