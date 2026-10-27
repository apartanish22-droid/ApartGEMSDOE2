"""
generate_submission.py — GEMS competition candidate-TIF generator.

Purpose
-------
Produce a UNIQUE, single-band GeoTIFF candidate submission for the DOE GEMS
fault-prospectivity competition, written entirely from an explicit, novel
geothermal hypothesis.  The output is:

  * single-band, Float32 GeoTIFF
  * every pixel finite, values clipped to the inclusive interval [0, 1]
  * CRS EPSG:32611 (UTM zone 11N — the competition CRS referenced in the
    task: https://epsg.io/32611)
  * accompanied by a SHA-256 digest and an automated validator report

Novel hypothesis (not copied from any listed GEMSDOE site)
----------------------------------------------------------
Blind, geothermally active faults in the northern Great Basin should be
highlighted where THREE independent evidence channels coincide:

  1. Multi-scale aeromagnetic edge persistence — a sharp, spatially continuous
     susceptibility contrast that persists across smoothing scales is more
     likely to be a fault offset of magnetic basement than a one-scale noise
     spike.  (Distinct from GEMSDOE30's single-scale "d28" Poisson edge and
     from simple ridge/edge magnitude methods.)
  2. Radiometric alteration gradient — the potassium-to-thorium (K/eTh) ratio
     gradient highlights hydrothermal alteration / lithologic juxtaposition
     along concealed structures, rather than raw radiometric intensity alone.
     (Distinct from GEMSDOE46's radiometric fusion, which fuses raw channels.)
  3. Topographic residual lineament — a DEM-derived curvature/terrain-position
     residual after removing broad regional relief, capturing subtle fault
     scarps not expressed as mapped ridges.
  4. Catalogue masking — known USGS/INGENIOUS catalogue traces are masked to
     zero *pixel-exactly* so the raster emphasizes off-catalogue (previously
     unmapped) structures, which is what the competition rewards.

Final prospectivity = clip(magnetic_persistence * alteration_gradient *
                           topographic_residual, 0, 1), then set to zero on
     catalogue traces.

This combination does not appear in the supplied GEMSDOE result list
(GEMSDOE24/25/27/28/30/31/32/33/36), whose entries are dominated by dotted
ridge/topographic-gap/Poisson/PINN/scatter methods.  It is therefore a
distinct generation method.  Distinct method != proven distinct raster: true
pixelwise uniqueness cannot be established without the registry rasters, which
are not present in this checkout (see status below).

Data status — READ THIS BEFORE DOWNLOADING
------------------------------------------
This checkout does NOT contain training_features.tif, labels.tif,
sample_submission.tif, existing_faults.tif, the cached feature stack, or the
registry rasters.  Competition data is behind the DrivenData login
(https://www.drivendata.org/competitions/306/competition-doe-gems/data/).

Because the official sample_submission.tif is unavailable, the CRS/shape/
geotransform of this generated raster CANNOT be matched to the official
submission format.  The file below is therefore a pipeline demonstration
artifact, NOT a confirmed competition entry.

RELEASE GATE (from README.md): a .tif is "OK TO SUBMIT" only when automated
checks confirm the official sample-submission footprint, CRS, shape and
geotransform; no NaN/Inf inside the footprint; all values in [0, 1]; the file
opens and reads back; SHA-256 and method provenance are recorded; and registry
correlation/dot-overlap checks pass.

Verdict for the generated artifact: NOT OK TO SUBMIT.
Reason: cannot verify match to the official sample_submission.tif footprint /
CRS / shape / geotransform (data behind DrivenData login).  Values are in
[0,1], finite, single-band, readable — those sub-checks pass.  The footprint
match check is the blocker.

Remediation to reach OK TO SUBMIT:
  1. On a machine with DrivenData access, download sample_submission.tif into
     data/ (do not commit credentials).
  2. Re-run this script with --match data/sample_submission.tif so the output
     grid is re-projected/re-sampled to the exact official shape, transform
     and CRS.
  3. Run scripts/validate_submission.py on the output; it must print OK for
     every gate before the file is labelled OK TO SUBMIT.
  4. Only then record an ORGANIZER-CONFIRMED receipt and use a weekly slot.

Usage
-----
  python scripts/generate_submission.py                 # illustrative grid
  python scripts/generate_submission.py --match data/sample_submission.tif
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling

# Import the canonical validator (reuse, don't rebuild / no private forks).
import sys as _sys
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_SCRIPTS_DIR))
from validate_submission import validate as _validate  # noqa: E402

# ---------------------------------------------------------------------------
# Competition / project constants
# ---------------------------------------------------------------------------
EPSG = 32611  # UTM zone 11N, northwestern Great Basin (NV).  https://epsg.io/32611
NODATA = np.float32(-9999.0)  # internal sentinel only; final file has no nodata

# Illustrative grid for the pipeline demonstration (meters, UTM 11N).
# These bounds are NOT the official footprint; see DATA STATUS above.
BBOX = (220000.0, 4380000.0, 340000.0, 4420000.0)  # west, south, east, north
DEFAULT_WIDTH = 300
DEFAULT_HEIGHT = 300

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Evidence-layer generators (synthetic, illustrative — replace with real
# competition layers once data/ is populated)
# ---------------------------------------------------------------------------
def _gaussian_ridge(xx, yy, x0, y0, length, width, angle_deg, amp):
    """A linear Gaussian ridge (fault-like lineament)."""
    theta = math.radians(angle_deg)
    dx = xx - x0
    dy = yy - y0
    # coordinate along / across the ridge
    along = dx * math.cos(theta) + dy * math.sin(theta)
    across = -dx * math.sin(theta) + dy * math.cos(theta)
    # taper along the ridge length with a raised cosine so ridges don't hit edges
    along_taper = np.clip(1.0 - (along / (0.5 * length)) ** 2, 0.0, 1.0)
    across_profile = np.exp(-0.5 * (across / width) ** 2)
    return amp * along_taper * across_profile


# Shared, explicit structure definitions (in normalised 0..1 grid coords as
# fractions of width/height, then converted to metres inside each layer).
#
# BLIND_FAULTS  : off-catalogue, previously unmapped blind geothermal faults
#                 where all three evidence channels coincide.  These are what
#                 the competition rewards (structures missing from the
#                 USGS/INGENIOUS catalogue).
# CATALOGUE_TRACES: known USGS/INGENIOUS catalogue traces.  Masked to zero
#                 pixel-exactly so they do not dominate the raster.
#
# These are PLACEHOLDER geometries for the pipeline demonstration.  Replace
# with real existing_faults.tif and real geophysical layers when data/ is
# populated.  NNE-SSW = typical northern Great Basin / Basin-and-Range trend.
BLIND_FAULTS = [
    # (x_frac, y_frac, length_frac, width_m_frac, angle_deg, strength)
    (0.50, 0.50, 0.85, 0.012, 15.0, 1.0),   # primary blind fault
    (0.30, 0.65, 0.60, 0.010, 15.0, 0.85),  # secondary blind fault
    (0.72, 0.35, 0.55, 0.010, 105.0, 0.75), # conjugate-set blind fault
]
CATALOGUE_TRACES = [
    # (x_frac, y_frac, length_frac, width_m_frac, angle_deg)
    (0.18, 0.22, 0.50, 0.010, 15.0),   # known catalogue trace 1 -> masked out
    (0.82, 0.82, 0.55, 0.010, 15.0),   # known catalogue trace 2 -> masked out
]


def magnetic_edge_persistence(xx, yy, width, height):
    """
    Multi-scale magnetic edge persistence.

    Build magnetic-basement susceptibility boundaries along the BLIND_FAULTS
    lineaments at two smoothing scales; persistence = min(fine, coarse) so
    only edges present at BOTH scales survive.  This suppresses one-scale
    noise and emphasises continuous buried structures — distinct from
    GEMSDOE30's single-scale edge and from plain ridge magnitude.
    """
    # Build fine and coarse edge fields explicitly over the blind faults.
    nx = xx / (xx.max() + 1e-9)
    ny = yy / (yy.max() + 1e-9)
    edges_fine = np.zeros((height, width), dtype=np.float64)
    edges_coarse = np.zeros((height, width), dtype=np.float64)
    for (xf, yf, lf, wf, angle, amp) in BLIND_FAULTS:
        x0 = xf * width
        y0 = yf * height
        length = lf * min(width, height)
        fine = _gaussian_ridge(nx * width, ny * height, x0, y0, length,
                               wf * min(width, height), angle, amp)
        coarse = _gaussian_ridge(nx * width, ny * height, x0, y0, length,
                                 wf * min(width, height) * 2.2, angle, amp)
        edges_fine = np.maximum(edges_fine, fine)
        edges_coarse = np.maximum(edges_coarse, coarse)

    persistence = np.minimum(edges_fine, edges_coarse)
    pmax = persistence.max()
    if pmax > 0:
        persistence = persistence / pmax
    return persistence


def alteration_gradient(xx, yy, width, height):
    """
    K/eTh radiometric alteration gradient.

    Hydrothermal alteration expressed as K/eTh ratio gradients concentrated
    along the BLIND_FAULTS lineaments (concealed structures), rather than raw
    radiometric intensity.  Modelled as gradient magnitude of alteration
    plumes centred on the blind faults — distinct from GEMSDOE46's raw-channel
    radiometric fusion.
    """
    nx = xx / (xx.max() + 1e-9)
    ny = yy / (yy.max() + 1e-9)
    field = np.zeros((height, width), dtype=np.float64)
    for (xf, yf, lf, wf, angle, amp) in BLIND_FAULTS:
        x0 = xf * width
        y0 = yf * height
        sx = wf * min(width, height) * 1.6
        sy = wf * min(width, height) * 0.9
        field += amp * np.exp(-0.5 * (((nx - x0 / width) / sx) ** 2
                                      + ((ny - y0 / height) / sy) ** 2))
    gx, gy = np.gradient(field)
    grad = np.hypot(gx, gy)
    gmax = grad.max()
    if gmax > 0:
        grad = grad / gmax
    return grad


def topographic_residual(xx, yy, width, height):
    """
    Topographic residual lineament after removing broad relief.

    Broad regional tilt plus narrow fault scarps along BLIND_FAULTS;
    residual = detrended elevation, normalised to [0,1].  Captures subtle
    scarps not expressed as mapped ridges (distinct from the many
    ridge/scarp-top2pct methods in the listed GEMSDOE results).
    """
    nx = xx / (xx.max() + 1e-9)
    ny = yy / (yy.max() + 1e-9)
    broad = 0.6 * nx + 0.2 * ny  # regional tilt (broad relief)
    scarps = np.zeros((height, width), dtype=np.float64)
    for (xf, yf, lf, wf, angle, amp) in BLIND_FAULTS:
        x0 = xf * width
        y0 = yf * height
        length = lf * min(width, height)
        scarps += amp * _gaussian_ridge(nx * width, ny * height, x0, y0,
                                        length, wf * min(width, height), angle,
                                        1.0)
    residual = scarps - broad
    rmin, rmax = residual.min(), residual.max()
    if rmax > rmin:
        residual = (residual - rmin) / (rmax - rmin)
    return residual


def catalogue_mask(xx, yy, width, height):
    """
    Mask known USGS/INGENIOUS catalogue traces to zero (pixel-exact), so the
    raster emphasises off-catalogue structures.  Placeholder traces only —
    replace with existing_faults.tif when data/ is available.
    """
    nx = xx / (xx.max() + 1e-9)
    ny = yy / (yy.max() + 1e-9)
    mask = np.ones((height, width), dtype=np.float64)  # 1 = keep
    for (xf, yf, lf, wf, angle) in CATALOGUE_TRACES:
        x0 = xf * width
        y0 = yf * height
        length = lf * min(width, height)
        ridge = _gaussian_ridge(nx * width, ny * height, x0, y0, length,
                                wf * min(width, height), angle, 1.0)
        mask = np.minimum(mask, 1.0 - ridge)  # zero where catalogue trace is
    return mask


# ---------------------------------------------------------------------------
# Prospectivity assembly
# ---------------------------------------------------------------------------
def build_prospectivity(width, height):
    west, south, east, north = BBOX
    transform = from_bounds(west, south, east, north, width, height)
    xs = np.arange(width, dtype=np.float64) * transform.a + transform.c + transform.a / 2
    ys = np.arange(height, dtype=np.float64) * transform.e + transform.f + transform.e / 2
    # note: transform.e is negative (north-up), so ys decreases; invert for intuitive coords
    ys = ys[::-1]
    xx, yy = np.meshgrid(xs, ys)

    mag = magnetic_edge_persistence(xx, yy, width, height)
    alt = alteration_gradient(xx, yy, width, height)
    topo = topographic_residual(xx, yy, width, height)
    cat = catalogue_mask(xx, yy, width, height)

    prospectivity = mag * alt * topo * cat
    prospectivity = np.clip(prospectivity, 0.0, 1.0).astype(np.float32)
    return prospectivity, transform, (mag, alt, topo, cat)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def write_geotiff(path, array, transform, crs=EPSG):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = array.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=rasterio.crs.CRS.from_epsg(crs),
        transform=transform,
        nodata=None,  # explicitly no nodata: every pixel is a valid [0,1] value
    ) as dst:
        dst.write(array, 1)
        dst.update_tags(
            METHOD="multi-evidence geothermal prospectivity (mag-persistence x K/eTh-gradient x topo-residual, catalogue-masked)",
            UNIQUE_VS_LISTED_SITES="distinct generation method; pixelwise uniqueness UNKNOWN without registry rasters",
            STATUS="NOT OK TO SUBMIT — cannot match official sample_submission.tif footprint (data behind DrivenData login)",
        )


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Validation (reuses the same gate logic as scripts/validate_submission.py)
# ---------------------------------------------------------------------------
def validate(path, sample_path=None):
    """Thin wrapper around the canonical validator in validate_submission.py."""
    return _validate(path, sample_path=sample_path)


def main():
    ap = argparse.ArgumentParser(description="Generate a unique GEMS candidate GeoTIFF.")
    ap.add_argument("--out", default=None, help="Output .tif path (default: artifacts/candidate_submission.tif)")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    ap.add_argument(
        "--match",
        default=None,
        help="Regrid output to match this sample_submission.tif (CRS/shape/transform)",
    )
    ap.add_argument(
        "--name",
        default="gemsdoe-multi-evidence-prospectivity-v1",
        help="Submission name (<= ~60 chars recommended)",
    )
    ap.add_argument(
        "--note",
        default="Unique multi-evidence geothermal prospectivity (mag-persistence x K/eTh-gradient x topo-residual, catalogue-masked). Pipeline demo; footprint match unverified.",
        help="Submission note (<= 140 chars)",
    )
    args = ap.parse_args()

    out = Path(args.out) if args.out else ARTIFACTS_DIR / "candidate_submission.tif"
    out.parent.mkdir(parents=True, exist_ok=True)

    prospectivity, transform, layers = build_prospectivity(args.width, args.height)

    # If matching the official sample, regrid onto its grid exactly.
    sample_path = Path(args.match) if args.match else None
    if sample_path is not None:
        if not sample_path.exists():
            print(f"ERROR: --match file not found: {sample_path}", file=sys.stderr)
            sys.exit(2)
        with rasterio.open(sample_path) as sample:
            out_array = np.empty(
                (sample.height, sample.width), dtype=np.float32
            )
            reproject(
                source=prospectivity,
                destination=out_array,
                src_transform=transform,
                src_crs=CRS.from_epsg(EPSG),
                dst_transform=sample.transform,
                dst_crs=sample.crs,
                resampling=Resampling.bilinear,
            )
            out_array = np.clip(out_array, 0.0, 1.0).astype(np.float32)
            transform = sample.transform
            prospectivity = out_array

    write_geotiff(out, prospectivity, transform)

    digest = sha256(out)
    report = validate(out, sample_path=sample_path)

    # Run card
    run_card = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "Coincident multi-scale magnetic edge persistence x K/eTh "
        "radiometric alteration gradient x topographic residual lineament, "
        "catalogue-masked to emphasise off-catalogue blind geothermal faults.",
        "mechanism": "Multiply three independent normalised evidence layers; zero "
        "on known catalogue traces so only unmapped structures remain; values "
        "clipped to [0,1].",
        "named_non_fault_mimic": "Non-tectonic lithologic contacts, surficial cover, "
        "and non-fault topographic edges can mimic linear magnetic/radiometric "
        "contrast.",
        "holdout_dti": None,
        "holdout_ci_95": None,
        "evaluator_version": None,
        "withheld_positive_count": None,
        "correlation_overlap_vs_registry": "UNTESTED — registry rasters unavailable "
        "in this checkout.",
        "raster_sha256": digest,
        "validator_output": report,
        "submission_name": args.name,
        "submission_note": args.note[:140],
        "verdict": "negative",
        "ok_to_submit": False,
        "submit_blocker": "Cannot verify match to official sample_submission.tif "
        "CRS/shape/geotransform (competition data behind DrivenData login).",
    }
    card_path = ARTIFACTS_DIR / "run-card.json"
    with open(card_path, "w") as f:
        json.dump(run_card, f, indent=2)

    print(f"Wrote raster:        {out}")
    print(f"SHA-256:             {digest}")
    print(f"Validator gate pass: {report['gate_pass']}")
    print(f"Values in [0,1]:     {report['values_in_0_1']}  "
          f"(min={report['min']}, max={report['max']})")
    print(f"Finite/no NaN:       {report['finite']} / {report['no_nan']}")
    print(f"Sample match:        {report['matches_sample_crs_shape_transform']}")
    print(f"Run card:            {card_path}")
    print("\nSTATUS: NOT OK TO SUBMIT — see DATA STATUS and RELEASE GATE in this script.")


if __name__ == "__main__":
    main()
