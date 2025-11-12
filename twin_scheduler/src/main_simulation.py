import os
import json
import simpy
from core.environment import ManufacturingEnv

if __name__ == "__main__":
    # === Rutas seguras ===
    base_path = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_path, "data")
    config_path = os.path.join(data_path, "machines_config.json")
    log_path = os.path.join(data_path, "events_log.csv")

    # === Cargar configuración ===
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"[ERROR] No se encontró el archivo: {config_path}")

    # === Inicializar entorno SimPy ===
    env = simpy.Environment()
    system = ManufacturingEnv(env, config)

    # ============================================================
    # === SELECCIÓN DE REGLA DE DESPACHO =========================
    # Opciones disponibles: "SPT", "EDD", "LPT"
    # ============================================================
    regla = "EDD"  # cambia "SPT" a "EDD" o "LPT" para probar otras reglas
    system.sort_jobs(regla)

    # === Simulación ===
    print("[INFO] Iniciando simulación...\n")
    system.initialize_jobs()
    env.run(until=system.simulation_time)
    print("\n[INFO] Simulación completada.\n")

    # === Métricas ===
    makespan, tardanza, wip, utilizacion = system.compute_metrics()

    # === Exportar log ===
    system.export_log(log_path)
    print(f"[INFO] Log exportado correctamente a: {log_path}")

    # === Guardar métricas resumidas (opcional) ===
    results_path = os.path.join(data_path, f"metrics_{regla}.csv")
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("Regla,Makespan,Tardanza,WIP,Utilizacion\n")
        f.write(f"{regla},{makespan},{tardanza},{wip:.3f},{utilizacion:.3f}\n")

    print(f"[INFO] Métricas guardadas en: {results_path}")
