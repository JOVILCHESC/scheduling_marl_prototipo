"""
Script de entrenamiento para el agente JADE usando el simulador dinámico.
Ejecuta la simulación con la regla de despacho 'JADE', lo que activa
la comunicación vía ZeroMQ para la toma de decisiones y feedback.
"""
import simpy
import random
import numpy as np
from simulator_dynamic import DynamicJobShopSimulator

def run_training_episode(episode_id, duration=1000):
    env = simpy.Environment()
    
    # Configuración del entorno
    num_machines = 6  # Ejemplo: FT06 tiene 6 máquinas
    arrival_rate = 0.5
    
    print(f"--- Iniciando Episodio {episode_id} ---")
    
    sim = DynamicJobShopSimulator(
        env=env,
        num_machines=num_machines,
        arrival_rate=arrival_rate,
        scheduling_rule="JADE",  # Activa el agente externo
        random_seed=42 + episode_id,
        training=True
    )
    
    env.run(until=duration)
    
    # Calcular métricas básicas del episodio
    completed = len(sim.jobs_completed)
    print(f"--- Fin Episodio {episode_id} | Completados: {completed} ---")

if __name__ == "__main__":
    NUM_EPISODES = 20
    EPISODE_DURATION = 2000
    
    print(f"Iniciando entrenamiento por {NUM_EPISODES} episodios de {EPISODE_DURATION} u.t. cada uno.")
    
    for i in range(1, NUM_EPISODES + 1):
        run_training_episode(i, duration=EPISODE_DURATION)
