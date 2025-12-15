"""
Script de ejecución en modo 'Mirroring' (Espejo).
Ejecuta la simulación con una regla simple (SPT) y notifica eventos a JADE.
Esto permite que JADE mantenga un Gemelo Digital del estado de la simulación.
"""
import simpy
from simulator_dynamic import DynamicJobShopSimulator

def run_mirroring_episode(duration=2000):
    env = simpy.Environment()
    
    # Configuración del entorno
    num_machines = 6
    arrival_rate = 0.5
    
    print(f"--- Iniciando Simulación en Modo Mirroring ---")
    
    sim = DynamicJobShopSimulator(
        env=env,
        num_machines=num_machines,
        arrival_rate=arrival_rate,
        scheduling_rule="SPT",  # Regla simple para la simulación física
        random_seed=42,
        training=False,
        mirroring=True  # Activa notificaciones a JADE
    )
    
    env.run(until=duration)
    
    completed = len(sim.jobs_completed)
    print(f"--- Fin Simulación | Completados: {completed} ---")

if __name__ == "__main__":
    run_mirroring_episode()
