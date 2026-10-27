#!/usr/bin/env python3
"""AP2 final stage: uniqueness (G3, incl. broad focus-repo registry), canonical write (G1),
independent re-validation, gates, projection, and the protocol Rule-5 run card.

Expects stage outputs from scripts/run_ap2.py and scripts/audit_focus9.py.
Writes posteriors only; it does not spend any submission slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems32 import holdout, submission  # noqa: E402
from gems32.metric import kernel  # noqa: E402
from gems32.paths import data_dir, downloads_dir, work_dir  # noqa: E402
from validate_submission import check as validate_check  # noqa: E402

CHAMPION_LIVE_OWNER = 0.2778  # OWNER-REPORTED; no organiser receipt in any reviewed repo


def log(m):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-dir", default="/tmp/refs")
    ap.add_argument("--broad-registry", action="store_true", help="also check every downloads tif in the 9 focus clones")
    args = ap.parse_args()
    refs = Path(args.refs_dir)
    ddir, wdir = data_dir(), work_dir()
    out_dir = downloads_dir()

    ctx = holdout.load_holdout_context(ddir)
    foot, labels = ctx.foot, ctx.labels
    exp = json.loads((ROOT / "evidence/ap2_experiments.json").read_text())["results"]
    canary = json.loads((ROOT / "evidence/ap2_exp1_canary.json").read_text())
    partial = json.loads((ROOT / "evidence/ap2_final_partial.json").read_text())
    focus9 = json.loads((ROOT / "evidence/ap2_focus9_forensics.json").read_text())
    oof_meta = json.loads((ROOT / "evidence/ap2_exp1_oof.json").read_text())

    final_mask = np.load(wdir / "ap2_final_mask.npy") & foot & ~labels
    cand_hr = exp["FINAL"]["hide_and_recover"]
    champ_hr = exp["CHAMPION"]["hide_and_recover"]
    cand_sg = exp["FINAL"]["sgmc"]
    champ_sg = exp["CHAMPION"]["sgmc"]
    cand_dti, champ_dti = float(cand_hr["pooled_dti"]), float(champ_hr["pooled_dti"])
    paired = partial.get("paired_vs_champion") or {}
    g2 = bool(cand_dti > champ_dti and paired.get("ci95", [0, 0])[0] > 0)

    boots_np = np.load(wdir / "ap2_boots.npz") if (wdir / "ap2_boots.npz").exists() else None

    # -------- G3 uniqueness: surface (pre-placement) + dots (final), per protocol rule 1 ----
    surf = np.load(wdir / "ap2_field_better.npy") if (wdir / "ap2_field_better.npy").exists() else \
        np.asarray(np.lib.format.open_memmap(wdir / "ap2_oof_surface.npy", mode="r"), dtype=np.float32)
    rng = np.random.default_rng(20261027)
    foot_idx = np.flatnonzero(foot.ravel())
    sp_idx = rng.choice(foot_idx, size=min(300_000, foot_idx.size), replace=False)
    surf_vec = surf.ravel()[sp_idx].astype(np.float64)
    per_winner = {}
    worst_rho, worst_frac = 0.0, 0.0
    for repo, info in focus9["winners"].items():
        if not info.get("found"):
            per_winner[repo] = {"found": False}
            continue
        p = refs / info["measured_file"]
        rm = holdout.read_binary(p) & foot
        edt_r = distance_transform_edt(~rm)
        frac = float((edt_r[final_mask] <= 3.0).mean()) if final_mask.any() else 0.0
        dens_vec = kernel(edt_r.ravel()[sp_idx])
        rho = float(spearmanr(surf_vec, dens_vec).statistic)
        rho = 0.0 if not np.isfinite(rho) else rho
        per_winner[repo] = {
            "measured_file": info["measured_file"], "registry_dots": int(rm.sum()),
            "surface_spearman_vs_registry_dot_kernel_density_sampled300k": round(rho, 5),
            "frac_candidate_dots_within_3px": round(frac, 5),
            "candidate_subset_of_registry_exact": bool((final_mask & ~rm).sum() == 0),
            "registry_subset_of_candidate_exact": bool((rm & ~final_mask).sum() == 0),
            "dotmask_identical": info["dotmask_sha256"] == hashlib.sha256(np.packbits(final_mask)).hexdigest(),
        }
        worst_rho = max(worst_rho, abs(rho))
        worst_frac = max(worst_frac, frac)
        del rm, edt_r
    g3_winners = bool(worst_rho <= 0.90 and worst_frac <= 0.70)

    broad = None
    if args.broad_registry:
        t0 = time.time()
        seen_dotmasks: dict[str, int] = {}
        n_files = n_genuine = n_skipped_dense = 0
        worst_b = (0.0, "")
        focus_repos = sorted(focus9["winners"].keys())
        cand_edt_cache = None
        for repo in focus_repos:
            for p in sorted((refs / repo / "docs" / "downloads").glob("*.tif")) if (refs / repo / "docs" / "downloads").exists() else []:
                n_files += 1
                try:
                    rm = holdout.read_binary(p) & foot
                except Exception as e:  # corrupt/foreign raster: count, don't hide
                    seen_dotmasks[f"UNREADABLE:{p.name}"] = 0
                    continue
                nd = int(rm.sum())
                dm = hashlib.sha256(np.packbits(rm)).hexdigest()
                if dm in seen_dotmasks:
                    continue
                seen_dotmasks[dm] = nd
                if nd == 0 or nd > 150_000:  # continuous surfaces / covering lattices / dense probes
                    n_skipped_dense += 1
                    continue
                n_genuine += 1
                edt_r = distance_transform_edt(~rm)
                frac = float((edt_r[final_mask] <= 3.0).mean())
                if frac > worst_b[0]:
                    worst_b = (frac, f"{repo}/docs/downloads/{p.name}")
                del rm, edt_r
        broad = {"focus_downloads_tif_files_seen": n_files,
                 "unique_dotmasks": len(seen_dotmasks),
                 "genuine_discrete_le150k_dot_rasters_checked": n_genuine,
                 "skipped_dense_continuous_or_lattice": n_skipped_dense,
                 "worst_frac_candidate_dots_within_3px": round(worst_b[0], 5),
                 "worst_peer": worst_b[1], "seconds": round(time.time() - t0, 1),
                 "passed_le_0.70": bool(worst_b[0] <= 0.70)}
        log(f"broad registry: {broad}")

    gates_pre = {
        "G2_holdout_beats_champion_paired_ci_gt_0": g2,
        "G3_unique_vs_9_winners": g3_winners,
        "G3b_unique_vs_broad_focus_registry": (broad["passed_le_0.70"] if broad else None),
        "G4_leakage_canary": bool(canary["passed"]),
        "G5_zero_on_catalogue_and_Bgt2": bool(partial["on_catalogue_dots"] == 0 and (partial["min_distance_to_catalogue_px"] or 0) > 2.0),
        "G6_no_exact_subset_or_identical": bool(all(not v.get("candidate_subset_of_registry_exact", False)
                                                     and not v.get("dotmask_identical", False)
                                                     for v in per_winner.values() if v.get("found", True))),
    }
    promote_pre = all(v for v in gates_pre.values() if v is not None)

    # -------- canonical write (G1 inside writer) -------------------------------------------
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    budget = int(final_mask.sum())
    note_tmpl = ("AP2 OOFCTRL crest+creditbar {dots}dots B2 HOLDOUT-DTI {cat_hid:.4f} "
                 "vs champ0.0992 uniq-score sha{sha8}")
    meta = {
        "candidate_id": "AP2-OOFCTRL",
        "description": "ApartGEMSDOE2 AP2 lane candidate: crest-sharpened 4-quadrant OOF HistGB (35ch canonical stack incl. 20 external, PU lidar-gap neg weight 0.5), EXP1 control selected over the chain gate by the preregistered EXP3 rule; exact emitter min_sep 0.0, B=2, credit-bar budget. See evidence/ap2_run_card.json.",
        "submission_note_zeros": note_tmpl, "submission_note_nan": note_tmpl,
        "catalogue_hidden_mean": cand_dti, "catalogue_hidden_per_quadrant": cand_hr.get("per_quadrant_dti", {}),
        "sgmc_prevalence_calibrated_dti": float(cand_sg.get("sgmc_prevalence_calibrated_dti", 0.0)),
        "drift_corrected_holdout_mean": cand_dti, "drift_corrected_per_quadrant": cand_hr.get("per_quadrant_dti", {}),
        "predicted_leaderboard_dti": None, "ei_drift_corrected": None,
        "slot_decision": "PROMOTE-ELIGIBLE" if promote_pre else "HOLD-DO-NOT-SUBMIT",
    }
    bundle = submission.write_submission_pair(
        mask=final_mask, foot=foot, labels=labels, template_tif=ddir / "sample_submission.tif",
        out_dir=out_dir, slug=f"ap2-oofctrl-{budget}dots", timestamp_tag=ts,
        candidate_meta=meta, prefix="apartgemsdoe2")
    zeros_path = out_dir / bundle["zeros_tif"]["filename"]
    nan_path = out_dir / bundle["nan_tif"]["filename"]
    zip_path = zeros_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)
    bundle["zeros_zip"] = {"filename": zip_path.name, "size_bytes": zip_path.stat().st_size,
                           "sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest()}

    # -------- independent re-validation of the saved bytes ----------------------------------
    val_zero = validate_check(zeros_path, ddir / "sample_submission.tif", ddir / "labels.tif")
    val_nan = validate_check(nan_path, ddir / "sample_submission.tif", ddir / "labels.tif")
    g1 = bool(val_zero["pass"] and bundle["zeros_tif"]["all_checks_passed"])
    gates = {"G1_format_strict_saved_bytes": g1, **gates_pre}
    verdict = "promote" if all(v for v in gates.values() if v is not None) else "negative"

    # -------- projection (labelled, champion-anchored; NOT a score) -------------------------
    ratio_est = CHAMPION_LIVE_OWNER * (cand_dti / champ_dti) if champ_dti > 0 else None
    delta_est = CHAMPION_LIVE_OWNER + (cand_dti - champ_dti)
    proj_lo, proj_hi = sorted([ratio_est, delta_est])
    projection = {
        "label": "PROJECTION (not a score)",
        "method": "Champion-anchored transfer: ratio and delta maps from HOLDOUT-DTI(v3.0) to the champion's OWNER-REPORTED live 0.2778. The interval spans both maps.",
        "anchor": {"candidate_holdout_dti": cand_dti, "champion_holdout_dti_same_evaluator": champ_dti,
                   "champion_live_owner_reported": CHAMPION_LIVE_OWNER},
        "ratio_map": ratio_est, "delta_map": delta_est, "interval": [proj_lo, proj_hi],
        "caveat": "Unvalidated transfer: every holdout-beating candidate since Oct 2025 was held DO-NOT-SUBMIT, so no holdout->live pair above the champion exists. Holdout truth is catalogue-style segments; live truth is expert-mapped off-catalogue faults. Treat as planning range only.",
    }

    submission_name = f"ApartGEMSDOE2-AP2-OOFCTRL-{bundle['zeros_tif']['sha256'][:8].upper()}"
    note_final = bundle["submission_note_zeros"]
    assert len(note_final) <= 140, note_final

    card = {
        "hypothesis": "AP2-H1 CCCB as tested: a crest-sharpened 4-quadrant OOF multi-physics surface (PU lidar-gap down-weighting) might beat the champion, and chain corroboration (along-strike continuity) might add more. The chain arm was rejected (EXP2 < EXP1 on both holdout metrics), so the emitted candidate is the preregistered EXP3-selected EXP1 control field, not a chain field.",
        "mechanism": f"field={exp['FINAL']['field']} (chain gate not applied) -> mdrc.sharpen_ridge_crest -> exact submodular emitter (min_sep 0.0px per Pass-2 amendment, B>2) at budget {budget}; OOF fold AUCs {oof_meta.get('fold_aucs')}; shoreline-risk proxy share {partial['shoreline_risk_proxy_share']:.4f}.",
        "named_non_fault_mimic": "Pleistocene Lake Lahontan shoreline benches and basalt-flow margins (elongated, chain-supported, low-slope); saline playa conductivity edges and road/rail prisms are secondary mimics.",
        "holdout_dti": {"label": "HOLDOUT-DTI", "evaluator_version": cand_hr["evaluator_version"],
                        "pooled_dti": cand_dti, "ci95": cand_hr["ci95_cluster_bootstrap"],
                        "n_withheld_positives": cand_hr["n_withheld_positives"],
                        "per_quadrant_dti": cand_hr.get("per_quadrant_dti")},
        "champion_control_same_evaluator": {"label": "HOLDOUT-DTI", "evaluator_version": champ_hr["evaluator_version"],
                                            "pooled_dti": champ_dti, "ci95": champ_hr["ci95_cluster_bootstrap"],
                                            "n_withheld_positives": champ_hr["n_withheld_positives"],
                                            "live_score": "OWNER-REPORTED 0.2778 (no organiser receipt)"},
        "paired_delta_vs_champion": paired,
        "sgmc_off_catalogue": {"label": "HOLDOUT-DTI", "evaluator_version": cand_sg["evaluator_version"],
                               "candidate_calibrated": cand_sg.get("sgmc_prevalence_calibrated_dti"),
                               "candidate_calibrated_ci95": cand_sg.get("sgmc_calibrated_ci95"),
                               "champion_calibrated": champ_sg.get("sgmc_prevalence_calibrated_dti"),
                               "n_withheld_positives": cand_sg.get("n_withheld_positives")},
        "experiments": {"EXP1_CTRL": exp.get("EXP1_CTRL", {}).get("hide_and_recover", {}).get("pooled_dti"),
                        "EXP2_CHAIN": exp.get("EXP2_CHAIN", {}).get("hide_and_recover", {}).get("pooled_dti"),
                        "EXP3_best_budget": exp.get("EXP3_SCAN", {}).get("best_budget"),
                        "EXP3_scan": {k: v["hide_and_recover"]["pooled_dti"] for k, v in exp.get("EXP3_SCAN", {}).get("scan", {}).items()}},
        "leakage_canary": {"worst_channel": canary["worst_channel"], "worst_auc_oriented": canary["worst_auc_oriented"],
                           "threshold": 0.90, "passed": canary["passed"]},
        "correlation_overlap_vs_registry": {"per_focus_winner": per_winner,
                                            "worst_abs_surface_spearman": round(worst_rho, 5),
                                            "worst_frac_dots_within_3px": round(worst_frac, 5),
                                            "broad_focus_registry": broad},
        "raster_sha256": bundle["zeros_tif"]["sha256"],
        "raster_file": bundle["zeros_tif"]["filename"],
        "zip_file": bundle["zeros_zip"]["filename"], "zip_sha256": bundle["zeros_zip"]["sha256"],
        "validator_output": {"canonical_13check": bundle["zeros_tif"], "independent_revalidation_zeros": val_zero,
                             "independent_revalidation_nan": val_nan},
        "projection": projection,
        "gates": gates,
        "submission_name": submission_name,
        "submission_note": note_final,
        "submission_note_chars": len(note_final),
        "download_instruction": "Upload the -zeros.tif (or its .zip) on the DrivenData New-submission page; paste submission_name as your tracking name and submission_note into the Note field.",
        "weekly_slots_used": 0,
        "verdict": verdict,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    rc = ROOT / "evidence" / "ap2_run_card.json"
    rc.write_text(json.dumps(card, indent=1))
    # keep the writer sidecar name consistent with final verdict note
    log(f"verdict={verdict} gates={gates}")
    log(f"final file {zeros_path.name} sha256={card['raster_sha256'][:16]}... dots={budget}")
    print(json.dumps({"verdict": verdict, "gates": gates, "file": zeros_path.name,
                      "sha256": card["raster_sha256"], "holdout_dti": cand_dti,
                      "champion_holdout_dti": champ_dti, "projection_interval": [proj_lo, proj_hi]}, indent=1))


if __name__ == "__main__":
    main()
