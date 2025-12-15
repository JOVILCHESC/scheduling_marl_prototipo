"""
FASE 3: SIMULADOR CNP - Contract Net Protocol con OrderAgents

Simulador Job Shop que implementa negociación distribuida via CNP:
  - Llegadas dinámicas de órdenes
  - Creación de OrderAgent por cada job
  - Negociación CNP para asignar operaciones
  - Fallas estocásticas con re-negociación
  - Sistema integrado de eventos

Diferencia con Fase 2: Decisiones distribuidas (OrderAgents + MachineAgents)
en vez de SchedulerAgent centralizado.
"""

import simpy
import pandas as pd
import os
import argparse
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import numpy as np

# Imports módulos del proyecto
try:
    from .arrival_generator import ArrivalGenerator, JobSpec
    from .machine_failures import MachineFailureManager, MachineFailureEvent, ReliabilityProfile
    from .event_manager import EventManager, EventType, SimulationEvent
    from .integration.jade_cnp_client import get_cnp_client, JADECNPClient
except ImportError:
    from arrival_generator import ArrivalGenerator, JobSpec
    from machine_failures import MachineFailureManager, MachineFailureEvent, ReliabilityProfile
    from event_manager import EventManager, EventType, SimulationEvent
    from integration.jade_cnp_client import get_cnp_client, JADECNPClient
    # Fallback para imports de integración
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integration'))
        from jade_cnp_client import get_cnp_client, JADECNPClient
    except Exception as e:
        print(f"[WARNING] No se pudo importar jade_cnp_client: {e}")
        get_cnp_client = None
        JADECNPClient = None


class CNPMachine:
    """Máquina con soporte para CNP y fallos dinámicos."""
    
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
        self.current_job_id = None
        self.current_op_index = None
    
    def process(self, job_id: int, operation_index: int, duration: float):
        """Procesa operación, verificando fallos. MEJORA #4: Detecta fallas durante ejecución."""
        # Si hay fallo al inicio, esperar a que se repare
        while self.failure_manager.is_machine_failed(self.id):
            yield self.env.timeout(0.1)
        
        self.current_job_id = job_id
        self.current_op_index = operation_index
        
        # MEJORA #4: Verificar fallas durante la ejecución
        start_time = self.env.now
        elapsed = 0.0
        check_interval = min(1.0, duration / 10)  # Verificar cada 1s o cada 10% de duración
        
        while elapsed < duration:
            # Procesar en intervalos pequeños
            next_check = min(check_interval, duration - elapsed)
            yield self.env.timeout(next_check)
            elapsed += next_check
            
            # Verificar si la máquina falló durante el procesamiento
            if self.failure_manager.is_machine_failed(self.id):
                print(f"[FAILURE] Machine {self.id} falló durante Job {job_id} op {operation_index} (progreso: {elapsed:.2f}/{duration:.2f})")
                # Limpiar estado y propagar falla
                self.current_job_id = None
                self.current_op_index = None
                # Lanzar excepción para que el caller maneje la re-negociación
                raise RuntimeError(f"MachineFailure:M{self.id}:Job{job_id}:Op{operation_index}")
        
        # Operación completada exitosamente
        self.total_processing_time += duration
        self.num_operations += 1
        self.current_job_id = None
        self.current_op_index = None


class CNPJobShopSimulator:
    """Simulador de Job Shop con Contract Net Protocol."""
    
    def __init__(self, env: simpy.Environment,
                 num_machines: int,
                 arrival_rate: float = 0.5,
                 mtbf: float = 100.0,
                 mttr: float = 5.0,
                 random_seed: int = 42,
                 jade_server: str = "tcp://localhost:5555"):
        """
        Args:
            env: Entorno SimPy
            num_machines: Número de máquinas
            arrival_rate: Tasa de llegada de órdenes (trabajos/u.t.)
            mtbf: Mean Time Between Failures
            mttr: Mean Time To Repair
            random_seed: Seed para reproducibilidad
            jade_server: Dirección servidor JADE ZeroMQ
        """
        self.env = env
        self.num_machines = num_machines
        self.random_seed = random_seed
        
        # Cliente CNP para comunicación con JADE
        try:
            self.cnp_client = get_cnp_client(jade_server) if get_cnp_client else None
            if self.cnp_client:
                print(f"[CNP] Cliente conectado a {jade_server}")
            else:
                print("[WARNING] Cliente CNP no disponible, modo simulación sin JADE")
        except Exception as e:
            print(f"[ERROR] No se pudo conectar cliente CNP: {e}")
            self.cnp_client = None
        
        # Generador de llegadas
        self.arrival_gen = ArrivalGenerator(
            env=env,
            arrival_rate=arrival_rate,
            num_machines=num_machines
        )
        
        # Gestor de fallas de máquinas
        self.failure_manager = MachineFailureManager(
            env=env,
            num_machines=num_machines,
            mtbf_mean=mtbf,
            mttr_mean=mttr
        )
        
        # Crear máquinas
        self.machines = [CNPMachine(env, i, self.failure_manager) for i in range(num_machines)]
        
        # Gestor de eventos
        self.event_manager = EventManager()
        
        # Estructuras de datos
        self.jobs = {}  # jobId -> JobSpec
        self.order_agents = {}  # jobId -> agentId (AID from JADE)
        self.job_completion_times = {}
        self.job_tardiness = {}
        
        # Contadores
        self.next_job_id = 0
        self.completed_jobs = 0
        
    def run(self, duration: float):
        """Ejecuta simulación por tiempo especificado."""
        print(f"\n[SIMULATION] Iniciando Fase 3 (CNP) - Duración: {duration} u.t.")
        print(f"[PARAMS] arrival_rate={self.arrival_gen.arrival_rate}, mtbf={self.failure_manager.mtbf_mean}")
        
        # Iniciar procesos
        self.env.process(self.arrival_process())
        
        # Iniciar procesos de falla para cada máquina
        for machine_id in range(self.num_machines):
            self.env.process(self.failure_manager.failure_process(machine_id))
        
        # Ejecutar simulación
        self.env.run(until=duration)
        
        print(f"\n[SIMULATION] Finalizada. Jobs completados: {self.completed_jobs}")
        
    def arrival_process(self):
        """Proceso de llegada de jobs con creación de OrderAgents."""
        while True:
            # Esperar siguiente llegada (distribución exponencial)
            interarrival_time = np.random.exponential(1.0 / self.arrival_gen.arrival_rate)
            yield self.env.timeout(interarrival_time)
            
            # Generar nuevo job usando arrival_gen
            job_id = self.next_job_id
            operations_list = self.arrival_gen.generate_job_operations()
            arrival_time = self.env.now
            due_date = self.arrival_gen.calculate_due_date(arrival_time, operations_list)
            
            # Crear JobSpec
            job_spec = JobSpec(
                job_id=job_id,
                arrival_time=arrival_time,
                operations=operations_list,
                due_date=due_date
            )
            
            self.jobs[job_id] = job_spec
            self.next_job_id += 1
            
            self.event_manager.arrival_event(
                time=self.env.now,
                job_id=job_id,
                num_operations=len(job_spec.operations)
            )
            
            print(f"[t={self.env.now:.2f}] Job {job_id} arrived (ops={len(job_spec.operations)}, due={job_spec.due_date:.2f})")
            
            # Crear OrderAgent en JADE (opcional, solo si cliente disponible)
            if self.cnp_client:
                agent_id = self.cnp_client.create_order_agent(
                    job_id=job_id,
                    operations=[{
                        'machine_type': machine_id,
                        'duration': duration
                    } for machine_id, duration in job_spec.operations],
                    due_date=job_spec.due_date,
                    current_time=self.env.now
                )
                
                if agent_id:
                    self.order_agents[job_id] = agent_id
                    print(f"[CNP] OrderAgent '{agent_id}' creado para Job {job_id}")
            
            # Iniciar procesamiento del job
            self.env.process(self.process_job(job_spec))
    
    def process_job(self, job: JobSpec):
        """Procesa todas las operaciones de un job usando CNP."""
        job_id = job.job_id
        start_time = self.env.now
        
        for op_index, (machine_type, duration) in enumerate(job.operations):
            
            # Negociar asignación via CNP (fallback a asignación directa si no hay JADE)
            assigned_machine_id = yield from self.negotiate_assignment(job_id, op_index, machine_type, duration)
            
            if assigned_machine_id is None:
                print(f"[ERROR] No se pudo asignar Job {job_id} op {op_index}")
                return
            
            machine = self.machines[assigned_machine_id]
            
            # Solicitar máquina
            with machine.resource.request() as req:
                yield req
                
                # Si la máquina está fallida, el failure_process() ya tiene el recurso bloqueado
                # El yield req arriba esperará automáticamente hasta que esté disponible
                
                # Procesar operación con manejo de fallos
                op_start = self.env.now
                
                self.event_manager.operation_start(
                    time=op_start,
                    job_id=job_id,
                    machine_id=assigned_machine_id,
                    duration=duration,
                    queue_length=0
                )
                
                # Notificar inicio a JADE
                if self.cnp_client:
                    self.cnp_client.notify_operation_start(
                        job_id=job_id,
                        operation_index=op_index,
                        machine_id=assigned_machine_id,
                        start_time=op_start
                    )
                
                print(f"[t={op_start:.2f}] Job {job_id} op {op_index} STARTED on M{assigned_machine_id} (dur={duration:.2f})")
                
                # MEJORA #4: Ejecutar operación con manejo de fallas
                try:
                    yield from machine.process(job_id, op_index, duration)
                    
                    op_end = self.env.now
                    
                    self.event_manager.operation_end(
                        time=op_end,
                        job_id=job_id,
                        machine_id=assigned_machine_id
                    )
                    
                    # Notificar finalización exitosa a JADE
                    is_last_op = (op_index == len(job.operations) - 1)
                    if self.cnp_client:
                        self.cnp_client.notify_operation_complete(
                            job_id=job_id,
                            operation_index=op_index,
                            machine_id=assigned_machine_id,
                            completion_time=op_end,
                            is_last_operation=is_last_op
                        )
                    
                    print(f"[t={op_end:.2f}] Job {job_id} op {op_index} COMPLETED on M{assigned_machine_id}")
                    
                except RuntimeError as e:
                    # MEJORA #4: Capturar falla y re-negociar
                    if str(e).startswith("MachineFailure:"):
                        failure_time = self.env.now
                        print(f"[t={failure_time:.2f}] FALLA DETECTADA: {e}")
                        
                        # Notificar falla y solicitar re-negociación a JADE
                        if self.cnp_client:
                            # Obtener máquinas disponibles del mismo tipo
                            available_machines = [
                                m.id for m in self.machines
                                if m.id == machine_type and not self.failure_manager.is_machine_failed(m.id)
                            ]
                            
                            print(f"[RENEGOTIATE] Solicitando re-asignación para Job {job_id} op {op_index}")
                            print(f"[RENEGOTIATE] Máquinas disponibles tipo {machine_type}: {available_machines}")
                            
                            new_assignment = self.cnp_client.renegotiate_after_failure(
                                job_id=job_id,
                                operation_index=op_index,
                                failed_machine_id=assigned_machine_id,
                                current_time=failure_time,
                                available_machines=available_machines
                            )
                            
                            if new_assignment and new_assignment.get('status') == 'success':
                                new_machine_id = new_assignment['assignment']['machine_id']
                                print(f"[RENEGOTIATE] ✓ Re-asignado a M{new_machine_id}, reintentando...")
                                
                                # Reintentar operación con nueva máquina
                                # (recursión para simplificar el código)
                                yield from self.process_operation(job, job_id, op_index)
                            else:
                                print(f"[ERROR] No se pudo re-asignar Job {job_id} op {op_index} tras falla")
                        else:
                            print(f"[ERROR] CNP client no disponible para re-negociación")
                    else:
                        # Otro tipo de error, re-lanzar
                        raise
        
        # Job completado
        completion_time = self.env.now
        tardiness = max(0, completion_time - job.due_date)
        
        self.job_completion_times[job_id] = completion_time
        self.job_tardiness[job_id] = tardiness
        self.completed_jobs += 1
        
        # EventManager no tiene método job_complete, usamos log_event directamente
        event = SimulationEvent(
            time=completion_time,
            event_type=EventType.COMPLETE.value,
            job_id=job_id,
            additional_info={"tardiness": tardiness}
        )
        self.event_manager.log_event(event)
        
        print(f"[t={completion_time:.2f}] Job {job_id} COMPLETED (tardiness={tardiness:.2f})")
    
    def negotiate_assignment(self, job_id: int, op_index: int, machine_type: int, duration: float):
        """Negocia asignación de operación via CNP."""
        # Obtener máquinas disponibles del tipo requerido
        available_machines = [
            m.id for m in self.machines 
            if m.id == machine_type and not self.failure_manager.is_machine_failed(m.id)
        ]
        
        if not available_machines:
            print(f"[WARNING] No hay máquinas tipo {machine_type} disponibles")
            # Esperar y reintentar
            yield self.env.timeout(1.0)
            available_machines = [
                m.id for m in self.machines 
                if m.id == machine_type and not self.failure_manager.is_machine_failed(m.id)
            ]
        
        # Solicitar negociación CNP a JADE
        if self.cnp_client:
            assignment = self.cnp_client.request_machine_assignment(
                job_id=job_id,
                operation_index=op_index,
                current_time=self.env.now,
                available_machines=available_machines
            )
            
            if assignment:
                return assignment['machine_id']
        
        # Fallback: asignar primera máquina disponible
        if available_machines:
            return available_machines[0]
        
        return None
    
    def export_results(self, prefix: str = "simulation_phase3_cnp"):
        """Exporta resultados a CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorio logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Exportar eventos usando el método correcto (solo el prefijo, no el path completo)
        self.event_manager.export_to_csv(filename=prefix)
        print(f"\n[EXPORT] Eventos exportados con prefijo: {prefix}")
        
        # Exportar jobs
        jobs_data = []
        for job_id, job_spec in self.jobs.items():
            if job_id in self.job_completion_times:
                jobs_data.append({
                    'job_id': job_id,
                    'arrival_time': job_spec.arrival_time,
                    'due_date': job_spec.due_date,
                    'completion_time': self.job_completion_times[job_id],
                    'tardiness': self.job_tardiness[job_id],
                    'num_operations': len(job_spec.operations)
                })
        
        jobs_df = pd.DataFrame(jobs_data)
        jobs_file = f"logs/{prefix}_jobs_{timestamp}.csv"
        jobs_df.to_csv(jobs_file, index=False)
        print(f"[EXPORT] Jobs: {jobs_file}")
        
        # Las fallas ya están en el event log, no necesitamos un archivo separado
        
        # Métricas
        if jobs_data:
            avg_tardiness = jobs_df['tardiness'].mean()
            max_tardiness = jobs_df['tardiness'].max()
            total_tardiness = jobs_df['tardiness'].sum()
            makespan = jobs_df['completion_time'].max()
            
            print(f"\n[METRICS] Makespan: {makespan:.2f}")
            print(f"[METRICS] Total Tardiness: {total_tardiness:.2f}")
            print(f"[METRICS] Avg Tardiness: {avg_tardiness:.2f}")
            print(f"[METRICS] Max Tardiness: {max_tardiness:.2f}")
            print(f"[METRICS] Jobs completados: {len(jobs_data)}")


def main():
    """Función principal para ejecutar simulación Fase 3."""
    parser = argparse.ArgumentParser(description='Simulador Job Shop Fase 3 (CNP)')
    parser.add_argument('--duration', type=float, default=1000.0, help='Duración de simulación')
    parser.add_argument('--arrival-rate', type=float, default=0.4, help='Tasa de llegada')
    parser.add_argument('--mtbf', type=float, default=100.0, help='Mean Time Between Failures')
    parser.add_argument('--mttr', type=float, default=8.0, help='Mean Time To Repair')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--jade-server', type=str, default='tcp://localhost:5555', help='JADE ZeroMQ server')
    
    args = parser.parse_args()
    
    # Crear entorno SimPy
    env = simpy.Environment()
    
    # Crear simulador CNP
    simulator = CNPJobShopSimulator(
        env=env,
        num_machines=6,
        arrival_rate=args.arrival_rate,
        mtbf=args.mtbf,
        mttr=args.mttr,
        random_seed=args.seed,
        jade_server=args.jade_server
    )
    
    # Ejecutar simulación
    simulator.run(args.duration)
    
    # Exportar resultados
    simulator.export_results()
    
    # Cerrar cliente CNP
    if simulator.cnp_client:
        simulator.cnp_client.close()


if __name__ == "__main__":
    main()
