import zmq
import sys

def check_connection():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    
    print("Enviando ping a JADE...")
    # Enviar un mensaje dummy que JADE pueda entender o al menos recibir
    # El protocolo espera JSON con 'machine_id', etc.
    # Enviaremos un mensaje de 'ping' si el servidor lo soporta, o una solicitud malformada para ver si responde error (lo cual implica vida)
    # O mejor, una solicitud válida de prueba.
    
    payload = {
        "type": "decision_request",
        "machine_id": 0,
        "job_id": 999,
        "queue": []
    }
    
    socket.send_json(payload)
    
    # Usar poller para timeout
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    
    if poller.poll(2000): # 2 segundos timeout
        message = socket.recv_json()
        print(f"Respuesta recibida de JADE: {message}")
        return True
    else:
        print("Timeout: JADE no respondió en 2 segundos.")
        return False

if __name__ == "__main__":
    if check_connection():
        print("JADE está CORRIENDO y respondiendo.")
        sys.exit(0)
    else:
        print("JADE NO parece estar corriendo o no responde.")
        sys.exit(1)
