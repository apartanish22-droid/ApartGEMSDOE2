#!/usr/bin/env python3
"""
ARCHIVED RUNNER: BLOCKED; the saved TIFF fails literal lattice uniqueness.
Historical claims below are not authorization: the shared v3 split is not a
validated whole-segment buffer, the lattice overlap calculation was reversed,
and the complete registry and organizer template were never verified.

Experiment 1 — H-DIL-GRAV (ranked hypothesis #1, research/hypotheses.md).

Hypothesis: concealed normal faults controlling geothermal upflow express as
co-located geodetic dilatation (band 8 `geod_dilaterate`) and an isostatic
gravity low (band 13 `iso_grav_anom`). Propensity =
  normalize(clip(dilatation, 0, None)) * normalize(-gravity)
over the study footprint. Both bands come from the pinned training_features.tif
mirror (GEMSDAWN-derived stack); no external download is required.

Design notes (line-by-line verifiable):
  * Band 8 description: 'Geodetic dilatation rate - rate of volumetric strain'
  * Band 13 description: 'Isostatic gravity anomaly - gravity after compensating
    for topographic mass'
  * Source: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
    (USGS GeoDAWN); grid per prepare_data.py output: EPSG:32611, 3730x3292,
    100 m, origin (243350, 4508550).
  * Non-fault mimics (must be tested, not assumed): broad sedimentary basins
    give gravity lows without faults; regional extension gives dilation without
    a discrete fault. Single-feature rank AUC vs held-out truth is the leakage
    canary (AUC > 0.90 => leakage until proven otherwise).
  * Emission: top-N propensity pixels as a binary mask (N = 37,654, the same dot
    budget as the GEMSDOE32 champion B2), written with the shared writer so
    catalogue pixels are zeroed and values stay in [0,1].
  * Historical evaluation: the shared v3 split did not establish the required
    buffered whole-segment protocol; its numerical report is a diagnostic, not
    valid holdout evidence or an organizer score.
  * Historical uniqueness: sampled surface comparison covered a subset only;
    the lattice check counted lattice pixels near candidates rather than
    candidate pixels near the lattice. The saved TIFF fails the literal gate.

Outputs:
  evidence/h_dil_grav_exp1.json   run card (HOLDOUT-DTI + CI, canary, registry)
  docs/downloads/*-h-dil-grav-*.tif / .zip / -audit.json   archived research bytes, DO NOT SUBMIT
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402
from submission_writer import write_validated_submission  # noqa: E402 (src/submission_writer.py)

N_DOTS = 37_654  # same dot budget as the GEMSDOE32 B2 archival variant
B_GATE_PX = 2.0  # catalogue collar, derived strictly from visible faults inside each split
SEED = 20261028


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_band(path: Path, index: int) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(index).astype(np.float64)


def norm01(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.zeros_like(a)
    v = a[valid]
    if v.size == 0:
        return out
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
    if not np.isfinite(hi - lo) or hi == lo:
        return out
    out[valid] = np.clip((a[valid] - lo) / (hi - lo), 0.0, 1.0)
    return out


def rank_auc(score: np.ndarray, truth: np.ndarray, valid: np.ndarray) -> float:
    """Rank (Spearman-equivalent) AUC of a continuous score vs binary truth."""
    s = score[valid]
    t = truth[valid]
    n_pos = int(t.sum())
    n_neg = int((~t).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = rankdata(s, method="average")
    auc = (r[t].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def main() -> int:
    from experiment_guard import require_current_protocol
    if not require_current_protocol():
        return 2
    ddir = data_dir()
    print(f"Data dir: {ddir}")
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template = ds
    labels = read_band(ddir / "labels.tif", 1) > 0
    labels = labels & foot

    dilate = read_band(ddir / "training_features.tif", 8)   # geod_dilaterate
    grav = read_band(ddir / "training_features.tif", 13)    # iso_grav_anom
    assert dilate.shape == foot.shape and grav.shape == foot.shape, "band/grid mismatch"

    valid = foot & np.isfinite(dilate) & np.isfinite(grav)
    print(f"footprint={int(foot.sum())} valid={int(valid.sum())} labels={int(labels.sum())}")

    # ---- canary: each feature alone on the visible truth (leakage check) ----
    canary = {}
    for name, band in (("geod_dilaterate", dilate), ("minus_iso_grav_anom", -grav)):
        a = rank_auc(band, labels, valid)
        canary[name] = {"auc": a, "two_sided_max": max(a, 1 - a) if np.isfinite(a) else None,
                        "leakage_flag_gt_0.90": bool(max(a, 1 - a) > 0.90) if np.isfinite(a) else None}
        print(f"canary {name}: AUC={a:.4f} two-sided={canary[name]['two_sided_max']:.4f}")
    if any(c["leakage_flag_gt_0.90"] for c in canary.values()):
        print("LEAKAGE CANARY FAILED: a single feature exceeds AUC 0.90 — stop.")
        return 2

    # ---- propensity surface ----
    dil_n = norm01(np.clip(dilate, 0.0, None), valid)   # expansion only
    grav_low_n = norm01(-grav, valid)                   # gravity low = altered/fractured core
    propensity = np.where(valid, dil_n * grav_low_n, 0.0).astype(np.float32)

    # ---- surface uniqueness BEFORE placement (sampled Spearman vs registry) ----
    from scipy.stats import spearmanr

    rng = np.random.default_rng(7)
    fy, fx = np.nonzero(foot)
    sel = rng.choice(fy.size, size=min(300_000, fy.size), replace=False)
    svals = propensity[fy[sel], fx[sel]]
    surface_rho = {}
    focus_dir = Path(".cache/gems_data/registry_focus")
    for p in sorted(focus_dir.glob("GEMSDOE*_best.tif")):
        with rasterio.open(p) as ds:
            m = ds.read(1) > 0
        rho = float(spearmanr(svals, m[fy[sel], fx[sel]]).statistic)
        surface_rho[p.stem] = rho
        print(f"surface Spearman vs {p.stem}: {rho:+.4f}")
    with rasterio.open(focus_dir / "LATTICE_r13.tif") as ds:
        m = ds.read(1) > 0
    rho = float(spearmanr(svals, m[fy[sel], fx[sel]]).statistic)
    surface_rho["LATTICE_r13"] = rho
    print(f"surface Spearman vs LATTICE_r13: {rho:+.4f}")
    if max(abs(v) for v in surface_rho.values()) > 0.90:
        print("SURFACE DRIFT STOP: |rho| > 0.90 vs a registry raster.")
        return 3

    # ---- emission: top-N propensity pixels, binary mask ----
    order = propensity[valid]
    kth = np.partition(order, order.size - N_DOTS)[order.size - N_DOTS]
    mask = (propensity >= kth) & valid
    n_emit = int(mask.sum())
    print(f"emitted={n_emit} on_catalogue={int((mask & labels).sum())}")

    # ---- holdout evaluation (canonical shared evaluator, no private fork) ----
    ctx = holdout.load_holdout_context(ddir)
    res = holdout.evaluate_visible_gated_holdout(
        mask, ctx, b_gate_px=B_GATE_PX, full_map_mask=mask, name="h-dil-grav-exp1",
        n_boot=2000, seed=SEED,
    )
    print(json.dumps({"pooled_dti": res["pooled_dti"], "ci95": res["ci95"],
                      "n_withheld": res["n_withheld_positives"],
                      "sgmc_cal": res["sgmc_off_catalogue"]["prevalence_calibrated_dti"]}, indent=1))

    # ---- uniqueness ON FINAL DOTS vs registry ----
    dot_y, dot_x = np.nonzero(mask)
    dot_overlap = {}
    for p in sorted(focus_dir.glob("GEMSDOE*_best.tif")):
        with rasterio.open(p) as ds:
            m = ds.read(1) > 0 & foot
        # vectorized 3-px neighborhood test via binary dilation
        from scipy.ndimage import binary_dilation

        nb = binary_dilation(m, iterations=3) & foot
        dot_overlap[p.stem] = int((nb & mask).sum()) / max(int(mask.sum()), 1)
        print(f"final-dot 3px overlap vs {p.stem}: {dot_overlap[p.stem]*100:.2f}%")
    from scipy.ndimage import binary_dilation

    nb = binary_dilation(mask, iterations=3) & foot
    with rasterio.open(focus_dir / "LATTICE_r13.tif") as ds:
        lat = ds.read(1) > 0 & foot
    dot_overlap["LATTICE_r13"] = int((nb & lat).sum()) / max(int(mask.sum()), 1)
    print(f"final-dot 3px overlap vs LATTICE_r13: {dot_overlap['LATTICE_r13']*100:.2f}%")
    max_overlap = max(dot_overlap.values())
    if max_overlap > 0.70:
        print(f"UNIQUENESS STOP: max overlap {max_overlap*100:.2f}% > 70%.")
        return 4

    # ---- write archived research bytes, DO NOT SUBMIT ----
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"h-dil-grav-dilate-x-gravlow-top{N_DOTS}"
    note = ("Unique H-DIL-GRAV: geodetic dilatation x gravity low, top-37654 pixels, "
            "not a copy of any prior GEMSDOE site submission")
    assert len(note) <= 140, len(note)
    bundle = write_validated_submission(
        mask, slug=slug,
        candidate_meta={
            "candidate_id": f"h-dil-grav-exp1-{now}",
            "description": "Experiment 1: H-DIL-GRAV geodetic dilatation x isostatic gravity low propensity.",
            "submission_note_zeros": note,
            "submission_note_nan": note,
            "catalogue_hidden_mean": None,
            "catalogue_hidden_per_quadrant": {},
            "sgmc_prevalence_calibrated_dti": res["sgmc_off_catalogue"]["prevalence_calibrated_dti"],
            "drift_corrected_holdout_mean": None,
            "drift_corrected_per_quadrant": {},
            "predicted_leaderboard_dti": None,
            "ei_drift_corrected": None,
            "slot_decision": "HOLD-PENDING-SELECTOR",
        },
    )
    zeros_path = ROOT / "docs" / "downloads" / bundle["zeros_tif"]["filename"]
    print(json.dumps({k: bundle[k] for k in ("candidate_id", "slug", "content_digest8")}, indent=1))
    print("zeros:", bundle["zeros_tif"]["filename"], bundle["zeros_tif"]["sha256"][:16])

    # ---- run card ----
    run_card = {
        "schema": "parallel-run-protocol-run-card-v1",
        "generated_at_utc": now,
        "session_branch": "arena/59f115dd-apartgemsdoe2",
        "hypothesis": "H-DIL-GRAV: concealed geothermal normal faults missing from the USGS/INGENIOUS "
                      "catalogue co-express as geodetic dilatation (training_features band 8) and an "
                      "isostatic gravity low (band 13); propensity = normalized dilatation x normalized "
                      "(-gravity) over the footprint.",
        "mechanism": "Extensional fault zones localize volumetric strain (dilatation); hydrothermal "
                     "alteration and fracturing lower bulk density (gravity low). Their product targets "
                     "concealed faults with no mapped surface scarp.",
        "mimicking_non_fault_process": "Broad sedimentary basins produce gravity lows without faults; "
                                       "regional tectonic extension produces dilation without a discrete fault.",
        "holdout_dti": res["pooled_dti"],
        "holdout_ci95": res["ci95"],
        "holdout_withheld_positives": res["n_withheld_positives"],
        "evaluator_version": res["evaluator_version"],
        "leakage_canary": canary,
        "surface_spearman_vs_registry": surface_rho,
        "final_dot_overlap_vs_registry": {k: round(v, 4) for k, v in dot_overlap.items()},
        "raster": bundle["zeros_tif"]["filename"],
        "raster_sha256": bundle["zeros_tif"]["sha256"],
        "raster_path": str(zeros_path),
        "validator_output": bundle["zeros_tif"],
        "submission_name": bundle["zeros_tif"]["filename"].replace(".tif", ""),
        "note": note,
        "note_length_chars": len(note),
        "emitted_pixels": int(mask.sum()),
        "verdict": "promote" if (res["pooled_dti"] > 0.0992 and max_overlap <= 0.70
                                 and not any(c["leakage_flag_gt_0.90"] for c in canary.values()))
                   else "negative",
    }
    out_path = ROOT / "evidence" / f"h_dil_grav_exp1_{now}.json"
    out_path.write_text(json.dumps(run_card, indent=2) + "\n")
    print(f"wrote run card: {out_path}")
    print(f"VERDICT: {run_card['verdict']}  holdout DTI={res['pooled_dti']:.5f} "
          f"CI={res['ci95']}  max overlap={max_overlap*100:.2f}%")
    return 0 if run_card["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
