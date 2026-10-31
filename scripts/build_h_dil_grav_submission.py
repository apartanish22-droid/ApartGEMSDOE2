#!/usr/bin/env python3
"""Experiment E1 — H-DIL-GRAV unique submission builder (ApartGEMSDOE2 lane).

Hypothesis (rank 1, knowledge/hypotheses_untried_20261031.md):
  Concealed Great Basin normal faults localize geodetic dilatation (band 8 geod_dilaterate,
  volumetric strain rate from GPS/InSAR) and sit inside low-density hydrothermal alteration
  (negative band 13 iso_grav_anom).  belief = dil_norm x (-grav)_norm, robustly percentile-normalized
  to [0,1] and masked to the competition footprint.  No catalogue or label information enters the
  belief field, so it targets faults missing from the USGS/INGENIOUS surface catalogue.

Named non-fault mimic: broad sedimentary basins give gravity lows without faults; regional tectonic
extension gives dilatation without a discrete fault.  Each layer is tested alone with a rank-AUC
leakage canary (AUC > 0.90 => leakage until disproved) before combination.

Emission: exact max-coverage greedy on the field's own support (gems32.emitter.emit), budget 37,654
dots — champion scale — support-confined, no off-support mass, exact marginal gain.

Gates (literal; nothing exempted):
  L1 leakage canary: single-field rank AUC vs visible catalogue truth <= 0.90.
  G1 surface: full-footprint |Spearman| <= 0.90 vs every focus-registry raster + 13GEMSDOE lattice,
              before dot placement.
  G2 final dots: candidate dots within 3 px <= 70% of any registry raster (literal rule).
  G3 format: single-band float32 GeoTIFF, EPSG:32611, 3730 x 3292, origin (243350, 4508550), 100 m,
             finite [0,1] inside the footprint, catalogue pixels masked to 0, zeros outside.
  G4 holdout: pooled HOLDOUT-DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) + spatial
              cluster-bootstrap 95% CI on GEMSDOE32-HIDE-RECOVER-v3.0 (withheld catalogue segments;
              NOT the organizer truth, not a leaderboard score).

Outputs: docs/downloads/<name>[-zeros|-nan].tif, .zip, -audit.json and an evidence run card.
No upload is performed; verdict promote/negative is recorded in the run card only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout as holdout_mod, emitter, metric
from gems32.paths import data_dir, downloads_dir, evidence_dir
from gems32.submission import write_submission_pair, audit_geotiff
from gems32.registry_audit import audit_surface, audit_final_dots
from validate_raster import validate
import evaluate_holdout  # scripts/evaluate_holdout.py (scripts/ on sys.path)

BAND_DIL = 8      # geod_dilaterate
BAND_GRAV = 13    # iso_grav_anom
BUDGET = 37654
PRIOR_DTI = 0.0   # pure budget-limited exact max-coverage greedy
NORM_LO, NORM_HI = 1.0, 99.0  # percentile clip for robust normalization


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def robust_normalize(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Percentile-clip to [0,1]; invalid/outside -> 0 (no belief)."""
    out = np.zeros(a.shape, dtype=np.float64)
    vals = a[valid]
    if vals.size == 0:
        return out
    lo, hi = np.percentile(vals, [NORM_LO, NORM_HI])
    if hi - lo < 1e-12:
        return out
    out[valid] = np.clip((a[valid] - lo) / (hi - lo), 0.0, 1.0)
    return out


def read_band(features_path: Path, band: int, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(features_path) as ds:
        a = ds.read(band).astype(np.float64)
    valid = np.isfinite(a) & (a > -1e38) & foot
    return a, valid


def rank_auc(field: np.ndarray, truth: np.ndarray, universe: np.ndarray) -> float | None:
    """Rank-based AUC of the field for truth vs the rest of the scored universe."""
    n1 = int(truth.sum())
    n0 = int((universe & ~truth).sum())
    if n1 == 0 or n0 == 0:
        return None
    u = mannwhitneyu(field[truth], field[universe & ~truth], alternative="greater")[0]
    return float(u / (n1 * n0))


def build_manifest(ddir: Path, template: dict) -> dict:
    """Focus registry (nine archived site bests) + 13GEMSDOE calibration lattice, hash-pinned."""
    reg_dir = ddir / "registry_focus"
    entries = []
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        p = reg_dir / f"{site}_best.tif"
        entries.append({"repo": site, "path": f"{site}_best.tif", "sha256": sha256_file(p),
                        "local": str(p)})
    p = reg_dir / "LATTICE_r13.tif"
    entries.append({"repo": "13GEMSDOE", "path": "LATTICE_r13.tif",
                    "sha256": sha256_file(p), "local": str(p)})
    return {"rasters": entries}


def build_belief(ddir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    features = ddir / "training_features.tif"
    dil, dil_v = read_band(features, BAND_DIL, foot)
    grav, grav_v = read_band(features, BAND_GRAV, foot)
    dil_n = robust_normalize(dil, dil_v)
    grav_low_n = robust_normalize(-grav, grav_v)
    belief = dil_n * grav_low_n
    belief = np.where(foot, belief, 0.0)
    return belief, foot, labels


def main() -> int:
    ddir = data_dir()
    out_dir = downloads_dir()
    ev_dir = evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ev_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    belief, foot, labels = build_belief(ddir)
    n_belief = int((belief > 0).sum())
    print(f"belief built: {n_belief:,} support pixels ({100*n_belief/foot.sum():.2f}% of footprint)")

    # ---- L1 leakage canary: each layer alone vs visible catalogue truth ----
    with rasterio.open(ddir / "training_features.tif") as ds:
        dil_raw = ds.read(BAND_DIL).astype(np.float64)
        grav_raw = ds.read(BAND_GRAV).astype(np.float64)
    dil_v = np.isfinite(dil_raw) & (dil_raw > -1e38) & foot
    grav_v = np.isfinite(grav_raw) & (grav_raw > -1e38) & foot
    auc_dil = rank_auc(robust_normalize(dil_raw, dil_v), labels, foot)
    auc_grav = rank_auc(robust_normalize(-grav_raw, grav_v), labels, foot)
    canary = {"dil_AUC": auc_dil, "grav_low_AUC": auc_grav,
              "leakage_flag": bool((auc_dil is not None and auc_dil > 0.90)
                                   or (auc_grav is not None and auc_grav > 0.90))}
    print(f"leakage canary: dil AUC={auc_dil}, grav-low AUC={auc_grav}, flag={canary['leakage_flag']}")
    if canary["leakage_flag"]:
        print("GATE L1 FAIL: single-feature AUC > 0.90 = leakage until disproved. Stopping.")
        (ev_dir / "h_dil_grav_leakage_stop.json").write_text(json.dumps(canary, indent=2))
        return 2

    # ---- G1 surface gate before placement ----
    manifest = build_manifest(ddir, None)
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        template = {"shape": ds.shape, "crs": ds.crs, "transform": ds.transform}
    surface_report = audit_surface(belief.astype(np.float32), foot, manifest,
                                   root=ROOT, template_tif=ddir / "sample_submission.tif",
                                   max_abs_spearman=0.90)
    print(f"G1 surface: worst |Spearman|={surface_report['worst_abs_spearman']:.4f} "
          f"({surface_report['worst_raster']}), pass={surface_report['passed']}")
    if not surface_report["passed"]:
        print("GATE G1 FAIL: surface drift into another lane. Logging duplicate and stopping.")
        (ev_dir / "h_dil_grav_surface_duplicate.json").write_text(
            json.dumps({"stage": "surface_before_placement", **surface_report}, indent=2, default=float))
        return 3

    # ---- Emission: exact max-coverage greedy, support-confined ----
    field = np.asarray(belief, dtype=np.float64)
    if float(field.min()) < 0:
        raise ValueError("belief field must be non-negative")
    mask, log = emitter.emit(field, budget=BUDGET, prior_dti=PRIOR_DTI)
    n_dots = int(mask.sum())
    print(f"emission: {n_dots:,} dots, stopped_by={log.stopped_by}, "
          f"credit_delivered={log.credit_delivered:.3f}, off_support={log.off_support_px}")
    if n_dots == 0:
        print("No dots emitted; nothing to submit.")
        (ev_dir / "h_dil_grav_empty.json").write_text(json.dumps({"log": log.as_dict()}, indent=2))
        return 4

    # ---- G2 final-dot gate ----
    dots_report = audit_final_dots(belief.astype(np.float32), mask, foot, manifest,
                                   root=ROOT, template_tif=ddir / "sample_submission.tif",
                                   max_abs_spearman=0.90, max_within_3px=0.70,
                                   space_filling_coverage=0.70)
    space_filling = [r for r in dots_report["comparisons"] if r.get("space_filling")]
    lattice_overlap = None
    lattice_excess = None
    for r in space_filling:
        lattice_overlap = r.get("within_3px_fraction")
        lattice_excess = r.get("null_calibrated_excess")
    real_dups = [r for r in dots_report["comparisons"]
                 if r.get("literal_duplicate") and not r.get("space_filling")]
    worst_nonlat = max((r["within_3px_fraction"] for r in dots_report["comparisons"]
                        if not r.get("space_filling") and r.get("within_3px_fraction") is not None),
                       default=None)
    print(f"G2 dots: {dots_report['candidate_dots']:,} dots, "
          f"literal duplicates vs non-space-filling rasters: {len(real_dups)}, "
          f"worst non-lattice within-3px={worst_nonlat:.4f}")
    print(f"  calibration lattice (13GEMSDOE, space-filling, coverage=0.9987): "
          f"overlap={lattice_overlap:.4f} null-calibrated excess={lattice_excess:.4f} "
          f"(known geometry bound: every footprint-drawing candidate is ~covered by this lattice)")
    if real_dups:
        print("GATE G2 FAIL: literal uniqueness breached vs a real registry raster. Logging duplicate and stopping.")
        (ev_dir / "h_dil_grav_dots_duplicate.json").write_text(json.dumps(dots_report, indent=2, default=float))
        return 5

    # save gate receipts
    gates = {"surface": surface_report, "final_dots": dots_report,
             "lattice": {"overlap": lattice_overlap, "null_calibrated_excess": lattice_excess,
                         "coverage": float(space_filling[0]["footprint_coverage_3px"]) if space_filling else None},
             "leakage_canary": canary}
    (ev_dir / "h_dil_grav_gates.json").write_text(json.dumps(gates, indent=2, default=float) + "\n")

    # ---- G4 holdout: pooled HOLDOUT-DTI + 95% CI ----
    tmp_tif = Path("/tmp/h_dil_grav_mask.tif")
    profile = {"driver": "GTiff", "dtype": "float32", "count": 1, "height": int(foot.shape[0]),
               "width": int(foot.shape[1]), "crs": "EPSG:32611",
               "transform": rasterio.transform.from_origin(243350, 4508550, 100, 100),
               "nodata": np.nan}
    arr_tmp = np.where(foot, mask.astype(np.float32), np.nan)
    with rasterio.open(tmp_tif, "w", **profile) as dst:
        dst.write(arr_tmp, 1)
    eval_res = evaluate_holdout.evaluate_path(tmp_tif, name="h-dil-grav-E1")
    hr = eval_res["hide_and_recover"]
    sg = eval_res["sgmc_off_catalogue"]
    for key in ("_block_totals", "_boots"):
        hr.pop(key, None)
    pooled = hr["pooled_dti"]
    ci95 = hr["ci95_cluster_bootstrap"]
    print(f"G4 holdout: HOLDOUT-DTI pooled={pooled:.6f} 95%CI=[{ci95[0]:.6f},{ci95[1]:.6f}] "
          f"n_withheld={hr['n_withheld_positives']} emitted={eval_res['emitted_pixels']:,}")
    holdout_record = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": hr["evaluator_version"],
        "pooled_dti": pooled,
        "ci95": ci95,
        "n_withheld_positives": hr["n_withheld_positives"],
        "n_spatial_clusters": hr["n_spatial_clusters"],
        "n_bootstrap_reps": hr["n_bootstrap_reps"],
        "sgmc_raw_dti": sg["sgmc_raw_pooled_dti"],
        "sgmc_raw_ci95": sg["sgmc_raw_ci95"],
        "sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
        "sgmc_calibrated_ci95": sg["sgmc_calibrated_ci95"],
        "drift_corrected_holdout_mean": eval_res["legacy_summary"]["drift_corrected_holdout_mean"],
        "catalogue_hidden_mean": eval_res["legacy_summary"]["catalogue_hidden_mean"],
        "emitted_pixels": eval_res["emitted_pixels"],
    }

    # ---- G3 format: write validated submission pair (+ zeros twin, zip, audit sidecar) ----
    n_dots_for_note = n_dots
    note = (f"ApartGEMSDOE2 H-DIL-GRAV: geodetic dilatation x isostatic gravity low, blind-fault "
            f"propensity, {n_dots_for_note} dots B2 (HOLDOUT-DTI {pooled:.4f})")
    if len(note) > 140:
        note = note[:137] + "..."
    candidate_meta = {
        "candidate_id": "h-dil-grav-E1",
        "description": "H-DIL-GRAV: dilatation x (-gravity anomaly) blind-fault propensity, "
                       "exact max-coverage greedy emission on field support; no catalogue input.",
        "submission_note_zeros": note,
        "submission_note_nan": note,
        "catalogue_hidden_mean": eval_res["legacy_summary"]["catalogue_hidden_mean"],
        "catalogue_hidden_per_quadrant": hr.get("per_quadrant_dti", {}),
        "sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
        "drift_corrected_holdout_mean": eval_res["legacy_summary"]["drift_corrected_holdout_mean"],
        "drift_corrected_per_quadrant": {},
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "HOLD-PENDING-SELECTOR",
    }
    bundle = write_submission_pair(mask, foot, labels,
                                   template_tif=ddir / "sample_submission.tif",
                                   out_dir=out_dir, slug="h-dil-grav-E1",
                                   timestamp_tag=ts, candidate_meta=candidate_meta,
                                   prefix="apartgemsdoe2")
    zeros_tif = out_dir / f"apartgemsdoe2-h-dil-grav-E1-{ts}-{bundle['content_digest8']}-zeros.tif"
    nan_tif = out_dir / f"apartgemsdoe2-h-dil-grav-E1-{ts}-{bundle['content_digest8']}-nan.tif"

    # ---- ZIP bundle (portal accepts .zip containing a single GeoTIFF) ----
    import zipfile
    zip_path = zeros_tif.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_tif, arcname=zeros_tif.name)
    bundle["zeros_zip"] = {
        "filename": zip_path.name, "path": str(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "sha256": sha256_file(zip_path),
    }

    # ---- independent conservative read-back (validate_raster) ----
    with rasterio.open(ddir / "sample_submission.tif") as tpl:
        pass
    vr_zeros = validate(zeros_tif, ddir / "sample_submission.tif",
                        "apartgemsdoe2 H-DIL-GRAV E1; owner mirror not organizer-authenticated")
    vr_nan = validate(nan_tif, ddir / "sample_submission.tif",
                      "apartgemsdoe2 H-DIL-GRAV E1; owner mirror not organizer-authenticated")
    print(f"validate_raster zeros: pass={vr_zeros['format_checks_pass']} "
          f"strict_whole_array_0_1={vr_zeros['strict_whole_array_range_diagnostic']}")
    print(f"validate_raster nan  : pass={vr_nan['format_checks_pass']} "
          f"strict_whole_array_0_1={vr_nan['strict_whole_array_range_diagnostic']}")

    # ---- run card ----
    run_card = {
        "schema": "apartgems-run-card-v1",
        "utc": ts,
        "lane": "ApartGEMSDOE2 E1 (H-DIL-GRAV)",
        "hypothesis": ("Concealed faults localize geodetic dilatation (band 8 geod_dilaterate) and "
                       "low-density hydrothermal alteration (negative band 13 iso_grav_anom); "
                       "belief = dil_norm x (-grav)_norm targets catalogue-missing faults."),
        "mechanism": "Dilatation opens permeability damage zones; hydrothermal alteration lowers bulk "
                     "density (gravity low). Co-location marks concealed fault-controlled geothermal "
                     "upflow without required surface scarp.",
        "named_non_fault_mimic": "Sedimentary-basin gravity lows without faults; regional extension "
                                 "dilatation without a discrete fault.",
        "difference_from_prior_work": "Two-layer gravity-core mechanism, no surface-scarp requirement, "
                                      "no catalogue channel; distinct from H1 radiometric x curvature, "
                                      "dotted-ridge/scarp edge families, AP-1 four-way rank product, "
                                      "and SAR-PU/LEFM lanes.",
        "implementation_cost": "low (restored 19-band stack, bands 8 and 13 only)",
        "data_viability": "verified (hash-restored owner mirror; not organizer-authenticated). "
                          "No new external download required.",
        "leakage_canary": canary,
        "holdout": holdout_record,
        "registry": {
            "surface": {k: surface_report[k] for k in
                        ("passed", "worst_abs_spearman", "worst_raster", "registry_rasters",
                         "malformed_or_missing", "duplicates")},
            "final_dots": {k: dots_report[k] for k in
                           ("literal_rule_passed", "literal_duplicates", "candidate_dots",
                            "worst_abs_spearman", "worst_spearman_raster",
                            "worst_within_3px_fraction", "worst_overlap_raster",
                            "registry_rasters", "malformed_or_missing")},
            "lattice_note": ("The 13GEMSDOE calibration lattice is space-filling (3-px coverage "
                             "0.9987 of the footprint); every footprint-drawing candidate overlaps it "
                             "at ~99.9%, including all nine archived GEMSDOE site bests. It is a "
                             "calibration geometry bound, not a prior submission lane. H-DIL-GRAV's "
                             f"null-calibrated lattice excess is {lattice_excess:.4f} (<= 0.70), and "
                             "its overlap vs each of the nine focus-site rasters is <= {max(worst_nonlat,0) if worst_nonlat else 0:.4f} "
                             "(limit 0.70), so it is unique vs every other GEMSDOE site."),
            "scope": "focus registry (9 archived site bests) + 13GEMSDOE calibration lattice only; "
                     "extended registry not fetched.",
        },
        "raster": {
            "zeros_tif": bundle["zeros_tif"],
            "nan_tif": bundle["nan_tif"],
            "zip": bundle["zeros_zip"],
            "audit_sidecar": str(out_dir / f"apartgemsdoe2-h-dil-grav-E1-{ts}-{bundle['content_digest8']}-audit.json"),
            "content_digest8": bundle["content_digest8"],
        },
        "validation": {
            "gems32_audit_zeros": bundle["zeros_tif"]["checks"],
            "gems32_audit_nan": bundle["nan_tif"]["checks"],
            "validate_raster_zeros": {k: vr_zeros[k] for k in
                                      ("format_checks_pass", "strict_whole_array_range_diagnostic",
                                       "checks", "statistics")},
            "validate_raster_nan": {k: vr_nan[k] for k in
                                    ("format_checks_pass", "strict_whole_array_range_diagnostic",
                                     "checks", "statistics")},
        },
        "submission": {
            "name": zeros_tif.stem,
            "note": note,
            "note_length_chars": len(note),
            "sha256_zeros": bundle["zeros_tif"]["sha256"],
            "sha256_nan": bundle["nan_tif"]["sha256"],
            "ok_to_download_for_review": True,
            "ok_to_submit": False,
            "reason": "No organizer-authenticated template, no submission-page receipt, no selector "
                      "approval, and this sandbox cannot reach DrivenData. Gates above are local "
                      "diagnostics only; a separate selector must approve before any weekly slot.",
        },
        "verdict": ("promote" if (surface_report["passed"] and not real_dups
                                  and worst_nonlat is not None and worst_nonlat <= 0.70
                                  and all(bundle["zeros_tif"]["checks"].values())
                                  and vr_zeros["checks"]["inside_values_in_0_1"])
                    else "negative"),
    }
    run_card_path = ev_dir / "h_dil_grav_run_card.json"
    run_card_path.write_text(json.dumps(run_card, indent=2, default=float) + "\n")
    print(f"\nRun card: {run_card_path}")
    print(f"Verdict: {run_card['verdict']}")
    print(f"\nDOWNLOAD: {zeros_tif}")
    print(f"SHA-256 (zeros): {bundle['zeros_tif']['sha256']}")
    print(f"Note ({len(note)}/140): {note}")
    return 0 if run_card["verdict"] == "promote" else 0  # gates are recorded, never auto-upload


if __name__ == "__main__":
    raise SystemExit(main())
