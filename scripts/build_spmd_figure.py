#!/usr/bin/env python3
"""Generate docs/assets/fig6_spmd_experiments.png directly from saved experiment JSONs."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spmd = json.loads((ROOT / "evidence/spmd_three_experiments_20261028.json").read_text())
    udsr = json.loads((ROOT / "evidence/udsr_three_experiments_20261027.json").read_text())
    trace = json.loads((ROOT / "evidence/trace_three_experiments_20261028.json").read_text())

    d28 = spmd["baselines"]["D28_B2_fold_honest_holdout"]
    udsr_e2 = next(e for e in udsr["experiments"] if e["experiment_id"] == "EXP-2")
    udsr_e3 = next(e for e in udsr["experiments"] if e["experiment_id"] == "EXP-3")
    tr_e2 = next(e for e in trace["experiments"] if e["experiment_id"] == "EXP-2")
    sp_e1, sp_e2, sp_e3 = spmd["experiments"]

    labels = [
        "D28_B2\n(fold-honest ctrl)",
        "H-TRACE EXP-2\n(km trace gate)",
        "H-UDSR EXP-3\n(2-stage 50/50)",
        "H-UDSR EXP-2\n(sup 53ch)",
        "H-SPMD EXP-1\n(sup 61ch ctrl)",
        "H-SPMD EXP-2\n(SAR-PU unified)",
        "H-SPMD EXP-3\n(SAR-PU 64/36)",
    ]

    hr_pts = [
        d28["pooled_dti"],
        tr_e2["holdout_hide_and_recover"]["pooled_dti"],
        udsr_e3["holdout_hide_and_recover"]["pooled_dti"],
        udsr_e2["holdout_hide_and_recover"]["pooled_dti"],
        sp_e1["holdout_hide_and_recover"]["pooled_dti"],
        sp_e2["holdout_hide_and_recover"]["pooled_dti"],
        sp_e3["holdout_hide_and_recover"]["pooled_dti"],
    ]
    hr_cis = [
        d28["ci95_cluster_bootstrap"],
        tr_e2["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
        udsr_e3["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
        udsr_e2["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
        sp_e1["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
        sp_e2["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
        sp_e3["holdout_hide_and_recover"]["ci95_cluster_bootstrap"],
    ]
    sparse_ov = [
        100.0,  # D28_B2 is an archival registry raster
        100.0 * tr_e2["dots_audit"]["worst_sparse_within_3px"],
        100.0 * udsr_e3["registry_dots_audit_extended_488"]["worst_sparse_within_3px"],
        100.0 * udsr_e2["registry_dots_audit_extended_488"]["worst_sparse_within_3px"],
        100.0 * sp_e1["dots_audit"]["worst_sparse_within_3px"],
        100.0 * sp_e2["dots_audit"]["worst_sparse_within_3px"],
        100.0 * sp_e3["dots_audit"]["worst_sparse_within_3px"],
    ]

    colors_a = ["#6b7280", "#dc2626", "#2563eb", "#d97706", "#b45309", "#059669", "#0d9488"]
    colors_b = ["#9ca3af", "#dc2626", "#2563eb", "#d97706", "#b45309", "#059669", "#0d9488"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)
    y = np.arange(len(labels))

    xerr_lo = [pt - ci[0] for pt, ci in zip(hr_pts, hr_cis)]
    xerr_hi = [ci[1] - pt for pt, ci in zip(hr_pts, hr_cis)]

    bars1 = ax1.barh(y, hr_pts, color=colors_a, alpha=0.88, height=0.62)
    ax1.errorbar(hr_pts, y, xerr=[xerr_lo, xerr_hi], fmt="none", ecolor="#111827", elinewidth=1.4, capsize=3.5)
    ax1.axvline(d28["pooled_dti"], color="#374151", linestyle="--", linewidth=1.1, label="D28_B2 ctrl (0.0992)")
    ax1.set_yticks(y)
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("Pooled HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, n=22,232)", fontsize=9.5)
    ax1.set_title("A. Spatially-Blocked Hide-and-Recover Holdout + 95% CI", fontsize=10.5, fontweight="bold")
    ax1.set_xlim(0.0, 0.165)
    for bar, pt, ci in zip(bars1, hr_pts, hr_cis):
        ax1.text(ci[1] + 0.0025, bar.get_y() + bar.get_height() / 2, f"{pt:.4f}", va="center", fontsize=8.5, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=8.5)
    ax1.grid(axis="x", alpha=0.25)

    bars2 = ax2.barh(y[1:], sparse_ov[1:], color=colors_b[1:], alpha=0.88, height=0.62)
    ax2.axvline(70.0, color="#dc2626", linestyle="--", linewidth=1.4, label="70% Sparse Overlap Ceiling")
    ax2.set_yticks(y[1:])
    ax2.set_yticklabels(labels[1:], fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Max Within-3px Overlap vs 543 Sparse Registry Rasters (%)", fontsize=9.5)
    ax2.set_title("B. Sparse Portfolio Uniqueness (549-Raster Extended Registry)", fontsize=10.5, fontweight="bold")
    ax2.set_xlim(0.0, 114.0)
    for bar, ov in zip(bars2, sparse_ov[1:]):
        status = "PASS" if ov <= 70.0 else "DUP"
        ax2.text(ov + 1.4, bar.get_y() + bar.get_height() / 2, f"{ov:.2f}% ({status})", va="center", fontsize=8.5, fontweight="bold")
    ax2.legend(loc="lower left", fontsize=8.5)
    ax2.grid(axis="x", alpha=0.25)

    fig.suptitle(
        "H-SPMD Factorial (2026-10-28): SAR-PU De-confounding Breaks Bare-Rock Crowding (<70%) While Preserving Holdout Gain",
        fontsize=11,
        fontweight="bold",
        y=0.99,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = ROOT / "docs/assets/fig6_spmd_experiments.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
