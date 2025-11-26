"""
Reglas de despacho (scheduling rules) para ordenar trabajos.
Implementa: SPT, EDD, LPT
"""

from typing import List, Tuple, Callable


class SchedulingRules:
    """Implementa reglas de despacho para ordenar trabajos."""
    
    @staticmethod
    def get_job_processing_time(job_operations: List[Tuple[int, int]]) -> int:
        """
        Calcula el tiempo total de procesamiento de un job.
        Args:
            job_operations: Lista de (machine_id, duration)
        Returns:
            Suma de duraciones de todas las operaciones
        """
        return sum(duration for _, duration in job_operations)
    
    @staticmethod
    def SPT(jobs_data: List[List[Tuple]], due_dates: dict = None) -> List[int]:
        """
        SPT - Shortest Processing Time
        Ordena trabajos por tiempo total de procesamiento (ascendente).
        Los trabajos más cortos se ejecutan primero.
        
        Args:
            jobs_data: Lista de trabajos, cada uno con sus operaciones
            due_dates: Diccionario opcional {job_id: due_date}
        
        Returns:
            Lista de índices de jobs ordenados por SPT
        """
        job_indices = list(range(len(jobs_data)))
        job_times = [
            SchedulingRules.get_job_processing_time(jobs_data[i])
            for i in job_indices
        ]
        
        # Ordenar por tiempo de procesamiento (menor primero)
        sorted_indices = sorted(job_indices, key=lambda i: job_times[i])
        
        return sorted_indices
    
    @staticmethod
    def EDD(jobs_data: List[List[Tuple]], due_dates: dict = None) -> List[int]:
        """
        EDD - Earliest Due Date
        Ordena trabajos por fecha de entrega más temprana.
        
        Args:
            jobs_data: Lista de trabajos (no se usa directamente)
            due_dates: Diccionario {job_id: due_date}
        
        Returns:
            Lista de índices de jobs ordenados por EDD
        """
        if not due_dates:
            # Si no hay fechas de entrega, usar orden original
            return list(range(len(jobs_data)))
        
        job_indices = list(range(len(jobs_data)))
        
        # Ordenar por fecha de entrega (menor primero)
        sorted_indices = sorted(
            job_indices,
            key=lambda i: due_dates.get(i, float('inf'))
        )
        
        return sorted_indices
    
    @staticmethod
    def LPT(jobs_data: List[List[Tuple]], due_dates: dict = None) -> List[int]:
        """
        LPT - Longest Processing Time
        Ordena trabajos por tiempo total de procesamiento (descendente).
        Los trabajos más largos se ejecutan primero.
        
        Args:
            jobs_data: Lista de trabajos, cada uno con sus operaciones
            due_dates: Diccionario opcional {job_id: due_date}
        
        Returns:
            Lista de índices de jobs ordenados por LPT
        """
        job_indices = list(range(len(jobs_data)))
        job_times = [
            SchedulingRules.get_job_processing_time(jobs_data[i])
            for i in job_indices
        ]
        
        # Ordenar por tiempo de procesamiento (mayor primero)
        sorted_indices = sorted(job_indices, key=lambda i: job_times[i], reverse=True)
        
        return sorted_indices
    
    @staticmethod
    def apply_rule(rule_name: str, jobs_data: List[List[Tuple]], 
                   due_dates: dict = None) -> Tuple[List[int], str]:
        """
        Aplica una regla de despacho y retorna el orden de jobs.
        
        Args:
            rule_name: Nombre de la regla ('SPT', 'EDD', 'LPT')
            jobs_data: Lista de trabajos con sus operaciones
            due_dates: Diccionario opcional {job_id: due_date}
        
        Returns:
            Tupla (lista_ordenada_de_indices, descripcion_de_regla)
        """
        if rule_name.upper() == "SPT":
            ordered = SchedulingRules.SPT(jobs_data, due_dates)
            desc = "SPT - Shortest Processing Time (trabajos más cortos primero)"
        elif rule_name.upper() == "EDD":
            ordered = SchedulingRules.EDD(jobs_data, due_dates)
            desc = "EDD - Earliest Due Date (fecha de entrega más temprana primero)"
        elif rule_name.upper() == "LPT":
            ordered = SchedulingRules.LPT(jobs_data, due_dates)
            desc = "LPT - Longest Processing Time (trabajos más largos primero)"
        else:
            raise ValueError(f"Regla desconocida: {rule_name}. Use 'SPT', 'EDD' o 'LPT'")
        
        return ordered, desc
    
    @staticmethod
    def print_schedule(rule_name: str, ordered_indices: List[int], 
                      jobs_data: List[List[Tuple]], due_dates: dict = None):
        """
        Imprime un reporte formateado del orden de despacho.
        """
        print(f"\n{'='*70}")
        print(f"[SCHEDULE] REGLA DE DESPACHO: {rule_name.upper()}")
        print(f"{'='*70}")
        
        print(f"\nOrden de ejecución:")
        for position, job_idx in enumerate(ordered_indices, 1):
            proc_time = SchedulingRules.get_job_processing_time(jobs_data[job_idx])
            due_date = due_dates.get(job_idx, "N/A") if due_dates else "N/A"
            
            print(f"   {position:2d}. Job {job_idx:2d} | "
                  f"Tiempo procesamiento: {proc_time:5.0f} u.t. | "
                  f"Fecha entrega: {due_date}")
        
        print(f"{'='*70}\n")
