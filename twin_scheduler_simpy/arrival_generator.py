"""
MÓDULO: Generador de Llegadas en Línea

Simula la llegada dinámica de órdenes de trabajo durante la simulación.
Utiliza procesos de Poisson para generar llegadas realistas.

Características:
  - Distribución Poisson de inter-arrival times
  - Generación de órdenes con operaciones aleatorias
  - Control de tasa de llegada (λ)
  - Integración con SimPy
"""

import simpy
import random
import numpy as np
from typing import List, Tuple, Dict, Callable
from dataclasses import dataclass


@dataclass
class JobSpec:
    """Especificación de un trabajo generado dinámicamente."""
    job_id: int
    arrival_time: float
    operations: List[Tuple[int, int]]  # [(machine_id, duration), ...]
    due_date: float = None


class ArrivalGenerator:
    """Genera órdenes de trabajo con llegadas dinámicas."""
    
    def __init__(self, env: simpy.Environment, 
                 arrival_rate: float = 0.5,
                 num_machines: int = 6,
                 min_operations: int = 3,
                 max_operations: int = 6,
                 min_duration: int = 1,
                 max_duration: int = 10,
                 due_date_multiplier: float = 1.5):
        """
        Args:
            env: Entorno SimPy
            arrival_rate: Tasa de llegada λ (trabajos por unidad de tiempo)
            num_machines: Número de máquinas disponibles
            min_operations: Mínimo de operaciones por trabajo
            max_operations: Máximo de operaciones por trabajo
            min_duration: Duración mínima de una operación
            max_duration: Duración máxima de una operación
            due_date_multiplier: Multiplicador para fecha de entrega (vs makespan estimado)
        """
        self.env = env
        self.arrival_rate = arrival_rate
        self.num_machines = num_machines
        self.min_operations = min_operations
        self.max_operations = max_operations
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.due_date_multiplier = due_date_multiplier
        
        self.job_counter = 0
        self.jobs_generated = []
        self.arrival_callback = None  # Callback para notificar nuevas llegadas
    
    def set_arrival_callback(self, callback: Callable[[JobSpec], None]):
        """Registra callback para ser llamado cuando llega una orden."""
        self.arrival_callback = callback
    
    def generate_job_operations(self) -> List[Tuple[int, int]]:
        """
        Genera una secuencia aleatoria de operaciones.
        
        Returns:
            Lista de (machine_id, duration)
        """
        num_ops = random.randint(self.min_operations, self.max_operations)
        machines = random.sample(range(self.num_machines), min(num_ops, self.num_machines))
        
        operations = [
            (machine, random.randint(self.min_duration, self.max_duration))
            for machine in machines
        ]
        return operations
    
    def calculate_due_date(self, arrival_time: float, operations: List[Tuple[int, int]]) -> float:
        """
        Calcula fecha de entrega estimada basada en suma de operaciones.
        
        Args:
            arrival_time: Momento de llegada del trabajo
            operations: Operaciones del trabajo
        
        Returns:
            Due date = arrival_time + sum(operations) * multiplier
        """
        total_processing = sum(duration for _, duration in operations)
        return arrival_time + total_processing * self.due_date_multiplier
    
    def arrival_process(self):
        """
        Proceso SimPy que genera llegadas de trabajos.
        Implementa un proceso de Poisson.
        """
        while True:
            # Tiempo hasta próxima llegada: distribución exponencial
            inter_arrival_time = np.random.exponential(1.0 / self.arrival_rate)
            yield self.env.timeout(inter_arrival_time)
            
            # Crear nuevo trabajo
            self.job_counter += 1
            operations = self.generate_job_operations()
            arrival_time = self.env.now
            due_date = self.calculate_due_date(arrival_time, operations)
            
            job = JobSpec(
                job_id=self.job_counter,
                arrival_time=arrival_time,
                operations=operations,
                due_date=due_date
            )
            
            self.jobs_generated.append(job)
            
            # Notificar al callback si está registrado
            if self.arrival_callback:
                self.arrival_callback(job)
    
    def start(self):
        """Inicia el proceso de generación de llegadas."""
        self.env.process(self.arrival_process())
    
    def get_generated_jobs(self) -> List[JobSpec]:
        """Retorna lista de trabajos generados hasta el momento."""
        return self.jobs_generated.copy()
    
    def reset(self):
        """Resetea el generador de llegadas."""
        self.job_counter = 0
        self.jobs_generated = []


# ============================================================================
# FUNCIONES AUXILIARES PARA DISTRIBUCIONES
# ============================================================================

def inter_arrival_time_poisson(lambda_rate: float) -> float:
    """
    Genera inter-arrival time con distribución exponencial (proceso Poisson).
    
    Args:
        lambda_rate: Tasa de llegada (trabajos por unidad de tiempo)
    
    Returns:
        Tiempo hasta próxima llegada
    """
    return np.random.exponential(1.0 / lambda_rate)


def inter_arrival_time_normal(mean: float, std: float) -> float:
    """
    Genera inter-arrival time con distribución normal.
    
    Args:
        mean: Media del inter-arrival time
        std: Desviación estándar
    
    Returns:
        Tiempo hasta próxima llegada (mínimo 0)
    """
    return max(0, np.random.normal(mean, std))
