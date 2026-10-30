#!/usr/bin/env python3
"""Single-feature leakage canary (protocol item 4): AUC of each training_features band vs catalogue
fault cells inside the footprint. AUC > 0.90 = leakage until disproved. Writes evidence/v4_feature_canary.json."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, rasterio
from sklearn.metrics import roc_auc_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ridge_candidate_v4 as rc
fp = rc.load_footprint(); truth = rc.load_labels()
rows = []
with rasterio.open(rc.DATA / "training_features.tif") as src:
    nodata = src.nodata
    for i in range(1, src.count + 1):
        a = src.read(i).astype(np.float64)
        bad = ~np.isfinite(a)
        if nodata is not None:
            bad |= a == nodata
        m = fp & ~bad
        y = truth[m].astype(int); v = a[m]
        auc = float(roc_auc_score(y, v)) if 0 < y.sum() < len(y) else float("nan")
        rows.append({"band": i, "name": src.descriptions[i - 1], "auc_one_sided": auc,
                     "auc_two_sided": max(auc, 1 - auc), "cells_used": int(m.sum())})
        print(rows[-1], flush=True)
mx = max(r["auc_two_sided"] for r in rows)
out = {"threshold": 0.90, "max_two_sided_auc": mx, "passes_canary": bool(mx <= 0.90), "features": rows,
       "note": "Univariate AUC only. Not a spatial test; lack of leakage is not proven by this check."}
(rc.ROOT / "evidence" / "v4_feature_canary.json").write_text(json.dumps(out, indent=2))
print("max two-sided AUC", mx, "PASS" if mx <= 0.90 else "FAIL")
