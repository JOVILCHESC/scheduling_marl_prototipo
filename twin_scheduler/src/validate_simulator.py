import os
import json
import simpy
from core.environment import ManufacturingEnv

def run_simulation(rule):
    base_path = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_path, "data")
    config_path = os.path.join(data_path, "machines_config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    env = simpy.Environment()
    system = ManufacturingEnv(env, config)
    system.sort_jobs(rule)
    system.initialize_jobs()
    env.run(until=system.simulation_time)
    makespan, tardanza, wip, util = system.compute_metrics()

    return {"rule": rule, "makespan": makespan, "tardanza": tardanza, "wip": wip, "util": util}

if __name__ == "__main__":
    rules = ["SPT", "EDD", "LPT"]
    results = []

    print("\n[INFO] === VALIDACIÓN DEL SIMULADOR ===\n")

    for r in rules:
        print(f"\n[INFO] Ejecutando simulación con regla {r}...")
        res = run_simulation(r)
        results.append(res)

    print("\n=== RESULTADOS COMPARATIVOS ===")
    print(f"{'Regla':<10}{'Makespan':<10}{'Tardanza':<12}{'WIP':<10}{'Utilización'}")
    for r in results:
        print(f"{r['rule']:<10}{r['makespan']:<10.2f}{r['tardanza']:<12.2f}{r['wip']:<10.2f}{r['util']:.2f}")

    # Guardar CSV con resultados
    base_path = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_path, "data")
    out_path = os.path.join(data_path, "validation_results.csv")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Regla,Makespan,Tardanza,WIP,Utilizacion\n")
        for r in results:
            f.write(f"{r['rule']},{r['makespan']},{r['tardanza']},{r['wip']:.3f},{r['util']:.3f}\n")

    print(f"\n[INFO] Resultados guardados en: {out_path}")
