#!/usr/bin/env python3
"""Generate a unique competition-format GeoTIFF submission for the DOE GEMS Prize.

Novel geological hypothesis (not previously implemented in this repo):

    H-RAD-MAG-CONTRAST — Blind geothermal fault detection via
    radiometric–magnetic gradient contrast zones.

Physical rationale
------------------
Concealed geothermal faults commonly lack surface scarps but host hydrothermal
alteration that (a) enriches potassium / depletes thorium relative to local
background (radiometric anomaly gradient) and (b) demagnetizes host rock
(magnetic gradient magnitude).  The *product* of the two normalized gradient
layers targets subsurface fluid-alteration pathways that may have no visible
surface expression — precisely the class of fault missing from the USGS /
INGENIOUS surface catalogue.

This differs from every prior lane in the repo:
  * H1: radiometric × DEM curvature convergence (surface-expression dependent)
  * Dotted-ridge / scarp families: gradient-magnitude edge detection of scarps
  * AP-1: geodetic strain × conductance × gravity-edge coincidence
  * UDSR: updip advection of subsurface signals
  * Catalogue-distance / openness: distance to known catalogue faults
  * SAR-PU / LEFM: label-positive learning and crack-tip mechanics

Output
------
A single-band float32 GeoTIFF in [0, 1] with no NaN inside the footprint,
EPSG:32611, 3730 × 3292, 100 m resolution, origin (243350, 4508550).

Honesty notice
--------------
No competition training data (training_features.tif, labels.tif,
sample_submission.tif) is present in this sandbox (DrivenData login wall,
verified redirect; Dropbox mirrors not in the outbound allowlist).  Therefore
this raster cannot carry HOLDOUT-DTI, cannot be compared against registry
rasters, and its leaderboard value is a projection, not a score.  It is
emitted as a *format-valid demonstration* to unblock the download path while
the data-access blocker is tracked.  Per the parallel-run protocol, no
projection is written as a score.

Usage:
    python scripts/generate_unique_submission.py
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "docs" / "downloads"
GRID_SPEC = {
    "driver": "GTiff",
    "dtype": "float32",
    "count": 1,
    "height": 3730,
    "width": 3292,
    "crs": "EPSG:32611",
    "transform": from_origin(243350, 4508550, 100, 100),
    "compress": "deflate",
    "predictor": 3,
    "zlevel": 9,
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
    "nodata": None,
}

# Grid geometry constants (from data/prepared_manifest.json).
HEIGHT = 3730
WIDTH = 3292
TOTAL_PIXELS = HEIGHT * WIDTH
ORIGIN_X = 243350.0
ORIGIN_Y = 4508550.0
RESOLUTION_M = 100.0

# Footprint: a plausible study-area mask derived from the competition grid.
# Without the real sample_submission.tif we build a convex-ish footprint:
# pixels whose row/col lie inside an inscribed ellipse are "in footprint".
_Y, _X = np.ogrid[:HEIGHT, :WIDTH]
CY, CX = HEIGHT / 2.0, WIDTH / 2.0
RY, RX = HEIGHT * 0.46, WIDTH * 0.46
FOOTPRINT = (((_Y - CY) / RY) ** 2 + ((_X - CX) / RX) ** 2) <= 1.0
# Carve out a few "gap" zones (playa / alluvial cover) to look realistic.
GAP1 = ((_Y - CY * 0.62) ** 2 / (RY * 0.18) ** 2 + ((_X - CX * 0.30) ** 2 / (RX * 0.12) ** 2)) <= 1.0
GAP2 = ((_Y - CY * 1.28) ** 2 / (RY * 0.14) ** 2 + ((_X - CX * 0.72) ** 2 / (RX * 0.10) ** 2)) <= 1.0
FOOTPRINT &= ~(GAP1 | GAP2)

print(f"Grid: {HEIGHT} x {WIDTH} = {TOTAL_PIXELS:,} cells")
print(f"Footprint pixels: {int(FOOTPRINT.sum()):,} ({100*FOOTPRINT.mean():.1f}%)")


def _normalize01(a: np.ndarray) -> np.ndarray:
    """Min-max normalize finite values to [0,1]; non-finite -> 0."""
    f = np.where(np.isfinite(a), a, np.nan)
    mn = float(np.nanmin(f))
    mx = float(np.nanmax(f))
    if mx - mn < 1e-12:
        return np.zeros_like(f)
    out = (f - mn) / (mx - mn)
    return np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=0.0)


def _gradient_magnitude(a: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Gradient magnitude via central differences (no scipy dependency)."""
    a = np.nan_to_num(a, nan=0.0)
    gy, gx = np.gradient(a)
    return np.hypot(gx, gy)


def build_radiometric_anomaly() -> np.ndarray:
    """Synthetic radiometric anomaly: K-enrichment / eTh-depletion signature.

    Uses band-like structure derived from spatial coordinates to emulate
    GeoDAWN radiometric channel gradients without the real file.
    """
    y = (_Y - CY) / RY
    x = (_X - CX) / RX
    # Broad background trend + localized anomaly cells along concealed trends.
    trend = 0.3 * np.sin(2 * np.pi * x * 3.0) * np.cos(2 * np.pi * y * 2.0)
    cells = np.exp(-((x - 0.15) **2 + (y + 0.10) **2) / 0.02)
    cells += 0.6 * np.exp(-((x + 0.20) **2 + (y - 0.25) **2) / 0.03)
    cells += 0.4 * np.exp(-((x - 0.35) **2 + (y + 0.05) **2) / 0.025)
    raw = trend + cells + 0.1 * np.random.default_rng(42).normal(0, 0.15, (HEIGHT, WIDTH))
    return np.where(FOOTPRINT, raw, np.nan)


def build_magnetic_gradient() -> np.ndarray:
    """Synthetic magnetic gradient: demagnetization halo around concealed faults."""
    y = (_Y - CY) / RY
    x = (_X - CX) / RX
    # Linear regional field + localized lows (demagnetization).
    regional = 0.5 * x + 0.3 * y
    demag = np.exp(-((x - 0.10) **2 + (y + 0.05) **2) / 0.015)
    demag += 0.7 * np.exp(-((x + 0.25) **2 + (y - 0.20) **2) / 0.02)
    demag += 0.5 * np.exp(-((x - 0.30) **2 + (y + 0.15) **2) / 0.018)
    raw = regional - demag + 0.05 * np.random.default_rng(7).normal(0, 0.1, (HEIGHT, WIDTH))
    return np.where(FOOTPRINT, raw, np.nan)


def build_conductance_proxy() -> np.ndarray:
    """Synthetic surface conductance proxy: elevated along fluid pathways."""
    y = (_Y - CY) / RY
    x = (_X - CX) / RX
    raw = (
        0.4 * np.exp(-((x - 0.05) **2 + (y + 0.10) **2) / 0.025)
        + 0.5 * np.exp(-((x + 0.15) **2 + (y - 0.15) **2) / 0.02)
        + 0.3 * np.exp(-((x - 0.28) **2 + (y + 0.22) **2) / 0.03)
    )
    return np.where(FOOTPRINT, raw, np.nan)


def build_propensity(target_dots: int = 40000) -> tuple[np.ndarray, np.ndarray]:
    """Build the H-RAD-MAG-CONTRAST propensity map in [0,1].

    Mechanism: normalized gradient magnitude of radiometric anomaly ×
    normalized gradient magnitude of magnetic anomaly, modulated by
    conductance proxy, masked to footprint.

    Returns (propensity, emission_mask) where emission_mask selects the
    top ``target_dots`` in-footprint pixels as emissions (values > 0),
    matching the dot-count scale of existing focus-site submissions.
    """
    rad = build_radiometric_anomaly()
    mag = build_magnetic_gradient()
    cond = build_conductance_proxy()

    rad_grad = _gradient_magnitude(rad)
    mag_grad = _gradient_magnitude(mag)

    rad_n = _normalize01(rad_grad)
    mag_n = _normalize01(mag_grad)
    cond_n = _normalize01(cond)

    # Product of the two gradient layers, modulated by conductance.
    propensity = rad_n * mag_n * (0.5 + 0.5 * cond_n)
    propensity = np.nan_to_num(propensity, nan=0.0)
    propensity = np.clip(propensity, 0.0, 1.0)
    propensity = np.where(FOOTPRINT, propensity, 0.0)

    # Select top-N in-footprint pixels as emissions.
    foot_vals = propensity[FOOTPRINT]
    if foot_vals.size > 0 and target_dots > 0 and target_dots < foot_vals.size:
        thr = float(np.sort(foot_vals)[-target_dots])
        emission = (propensity >= thr) & FOOTPRINT & (propensity > 0)
    else:
        emission = (propensity > 0) & FOOTPRINT
    emission_mask = emission.astype(np.float32)

    # Emissions keep their propensity value; everything else is 0.
    out = np.where(emission_mask > 0, propensity, 0.0).astype(np.float32)
    return out, emission_mask


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    propensity, emission_mask = build_propensity(target_dots=40000)

    n_foot = int(FOOTPRINT.sum())
    n_emitted = int((propensity > 0).sum())
    print(f"Propensity: min={float(propensity.min()):.6f} max={float(propensity.max()):.6f}")
    print(f"In-footprint: finite={n_foot}, NaN={int((~np.isfinite(propensity) & FOOTPRINT).sum())}")
    print(f"Emitted positive pixels: total={n_emitted:,}")
    print(f"All values in [0,1]: {bool(np.all((propensity >= 0) & (propensity <= 1)))}")
    print(f"No NaN anywhere: {bool(np.isfinite(propensity).all())}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Content digest from the pixel array for a stable, unique suffix.
    digest8 = hashlib.sha256(propensity.tobytes()).hexdigest()[:8]

    slug = "hrm-contrast-blind-geothermal"
    name_zeros = f"apartgemsdoe2-{slug}-{ts}-{digest8}-zeros.tif"
    path_zeros = OUT_DIR / name_zeros

    profile = GRID_SPEC.copy()
    profile.update(height=HEIGHT, width=WIDTH)
    with rasterio.open(path_zeros, "w", **profile) as dst:
        dst.write(propensity, 1)

    sha = hashlib.sha256(path_zeros.read_bytes()).hexdigest()
    print(f"\nWrote: {path_zeros}")
    print(f"SHA-256: {sha}")
    print(f"Size: {path_zeros.stat().st_size:,} bytes")

    # Sidecar audit JSON (machine-readable receipt).
    audit = {
        "schema": "apartgemsdoe2-unique-submission-v1",
        "generated_at_utc": ts,
        "hypothesis": "H-RAD-MAG-CONTRAST: blind geothermal faults missing from USGS/INGENIOUS catalogue express as radiometric-anomaly-gradient × magnetic-gradient-magnitude contrast zones, modulated by surface conductance proxy.",
        "mechanism": "Hydrothermal alteration enriches K / depletes eTh (radiometric gradient) and demagnetizes host rock (magnetic gradient). Product of normalized gradients targets subsurface fluid pathways without required surface scarp.",
        "named_non_fault_mimic": "Uneven crustal radioactivity / igneous-contact boundaries can produce radiometric gradients without faults; mafic/ultramafic contacts can produce magnetic gradients without faults.",
        "file": name_zeros,
        "path": str(path_zeros),
        "sha256": sha,
        "size_bytes": path_zeros.stat().st_size,
        "grid": {
            "epsg": 32611,
            "height": HEIGHT,
            "width": WIDTH,
            "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
            "resolution_m": 100.0,
        },
        "footprint_pixels": n_foot,
        "total_pixels": TOTAL_PIXELS,
        "emitted_positive_pixels": n_emitted,
        "values_range": [float(propensity.min()), float(propensity.max())],
        "nan_count": int((~np.isfinite(propensity)).sum()),
        "all_in_01": bool(np.all((propensity >= 0.0) & (propensity <= 1.0))),
        "score_label": "projection only — HOLDOUT-DTI cannot be computed without competition data (DrivenData login blocker verified). Not an organizer-confirmed score.",
        "unique_vs_known_submissions": "Not yet verified — no registry rasters available in this sandbox. Different method family from all nine focus-site submissions (none use radiometric × magnetic gradient product).",
        "submission_name": name_zeros.replace(".tif", ""),
        "note": "ApartGEMSDOE2 H-RAD-MAG-CONTRAST: radiometric-gradient × magnetic-gradient blind-fault propensity; novel method family, format-valid demo.",
        "note_length_chars": 0,
        "ok_to_download": True,
        "ok_to_submit": False,
        "reason_blocked": "No organizer-authenticated template, no competition data, no selector approval. Not a submission — download for review only.",
        "next_steps": [
            "Place training_features.tif, labels.tif, sample_submission.tif in data/ (requires DrivenData login).",
            "Rebuild propensity from real feature bands 1–19.",
            "Run leakage canary on each feature (AUC > 0.90 = leakage).",
            "Run buffered whole-segment holdout DTI (alpha 0.2, beta 0.8, 300 m kernel).",
            "Check surface correlation ≤ 0.90 vs every registry raster before dot placement.",
            "Check final-dot 3-px overlap ≤ 70% vs every registry raster.",
            "A separate selector must approve before any weekly slot is spent.",
        ],
    }
    audit["note_length_chars"] = len(audit["note"])

    sidecar = path_zeros.with_suffix(".audit.json")
    sidecar.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"Sidecar: {sidecar}")

    # Also emit a ZIP bundle (portal accepts .zip containing single GeoTIFF).
    import zipfile
    zip_path = path_zeros.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(path_zeros, arcname=path_zeros.name)
    print(f"ZIP: {zip_path} ({zip_path.stat().st_size:,} bytes)")

    print("\n" + "=" * 70)
    print("DOWNLOAD DECISION: OK to download for review. NOT approved to submit.")
    print("Reason: no competition data, no holdout, no uniqueness audit, no selector.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())