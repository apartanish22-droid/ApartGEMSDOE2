#!/usr/bin/env python3
"""Byte-level verification of the nine focus GEMSDOE files plus the GEMSDOE28 S31 candidates.

Measures, from saved bytes only (no organizer data, no holdout, no score estimate):
  * SHA-256 of each file against the pin in registry/historical-pins.json (focus) or the
    value published on the owner's page (S31 far65, 31 Oct 2026).
  * Format: shape, transform, CRS against sample_submission.tif; values inside the footprint
    (finite, in [0, 1]); NaN and non-zero counts outside the footprint.
  * Dot set = finite, > 0, inside footprint (same definition as scripts/gate_candidates.py).
  * Directional 3-px overlap: share of dots of A within 3 px (Euclidean, <= 3.0) of any dot of B,
    for every ordered pair, including the 13GEMSDOE r13 lattice as B.
  * Catalogue proximity: share of dots within 3 px of a USGS/INGENIOUS catalogue positive.
  * Lattice geometry: footprint cells farther than 3 px from every lattice dot.

Writes evidence/nine_site_verification_20261031.json. Passing or failing here is NOT approval to
upload: the literal lattice rule and the organizer's private-set score are separate gates.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
NINE_DIR = ROOT / ".cache" / "nine"
OUT = ROOT / "evidence" / "nine_site_verification_20261031.json"
RADIUS_PX = 3.0

PINS = json.loads((ROOT / "registry" / "historical-pins.json").read_text())
SAMPLE = DATA / "sample_submission.tif"
LABELS = DATA / "labels.tif"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        return arr, ds.transform, ds.crs.to_string() if ds.crs else None, arr.shape, ds.dtypes[0]


def main() -> int:
    samp_arr, samp_tf, samp_crs, samp_shape, _ = read(SAMPLE)
    foot = np.isfinite(samp_arr)
    lab_arr, lab_tf, _, lab_shape, _ = read(LABELS)
    if lab_shape != samp_shape or lab_tf != samp_tf:
        raise SystemExit("labels grid differs from sample grid")
    catalogue = lab_arr == 1
    dist_to_cat = ndimage.distance_transform_edt(~catalogue)

    files = []  # (key, label, path, expected_sha, source)
    for pin in PINS["focus"]:
        site = pin["site"]
        files.append((site, f"{site} best (repo pin)", DATA / "registry_focus" / f"{site}_best.tif",
                      pin["sha256"], pin["source_url"]))
    lat = PINS["lattice"]
    files.append(("LATTICE", "13GEMSDOE r13-lattice-s5 (calibration raster, registry-039)",
                  DATA / "registry_focus" / "LATTICE_r13.tif", lat["sha256"],
                  f"https://github.com/{lat['repo']}/blob/{lat['ref']}/{lat['path']}"))
    files.append(("S31_FAR65", "gemsdoe28-s31-far65-dispfill-20261031-zeros.tif (GEMSDOE28 main)",
                  NINE_DIR / "s31_far65.tif",
                  "baf007bd1f360ee3b381584ee67eb15120deb15829f76d8632bfce0b2815e7eb",
                  "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/docs/candidates/gemsdoe28-s31-far65-dispfill-20261031-zeros.tif"))
    files.append(("S31_MIDBAND", "gemsdoe28-s31-midband-random-budgetfill-20261031-zeros.tif (GEMSDOE28 main)",
                  NINE_DIR / "s31_midband.tif", None,
                  "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/docs/candidates/gemsdoe28-s31-midband-random-budgetfill-20261031-zeros.tif"))

    records, dots, surfaces = {}, {}, {}
    for key, label, path, expected, source in files:
        if not path.is_file():
            raise SystemExit(f"missing local bytes for {key}: {path}")
        arr, tf, crs, shape, dtype = read(path)
        digest = sha256(path)
        inside = arr[foot]
        outside = arr[~foot]
        d = np.isfinite(arr) & (arr > 0) & foot
        dots[key] = d
        surfaces[key] = arr
        vals_in = np.unique(inside[np.isfinite(inside)])
        records[key] = {
            "label": label,
            "source_url": source,
            "local_path": str(path.relative_to(ROOT)),
            "sha256": digest,
            "sha256_matches_expected": (None if expected is None else digest == expected),
            "dtype": dtype,
            "shape_matches_sample": shape == samp_shape,
            "transform_matches_sample": tf == samp_tf,
            "crs": crs,
            "crs_matches_sample": crs == samp_crs,
            "in_footprint_all_finite": bool(np.isfinite(inside).all()),
            "in_footprint_min": float(np.nanmin(inside)),
            "in_footprint_max": float(np.nanmax(inside)),
            "in_footprint_in_0_1": bool(np.nanmin(inside) >= 0.0 and np.nanmax(inside) <= 1.0),
            "in_footprint_distinct_values": [float(v) for v in vals_in[:5]],
            "in_footprint_binary_0_1": bool(set(np.unique(inside).tolist()) <= {0.0, 1.0}),
            "outside_footprint_nan_cells": int(np.isnan(outside).sum()),
            "outside_footprint_nonzero_finite_cells": int(((outside != 0) & np.isfinite(outside)).sum()),
            "outside_footprint_encoding": ("NaN" if np.isnan(outside).any() else
                                           ("zeros" if (outside == 0).all() else "other")),
            "dots": int(d.sum()),
            "dots_within_3px_of_catalogue_fraction": float((dist_to_cat[d] <= RADIUS_PX).mean()) if d.any() else None,
            "dots_on_catalogue_positive_cells": int((d & catalogue).sum()),
        }

    # The file names the user listed (many end in -nan). Found by name in the focus registry manifest;
    # each is compared with the pinned zeros/allfinite copy for the same site (in-footprint dot set).
    user_named = {
        "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
    }
    manifest = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())["rasters"]
    user_records = {}
    for site, fname in user_named.items():
        hits = [r for r in manifest if r["repo"] == site and r["path"].endswith(fname)]
        if len(hits) != 1:
            raise SystemExit(f"user-named file not uniquely found in registry: {site} {fname} ({len(hits)})")
        hit = hits[0]
        path = ROOT / hit["local"]
        arr, _, _, _, _ = read(path)
        d = np.isfinite(arr) & (arr > 0) & foot
        outside = arr[~foot]
        user_records[site] = {
            "file_name": fname,
            "source_url": f"https://github.com/buffedlizard55-lab/{site}/blob/{hit['ref']}/{hit['path']}",
            "sha256": hit["sha256"],
            "bytes": hit["bytes"],
            "sha256_recomputed_matches_manifest": sha256(path) == hit["sha256"],
            "outside_footprint_encoding": ("NaN" if np.isnan(outside).any() else
                                           ("zeros" if (outside == 0).all() else "other")),
            "outside_footprint_nan_cells": int(np.isnan(outside).sum()),
            "dots": int(d.sum()),
            "dot_set_identical_to_pinned_copy": bool(np.array_equal(d, dots[site])),
        }

    # Lattice geometry: footprint cells that are NOT within 3 px of any lattice dot.
    lat_d = dots["LATTICE"]
    lat_dist = ndimage.distance_transform_edt(~lat_d)
    uncovered = foot & (lat_dist > RADIUS_PX)
    lattice_geometry = {
        "footprint_cells": int(foot.sum()),
        "cells_within_3px_of_lattice": int((foot & (lat_dist <= RADIUS_PX)).sum()),
        "cells_NOT_within_3px_of_lattice": int(uncovered.sum()),
        "lattice_coverage_fraction": float((foot & (lat_dist <= RADIUS_PX)).sum() / foot.sum()),
        # Upper bound on dots for a file that meets the literal <=70% rule against the lattice:
        # u dots in uncovered cells and c covered dots need c/(u+c) <= 0.70, so u+c <= u/0.30.
        "literal_70pct_upper_bound_on_total_dots": int(np.floor(uncovered.sum() / 0.30)),
    }

    # Directional overlap matrix: rows = A (candidate), columns = B (reference).
    keys = [k for k, *_ in files]
    dist_cache = {}
    for b in keys:
        dist_cache[b] = ndimage.distance_transform_edt(~dots[b])
    matrix = {}
    for a in keys:
        matrix[a] = {}
        da = dots[a]
        n = int(da.sum())
        for b in keys:
            if a == b:
                matrix[a][b] = 1.0
                continue
            matrix[a][b] = float((dist_cache[b][da] <= RADIUS_PX).mean()) if n else None

    # Subset and derivation facts used in the mechanism section.
    subset = {}
    for a, b in [("GEMSDOE32", "GEMSDOE30"), ("S31_FAR65", "GEMSDOE32"), ("S31_MIDBAND", "GEMSDOE32")]:
        subset[f"{a}_dots_subset_of_{b}"] = bool((dots[a] & ~dots[b]).sum() == 0)
        subset[f"{a}_dots_not_in_{b}"] = int((dots[a] & ~dots[b]).sum())
        subset[f"{b}_dots_not_in_{a}"] = int((dots[b] & ~dots[a]).sum())
    removed_30_to_32 = dots["GEMSDOE30"] & ~dots["GEMSDOE32"]
    subset["GEMSDOE30_minus_GEMSDOE32_within_3px_of_catalogue"] = [
        int((dist_to_cat[removed_30_to_32] <= RADIUS_PX).sum()), int(removed_30_to_32.sum())]
    subset["GEMSDOE32_dots_kept_within_3px_of_catalogue"] = [
        int((dist_to_cat[dots["GEMSDOE32"]] <= RADIUS_PX).sum()), int(dots["GEMSDOE32"].sum())]

    # Literal-rule status per candidate: worst non-lattice overlap and lattice overlap.
    status = {}
    for a in ["S31_FAR65", "S31_MIDBAND"] + [k for k, *_ in files if k not in ("LATTICE", "S31_FAR65", "S31_MIDBAND")]:
        others_nine = [b for b in keys if b not in (a, "LATTICE", "S31_FAR65", "S31_MIDBAND")]
        status[a] = {
            "worst_overlap_vs_other_focus_nine": max(matrix[a][b] for b in others_nine
                                                    if b in [x[0] for x in files[:9]]),
            "overlap_vs_lattice": matrix[a]["LATTICE"],
            "literal_70pct_lattice_gate_passes": matrix[a]["LATTICE"] <= 0.70,
        }

    out = {
        "schema": "nine-site-verification-20261031-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "sample_grid": {"shape": list(samp_shape), "crs": samp_crs, "transform": list(samp_tf)[:6]},
        "radius_px": RADIUS_PX,
        "files": records,
        "user_named_variants": user_records,
        "lattice_geometry": lattice_geometry,
        "overlap_matrix_A_within_3px_of_B": matrix,
        "subset_and_mechanism": subset,
        "status": status,
        "scope_note": ("Nine focus references + 13GEMSDOE lattice + two S31 candidates only. The full "
                       "511-raster registry gate is evidence/gates_s31_20261031.json (run separately). "
                       "Scores are owner/user-reported; none is an organizer receipt."),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for k in keys:
        r = records[k]
        print(f"{k:12s} dots={r['dots']:6d} enc={r['outside_footprint_encoding']:5s} "
              f"sha={r['sha256'][:12]} in01={r['in_footprint_in_0_1']} binary={r['in_footprint_binary_0_1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
