"""
Cálculo de métricas del simulador estático.
Incluye: Makespan, Tardanza, VIP (Work In Progress), Utilización.
"""

import pandas as pd
from typing import Dict, List, Tuple


class MetricsCalculator:
    """Calcula métricas de desempeño del sistema de manufactura."""
    
    def __init__(self, log: List[List], jobs_data: List[List[Tuple]], due_dates: Dict[int, float] = None):
        """
        Args:
            log: Lista de eventos [time, event, job, machine]
            jobs_data: Lista de trabajos con sus operaciones
            due_dates: Diccionario {job_id: due_date} (opcional)
        """
        self.log = log
        self.jobs_data = jobs_data
        self.due_dates = due_dates or {}
        self.df = pd.DataFrame(log, columns=["time", "event", "job", "machine"])
        
    def calculate_makespan(self) -> float:
        """
        Calcula el MAKESPAN: tiempo total desde el primer evento hasta el último.
        Makespan = max(tiempo de finalización de todos los jobs)
        """
        if self.df.empty:
            return 0
        
        finish_events = self.df[self.df["event"] == "finish"]
        if finish_events.empty:
            return 0
            
        makespan = finish_events["time"].max()
        return makespan
    
    def calculate_tardiness(self) -> Tuple[float, float, int]:
        """
        Calcula la TARDANZA (Tardiness):
        - Tardanza total: suma de max(0, end_time - due_date) para cada job
        - Tardanza promedio: tardanza_total / número de jobs con due_date
        
        Returns:
            (tardanza_total, tardanza_promedio, count_with_due_date)
        """
        job_completion_times = {}
        
        # Obtener tiempo de finalización de cada job
        finish_events = self.df[self.df["event"] == "finish"]
        for _, row in finish_events.iterrows():
            job_id = row["job"]
            end_time = row["time"]
            if job_id not in job_completion_times or end_time > job_completion_times[job_id]:
                job_completion_times[job_id] = end_time
        
        tardiness_total = 0
        count = 0
        
        for job_id, completion_time in job_completion_times.items():
            if job_id in self.due_dates:
                due_date = self.due_dates[job_id]
                tardiness = max(0, completion_time - due_date)
                tardiness_total += tardiness
                count += 1
        
        tardiness_avg = tardiness_total / count if count > 0 else 0
        return tardiness_total, tardiness_avg, count
    
    def calculate_vip(self) -> float:
        """
        Calcula VIP (Work In Progress promedio):
        VIP = Número total de trabajos completados / Makespan
        
        Aproximación de la cantidad promedio de trabajos en proceso simultáneamente.
        """
        num_jobs = len(self.jobs_data)
        makespan = self.calculate_makespan()
        
        if makespan == 0:
            return 0
        
        vip = num_jobs / makespan
        return vip
    
    def calculate_machine_utilization(self) -> Dict[int, float]:
        """
        Calcula la UTILIZACIÓN por máquina:
        Utilización = (Tiempo de máquina ocupada) / (Tiempo total de simulación)
        
        Returns:
            Diccionario {machine_id: utilization_percentage}
        """
        makespan = self.calculate_makespan()
        
        if makespan == 0:
            return {}
        
        utilization = {}
        
        # Para cada máquina, calcular tiempo ocupado
        for machine_id in self.df["machine"].unique():
            machine_events = self.df[self.df["machine"] == machine_id]
            
            busy_time = 0
            current_start = None
            
            for _, row in machine_events.sort_values("time").iterrows():
                if row["event"] == "start":
                    current_start = row["time"]
                elif row["event"] == "finish" and current_start is not None:
                    busy_time += row["time"] - current_start
                    current_start = None
            
            utilization[machine_id] = (busy_time / makespan) * 100
        
        return utilization
    
    def calculate_average_utilization(self) -> float:
        """Calcula la utilización promedio de todas las máquinas."""
        util_per_machine = self.calculate_machine_utilization()
        
        if not util_per_machine:
            return 0
        
        avg_util = sum(util_per_machine.values()) / len(util_per_machine)
        return avg_util
    
    def get_all_metrics(self) -> Dict:
        """
        Retorna todas las métricas en un diccionario.
        """
        makespan = self.calculate_makespan()
        tardiness_total, tardiness_avg, tardiness_count = self.calculate_tardiness()
        vip = self.calculate_vip()
        avg_util = self.calculate_average_utilization()
        util_per_machine = self.calculate_machine_utilization()
        
        return {
            "makespan": makespan,
            "tardiness_total": tardiness_total,
            "tardiness_average": tardiness_avg,
            "tardiness_count": tardiness_count,
            "vip": vip,
            "utilization_average": avg_util,
            "utilization_per_machine": util_per_machine
        }
    
    def print_metrics(self, rule_name: str = ""):
        """Imprime un reporte formateado de las métricas."""
        metrics = self.get_all_metrics()
        
        print(f"\n{'='*70}")
        if rule_name:
            print(f"[METRICS] METRICS - RULE: {rule_name}")
        else:
            print(f"[METRICS] SIMULATOR METRICS")
        print(f"{'='*70}")
        print(f"Makespan (tiempo total):          {metrics['makespan']:10.2f} u.t.")
        print(f"Tardanza total:                   {metrics['tardiness_total']:10.2f} u.t.")
        
        if metrics['tardiness_count'] > 0:
            print(f"Tardanza promedio (n={metrics['tardiness_count']}):        {metrics['tardiness_average']:10.2f} u.t.")
        else:
            print(f"Tardanza promedio:                N/A (sin fechas límite)")
        
        print(f"VIP (promedio en proceso):        {metrics['vip']:10.2f} trabajos")
        print(f"Utilización promedio máquinas:    {metrics['utilization_average']:10.2f}%")
        
        if metrics['utilization_per_machine']:
            print(f"\nUtilización por máquina:")
            for machine_id, util in sorted(metrics['utilization_per_machine'].items()):
                print(f"   Máquina {machine_id}: {util:6.2f}%")
        
        print(f"{'='*70}\n")
        
        return metrics
