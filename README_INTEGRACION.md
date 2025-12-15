# Integración SimPy ↔ JADE (REST HTTP)

## Opción A: Usar JADE Real (recomendado para pruebas)

### Paso 1: Compilar y levantar el servidor JADE

```bash
cd tt_twin_scheduler_2025
mvn clean package
mvn exec:java
```

El servidor HTTP estará disponible en `http://localhost:5000`. Verás un mensaje como:
```
JADE HTTP API listening on http://localhost:5000
```

### Paso 2: En otra terminal, ejecutar el simulador dinámico SimPy

```bash
python -u twin_scheduler_simpy/simulator_dynamic.py
```

El simulador hará llamadas HTTP a JADE (`/decide` y `/feedback`) para tomar decisiones de despacho en tiempo real.

### Paso 3: Detener JADE cuando termines

Ejecuta en PowerShell:
```powershell
tasklist | findstr java          # Buscar PIDs de procesos Java
taskkill /PID <PID> /F           # Terminar el proceso JADE (reemplaza <PID>)
```

---

## Opción B: Usar Mock JADE (pruebas rápidas sin Java)

Si no necesitas JADE real, puedes usar un servidor mock Python:

```bash
# Terminal 1: Mock JADE
python tools\mock_jade_server.py

# Terminal 2: Simulador SimPy
python -u twin_scheduler_simpy/simulator_dynamic.py
```

El mock responde a `/decide` seleccionando SPT por `next_op_duration`, sin necesidad de Maven/Java.

---

## Endpoints REST Disponibles (JADE o Mock)

### `/decide` (POST)
Recibe estado de máquina + cola de trabajos; retorna job seleccionado.

**Request:**
```json
{
  "machine_id": 0,
  "current_job": 5,
  "queue": [
    {"job_id": 5, "next_op_duration": 3.0},
    {"job_id": 6, "next_op_duration": 7.0}
  ]
}
```

**Response:**
```json
{"selected_job": 5}
```

### `/feedback` (POST)
Recibe recompensa/info de entrenamiento; retorna confirmación.

**Request:**
```json
{
  "job_id": 5,
  "reward": -10.0
}
```

**Response:**
```json
{"ok": true}
```

---

## Comparación de Heurísticas

Para ejecutar comparativa (SPT, EDD, LPT) contra diferentes conjuntos de datos:

```bash
python twin_scheduler_simpy/main_comparison.py
```

Genera CSV con métricas en `twin_scheduler_simpy/logs/`.

---

## Estructura del Proyecto

```
scheduling_marl_prototipo/
├── tt_twin_scheduler_2025/          # Servidor JADE (Java)
│   ├── src/main/java/tt/twin_scheduler/
│   │   ├── MainJADE.java            # HTTP server + JADE bootstrap
│   │   ├── MachineAgent.java
│   │   └── SchedulerAgent.java
│   ├── pom.xml                      # Maven config (Gson, JADE)
│   └── target/                      # Compiled JARs
│
├── twin_scheduler_simpy/            # Simulador dinámico (Python SimPy)
│   ├── src/
│   │   ├── simulator_dynamic.py      # Simulador con llegadas + fallos
│   │   ├── simulator_static.py       # Simulador estático (Fase 1)
│   │   ├── main_comparison.py        # Comparativa de reglas
│   │   ├── integration/
│   │   │   └── jade_http_client.py   # Cliente REST (timeout + fallback)
│   │   └── agents/, core/, utils/
│   ├── notebooks/                   # Jupyter notebooks de validación
│   ├── data/                        # Taillard benchmarks, CSVs
│   ├── logs/                        # Resultados de simulaciones
│   └── requirements.txt
│
├── tools/
│   ├── mock_jade_server.py          # Servidor mock (sin Java)
│   └── run_with_mock.py             # Runner E2E con mock
│
└── README.me                        # Este archivo
```

---

## Próximos Pasos

1. **Implementar Q-learning en JADE**: Agregar lógica de aprendizaje tabular a `SchedulerAgent.java` que utilice `/feedback` para actualizar política.
2. **Entrenar agente MARL**: Ejecutar episodios de entrenamiento apuntando SimPy a JADE + Q-learning.
3. **Comparar resultados**: Generar tablas y gráficos comparativos (heurísticas vs MARL) para defensa de tesis.

---

## Referencias Técnicas

- **SimPy**: Discrete-event simulator para modelar Job Shop dinámico.
- **JADE**: Multi-agent platform Java; HttpServer embedido para REST.
- **Gson**: JSON serialization en Java.
- **requests/urllib**: Cliente HTTP Python (fallback a urllib si no hay requests).
- **Taillard Benchmarks**: Instancias estándar de Job Shop (4x4 a 20x20).
