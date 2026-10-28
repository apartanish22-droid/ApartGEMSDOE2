#!/usr/bin/env python3
"""Measure the literal lattice stop rule and conditional dot-budget bounds.

This read-only forensic diagnostic is not a geological experiment, holdout,
complete-registry audit, authenticated format validation, or submission selector.
The sample and lattice are immutable owner mirrors fetched by fetch_audit_data.py.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.spatial import cKDTree

from audit_history import disk, grid_match, require_self_contained
from fetch_audit_data import checked_entries, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def occupied_block_bound(mask: np.ndarray, height: int, width: int) -> dict:
    """Upper bound on points in mask if any two in one block are too close.

    All translations of a disjoint rectangular partition are tried; the
    tightest count of occupied blocks remains a valid upper bound. This does
    not calculate the maximum independent set or promise the bound is tight.
    """
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or height <= 0 or width <= 0:
        raise ValueError('expected a 2-D mask and positive block dimensions')
    yy, xx = np.nonzero(mask)
    counts = []
    for dy in range(height):
        for dx in range(width):
            # A separate 2-column unique avoids arithmetic-index overflow.
            blocks = np.column_stack(((yy + dy) // height, (xx + dx) // width))
            counts.append(int(np.unique(blocks, axis=0).shape[0]))
    best = min(counts)
    offset = counts.index(best)
    return {
        'block_shape': [height, width],
        'max_within_block_distance_pixels': math.hypot(height - 1, width - 1),
        'occupied_blocks_upper_bound': best,
        'best_offset': [offset // width, offset % width],
        'offset_counts': counts,
    }


def budget_bound(uncovered_upper_bound: int, max_overlap: Fraction = Fraction(7, 10)) -> int:
    """Floor of the necessary budget bound when overlap must be <= 70%."""
    if (isinstance(uncovered_upper_bound, bool) or not isinstance(uncovered_upper_bound, int)
            or uncovered_upper_bound < 0 or not 0 <= max_overlap < 1):
        raise ValueError('invalid uncovered bound or overlap threshold')
    return int(Fraction(uncovered_upper_bound, 1) / (1 - max_overlap))


def bounds(uncovered: np.ndarray) -> dict:
    uncovered = np.asarray(uncovered, dtype=bool)
    if uncovered.ndim != 2:
        raise ValueError('uncovered mask must be 2-D')
    n = int(uncovered.sum())
    two_by_three = occupied_block_bound(uncovered, 2, 3)
    three_by_two = occupied_block_bound(uncovered, 3, 2)
    three_by_three = occupied_block_bound(uncovered, 3, 3)
    # The first pair has diameter sqrt(5)<2.8; the last has diameter
    # sqrt(8)<2.9. Therefore a raster with at least the indicated minimum
    # separation contains at most one dot in each partition block.
    u28 = min(two_by_three['occupied_blocks_upper_bound'], three_by_two['occupied_blocks_upper_bound'])
    u29 = three_by_three['occupied_blocks_upper_bound']
    return {
        'uncovered_cells': n,
        'max_budget_without_spacing_assumption': budget_bound(n),
        'if_minimum_spacing_at_least_2_8_px': {
            'uncovered_dot_upper_bound': u28,
            'max_budget_necessary_not_sufficient': budget_bound(u28),
            'partitions': [two_by_three, three_by_two],
        },
        'if_minimum_spacing_at_least_2_9_px': {
            'uncovered_dot_upper_bound': u29,
            'max_budget_necessary_not_sufficient': budget_bound(u29),
            'partitions': [three_by_three],
        },
    }


def run(data_dir: Path, manifest_path: Path, candidates: list[Path]) -> dict:
    pins = {entry['id']: entry for entry in checked_entries(json.loads(manifest_path.read_text()))}
    inputs = {}
    for name in ('mirror_sample', 'lattice'):
        if name not in pins:
            raise ValueError(f'missing {name} in manifest')
        path = data_dir / f'{name}.tif'
        if not path.is_file() or sha256_file(path) != pins[name]['sha256']:
            raise ValueError(f'missing or hash-mismatched {name}: {path}')
        inputs[name] = path
    initial_hashes = {p: sha256_file(p) for p in [*inputs.values(), *candidates]}
    with rasterio.open(inputs['mirror_sample']) as sample, rasterio.open(inputs['lattice']) as lattice:
        require_self_contained(sample)
        require_self_contained(lattice)
        if sample.count != 1 or lattice.count != 1 or not grid_match(sample, lattice):
            raise ValueError('sample and lattice must be aligned single-band rasters')
        foot = sample.read_masks(1) != 0
        sample_values = sample.read(1)
        lv = lattice.read(1)
        lm = lattice.read_masks(1) != 0
        if (not foot.any() or not np.isfinite(sample_values[foot]).all()
                or not np.isfinite(lv[foot]).all() or not lm[foot].all()
                or not np.isin(lv[foot], (0, 1)).all()):
            raise ValueError('invalid mirror footprint or lattice data')
        lattice_dots = foot & (lv > 0)
        if not lattice_dots.any():
            raise ValueError('empty lattice witness')
        covered = binary_dilation(lattice_dots, structure=disk(3))
        uncovered = foot & ~covered
        result_bounds = bounds(uncovered)
        edge_dist = distance_transform_edt(foot)
        edge_counts = {str(t): int(np.count_nonzero(uncovered & (edge_dist <= t)))
                       for t in (1, 3, 5, 10)}
        results = []
        for path in candidates:
            with rasterio.open(path) as candidate:
                require_self_contained(candidate)
                if candidate.count != 1 or not grid_match(sample, candidate):
                    raise ValueError(f'candidate grid mismatch: {path}')
                arr = candidate.read(1)
                cmask = candidate.read_masks(1) != 0
                valid = np.isfinite(arr[foot])
                if not valid.all() or not cmask[foot].all():
                    raise ValueError(f'candidate has nonfinite or masked values in mirror footprint: {path}')
                if not np.isin(arr[foot], (0, 1)).all():
                    raise ValueError(f'candidate must be binary inside the mirror footprint; continuous probabilities cannot be treated as dots: {path}')
                dots = foot & (arr > 0)
                count = int(dots.sum())
                if not count:
                    raise ValueError(f'empty candidate: {path}')
                near = int(np.count_nonzero(dots & covered))
                coords = np.column_stack(np.nonzero(dots))
                nearest = None
                if 1 < count <= 250_000:
                    nearest = float(cKDTree(coords).query(coords, k=2, workers=1)[0][:, 1].min())
                results.append({
                    'file': str(path), 'sha256': initial_hashes[path], 'dots_in_mirror': count,
                    'dots_within_3px_of_lattice': near, 'fraction_within_3px': near / count,
                    'minimum_dot_spacing_pixels': nearest,
                    'literal_lattice_rule': 'FAIL' if near * 10 > count * 7 else 'NOT DISPROVED BY THIS WITNESS',
                    'all_registry_uniqueness': 'FAIL (lattice witness)' if near * 10 > count * 7 else 'NOT ESTABLISHED',
                    'preplacement_surface_correlation': None,
                })
    if any(sha256_file(p) != h for p, h in initial_hashes.items()):
        raise ValueError('an input changed during the read-only audit')
    return {
        'audit_version': 'apartgems-lattice-bounds-v1',
        'observed_utc': datetime.now(timezone.utc).isoformat(),
        'scope': ('Geometry only. One hash-pinned lattice is a duplicate witness, not the complete registry. '
                  'The sample is an unauthenticated owner mirror. This is not a score, experiment, '
                  'portal validation, or permission to submit.'),
        'sample_sha256': initial_hashes[inputs['mirror_sample']],
        'lattice_sha256': initial_hashes[inputs['lattice']],
        'footprint_cells': int(foot.sum()),
        'lattice_positive_cells': int(lattice_dots.sum()),
        'literal_rule': 'strictly more than 70% of candidate dots within 3 Euclidean pixels is a duplicate',
        'bounds': result_bounds,
        'uncovered_cells_within_footprint_edge_distance_pixels': edge_counts,
        'edge_distance_note': 'Euclidean distance to a zero cell of the mirrored footprint array.',
        'candidates': results,
        'verdict': 'negative',
        'submission_authorized': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/audit')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'evidence/history_manifest.json')
    parser.add_argument('--candidate', type=Path, action='append', default=[])
    parser.add_argument('--out', type=Path, help='optional JSON report; never overwrites an input')
    args = parser.parse_args()
    try:
        if args.out and args.out.resolve() in {p.resolve() for p in [args.manifest, *args.candidate,
                  args.data / 'mirror_sample.tif', args.data / 'lattice.tif']}:
            raise ValueError('report path must not overwrite an input')
        result = run(args.data, args.manifest, args.candidate)
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text)
            print(f'Wrote {args.out}; no submission is authorized.')
        else:
            print(text, end='')
        return 0
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        print(f'FEASIBILITY AUDIT FAILED: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
