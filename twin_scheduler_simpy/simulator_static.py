"""
FASE 1: SIMULADOR BASE (Entorno Estático)

Simulador Job Shop determinístico con SimPy.
Implementa:
  - Máquinas con recursos y colas (buffers)
  - Trabajos con operaciones en secuencia
  - Reglas de despacho: SPT, EDD, LPT
  - Cálculo de métricas: Makespan, Tardanza, VIP, Utilización
  - Validación y comparación de resultados

Datasets: FT06 (6x6), FT10 (10x10)
"""

import simpy
import pandas as pd
import os
from datetime import datetime
from typing import List, Tuple, Dict

from .metrics import MetricsCalculator
from .scheduling_rules import SchedulingRules
from .datasets import Datasets


class Machine:
    """Representa una máquina en el job shop."""
    
    def __init__(self, env: simpy.Environment, machine_id: int):
        """
        Args:
            env: Entorno SimPy
            machine_id: Identificador único de la máquina
        """
        self.env = env
        self.id = machine_id
        self.resource = simpy.Resource(env, capacity=1)  # Una operación a la vez
        self.queue = []  # Buffer de trabajos esperando
    
    def process(self, job_id: int, duration: int):
        """
        Procesa una operación durante `duration` unidades de tiempo.
        
        Args:
            job_id: ID del trabajo
            duration: Duración de la operación en unidades de tiempo
        """
        yield self.env.timeout(duration)


class Job:
    """Representa un trabajo con una secuencia de operaciones."""
    
    def __init__(self, job_id: int, operations: List[Tuple[int, int]]):
        """
        Args:
            job_id: Identificador único del trabajo
            operations: Lista de (machine_id, duration)
        """
        self.id = job_id
        self.operations = operations
        self.arrival_time = None
        self.completion_time = None


def job_process(env: simpy.Environment, job: Job, machines: List[Machine], 
                log: List[List], verbose: bool = True):
    """
    Simula todas las operaciones de un job en secuencia.
    
    Args:
        env: Entorno SimPy
        job: Objeto Job a procesar
        machines: Lista de máquinas disponibles
        log: Lista para registrar eventos [time, event, job, machine]
        verbose: Si True, imprime eventos
    """
    job.arrival_time = env.now
    
    for op_idx, (machine_id, duration) in enumerate(job.operations):
        machine = machines[machine_id]
        
        # Agregar a la cola de la máquina
        machine.queue.append(job.id)
        
        # Solicitar acceso a la máquina
        with machine.resource.request() as req:
            yield req
            
            # Remover de la cola
            if job.id in machine.queue:
                machine.queue.remove(job.id)
            
            start_time = env.now
            log.append([env.now, "start", job.id, machine_id])
            
            if verbose:
                queue_size = len(machine.queue)
                print(f"[{env.now:6.1f}] ⚙️  Job {job.id:2d} Operación {op_idx} en Máquina {machine_id} "
                      f"({duration} u.t.) [Cola: {queue_size}]")
            
            # Procesar
            yield env.process(machine.process(job.id, duration))
            
            # Registrar finalización
            log.append([env.now, "finish", job.id, machine_id])
            
            if verbose:
                print(f"[{env.now:6.1f}] ✓ Job {job.id:2d} Operación {op_idx} completada en "
                      f"Máquina {machine_id}")
    
    job.completion_time = env.now


def run_simulation(jobs_data: List[List[Tuple[int, int]]], 
                  due_dates: Dict[int, float],
                  rule: str = "SPT",
                  dataset_name: str = "",
                  verbose: bool = True,
                  export_log: bool = True) -> Dict:
    """
    Ejecuta una simulación del Job Shop.
    
    Args:
        jobs_data: Lista de trabajos con operaciones
        due_dates: Diccionario {job_id: due_date}
        rule: Regla de despacho ('SPT', 'EDD', 'LPT')
        dataset_name: Nombre del dataset (para reportes)
        verbose: Si True, imprime eventos de simulación
        export_log: Si True, exporta log a CSV
    
    Returns:
        Diccionario con métricas de la simulación
    """
    
    # === CREAR ENTORNO ===
    env = simpy.Environment()
    
    # === APLICAR REGLA DE DESPACHO ===
    ordered_indices, rule_desc = SchedulingRules.apply_rule(rule, jobs_data, due_dates)
    
    # Reordenar trabajos según la regla
    ordered_jobs = [jobs_data[i] for i in ordered_indices]
    
    # Mostrar información de la regla
    SchedulingRules.print_schedule(rule, ordered_indices, jobs_data, due_dates)
    
    # === CREAR MÁQUINAS ===
    num_machines = len(set(m for job in jobs_data for m, _ in job))
    machines = [Machine(env, i) for i in range(num_machines)]
    
    # === CREAR TRABAJOS ===
    jobs = [Job(ordered_indices[i], ordered_jobs[i]) for i in range(len(ordered_jobs))]
    
    # === EVENTO LOG ===
    log = []
    
    # === INICIAR PROCESOS ===
    print(f"\n{'='*70}")
    print(f"🚀 INICIANDO SIMULACIÓN - REGLA: {rule}")
    print(f"{'='*70}\n")
    
    for job in jobs:
        env.process(job_process(env, job, machines, log, verbose=verbose))
    
    # === EJECUTAR SIMULACIÓN ===
    env.run()
    
    # === CALCULAR MÉTRICAS ===
    metrics_calc = MetricsCalculator(log, jobs_data, due_dates)
    metrics = metrics_calc.print_metrics(rule_name=rule)
    
    # === EXPORTAR LOG ===
    if export_log:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"simulation_log_{rule}_{timestamp}.csv"
        df = pd.DataFrame(log, columns=["time", "event", "job", "machine"])
        df.to_csv(log_filename, index=False)
        print(f"[INFO] Log exportado a: {log_filename}\n")
    
    # === RETORNAR RESULTADOS ===
    results = {
        "rule": rule,
        "dataset": dataset_name,
        "metrics": metrics,
        "log": log,
        "jobs_completed": len(jobs)
    }
    
    return results


def run_validation(dataset_name: str = "FT06", verbose: bool = False):
    """
    Ejecuta validación comparativa del simulador con múltiples reglas.
    
    Args:
        dataset_name: Nombre del dataset a usar
        verbose: Si True, muestra detalles de la simulación
    """
    
    # === CARGAR DATASET ===
    try:
        jobs_data, due_dates = Datasets.load_dataset(dataset_name)
    except ValueError as e:
        print(f"[ERROR] {e}")
        print(f"Datasets disponibles: {', '.join(Datasets.get_available_datasets().keys())}")
        return
    
    # Mostrar información del dataset
    Datasets.print_dataset_info(jobs_data, due_dates, dataset_name)
    
    # === EJECUTAR SIMULACIONES ===
    rules = ["SPT", "EDD", "LPT"]
    results = []
    
    print(f"\n{'='*70}")
    print(f"📊 VALIDACIÓN DEL SIMULADOR BASE")
    print(f"{'='*70}\n")
    
    for rule in rules:
        print(f"\n{'─'*70}")
        print(f"Ejecutando simulación con regla {rule}...")
        print(f"{'─'*70}\n")
        
        result = run_simulation(
            jobs_data,
            due_dates,
            rule=rule,
            dataset_name=dataset_name,
            verbose=verbose,
            export_log=True
        )
        
        results.append(result)
    
    # === COMPARACIÓN DE RESULTADOS ===
    print(f"\n{'='*70}")
    print(f"📈 COMPARACIÓN DE REGLAS")
    print(f"{'='*70}\n")
    
    comparison_data = []
    for result in results:
        m = result["metrics"]
        comparison_data.append({
            "Regla": result["rule"],
            "Makespan": f"{m['makespan']:.2f}",
            "Tardanza Total": f"{m['tardiness_total']:.2f}",
            "Tardanza Promedio": f"{m['tardiness_average']:.2f}",
            "VIP": f"{m['vip']:.2f}",
            "Utilización %": f"{m['utilization_average']:.2f}"
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    print(df_comparison.to_string(index=False))
    print(f"\n{'='*70}\n")
    
    # === GUARDAR RESULTADOS ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"validation_results_{dataset_name}_{timestamp}.csv"
    df_comparison.to_csv(results_filename, index=False)
    print(f"[INFO] Resultados guardados en: {results_filename}\n")
    
    return results


if __name__ == "__main__":
    # === EJECUTAR VALIDACIÓN DEL SIMULADOR BASE ===
    run_validation(dataset_name="FT06", verbose=False)
