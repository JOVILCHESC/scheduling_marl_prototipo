"""Servidor ZeroMQ mínimo para simular el endpoint JADE.

Uso:
    python tools\mock_jade_server.py

Responde a peticiones REQ-REP en tcp://*:5555.
Soporta mensajes tipo 'decide' y 'feedback'.
"""
import zmq
import json
import time

def run_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    
    print("Mock JADE ZMQ Server listening on tcp://*:5555")

    while True:
        # Esperar petición del cliente
        message = socket.recv_string()
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            socket.send_string(json.dumps({'error': 'invalid json'}))
            continue

        msg_type = payload.get('type', 'decide')

        if msg_type == 'decide':
            # Lógica simple: SPT (Shortest Processing Time) o next_op_duration
            queue = payload.get('queue', [])
            best = None
            best_val = None
            
            for item in queue:
                val = None
                if item.get('next_op_duration') is not None:
                    val = item['next_op_duration']
                else:
                    # Fallback si no hay next_op_duration
                    val = 999999

                if best is None or (val is not None and val < best_val):
                    best = item.get('job_id')
                    best_val = val
            
            # Simular pequeño delay de red/proceso
            # time.sleep(0.001)
            
            response = {'selected_job': best}
            socket.send_string(json.dumps(response))
            print(f"[MOCK] Decided job {best} for machine {payload.get('machine_id')}")

        elif msg_type == 'feedback':
            # Aceptar feedback y responder OK
            # print(f"[MOCK] Received feedback: reward={payload.get('reward')}")
            socket.send_string(json.dumps({'ok': True}))
        
        else:
            socket.send_string(json.dumps({'error': 'unknown type'}))

if __name__ == '__main__':
    run_server()

