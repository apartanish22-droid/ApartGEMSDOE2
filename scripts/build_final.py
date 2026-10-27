#!/usr/bin/env python3
"""EXP-3 confirmation (no tuning): freeze EXP-2 mask -> GeoTIFF pair -> validator + uniqueness.

Verdict logic is fail-closed (knowledge/preregistration-20261027.md): any failed gate
=> DO NOT SUBMIT. This script never upgrades a verdict; it only records measurements.
"""
from __future__ import annotations

import hashlib, json, sys, zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

WORK = Path("/tmp/apart_work")
DDATA = Path("/tmp/gems_data")
TAG = "exp2"  # frozen winner of EXP-1/2 screen (both negative; EXP-2 is the confirmed variant)


def dots_overlap_3px(cand: np.ndarray, reg: np.ndarray) -> float:
    from scipy.ndimage import distance_transform_edt
    d = distance_transform_edt(~reg)
    return float((d[cand] <= 3).mean()) if cand.any() else 0.0


def main() -> int:
    raise SystemExit('STOP: archived parallel lane failed the literal lattice novelty gate and the experiment budget was reported spent; no new run or promotion is authorized.')
    import rasterio
    from gemsdoe32.submission import write_submission_geotiff, validate_submission_geotiff

    mask = np.load(WORK / f"mask_{TAG}.npy")
    surf = np.load(WORK / f"surface_final_{TAG}.npy")
    with rasterio.open(DDATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(DDATA / "labels.tif") as ds:
        labels = (ds.read(1) == 1) & foot
    assert int(mask.sum()) == 37654 and int((mask & labels).sum()) == 0

    digest8 = hashlib.sha256(np.packbits(mask)).hexdigest()[:8]
    stamp = "20261027"
    base = f"apartgemsdoe2-ap1-dilatcond-37654-{stamp}-{digest8}"
    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    tmpl = DDATA / "sample_submission.tif"

    man_z = write_submission_geotiff(mask.astype(np.float32), tmpl, outdir / f"{base}-zeros.tif", outside_mode="zeros")
    man_n = write_submission_geotiff(mask.astype(np.float32), tmpl, outdir / f"{base}-nan.tif", outside_mode="nan")
    with zipfile.ZipFile(outdir / f"{base}-zeros.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(outdir / f"{base}-zeros.tif", arcname=f"{base}-zeros.tif")

    # uniqueness: final dots vs 9 champions + lattice (surface rho already in exp receipts)
    uniq = {}
    for p in sorted(Path("/tmp/gems_data/registry_focus").glob("*.tif")):
        with rasterio.open(p) as ds:
            reg = np.isfinite(ds.read(1)) & (ds.read(1) > 0)
        uniq[p.stem] = {"within3px_frac": dots_overlap_3px(mask, reg), "dots": int(reg.sum())}
        print(p.stem, uniq[p.stem])

    e1 = json.loads((ROOT / "evidence/experiment_exp1.json").read_text())
    e2 = json.loads((ROOT / "evidence/experiment_exp2.json").read_text())
    gates = {
        "format_validator_zeros": bool(man_z["validation_passed"]),
        "format_validator_nan": bool(man_n["validation_passed"]),
        "leakage_canary_le_0.90": bool(all(not v.get("leakage_flag_gt_0.90", False) for v in e1["canary_auc"].values())),
        "holdout_beats_champion_paired_ci_gt_0": bool(e2["paired_vs_champion_foldlocal"]["paired_ci95"][0] > 0),
        "sgmc_no_regression_vs_champion": bool(
            e2["sgmc_candidate_final"]["sgmc_prevalence_calibrated_dti"]
            >= e2["sgmc_champion_final"]["sgmc_prevalence_calibrated_dti"]),
        "uniqueness_focus9_within3px_le_0.70": bool(
            max(v["within3px_frac"] for k, v in uniq.items() if k.startswith("GEMSDOE")) <= 0.70),
        # The archived code below is stopped above. Even if the stop is removed,
        # the lattice is not exempt and an incomplete registry cannot promote.
        "uniqueness_including_lattice_within3px_le_0.70": bool(
            "LATTICE_r13" in uniq and uniq["LATTICE_r13"]["within3px_frac"] <= 0.70),
        "complete_registry_and_final_surface_verified": False,
    }
    verdict = "promote" if all(gates.values()) else "negative"
    note = f"AP-1 dilat+cond+base+grav coincidence 37654d B2 | HOLDOUT-DTI 0.0389 vs champ 0.0992 | {digest8} | DO NOT SUBMIT"[:140]
    card = {
        "hypothesis": "Blind dilatational stepovers coincide in geodetic strain, conductivity edge, basement step and gravity edge (AP-1 lane, knowledge/preregistration-20261027.md).",
        "mechanism": "Geometric-mean percentile-rank coincidence (bands 4/7/8 x grad 17 x grad 15 x grad 13), score-ordered Poisson emission min-sep 2.8px, B=2 collar, 37,654 dots.",
        "named_non_fault_mimic": "Basin-margin depocentre edges, buried volcanic/pluton contacts, aquifer lithologic boundaries.",
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": e2["candidate_oof"]["evaluator_version"],
        "holdout_dti": e2["candidate_oof"]["pooled_dti"],
        "holdout_ci95": e2["candidate_oof"]["ci95"],
        "n_withheld_positives": e2["candidate_oof"]["n_withheld_positives"],
        "champion_foldlocal_dti": e2["control_champion_foldlocal"]["pooled_dti"],
        "paired_delta_vs_champion": e2["paired_vs_champion_foldlocal"],
        "sgmc_cal_candidate": e2["sgmc_candidate_final"]["sgmc_prevalence_calibrated_dti"],
        "sgmc_cal_champion": e2["sgmc_champion_final"]["sgmc_prevalence_calibrated_dti"],
        "correlation_overlap_vs_registry": {"surface_spearman_sample300k_exp1": e1["surface_spearman_vs_registry_sample300k"],
                                            "final_dots_within3px": uniq},
        "gates": gates,
        "raster_sha256_zeros": man_z["sha256"], "raster_sha256_nan": man_n["sha256"],
        "validator_output": {"zeros": man_z["validation_report"], "nan": man_n["validation_report"],
                             "dots": int(mask.sum()), "on_catalogue": int((mask & labels).sum()),
                             "footprint_px": int(foot.sum())},
        "submission_name": base + "-zeros",
        "submission_note_140": note, "note_chars": len(note),
        "leaderboard_estimate": "NOT ESTIMABLE — no validated HOLDOUT-DTI to live-score transfer (cross-family RMSE 0.09-0.20 in GEMSDOE31 calibration audit); HOLDOUT-DTI is not a leaderboard score.",
        "verdict": verdict,
        "download_ok": True, "submit_ok": bool(verdict == "promote"),
    }
    (ROOT / "evidence/run_card_final.json").write_text(json.dumps(card, indent=1) + "\n")
    (outdir / f"receipt-{base}-zeros.json").write_text(json.dumps(card, indent=1) + "\n")
    print(json.dumps({"gates": gates, "verdict": verdict, "name": card["submission_name"],
                      "sha256": man_z["sha256"][:16], "note": note}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
