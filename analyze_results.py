"""
Análisis comparativo de las 3 reglas de scheduling (SPT, EDD, LPT)
"""
import pandas as pd
import os

# Cargar datos
logs_dir = "logs"
spt = pd.read_csv(os.path.join(logs_dir, "simulation_phase1_SPT_jobs_20251210_031101.csv"))
edd = pd.read_csv(os.path.join(logs_dir, "simulation_phase1_EDD_jobs_20251210_031105.csv"))
lpt = pd.read_csv(os.path.join(logs_dir, "simulation_phase1_LPT_jobs_20251210_031110.csv"))

print("\n" + "="*60)
print(" COMPARACIÓN DE REGLAS DE SCHEDULING - FASE 1")
print("="*60 + "\n")

# Función para calcular métricas
def analizar_regla(df, nombre):
    total_jobs = len(df)
    makespan_avg = df['makespan'].mean()
    tardiness_total = df['tardiness'].sum()
    jobs_atrasados = len(df[df['tardiness'] > 0])
    tardiness_avg = df['tardiness'].mean()
    
    print(f"{nombre}:")
    print(f"  ✓ Jobs completados: {total_jobs}")
    print(f"  ✓ Makespan promedio: {makespan_avg:.2f} u.t.")
    print(f"  ✓ Tardanza total: {tardiness_total:.2f} u.t.")
    print(f"  ✓ Tardanza promedio: {tardiness_avg:.2f} u.t.")
    print(f"  ✓ Jobs atrasados: {jobs_atrasados} ({100*jobs_atrasados/total_jobs:.1f}%)")
    print()
    
    return {
        'regla': nombre,
        'jobs': total_jobs,
        'makespan_avg': makespan_avg,
        'tardiness_total': tardiness_total,
        'tardiness_avg': tardiness_avg,
        'jobs_atrasados': jobs_atrasados,
        'porcentaje_atrasados': 100 * jobs_atrasados / total_jobs
    }

# Analizar cada regla
resultados = []
resultados.append(analizar_regla(spt, "SPT (Shortest Processing Time)"))
resultados.append(analizar_regla(edd, "EDD (Earliest Due Date)"))
resultados.append(analizar_regla(lpt, "LPT (Longest Processing Time)"))

# Determinar mejor regla
print("="*60)
print(" RANKING POR TARDANZA TOTAL")
print("="*60)
df_resultados = pd.DataFrame(resultados).sort_values('tardiness_total')
for idx, row in df_resultados.iterrows():
    print(f"  {list(df_resultados.index).index(idx)+1}. {row['regla']}: {row['tardiness_total']:.2f} u.t.")

print("\n" + "="*60)
print(f" 🏆 GANADOR: {df_resultados.iloc[0]['regla']}")
print(f"    Tardanza total: {df_resultados.iloc[0]['tardiness_total']:.2f} u.t.")
print(f"    Jobs completados: {int(df_resultados.iloc[0]['jobs'])}")
print("="*60 + "\n")

# Comparación porcentual
mejor_tardanza = df_resultados.iloc[0]['tardiness_total']
print("MEJORA RELATIVA:")
for idx, row in df_resultados.iterrows():
    if row['tardiness_total'] > mejor_tardanza:
        mejora = 100 * (row['tardiness_total'] - mejor_tardanza) / mejor_tardanza
        print(f"  {row['regla']}: +{mejora:.1f}% peor que el mejor")
print()
