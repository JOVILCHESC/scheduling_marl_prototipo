"""Cliente ZeroMQ para integrar SimPy con el servidor JADE.

Reemplaza la comunicación HTTP por ZeroMQ (REQ-REP) para menor latencia.
Provee `decide_allow` que consulta al servidor JADE y, en caso de
error o timeout, aplica una política fallback (SPT) usando
`scheduling_rules.SchedulingRules`.
"""
import json
import zmq
from typing import List, Dict, Any, Optional

try:
    from ..scheduling_rules import SchedulingRules
except ImportError:
    from scheduling_rules import SchedulingRules

DEFAULT_JADE_ZMQ_ADDR = "tcp://localhost:5555"

class ZmqClient:
    _context: Optional[zmq.Context] = None
    _socket: Optional[zmq.Socket] = None

    @classmethod
    def get_socket(cls, addr: str = DEFAULT_JADE_ZMQ_ADDR) -> zmq.Socket:
        if cls._context is None:
            cls._context = zmq.Context()
        
        if cls._socket is None:
            cls._socket = cls._context.socket(zmq.REQ)
            cls._socket.connect(addr)
            # Configurar timeout de recepción (ms)
            cls._socket.setsockopt(zmq.RCVTIMEO, 2000)
            cls._socket.setsockopt(zmq.LINGER, 0)
        
        return cls._socket

    @classmethod
    def send_request(cls, req_type: str, payload: Dict[str, Any], timeout_ms: int = 2000) -> Dict[str, Any]:
        sock = cls.get_socket()
        # Actualizar timeout si es necesario (aunque setsockopt es global para el socket)
        sock.setsockopt(zmq.RCVTIMEO, timeout_ms)

        full_payload = payload.copy()
        full_payload['type'] = req_type
        
        try:
            sock.send_string(json.dumps(full_payload))
            reply = sock.recv_string()
            return json.loads(reply)
        except zmq.Again:
            # Timeout
            # Reiniciar socket en caso de timeout para evitar estado inconsistente (REQ/REP lockstep)
            cls._reset_socket()
            raise TimeoutError("ZMQ Request timed out")
        except Exception as e:
            cls._reset_socket()
            raise e

    @classmethod
    def _reset_socket(cls):
        if cls._socket:
            cls._socket.close()
            cls._socket = None

def send_feedback(machine_id: int, current_job_id: int, queue_jobs: List[Dict], action: int, reward: float,
                 next_state: str = None, next_actions: List[int] = None, 
                 zmq_addr: str = DEFAULT_JADE_ZMQ_ADDR,
                 timeout: float = 2.0) -> bool:
    """Envía feedback de aprendizaje al servidor JADE vía ZeroMQ.
    """
    payload = {
        'machine_id': machine_id,
        'current_job': current_job_id,
        'queue': [
            {
                'job_id': j['job_id'],
                'next_op_duration': j.get('next_op_duration'),
                'due_date': j.get('due_date')
            }
            for j in queue_jobs
        ],
        'action': action,
        'reward': reward
    }
    if next_state is not None:
        payload['next_state'] = next_state
    if next_actions is not None:
        payload['next_actions'] = next_actions

    try:
        # Convertir timeout a ms
        resp = ZmqClient.send_request("feedback", payload, timeout_ms=int(timeout * 1000))
        return isinstance(resp, dict) and resp.get('ok', False)
    except Exception as e:
        # print(f"[JADE-ZMQ] feedback failed: {e}")
        return False


def notify_event(event_type: str, payload: Dict[str, Any], zmq_addr: str = DEFAULT_JADE_ZMQ_ADDR, timeout: float = 2.0) -> bool:
    """Envía una notificación de evento al sistema JADE (Mirroring).
    
    Tipos de eventos sugeridos:
    - ORDER_ARRIVED: Nueva orden en el sistema.
    - MACHINE_STARTED: Máquina comienza a procesar.
    - MACHINE_FINISHED: Máquina termina de procesar.
    - MACHINE_FAILED: Máquina entra en estado de fallo.
    """
    full_payload = payload.copy()
    full_payload['event_type'] = event_type
    
    try:
        resp = ZmqClient.send_request("event", full_payload, timeout_ms=int(timeout * 1000))
        return isinstance(resp, dict) and resp.get('status') == 'ok'
    except Exception as e:
        # print(f"[JADE-ZMQ] notification failed: {e}")
        return False


def request_decision(machine_id: int, current_job_id: int, queue_jobs: List[Dict], 
                     zmq_addr: str = DEFAULT_JADE_ZMQ_ADDR,
                     timeout: float = 2.0) -> Dict[str, Any]:
    """Solicita decisión al servidor JADE vía ZeroMQ.
    """
    payload = {
        'machine_id': machine_id,
        'current_job': current_job_id,
        'queue': [
            {
                'job_id': j['job_id'],
                'next_op_duration': j.get('next_op_duration'),
                'due_date': j.get('due_date')
            }
            for j in queue_jobs
        ]
    }
    
    try:
        resp = ZmqClient.send_request("decide", payload, timeout_ms=int(timeout * 1000))
        return resp
    except Exception as e:
        # print(f"[JADE-ZMQ] decide failed: {e}")
        raise


def decide_allow(machine_id: int, current_job_id: int, queue_jobs: List[Dict],
                scheduling_rule: str = "SPT", zmq_addr: str = DEFAULT_JADE_ZMQ_ADDR,
                timeout: float = 0.5) -> bool:
    """Consulta al servidor JADE si el `current_job_id` debe ser procesado ahora.
    """
    try:
        resp = request_decision(machine_id, current_job_id, queue_jobs, zmq_addr, timeout)
        
        if isinstance(resp, dict):
            if 'allow' in resp:
                return bool(resp['allow'])
            if 'selected_job' in resp:
                return int(resp['selected_job']) == int(current_job_id)
    except Exception:
        # Fallback silencioso
        pass

    # Fallback local: aplicar regla de despacho (SPT por defecto).
    jobs_data = [j.get('operations', []) for j in queue_jobs]
    job_ids = [j['job_id'] for j in queue_jobs]

    if not jobs_data:
        return True

    try:
        ordered_indices = SchedulingRules.apply_rule(scheduling_rule, jobs_data)[0]
    except Exception:
        ordered_indices = SchedulingRules.SPT(jobs_data)

    first_job_idx = ordered_indices[0]
    first_job_id = job_ids[first_job_idx]
    return int(first_job_id) == int(current_job_id)
