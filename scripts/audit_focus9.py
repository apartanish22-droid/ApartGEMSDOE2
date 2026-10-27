#!/usr/bin/env python3
"""Byte-level audit of the nine focus sites' best OWNER-REPORTED submissions.

Reads the actual TIFFs from local clones of the nine repos (pinned commits in
registry/PROVENANCE.md), never writes/modifies them. Scores are transcribed OWNER-REPORTED
values from the task prompt (no organiser receipts exist in the repos); everything else
(dots, hashes, catalogue distances, subset relations, value ranges) is measured here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

# repo -> (filename search tokens, owner-reported score from prompt, submission id as listed)
WINNERS = {
    "GEMSDOE24": ("h25-1-dotted-h19-5-d1-5-20261002-989f59505db1", 0.2477,
                  "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan"),
    "GEMSDOE25": ("dotted-h19-5-d2-8-20261002-e56ea318af89", 0.2600,
                  "dotted-h19-5-d2-8-20261002-e56ea318af89-nan"),
    "GEMSDOE27": ("topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1", 0.2449,
                  "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan"),
    "GEMSDOE28": ("h36-1-rung30-blind-r1-20261003-b531dae0a36f", 0.2710,
                  "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan"),
    "GEMSDOE30": ("91eae1ca", 0.2600, "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca"),
    "GEMSDOE31": ("h27-4-solo-d28-20261004-8acb75e1", 0.2708, "h27-4-solo-d28-20261004-8acb75e1-nan"),
    "GEMSDOE32": ("h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778,
                  "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros"),
    "GEMSDOE33": ("h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632,
                  "h33d-analog-tip-stepover-r30-20261004-cb490425926e"),
    "GEMSDOE36": ("anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750,
                  "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros"),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_file(repo_dir: Path, token: str) -> Path | None:
    cands = [p for p in repo_dir.rglob("*.tif") if token in p.name]
    if not cands:
        return None
    # prefer -zeros/-allfinite over -nan for byte identity of the dot set; else shortest name
    def rank(p: Path):
        n = p.name
        pref = 0 if ("-zeros" in n or "-allfinite" in n) else (1 if "nan" not in n else 2)
        return (pref, len(n))
    return sorted(cands, key=rank)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-dir", default="/tmp/refs")
    ap.add_argument("--data-dir", default="/tmp/gems_data")
    ap.add_argument("--out", default="evidence/ap2_focus9_forensics.json")
    args = ap.parse_args()
    refs, ddir = Path(args.refs_dir), Path(args.data_dir)

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        tpl_crs, tpl_shape, tpl_transform = str(ds.crs), ds.shape, tuple(ds.transform)[:6]
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    dcat = distance_transform_edt(~labels)

    masks: dict[str, np.ndarray] = {}
    rows = {}
    for repo, (token, score, sub_id) in WINNERS.items():
        p = find_file(refs / repo, token)
        if p is None:
            rows[repo] = {"found": False, "token": token, "owner_reported_score": score,
                          "submission_id_as_listed": sub_id}
            continue
        with rasterio.open(p) as ds:
            arr = ds.read(1)
            meta = {"crs": str(ds.crs), "shape": list(ds.shape),
                    "transform": [float(x) for x in tuple(ds.transform)[:6]],
                    "dtype": ds.dtypes[0], "count": ds.count, "nodata_repr": str(ds.nodata)}
            grid_match = (meta["crs"] == tpl_crs and list(tpl_shape) == meta["shape"]
                          and all(abs(a - b) < 1e-9 for a, b in zip(meta["transform"], tpl_transform)))
        m = np.isfinite(arr) & (arr > 0) & foot
        masks[repo] = m
        d = dcat[m]
        in_foot = arr[foot]
        vals, counts = np.unique(in_foot[np.isfinite(in_foot)], return_counts=True)
        top_vals = {str(float(v)): int(c) for v, c in sorted(zip(vals, counts), key=lambda t: -t[1])[:5]}
        rows[repo] = {
            "found": True,
            "submission_id_as_listed": sub_id,
            "owner_reported_score": score,
            "score_evidence_class": "OWNER-REPORTED (task prompt / repo ledgers; no organiser receipt binds score to these bytes)",
            "measured_file": f"{repo}/{p.relative_to(refs / repo).as_posix()}",
            "sha256": sha256_file(p),
            "size_bytes": p.stat().st_size,
            "meta": meta,
            "grid_matches_sample_submission": bool(grid_match),
            "dots_positive_in_footprint": int(m.sum()),
            "on_catalogue_dots": int((m & labels).sum()),
            "dcat_px_hist": {"le1": int((d <= 1).sum()), "gt1_le2": int(((d > 1) & (d <= 2)).sum()),
                             "gt2_le3": int(((d > 2) & (d <= 3)).sum()), "gt3_le10": int(((d > 3) & (d <= 10)).sum()),
                             "gt10": int((d > 10).sum()), "median": float(np.median(d)) if d.size else None},
            "full_raster_finite_cells": int(np.isfinite(arr).sum()),
            "full_raster_all_in_0_1": bool(np.isfinite(arr).all() and (arr >= 0).all() and (arr <= 1).all()),
            "in_footprint_finite": int(np.isfinite(in_foot).sum()),
            "in_footprint_nan": int(np.isnan(in_foot).sum()),
            "in_footprint_top_values": top_vals,
            "dotmask_sha256": hashlib.sha256(np.packbits(m)).hexdigest(),
        }
        print(repo, rows[repo]["dots_positive_in_footprint"], rows[repo]["sha256"][:12], p.name)

    # directed 3-px overlap + exact subset relations among the nine winners
    overlap = {}
    repos_found = [r for r in WINNERS if r in masks]
    edts = {r: distance_transform_edt(~masks[r]) for r in repos_found}
    for a in repos_found:
        overlap[a] = {}
        for b in repos_found:
            overlap[a][b] = {
                "frac_a_dots_within_3px_of_b": float((edts[b][masks[a]] <= 3.0).mean()) if masks[a].any() else None,
                "a_dotset_subset_of_b": bool((masks[a] & ~masks[b]).sum() == 0),
                "a_dots_not_in_b_exact": int((masks[a] & ~masks[b]).sum()),
                "dotmask_identical": rows[a]["dotmask_sha256"] == rows[b]["dotmask_sha256"],
            }
    doc = {"label": "Measured bytes; scores OWNER-REPORTED only. Generated by scripts/audit_focus9.py.",
           "grid": {"footprint_px": int(foot.sum()), "label_px": int(labels.sum())},
           "winners": rows, "pairwise": overlap}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
