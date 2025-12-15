import os
import sys
import csv
import argparse

import matplotlib.pyplot as plt


def load_csv(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (float(v) if k != 'episode' else int(v)) for k, v in r.items()})
    return rows


def plot_metrics(rows, out_path=None):
    episodes = [r['episode'] for r in rows]
    reward = [r['reward'] for r in rows]
    tardanza = [r['tardanza_total'] for r in rows]
    makespan = [r['makespan_promedio'] for r in rows]

    fig, axs = plt.subplots(3, 1, figsize=(8, 10), sharex=True)

    axs[0].plot(episodes, reward, label='Reward (-tardanza)')
    axs[0].set_ylabel('Reward')
    axs[0].legend()
    axs[0].grid(True, alpha=0.3)

    axs[1].plot(episodes, tardanza, color='orange', label='Tardanza total')
    axs[1].set_ylabel('Tardanza')
    axs[1].legend()
    axs[1].grid(True, alpha=0.3)

    axs[2].plot(episodes, makespan, color='green', label='Makespan promedio')
    axs[2].set_ylabel('Makespan')
    axs[2].set_xlabel('Episodios')
    axs[2].legend()
    axs[2].grid(True, alpha=0.3)

    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150)
        print(f"[OK] Figura guardada en: {out_path}")
    else:
        plt.show()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Graficar resultados de entrenamiento')
    ap.add_argument('csv', help='Ruta al CSV generado por run_training.py')
    ap.add_argument('--out', help='Ruta de salida PNG (opcional)')
    args = ap.parse_args()

    rows = load_csv(args.csv)
    plot_metrics(rows, out_path=args.out)
