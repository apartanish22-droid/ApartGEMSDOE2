#!/usr/bin/env python3
"""Uniqueness gate against the FULL pinned focus registry (489 rasters) plus the 13GEMSDOE lattice.

Protocol checks (PARALLEL-RUN PROTOCOL, rule 1, thresholds as written by the user):
  * rank-correlation with any registry raster > 0.90 => duplicate (computed as Pearson correlation of
    the binary/float fields over the footprint; for binary fields this equals the phi coefficient);
  * more than 70% of the candidate's dots within 3 px of one registry raster's dots => duplicate.
Also reported (not part of the gate): the reverse direction (registry dots within 3 px of the candidate),
exact byte-level duplicates (SHA-256) and exact dot-set duplicates.

Dots = finite and > 0 over the whole raster (outside-footprint dots count, as the registry scoring
treats them). The candidate's own bytes are excluded from the comparison by SHA-256.

    python scripts/focus_registry_uniqueness.py docs/downloads/<candidate>.tif [...] --out evidence/x.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "focus_registry_manifest.json"
FOCUS_DIR = ROOT / ".cache" / "gems_data" / "registry_focus"
LATTICE = FOCUS_DIR / "LATTICE_r13.tif"
OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
RADIUS = 3.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def raster_shape(path: Path) -> tuple:
    with rasterio.open(path) as ds:
        return (ds.height, ds.width)


def load_dots_and_field(path: Path, foot: np.ndarray):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float32)
    fin = np.isfinite(a)
    dots = fin & (a > 0)
    field = np.where(foot & fin, a, 0.0).astype(np.float32)
    return dots, field


def footprint_vector(field: np.ndarray, foot_flat_idx: np.ndarray) -> np.ndarray:
    """Centred, unit-norm float64 vector over the footprint; Pearson r is then a dot product."""
    v = field.ravel()[foot_flat_idx].astype(np.float64)
    v -= v.mean()
    n = np.sqrt((v * v).sum())
    return v / n if n > 0 else v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(REG.read_text())
    foot = np.isfinite(rasterio.open(ROOT / ".cache/gems_data/sample_submission.tif").read(1))
    foot_idx = np.flatnonzero(foot.ravel())
    reg_rows = []
    for e in manifest["rasters"]:
        p = ROOT / e["local"]
        reg_rows.append({"label": f"{e['repo']}:{e['path']}", "path": p, "sha256": e["sha256"]})
    reg_rows.append({"label": "13GEMSDOE:" + "docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
                     "path": LATTICE, "sha256": sha256(LATTICE)})

    queries = []
    for c in args.candidates:
        queries.append({"label": f"CANDIDATE {c.name}", "path": c, "sha256": sha256(c), "kind": "candidate"})
    for p in sorted(FOCUS_DIR.glob("GEMSDOE*_best.tif")):
        queries.append({"label": f"FOCUS {p.stem.replace('_best','')}", "path": p, "sha256": sha256(p), "kind": "focus"})

    # Precompute dots, fields and distance transforms for every query.
    qdata = {}
    for q in queries:
        dots, field = load_dots_and_field(q["path"], foot)
        dt = distance_transform_edt(~dots)
        qdata[q["label"]] = {"dots": None, "near": dt <= RADIUS,  # bool, memory-light
                             "n": int(dots.sum()), "idx": np.flatnonzero(dots.ravel()),
                             "vec": footprint_vector(field, foot_idx)}
        del dt, field

    results = {q["label"]: {"sha256": q["sha256"], "dots": qdata[q["label"]]["n"], "kind": q["kind"],
                            "max_overlap_cand_to_registry": -1.0, "argmax": None,
                            "max_overlap_registry_to_cand": -1.0,
                            "max_abs_corr": -1.0, "argmax_corr": None,
                            "n_registry_over_70pct": 0, "n_registry_corr_over_0_90": 0,
                            "exact_sha_duplicates": [], "exact_dotset_duplicates": [],
                            "registry_over_70pct_examples": []} for q in queries}

    n_compared = 0
    skipped_shape: list = []
    for r in reg_rows:
        if raster_shape(r["path"]) != foot.shape:
            skipped_shape.append({"label": r["label"], "shape": list(raster_shape(r["path"]))})
            continue
        rd, rf = load_dots_and_field(r["path"], foot)
        rdt = distance_transform_edt(~rd)
        r_idx = np.flatnonzero(rd.ravel())
        del rd
        r_n = int(r_idx.size)
        r_vec = footprint_vector(rf, foot_idx)
        for q in queries:
            qd = qdata[q["label"]]
            res = results[q["label"]]
            if r["sha256"] == q["sha256"]:
                res["exact_sha_duplicates"].append(r["label"])
                continue
            if qd["n"] == r_n and np.array_equal(r_idx, qd["idx"]):
                res["exact_dotset_duplicates"].append(r["label"])
            if qd["n"] == 0 or r_n == 0:
                continue
            ov = float((rdt.ravel()[qd["idx"]] <= RADIUS).sum()) / qd["n"]
            rev = float(qd["near"].ravel()[r_idx].sum()) / r_n
            if ov > res["max_overlap_cand_to_registry"]:
                res["max_overlap_cand_to_registry"] = ov
                res["argmax"] = r["label"]
            if rev > res["max_overlap_registry_to_cand"]:
                res["max_overlap_registry_to_cand"] = rev
            if ov > OVERLAP_LIMIT:
                res["n_registry_over_70pct"] += 1
                if len(res["registry_over_70pct_examples"]) < 5:
                    res["registry_over_70pct_examples"].append({"registry": r["label"], "overlap": round(ov, 5)})
            rho = float(np.dot(qd["vec"], r_vec))
            if abs(rho) > res["max_abs_corr"]:
                res["max_abs_corr"] = abs(rho)
                res["argmax_corr"] = r["label"]
            if abs(rho) > RHO_LIMIT:
                res["n_registry_corr_over_0_90"] += 1
        n_compared += 1
        if n_compared % 50 == 0:
            print(f"progress {n_compared}/{len(reg_rows)}", flush=True)

    for label, res in results.items():
        res["gate_pass_overlap"] = res["max_overlap_cand_to_registry"] <= OVERLAP_LIMIT
        res["gate_pass_corr"] = res["max_abs_corr"] <= RHO_LIMIT
        res["gate_pass_exact_duplicate"] = not res["exact_sha_duplicates"] and not res["exact_dotset_duplicates"]
        res["unique_under_protocol"] = bool(res["gate_pass_overlap"] and res["gate_pass_corr"]
                                            and res["gate_pass_exact_duplicate"])
        for k in ("max_overlap_cand_to_registry", "max_overlap_registry_to_cand", "max_abs_corr"):
            res[k] = round(res[k], 6)

    report = {
        "schema": "focus-registry-uniqueness-v1",
        "registry_manifest": str(REG.relative_to(ROOT)),
        "registry_rasters_compared": n_compared,
        "registry_rasters_skipped_grid_mismatch": skipped_shape,
        "footprint_shape": list(foot.shape),
        "includes_lattice": True,
        "thresholds": {"overlap_within_3px_max": OVERLAP_LIMIT, "abs_corr_max": RHO_LIMIT, "radius_px": RADIUS},
        "dot_definition": "finite and > 0 over the whole raster",
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    for label, res in results.items():
        if res["kind"] == "candidate":
            print(label, json.dumps({k: res[k] for k in ("dots", "max_overlap_cand_to_registry", "argmax",
                                                          "max_abs_corr", "argmax_corr", "n_registry_over_70pct",
                                                          "exact_sha_duplicates", "exact_dotset_duplicates",
                                                          "unique_under_protocol")}, indent=1))
    print(f"compared {n_compared} registry rasters; wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
