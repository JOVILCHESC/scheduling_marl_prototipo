"""
MÓDULO: Gestor de Fallas de Máquinas

Simula fallos en máquinas durante la simulación con distribuciones realistas.
Implementa MTBF (Mean Time Between Failures) y MTTR (Mean Time To Repair).

Características:
  - Fallos basados en distribución exponencial
  - Tiempo de reparación variable
  - Bloqueo de máquina durante reparación
  - Registro de eventos de falla y reparación
  - Estadísticas de disponibilidad por máquina
"""

import simpy
import numpy as np
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass


@dataclass
class MachineFailureEvent:
    """Registro de un evento de falla en máquina."""
    machine_id: int
    failure_time: float
    repair_start_time: float
    repair_duration: float
    repair_end_time: float
    downtime: float  # repair_end_time - failure_time


class MachineFailureManager:
    """Gestiona fallos y reparaciones de máquinas."""
    
    def __init__(self, env: simpy.Environment,
                 num_machines: int,
                 mtbf_mean: float = 100.0,  # Mean Time Between Failures
                 mttr_mean: float = 5.0):   # Mean Time To Repair
        """
        Args:
            env: Entorno SimPy
            num_machines: Número de máquinas
            mtbf_mean: Tiempo medio entre fallos (exponencial)
            mttr_mean: Tiempo medio de reparación (exponencial)
        """
        self.env = env
        self.num_machines = num_machines
        self.mtbf_mean = mtbf_mean
        self.mttr_mean = mttr_mean
        
        # Estado de máquinas
        self.machine_failed = {i: False for i in range(num_machines)}
        self.machine_busy = {i: False for i in range(num_machines)}
        
        # Historial de fallos
        self.failure_events: List[MachineFailureEvent] = []
        
        # Callbacks
        self.on_failure_callback = None
        self.on_repair_callback = None
    
    def set_on_failure_callback(self, callback: Callable[[MachineFailureEvent], None]):
        """Callback cuando ocurre una falla."""
        self.on_failure_callback = callback
    
    def set_on_repair_callback(self, callback: Callable[[MachineFailureEvent], None]):
        """Callback cuando termina una reparación."""
        self.on_repair_callback = callback
    
    def is_machine_failed(self, machine_id: int) -> bool:
        """Verifica si una máquina está en fallo."""
        return self.machine_failed.get(machine_id, False)
    
    def is_machine_busy(self, machine_id: int) -> bool:
        """Verifica si una máquina está ocupada procesando."""
        return self.machine_busy.get(machine_id, False)
    
    def mark_machine_busy(self, machine_id: int, is_busy: bool = True):
        """Marca máquina como ocupada/desocupada."""
        self.machine_busy[machine_id] = is_busy
    
    def failure_process(self, machine_id: int):
        """
        Proceso que simula el ciclo de fallos de una máquina.
        Implementa: Funcionamiento → Fallo → Reparación → Funcionamiento
        """
        while True:
            # Esperar hasta próximo fallo (distribución exponencial)
            time_to_failure = np.random.exponential(self.mtbf_mean)
            yield self.env.timeout(time_to_failure)
            
            # Registrar fallo
            failure_time = self.env.now
            self.machine_failed[machine_id] = True
            
            # Generar tiempo de reparación
            repair_duration = max(1, np.random.exponential(self.mttr_mean))
            repair_start_time = self.env.now
            
            # Notificar fallo
            if self.on_failure_callback:
                event = MachineFailureEvent(
                    machine_id=machine_id,
                    failure_time=failure_time,
                    repair_start_time=repair_start_time,
                    repair_duration=repair_duration,
                    repair_end_time=failure_time + repair_duration,
                    downtime=0  # Se actualiza en reparación
                )
                self.on_failure_callback(event)
            
            # Reparar
            yield self.env.timeout(repair_duration)
            
            # Máquina repuesta
            self.machine_failed[machine_id] = False
            repair_end_time = self.env.now
            downtime = repair_end_time - failure_time
            
            # Registrar evento completo
            event = MachineFailureEvent(
                machine_id=machine_id,
                failure_time=failure_time,
                repair_start_time=repair_start_time,
                repair_duration=repair_duration,
                repair_end_time=repair_end_time,
                downtime=downtime
            )
            self.failure_events.append(event)
            
            # Notificar reparación completada
            if self.on_repair_callback:
                self.on_repair_callback(event)
    
    def start_failure_simulation(self):
        """Inicia los procesos de fallo para todas las máquinas."""
        for machine_id in range(self.num_machines):
            self.env.process(self.failure_process(machine_id))
    
    def get_failure_stats(self, machine_id: int = None) -> Dict:
        """
        Calcula estadísticas de fallos.
        
        Args:
            machine_id: Si es None, retorna estadísticas de todas
        
        Returns:
            Dict con: num_failures, total_downtime, availability, avg_repair_time
        """
        if machine_id is not None:
            events = [e for e in self.failure_events if e.machine_id == machine_id]
        else:
            events = self.failure_events
        
        if not events:
            return {
                'num_failures': 0,
                'total_downtime': 0,
                'availability': 100.0,
                'avg_repair_time': 0
            }
        
        num_failures = len(events)
        total_downtime = sum(e.downtime for e in events)
        avg_repair_time = sum(e.repair_duration for e in events) / num_failures if events else 0
        
        # Disponibilidad: % de tiempo operacional
        total_time = self.env.now if self.env.now > 0 else 1
        availability = ((total_time - total_downtime) / total_time) * 100
        
        return {
            'num_failures': num_failures,
            'total_downtime': total_downtime,
            'availability': availability,
            'avg_repair_time': avg_repair_time,
            'max_repair_time': max(e.repair_duration for e in events) if events else 0,
            'min_repair_time': min(e.repair_duration for e in events) if events else 0
        }
    
    def get_all_failure_events(self) -> List[MachineFailureEvent]:
        """Retorna todos los eventos de fallo registrados."""
        return self.failure_events.copy()
    
    def reset(self):
        """Resetea el gestor de fallos."""
        self.machine_failed = {i: False for i in range(self.num_machines)}
        self.failure_events = []


# ============================================================================
# CONFIGURACIONES PREDEFINIDAS DE CONFIABILIDAD
# ============================================================================

class ReliabilityProfile:
    """Perfiles predefinidos de confiabilidad."""
    
    @staticmethod
    def high_reliability() -> Tuple[float, float]:
        """Máquinas muy confiables: MTBF=1000, MTTR=2"""
        return (1000.0, 2.0)
    
    @staticmethod
    def medium_reliability() -> Tuple[float, float]:
        """Máquinas moderadamente confiables: MTBF=100, MTTR=5"""
        return (100.0, 5.0)
    
    @staticmethod
    def low_reliability() -> Tuple[float, float]:
        """Máquinas poco confiables: MTBF=30, MTTR=8"""
        return (30.0, 8.0)
    
    @staticmethod
    def custom_reliability(mtbf: float, mttr: float) -> Tuple[float, float]:
        """Perfil personalizado."""
        return (mtbf, mttr)
