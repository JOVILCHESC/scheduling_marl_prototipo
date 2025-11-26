"""
Twin Scheduler SimPy - FASE 1: Simulador Base Estático
======================================================

Módulo de simulación estática usando SimPy para Job Shop Scheduling.

Componentes:
  - metrics.py: Cálculo de métricas (Makespan, Tardanza, VIP, Utilización)
  - scheduling_rules.py: Reglas de despacho (SPT, EDD, LPT)
  - datasets.py: Datasets de benchmark (FT06, FT10)
  - simulator_static.py: Simulador principal
"""

__version__ = "1.0.0"
__author__ = "JOVILCHESC"
__description__ = "Job Shop Scheduler Simulator - Static Environment"

from metrics import MetricsCalculator
from scheduling_rules import SchedulingRules
from datasets import Datasets
from simulator_static import (
    Machine, Job, job_process, run_simulation, run_validation
)

__all__ = [
    "MetricsCalculator",
    "SchedulingRules",
    "Datasets",
    "Machine",
    "Job",
    "job_process",
    "run_simulation",
    "run_validation"
]
