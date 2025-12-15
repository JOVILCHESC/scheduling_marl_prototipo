"""
Cliente ZeroMQ para comunicación con JADE - Fase 3 (CNP)

Protocolo Contract Net:
1. Crear OrderAgent cuando llega un job
2. OrderAgent envía CFP (Call For Proposal) a MachineAgents
3. MachineAgents responden con Proposal/Refuse
4. OrderAgent acepta mejor propuesta
5. Notificar asignación a SimPy
"""

import zmq
import json
from typing import Dict, List, Optional, Tuple
import time


class JADECNPClient:
    """Cliente para comunicación CNP entre SimPy y JADE."""
    
    def __init__(self, server_address: str = "tcp://localhost:5555", timeout: int = 5000):
        """
        Args:
            server_address: Dirección del servidor ZeroMQ en JADE
            timeout: Timeout para operaciones en ms
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, timeout)
        self.socket.connect(server_address)
        self.server_address = server_address
        self.timeout = timeout
        
    def create_order_agent(self, job_id: int, operations: List[Dict], due_date: float, 
                          current_time: float) -> Optional[str]:
        """
        Crea un OrderAgent en JADE cuando llega un job a SimPy.
        
        Args:
            job_id: ID del job
            operations: Lista de operaciones [{'machine_type': int, 'duration': float}, ...]
            due_date: Fecha límite del job
            current_time: Tiempo actual de simulación
            
        Returns:
            str: AID del OrderAgent creado, o None si falla
        """
        try:
            request = {
                "action": "create_order_agent",
                "job_id": job_id,
                "operations": operations,
                "due_date": due_date,
                "current_time": current_time
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            # DEBUG: Mostrar respuesta completa
            print(f"[DEBUG] create_order_agent response: {response}")
            
            if response.get("status") == "success":
                return response.get("agent_id")
            else:
                print(f"[CNP] Error creando OrderAgent: {response}")
                return None
                
        except zmq.error.Again:
            print(f"[CNP] Timeout creando OrderAgent para job {job_id}")
            return None
        except Exception as e:
            print(f"[CNP] Excepción creando OrderAgent: {e}")
            return None
    
    def request_machine_assignment(self, job_id: int, operation_index: int, 
                                   current_time: float, 
                                   available_machines: List[int]) -> Optional[Dict]:
        """
        Solicita a OrderAgent que negocie con MachineAgents via CNP.
        
        Flujo CNP:
        1. OrderAgent envía CFP a MachineAgents disponibles
        2. MachineAgents evalúan y responden con Proposal/Refuse
        3. OrderAgent selecciona mejor propuesta
        4. Retorna asignación a SimPy
        
        Args:
            job_id: ID del job
            operation_index: Índice de operación actual del job
            current_time: Tiempo actual de simulación
            available_machines: IDs de máquinas disponibles
            
        Returns:
            dict: {"machine_id": int, "expected_start": float, "expected_end": float}
                  o None si no hay propuestas válidas
        """
        try:
            request = {
                "action": "cnp_negotiation",
                "job_id": job_id,
                "operation_index": operation_index,
                "current_time": current_time,
                "available_machines": available_machines
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            print(f"[DEBUG] cnp_negotiation response: {response}")
            
            if response.get("status") == "success":
                assignment = response.get("assignment")
                if assignment:
                    return {
                        "machine_id": assignment["machine_id"],
                        "expected_start": assignment.get("expected_start", current_time),
                        "expected_end": assignment.get("expected_end", current_time)
                    }
            else:
                print(f"[CNP] Negociación fallida para job {job_id}: {response.get('message')}")
            
            return None
                
        except zmq.error.Again:
            print(f"[CNP] Timeout en negociación para job {job_id}")
            return None
        except Exception as e:
            print(f"[CNP] Excepción en negociación: {e}")
            return None
    
    def notify_operation_start(self, job_id: int, operation_index: int, 
                               machine_id: int, start_time: float):
        """
        Notifica a JADE que una operación comenzó en SimPy.
        
        Args:
            job_id: ID del job
            operation_index: Índice de operación
            machine_id: ID de máquina asignada
            start_time: Tiempo de inicio
        """
        try:
            request = {
                "action": "operation_start",
                "job_id": job_id,
                "operation_index": operation_index,
                "machine_id": machine_id,
                "start_time": start_time
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") != "success":
                print(f"[CNP] Error notificando inicio: {response.get('message')}")
                
        except Exception as e:
            print(f"[CNP] Error notificando inicio de operación: {e}")
    
    def notify_operation_complete(self, job_id: int, operation_index: int, 
                                  machine_id: int, completion_time: float,
                                  is_last_operation: bool = False):
        """
        Notifica a JADE que una operación terminó.
        
        Args:
            job_id: ID del job
            operation_index: Índice de operación
            machine_id: ID de máquina
            completion_time: Tiempo de finalización
            is_last_operation: True si es la última operación del job
        """
        try:
            request = {
                "action": "operation_complete",
                "job_id": job_id,
                "operation_index": operation_index,
                "machine_id": machine_id,
                "completion_time": completion_time,
                "is_last_operation": is_last_operation
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") != "success":
                print(f"[CNP] Error notificando finalización: {response.get('message')}")
                
        except Exception as e:
            print(f"[CNP] Error notificando finalización: {e}")
    
    def notify_machine_failure(self, machine_id: int, failure_time: float, 
                              repair_duration: float, affected_job_id: Optional[int] = None):
        """
        Notifica falla de máquina. Si hay job afectado, OrderAgent re-negocia.
        
        Args:
            machine_id: ID de máquina que falló
            failure_time: Tiempo de falla
            repair_duration: Duración de reparación
            affected_job_id: Job que estaba ejecutándose (si aplica)
        """
        try:
            request = {
                "action": "machine_failure",
                "machine_id": machine_id,
                "failure_time": failure_time,
                "repair_duration": repair_duration,
                "affected_job_id": affected_job_id
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") == "success" and affected_job_id:
                # Si había job afectado, puede necesitar re-negociación
                print(f"[CNP] Máquina {machine_id} falló. Job {affected_job_id} necesita re-asignación")
            
        except Exception as e:
            print(f"[CNP] Error notificando falla de máquina: {e}")
    
    def notify_machine_repair(self, machine_id: int, repair_time: float):
        """
        Notifica que máquina fue reparada y está disponible.
        
        Args:
            machine_id: ID de máquina reparada
            repair_time: Tiempo de finalización de reparación
        """
        try:
            request = {
                "action": "machine_repair",
                "machine_id": machine_id,
                "repair_time": repair_time
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") == "success":
                print(f"[CNP] Máquina {machine_id} reparada en t={repair_time:.2f}")
                
        except Exception as e:
            print(f"[CNP] Error notificando reparación: {e}")
    
    def get_machine_status(self, machine_id: int) -> Optional[Dict]:
        """
        Obtiene estado actual de una máquina desde JADE.
        
        Args:
            machine_id: ID de máquina
            
        Returns:
            dict: {"available": bool, "current_job": int, "queue_length": int}
        """
        try:
            request = {
                "action": "get_machine_status",
                "machine_id": machine_id
            }
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") == "success":
                return response.get("machine_status")
            
            return None
                
        except Exception as e:
            print(f"[CNP] Error obteniendo estado de máquina: {e}")
            return None
    
    def close(self):
        """Cierra conexión con JADE."""
        try:
            self.socket.close()
            self.context.term()
        except:
            pass
    
    def renegotiate_after_failure(self, job_id: int, operation_index: int, 
                                   failed_machine_id: int, current_time: float,
                                   available_machines: List[int]) -> Optional[Dict]:
        """
        MEJORA #4: Solicita re-negociación cuando una máquina falla durante ejecución.
        
        Args:
            job_id: ID del job afectado
            operation_index: Índice de operación que falló
            failed_machine_id: ID de máquina que falló
            current_time: Tiempo actual de simulación
            available_machines: Lista de máquinas disponibles del tipo requerido
            
        Returns:
            Dict con nueva asignación o None si falla
        """
        try:
            request = {
                "action": "operation_failure",
                "job_id": job_id,
                "operation_index": operation_index,
                "failed_machine_id": failed_machine_id,
                "current_time": current_time,
                "available_machines": available_machines
            }
            
            print(f"[CNP] Solicitando re-negociación para Job {job_id} op {operation_index}")
            
            self.socket.send_json(request)
            response = self.socket.recv_json()
            
            if response.get("status") == "success":
                assignment = response.get("assignment")
                print(f"[CNP] ✓ Re-negociación exitosa: M{assignment['machine_id']}")
                return response
            else:
                print(f"[CNP] ✗ Re-negociación fallida: {response.get('message')}")
                return None
                
        except Exception as e:
            print(f"[CNP] Error en re-negociación: {e}")
            return None


# Función de conveniencia para inicializar cliente CNP
def get_cnp_client(server_address: str = "tcp://localhost:5555") -> JADECNPClient:
    """
    Crea y retorna un cliente CNP conectado a JADE.
    
    Args:
        server_address: Dirección del servidor JADE
        
    Returns:
        JADECNPClient: Cliente listo para usar
    """
    return JADECNPClient(server_address)
