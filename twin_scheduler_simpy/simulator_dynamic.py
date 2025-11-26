"""
FASE 2: SIMULADOR DINÁMICO CON LLEGADAS EN LÍNEA Y FALLAS DE MÁQUINAS

Simulador Job Shop que incorpora:
  - Llegadas dinámicas de órdenes (procesos de Poisson)
  - Fallas estocásticas de máquinas con reparación
  - Sistema integrado de eventos
  - Cálculo de métricas avanzadas

Basado en simulator_static.py pero con eventos dinámicos.
"""

import simpy
import pandas as pd
import os
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import numpy as np

from arrival_generator import ArrivalGenerator, JobSpec
from machine_failures import MachineFailureManager, MachineFailureEvent, ReliabilityProfile
from event_manager import EventManager, EventType
# from metrics import MetricsCalculator
# from scheduling_rules import SchedulingRules
# from datasets import Datasets


class DynamicMachine:
    """Máquina con soporte para fallos dinámicos."""
    
    def __init__(self, env: simpy.Environment, machine_id: int, 
                 failure_manager: MachineFailureManager):
        """
        Args:
            env: Entorno SimPy
            machine_id: ID de máquina
            failure_manager: Gestor de fallos
        """
        self.env = env
        self.id = machine_id
        self.resource = simpy.Resource(env, capacity=1)
        self.queue = []
        self.failure_manager = failure_manager
        
        # Estadísticas
        self.total_processing_time = 0
        self.num_operations = 0
        self.idle_time = 0
    
    def process(self, job_id: int, duration: float):
        """Procesa operación, verificando fallos."""
        # Si hay fallo, esperar a que se repare
        while self.failure_manager.is_machine_failed(self.id):
            yield self.env.timeout(0.1)
        
        yield self.env.timeout(duration)
        self.total_processing_time += duration
        self.num_operations += 1


class DynamicJobShopSimulator:
    """Simulador de Job Shop con llegadas dinámicas y fallos."""
    
    def __init__(self, env: simpy.Environment,
                 num_machines: int,
                 arrival_rate: float = 0.5,
                 mtbf: float = 100.0,
                 mttr: float = 5.0,
                 scheduling_rule: str = "SPT",
                 random_seed: int = 42):
        """
        Args:
            env: Entorno SimPy
            num_machines: Número de máquinas
            arrival_rate: Tasa de llegada de órdenes (trabajos/u.t.)
            mtbf: Mean Time Between Failures
            mttr: Mean Time To Repair
            scheduling_rule: Regla de despacho (SPT, EDD, LPT)
            random_seed: Seed para reproducibilidad
        """
        self.env = env
        self.num_machines = num_machines
        self.arrival_rate = arrival_rate
        self.scheduling_rule = scheduling_rule
        
        # Fijar seed para reproducibilidad
        np.random.seed(random_seed)
        
        # Componentes
        self.failure_manager = MachineFailureManager(
            env, num_machines, mtbf_mean=mtbf, mttr_mean=mttr
        )
        self.arrival_generator = ArrivalGenerator(
            env, arrival_rate=arrival_rate, num_machines=num_machines
        )
        self.event_manager = EventManager()
        
        # Máquinas
        self.machines: List[DynamicMachine] = [
            DynamicMachine(env, i, self.failure_manager) for i in range(num_machines)
        ]
        
        # Registro de trabajos
        self.jobs_in_progress: Dict[int, JobSpec] = {}
        self.jobs_completed: Dict[int, Dict] = {}
        self.pending_jobs: List[JobSpec] = []
        
        # Métricas
        # self.metrics_calculator = MetricsCalculator()
        # self.scheduling_rules = SchedulingRules()
        
        # Callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Configura callbacks para eventos dinámicos."""
        
        # Callback de llegada
        self.arrival_generator.set_arrival_callback(self._on_job_arrival)
        
        # Callbacks de falla/reparación
        self.failure_manager.set_on_failure_callback(self._on_machine_failure)
        self.failure_manager.set_on_repair_callback(self._on_machine_repair)
    
    def _on_job_arrival(self, job: JobSpec):
        """Callback cuando llega un nuevo trabajo."""
        self.pending_jobs.append(job)
        
        # Registrar evento
        self.event_manager.arrival_event(
            time=self.env.now,
            job_id=job.job_id,
            num_operations=len(job.operations)
        )
        
        if True:  # verbose
            print(f"[{self.env.now:6.1f}] [ARRIVAL] Job {job.job_id:3d} LLEGA "
                  f"(Operaciones: {len(job.operations)}, Due date: {job.due_date:.1f})")
        
        # Iniciar procesamiento
        self.env.process(self._process_job(job))
    
    def _on_machine_failure(self, event: MachineFailureEvent):
        """Callback cuando falla una máquina."""
        self.event_manager.machine_failure(
            time=event.failure_time,
            machine_id=event.machine_id,
            repair_duration=event.repair_duration
        )
        
        print(f"[{event.failure_time:6.1f}] [FAILURE] Maquina {event.machine_id:2d} FALLO "
              f"(Reparacion estimada: {event.repair_duration:.1f} u.t.)")
    
    def _on_machine_repair(self, event: MachineFailureEvent):
        """Callback cuando termina reparación."""
        self.event_manager.repair_end(
            time=event.repair_end_time,
            machine_id=event.machine_id,
            total_downtime=event.downtime
        )
        
        print(f"[{event.repair_end_time:6.1f}] [REPAIR] Maquina {event.machine_id:2d} REPUESTA "
              f"(Downtime: {event.downtime:.1f} u.t.)")
    
    def _process_job(self, job: JobSpec):
        """Procesa todas las operaciones de un trabajo."""
        self.jobs_in_progress[job.job_id] = job
        
        for op_idx, (machine_id, duration) in enumerate(job.operations):
            machine = self.machines[machine_id]
            
            # Agregar a cola
            machine.queue.append(job.job_id)
            queue_length = len(machine.queue)
            
            # Solicitar máquina
            with machine.resource.request() as req:
                yield req
                
                # Remover de cola
                if job.job_id in machine.queue:
                    machine.queue.remove(job.job_id)
                
                # Registrar inicio
                start_time = self.env.now
                self.event_manager.operation_start(
                    time=start_time,
                    job_id=job.job_id,
                    machine_id=machine_id,
                    duration=duration,
                    queue_length=queue_length - 1  # Ya removido
                )
                
                print(f"[{start_time:6.1f}] [START] Job {job.job_id:3d} Op{op_idx+1} en "
                      f"Maq {machine_id:2d} ({duration} u.t.) [Cola: {len(machine.queue)}]")
                
                # Procesar
                yield self.env.process(machine.process(job.job_id, duration))
                
                # Registrar fin
                end_time = self.env.now
                self.event_manager.operation_end(
                    time=end_time,
                    job_id=job.job_id,
                    machine_id=machine_id
                )
        
        # Trabajo completado
        completion_time = self.env.now
        makespan = completion_time - job.arrival_time
        
        self.jobs_completed[job.job_id] = {
            'job_id': job.job_id,
            'arrival_time': job.arrival_time,
            'completion_time': completion_time,
            'makespan': makespan,
            'due_date': job.due_date,
            'tardiness': max(0, completion_time - job.due_date)
        }
        
        # Registrar completación
        self.event_manager.job_complete(
            time=completion_time,
            job_id=job.job_id,
            makespan=makespan
        )
        
        if True:  # verbose
            tardiness = max(0, completion_time - job.due_date)
            status = "[OK]" if tardiness <= 0 else "[LATE]"
            print(f"[{completion_time:6.1f}] {status} Job {job.job_id:3d} COMPLETO "
                  f"(Makespan: {makespan:.1f}, Tardanza: {tardiness:.1f})")
        
        del self.jobs_in_progress[job.job_id]
    
    def run(self, until_time: float = 500.0, warmup: float = 50.0):
        """
        Ejecuta la simulación.
        
        Args:
            until_time: Tiempo total de simulación
            warmup: Tiempo de calentamiento (no contar en métricas)
        """
        print("\n" + "="*80)
        print("[INICIANDO SIMULACION DINAMICA]")
        print(f"   Maquinas: {self.num_machines}")
        print(f"   Tasa llegada: {self.arrival_rate} ordenes/u.t.")
        print(f"   MTBF: {self.failure_manager.mtbf_mean:.1f}, MTTR: {self.failure_manager.mttr_mean:.1f}")
        print(f"   Regla despacho: {self.scheduling_rule}")
        print(f"   Tiempo simulacion: {until_time:.1f} u.t. (Warmup: {warmup:.1f})")
        print("="*80 + "\n")
        
        # Iniciar componentes
        self.arrival_generator.start()
        self.failure_manager.start_failure_simulation()
        
        # Ejecutar
        self.env.run(until=until_time)
        
        # Resumen
        self._print_summary(warmup)
    
    def _print_summary(self, warmup: float = 0):
        """Imprime resumen de la simulación."""
        print("\n" + "="*80)
        print("[RESUMEN DE SIMULACION DINAMICA]")
        print("="*80)
        
        # Eventos
        self.event_manager.print_event_summary()
        
        # Trabajos
        print(f"[OK] Trabajos completados: {len(self.jobs_completed)}")
        
        if self.jobs_completed:
            makespans = [j['makespan'] for j in self.jobs_completed.values()]
            tardiness = [j['tardiness'] for j in self.jobs_completed.values()]
            
            print(f"   Makespan promedio: {np.mean(makespans):.2f}")
            print(f"   Tardanza total: {sum(tardiness):.2f}")
            print(f"   Trabajos atrasados: {len([t for t in tardiness if t > 0])}")
        
        # Máquinas
        print("\n[ESTADISTICAS POR MAQUINA]:")
        total_downtime = 0
        for i, machine in enumerate(self.machines):
            stats = self.failure_manager.get_failure_stats(i)
            downtime = stats['total_downtime']
            availability = stats['availability']
            total_downtime += downtime
            
            print(f"   Maquina {i}: "
                  f"Fallos={stats['num_failures']:2d}, "
                  f"Downtime={downtime:7.1f}, "
                  f"Disponibilidad={availability:6.1f}%")
        
        print(f"\n   Total downtime del sistema: {total_downtime:.1f} u.t.")
        print("="*80 + "\n")
    
    def export_results(self, prefix: str = "simulation_dynamic"):
        """Exporta resultados a CSV."""
        # Log de eventos
        log_file = self.event_manager.export_to_csv(prefix)
        
        # Trabajos completados
        if self.jobs_completed:
            df_jobs = pd.DataFrame(list(self.jobs_completed.values()))
            jobs_file = os.path.join(self.event_manager.output_dir, 
                                     f"{prefix}_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df_jobs.to_csv(jobs_file, index=False)
            print(f"✅ Trabajos exportados: {jobs_file}")
        
        # Fallos de máquinas
        failure_events = self.failure_manager.get_all_failure_events()
        if failure_events:
            df_failures = pd.DataFrame([
                {
                    'machine_id': e.machine_id,
                    'failure_time': e.failure_time,
                    'repair_start': e.repair_start_time,
                    'repair_duration': e.repair_duration,
                    'repair_end': e.repair_end_time,
                    'total_downtime': e.downtime
                }
                for e in failure_events
            ])
            failures_file = os.path.join(self.event_manager.output_dir,
                                         f"{prefix}_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df_failures.to_csv(failures_file, index=False)
            print(f"✅ Fallos exportados: {failures_file}")
        
        return log_file


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Ejecuta simulación dinámica de prueba."""
    
    # Crear entorno
    env = simpy.Environment()
    
    # Crear simulador
    simulator = DynamicJobShopSimulator(
        env=env,
        num_machines=6,
        arrival_rate=0.4,  # 0.4 órdenes por u.t.
        mtbf=100.0,        # Fallo cada 100 u.t. en promedio
        mttr=8.0,          # Reparación de 8 u.t. en promedio
        scheduling_rule="SPT",
        random_seed=42
    )
    
    # Ejecutar
    simulator.run(until_time=1000.0, warmup=100.0)
    
    # Exportar
    simulator.export_results()


if __name__ == "__main__":
    main()
