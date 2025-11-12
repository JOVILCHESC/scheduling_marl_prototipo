from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

class MachineAgent(Agent):
    class ProcessBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)  # espera mensajes del scheduler
            if msg:
                print(f"[{self.name}] recibió tarea: {msg.body}")
                await asyncio.sleep(2)  # simula procesamiento
                reply = Message(to=str(msg.sender))
                reply.set_metadata("performative", "inform")
                reply.body = f"Tarea completada por {self.name}"
                await self.send(reply)
            else:
                await asyncio.sleep(1)

    async def setup(self):
        print(f"✅ Agente máquina {self.name} inicializado.")
        self.add_behaviour(self.ProcessBehaviour())
