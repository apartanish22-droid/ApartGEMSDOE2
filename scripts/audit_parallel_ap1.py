#!/usr/bin/env python3
"""Read back the already-merged parallel AP-1 raster; never train or authorize.

Compares its saved dots with the nine pinned references AND the lattice witness.
The complete registry and final pre-placement surface are not replayed here.
The historical holdout receipt is checked only for arithmetic consistency, not
independently rerun or certified as protocol-compliant.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from audit_history import binary_spearman, disk, grid_match, require_self_contained
from fetch_audit_data import checked_entries, sha256_file
from validate_raster import validate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif'
CANDIDATE_SHA256 = '973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28'


def run(data_dir: Path = ROOT / 'data/audit') -> dict:
    manifest = checked_entries(json.loads((ROOT/'evidence/history_manifest.json').read_text()))
    by_id = {entry['id']: entry for entry in manifest}
    sample_path = data_dir/'mirror_sample.tif'
    if not CANDIDATE.is_file() or sha256_file(CANDIDATE) != CANDIDATE_SHA256:
        raise ValueError('parallel candidate is missing or does not match its recorded SHA-256')
    for entry in manifest:
        p = data_dir/f"{entry['id']}.tif"
        if not p.is_file() or sha256_file(p) != entry['sha256']:
            raise ValueError(f"missing or incorrect pinned input: {entry['id']}")
    diagnostic = validate(CANDIDATE, sample_path, 'unauthenticated owner mirror')
    with rasterio.open(sample_path) as t, rasterio.open(CANDIDATE) as c:
        require_self_contained(t); require_self_contained(c)
        if not grid_match(t, c) or c.count != 1:
            raise ValueError('candidate does not match provisional forensic grid')
        footprint = t.read_masks(1) != 0
        values = c.read(1)
        if not np.isfinite(values[footprint]).all() or not np.isin(values[footprint], (0, 1)).all():
            raise ValueError('binary candidate expected for this dot comparison')
        dots = footprint & (values > 0)
        n_dots, n_foot = int(dots.sum()), int(footprint.sum())
        if not n_dots:
            raise ValueError('empty candidate dot set')
        comparisons = {}
        for entry in manifest:
            if entry['kind'] != 'historical' and entry['id'] != 'lattice':
                continue
            with rasterio.open(data_dir/f"{entry['id']}.tif") as ref:
                require_self_contained(ref)
                if not grid_match(t, ref) or ref.count != 1:
                    raise ValueError(f"reference grid mismatch: {entry['id']}")
                raw = ref.read(1)
                if not np.isin(raw[footprint], (0, 1)).all():
                    raise ValueError(f"non-binary reference: {entry['id']}")
                positive = footprint & np.isfinite(raw) & (raw > 0)
                count = int(np.count_nonzero(dots & binary_dilation(positive, structure=disk(3))))
                comparisons[entry['id']] = {
                    'reference_sha256': entry['sha256'], 'candidate_dots': n_dots,
                    'reference_dots': int(positive.sum()), 'within_3px_count': count,
                    'within_3px_fraction': count / n_dots,
                    'binary_spearman_within_mirror_footprint': binary_spearman(dots, positive, n_foot),
                }
        outside_positive = int(np.count_nonzero(~footprint & np.isfinite(values) & (values > 0)))
    # The JSON contains fold aggregates, not the predictions, features or a rerun.
    exp_path = ROOT/'evidence/experiment_exp2.json'
    exp = json.loads(exp_path.read_text())
    arithmetic = {}
    for key in ('candidate_oof', 'control_champion_foldlocal'):
        saved = exp[key]
        folds = saved['folds'].values()
        tp = sum(f['tp'] for f in folds); fp = sum(f['fp'] for f in folds)
        fn = sum(f['fn'] for f in folds); n = sum(f['n_truth'] for f in folds)
        score = tp/(tp + 0.2*fp + 0.8*fn) if (tp + 0.2*fp + 0.8*fn) else None
        arithmetic[key] = {'reported_pooled_dti': saved['pooled_dti'],
                           'recomputed_from_reported_fold_totals': score,
                           'arithmetic_matches': score is not None and abs(score - saved['pooled_dti']) < 1e-9,
                           'reported_withheld_positive_instances': saved['n_withheld_positives'],
                           'fold_sum_withheld_positive_instances': n,
                           'reported_ci95': saved['ci95'], 'reported_evaluator_version': saved['evaluator_version']}
    if any(not x['arithmetic_matches'] for x in arithmetic.values()):
        raise ValueError('parallel holdout receipt is internally inconsistent')
    if sha256_file(CANDIDATE) != CANDIDATE_SHA256:
        raise ValueError('candidate changed during audit')
    for entry in manifest:
        if sha256_file(data_dir/f"{entry['id']}.tif") != entry['sha256']:
            raise ValueError(f"input changed during audit: {entry['id']}")
    return {
        'audit_version': 'apartgemsdoe2-parallel-ap1-readback-v1',
        'observed_utc': datetime.now(timezone.utc).isoformat(),
        'candidate': str(CANDIDATE.relative_to(ROOT)), 'candidate_sha256': CANDIDATE_SHA256,
        'scope': 'Saved-byte forensic comparisons only; nine focus files and one lattice, not the complete registry. No pre-placement surface or holdout replay.',
        'reference_is_authenticated': False,
        'candidate_dots_inside': n_dots, 'candidate_positive_outside_mirror': outside_positive,
        'comparison_radius_pixels': 3, 'directional_comparisons': comparisons,
        'literal_lattice_duplicate': comparisons['lattice']['within_3px_fraction'] > .70,
        'format_diagnostic': diagnostic,
        'parallel_holdout_receipt_sha256': sha256_file(exp_path),
        'parallel_holdout_arithmetic_only': arithmetic,
        'holdout_limitation': 'Reported fold totals reproduce the archived pooled values. This does not rerun predictions, audit hidden-input leakage or validate the confidence intervals.',
        'verdict': 'negative: stop; lattice fails the literal novelty rule; no submission authorization',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data/audit')
    parser.add_argument('--out', type=Path, default=ROOT/'evidence/parallel_ap1_audit.json')
    args = parser.parse_args()
    try:
        result = run(args.data_dir)
        args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print(f"AP-1: {result['candidate_dots_inside']} dots; {result['directional_comparisons']['lattice']['within_3px_fraction']:.6%} overlap vs lattice; STOP")
        print(f"Wrote {args.out}")
    except (OSError, KeyError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f'PARALLEL AUDIT FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
