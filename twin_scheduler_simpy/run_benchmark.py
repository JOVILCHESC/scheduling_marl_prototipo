import simpy
import pandas as pd
import sys
import os

# Asegurar que el directorio raíz está en el path para imports
sys.path.append(os.getcwd())

from twin_scheduler_simpy.simulator_dynamic import DynamicJobShopSimulator

def run_benchmark():
    # Reglas a comparar. JADE requiere que el servidor Java esté corriendo.
    rules = ["SPT", "LPT", "EDD", "JADE"]
    results = []
    
    print("\n--- Iniciando Benchmark de Reglas de Despacho ---")
    print(f"Reglas a evaluar: {', '.join(rules)}")
    print(f"Configuración: Semilla=999, Duración=1000 u.t.")
    print("-" * 70)

    for rule in rules:
        print(f"Ejecutando regla: {rule:<5} ...", end=" ", flush=True)
        
        # Configuración idéntica para todas las reglas para garantizar comparabilidad
        SEED = 999
        DURATION = 1000
        
        env = simpy.Environment()
        
        try:
            sim = DynamicJobShopSimulator(
                env=env,
                num_machines=6,
                scheduling_rule=rule,
                random_seed=SEED, # Importante: Modo evaluación (sin feedback de RL)
                training=False
            )
            
            env.run(until=DURATION)
            
            # Calcular métricas
            completed_jobs = len(sim.jobs_completed)
            if completed_jobs > 0:
                tardiness_vals = [info['tardiness'] for info in sim.jobs_completed.values()]
                # En este simulador, 'makespan' en jobs_completed es el tiempo de flujo del trabajo individual
                flow_time_vals = [info['makespan'] for info in sim.jobs_completed.values()] 
                
                avg_tardiness = sum(tardiness_vals) / completed_jobs
                avg_flow_time = sum(flow_time_vals) / completed_jobs
                max_tardiness = max(tardiness_vals)
            else:
                avg_tardiness = 0
                avg_flow_time = 0
                max_tardiness = 0
            
            results.append({
                "Regla": rule,
                "Completados": completed_jobs,
                "Tardanza Prom.": round(avg_tardiness, 2),
                "Flow Time Prom.": round(avg_flow_time, 2),
                "Max Tardanza": round(max_tardiness, 2)
            })
            print("OK")
            
        except Exception as e:
            print(f"FALLÓ")
            print(f"  Error: {e}")
            results.append({
                "Regla": rule,
                "Completados": 0,
                "Tardanza Prom.": "-",
                "Flow Time Prom.": "-",
                "Max Tardanza": "-"
            })

    print("-" * 70)
    print("RESULTADOS COMPARATIVOS:")
    if results:
        df = pd.DataFrame(results)
        # Ajustar formato de impresión
        print(df.to_string(index=False, justify='center'))
    else:
        print("No se obtuvieron resultados.")
    print("-" * 70)

if __name__ == "__main__":
    run_benchmark()
