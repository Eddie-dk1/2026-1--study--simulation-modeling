from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib.pyplot as plt


DATA = ROOT / "data"
PLOTS = ROOT / "plots"
PLOTS.mkdir(exist_ok=True)


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def plot_mmc_trace() -> None:
    data = rows("mmc_trace.csv")
    step = max(1, len(data) // 4000)
    sample = data[::step]
    t = [f(r, "time") for r in sample]
    queue = [f(r, "queue_length") for r in sample]
    system = [f(r, "system_size") for r in sample]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t, system, label="число заявок в системе", linewidth=1.2)
    ax.plot(t, queue, label="длина очереди", linewidth=1.2)
    ax.set_title("M/M/c: динамика системы и очереди")
    ax.set_xlabel("время")
    ax.set_ylabel("число заявок")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "mmc_trace.png", dpi=180)
    plt.close(fig)


def plot_mmc_sweep() -> None:
    data = rows("mmc_sweep.csv")
    by_c: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in data:
        by_c[int(row["c"])].append(row)

    fig, ax = plt.subplots(figsize=(9, 5))
    for c, group in sorted(by_c.items()):
        group.sort(key=lambda r: f(r, "rho"))
        rho = [f(r, "rho") for r in group]
        analytic = [f(r, "wq") for r in group]
        observed = [f(r, "observed_wq") for r in group]
        ax.plot(rho, analytic, marker="o", label=f"аналитика c={c}")
        ax.plot(rho, observed, marker="x", linestyle="--", label=f"имитация c={c}")
    ax.set_title("M/M/c: среднее ожидание Wq")
    ax.set_xlabel("загрузка rho")
    ax.set_ylabel("Wq")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "mmc_sweep_wq.png", dpi=180)
    plt.close(fig)


def plot_ross_trace() -> None:
    data = rows("ross_trace.csv")
    t = [f(r, "time") for r in data]
    good = [f(r, "good_machines") for r in data]
    spares = [f(r, "spares") for r in data]
    queue = [f(r, "repair_queue") for r in data]
    busy = [f(r, "busy_repairers") for r in data]

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    axes[0].step(t, good, where="post", label="исправные машины", linewidth=1.3)
    axes[0].step(t, spares, where="post", label="резерв", linewidth=1.1)
    axes[0].set_ylabel("машины")
    axes[0].grid(alpha=0.25)
    axes[0].legend()
    axes[1].step(t, busy, where="post", label="занятые ремонтники", linewidth=1.3)
    axes[1].step(t, queue, where="post", label="очередь ремонта", linewidth=1.1)
    axes[1].set_xlabel("время, ч")
    axes[1].set_ylabel("ремонт")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    fig.suptitle("Модель Росса: мониторинг состояния")
    fig.tight_layout()
    fig.savefig(PLOTS / "ross_trace.png", dpi=180)
    plt.close(fig)


def plot_ross_params() -> None:
    data = rows("ross_params_summary.csv")
    by_r: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in data:
        by_r[int(row["repairers"])].append(row)

    fig, ax = plt.subplots(figsize=(9, 5))
    for repairers, group in sorted(by_r.items()):
        group.sort(key=lambda r: f(r, "N"))
        n = [f(r, "N") for r in group]
        sim = [f(r, "mean_crash_time") for r in group]
        analytic = [f(r, "analytic_crash_time") for r in group]
        ax.plot(n, sim, marker="o", label=f"имитация, R={repairers}")
        ax.plot(n, analytic, marker="x", linestyle="--", label=f"аналитика, R={repairers}")
    ax.set_title("Модель Росса: время до падения")
    ax.set_xlabel("N, основных машин")
    ax.set_ylabel("среднее время, ч")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "ross_crash_time.png", dpi=180)
    plt.close(fig)


def plot_ross_monitoring() -> None:
    data = rows("ross_params_summary.csv")
    by_r: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in data:
        by_r[int(row["repairers"])].append(row)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for repairers, group in sorted(by_r.items()):
        group.sort(key=lambda r: f(r, "N"))
        n = [f(r, "N") for r in group]
        util = [f(r, "mean_repairer_utilization") for r in group]
        q = [f(r, "mean_repair_queue") for r in group]
        axes[0].plot(n, util, marker="o", label=f"R={repairers}")
        axes[1].plot(n, q, marker="o", label=f"R={repairers}")
    axes[0].set_title("Загрузка ремонтников")
    axes[0].set_xlabel("N")
    axes[0].set_ylabel("доля занятости")
    axes[1].set_title("Средняя длина очереди ремонта")
    axes[1].set_xlabel("N")
    axes[1].set_ylabel("машины")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "ross_monitoring.png", dpi=180)
    plt.close(fig)


def main() -> None:
    plot_mmc_trace()
    plot_mmc_sweep()
    plot_ross_trace()
    plot_ross_params()
    plot_ross_monitoring()
    print(f"Saved plots to {PLOTS}")


if __name__ == "__main__":
    main()
