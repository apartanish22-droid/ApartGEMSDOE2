#!/usr/bin/env python3
"""Reproduce a *read-only* geometry audit of pinned historical TIFFs.

This is not a model, holdout evaluator, submission writer, or portal validator.
It may download prior TIFFs into an ignored scratch cache for comparison only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage

from fetch_audit_data import fetch_one

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "registry" / "historical-pins.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_pin(pin: dict, cache: Path) -> Path:
    """Obtain immutable content as bytes; never trust an unverified cache."""
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (pin["sha256"] + Path(pin["path"]).suffix)
    fetch_one(pin, path)
    return path


def disk(radius_px: int) -> np.ndarray:
    y, x = np.ogrid[-radius_px : radius_px + 1, -radius_px : radius_px + 1]
    return x * x + y * y <= radius_px * radius_px


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float | None:
    """Exact Spearman (tied mid-ranks) for two binary rasters in the footprint."""
    n = int(footprint.sum())
    if not n:
        return None
    n_a = int(np.count_nonzero(a & footprint))
    n_b = int(np.count_nonzero(b & footprint))
    intersection = int(np.count_nonzero(a & b & footprint))
    denom = math.sqrt(n_a * (n - n_a) * n_b * (n - n_b))
    if denom == 0:
        return None  # constant raster has undefined correlation; not a pass
    return (n * intersection - n_a * n_b) / denom


def directional_overlap(candidate: np.ndarray, covered: np.ndarray) -> tuple[int, int, float | None]:
    total = int(candidate.sum())
    matched = int(np.count_nonzero(candidate & covered))
    return matched, total, matched / total if total else None


def unavoidable_overlap(positive_count: int, uncovered_count: int) -> float | None:
    if positive_count <= 0:
        return None
    return max(0, positive_count - uncovered_count) / positive_count


def load_grid(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        mask = ds.read_masks(1) != 0
        return arr, mask, {
            "shape": [ds.height, ds.width],
            "crs": ds.crs.to_string() if ds.crs else None,
            "transform": list(ds.transform)[:6],
            "bands": ds.count,
            "dtype": ds.dtypes[0] if ds.count else None,
            "nodata": str(ds.nodata),
            "driver": ds.driver,
        }


def format_checks(arr, mask, grid, template_grid, footprint):
    finite = np.isfinite(arr)
    inside = arr[footprint]
    outside = ~footprint
    grid_matches = all(grid[k] == template_grid[k] for k in ("shape", "crs", "transform"))
    transform = grid["transform"]
    official_crs_resolution = grid["crs"] == "EPSG:32611" and transform[:2] == [100.0, 0.0] and transform[3:5] == [0.0, -100.0]
    inside_range = bool(np.all(np.isfinite(inside) & (inside >= 0) & (inside <= 1)))
    inside_unmasked = bool(np.all(mask[footprint]))
    # A declared mask with finite invalid numeric nodata can still upset a portal range check.
    outside_null = bool(np.all((~finite | ~mask)[outside]))
    single_band = grid["bands"] == 1 and grid["dtype"] == "float32" and grid["driver"] == "GTiff"
    return {
        "grid_matches_owner_mirror": grid_matches,
        "epsg32611_and_100m_pixels": official_crs_resolution,
        "single_band_float32_geotiff": single_band,
        "all_footprint_finite_in_range": inside_range,
        "footprint_all_unmasked": inside_unmasked,
        "masked_footprint_pixels": int(np.count_nonzero(~mask[footprint])),
        "inside_nan_count": int(np.count_nonzero(np.isnan(inside))),
        "nodata_tag": grid.get("nodata"),
        "outside_null_or_masked": outside_null,
        "whole_array_finite_in_range_diagnostic": bool(np.all(finite & (arr >= 0) & (arr <= 1))),
        "published_format_conservative_local_check": bool(grid_matches and official_crs_resolution and single_band and inside_range and inside_unmasked and outside_null),
        "portal_acceptance": "not tested",
    }


def audit(pins: dict, cache: Path) -> dict:
    files = {key: fetch_pin(pins[key], cache) for key in ("sample", "labels", "lattice", "registry")}
    registry = json.loads(files["registry"].read_text())
    members = registry.get("unique_rasters", [])
    if not any(e.get("sha256") == pins["lattice"]["sha256"] for e in members):
        raise ValueError("Pinned lattice was not found in the pinned registry snapshot")

    sample, _, sample_grid = load_grid(files["sample"])
    labels, _, labels_grid = load_grid(files["labels"])
    lattice, _, lattice_grid = load_grid(files["lattice"])
    if any(labels_grid[k] != sample_grid[k] or lattice_grid[k] != sample_grid[k] for k in ("shape", "crs", "transform")):
        raise ValueError("Pinned sample, labels and lattice grids differ")
    foot = np.isfinite(sample)
    if not foot.any() or not np.array_equal(np.isfinite(lattice), foot):
        raise ValueError("Empty or inconsistent mirror/lattice footprint")
    if not np.all(np.isfinite(lattice[foot]) & (lattice[foot] >= 0) & (lattice[foot] <= 1)):
        raise ValueError("Lattice values are invalid in footprint")
    reference = foot & np.isfinite(lattice) & (lattice > 0)
    if not reference.any():
        raise ValueError("Empty lattice support")
    covered = ndimage.binary_dilation(reference, structure=disk(3))
    uncovered = int(np.count_nonzero(foot & ~covered))
    total = int(foot.sum())
    lattice_covered = total - uncovered

    rasters = {}
    rows = []
    for pin in pins["focus"]:
        file = fetch_pin(pin, cache)
        arr, mask, grid = load_grid(file)
        checks = format_checks(arr, mask, grid, sample_grid, foot)
        if not checks["grid_matches_owner_mirror"]:
            raise ValueError(f"Grid mismatch: {pin['site']}")
        if not checks["single_band_float32_geotiff"] or not checks["all_footprint_finite_in_range"] or not checks["footprint_all_unmasked"]:
            raise ValueError(f"Invalid or masked footprint data: {pin['site']}")
        if not np.all((arr[foot] == 0) | (arr[foot] == 1)):
            raise ValueError(f"Non-binary comparator, binary Spearman would be invalid: {pin['site']}")
        positive = foot & (arr > 0)
        if not positive.any():
            raise ValueError(f"Empty historical raster: {pin['site']}")
        rasters[pin["site"]] = positive
        matched, n, fraction = directional_overlap(positive, covered)
        rows.append({
            "site": pin["site"],
            "filename": Path(pin["path"]).name,
            "source_url": pin["source_url"],
            "sha256": pin["sha256"],
            "reported_submission_name": pin["reported_submission_name"],
            "reported_value": pin["reported_value"],
            "score_evidence": pin["evidence_class"],
            "format": checks,
            "positive_pixels": n,
            "lattice_matches_within_3px": matched,
            "lattice_overlap_fraction": fraction,
            "unavoidable_overlap_bound_at_this_count": unavoidable_overlap(n, uncovered),
        })

    pairs = []
    for ref_site, ref in rasters.items():
        near_ref = ndimage.binary_dilation(ref, structure=disk(3))
        for candidate_site, candidate in rasters.items():
            if candidate_site == ref_site:
                continue
            matched, n, fraction = directional_overlap(candidate, near_ref)
            rho = binary_spearman(candidate, ref, foot)
            pairs.append({"candidate": candidate_site, "reference": ref_site, "matched": matched, "candidate_dots": n, "within_3px_fraction": fraction, "binary_spearman": rho, "duplicate_stop": fraction is not None and fraction > 0.70 or rho is not None and abs(rho) > 0.90})

    for row in rows:
        ours = [p for p in pairs if p["candidate"] == row["site"]]
        best = max(ours, key=lambda p: p["within_3px_fraction"])
        row["max_overlap_other_focus_site"] = {"reference": best["reference"], "fraction": best["within_3px_fraction"]}
        row["duplicate_vs_other_focus_site"] = any(p["duplicate_stop"] for p in ours)

    f25, f31, f32, f36 = (rasters[f"GEMSDOE{x}"] for x in (25, 31, 32, 36))
    cat = foot & (labels > 0)
    distance_to_cat = ndimage.distance_transform_edt(~cat)
    difference = f31 & ~f32
    audit = {
        "schema": "apartgems-historical-forensics-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "GEOMETRY-AUDIT (not HOLDOUT-DTI or an organizer score)",
        "scope": "Nine immutable historical archival variants, one registry lattice, and owner-supplied sample/labels mirrors. No pre-placement surfaces, complete registry, hidden labels, organizer receipts, experiment, or portal submission.",
        "sample_mirror": {"sha256": pins["sample"]["sha256"], "provenance": pins["sample"]["provenance"], "grid": sample_grid, "footprint_pixels": total, "positive_pixels": int(np.count_nonzero(foot & (sample > 0))), "identical_to_labels_in_footprint": bool(np.array_equal(sample[foot], labels[foot]))},
        "lattice_witness": {"sha256": pins["lattice"]["sha256"], "source": f"https://github.com/{pins['lattice']['repo']}/blob/{pins['lattice']['ref']}/{pins['lattice']['path']}", "pinned_registry_sha256": pins["registry"]["sha256"], "registry_id": pins["lattice"]["registry_id"], "positive_pixels": int(reference.sum()), "radius_px": 3, "covered_footprint_pixels": lattice_covered, "uncovered_footprint_pixels": uncovered, "covered_fraction": lattice_covered / total, "champion_sized_budget": int(f32.sum()), "champion_sized_minimum_overlap": unavoidable_overlap(int(f32.sum()), uncovered), "explanation": "At most U distinct dots can lie in uncovered cells. Therefore at least max(0, K-U)/K must be within 3 pixels of the lattice. A bound above 70% is a decisive stop for that K only, not proof every smaller candidate is impossible."},
        "sites": rows,
        "focus_pair_comparisons": pairs,
        "forensics": {"gems32_positives": int(f32.sum()), "gems31_positives": int(f31.sum()), "gems31_only_pixels": int(difference.sum()), "gems32_only_pixels_vs_gems31": int((f32 & ~f31).sum()), "gems31_only_at_most_2px_from_catalogue": int(np.count_nonzero(difference & (distance_to_cat <= 2))), "gems25_only_pixels_vs_gems32": int((f25 & ~f32).sum()), "gems32_only_pixels_vs_gems25": int((f32 & ~f25).sum()), "gems36_extra_pixels_vs_gems32": int((f36 & ~f32).sum()), "gems32_only_pixels_vs_gems36": int((f32 & ~f36).sum())},
        "experiments_run": 0,
        "submission_slots_used": 0,
        "new_tiff_generated": False,
    }
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "audit")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "historical_audit.json")
    args = parser.parse_args()
    result = audit(json.loads(PINS.read_text()), args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Audited {len(result['sites'])} archival TIFFs; {len(result['focus_pair_comparisons'])} directional comparisons; no submission generated.")
    print(f"Lattice uncovered {result['lattice_witness']['uncovered_footprint_pixels']} cells; bound at champion count {result['lattice_witness']['champion_sized_minimum_overlap']:.4%}")
    print(f"Evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
