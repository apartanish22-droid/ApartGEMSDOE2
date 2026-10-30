#!/usr/bin/env python3
"""Single-feature leakage canary (protocol item 4): AUC of each feature alone vs holdout truth.

Truth for the canary is the off-catalogue USGS SGMC set (pixels > 300 m from the catalogue,
the same truth used by the SGMC-CAL-v3.0 proxy). A feature whose oriented AUC exceeds 0.90 is
treated as leakage until disproved. The canary does not rank features for the candidate, so it
does not tune anything on the proxy.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

SEED = 20261030
N_NEG = 300_000


def main() -> int:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    foot = ctx.foot
    pos_mask = ctx.sgmc_off & foot & ~ctx.labels
    neg_pool = foot & ~ctx.labels & ~ctx.sgmc_off
    rng = np.random.default_rng(SEED)
    pos_idx = np.flatnonzero(pos_mask.ravel())
    neg_idx = rng.choice(np.flatnonzero(neg_pool.ravel()), size=N_NEG, replace=False)
    idx = np.concatenate([pos_idx, neg_idx])
    y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
    # Second truth set (selection-free w.r.t. SGMC): the hide-and-recover withheld catalogue cells.
    hr_truth = np.zeros(foot.shape, dtype=bool)
    for cell in ctx.cells:
        ty, tx = cell.truth_coords
        r0, c0 = int(cell.bbox[0].start), int(cell.bbox[1].start)
        hr_truth[ty + r0, tx + c0] = True
    hr_truth &= foot
    hr_bg = foot & ~ctx.labels & ~hr_truth
    hr_pos_idx = np.flatnonzero(hr_truth.ravel())
    hr_neg_idx = rng.choice(np.flatnonzero(hr_bg.ravel()), size=N_NEG, replace=False)
    hr_idx = np.concatenate([hr_pos_idx, hr_neg_idx])
    hr_y = np.concatenate([np.ones(hr_pos_idx.size, np.int8), np.zeros(hr_neg_idx.size, np.int8)])
    rows = []
    hr_rows = []
    with rasterio.open(ddir / "training_features.tif") as ds:
        for b in range(1, ds.count + 1):
            a = ds.read(b).ravel().astype(np.float64)
            v = a[idx]
            ok = np.isfinite(v) & (v > -1e30)
            auc = float(roc_auc_score(y[ok], v[ok]))
            name = (ds.descriptions[b - 1] or f"band{b}").split(" - ")[0]
            rows.append({"band": b, "name": name, "auc_raw": auc, "auc_oriented": max(auc, 1 - auc),
                         "direction": "higher=truth" if auc >= 0.5 else "lower=truth",
                         "leakage_flag": bool(max(auc, 1 - auc) > 0.90), "n_valid": int(ok.sum())})
            hv = a[hr_idx]
            hok = np.isfinite(hv) & (hv > -1e30)
            hauc = float(roc_auc_score(hr_y[hok], hv[hok]))
            hr_rows.append({"band": b, "name": name, "auc_raw": hauc, "auc_oriented": max(hauc, 1 - hauc),
                            "direction": "higher=truth" if hauc >= 0.5 else "lower=truth",
                            "leakage_flag": bool(max(hauc, 1 - hauc) > 0.90), "n_valid": int(hok.sum())})
    prob_path = ROOT / ".cache" / "work" / "catlogit" / "catlogit_prob_footprint.npy"
    if prob_path.exists():
        p = np.load(prob_path)
        fo = foot[foot]  # footprint-flattened order
        sgmc_flat = pos_mask[foot]
        neg_flat = neg_pool[foot]
        sel = np.flatnonzero(sgmc_flat | neg_flat)
        yy = sgmc_flat[sel].astype(np.int8)
        auc = float(roc_auc_score(yy, p[sel]))
        rows.append({"band": None, "name": "H-CATLOGIT-OOF surface (out-of-fold, catalogue-trained)",
                     "auc_raw": auc, "auc_oriented": max(auc, 1 - auc), "direction": "higher=truth",
                     "leakage_flag": False, "note": "candidate surface; uses catalogue labels only, not SGMC"})
    out = {"schema": "apartgems-feature-canary-v2",
           "hide_recover_truth_px": int(hr_pos_idx.size),
           "hide_recover_canary": hr_rows,
           "hide_recover_any_leakage_flag": any(r["leakage_flag"] for r in hr_rows),
           "checked_utc": datetime.now(timezone.utc).isoformat(),
           "truth": "off-catalogue SGMC pixels (>300 m from catalogue)",
           "n_truth_px": int(pos_idx.size), "n_background_px": int(neg_idx.size),
           "threshold": 0.90, "any_leakage_flag": any(r["leakage_flag"] for r in rows),
           "features": rows}
    path = ROOT / "evidence" / "feature_canary_sgmc_20261030.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    for r in sorted(rows, key=lambda r: -r["auc_oriented"]):
        print(f"SGMC {r['auc_oriented']:.4f}  {r['name']}  {r['direction']}")
    for r in sorted(hr_rows, key=lambda r: -r["auc_oriented"]):
        print(f"HR   {r['auc_oriented']:.4f}  {r['name']}  {r['direction']}")
    print("any leakage flag:", out["any_leakage_flag"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
