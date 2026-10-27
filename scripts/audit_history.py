#!/usr/bin/env python3
"""Re-audit hash-pinned historical rasters and a lattice witness (not experiments).

This is a forensic tool, not the shared holdout evaluator or a submission writer.
It cannot authenticate a competition template, forecast a score, or authorize a
candidate. It operates only on the supplied, explicitly incomplete registry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from numbers import Integral
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from fetch_audit_data import checked_entries, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    return x*x + y*y <= radius*radius


def lower_overlap_bound(uncovered: int, dots: int) -> tuple[int, float]:
    """Minimum number/fraction covered if dots are distinct and in footprint."""
    if (isinstance(uncovered, bool) or isinstance(dots, bool)
            or not isinstance(uncovered, Integral) or not isinstance(dots, Integral)
            or uncovered < 0 or dots <= 0):
        raise ValueError("uncovered must be nonnegative and dots must be positive")
    minimum = max(0, dots - uncovered)
    return minimum, minimum / dots


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint_size: int) -> float | None:
    """Binary Spearman equals phi: ranks have exactly two tied groups."""
    n_a = int(a.sum()); n_b = int(b.sum()); both = int(np.count_nonzero(a & b))
    denom = n_a * (footprint_size - n_a) * n_b * (footprint_size - n_b)
    if denom <= 0:
        return None
    return (footprint_size * both - n_a * n_b) / math.sqrt(denom)


def grid_match(a, b) -> bool:
    return (a.width == b.width and a.height == b.height and a.crs == b.crs
            and a.transform == b.transform)


def require_self_contained(dataset) -> None:
    """External masks or metadata are not covered by the TIFF's pinned hash."""
    if {Path(name).resolve() for name in dataset.files} != {Path(dataset.name).resolve()}:
        raise ValueError(f"external sidecar affects pinned raster: {dataset.name}")


def run(manifest_path: Path, data_dir: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    entries = checked_entries(manifest)
    by_id = {e["id"]: e for e in entries}
    required = {"mirror_sample", "mirror_labels", "lattice"}
    if not required <= set(by_id):
        raise ValueError(f"required inputs missing: {required - set(by_id)}")
    for entry in entries:
        path = data_dir / f"{entry['id']}.tif"
        if not path.is_file() or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"missing or incorrect pinned file: {path}")

    sample_path = data_dir / "mirror_sample.tif"
    with rasterio.open(sample_path) as sample:
        require_self_contained(sample)
        if sample.count != 1:
            raise ValueError("mirrored sample must have one band for this audit")
        template = sample.profile.copy()
        footprint = sample.read_masks(1) != 0
        sample_values = sample.read(1)
        if not footprint.any():
            raise ValueError("empty sample-derived footprint")
        if not np.isfinite(sample_values[footprint]).all():
            raise ValueError("sample has nonfinite values in its own footprint")
        sample_positives = int(np.count_nonzero(sample_values[footprint] > 0))
        with rasterio.open(data_dir / "mirror_labels.tif") as labels:
            require_self_contained(labels)
            if not grid_match(sample, labels):
                raise ValueError("label mirror and sample mirror have different grids")
            label_values = labels.read(1)
            label_mask = labels.read_masks(1) != 0
            label_mask_equal = bool(np.array_equal(footprint, label_mask))
            label_positives = int(np.count_nonzero(label_values[footprint] > 0))
            sample_label_equal = bool(np.array_equal(sample_values[footprint], label_values[footprint]))
        del sample_values, label_values, label_mask

        hist = [e for e in entries if e["kind"] == "historical"]
        dots = {}
        raster_reports = {}
        for entry in hist + [by_id["lattice"]]:
            with rasterio.open(data_dir / f"{entry['id']}.tif") as src:
                require_self_contained(src)
                if not grid_match(sample, src):
                    raise ValueError(f"grid mismatch: {entry['id']}")
                if src.count != 1:
                    raise ValueError(f"unexpected band count: {entry['id']}")
                values = src.read(1)
                raster_mask = src.read_masks(1) != 0
                inside = values[footprint]
                finite_inside = np.isfinite(inside)
                out_of_range_inside = int(np.count_nonzero(finite_inside & ((inside < 0) | (inside > 1))))
                binary = bool(np.all((inside == 0) | (inside == 1)))
                if not binary:
                    raise ValueError(f"historical file {entry['id']} is not binary inside the footprint; cannot use binary-only comparison")
                positive = footprint & np.isfinite(values) & (values > 0)
                dots[entry['id']] = positive
                raster_reports[entry['id']] = {
                    "sha256": entry["sha256"],
                    "source": entry["reference_source"],
                    "dots_inside": int(positive.sum()),
                    "single_band": src.count == 1,
                    "driver": src.driver,
                    "dtype": src.dtypes[0],
                    "grid_matches_unauthenticated_mirror": True,
                    "nonfinite_inside": int(np.count_nonzero(~finite_inside)),
                    "out_of_range_inside": out_of_range_inside,
                    "masked_inside": int(np.count_nonzero(footprint & ~raster_mask)),
                    "outside_not_null_or_masked": int(np.count_nonzero(~footprint & raster_mask & ~np.isnan(values))),
                    "positive_outside_footprint": int(np.count_nonzero(~footprint & np.isfinite(values) & (values > 0))),
                    "whole_array_nonfinite": int(np.count_nonzero(~np.isfinite(values))),
                    "nodata": str(src.nodata),
                    "method": "read raw TIFF pixels and GDAL masks; footprint from unauthenticated sample mirror; not organizer acceptance",
                }
                del values, raster_mask, inside, finite_inside
        n_footprint = int(footprint.sum())
        # Exactly nine focus files and one registry witness. Overlap is directional.
        comparison = {e['id']: {} for e in hist}
        for target in hist + [by_id["lattice"]]:
            target_id = target['id']
            covered = binary_dilation(dots[target_id], structure=disk(3))
            for source in hist:
                sid = source['id']
                if sid == target_id:
                    continue
                count = int(np.count_nonzero(dots[sid] & covered))
                n = int(dots[sid].sum())
                comparison[sid][target_id] = {
                    "within_3px_count": count,
                    "source_dot_count": n,
                    "directional_overlap": count/n if n else None,
                    "binary_spearman_within_footprint": binary_spearman(dots[sid], dots[target_id], n_footprint),
                    "exact_dot_intersection": int(np.count_nonzero(dots[sid] & dots[target_id])),
                }
            if target_id == 'lattice':
                uncovered = int(np.count_nonzero(footprint & ~covered))
                lattice_count = int(dots[target_id].sum())
            del covered

        n = 37654
        min_covered, min_fraction = lower_overlap_bound(uncovered, n)
        relationships = {}
        for a, b in [('GEMSDOE25','GEMSDOE30'), ('GEMSDOE31','GEMSDOE32'),
                     ('GEMSDOE25','GEMSDOE32'), ('GEMSDOE36','GEMSDOE32')]:
            relationships[f"{a}__{b}"] = {
                "a_only": int(np.count_nonzero(dots[a] & ~dots[b])),
                "b_only": int(np.count_nonzero(dots[b] & ~dots[a])),
                "intersection": int(np.count_nonzero(dots[a] & dots[b])),
            }

    # Detect ordinary mid-audit input changes; the pinned hashes are checked
    # both before and after all pixel reads.
    for entry in entries:
        if sha256_file(data_dir / f"{entry['id']}.tif") != entry['sha256']:
            raise ValueError(f"input changed during audit: {entry['id']}")
    transform = template['transform']
    return {
        "audit_version": "apartgemsdoe2-historical-forensics-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256_file(manifest_path),
        "scope": "Nine pinned historical files plus one lattice witness only; incomplete registry. No holdout, score forecast, or slot approval.",
        "grid_source": "unauthenticated owner sample mirror, not the organizer template",
        "grid": {"width": template['width'], "height": template['height'],
                 "crs": str(template['crs']), "transform": list(transform)[:6],
                 "footprint_cells": n_footprint},
        "sample_mirror_canary": {
            "positive_cells": sample_positives,
            "label_positive_cells": label_positives,
            "same_values_as_label_inside_footprint": sample_label_equal,
            "sample_and_label_masks_equal": label_mask_equal,
            "official_sample_described_as_all_absence": True,
            "passes_all_absence_canary": sample_positives == 0,
            "official_description": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format",
        },
        "rasters": raster_reports,
        "directional_comparisons": comparison,
        "exact_dot_relationships": relationships,
        "lattice_feasibility": {
            "radius_pixels": 3, "threshold": 0.70,
            "lattice_dots_in_footprint": lattice_count,
            "footprint_cells": n_footprint,
            "uncovered_footprint_cells": uncovered,
            "budget_assumed": n,
            "minimum_overlapping_dots": min_covered,
            "minimum_overlap_fraction": min_fraction,
            "necessarily_exceeds_70_percent": 10 * min_covered > 7 * n,
            "maximum_budget_that_can_possibly_pass": 10*uncovered//3,
            "assumptions": "Distinct positive dots, all in the same mirrored footprint; lattice is an included registry raster. Geometry is not a DTI score; no sufficiency claim for smaller budgets.",
        },
        "verdict": "negative: no experiment run and no submission authorized",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'evidence/history_manifest.json')
    parser.add_argument('--data', type=Path, default=ROOT / 'data/audit')
    parser.add_argument('--out', type=Path, default=ROOT / 'evidence/history_audit.json')
    args = parser.parse_args()
    try:
        report = run(args.manifest, args.data)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        print(f"Wrote {args.out}")
        print('sample mirror positives:', report['sample_mirror_canary']['positive_cells'])
        print('matches label mirror:', report['sample_mirror_canary']['same_values_as_label_inside_footprint'])
        print('lattice feasibility:', report['lattice_feasibility'])
        print('exact relationships:', report['exact_dot_relationships'])
    except (OSError, KeyError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f'AUDIT FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
