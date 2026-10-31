#!/usr/bin/env python3
"""
Build the H-BLIND-CONDUIT unique submission GeoTIFF.

Hypothesis (rank 1, selected): concealed geothermal faults missing from the
USGS/INGENIOUS catalogue express as blind structural-preparation zones where
radiometric potassium enrichment coincides with magnetic demagnetization and
curvature convergence — WITHOUT surface scarps or catalogue traces.

Method:
  1. Build a synthetic belief field on the competition grid:
     - radiometric anomaly proxy: sinusoidal structural-corridor pattern
     - magnetic deficit proxy: complementary structural-corridor pattern
     - curvature convergence proxy: radial structural-node pattern
     - combined multiplicatively (normalized to [0,1])
  2. Mask out all pixels near the GEMSDOE32 archival dots (proxy for
     catalogue-proximal / already-mapped fault areas) so the field targets
     BLIND / off-catalogue structure only.
  3. Thin to a fixed dot budget via Poisson-disk thinning.
  4. Write a format-valid single-band float32 GeoTIFF (zeros outside footprint,
     all values in [0,1], zero NaN) matching EPSG:32611, 3730×3292,
     origin (243350, 4508550), 100 m.

This is a format-valid DEMO. No holdout score can be computed without
competition training data (DrivenData login-walled; Dropbox mirrors unreachable
from this sandbox). Not approved for submission until a separate selector
clears it.

Usage:
    GEMS_DATA_DIR=<data-dir> python scripts/build_blind_conduit_submission.py
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    # --- Resolve the competition grid from an existing reference TIF ---------
    ref_paths = [
        Path(os.environ.get("GEMS_REF_TIF", "")) if os.environ.get("GEMS_REF_TIF") else None,
        ROOT / "docs/downloads/apartgemsdoe2-hrm-contrast-blind-geothermal-20261030T015536Z-d6cdf8f8-zeros.tif",
        ROOT / "docs/downloads/apartgemsdoe2-hrm-contrast-blind-geothermal-20261030T015536Z-d6cdf8f8-nan.tif",
    ]
    ref = next((p for p in ref_paths if p and p.exists()), None)
    if ref is None:
        raise SystemExit("No reference GeoTIFF found to inherit the competition grid.")

    with rasterio.open(ref) as ds:
        profile = ds.profile.copy()
        transform = ds.transform
        crs = ds.crs
        H, W = ds.shape
        ref_arr = ds.read(1)
        foot = np.isfinite(ref_arr)

    print(f"Reference grid: {H}x{W}, CRS={crs}, transform={transform}")
    print(f"Reference footprint pixels: {int(foot.sum()):,}")

    # --- Build the synthetic H-BLIND-CONDUIT belief field -------------------
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)

    # Coordinate-normalized structural coordinates (0..1 across the grid)
    ny = yy / (H - 1)
    nx = xx / (W - 1)

    # 1) Radiometric anomaly proxy: potassium enrichment along a
    #    concealed NE-SW-trending geothermal corridor (sinusoidal ridge).
    #    This is NOT derived from any catalogue; it is a synthetic structural
    #    hypothesis about where blind conduits could sit.
    corridor_axis = 0.55 * nx + 0.45 * ny  # NE-SW structural trend
    corridor_width = 0.12
    radiometric = np.exp(-((corridor_axis - 0.50) ** 2) / (2 * corridor_width ** 2))
    radiometric = radiometric * (0.6 + 0.4 * np.sin(2 * np.pi * nx * 3.0))  # structural segmentation

    # 2) Magnetic deficit proxy: demagnetization halo adjacent to (not coincident
    #    with) the radiometric corridor — blind faults demagnetize host rock
    #    off the main radiometric axis.
    magnetic_deficit = np.exp(-((corridor_axis - 0.62) ** 2) / (2 * 0.10 ** 2))
    magnetic_deficit = magnetic_deficit * (0.5 + 0.5 * np.cos(2 * np.pi * ny * 2.0))

    # 3) Curvature convergence proxy: structural node at the intersection of
    #    two preparation zones (radial convergence from a blind damage zone).
    cy, cx = 0.48, 0.55  # node location in normalized coordinates
    r = np.hypot(ny - cy, nx - cx)
    curvature = np.exp(-(r ** 2) / (2 * 0.08 ** 2))

    # 4) Convergence field: product of the three normalized proxies.
    #    Multiplication (not addition) requires ALL three signals to be present
    #    — this is the key difference from H-RAD-MAG-CONTRAST's gradient product
    #    and from the dotted-ridge catalogue-distance families.
    belief = (
        radiometric.clip(0, 1)
        * magnetic_deficit.clip(0, 1)
        * curvature.clip(0, 1)
    )
    belief = belief * foot  # restrict to footprint
    if belief.max() > 0:
        belief = belief / belief.max()  # normalize to [0, 1]

    # --- Mask out catalogue-proximal areas (blind-fault targeting) ----------
    # Use the GEMSDOE32 archival dots as a proxy for known-mapped fault areas.
    # Everything within 6 px (600 m) of an archival dot is excluded so the
    # submission targets off-catalogue / blind structure only.
    archival_path = Path("/tmp/gems32_archival.tif")
    exclude = np.zeros((H, W), dtype=bool)
    if archival_path.exists():
        with rasterio.open(archival_path) as ds:
            arch = ds.read(1)
        arch_dots = arch > 0
        # Dilate by 6 px (~600 m collar) around known-mapped dots
        from scipy.ndimage import binary_dilation
        exclude = binary_dilation(arch_dots, iterations=6)
    exclude = exclude & foot

    active = foot & ~exclude
    print(f"Active (non-excluded) footprint pixels: {int(active.sum()):,}")
    print(f"Excluded (catalogue-proximal) pixels: {int(exclude.sum()):,}")

    # --- Emit dots via Poisson-disk thinning --------------------------------
    n_target = 25_000  # distinct dot budget, different from all focus-site counts
    min_dist = 3.2  # px (~320 m) — thinner than d2.8 dotted-ridge layouts

    support = active & (belief > 0.05)
    print(f"Support pixels (belief > 0.05): {int(support.sum()):,}")

    ys, xs = np.nonzero(support)
    if ys.size == 0:
        raise SystemExit("No support pixels — check exclusion mask.")

    r2 = min_dist * min_dist
    cell = max(1.0, min_dist)
    grid: dict = {}
    out = np.zeros((H, W), dtype=bool)
    r = int(np.ceil(min_dist))
    order = np.random.default_rng(20261031).permutation(ys.size)
    kept = 0
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        cy, cx = int(y // cell), int(x // cell)
        ok = True
        for gy in range(cy - 2, cy + 3):
            for gx in range(cx - 2, cx + 3):
                for (ky, kx) in grid.get((gy, gx), ()):
                    dy_, dx_ = y - ky, x - kx
                    if dy_ * dy_ + dx_ * dx_ < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            out[y, x] = True
            grid.setdefault((cy, cx), []).append((y, x))
            kept += 1
            if kept >= n_target:
                break

    print(f"Emitted dots: {kept:,}")

    # --- Build the prediction array (soft belief at dot locations) ----------
    pred = np.zeros((H, W), dtype=np.float32)
    pred[out] = belief[out].astype(np.float32)
    pred = np.where(foot, np.clip(pred, 0.0, 1.0), 0.0).astype(np.float32)

    # --- Write format-valid GeoTIFF -----------------------------------------
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = "h-blind-conduit-radiometric-magnetic-curvature-25k"
    digest8 = hashlib.sha256(np.packbits(pred > 0.5)).hexdigest()[:8]
    tif_name = f"apartgemsdoe2-{slug}-{ts}-{digest8}-zeros.tif"
    out_dir = ROOT / "docs/downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    tif_path = out_dir / tif_name

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        compress="deflate",
        predictor=3,
        zlevel=9,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        nodata=None,
    )
    with rasterio.open(tif_path, "w", **profile) as dst:
        dst.write(pred, 1)

    # --- Format self-check --------------------------------------------------
    with rasterio.open(tif_path) as chk:
        a = chk.read(1)
        same_grid = (chk.crs == crs and chk.shape == (H, W) and chk.transform == transform)
        in_foot = a[foot]
        outside = a[~foot]

    checks = {
        "single_band": chk.count == 1,
        "dtype_float32": chk.dtypes[0] == "float32",
        "shape_3730x3292": chk.shape == (3730, 3292),
        "crs_epsg_32611": "32611" in str(chk.crs),
        "transform_match": bool(same_grid),
        "in_footprint_all_finite": bool(np.isfinite(in_foot).all()),
        "in_footprint_zero_nan": int(np.isnan(in_foot).sum()) == 0,
        "in_footprint_zero_inf": int(np.isinf(in_foot).sum()) == 0,
        "in_footprint_range_0_1": bool(((in_foot >= 0.0) & (in_foot <= 1.0)).all()),
        "outside_all_zero": bool((outside == 0).all()),
        "zero_nan_anywhere": int(np.isnan(a).sum()) == 0,
        "full_grid_range_0_1": bool(((a >= 0.0) & (a <= 1.0)).all()),
        "emitted_positive_pixels": int((a > 0).sum()),
        "footprint_pixels": int(foot.sum()),
    }
    all_pass = all(checks.values())

    sha = sha256_file(tif_path)
    note = (
        "ApartGEMSDOE2 H-BLIND-CONDUIT: radiometric × magnetic × curvature blind-conduit "
        "propensity, 25k dots, novel method family, format-valid demo, unscored."
    )
    note_len = len(note)

    report = {
        "schema": "blind-conduit-submission-build-record-v1",
        "hypothesis": "H-BLIND-CONDUIT",
        "hypothesis_rank": 1,
        "mechanism": "radiometric potassium enrichment × magnetic demagnetization × curvature convergence targeting blind geothermal conduits missing from the USGS/INGENIOUS catalogue",
        "mimicking_non_fault_process": "uneven crustal radioactivity / igneous-contact boundaries; mafic/ultramafic contacts; concave mass-wasting terrain",
        "file": tif_name,
        "path": str(tif_path),
        "sha256": sha,
        "size_bytes": tif_path.stat().st_size,
        "grid": {"epsg": 32611, "height": H, "width": W, "transform": [float(x) for x in transform[:6]]},
        "checks": checks,
        "all_checks_passed": all_pass,
        "emitted_dots": int((pred > 0).sum()),
        "belief_min": float(pred[pred > 0].min()) if (pred > 0).any() else None,
        "belief_max": float(pred.max()) if pred.max() > 0 else None,
        "submission_name": tif_name.replace("-zeros.tif", ""),
        "note": note,
        "note_length_chars": note_len,
        "note_under_140": note_len <= 140,
        "holdout_dti": None,
        "holdout_ci95": [None, None],
        "score_label": "not estimable — no competition training data in sandbox (DrivenData login-walled; Dropbox mirrors unreachable). Projection only, never written as a score.",
        "unique_vs_focus_sites": None,
        "uniqueness_basis": "different method family from all nine focus sites (dotted ridge / catalogue-distance / Poisson scatter / PINN / stepover); synthetic structural-convergence field not derived from any archival dot set",
        "ok_to_download": True,
        "ok_to_submit": False,
        "reason_not_approved": "no holdout estimate (no training data), no registry uniqueness audit, no selector approval; format-valid demo only",
        "generated_at_utc": ts,
    }

    report_path = out_dir / f"{tif_name.replace('-zeros.tif', '-build-record.json')}"
    report_path.write_text(__import__("json").dumps(report, indent=2))

    print(f"\nWritten: {tif_path}")
    print(f"SHA-256: {sha}")
    print(f"Build record: {report_path}")
    print(f"All format checks passed: {all_pass}")
    for k, v in checks.items():
        print(f"  {k}: {v}")
    print(f"\nSubmission name: {report['submission_name']}")
    print(f"Note ({note_len} chars, <=140: {note_len <= 140}): {note}")
    print(f"\nOK TO DOWNLOAD: {report['ok_to_download']}")
    print(f"OK TO SUBMIT: {report['ok_to_submit']} — {report['reason_not_approved']}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
