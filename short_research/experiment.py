"""
Experiment: Adaptive FDIA vs Random Baseline (Kaven et al. paper replication)

Runs both attackers for 96 timesteps (matching the paper's 15-min × 96 = 24 h),
then produces:
  1. Comparison table: detection rate, voltage impact, cumulative undetected impact
  2. Fig A — deviation over time per attacker  (replicates paper's Fig. 2 style)
  3. Fig B — detection event timeline
  4. Fig C — cumulative undetected voltage impact
  5. Fig D — phase timeline of adaptive attacker
  6. Saves results/experiment_results.json
"""

import json
import warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

from grid_setup    import load_grid, print_grid_summary
from adaptive_attacker import AdaptiveAttacker, RandomBaselineAttacker

TIMESTEPS  = 96      # 24 h of 15-min intervals — same as paper
MAX_METERS = 6
SEED_ADAPT = 42
SEED_BASE  = 99
RESULTS_DIR = "short_research/results"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _phase_color(phase: str) -> str:
    return {"PROBE": "#f0a500", "SELECT": "#6a4c93", "EXPLOIT": "#e63946", "RANDOM": "#457b9d"}[phase]


def run_experiment():
    print("=" * 60)
    print("  Adaptive FDIA vs Random Baseline Experiment")
    print("  Based on: Kaven et al. NetSoft 2020")
    print("=" * 60)

    # -----------------------------------------------------------------------
    print("\nLoading SimBench grid...")
    net, profiles = load_grid()
    print_grid_summary(net)
    bus_indices = list(net.bus.index)

    # -----------------------------------------------------------------------
    print(f"\nRunning ADAPTIVE attacker for {TIMESTEPS} timesteps...")
    adaptive = AdaptiveAttacker(bus_indices, max_meters=MAX_METERS, seed=SEED_ADAPT)
    adapt_results = []
    for t in range(TIMESTEPS):
        r = adaptive.step(net, profiles, t)
        adapt_results.append(r)
        if t % 10 == 0:
            print(f"  t={t:02d}  phase={r.phase:7s}  detected={r.detected}  dev_v={r.mean_dev_v:.5f}")

    # -----------------------------------------------------------------------
    print(f"\nRunning RANDOM BASELINE for {TIMESTEPS} timesteps...")
    baseline = RandomBaselineAttacker(bus_indices, n_meters=MAX_METERS, seed=SEED_BASE)
    base_results = []
    for t in range(TIMESTEPS):
        r = baseline.step(net, profiles, t)
        base_results.append(r)
        if t % 10 == 0:
            print(f"  t={t:02d}  phase={r.phase:7s}  detected={r.detected}  dev_v={r.mean_dev_v:.5f}")

    # -----------------------------------------------------------------------
    print("\nComputing metrics...")
    metrics = _compute_metrics(adapt_results, base_results)
    _print_metrics(metrics, adaptive, baseline)
    _save_results(metrics, adapt_results, base_results, adaptive, baseline)
    _plot_all(adapt_results, base_results, metrics)
    print(f"\nResults saved to {RESULTS_DIR}/")
    return metrics


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def _compute_metrics(adapt_res, base_res) -> dict:
    n = len(adapt_res)

    # --- adaptive ---
    a_detected     = [r.detected for r in adapt_res]
    a_dev          = [r.mean_dev_v for r in adapt_res]
    a_exploit_mask = [r.phase == "EXPLOIT" for r in adapt_res]

    a_det_rate     = sum(a_detected) / n
    a_exploit_det  = (sum(d and m for d, m in zip(a_detected, a_exploit_mask))
                      / max(sum(a_exploit_mask), 1))
    a_undetected_impact = sum(v for v, d in zip(a_dev, a_detected) if not d)
    a_mean_dev     = float(np.mean(a_dev))
    a_exploit_dev  = float(np.mean([v for v, m in zip(a_dev, a_exploit_mask) if m]) or 0)

    # --- baseline ---
    b_detected  = [r.detected for r in base_res]
    b_dev       = [r.mean_dev_v for r in base_res]

    b_det_rate  = sum(b_detected) / n
    b_undetected_impact = sum(v for v, d in zip(b_dev, b_detected) if not d)
    b_mean_dev  = float(np.mean(b_dev))

    # --- improvements ---
    det_reduction      = (b_det_rate - a_exploit_det) / b_det_rate if b_det_rate > 0 else 0
    cumulative_ratio   = a_undetected_impact / b_undetected_impact if b_undetected_impact > 0 else float("inf")

    return {
        "n_timesteps": n,
        "adaptive": {
            "overall_detection_rate":      round(a_det_rate, 4),
            "exploit_detection_rate":      round(a_exploit_det, 4),
            "mean_voltage_deviation":      round(a_mean_dev, 6),
            "exploit_mean_dev":            round(a_exploit_dev, 6),
            "cumulative_undetected_impact": round(a_undetected_impact, 6),
            "exploit_steps":               sum(a_exploit_mask),
        },
        "baseline": {
            "overall_detection_rate":      round(b_det_rate, 4),
            "mean_voltage_deviation":      round(b_mean_dev, 6),
            "cumulative_undetected_impact": round(b_undetected_impact, 6),
        },
        "comparison": {
            "exploit_detection_reduction_pct": round(det_reduction * 100, 1),
            "cumulative_impact_ratio_adapt_over_base": round(cumulative_ratio, 3),
        },
    }


def _print_metrics(metrics, adaptive, baseline):
    a, b, c = metrics["adaptive"], metrics["baseline"], metrics["comparison"]
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n{'Metric':<42} {'Adaptive':>10} {'Baseline':>10}")
    print("-" * 62)
    print(f"{'Overall detection rate':<42} {a['overall_detection_rate']:>10.1%} {b['overall_detection_rate']:>10.1%}")
    print(f"{'Exploit-phase detection rate':<42} {a['exploit_detection_rate']:>10.1%} {'—':>10}")
    print(f"{'Mean voltage deviation [pu]':<42} {a['mean_voltage_deviation']:>10.6f} {b['mean_voltage_deviation']:>10.6f}")
    print(f"{'Exploit mean deviation [pu]':<42} {a['exploit_mean_dev']:>10.6f} {'—':>10}")
    print(f"{'Cumulative undetected impact':<42} {a['cumulative_undetected_impact']:>10.6f} {b['cumulative_undetected_impact']:>10.6f}")
    print(f"{'Exploit steps':<42} {a['exploit_steps']:>10} {'—':>10}")
    print("-" * 62)
    print(f"\nDetection reduction (exploit vs baseline): {c['exploit_detection_reduction_pct']:+.1f}%")
    print(f"Cumulative impact ratio (adaptive/baseline): {c['cumulative_impact_ratio_adapt_over_base']:.3f}x")
    print(f"\nAdaptive learned delta : {adaptive.safe_delta:.5f} pu")
    print(f"Adaptive learned meters: {adaptive.best_meters}")
    print(f"Baseline fixed delta   : {baseline.FIXED_DELTA_V:.5f} pu")
    print("=" * 60)


def _save_results(metrics, adapt_res, base_res, adaptive, baseline):
    import os; os.makedirs(RESULTS_DIR, exist_ok=True)

    out = {
        "metrics": metrics,
        "adaptive_summary":  adaptive.summary(),
        "baseline_summary":  baseline.summary(),
        "adaptive_timeline": [
            {"t": i, "phase": r.phase, "delta": r.delta,
             "detected": r.detected, "dev_v": round(r.mean_dev_v, 6)}
            for i, r in enumerate(adapt_res)
        ],
        "baseline_timeline": [
            {"t": i, "detected": r.detected, "dev_v": round(r.mean_dev_v, 6)}
            for i, r in enumerate(base_res)
        ],
    }
    path = f"{RESULTS_DIR}/experiment_results.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# plots
# ---------------------------------------------------------------------------

def _plot_all(adapt_res, base_res, metrics):
    import os; os.makedirs(RESULTS_DIR, exist_ok=True)

    ts = np.arange(len(adapt_res))

    a_dev  = np.array([r.mean_dev_v for r in adapt_res])
    b_dev  = np.array([r.mean_dev_v for r in base_res])
    a_det  = np.array([r.detected   for r in adapt_res], dtype=float)
    b_det  = np.array([r.detected   for r in base_res],  dtype=float)
    phases = [r.phase for r in adapt_res]

    # rolling mean (window=8 for smoothing like paper)
    def rolling(x, w=8):
        return np.convolve(x, np.ones(w) / w, mode="same")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Adaptive FDIA vs Random Baseline\n"
        "Based on: Kaven et al. — Assessing Effects of Cyber-Attacks on Smart Grids (NetSoft 2020)",
        fontsize=11, fontweight="bold"
    )

    # ---- A: voltage deviation over time -----------------------------------
    ax = axes[0, 0]
    ax.plot(ts, rolling(b_dev), color="#457b9d", lw=1.5, label="Baseline (random)")
    ax.fill_between(ts, rolling(b_dev) - b_dev.std(), rolling(b_dev) + b_dev.std(),
                    alpha=0.2, color="#457b9d")
    ax.plot(ts, rolling(a_dev), color="#e63946", lw=1.5, label="Adaptive")
    ax.fill_between(ts, rolling(a_dev) - a_dev.std(), rolling(a_dev) + a_dev.std(),
                    alpha=0.2, color="#e63946")
    ax.set_xlabel("Timestep (15-min intervals)")
    ax.set_ylabel("Mean voltage deviation [pu]")
    ax.set_title("(A) Voltage Deviation over Time")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ---- B: detection events ----------------------------------------------
    ax = axes[0, 1]
    ax.scatter(ts[a_det == 1], np.ones(int(a_det.sum())) * 1.1,
               c="#e63946", s=18, marker="x", label=f"Adaptive detected ({int(a_det.sum())})")
    ax.scatter(ts[b_det == 1], np.ones(int(b_det.sum())) * 0.9,
               c="#457b9d", s=18, marker="x", label=f"Baseline detected ({int(b_det.sum())})")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Attacker (offset for clarity)")
    ax.set_yticks([0.9, 1.1]); ax.set_yticklabels(["Baseline", "Adaptive"])
    ax.set_title("(B) Detection Events")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3, axis="x")
    ax.set_xlim(-1, len(ts) + 1)

    # ---- C: cumulative undetected impact ----------------------------------
    ax = axes[1, 0]
    a_cumul = np.cumsum([v if not d else 0 for v, d in zip(a_dev, a_det)])
    b_cumul = np.cumsum([v if not d else 0 for v, d in zip(b_dev, b_det)])
    ax.plot(ts, b_cumul, color="#457b9d", lw=1.5, label="Baseline")
    ax.plot(ts, a_cumul, color="#e63946", lw=1.5, label="Adaptive")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Cumulative undetected voltage impact [pu]")
    ax.set_title("(C) Cumulative Undetected Grid Impact")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ---- D: adaptive phase timeline ---------------------------------------
    ax = axes[1, 1]
    phase_colors = [_phase_color(p) for p in phases]
    ax.bar(ts, np.ones(len(ts)), color=phase_colors, width=1.0, align="edge")
    # detection overlay
    det_ts = ts[a_det == 1]
    ax.scatter(det_ts + 0.5, np.ones(len(det_ts)) * 0.5,
               c="black", s=20, zorder=5, marker="x", label="Detected")
    patches = [mpatches.Patch(color=_phase_color(p), label=p)
               for p in ["PROBE", "SELECT", "EXPLOIT"]]
    patches.append(mpatches.Patch(color="black", label="Detected"))
    ax.legend(handles=patches, fontsize=7, loc="upper right")
    ax.set_xlabel("Timestep")
    ax.set_title("(D) Adaptive Attacker Phase Timeline")
    ax.set_yticks([])
    ax.set_xlim(0, len(ts))

    plt.tight_layout()
    path = f"{RESULTS_DIR}/comparison_results.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Fig 2 replica: deviation per bus (paper style) -------------------
    _plot_paper_style(adapt_res, base_res)


def _plot_paper_style(adapt_res, base_res):
    """Replicates paper's Fig. 2 — mean deviation per node across timesteps."""
    ts  = np.arange(len(adapt_res))
    a_d = np.array([r.mean_dev_v for r in adapt_res])
    b_d = np.array([r.mean_dev_v for r in base_res])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle("Voltage Deviation from State Estimation\n"
                 "(replicating Fig. 2 style from Kaven et al.)", fontsize=10)

    for ax, dev, label, color in [
        (ax1, b_d, "Baseline (Random, fixed delta)", "#457b9d"),
        (ax2, a_d, "Adaptive (Learned delta + optimal meters)", "#e63946"),
    ]:
        mean_line = np.convolve(dev, np.ones(6) / 6, mode="same")
        ax.plot(ts, mean_line, color=color, lw=1.5, label="Mean deviation")
        ax.fill_between(ts, mean_line - dev.std(), mean_line + dev.std(),
                        alpha=0.25, color=color, label="Std deviation")
        ax.axhline(0, color="gray", lw=0.6, ls="--")
        ax.set_ylabel("Deviation [pu]")
        ax.set_title(label, fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.text(0.98, 0.92, f"Overall mean: {dev.mean():.5f}",
                transform=ax.transAxes, ha="right", fontsize=8,
                bbox=dict(boxstyle="round", fc="white", alpha=0.7))

    ax2.set_xlabel("Timestep (15-min intervals)")
    plt.tight_layout()
    path = f"{RESULTS_DIR}/paper_style_deviation.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_experiment()
