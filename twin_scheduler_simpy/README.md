# 🏭 Twin Scheduler SimPy - FASE 1 + FASE 2

## Descripción General

Proyecto integrado de simulación Job Shop con dos fases:
- **Fase 1 (Estático)**: Simulador determinístico con reglas de despacho heurísticas (SPT, EDD, LPT)
- **Fase 2 (Dinámico)**: Simulador con llegadas dinámicas, fallos de máquinas y reparaciones

Ambas fases pueden ejecutarse **independientemente** o en **comparación directa** usando instancias Taillard como datos compartidos.

### Características Implementadas (Fase 1)

✅ **Simulador SimPy con máquinas y colas**
- Máquinas como recursos con capacidad = 1
- Trabajos con operaciones en secuencia
- Buffers por máquina para las colas

✅ **Cálculo de Métricas**
- **Makespan**: Tiempo total de fabricación
- **Tardanza**: Suma de atrasos respecto a fechas de entrega
- **VIP**: Work In Progress promedio
- **Utilización**: Porcentaje de ocupación de máquinas

✅ **Reglas de Despacho Implementadas**
- **SPT** (Shortest Processing Time): Trabajos cortos primero
- **EDD** (Earliest Due Date): Fecha de entrega más temprana primero
- **LPT** (Longest Processing Time): Trabajos largos primero

✅ **Datasets de Benchmark**
- **FT06**: 6 jobs × 6 máquinas (pequeño, rápido)
- **FT10**: 10 jobs × 10 máquinas (mediano)

✅ **Validación y Reportes**
- Comparación de rendimiento entre reglas
- Exportación de logs en CSV
- Reportes formateados en consola

---

## Estructura de Archivos

```
twin_scheduler_simpy/
├── FASE 1: Simulador Estático
│   ├── simulator_static.py          # Simulador principal
│   ├── metrics.py                    # Cálculo de métricas
│   ├── scheduling_rules.py           # Reglas de despacho (SPT, EDD, LPT)
│   ├── datasets.py                   # Loader de datasets (FT06, FT10, Taillard)
│
├── FASE 2: Simulador Dinámico
│   ├── simulator_dynamic.py          # Simulador con llegadas y fallos
│   ├── arrival_generator.py          # Generador de llegadas (Poisson)
│   ├── machine_failures.py           # Gestor de fallos (MTBF/MTTR)
│   ├── event_manager.py              # Logger centralizado de eventos
│
├── Integración y Comparación
│   ├── main_comparison.py            # Script de comparación Fase 1 vs Fase 2
│   ├── taillard_integration.py       # Conversor Taillard -> llegadas escalonadas
│   ├── taillard_loader.py            # Parser de instancias Taillard
│
├── Datos y Documentación
│   ├── datasets/
│   │   ├── jobshop1.txt              # Instancias Taillard (abz5-abz9, ft06, ft10, etc.)
│   │   └── jobshop2.txt              # Más instancias Taillard
│   ├── logs/                         # Logs y CSVs de simulaciones
│   ├── README.md                     # Este archivo
│   ├── PHASE1_SUMMARY.txt            # Resumen de Fase 1
│   ├── PHASE2_SUMMARY.txt            # Resumen de Fase 2
│
├── Infraestructura
│   ├── __init__.py                   # Módulo inicializador
│   ├── requirements.txt              # Dependencias Python
│   ├── venv/                         # Entorno virtual Python
│   └── tests/                        # Pruebas rápidas
│       └── test_taillard_load_and_run.py
```

---

## Instalación

### 1. Crear y activar entorno virtual

```bash
cd c:\DEV\scheduling_marl_prototipo\twin_scheduler_simpy
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Dependencias

- **simpy**: 4.1.1 - Simulación discreta de eventos
- **pandas**: 2.1.4 - Análisis y manipulación de datos
- **numpy**: 1.26.3 - Computación numérica

---

---

## Uso: Tres Modos de Ejecución

### 1️⃣ FASE 1 SOLO (Simulador Estático Independiente)

Para ejecutar **solo la Fase 1** sin Fase 2:

```bash
cd c:\DEV\scheduling_marl_prototipo\twin_scheduler_simpy
.venv\Scripts\python.exe simulator_static.py
```

Esto carga FT06 por defecto y ejecuta validación con SPT, EDD, LPT.

**Salida:** Makespan, Tardanza, Utilización por máquina. Archivos CSV con logs.

### 2️⃣ FASE 2 SOLO (Simulador Dinámico Independiente)

Para ejecutar **solo la Fase 2** con llegadas aleatorias y fallos:

```bash
cd c:\DEV\scheduling_marl_prototipo\twin_scheduler_simpy
.venv\Scripts\python.exe simulator_dynamic.py
```

Genera jobs con llegadas Poisson (λ=0.4) y fallos de máquinas (MTBF=100, MTTR=8).

**Salida:** Eventos de llegada/falla/reparación, downtime, disponibilidad. Archivos CSV.

### 3️⃣ COMPARACIÓN COMPLETA (Fase 1 + Fase 2 con datos Taillard)

Para ejecutar **ambas fases juntas** con los mismos datos y obtener reporte comparativo:

```bash
cd c:\DEV\scheduling_marl_prototipo\twin_scheduler_simpy
.venv\Scripts\python.exe -m twin_scheduler_simpy.main_comparison
```

**Parámetros opcionales:**

```bash
# Usar una instancia Taillard diferente
.venv\Scripts\python.exe -m twin_scheduler_simpy.main_comparison --dataset TA:datasets/jobshop1.txt:abz5 --rules SPT,EDD

# Cambiar MTBF y MTTR de Fase 2
.venv\Scripts\python.exe -m twin_scheduler_simpy.main_comparison --mtbf 200 --mttr 15

# Cambiar distribución de llegadas escalonadas
.venv\Scripts\python.exe -m twin_scheduler_simpy.main_comparison --arrival-dist poisson
```

**Salida:** Tabla comparativa CSV con columnas:
- Regla | Makespan F1 | Makespan F2 | Delta Makespan | Tardanza F1 | Tardanza F2 | Delta Tardanza | Jobs Completados F2 | Downtime F2 | Disponibilidad F2

---

## Datasets Disponibles

### Datasets Integrados (Fase 1)
- **FT06**: 6 jobs × 6 máquinas (muy rápido)
- **FT10**: 10 jobs × 10 máquinas (rápido)

Uso:
```python
from datasets import Datasets
jobs, due_dates = Datasets.load_dataset("FT06")
jobs, due_dates = Datasets.load_dataset("FT10")
```

### Instancias Taillard (Fase 1 + Fase 2)
Archivos: `datasets/jobshop1.txt`, `datasets/jobshop2.txt`

Contienen ~80 instancias: abz5-abz9, ft06, ft10, ft20, la01-la40, orb01-orb10, swv01-swv20, yn1-yn4, ta01-ta80

Uso:
```python
from datasets import Datasets

# Cargar por índice (1-based)
jobs, due_dates = Datasets.load_dataset("TA:datasets/jobshop1.txt:1")     # Primera instancia

# Cargar por nombre
jobs, due_dates = Datasets.load_dataset("TA:datasets/jobshop1.txt:abz5")  # Instancia abz5
jobs, due_dates = Datasets.load_dataset("TA:datasets/jobshop1.txt:ft06")  # Instancia ft06

# En Fase 2 (comparación)
python main_comparison.py --dataset TA:datasets/jobshop1.txt:abz5
```

---

## Uso Programático

### Fase 1 (Estático)

```python
from simulator_static import run_simulation, run_validation
from datasets import Datasets

# Validación completa con FT06
results = run_validation(dataset_name="FT06", verbose=False)

# Simulación individual
jobs, due_dates = Datasets.load_dataset("FT06")
result = run_simulation(jobs, due_dates, rule="SPT", verbose=True)
print(result["metrics"]["makespan"])
```

### Fase 2 (Dinámico)

```python
import simpy
from simulator_dynamic import DynamicJobShopSimulator

env = simpy.Environment()
sim = DynamicJobShopSimulator(
    env=env,
    num_machines=6,
    arrival_rate=0.4,
    mtbf=100.0,
    mttr=8.0,
    scheduling_rule="SPT"
)
sim.run(until_time=1000.0)
sim.export_results()
```

### Comparación (Ambas Fases)

```python
from main_comparison import run_phase1_batch, run_phase2_batch, generate_comparison_report
from datasets import Datasets

jobs, due_dates = Datasets.load_dataset("TA:datasets/jobshop1.txt:1")

# Fase 1
results_f1 = run_phase1_batch(jobs, due_dates, ["SPT", "EDD"])

# Fase 2
results_f2 = run_phase2_batch(jobs, due_dates, ["SPT", "EDD"])

# Reporte
df = generate_comparison_report(results_f1, results_f2, ["SPT", "EDD"])
print(df)
```


---

## Archivos Generados

Después de ejecutar la simulación, se generan los siguientes archivos:

### 📊 Logs de Simulación
```
simulation_log_SPT_20251125_034202.csv
simulation_log_EDD_20251125_034202.csv
simulation_log_LPT_20251125_034202.csv
```

Formato:
```
time,event,job,machine
0.0,start,4,1
1.0,finish,4,1
1.0,start,4,2
...
```

### 📈 Resultados Comparativos
```
validation_results_FT06_20251125_034202.csv
```

Formato:
```
Regla,Makespan,Tardanza Total,Tardanza Promedio,VIP,Utilización %
SPT,49.00,29.00,4.83,0.12,67.01
EDD,49.00,29.00,4.83,0.12,67.01
LPT,49.00,29.00,4.83,0.12,67.01
```

---

## Descripción de Clases

### `Machine`
Representa una máquina del job shop.

```python
machine = Machine(env, machine_id=0)
```

**Atributos:**
- `id`: Identificador único
- `resource`: Recurso SimPy (capacidad = 1)
- `queue`: Cola de trabajos esperando

### `Job`
Representa un trabajo con operaciones en secuencia.

```python
job = Job(job_id=0, operations=[(0, 5), (1, 3), (2, 4)])
```

**Atributos:**
- `id`: Identificador único
- `operations`: Lista de (machine_id, duration)
- `arrival_time`: Tiempo de llegada al sistema
- `completion_time`: Tiempo de finalización

### `MetricsCalculator`
Calcula métricas de desempeño.

```python
calc = MetricsCalculator(log, jobs_data, due_dates)
metrics = calc.print_metrics(rule_name="SPT")
```

**Métodos:**
- `calculate_makespan()`: Retorna el makespan
- `calculate_tardiness()`: Retorna (tardanza_total, tardanza_avg, count)
- `calculate_vip()`: Retorna VIP promedio
- `calculate_machine_utilization()`: Retorna utilización por máquina
- `get_all_metrics()`: Retorna diccionario con todas las métricas

### `SchedulingRules`
Implementa reglas de despacho estáticas.

```python
ordered = SchedulingRules.SPT(jobs_data)
ordered = SchedulingRules.EDD(jobs_data, due_dates)
ordered = SchedulingRules.LPT(jobs_data)
```

**Métodos estáticos:**
- `SPT()`: Shortest Processing Time
- `EDD()`: Earliest Due Date
- `LPT()`: Longest Processing Time
- `apply_rule()`: Aplica una regla y retorna orden

### `Datasets`
Gestiona datasets de benchmark.

```python
jobs, due_dates = Datasets.load_dataset("FT06")
Datasets.print_dataset_info(jobs, due_dates, "FT06")
```

**Métodos estáticos:**
- `load_ft06()`: Carga FT06 (6x6)
- `load_ft10()`: Carga FT10 (10x10)
- `load_dataset()`: Carga un dataset por nombre
- `get_available_datasets()`: Lista datasets disponibles

---

## Métricas Explicadas

### Makespan
**Definición:** Tiempo total desde que comienza la simulación hasta que se completa el último job.

**Fórmula:** `Makespan = max(completion_time)`

**Interpretación:** Menor makespan = mejor eficiencia general

### Tardanza (Tardiness)
**Definición:** Suma de los atrasos respecto a las fechas de entrega.

**Fórmula:** `Tardiness = Σ max(0, completion_time - due_date)`

**Interpretación:** Menor tardanza = menos jobs atrasados

### VIP (Work In Progress)
**Definición:** Número promedio de trabajos en proceso simultáneamente.

**Fórmula:** `VIP = número_de_jobs / makespan`

**Interpretación:** Menor VIP = menos congestión en el sistema

### Utilización
**Definición:** Porcentaje de tiempo que cada máquina está ocupada.

**Fórmula:** `Utilización = (tiempo_ocupado / tiempo_total) × 100%`

**Interpretación:** Mayor utilización = mejor uso de recursos

---

## Ejemplos de Uso Avanzado

### Ejemplo 1: Simular solo con FT10

```python
from simulator_static import run_validation

results = run_validation(dataset_name="FT10", verbose=True)
```

### Ejemplo 2: Simulación con una sola regla

```python
from simulator_static import run_simulation
from datasets import Datasets

jobs, due_dates = Datasets.load_dataset("FT06")

result = run_simulation(
    jobs, 
    due_dates,
    rule="EDD",
    verbose=True,
    export_log=True
)

print(f"Makespan: {result['metrics']['makespan']}")
print(f"Tardanza: {result['metrics']['tardiness_total']}")
```

### Ejemplo 3: Acceder a los logs programáticamente

```python
from simulator_static import run_simulation
from datasets import Datasets
import pandas as pd

jobs, due_dates = Datasets.load_dataset("FT06")

result = run_simulation(jobs, due_dates, rule="SPT", export_log=False)

# Convertir log a DataFrame
df = pd.DataFrame(result["log"], columns=["time", "event", "job", "machine"])

# Filtrar eventos de inicio
start_events = df[df["event"] == "start"]
print(start_events)

# Agrupar por máquina
by_machine = df.groupby("machine")["time"].count()
print(by_machine)
```

---

## Notas Importantes

### ⚠️ Comportamiento Esperado en FT06
Las tres reglas (SPT, EDD, LPT) generan el mismo makespan porque el dataset FT06 es pequeño y las restricciones de precedencia entre máquinas dominan más que el orden de inicio. Este es un comportamiento **normal** en datasets constringidos.

### 📝 Datos Generados
- Los archivos CSV se generan con timestamp para evitar sobrescrituras
- Cada simulación crea un nuevo CSV con el log completo
- Los resultados de validación se comparan en un único archivo

### 🔧 Personalización
Para agregar nuevos datasets, editar `datasets.py`:
```python
@staticmethod
def load_my_dataset() -> Tuple[List[List[Tuple[int, int]]], Dict[int, float]]:
    jobs = [...]  # tu dataset
    due_dates = {...}  # tus fechas de entrega
    return jobs, due_dates
```

---

## Próximas Fases

- **Fase 2:** Extensión dinámica (incorporar SPADE agents)
- **Fase 3:** Digital Twin con datos en tiempo real
- **Fase 4:** Integración con JADE (tt_twin_scheduler_2025)

---

## Autor
**JOVILCHESC** - Noviembre 2025

## Licencia
Proyecto de investigación en Scheduling Inteligente Multi-Agente
