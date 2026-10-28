#!/usr/bin/env python3
"""Figure for the H-TRACE session: holdout proxies for CTRL vs TRACE vs controls.

Reads only evidence/trace_three_experiments_20261028.json (measured values).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    d = json.loads((ROOT / "evidence/trace_three_experiments_20261028.json").read_text())
    exps = {e["experiment_id"]: e for e in d["experiments"]}
    b2h = d["baselines"]["D28_B2_fold_honest_holdout"]
    b2s = d["baselines"]["GEMSDOE32_B2_sgmc"]

    labels = ["D28_B2\nfold-honest", "EXP-1\nCTRL-T0", "EXP-2\nTRACE-T1", "EXP-3\nTRACE-T2"]
    hr = [b2h["pooled_dti"]] + [exps[k]["holdout_hide_and_recover"]["pooled_dti"] for k in ("EXP-1", "EXP-2", "EXP-3")]
    hr_lo = [b2h["ci95_cluster_bootstrap"][0]] + [exps[k]["holdout_hide_and_recover"]["ci95_cluster_bootstrap"][0] for k in ("EXP-1", "EXP-2", "EXP-3")]
    hr_hi = [b2h["ci95_cluster_bootstrap"][1]] + [exps[k]["holdout_hide_and_recover"]["ci95_cluster_bootstrap"][1] for k in ("EXP-1", "EXP-2", "EXP-3")]
    sg = [b2s["sgmc_prevalence_calibrated_dti"]] + [exps[k]["sgmc_diagnostic"]["sgmc_prevalence_calibrated_dti"] for k in ("EXP-1", "EXP-2", "EXP-3")]
    sg_lo = [b2s["sgmc_calibrated_ci95"][0]] + [exps[k]["sgmc_diagnostic"]["sgmc_calibrated_ci95"][0] for k in ("EXP-1", "EXP-2", "EXP-3")]
    sg_hi = [b2s["sgmc_calibrated_ci95"][1]] + [exps[k]["sgmc_diagnostic"]["sgmc_calibrated_ci95"][1] for k in ("EXP-1", "EXP-2", "EXP-3")]

    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for ax, vals, lo, hi, title in (
        (axes[0], hr, hr_lo, hr_hi, "Hide-and-recover HOLDOUT-DTI\n(GEMSDOE32-HIDE-RECOVER-v3.0, n=22,232)"),
        (axes[1], sg, sg_lo, sg_hi, "SGMC off-catalogue diagnostic (not a gate)\n(GEMSDOE32-SGMC-CAL-v3.0, n=62,703)"),
    ):
        err = [np.array(vals) - np.array(lo), np.array(hi) - np.array(vals)]
        colors = ["#6b7280", "#2563eb", "#dc2626", "#dc2626"]
        ax.bar(x, vals, yerr=err, capsize=4, color=colors, alpha=0.85)
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_title(title, fontsize=9)
        ax.set_ylim(0, max(hi) * 1.25)
        for xi, v in zip(x, vals):
            ax.text(xi, v + max(hi) * 0.03, f"{v:.4f}", ha="center", fontsize=8)
    axes[0].axhline(0.113696, color="#059669", ls="--", lw=1)
    axes[0].text(3.45, 0.113696 + 0.002, "repo best 0.1137\n(H-UDSR EXP-2)", color="#059669",
                 fontsize=7, ha="right")
    fig.suptitle("H-TRACE (2026-10-28): oriented trace-coherence gating hurts both holdout proxies",
                 fontsize=10)
    fig.tight_layout()
    out = ROOT / "docs/assets/fig5_trace_experiments.png"
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
