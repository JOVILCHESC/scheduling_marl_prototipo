import zmq
import json

# Conectar a JADE
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

# Preparar request simple
request = {
    "action": "create_order_agent",
    "job_id": 999,
    "operations": [{"machine_id": 0, "processing_time": 10}],
    "due_date": 100.0,
    "current_time": 0.0
}

print(f"[TEST] Enviando request:")
print(json.dumps(request, indent=2))

# Enviar
socket.send_string(json.dumps(request))

# Recibir
response_str = socket.recv_string()
print(f"\n[TEST] Respuesta recibida (raw):")
print(response_str)

# Parsear
try:
    response = json.loads(response_str)
    print(f"\n[TEST] Respuesta parseada:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"\n[ERROR] No se pudo parsear: {e}")

socket.close()
context.term()
