"""
Datasets de benchmarks para Job Shop Scheduling.
Incluye: FT06, FT10, y funciones para cargar datos.
"""

from typing import List, Tuple, Dict
from typing import Optional
from .taillard_loader import load_taillard_file


class Datasets:
    """Contiene datasets de benchmark para Job Shop Scheduling."""
    
    @staticmethod
    def load_ft06() -> Tuple[List[List[Tuple[int, int]]], Dict[int, float]]:
        """
        Dataset FT06 del Benchmark Job Shop Scheduling.
        Contiene 6 jobs y 6 máquinas.
        
        Formato: cada job es una lista de (machine_id, processing_time)
        
        Returns:
            (jobs_data, due_dates)
            - jobs_data: Lista de trabajos con operaciones
            - due_dates: Diccionario {job_id: due_date}
        """
        
        # FT06: 6 Jobs x 6 Machines
        jobs = [
            [(1, 1), (2, 3), (3, 6), (4, 7), (5, 3), (0, 6)],      # Job 0
            [(2, 8), (3, 5), (4, 10), (5, 10), (0, 10), (1, 4)],   # Job 1
            [(3, 5), (4, 4), (5, 8), (0, 9), (1, 1), (2, 7)],      # Job 2
            [(4, 5), (5, 5), (0, 5), (1, 3), (2, 8), (3, 9)],      # Job 3
            [(5, 9), (0, 3), (1, 5), (2, 4), (3, 3), (4, 1)],      # Job 4
            [(0, 3), (1, 3), (2, 9), (3, 10), (4, 4), (5, 1)],     # Job 5
        ]
        
        # Due dates para FT06 (estimados basados en total processing time)
        due_dates = {
            0: 55,   # Job 0: 26 u.t., due date = 55
            1: 68,   # Job 1: 47 u.t., due date = 68
            2: 34,   # Job 2: 34 u.t., due date = 34
            3: 35,   # Job 3: 35 u.t., due date = 35
            4: 25,   # Job 4: 25 u.t., due date = 25
            5: 30,   # Job 5: 30 u.t., due date = 30
        }
        
        return jobs, due_dates
    
    @staticmethod
    def load_ft10() -> Tuple[List[List[Tuple[int, int]]], Dict[int, float]]:
        """
        Dataset FT10 del Benchmark Job Shop Scheduling.
        Contiene 10 jobs y 10 máquinas.
        
        Nota: Este es un dataset más complejo. Aquí se proporciona
        una versión simplificada. El dataset completo es más grande.
        
        Returns:
            (jobs_data, due_dates)
        """
        
        # FT10 Simplified: 10 Jobs x 10 Machines
        jobs = [
            [(0, 29), (1, 78), (2, 9), (3, 36), (4, 49), (5, 11), (6, 62), (7, 56), (8, 44), (9, 21)],
            [(0, 43), (2, 90), (4, 75), (9, 11), (3, 69), (1, 28), (6, 46), (5, 72), (7, 30), (8, 55)],
            [(1, 91), (0, 85), (3, 39), (2, 74), (8, 90), (5, 10), (7, 12), (6, 89), (9, 45), (4, 33)],
            [(1, 81), (2, 95), (4, 84), (9, 52), (6, 95), (0, 86), (3, 11), (5, 40), (7, 29), (8, 7)],
            [(2, 50), (1, 61), (5, 41), (0, 44), (3, 44), (6, 74), (9, 36), (8, 45), (7, 38), (4, 21)],
            [(2, 72), (0, 50), (1, 75), (5, 32), (4, 39), (8, 92), (9, 36), (6, 54), (3, 76), (7, 70)],
            [(1, 84), (0, 77), (4, 11), (6, 50), (8, 99), (9, 10), (5, 67), (7, 61), (2, 56), (3, 40)],
            [(0, 50), (2, 60), (1, 75), (3, 45), (4, 30), (5, 80), (6, 35), (7, 25), (8, 55), (9, 40)],
            [(1, 42), (5, 36), (0, 50), (2, 61), (3, 32), (4, 28), (6, 45), (7, 33), (8, 47), (9, 29)],
            [(2, 73), (3, 49), (1, 58), (0, 44), (5, 55), (4, 47), (6, 62), (9, 35), (7, 41), (8, 58)],
        ]
        
        # Due dates para FT10
        due_dates = {i: 700 + i*10 for i in range(10)}
        
        return jobs, due_dates
    
    @staticmethod
    def get_available_datasets() -> Dict[str, str]:
        """Retorna un diccionario de datasets disponibles con descripciones."""
        return {
            "FT06": "6 jobs x 6 máquinas (pequeño, rápido)",
            "FT10": "10 jobs x 10 máquinas (mediano)",
        }
    
    @staticmethod
    def load_dataset(dataset_name: str) -> Tuple[List[List[Tuple[int, int]]], Dict[int, float]]:
        """
        Carga un dataset por su nombre.
        
        Args:
            dataset_name: Nombre del dataset ('FT06', 'FT10')
        
        Returns:
            (jobs_data, due_dates)
        
        Raises:
            ValueError: Si el dataset no existe
        """
        original = dataset_name
        if isinstance(original, str) and original.upper().startswith("TA:"):
            # Formato: TA:<path_or_filename>[:instanceName_or_index]
            # Ejemplos:
            #  TA:datasets/jobshop1.txt:abz5
            #  TA:datasets/jobshop1.txt:1
            parts = original.split(':', 2)
            # parts[0] == 'TA'
            if len(parts) < 2 or not parts[1]:
                raise ValueError("Formato TA inválido. Use 'TA:<file_path>[:instanceName_or_index]'")
            path = parts[1]
            instance = None
            index = 1
            if len(parts) == 3 and parts[2]:
                # si es dígito, tratar como índice
                if parts[2].isdigit():
                    index = int(parts[2])
                else:
                    instance = parts[2]

            jobs, due_dates = load_taillard_file(path, instance_name=instance, instance_index=index)
            return jobs, due_dates

        # No es TA:, trabajar con mayúsculas para los datasets integrados
        dataset_name = str(original).upper()

        if dataset_name == "FT06":
            return Datasets.load_ft06()
        elif dataset_name == "FT10":
            return Datasets.load_ft10()
        else:
            available = ", ".join(Datasets.get_available_datasets().keys())
            raise ValueError(
                f"Dataset '{original}' no encontrado. "
                f"Datasets disponibles: {available}"
            )
    
    @staticmethod
    def print_dataset_info(jobs_data: List[List[Tuple[int, int]]], 
                          due_dates: Dict[int, float] = None,
                          dataset_name: str = ""):
        """
        Imprime información sobre un dataset.
        
        Args:
            jobs_data: Lista de trabajos
            due_dates: Diccionario opcional de fechas de entrega
            dataset_name: Nombre del dataset para mostrar
        """
        num_jobs = len(jobs_data)
        num_machines = len(set(m for job in jobs_data for m, _ in job))
        total_time = sum(sum(d for _, d in job) for job in jobs_data)
        
        print(f"\n{'='*70}")
        print(f"📦 DATASET: {dataset_name if dataset_name else 'Información'}")
        print(f"{'='*70}")
        print(f"Número de jobs:           {num_jobs}")
        print(f"Número de máquinas:       {num_machines}")
        print(f"Tiempo total de proc.:    {total_time} u.t.")
        
        if due_dates:
            print(f"\nFechas de entrega:")
            for job_id, due_date in sorted(due_dates.items()):
                print(f"   Job {job_id}: {due_date:.0f}")
        
        print(f"{'='*70}\n")
