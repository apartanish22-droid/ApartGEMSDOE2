#!/usr/bin/env python3
"""Pairwise 3-px dot overlap (directed) and Spearman among the nine focus-site rasters
and the v4 candidate. Writes evidence/focus9_pairwise_v4.json."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ridge_candidate_v4 as rc
ROOT = rc.ROOT
SITES = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
fp = rc.load_footprint()
arrs, dots = {}, {}
for s in SITES:
    with rasterio.open(rc.DATA / "registry_focus" / f"{s}_best.tif") as src:
        a = np.nan_to_num(src.read(1).astype(np.float32))
    arrs[s] = a
    dots[s] = (a > 0) & fp
with rasterio.open(ROOT / "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif") as src:
    cand = src.read(1)
arrs["V4_CANDIDATE"] = np.nan_to_num(cand, nan=0.0)
dots["V4_CANDIDATE"] = (arrs["V4_CANDIDATE"] > 0) & fp
names = SITES + ["V4_CANDIDATE"]
dist = {n: ndi.distance_transform_edt(~dots[n]) for n in names}
rng = np.random.default_rng(7)
idx = rng.choice(np.flatnonzero(fp.ravel()), size=300000, replace=False)
samp = {n: arrs[n].ravel()[idx].astype(np.float64) for n in names}
matrix = {}
for a in names:
    for b in names:
        if a == b:
            continue
        frac = float((dist[b][dots[a]] <= 3.0).mean())  # fraction of a's dots within 3 px of b's dots
        rho = float(spearmanr(samp[a], samp[b]).statistic)
        matrix[f"{a}->{b}"] = {"dots_within_3px": round(frac, 5), "spearman": round(rho, 5)}
    print(a, "done", flush=True)
focus_pairs = {k: v for k, v in matrix.items() if k.split("->")[0] != "V4_CANDIDATE" and k.split("->")[1] != "V4_CANDIDATE"}
out = {
    "dots": {n: int(dots[n].sum()) for n in names},
    "pairs": matrix,
    "max_focus_pair_overlap": max(v["dots_within_3px"] for v in focus_pairs.values()),
    "max_v4_overlap_vs_focus": max(v["dots_within_3px"] for k, v in matrix.items() if k.startswith("V4_CANDIDATE->")),
    "max_v4_abs_spearman_vs_focus": max(abs(v["spearman"]) for k, v in matrix.items() if k.startswith("V4_CANDIDATE->")),
    "note": "Focus rasters are the owner-mirrored *_best.tif registry files; overlap uses the saved dots (>0) within the footprint.",
}
(ROOT / "evidence/focus9_pairwise_v4.json").write_text(json.dumps(out, indent=2))
print(json.dumps({k: out[k] for k in out if k not in ('pairs',)}, indent=2))
