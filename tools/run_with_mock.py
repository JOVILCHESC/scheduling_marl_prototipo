"""Runner para arrancar mock_jade_server en un hilo y ejecutar el simulador dinámico.

Esto evita depender de múltiples terminales y facilita pruebas E2E rápidas.
"""
import threading
import time
import runpy


def run_mock_server():
    # Ejecutar el script tools/mock_jade_server.py en este hilo
    runpy.run_path('tools/mock_jade_server.py', run_name='__main__')

def main():
    # Iniciar mock en hilo daemon
    t = threading.Thread(target=run_mock_server, daemon=True)
    t.start()
    # Esperar breve para que el servidor esté listo
    time.sleep(0.2)

    # Ejecutar simulador dinámico como módulo
    try:
        import runpy, sys, os
        # Asegurar que el paquete twin_scheduler_simpy sea importable por imports absolutos
        pkg_path = os.path.join(os.getcwd(), 'twin_scheduler_simpy')
        if pkg_path not in sys.path:
            sys.path.insert(0, pkg_path)
        runpy.run_path('twin_scheduler_simpy/simulator_dynamic.py', run_name='__main__')
    except Exception as e:
        print('Error al ejecutar el simulador dinámico:', e)

if __name__ == '__main__':
    main()
