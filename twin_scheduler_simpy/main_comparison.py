"""
Script de Comparación: Fase 1 vs Fase 2

Ejecuta ambas fases (simulador estático y dinámico) con la misma instancia Taillard
y genera un reporte comparativo completo.

Uso:
    python main_comparison.py [--dataset TA:datasets/jobshop1.txt:1] [--rules SPT,EDD,LPT]
    
Ejemplos:
    # Comparar con la primera instancia de jobshop1.txt, todas las reglas
    python main_comparison.py
    
    # Comparar solo con SPT
    python main_comparison.py --rules SPT
    
    # Usar una instancia diferente (si existe)
    python main_comparison.py --dataset TA:datasets/jobshop1.txt:abz5 --rules SPT,EDD
"""

import sys
import argparse
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

# Intentar imports relativos; si falla, usar imports directos
try:
    from .datasets import Datasets
    from .simulator_static import run_simulation
    from .taillard_integration import convert_taillard_to_staggered_arrivals, print_staggered_arrivals
    from .simulator_dynamic import DynamicJobShopSimulator
except ImportError:
    from datasets import Datasets
    from simulator_static import run_simulation
    from taillard_integration import convert_taillard_to_staggered_arrivals, print_staggered_arrivals
    from simulator_dynamic import DynamicJobShopSimulator

import simpy


def run_phase1_batch(
    jobs_data: List[List[Tuple[int, int]]],
    due_dates: Dict[int, float],
    rules: List[str],
    dataset_name: str = "TA_jobshop1"
) -> Dict[str, Dict]:
    """
    Ejecuta Fase 1 (simulador estático) con múltiples reglas.
    
    Returns:
        Diccionario {regla: {métricas}}
    """
    print("\n" + "="*80)
    print("FASE 1: SIMULADOR ESTÁTICO (Determinístico)")
    print("="*80)
    
    results_phase1 = {}
    
    for rule in rules:
        print(f"\n[FASE 1] Ejecutando regla: {rule}")
        try:
            result = run_simulation(
                jobs_data,
                due_dates,
                rule=rule,
                dataset_name=dataset_name,
                verbose=False,
                export_log=False
            )
            results_phase1[rule] = result['metrics']
            print(f"[FASE 1] {rule}: OK - Makespan={result['metrics']['makespan']:.1f}, "
                  f"Tardanza={result['metrics']['tardiness_total']:.1f}")
        except Exception as e:
            import traceback
            print(f"[FASE 1] {rule}: ERROR - {e}")
            traceback.print_exc()
            results_phase1[rule] = None
    
    return results_phase1


def run_phase2_batch(
    jobs_data: List[List[Tuple[int, int]]],
    due_dates: Dict[int, float],
    rules: List[str],
    dataset_name: str = "TA_jobshop1",
    mtbf: float = 150.0,
    mttr: float = 10.0,
    total_time: float = 2000.0,
    arrival_distribution: str = "uniform"
) -> Dict[str, Dict]:
    """
    Ejecuta Fase 2 (simulador dinámico) con los mismos datos como backlog escalonado.
    
    Returns:
        Diccionario {regla: {métricas dinámicas}}
    """
    print("\n" + "="*80)
    print("FASE 2: SIMULADOR DINÁMICO (Con Fallos y Llegadas Escalonadas)")
    print("="*80)
    
    results_phase2 = {}
    
    # Convertir jobs Taillard a llegadas escalonadas
    staggered_jobs = convert_taillard_to_staggered_arrivals(
        jobs_data,
        due_dates,
        total_simulation_time=total_time,
        arrival_distribution=arrival_distribution,
        seed=42
    )
    print_staggered_arrivals(staggered_jobs, "Conversión Taillard a Llegadas Escalonadas")
    
    # Detectar número de máquinas
    num_machines = len(set(m for job in jobs_data for m, _ in job))
    
    for rule in rules:
        print(f"\n[FASE 2] Ejecutando con llegadas escalonadas: {rule}")
        try:
            env = simpy.Environment()
            
            simulator = DynamicJobShopSimulator(
                env=env,
                num_machines=num_machines,
                arrival_rate=0.0,  # No usar generador automático; usaremos backlog
                mtbf=mtbf,
                mttr=mttr,
                scheduling_rule=rule,
                random_seed=42
            )
            
            # Inyectar jobs como backlog escalonado
            for job in staggered_jobs:
                simulator.env.process(simulator._process_job(job))
            
            # Iniciar generador de fallos
            simulator.failure_manager.start_failure_simulation()
            
            # Ejecutar simulación
            simulator.env.run(until=total_time)
            
            # Recolectar métricas
            metrics = {
                'makespan': max([j['completion_time'] for j in simulator.jobs_completed.values()]) if simulator.jobs_completed else 0,
                'tardiness_total': sum([j['tardiness'] for j in simulator.jobs_completed.values()]) if simulator.jobs_completed else 0,
                'tardiness_average': np.mean([j['tardiness'] for j in simulator.jobs_completed.values()]) if simulator.jobs_completed else 0,
                'jobs_completed': len(simulator.jobs_completed),
                'total_events': len(simulator.event_manager.events),
                'total_downtime': sum([
                    simulator.failure_manager.get_failure_stats(m)['total_downtime']
                    for m in range(num_machines)
                ]),
                'availability_avg': np.mean([
                    simulator.failure_manager.get_failure_stats(m)['availability']
                    for m in range(num_machines)
                ])
            }
            results_phase2[rule] = metrics
            
            print(f"[FASE 2] {rule}: OK - Makespan={metrics['makespan']:.1f}, "
                  f"Tardanza={metrics['tardiness_total']:.1f}, "
                  f"Downtime={metrics['total_downtime']:.1f}")
        except Exception as e:
            print(f"[FASE 2] {rule}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            results_phase2[rule] = None
    
    return results_phase2


def generate_comparison_report(
    results_phase1: Dict[str, Dict],
    results_phase2: Dict[str, Dict],
    rules: List[str]
) -> pd.DataFrame:
    """
    Genera tabla comparativa Fase 1 vs Fase 2.
    """
    comparison_data = []
    
    for rule in rules:
        m1 = results_phase1.get(rule)
        m2 = results_phase2.get(rule)
        
        if m1 is None or m2 is None:
            continue
        
        # Calcular deltas
        makespan_delta = m2['makespan'] - m1['makespan']
        makespan_delta_pct = (makespan_delta / m1['makespan'] * 100) if m1['makespan'] > 0 else 0
        
        tardiness_delta = m2['tardiness_total'] - m1['tardiness_total']
        tardiness_delta_pct = (tardiness_delta / m1['tardiness_total'] * 100) if m1['tardiness_total'] > 0 else 0
        
        comparison_data.append({
            'Regla': rule,
            'Makespan F1': f"{m1['makespan']:.1f}",
            'Makespan F2': f"{m2['makespan']:.1f}",
            'Delta Makespan': f"{makespan_delta:+.1f} ({makespan_delta_pct:+.1f}%)",
            'Tardanza F1': f"{m1['tardiness_total']:.1f}",
            'Tardanza F2': f"{m2['tardiness_total']:.1f}",
            'Delta Tardanza': f"{tardiness_delta:+.1f} ({tardiness_delta_pct:+.1f}%)",
            'Jobs Compl. F2': m2['jobs_completed'],
            'Downtime F2 (u.t.)': f"{m2['total_downtime']:.1f}",
            'Disponibilidad F2': f"{m2['availability_avg']:.1f}%",
        })
    
    return pd.DataFrame(comparison_data)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Comparar Fase 1 (estático) vs Fase 2 (dinámico) con instancias Taillard"
    )
    parser.add_argument(
        "--dataset",
        default="TA:datasets/jobshop1.txt:1",
        help="Dataset Taillard (formato TA:archivo:instancia). Ej: TA:datasets/jobshop1.txt:1"
    )
    parser.add_argument(
        "--rules",
        default="SPT,EDD,LPT",
        help="Reglas a probar, separadas por coma. Ej: SPT,EDD,LPT"
    )
    parser.add_argument(
        "--mtbf",
        type=float,
        default=150.0,
        help="Mean Time Between Failures (Fase 2)"
    )
    parser.add_argument(
        "--mttr",
        type=float,
        default=10.0,
        help="Mean Time To Repair (Fase 2)"
    )
    parser.add_argument(
        "--arrival-dist",
        default="uniform",
        choices=["uniform", "poisson"],
        help="Distribución de llegadas escalonadas (Fase 2)"
    )
    
    args = parser.parse_args()
    
    rules = [r.strip().upper() for r in args.rules.split(",")]
    
    # Cargar dataset Taillard
    print(f"Cargando dataset: {args.dataset}")
    try:
        jobs_data, due_dates = Datasets.load_dataset(args.dataset)
        print(f"Dataset cargado: {len(jobs_data)} jobs, "
              f"{len(set(m for job in jobs_data for m, _ in job))} máquinas")
    except Exception as e:
        print(f"ERROR cargando dataset: {e}")
        sys.exit(1)
    
    # Fase 1
    results_phase1 = run_phase1_batch(jobs_data, due_dates, rules, args.dataset)
    
    # Fase 2
    num_machines = len(set(m for job in jobs_data for m, _ in job))
    total_time = sum(sum(d for _, d in job) for job in jobs_data) * 3.0  # Estimación
    
    results_phase2 = run_phase2_batch(
        jobs_data,
        due_dates,
        rules,
        args.dataset,
        mtbf=args.mtbf,
        mttr=args.mttr,
        total_time=total_time,
        arrival_distribution=args.arrival_dist
    )
    
    # Generar reporte comparativo
    df_comparison = generate_comparison_report(results_phase1, results_phase2, rules)
    
    print("\n" + "="*80)
    print("REPORTE COMPARATIVO: FASE 1 vs FASE 2")
    print("="*80)
    print(df_comparison.to_string(index=False))
    print("="*80 + "\n")
    
    # Exportar a CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"comparison_report_{timestamp}.csv"
    df_comparison.to_csv(csv_file, index=False)
    print(f"Reporte exportado: {csv_file}\n")


if __name__ == "__main__":
    main()
