"""
Módulo de integración Taillard para Fase 2 (simulador dinámico).

Proporciona funciones para convertir instancias Taillard en llegadas escalonadas
(Opción B) que alimentan el simulador dinámico. Permite comparación directa 
entre Fase 1 (estático) y Fase 2 (dinámico) usando los mismos datos.
"""
from typing import List, Tuple, Dict, Optional
from arrival_generator import JobSpec
import numpy as np


def convert_taillard_to_staggered_arrivals(
    jobs_data: List[List[Tuple[int, int]]],
    due_dates: Dict[int, float],
    total_simulation_time: float = 1000.0,
    arrival_distribution: str = "uniform",
    seed: int = 42
) -> List[JobSpec]:
    """
    Convierte jobs de instancia Taillard en llegadas escalonadas.
    
    Opción B: Los jobs de Taillard se convierten en llegadas dinámicas distribuidas
    a lo largo del tiempo de simulación, manteniendo operaciones y due_dates originales.
    
    Args:
        jobs_data: Lista de jobs Taillard [(machine, duration), ...]
        due_dates: Diccionario {job_id: due_date}
        total_simulation_time: Tiempo total de la simulación
        arrival_distribution: "uniform" (distribuye uniformemente) o "poisson" (proceso Poisson)
        seed: Seed para reproducibilidad
    
    Returns:
        Lista de JobSpec con arrival_time distribuidos
    """
    np.random.seed(seed)
    
    num_jobs = len(jobs_data)
    arrival_times = []
    
    if arrival_distribution == "uniform":
        # Distribuir uniformemente los jobs a lo largo de la simulación
        arrival_times = np.linspace(0, total_simulation_time * 0.8, num_jobs)
    elif arrival_distribution == "poisson":
        # Proceso Poisson: inter-arrival times exponenciales
        lambda_rate = num_jobs / (total_simulation_time * 0.8)
        inter_arrivals = np.random.exponential(1.0 / lambda_rate, num_jobs)
        arrival_times = np.cumsum(inter_arrivals)
        # Recortar si algunos llegan después del final
        arrival_times = [t for t in arrival_times if t < total_simulation_time]
        # Rellenar si faltan (ajustar número de jobs)
        while len(arrival_times) < num_jobs:
            arrival_times.append(arrival_times[-1] + 10.0)
        arrival_times = arrival_times[:num_jobs]
    else:
        raise ValueError(f"Distribución desconocida: {arrival_distribution}")
    
    jobs = []
    for jid, (arrival_time, operations) in enumerate(zip(arrival_times, jobs_data)):
        # Ajustar due_date: si en Taillard era (1.5 * suma_operaciones),
        # en dinámico sumamos el arrival_time
        original_due = due_dates.get(jid, 0)
        adjusted_due = arrival_time + original_due
        
        job = JobSpec(
            job_id=jid,
            arrival_time=arrival_time,
            operations=operations,
            due_date=adjusted_due
        )
        jobs.append(job)
    
    return jobs


def print_staggered_arrivals(jobs: List[JobSpec], title: str = "Llegadas Escalonadas"):
    """Imprime información de las llegadas escalonadas."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"Total jobs: {len(jobs)}")
    print(f"\nPrimeros 10 jobs:")
    for job in jobs[:10]:
        ops_str = ", ".join([f"M{m}:{d}" for m, d in job.operations[:3]])
        if len(job.operations) > 3:
            ops_str += f", +{len(job.operations)-3} more"
        print(f"  Job {job.job_id:3d}: arrives={job.arrival_time:7.1f}, "
              f"due={job.due_date:7.1f}, ops=[{ops_str}]")
    
    if len(jobs) > 10:
        print(f"\n  ... ({len(jobs) - 10} más)")
    
    print(f"\nArrival timeline:")
    print(f"  Primer job: t={min(j.arrival_time for j in jobs):.1f}")
    print(f"  Último job:  t={max(j.arrival_time for j in jobs):.1f}")
    print(f"{'='*70}\n")
