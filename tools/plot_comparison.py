import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def plot_comparison(jade_csv, spt_csv, lpt_csv, out_file='comparison_plot.png'):
    # Cargar datos
    df_jade = pd.read_csv(jade_csv)
    df_spt = pd.read_csv(spt_csv)
    df_lpt = pd.read_csv(lpt_csv)

    # Configurar plot
    fig, axs = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    
    # 1. Makespan
    axs[0].plot(df_jade['episode'], df_jade['makespan_promedio'], label='JADE (RL)', color='blue', linewidth=2)
    axs[0].plot(df_spt['episode'], df_spt['makespan_promedio'], label='SPT (Heurística)', color='green', linestyle='--')
    axs[0].plot(df_lpt['episode'], df_lpt['makespan_promedio'], label='LPT (Heurística)', color='red', linestyle='--')
    axs[0].set_ylabel('Makespan Promedio (u.t.)')
    axs[0].set_title('Comparativa de Eficiencia (Makespan)')
    axs[0].legend()
    axs[0].grid(True, alpha=0.3)

    # 2. Tardanza Total
    axs[1].plot(df_jade['episode'], df_jade['tardanza_total'], label='JADE (RL)', color='blue', linewidth=2)
    axs[1].plot(df_spt['episode'], df_spt['tardanza_total'], label='SPT (Heurística)', color='green', linestyle='--')
    axs[1].plot(df_lpt['episode'], df_lpt['tardanza_total'], label='LPT (Heurística)', color='red', linestyle='--')
    axs[1].set_ylabel('Tardanza Total Acumulada')
    axs[1].set_xlabel('Episodios')
    axs[1].set_title('Comparativa de Puntualidad (Tardanza)')
    axs[1].legend()
    axs[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_file, dpi=150)
    print(f"[OK] Gráfica comparativa guardada en: {out_file}")

if __name__ == "__main__":
    base_dir = 'training_logs'
    jade = os.path.join(base_dir, 'training_jade.csv')
    spt = os.path.join(base_dir, 'training_spt.csv')
    lpt = os.path.join(base_dir, 'training_lpt.csv')
    
    if all(os.path.exists(f) for f in [jade, spt, lpt]):
        plot_comparison(jade, spt, lpt)
    else:
        print("[ERROR] Faltan archivos CSV. Asegúrate de ejecutar los 3 entrenamientos primero.")
