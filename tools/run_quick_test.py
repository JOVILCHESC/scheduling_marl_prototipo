"""Runner rápido para validar integración SimPy <-> JADE usando configuración corta.
Este script ejecuta una simulación corta (100 u.t.) y exporta resultados con prefijo `quick_test`.
"""

import os
import sys
# Asegurar que el directorio raíz del repo está en sys.path para poder importar el paquete
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from twin_scheduler_simpy.simulator_dynamic import DynamicJobShopSimulator
import simpy

def main():
    env = simpy.Environment()
    simulator = DynamicJobShopSimulator(
        env=env,
        num_machines=6,
        arrival_rate=0.4,
        mtbf=100.0,
        mttr=8.0,
        scheduling_rule="SPT",
        random_seed=42
    )
    # corrida corta
    simulator.run(until_time=120.0, warmup=10.0)
    simulator.export_results(prefix="quick_test")
    print("Quick test finished.")

if __name__ == '__main__':
    main()
