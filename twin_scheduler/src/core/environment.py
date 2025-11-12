import simpy
import csv

class ManufacturingEnv:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        self.simulation_time = config.get("simulation_time", 100)

        # Crear máquinas
        self.machines = {m["id"]: simpy.Resource(env, capacity=1) for m in config["machines"]}

        # Lista de trabajos
        self.jobs = config["jobs"]
        self.completed_jobs = []
        self.start_times = {}
        self.end_times = {}

        # 🔹 Nuevo: almacenamiento detallado de operaciones (para el log)
        self.operation_logs = []

    # === Inicialización de procesos ===
    def initialize_jobs(self):
        for job in self.jobs:
            self.env.process(self.process_job(job))

    # === Proceso principal de cada job ===
    def process_job(self, job):
        job_id = job["id"]
        self.start_times[job_id] = self.env.now
        print(f"[{self.env.now}] Iniciando Job {job_id}")

        for op in job["operations"]:
            machine_id = op["machine"]
            duration = op["duration"]

            with self.machines[machine_id].request() as req:
                yield req
                start_time = self.env.now
                print(f"[{self.env.now}] {job_id} procesando en {machine_id} ({duration} u.t.)")
                yield self.env.timeout(duration)
                end_time = self.env.now

                # 🔹 Guardar evento individual por operación
                self.operation_logs.append({
                    "JobID": job_id,
                    "Machine": machine_id,
                    "Start": start_time,
                    "End": end_time,
                    "Duration": end_time - start_time
                })

        self.end_times[job_id] = self.env.now
        self.completed_jobs.append(job_id)
        print(f"[{self.env.now}] Job {job_id} completado")

    # === Calcular métricas ===
    def compute_metrics(self):
        makespan = max(self.end_times.values()) - min(self.start_times.values())
        tardiness = sum(
            max(0, self.end_times[j] - self.config["jobs"][i].get("due_date", 0))
            for i, j in enumerate(self.completed_jobs)
        )
        wip = len(self.completed_jobs) / (self.env.now + 1)
        utilization = self._machine_utilization()

        print("\n--- MÉTRICAS ---")
        print(f"Makespan: {makespan}")
        print(f"Tardanza total: {tardiness}")
        print(f"WIP promedio: {wip:.2f}")
        print(f"Utilización estimada: {utilization:.2f}")
        return makespan, tardiness, wip, utilization

    def _machine_utilization(self):
        busy = 0
        for m in self.machines.values():
            busy += len(m.queue)
        return busy / self.env.now if self.env.now > 0 else 0

    # === Exportar log ===
    def export_log(self, filepath):
        """
        Exporta el log detallado de operaciones a CSV,
        con una fila por cada operación ejecutada.
        Formato: JobID,Machine,Start,End,Duration
        """
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["JobID", "Machine", "Start", "End", "Duration"])
                writer.writeheader()
                for op in self.operation_logs:
                    writer.writerow({
                        "JobID": op["JobID"],
                        "Machine": op["Machine"],
                        "Start": round(op["Start"], 2),
                        "End": round(op["End"], 2),
                        "Duration": round(op["Duration"], 2)
                    })
            print(f"[INFO] Log detallado exportado correctamente: {filepath}")
        except Exception as e:
            print(f"[ERROR] No se pudo exportar el log: {e}")

    # ============================================================
    # === REGLAS DE REFERENCIA: SPT, EDD, LPT ====================
    # ============================================================

    def sort_jobs(self, rule="SPT"):
        """
        Ordena los trabajos según la regla seleccionada.
        Opciones:
            - SPT: Shortest Processing Time
            - EDD: Earliest Due Date
            - LPT: Longest Processing Time
        """
        print(f"\n[INFO] Aplicando regla de despacho: {rule}")

        if rule == "SPT":
            # Ordena por tiempo total de procesamiento más corto
            self.jobs.sort(key=lambda j: sum(op["duration"] for op in j["operations"]))

        elif rule == "EDD":
            # Ordena por fecha de entrega más temprana
            self.jobs.sort(key=lambda j: j.get("due_date", float("inf")))

        elif rule == "LPT":
            # Ordena por tiempo total de procesamiento más largo
            self.jobs.sort(key=lambda j: -sum(op["duration"] for op in j["operations"]))

        else:
            print("[WARN] Regla desconocida, no se aplicó ningún ordenamiento.")
        
        # Mostrar orden final
        print("[INFO] Orden de trabajos después de aplicar la regla:")
        for job in self.jobs:
            print(f"   - {job['id']}")
