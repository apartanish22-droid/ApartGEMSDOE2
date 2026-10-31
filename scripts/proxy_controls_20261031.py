#!/usr/bin/env python3
"""Same-evaluator control run for the GEMSDOE32 best, GEMSDOE30 d2.8, and the GEMSDOE28 S31 files.

Every number is a HOLDOUT-DTI *proxy* produced by the repo's shared evaluators (gems32.holdout):
  * HOLDOUT-DTI (hide-and-recover) : evaluator GEMSDOE32-HIDE-RECOVER-v3.0, withheld USGS/INGENIOUS
    catalogue positives (n = 22,232). Catalogue recovery, NOT the organizer target. Known split defect
    (issue #60): 15,705 / 22,232 withheld positives lie within 15 px of visible faults.
  * SGMC-CAL (off-catalogue)        : evaluator GEMSDOE32-SGMC-CAL-v3.0, USGS SGMC faults > 300 m from
    the catalogue (n = 62,703 truth pixels). Prevalence-calibrated value is the number the repo quotes.
  * Random null                     : uniform random dots, same count as the candidate, 3 seeds.

None of these is a leaderboard estimate. Writes evidence/proxy_controls_20261031.json.
Requires the restored .cache/gems_data (labels, sample_submission) and the focus registry bytes.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import gate_candidates as gc  # noqa: E402
from gems32 import holdout  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "evidence" / "proxy_controls_20261031.json"

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
# Pinned zeros/allfinite copies (SHA-256 checked by restore_data.py); their in-footprint dot sets are
# identical to the user-named -nan files for the same site (evidence/nine_site_verification_20261031.json).
CANDIDATES = {site: DATA / "registry_focus" / f"{site}_best.tif" for site in FOCUS}
CANDIDATES["S31_far65 (GEMSDOE28 main, 31 Oct)"] = ROOT / ".cache/nine/s31_far65.tif"
CANDIDATES["S31_midband (GEMSDOE28 main, 31 Oct)"] = ROOT / ".cache/nine/s31_midband.tif"
NULL_SEEDS = (1000, 1001, 1002)


def main() -> int:
    ctx = holdout.load_holdout_context(DATA)
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    rows = {}
    for name, path in CANDIDATES.items():
        if not path.is_file():
            raise SystemExit(f"missing bytes: {path}")
        dots, _ = gc.read_candidate(path, foot)
        pb = gc.proxy_block(dots, ctx)
        sg = pb["SGMC-CAL_off_catalogue_proxy"]
        hr = pb["HOLDOUT-DTI_hide_recover"]
        rows[name] = {
            "file": str(path.relative_to(ROOT)),
            "dots": int(dots.sum()),
            "SGMC_CAL_prevalence_calibrated": sg["prevalence_calibrated_dti"],
            "SGMC_CAL_calibrated_ci95": sg["calibrated_ci95"],
            "SGMC_CAL_raw": sg["raw_dti"],
            "SGMC_CAL_truth_pixels": sg["n_truth_pixels"],
            "HOLDOUT_DTI_hide_recover_pooled": hr["pooled_dti"],
            "HOLDOUT_DTI_hide_recover_ci95": hr["ci95"],
            "HOLDOUT_DTI_withheld_positives": hr["n_withheld_positives"],
            "evaluators": {"hide_recover": hr["evaluator_version"], "sgmc": sg["evaluator_version"]},
        }
        print(name, rows[name]["dots"], round(sg["prevalence_calibrated_dti"], 4),
              round(hr["pooled_dti"], 4), flush=True)
    nulls = []
    for seed in NULL_SEEDS:
        nd = gc.null_dots(foot, ctx.labels, 37654, seed=seed)
        pb = gc.proxy_block(nd, ctx)
        nulls.append({
            "seed": seed,
            "dots": int(nd.sum()),
            "SGMC_CAL_prevalence_calibrated": pb["SGMC-CAL_off_catalogue_proxy"]["prevalence_calibrated_dti"],
            "HOLDOUT_DTI_hide_recover_pooled": pb["HOLDOUT-DTI_hide_recover"]["pooled_dti"],
        })
    out = {
        "schema": "proxy-controls-20261031-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "label": "HOLDOUT-DTI PROXY (not an organizer score; not a leaderboard estimate)",
        "candidates": rows,
        "random_null_37654_dots": nulls,
    }
    OUT.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
