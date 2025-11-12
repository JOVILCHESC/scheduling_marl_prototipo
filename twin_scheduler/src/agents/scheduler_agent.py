from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import asyncio

class SchedulerAgent(Agent):
    class AssignBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"✅ {self.agent.name} asignando trabajos...")
            for m in self.agent.machine_list:
                msg = Message(to=m)
                msg.set_metadata("performative", "request")
                msg.body = f"Procesa Job_X en {m}"
                await self.send(msg)
                print(f"[{self.agent.name}] asignó trabajo a {m}")

            # Escucha confirmaciones
            while True:
                reply = await self.receive(timeout=10)
                if reply:
                    print(f"[{self.agent.name}] recibió: {reply.body}")
                else:
                    print(f"[{self.agent.name}] sin mensajes nuevos.")
                    break

        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print(f"✅ Scheduler {self.name} activo.")
        b = self.AssignBehaviour()
        self.add_behaviour(b)
