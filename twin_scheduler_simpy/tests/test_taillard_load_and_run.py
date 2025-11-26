"""Prueba rápida: cargar primera instancia de datasets/jobshop1.txt y ejecutar simulador estático.
"""
from twin_scheduler_simpy.datasets import Datasets
from twin_scheduler_simpy.simulator_static import run_simulation


def main():
    path_key = "TA:datasets/jobshop1.txt:1"
    print(f"Cargando dataset {path_key}...")
    jobs, due = Datasets.load_dataset(path_key)
    print(f"Jobs cargados: {len(jobs)}, máquinas (estimadas): {len({m for job in jobs for m,_ in job})}")

    print("Ejecutando simulador estático (verbose=False, export_log=False)...")
    res = run_simulation(jobs, due, rule='SPT', dataset_name='TA_jobshop1_1', verbose=False, export_log=False)
    print("Resultado:", res['rule'], res['dataset'], "jobs_completed=", res['jobs_completed'])


if __name__ == '__main__':
    main()
