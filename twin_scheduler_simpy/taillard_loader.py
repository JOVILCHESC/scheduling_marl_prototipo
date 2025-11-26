"""
Parser para archivos de instancias Job-Shop en formato OR-Library / Taillard.

Funciones:
  - load_taillard_file(path, instance_name=None, instance_index=1, due_date_multiplier=1.5)

El parser busca bloques que empiezan con la palabra "instance <name>" y a
continuación una línea con "<num_jobs> <num_machines>" y luego una línea por
trabajo con pares "machine duration".

Las máquinas en los archivos Taillard están indexadas desde 0.
"""
from typing import List, Tuple, Dict, Optional


def _iter_nonempty_lines(lines):
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # saltar separadores visuales
        if line.startswith('+') and set(line) <= set('+ '):
            continue
        yield line


def load_taillard_file(path: str,
                       instance_name: Optional[str] = None,
                       instance_index: int = 1,
                       due_date_multiplier: float = 1.5) -> Tuple[List[List[Tuple[int, int]]], Dict[int, float]]:
    """
    Carga una instancia Taillard desde un archivo que puede contener varias.

    Args:
        path: Ruta al archivo que contiene una o más instancias.
        instance_name: Nombre textual de la instancia (p.ej. 'ta01' o 'abz5'). Si se
                       proporciona, se busca el bloque con ese nombre.
        instance_index: Si no se proporciona `instance_name`, se toma la enésima
                        instancia encontrada (1-based).
        due_date_multiplier: multiplicador para estimar due dates a partir del
                             procesamiento total del job.

    Returns:
        jobs_data: Lista de trabajos; cada trabajo es lista de tuplas (machine_id, duration)
        due_dates: Diccionario job_id -> due_date estimado
    """
    import os

    # Resolver rutas relativas respecto al paquete twin_scheduler_simpy
    if not os.path.isabs(path) and not os.path.exists(path):
        base = os.path.dirname(__file__)
        candidate = os.path.join(base, path)
        if os.path.exists(candidate):
            path = candidate

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    # Localizar bloques 'instance <name>'
    instances = []  # list of (name, start_line_index)
    for i, raw in enumerate(raw_lines):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0].lower() == 'instance':
            instances.append((parts[1], i))

    if not instances:
        # Si no aparecen 'instance', intentar parsear desde el inicio
        start_idx = 0
        chosen_idx = 0
    else:
        if instance_name:
            # buscar por nombre (case-insensitive)
            match = [idx for idx, (name, pos) in enumerate(instances) if name.lower() == instance_name.lower()]
            if not match:
                raise ValueError(f"Instancia '{instance_name}' no encontrada en {path}")
            chosen = match[0]
        else:
            if instance_index < 1 or instance_index > len(instances):
                raise IndexError(f"instance_index fuera de rango (1..{len(instances)})")
            chosen = instance_index - 1

        _, start_idx = instances[chosen]

    # Avanzar al siguiente renglón que contenga los números (jobs machines)
    it = iter(raw_lines[start_idx+1:])
    for line in it:
        s = line.strip()
        if not s:
            continue
        if s.startswith('+'):
            continue
        # buscar dos enteros
        parts = s.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            num_jobs = int(parts[0])
            num_machines = int(parts[1])
            break
    else:
        raise ValueError("No se encontró la linea 'num_jobs num_machines' tras la instancia")

    jobs = []
    # Leer las próximas num_jobs líneas con pares máquina-duración
    read = 0
    for line in it:
        s = line.strip()
        if not s:
            continue
        if s.startswith('+'):
            continue
        tokens = s.split()
        # En algunos ficheros existen líneas muy largas; los jobs pueden estar
        # en una sola línea o partirse; asumimos que cada job se representa en una sola línea.
        if len(tokens) < 2:
            continue
        # Parsear pares
        pairs = []
        nums = [int(t) for t in tokens]
        if len(nums) % 2 != 0:
            # Si la línea no tiene pares completos, intentar leer la siguiente y concatenar
            # (muy raro pero por seguridad)
            extra = []
            while len(nums) % 2 != 0:
                try:
                    extra_line = next(it)
                except StopIteration:
                    break
                extra_tokens = extra_line.strip().split()
                extra += [int(t) for t in extra_tokens if t.isdigit()]
                nums += extra

        for j in range(0, len(nums), 2):
            machine = nums[j]
            duration = nums[j+1]
            pairs.append((machine, duration))

        # Si la línea contiene más pares de los esperados, recortamos al número de máquinas
        if len(pairs) > num_machines:
            pairs = pairs[:num_machines]

        jobs.append(pairs)
        read += 1
        if read >= num_jobs:
            break

    if len(jobs) != num_jobs:
        raise ValueError(f"Esperaba {num_jobs} jobs pero parseé {len(jobs)} en {path}")

    # Estimar due_dates
    due_dates = {}
    for jid, ops in enumerate(jobs):
        total = sum(d for _, d in ops)
        due_dates[jid] = total * due_date_multiplier  # arrival_time assumed 0

    return jobs, due_dates
