#!/usr/bin/env python3
"""Retired RAD-SCARP research runner; it cannot authorize another experiment.

The prior self-selected method (not an explicitly assigned lane) was:
  Off-catalogue geothermal fault detection using two overlooked, free, official
  data layers -- USGS GeoDAWN airborne radiometrics (K/Th/U/TC, DOI
  10.5066/P93LGLVQ) and USGS 3DEP 1 m LiDAR-derived scaper features -- placed
  in the 2-15 px (200 m - 1.5 km) off-catalogue collar around VISIBLE catalogue
  faults. The code below uses the full catalogue for its distance field. An
  unsupervised threshold does not establish leakage-free fold evaluation.
  The old whole-array [0,1] diagnostic did not establish portal acceptance.
  A read-only recheck finds 99.66% overlap with the pinned lattice, so the
  literal uniqueness rule fails. Do not generate or submit these artifacts.

Geological hypothesis: young, radiometrically altered fault strands that are
absent from the USGS/INGENIOUS catalogue (hence off-catalogue) but lie adjacent
to mapped range-front faults host geothermal conduits. Radiometric enrichment
marks hydrothermal alteration; LiDAR scarps mark young, surface-breaking
faulting. Neither layer is in the H19-5/GEM32-B2 magnetic-lineament lineage,
so the raster is expected to be byte-unique and geometrically distinct.

The prior run wrote research artifacts to docs/downloads/. This entry point is
retired because it lacks required pre-placement, fold-local and time gates.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import submission as gems32_submission  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

EXPECTED_SHAPE = (3730, 3292)
RAD_BANDS = (1, 2, 3, 4)        # GeoDAWN K/Th/U/TC (order not tagged -> symmetric mean)
LIDAR_BANDS = tuple(range(1, 13))  # 12 LiDAR scarp metrics (order not tagged -> symmetric max)
RAD_PCT = 99.0                  # radiometric anomaly threshold (top 1%, unsupervised)
SCARP_PCT = 99.0                # confident-scarp threshold (top 1% of nonzero, unsupervised)
COLLAR_LO_PX = 2.0              # 200 m: just outside masked catalogue line
COLLAR_HI_PX = 12.0             # 1.2 km: within kernel reach of hidden parallel strands
SLUG = "rad-scarp-offcatalogue-geothermal"
PREFIX = "apartgemsdoe2"
NOTE = "RAD-SCARP research only: radiometric+LiDAR, 200m-1.2km collar; failed literal novelty gate."
assert len(NOTE) <= 140, f"note {len(NOTE)} chars > 140"


def read_band(path: Path, band: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(band).astype(np.float32)
    a = np.where(foot & np.isfinite(a), a, 0.0)
    return a


def main() -> int:
    from experiment_guard import require_current_protocol
    if not require_current_protocol(expected_lane='RAD-SCARP'):
        return 1
    ddir = data_dir()
    sample_tif = ddir / "sample_submission.tif"
    labels_tif = ddir / "labels.tif"
    rad_tif = ddir / "external" / "geodawn_rad_u8.tif"
    lidar_tif = ddir / "external" / "lidar_scarp_features_u8.tif"

    with rasterio.open(sample_tif) as ds:
        foot = np.isfinite(ds.read(1)).astype(bool)
        transform, crs = ds.transform, ds.crs
    assert foot.shape == EXPECTED_SHAPE, foot.shape

    with rasterio.open(labels_tif) as ds:
        cat = (ds.read(1) > 0) & foot
    cat_dist = distance_transform_edt(~cat).astype(np.float32)  # px (100 m each)
    collar = (cat_dist >= COLLAR_LO_PX) & (cat_dist <= COLLAR_HI_PX) & foot & ~cat

    # Radiometric anomaly index: symmetric mean of the 4 GeoDAWN bands.
    rad_idx = np.zeros(foot.shape, dtype=np.float32)
    for b in RAD_BANDS:
        rad_idx += read_band(rad_tif, b, foot)
    rad_idx /= float(len(RAD_BANDS))
    rad_hi = rad_idx >= float(np.percentile(rad_idx[foot], RAD_PCT))

    # Young-scarp proxy: symmetric max of the 12 LiDAR bands, confident tier.
    scarp_max = np.zeros(foot.shape, dtype=np.float32)
    for b in LIDAR_BANDS:
        scarp_max = np.maximum(scarp_max, read_band(lidar_tif, b, foot))
    scarp_pos = scarp_max > 0
    scarp_hi = scarp_pos & (scarp_max >= float(np.percentile(scarp_max[scarp_pos], SCARP_PCT)))

    mask = foot & ~cat & collar & rad_hi & scarp_hi
    n_dots = int(mask.sum())
    print(f"footprint_px={int(foot.sum())} cat_px={int(cat.sum())}")
    print(f"collar_px={int(collar.sum())} rad_hi_px={int(rad_hi.sum())} scarp_hi_px={int(scarp_hi.sum())}")
    print(f"emitted_dots={n_dots}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate_meta = {
        "candidate_id": f"{PREFIX}-{SLUG}-{ts}",
        "description": "RAD-SCARP research dots; full-catalogue-derived collar, not a validated fold-local holdout",
        "submission_note_zeros": NOTE,
        "submission_note_nan": NOTE,
        "catalogue_hidden_mean": 0.0,
        "catalogue_hidden_per_quadrant": {},
        "sgmc_prevalence_calibrated_dti": 0.0,
        "drift_corrected_holdout_mean": 0.0,
        "drift_corrected_per_quadrant": {},
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "HOLD-PENDING-HOLDOUT",
    }
    bundle = gems32_submission.write_submission_pair(
        mask=mask,
        foot=foot,
        labels=cat,
        template_tif=sample_tif,
        out_dir=ROOT / "docs" / "downloads",
        slug=SLUG,
        timestamp_tag=ts,
        candidate_meta=candidate_meta,
        prefix=PREFIX,
    )
    print(json.dumps(bundle, indent=2)[:4000])
    # Persist the boolean mask + receipt for the holdout step.
    npy = ROOT / "docs" / "downloads" / f"{PREFIX}-{SLUG}-{ts}-mask.npy"
    np.save(npy, mask.astype(np.uint8))
    receipt = {
        "candidate_id": candidate_meta["candidate_id"],
        "slug": SLUG,
        "prefix": PREFIX,
        "method": "RAD-SCARP off-catalogue geothermal fault dots",
        "timestamp_utc": ts,
        "grid": {"epsg": 32611, "shape": list(EXPECTED_SHAPE),
                 "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]},
        "emitted_dots": n_dots,
        "collar_lo_px": COLLAR_LO_PX,
        "collar_hi_px": COLLAR_HI_PX,
        "rad_pct": RAD_PCT,
        "scarp_pct": SCARP_PCT,
        "zeros_tif": bundle["zeros_tif"]["filename"],
        "nan_tif": bundle["nan_tif"]["filename"],
        "zeros_sha256": bundle["zeros_tif"]["sha256"],
        "nan_sha256": bundle["nan_tif"]["sha256"],
        "note": NOTE,
    }
    (ROOT / "docs" / "downloads" / f"{PREFIX}-{SLUG}-{ts}-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(f"WROTE {npy.name} and receipt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
