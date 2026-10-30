#!/usr/bin/env python3
"""Run every gate on saved GeoTIFF bytes (format, holdout proxies, null baseline, registry).

Gates (all literal; nothing is exempted silently):
  G1 format   : repo 12-point checker ``gems32.submission.audit_geotiff`` (grid, float32, finite
                and [0,1] inside footprint, outside-footprint convention, zero catalogue dots).
  G2 proxies  : HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0; catalogue recovery, NOT the organizer
                target) and SGMC-CAL-v3.0 (off-catalogue USGS SGMC faults, closest local proxy
                for new faults). Both report 95% cluster-bootstrap CIs. Compared with a random
                dot null of the same size.
  G3 registry : literal full-footprint |Spearman| <= 0.90 and candidate dots within 3 px of any
                registry raster <= 70%, against the focus registry (9 sites) + 13GEMSDOE lattice.
                Malformed registry rasters are counted, not hidden.

Verdicts are written as evidence; this script never authorizes an upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402
from gems32.registry_audit import audit_final_dots, load_manifest  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402

LATTICE_LOCAL = ".cache/gems_data/registry_focus/LATTICE_r13.tif"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"


def manifest_with_lattice(manifest_path: Path) -> dict:
    man = load_manifest(manifest_path)
    entries = list(man["rasters"])
    entries.append({
        "repo": "buffedlizard55-lab/13GEMSDOE",
        "ref": "92ee6f074323f161eed837b80ec3ee5b662e26f5",
        "path": "docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        "sha256": LATTICE_SHA,
        "local": LATTICE_LOCAL,
        "status": "ok",
    })
    return {**man, "rasters": entries}


def read_candidate(path: Path, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(path) as ds:
        arr = ds.read(1)
    dots = np.isfinite(arr) & (arr > 0) & foot
    surface = np.where(foot, np.nan_to_num(arr, nan=0.0), 0.0).astype(np.float32)
    return dots, surface


def null_dots(foot: np.ndarray, labels: np.ndarray, n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pool = np.flatnonzero((foot & ~labels).ravel())
    pick = rng.choice(pool, size=n, replace=False)
    out = np.zeros(foot.size, dtype=bool)
    out[pick] = True
    return out.reshape(foot.shape)


def proxy_block(mask: np.ndarray, ctx) -> dict:
    hr = holdout.evaluate_hide_and_recover(mask, ctx, name="candidate")
    sg = holdout.evaluate_sgmc_with_ci(mask, ctx, name="candidate")
    return {
        "HOLDOUT-DTI_hide_recover": {
            "evaluator_version": hr["evaluator_version"],
            "score_label": "HOLDOUT-DTI",
            "target": "withheld USGS/INGENIOUS catalogue segments (NOT the organizer target)",
            "pooled_dti": hr["pooled_dti"],
            "ci95": hr["ci95_cluster_bootstrap"],
            "n_withheld_positives": hr["n_withheld_positives"],
            "known_split_defect": "Withheld segments are only quadrant-collared (issue #60): 15,705/22,232 lie within 15 px of visible faults",
        },
        "SGMC-CAL_off_catalogue_proxy": {
            "evaluator_version": holdout.SGMC_EVALUATOR_VERSION,
            "score_label": "HOLDOUT-DTI (proxy)",
            "target": "USGS SGMC faults more than 300 m from the catalogue; closest local proxy for new faults, not the organizer truth",
            "raw_dti": sg["sgmc_raw_pooled_dti"],
            "raw_ci95": sg["sgmc_raw_ci95"],
            "prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
            "calibrated_ci95": sg["sgmc_calibrated_ci95"],
            "n_truth_pixels": sg["n_withheld_positives"],
        },
    }


def registry_block(surface: np.ndarray, dots: np.ndarray, foot: np.ndarray, man: dict,
                   exclude_sha: str | None = None) -> dict:
    # A candidate that is itself pinned in the registry must not be compared with its own copy.
    if exclude_sha:
        kept = [e for e in man["rasters"] if e.get("sha256") != exclude_sha]
        man = {**man, "rasters": kept}
    res = audit_final_dots(surface, dots, foot, man, root=ROOT, template_tif=ROOT / ".cache" / "gems_data" / "sample_submission.tif")
    top = sorted((r for r in res["comparisons"] if r.get("within_3px_fraction") is not None),
                 key=lambda r: -r["within_3px_fraction"])[:5]
    return {
        "literal_rule_passed": res["literal_rule_passed"],
        "no_exemption_duplicates_empty": res["passed"],
        # Space-filling = registry 3-px footprint coverage >= 0.70 (the lattice). Not exempted from the
        # literal rule above; reported separately so the non-lattice uniqueness margin is visible.
        "worst_within_3px_excluding_space_filling": max(
            (r["within_3px_fraction"] for r in res["comparisons"]
             if r.get("within_3px_fraction") is not None and (r.get("footprint_coverage_3px") or 0.0) < 0.70),
            default=None),
        "worst_within_3px_excluding_space_filling_raster": max(
            ((r["within_3px_fraction"], f"{r.get('repo')}:{r.get('path')}") for r in res["comparisons"]
             if r.get("within_3px_fraction") is not None and (r.get("footprint_coverage_3px") or 0.0) < 0.70),
            default=(None, None))[1],
        "rule": res["rule"],
        "registry_rasters": res["registry_rasters"],
        "malformed_or_missing": res["malformed_or_missing"],
        "constant_or_empty": res["constant_or_empty"],
        "worst_abs_spearman": res["worst_abs_spearman"],
        "worst_spearman_raster": res["worst_spearman_raster"],
        "worst_within_3px_fraction": res["worst_within_3px_fraction"],
        "worst_overlap_raster": res["worst_overlap_raster"],
        "top5_overlap": [{"repo": r["repo"], "path": r["path"], "within_3px": r["within_3px_fraction"],
                          "footprint_coverage_3px": r.get("footprint_coverage_3px"), "spearman": r.get("spearman")} for r in top],
        "literal_duplicates": res["literal_duplicates"],
    }


def run(candidates: list[tuple[str, Path]], out: Path, manifest_path: Path, n_null_seeds: int) -> dict:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template = ds.profile
    labels = ctx.labels
    man = manifest_with_lattice(manifest_path)
    report = {"schema": "apartgems-gate-run-v1", "checked_utc": datetime.now(timezone.utc).isoformat(),
              "manifest": str(manifest_path.relative_to(ROOT)), "manifest_rasters": len(man["rasters"]),
              "lane_note": "Uniqueness scope = focus registry + 13GEMSDOE lattice only; other listed repos not fetched in this run.",
              "candidates": {}}
    for name, path in candidates:
        print(f"[gate] {name}: {path}", flush=True)
        dots, surface = read_candidate(path, foot)
        mode = "nan" if "-nan" in path.name else "zeros"
        fmt = audit_geotiff(path, foot, labels, mode=mode, template_tif=ddir / "sample_submission.tif")
        n = int(dots.sum())
        nulls = []
        for s in range(n_null_seeds):
            nd = null_dots(foot, labels, n, seed=1000 + s)
            nulls.append(proxy_block(nd, ctx))
        sgmc_null = [x["SGMC-CAL_off_catalogue_proxy"]["raw_dti"] for x in nulls]
        hr_null = [x["HOLDOUT-DTI_hide_recover"]["pooled_dti"] for x in nulls]
        proxies = proxy_block(dots, ctx)
        reg = registry_block(surface, dots, foot, man, exclude_sha=fmt["sha256"])
        report["candidates"][name] = {
            "file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "sha256": fmt["sha256"],
            "bytes": fmt["size_bytes"],
            "mode": mode,
            "dots": n,
            "G1_format": {"all_checks_passed": fmt["all_checks_passed"], "checks": fmt["checks"],
                          "in_footprint_min": fmt["in_footprint_min"], "in_footprint_max": fmt["in_footprint_max"],
                          "on_catalogue_positive_pixels": fmt["on_catalogue_positive_pixels"]},
            "G2_proxies": proxies,
            "G2_random_null_same_n": {"seeds": n_null_seeds, "SGMC_raw_dti_values": sgmc_null,
                                      "HOLDOUT_hide_recover_values": hr_null},
            "G3_registry": reg,
            "G3_self_excluded_sha": fmt["sha256"],
        }
        report["candidates"][name]["_dots_digest"] = hashlib.sha256(np.packbits(dots)).hexdigest()
    report["checked_utc"] = datetime.now(timezone.utc).isoformat()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=float) + "\n")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("candidate", nargs="+", help="NAME=PATH pairs")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=ROOT / "registry" / "focus_registry_manifest.json")
    ap.add_argument("--null-seeds", type=int, default=3)
    args = ap.parse_args()
    cands = []
    for item in args.candidate:
        name, _, p = item.partition("=")
        cands.append((name, Path(p)))
    rep = run(cands, args.out, args.manifest, args.null_seeds)
    print(json.dumps({k: {"dots": v["dots"], "G1": v["G1_format"]["all_checks_passed"],
                          "G3_literal_pass": v["G3_registry"]["literal_rule_passed"],
                          "G3_worst_overlap": v["G3_registry"]["worst_within_3px_fraction"],
                          "G3_worst_rho": v["G3_registry"]["worst_abs_spearman"]} for k, v in rep["candidates"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
