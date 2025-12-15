from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class JobSpec:
    """Especificación de un job"""
    job_id: int
    arrival_time: float
    operations: List[Tuple[int, float]]  # [(machine_type, duration), ...]
    due_date: float
    
    def total_processing_time(self) -> float:
        """Suma de duraciones de todas las operaciones"""
        return sum(duration for _, duration in self.operations)
    
    def num_operations(self) -> int:
        return len(self.operations)

# Ejemplo de uso
job = JobSpec(
    job_id=42,
    arrival_time=18.3,
    operations=[(3, 5.2), (1, 3.8), (4, 7.1), (0, 2.5)],
    due_date=18.3 + (5.2 + 3.8 + 7.1 + 2.5) * 1.5
)

print(f"Job {job.job_id}: {job.num_operations()} ops, TPT={job.total_processing_time():.1f}")
