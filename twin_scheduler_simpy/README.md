# 🏭 Twin Scheduler SimPy - FASE 1: Simulador Base Estático

## Descripción General

Este es el **simulador base (entorno estático)** para el Job Shop Scheduling Problem usando SimPy. Implementa un ambiente determinístico con máquinas, trabajos y colas (buffers) para simular y analizar el desempeño de diferentes reglas de despacho.

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
├── simulator_static.py          # 🎯 Simulador principal
├── metrics.py                    # 📊 Cálculo de métricas
├── scheduling_rules.py           # 📋 Reglas de despacho (SPT, EDD, LPT)
├── datasets.py                   # 📦 Datasets de benchmark
├── __init__.py                   # Módulo inicializador
├── requirements.txt              # Dependencias Python
├── README.md                     # Este archivo
├── simulator_static_old.py       # Backup del código anterior
└── venv/                         # Entorno virtual Python
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

## Uso

### Ejecución Rápida (Validación Completa)

```bash
python simulator_static.py
```

Esto ejecutará una validación completa que:
1. Carga el dataset FT06
2. Ejecuta simulaciones con las 3 reglas (SPT, EDD, LPT)
3. Compara métricas y resultados
4. Genera archivos CSV con logs y resultados

**Salida esperada:**
```
======================================================================
📊 VALIDACIÓN DEL SIMULADOR BASE
======================================================================

Ejecutando simulación con regla SPT...
[...]
Ejecutando simulación con regla EDD...
[...]
Ejecutando simulación con regla LPT...
[...]

======================================================================
📈 COMPARACIÓN DE REGLAS
======================================================================

Regla Makespan Tardanza Total Tardanza Promedio  VIP Utilización %
  SPT    49.00          29.00              4.83 0.12         67.01
  EDD    49.00          29.00              4.83 0.12         67.01
  LPT    49.00          29.00              4.83 0.12         67.01
```

### Uso Programático

```python
from simulator_static import run_simulation, run_validation
from datasets import Datasets

# Opción 1: Validación completa
results = run_validation(dataset_name="FT06", verbose=False)

# Opción 2: Simulación individual
jobs_data, due_dates = Datasets.load_dataset("FT06")
result = run_simulation(
    jobs_data, 
    due_dates, 
    rule="SPT",
    dataset_name="FT06",
    verbose=True,
    export_log=True
)

# Acceder a métricas
metrics = result["metrics"]
print(f"Makespan: {metrics['makespan']}")
print(f"Utilización: {metrics['utilization_average']:.2f}%")
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
