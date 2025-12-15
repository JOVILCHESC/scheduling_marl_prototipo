"""
Script de TEST para el agente JADE usando el simulador dinámico.
Ejecuta la simulación con la regla de despacho 'JADE' en modo EVALUACIÓN (sin entrenamiento).
"""
import simpy
import random
import numpy as np
from simulator_dynamic import DynamicJobShopSimulator

def run_test_episode(duration=500):
    env = simpy.Environment()
    
    # Configuración del entorno
    num_machines = 6
    arrival_rate = 0.5
    
    print(f"--- Iniciando TEST (Evaluación) ---")
    print(f"Duración: {duration} u.t.")
    print(f"Regla: JADE (ZeroMQ)")
    print(f"Entrenamiento: DESACTIVADO (Solo explotación)")
    
    sim = DynamicJobShopSimulator(
        env=env,
        num_machines=num_machines,
        arrival_rate=arrival_rate,
        scheduling_rule="JADE",
        random_seed=999, # Seed diferente al de entrenamiento
        training=False   # Desactivar feedback/aprendizaje
    )
    
    env.run(until=duration)
    
    print(f"--- Fin TEST ---")
    print(f"Trabajos completados: {len(sim.jobs_completed)}")
    
    # Calcular métricas básicas
    if sim.jobs_completed:
        tardiness = []
        flow_time = []
        for jid, info in sim.jobs_completed.items():
            # info ya contiene los datos calculados por el simulador
            ft = info['makespan'] # Flow time es equivalente a makespan del trabajo individual
            flow_time.append(ft)
            lat = info['tardiness']
            tardiness.append(lat)
        
        if tardiness:
            print(f"Tardanza Promedio: {np.mean(tardiness):.2f}")
            print(f"Flow Time Promedio: {np.mean(flow_time):.2f}")
            print(f"Makespan (aprox): {max([info['completion_time'] for info in sim.jobs_completed.values()]):.2f}")

if __name__ == "__main__":
    run_test_episode(duration=1000)
