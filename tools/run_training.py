import os
import sys
import time
import csv
from datetime import datetime
import simpy

# Asegurar import del paquete
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from twin_scheduler_simpy.simulator_dynamic import DynamicJobShopSimulator


def run_episode(sim_time=120.0, warmup=10.0, arrival_rate=0.4, seed=None, scheduling_rule="SPT"):
    env = simpy.Environment()
    sim = DynamicJobShopSimulator(
        env=env,
        num_machines=6,
        arrival_rate=arrival_rate,
        mtbf=100.0,
        mttr=8.0,
        scheduling_rule=scheduling_rule,
        random_seed=seed,
    )
    sim.run(until_time=sim_time, warmup=warmup)
    # métricas agregadas desde jobs_completed
    if sim.jobs_completed:
        makespans = [j['makespan'] for j in sim.jobs_completed.values()]
        tardiness = [j['tardiness'] for j in sim.jobs_completed.values()]
        makespan_promedio = sum(makespans) / len(makespans) if makespans else 0.0
        tardanza_total = sum(tardiness)
        trabajos_atrasados = len([t for t in tardiness if t > 0])
        jobs_completados = len(sim.jobs_completed)
    else:
        makespan_promedio = 0.0
        tardanza_total = 0.0
        trabajos_atrasados = 0
        jobs_completados = 0
    
    metrics = {
        'makespan_promedio': makespan_promedio,
        'tardanza_total': tardanza_total,
        'trabajos_atrasados': trabajos_atrasados,
        'jobs_completados': jobs_completados,
    }
    # reward aproximado: negativo de tardanza_total
    metrics['reward'] = -float(metrics['tardanza_total'])
    return metrics


def run_training(episodes=50, sim_time=120.0, warmup=10.0, arrival_rate=0.4, out_dir='training_logs', scheduling_rule="SPT", filename=None):
    os.makedirs(out_dir, exist_ok=True)
    if filename:
        csv_path = os.path.join(out_dir, filename)
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join(out_dir, f'training_{scheduling_rule}_{ts}.csv')

    fields = ['episode', 'reward', 'tardanza_total', 'makespan_promedio', 'jobs_completados', 'trabajos_atrasados']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for ep in range(1, episodes+1):
            # semilla determinista basada en episodio para comparabilidad
            seed = 42000 + ep
            metrics = run_episode(sim_time=sim_time, warmup=warmup, arrival_rate=arrival_rate, seed=seed, scheduling_rule=scheduling_rule)
            row = {
                'episode': ep,
                **metrics,
            }
            writer.writerow(row)
            print(f"[EP {ep:03d}] [{scheduling_rule}] reward={row['reward']:.2f} tardanza={row['tardanza_total']:.2f} makespan={row['makespan_promedio']:.2f} jobs={row['jobs_completados']}")
    print(f"[OK] Log CSV: {csv_path}")
    return csv_path


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Runner multi-episodios')
    p.add_argument('--episodes', type=int, default=50)
    p.add_argument('--sim-time', type=float, default=120.0)
    p.add_argument('--warmup', type=float, default=10.0)
    p.add_argument('--arrival-rate', type=float, default=0.4)
    p.add_argument('--rule', type=str, default='SPT', help='Regla de despacho: SPT, LPT, EDD, JADE')
    p.add_argument('--out', type=str, default=None, help='Nombre archivo salida (opcional)')
    args = p.parse_args()

    run_training(episodes=args.episodes, sim_time=args.sim_time, warmup=args.warmup, 
                 arrival_rate=args.arrival_rate, scheduling_rule=args.rule, filename=args.out)
