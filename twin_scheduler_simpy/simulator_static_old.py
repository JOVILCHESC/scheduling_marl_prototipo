import simpy
import pandas as pd

class Machine:
    """Representa una máquina del job shop."""
    def __init__(self, env, machine_id):
        self.env = env
        self.id = machine_id
        self.resource = simpy.Resource(env, capacity=1)

    def process(self, job_id, duration):
        """Procesar una operación durante `duration`."""
        yield self.env.timeout(duration)


class Job:
    """Representa un trabajo que tiene una secuencia de operaciones."""
    def __init__(self, job_id, operations):
        self.id = job_id
        self.operations = operations
        self.current_op = 0


def job_process(env, job: Job, machines, log):
    """Simula todas las operaciones de un job."""
    for (machine_id, duration) in job.operations:
        machine = machines[machine_id]

        with machine.resource.request() as req:
            yield req
            start = env.now
            log.append([env.now, "start", job.id, machine_id])
            yield env.process(machine.process(job.id, duration))
            log.append([env.now, "finish", job.id, machine_id])

    print(f"Job {job.id} completado en t={env.now}")


def load_ft06():
    """
    Carga el dataset FT06 del Job Shop Scheduling Benchmark.
    Formato: lista de trabajos, cada trabajo es
    [(machine, processing_time), ...]
    """

    # FT06 DATA:
    data = [
        [ (1,1), (2,3), (3,6), (4,7), (5,3), (0,6) ],
        [ (2,8), (3,5), (4,10), (5,10), (0,10), (1,4) ],
        [ (3,5), (4,4), (5,8), (0,9), (1,1), (2,7) ],
        [ (4,5), (5,5), (0,5), (1,3), (2,8), (3,9) ],
        [ (5,9), (0,3), (1,5), (2,4), (3,3), (4,1) ],
        [ (0,3), (1,3), (2,9), (3,10), (4,4), (5,1) ],
    ]
    return data


def run_simulation():
    env = simpy.Environment()
    ft_data = load_ft06()

    N_MACHINES = 6
    machines = [Machine(env, i) for i in range(N_MACHINES)]

    # Crear jobs
    jobs = [Job(jid, ops) for jid, ops in enumerate(ft_data)]

    log = []

    # Iniciar procesos
    for job in jobs:
        env.process(job_process(env, job, machines, log))

    env.run()

    df = pd.DataFrame(log, columns=["time", "event", "job", "machine"])
    df.to_csv("static_log.csv", index=False)
    print(df.head())

if __name__ == "__main__":
    run_simulation()
