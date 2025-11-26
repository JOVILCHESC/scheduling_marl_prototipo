# Twin Scheduler SimPy - FASE 1 y FASE 2

## Descripción General

**Twin Scheduler** es un simulador de **Job Shop Scheduling** con soporte para eventos dinámicos, fallos de máquinas y generación automática de órdenes. Implementa dos fases:

- **FASE 1**: Simulador base estático con máquinas y colas
- **FASE 2**: Simulador dinámico con llegadas en línea y fallos estocásticos

---

## FASE 1: Simulador Base Estático

### Características

✅ **Máquinas y Colas**
- Máquinas con capacidad = 1 (una operación a la vez)
- Buffers dinámicos por máquina
- Simulación de procesamiento en secuencia

✅ **Cálculo de Métricas**
- Makespan: Tiempo total de fabricación
- Tardanza: Atrasos respecto a due dates
- VIP: Work In Progress promedio
- Utilización: Porcentaje de ocupación

✅ **Reglas de Despacho**
- SPT (Shortest Processing Time)
- EDD (Earliest Due Date)
- LPT (Longest Processing Time)

✅ **Datasets**
- FT06: 6 jobs × 6 máquinas
- FT10: 10 jobs × 10 máquinas

### Archivo Principal
```
simulator_static.py (270 líneas)
```

---

## FASE 2: Simulador Dinámico [NUEVA]

### Características Nuevas

✅ **Llegadas Dinámicas de Órdenes (arrival_generator.py)**
- Proceso de Poisson para inter-arrival times
- Generación automática de operaciones aleatorias
- Due dates dinámicas basadas en operaciones
- Callbacks para notificación de nuevas órdenes

✅ **Fallos de Máquinas (machine_failures.py)**
- Modelo MTBF/MTTR (Mean Time Between/To Repair)
- Distribuciones exponenciales de fallos y reparaciones
- Bloqueo automático durante mantenimiento
- Perfiles de confiabilidad (HIGH, MEDIUM, LOW)
- Estadísticas de disponibilidad por máquina

✅ **Sistema de Eventos Centralizado (event_manager.py)**
- Log estructurado de todos los eventos
- 6 tipos de eventos: ARRIVAL, START, END, FAILURE, REPAIR_END, COMPLETE
- Exportación automática a CSV
- Reportes sumarios con desglose por tipo

✅ **Simulador Dinámico Integrado (simulator_dynamic.py)**
- Integración de todos los módulos
- Máquinas dinámicas con soporte para fallos
- Procesamiento de trabajos con llegadas en línea
- Sistema de colas dinámicas
- Métricas en tiempo real

### Archivos Nuevos

```
arrival_generator.py    (6.1 KB)  - Generador de llegadas dinámicas
machine_failures.py     (8.2 KB)  - Gestor de fallos de máquinas
event_manager.py        (8.5 KB)  - Sistema centralizado de eventos
simulator_dynamic.py    (13.7 KB) - Simulador dinámico integrado
```

---

## Instalación

### 1. Crear entorno virtual

```bash
cd c:\DEV\scheduling_marl_prototipo\twin_scheduler_simpy
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Dependencias:**
- simpy >= 4.1.1
- pandas >= 2.1.4
- numpy >= 1.26.3

---

## Uso

### FASE 1: Simulador Estático

```bash
python simulator_static.py
```

**Salida:**
- Simulaciones con SPT, EDD, LPT
- Comparación de métricas
- CSV con logs: `simulation_log_*.csv`

### FASE 2: Simulador Dinámico

```bash
python simulator_dynamic.py
```

**Salida:**
- 393 órdenes generadas dinámicamente
- 56 eventos de fallo de máquinas
- 2,688 eventos totales registrados
- CSV con eventos: `simulation_dynamic_*.csv`
- CSV con trabajos: `simulation_dynamic_jobs_*.csv`
- CSV con fallos: `simulation_dynamic_failures_*.csv`

---

## Configuración de Parámetros

### Para FASE 2, en `simulator_dynamic.py` función `main()`:

```python
simulator = DynamicJobShopSimulator(
    env=env,
    num_machines=6,           # Número de máquinas
    arrival_rate=0.4,         # Órdenes/unidad de tiempo
    mtbf=100.0,               # Mean Time Between Failures
    mttr=8.0,                 # Mean Time To Repair
    scheduling_rule="SPT",    # Regla de despacho
    random_seed=42            # Para reproducibilidad
)

simulator.run(
    until_time=1000.0,  # Tiempo total de simulación
    warmup=100.0        # Tiempo de calentamiento
)

simulator.export_results()  # Exportar CSV
```

---

## Resultados Ejemplo (FASE 2)

**Configuración:**
- Máquinas: 6
- Tasa llegada: 0.4 órdenes/u.t.
- MTBF: 100 u.t.
- MTTR: 8 u.t.
- Tiempo simulación: 1000 u.t.

**Resultados:**
- Órdenes llegadas: 393
- Órdenes completadas: 143
- Eventos totales: 2,688
- Makespan promedio: 347.76 u.t.
- Tardanza total: 44,600.82 u.t.
- Trabajos atrasados: 142 de 143 (99.3%)
- Downtime total: 381.7 u.t.
- Disponibilidad promedio: 93.6%

### Distribución de Fallos por Máquina

```
Máquina 0: 8 fallos (Downtime: 71.1, Disponibilidad: 92.9%)
Máquina 1: 10 fallos (Downtime: 58.6, Disponibilidad: 94.1%)
Máquina 2: 7 fallos (Downtime: 36.0, Disponibilidad: 96.4%)
Máquina 3: 11 fallos (Downtime: 83.0, Disponibilidad: 91.7%)
Máquina 4: 12 fallos (Downtime: 60.4, Disponibilidad: 94.0%)
Máquina 5: 6 fallos (Downtime: 72.6, Disponibilidad: 92.7%)
```

---

## Estructura de Datos

### Evento (event_manager.py)

```python
@dataclass
class SimulationEvent:
    time: float                 # Timestamp del evento
    event_type: str            # arrival, start, end, failure, repair_end, complete
    job_id: int = None         # ID del trabajo (si aplica)
    machine_id: int = None     # ID de máquina (si aplica)
    duration: float = None     # Duración de operación/reparación
    queue_length: int = None   # Largo de cola en máquina
    additional_info: Dict = None  # Información adicional
```

### Trabajo Dinámico (arrival_generator.py)

```python
@dataclass
class JobSpec:
    job_id: int                        # ID único
    arrival_time: float                # Timestamp de llegada
    operations: List[Tuple[int, int]]  # [(machine_id, duration), ...]
    due_date: float = None             # Fecha de entrega
```

### Evento de Falla (machine_failures.py)

```python
@dataclass
class MachineFailureEvent:
    machine_id: int        # ID de máquina
    failure_time: float    # Timestamp de fallo
    repair_start_time: float
    repair_duration: float
    repair_end_time: float
    downtime: float        # Tiempo total = repair_end - failure
```

---

## Archivos de Salida

### logs/simulation_dynamic_*.csv
Evento por evento con estructura:
```
time, event_type, job_id, machine_id, duration, queue_length, additional_info
428.8, failure, , 2, , , {'repair_duration': 1.6}
429.6, start, 100, 0, 9, 39, 
429.7, arrival, 185, , , , {'num_operations': 5}
```

### logs/simulation_dynamic_jobs_*.csv
Métricas por trabajo:
```
job_id, arrival_time, completion_time, makespan, due_date, tardiness
1, 0.0, 347.6, 347.6, 523.5, 0.0
2, 1.2, 475.8, 474.6, 425.1, 50.7
```

### logs/simulation_dynamic_failures_*.csv
Historial de fallos:
```
machine_id, failure_time, repair_start, repair_duration, repair_end, total_downtime
0, 428.8, 428.8, 1.6, 430.4, 1.6
1, 429.6, 429.6, 5.2, 434.8, 5.2
```

---

## Comparación FASE 1 vs FASE 2

| Aspecto | FASE 1 | FASE 2 |
|---------|--------|--------|
| Llegadas | Predefinidas | ✅ Dinámicas (Poisson) |
| Fallos | No | ✅ MTBF/MTTR |
| Disponibilidad | 100% | ✅ 91-96% |
| Tipos eventos | 3 | ✅ 6 tipos |
| Log | Básico | ✅ Estructurado |
| Realismo | Bajo | ✅ Alto |

---

## Próximas Fases

### FASE 3: Multi-Agent Reinforcement Learning (MARL)

Planeado para incorporar:
- Agentes inteligentes para despacho de órdenes
- Q-Learning o Policy Gradient
- Comunicación entre agentes
- Comparación con heurísticas
- Convergencia y evaluación

---

## Documentación Adicional

- `PHASE1_SUMMARY.txt` - Resumen detallado de Fase 1
- `PHASE2_SUMMARY.txt` - Resumen detallado de Fase 2

---

## Autor

GitHub Copilot
Fecha: 26 de Noviembre de 2025
Versión: 2.0 (FASE 1 + FASE 2)
