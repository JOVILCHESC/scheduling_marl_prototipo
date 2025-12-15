"""Cliente HTTP ligero para integrar SimPy con el servidor JADE vía REST.

Provee `decide_allow` que consulta el endpoint `/decide` y, en caso de
error o timeout, aplica una política fallback (SPT) usando
`scheduling_rules.SchedulingRules`.
"""
import json
import urllib.request
import urllib.error
import socket
from typing import List, Dict, Any

try:
    # prefer requests si está instalado
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False

from ..scheduling_rules import SchedulingRules



DEFAULT_JADE_URL = "http://localhost:5000"
DECIDE_PATH = "/decide"
FEEDBACK_PATH = "/feedback"

def send_feedback(machine_id: int, current_job_id: int, queue_jobs: List[Dict], action: int, reward: float,
                 next_state: str = None, next_actions: List[int] = None, jade_url: str = DEFAULT_JADE_URL,
                 timeout: float = 2.0) -> bool:
    """Envía feedback de aprendizaje al servidor JADE (/feedback).
    Args:
        machine_id: id de la máquina
        current_job_id: id del job procesado
        queue_jobs: lista de dicts (igual que en decide_allow)
        action: índice del job elegido en la cola
        reward: recompensa obtenida
        next_state: representación serializada del siguiente estado (opcional)
        next_actions: lista de acciones posibles en el siguiente estado (opcional)
        jade_url: base URL JADE
        timeout: timeout en segundos
    Returns:
        True si JADE respondió ok, False si hubo error
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

    url = jade_url.rstrip('/') + FEEDBACK_PATH
    # print(f"[JADE-CLIENT] POST {url} payload={json.dumps(payload)}")
    try:
        resp = _http_post(url, payload, timeout=timeout)
        # print(f"[JADE-CLIENT] /feedback resp={resp}")
        return isinstance(resp, dict) and resp.get('ok', False)
    except Exception as e:
        # Mostrar información detallada para depuración en modo ALTO
        try:
            import traceback
            tb = traceback.format_exc()
        except Exception:
            tb = str(e)
        # print(f"[JADE-CLIENT] /feedback failed: {e}\n{tb}")
        return False


def request_decision(machine_id: int, current_job_id: int, queue_jobs: List[Dict], jade_url: str = DEFAULT_JADE_URL,
                     timeout: float = 2.0) -> Dict[str, Any]:
    """Solicita decisión al servidor JADE (/decide).

    Retorna el diccionario parseado de la respuesta, o lanza excepción en fallo.
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
    url = jade_url.rstrip('/') + DECIDE_PATH
    # print(f"[JADE-CLIENT] POST {url} payload={json.dumps(payload)}")
    try:
        resp = _http_post(url, payload, timeout=timeout)
        # print(f"[JADE-CLIENT] /decide resp={resp}")
        return resp
    except Exception as e:
        try:
            import traceback
            tb = traceback.format_exc()
        except Exception:
            tb = str(e)
        # print(f"[JADE-CLIENT] /decide failed: {e}\n{tb}")
        raise


def _http_post(url: str, payload: Dict[str, Any], timeout: float = 0.5) -> Dict[str, Any]:
    """Envía JSON por POST y devuelve el JSON de respuesta.
    Usa `requests` si está disponible, si no, `urllib`.
    Lanza excepción en fallo de conexión o parseo.
    """
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    if _HAS_REQUESTS:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    else:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw.decode("utf-8"))


def decide_allow(machine_id: int, current_job_id: int, queue_jobs: List[Dict],
                scheduling_rule: str = "SPT", jade_url: str = DEFAULT_JADE_URL,
                timeout: float = 0.5) -> bool:
    """Consulta al servidor JADE si el `current_job_id` debe ser procesado ahora.

    Args:
        machine_id: id de la máquina que procesa.
        current_job_id: id del job que quiere procesar.
        queue_jobs: lista de dicts con claves: 'job_id', 'operations' (lista tuplas), 'due_date'
        scheduling_rule: regla por defecto para fallback ('SPT','EDD','LPT')
        jade_url: base URL del servidor JADE
        timeout: timeout en segundos para la llamada HTTP

    Returns:
        True si el job debe procesarse ahora; False si debe ceder la CPU.
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

    url = jade_url.rstrip('/') + DECIDE_PATH
    try:
        resp = _http_post(url, payload, timeout=timeout)
        # esperado: {'allow': True} o {'selected_job': job_id}
        if isinstance(resp, dict):
            if 'allow' in resp:
                return bool(resp['allow'])
            if 'selected_job' in resp:
                return int(resp['selected_job']) == int(current_job_id)
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, ConnectionRefusedError, Exception):
        # fallback silencioso
        pass

    # Fallback local: aplicar regla de despacho (SPT por defecto).
    # Construir jobs_data para SchedulingRules
    jobs_data = [j.get('operations', []) for j in queue_jobs]
    job_ids = [j['job_id'] for j in queue_jobs]

    if not jobs_data:
        return True

    try:
        ordered_indices = SchedulingRules.apply_rule(scheduling_rule, jobs_data)[0]
    except Exception:
        ordered_indices = SchedulingRules.SPT(jobs_data)

    # mapear índice ordenado a job_id y ver si current_job_id es el primero
    first_job_idx = ordered_indices[0]
    first_job_id = job_ids[first_job_idx]
    return int(first_job_id) == int(current_job_id)
