"""
MÓDULO: Gestor de Eventos

Sistema centralizado para registrar y gestionar todos los eventos de la simulación:
  - Llegadas de órdenes
  - Inicio/fin de operaciones
  - Fallos y reparaciones de máquinas
  - Eventos especiales

Características:
  - Log estructurado con timestamps
  - Exportación a CSV
  - Generación automática de reportes
  - Integración con SimPy
"""

import csv
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Tipos de eventos en la simulación."""
    ARRIVAL = "arrival"           # Llegada de orden
    START = "start"               # Inicio de operación
    END = "end"                   # Fin de operación
    FAILURE = "failure"           # Fallo de máquina
    REPAIR_START = "repair_start" # Inicio de reparación
    REPAIR_END = "repair_end"     # Fin de reparación
    COMPLETE = "complete"         # Trabajo completado


@dataclass
class SimulationEvent:
    """Representación de un evento en la simulación."""
    time: float
    event_type: str
    job_id: int = None
    machine_id: int = None
    duration: float = None      # Para operaciones
    queue_length: int = None    # Largo de cola en máquina
    additional_info: Dict = None  # Información adicional
    
    def to_dict(self) -> Dict:
        """Convierte evento a diccionario."""
        data = asdict(self)
        # Convertir additional_info a formato serializable
        if data['additional_info']:
            data['additional_info'] = str(data['additional_info'])
        return data


class EventManager:
    """Gestor centralizado de eventos de simulación."""
    
    def __init__(self, output_dir: str = "logs"):
        """
        Args:
            output_dir: Directorio para guardar logs
        """
        self.events: List[SimulationEvent] = []
        self.output_dir = output_dir
        self.start_time = None
        self.end_time = None
        
        # Crear directorio si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def log_event(self, event: SimulationEvent):
        """Registra un evento."""
        self.events.append(event)
    
    def arrival_event(self, time: float, job_id: int, num_operations: int):
        """Registra llegada de orden."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.ARRIVAL.value,
            job_id=job_id,
            additional_info={"num_operations": num_operations}
        )
        self.log_event(event)
    
    def operation_start(self, time: float, job_id: int, machine_id: int, 
                       duration: float, queue_length: int = 0):
        """Registra inicio de operación."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.START.value,
            job_id=job_id,
            machine_id=machine_id,
            duration=duration,
            queue_length=queue_length
        )
        self.log_event(event)
    
    def operation_end(self, time: float, job_id: int, machine_id: int):
        """Registra fin de operación."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.END.value,
            job_id=job_id,
            machine_id=machine_id
        )
        self.log_event(event)
    
    def machine_failure(self, time: float, machine_id: int, repair_duration: float):
        """Registra fallo de máquina."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.FAILURE.value,
            machine_id=machine_id,
            additional_info={"repair_duration": repair_duration}
        )
        self.log_event(event)
    
    def repair_start(self, time: float, machine_id: int, repair_duration: float):
        """Registra inicio de reparación."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.REPAIR_START.value,
            machine_id=machine_id,
            duration=repair_duration
        )
        self.log_event(event)
    
    def repair_end(self, time: float, machine_id: int, total_downtime: float):
        """Registra fin de reparación."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.REPAIR_END.value,
            machine_id=machine_id,
            duration=total_downtime
        )
        self.log_event(event)
    
    def job_complete(self, time: float, job_id: int, makespan: float):
        """Registra completación de trabajo."""
        event = SimulationEvent(
            time=time,
            event_type=EventType.COMPLETE.value,
            job_id=job_id,
            additional_info={"makespan": makespan}
        )
        self.log_event(event)
    
    def export_to_csv(self, filename: str = "simulation_log"):
        """
        Exporta eventos a archivo CSV.
        
        Args:
            filename: Nombre del archivo (sin extensión)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.csv")
        
        if not self.events:
            print(f"[WARNING] No hay eventos para exportar")
            return filepath
        
        # Convertir eventos a diccionarios
        rows = [event.to_dict() for event in self.events]
        
        # Escribir CSV
        fieldnames = ['time', 'event_type', 'job_id', 'machine_id', 'duration', 
                     'queue_length', 'additional_info']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"[OK] Log exportado: {filepath}")
        return filepath
    
    def get_event_summary(self) -> Dict[str, Any]:
        """Retorna resumen de eventos."""
        event_counts = {}
        for event in self.events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(self.events),
            'event_counts': event_counts,
            'simulation_time': self.events[-1].time if self.events else 0,
            'unique_jobs': len(set(e.job_id for e in self.events if e.job_id)),
            'machines_involved': len(set(e.machine_id for e in self.events if e.machine_id))
        }
    
    def print_event_summary(self):
        """Imprime resumen de eventos."""
        summary = self.get_event_summary()
        
        print("\n" + "="*70)
        print("[RESUMEN DE EVENTOS DE SIMULACION]")
        print("="*70)
        print(f"Total de eventos registrados: {summary['total_events']}")
        print(f"Tiempo de simulacion: {summary['simulation_time']:.2f} u.t.")
        print(f"Ordenes procesadas: {summary['unique_jobs']}")
        print(f"Maquinas involucradas: {summary['machines_involved']}")
        print("\nDesglose por tipo de evento:")
        
        event_order = ['arrival', 'start', 'end', 'failure', 'repair_start', 'repair_end', 'complete']
        for event_type in event_order:
            if event_type in summary['event_counts']:
                count = summary['event_counts'][event_type]
                print(f"  - {event_type:15s}: {count:4d} eventos")
        
        print("="*70 + "\n")
    
    def get_events_by_type(self, event_type: str) -> List[SimulationEvent]:
        """Retorna eventos de un tipo específico."""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_by_job(self, job_id: int) -> List[SimulationEvent]:
        """Retorna todos los eventos de un trabajo específico."""
        return [e for e in self.events if e.job_id == job_id]
    
    def get_events_by_machine(self, machine_id: int) -> List[SimulationEvent]:
        """Retorna todos los eventos de una máquina específica."""
        return [e for e in self.events if e.machine_id == machine_id]
    
    def reset(self):
        """Resetea el gestor de eventos."""
        self.events = []
        self.start_time = None
        self.end_time = None
