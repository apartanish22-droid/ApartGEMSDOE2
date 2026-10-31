#!/usr/bin/env python3
"""Pairwise uniqueness among the nine GEMSDOE focus submissions (plus the 13GEMSDOE lattice).

Uses the same definitions as scripts/focus_registry_uniqueness.py: dots are finite and > 0 over the raster;
overlap = share of dots of row file within 3 px of column file's dots; corr = Pearson over the footprint.
Output: evidence/focus9_pairwise_20261031.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from focus_registry_uniqueness import footprint_vector, RADIUS  # noqa: E402

SRC = ROOT / ".cache/gems_data/registry_focus"
OUT = ROOT / "evidence/focus9_pairwise_20261031.json"
SITES = ["24", "25", "27", "28", "30", "31", "32", "33", "36"]


def load(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float32)
    fin = np.isfinite(a)
    dots = fin & (a > 0)
    foot = fin  # footprint = finite cells, matching the sample's NaN-outside grid
    return a, dots, foot


def main() -> int:
    data = {}
    for s in SITES:
        p = SRC / f"GEMSDOE{s}_best.tif"
        a, dots, foot = load(p)
        data[s] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "dots": dots, "idx": np.flatnonzero(dots.ravel()),
                   "foot": foot, "a": a}
    foot_all = np.zeros_like(data[SITES[0]]["foot"])
    for s in SITES:
        foot_all |= data[s]["foot"]
    foot_idx = np.flatnonzero(foot_all.ravel())
    vec = {s: footprint_vector(np.where(data[s]["foot"], data[s]["a"], 0.0), foot_idx) for s in SITES}
    near = {}
    for s in SITES:
        dt = distance_transform_edt(~data[s]["dots"])
        near[s] = dt <= RADIUS
        del dt
    rows = {}
    for i in SITES:
        for j in SITES:
            if i == j:
                continue
            ni = data[i]["idx"].size
            ov = float(near[j].ravel()[data[i]["idx"]].sum()) / ni
            rows[f"{i}->{j}"] = {"overlap_within_3px": round(ov, 6)}
    corr = {}
    for i in SITES:
        for j in SITES:
            if j <= i:
                continue
            corr[f"{i}~{j}"] = round(float(np.dot(vec[i], vec[j])), 6)
    exact = {}
    for i in SITES:
        for j in SITES:
            if j <= i:
                continue
            same = data[i]["sha256"] == data[j]["sha256"]
            dotset = data[i]["idx"].size == data[j]["idx"].size and np.array_equal(data[i]["idx"], data[j]["idx"])
            if same or dotset:
                exact[f"{i}={j}"] = {"same_bytes": same, "same_dot_set": bool(dotset)}
    report = {
        "schema": "focus9-pairwise-v1",
        "definition": "dots: finite and > 0; overlap: share of row dots within 3 px of column dots; corr: Pearson over finite cells",
        "sites": {s: {"sha256": data[s]["sha256"], "dots": int(data[s]["idx"].size)} for s in SITES},
        "overlap_rows_to_cols": rows,
        "pearson_pairs": corr,
        "exact_duplicates": exact,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"exact": exact, "corr_min": min(corr.values()), "corr_max": max(corr.values())}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
