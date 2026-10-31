#!/usr/bin/env python3
"""Read-back diagnostic for a single GeoTIFF; NEVER authorizes an upload.

For future use after an official sample is available. This independent audit is
not a replacement for the shared submission_writer.py, holdout, novelty checks,
or a weekly-slot selector. Its sample-zero check can flag an inconsistency; it
cannot authenticate a downloaded template.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from fetch_audit_data import sha256_file


def validate(candidate: Path, template: Path, template_provenance: str) -> dict:
    sha_before = sha256_file(candidate)
    template_sha_before = sha256_file(template)
    with rasterio.open(template) as t, rasterio.open(candidate) as c:
        if t.count != 1:
            raise ValueError('reference template must have one band')
        t_data = t.read(1)
        footprint = t.read_masks(1) != 0
        if not footprint.any():
            raise ValueError('reference template has an empty valid footprint')
        reference_inside = t_data[footprint]
        shape_matches = c.shape == t.shape
        checks = {
            'reference_is_geotiff': t.driver == 'GTiff',
            'reference_epsg_32611': t.crs is not None and t.crs.to_epsg() == 32611,
            'reference_resolution_100m': bool(abs(t.transform.a) == 100 and abs(t.transform.e) == 100
                                               and t.transform.b == 0 and t.transform.d == 0),
            'reference_float32': t.dtypes == ('float32',),
            'reference_self_contained': all(Path(f).resolve() == template.resolve() for f in t.files),
            # Fixed 2026-10-31: the official sample is binary (0/1) inside its footprint, not all zeros.
            'reference_values_in_0_1_inside_footprint': bool(np.isfinite(reference_inside).all()
                                                             and np.all((reference_inside >= 0) & (reference_inside <= 1))),
            'candidate_is_geotiff': c.driver == 'GTiff',
            'candidate_self_contained': all(Path(f).resolve() == candidate.resolve() for f in c.files),
            'single_band': c.count == 1,
            'float32': c.dtypes == ('float32',),
            'shape_matches_reference': shape_matches,
            'crs_matches_reference': c.crs == t.crs and c.crs is not None,
            'transform_matches_reference': c.transform == t.transform,
        }
        data = c.read(1)
        mask = c.read_masks(1) != 0
        stats = {'nonfinite_inside': None, 'out_of_range_inside': None, 'masked_inside': None,
                 'outside_not_null_or_masked': None, 'whole_array_nonfinite': int(np.count_nonzero(~np.isfinite(data))),
                 'whole_array_out_of_range_finite': int(np.count_nonzero(np.isfinite(data) & ((data < 0) | (data > 1))))}
        if shape_matches:
            inside = data[footprint]
            finite = np.isfinite(inside)
            stats['nonfinite_inside'] = int(np.count_nonzero(~finite))
            stats['out_of_range_inside'] = int(np.count_nonzero(finite & ((inside < 0) | (inside > 1))))
            stats['masked_inside'] = int(np.count_nonzero(footprint & ~mask))
            stats['outside_not_null_or_masked'] = int(np.count_nonzero(~footprint & mask & ~np.isnan(data)))
            checks.update({
                'no_nonfinite_inside': stats['nonfinite_inside'] == 0,
                'inside_values_in_0_1': stats['out_of_range_inside'] == 0,
                'no_masked_inside': stats['masked_inside'] == 0,
                'outside_null_or_masked': stats['outside_not_null_or_masked'] == 0,
            })
        else:
            checks.update({k: False for k in ('no_nonfinite_inside', 'inside_values_in_0_1',
                                               'no_masked_inside', 'outside_null_or_masked')})
        strict_whole_array_pass = bool(np.isfinite(data).all() and np.all((data >= 0) & (data <= 1)))
        # Stricter than the published NaN-outside allowance; guards the reported
        # range error without claiming to reproduce the organizer's validator.
        checks['conservative_strict_whole_array_0_1'] = strict_whole_array_pass
        properties = {
            'width': c.width, 'height': c.height, 'count': c.count, 'dtype': list(c.dtypes),
            'crs': str(c.crs) if c.crs else None, 'transform': list(c.transform)[:6],
            'nodata': str(c.nodata), 'reference_footprint_cells': int(footprint.sum()),
        }
    sha_after = sha256_file(candidate)
    template_sha_after = sha256_file(template)
    checks['candidate_bytes_unchanged_during_audit'] = sha_before == sha_after
    checks['reference_bytes_unchanged_during_audit'] = template_sha_before == template_sha_after
    return {
        'validator_version': 'apartgemsdoe2-readback-v1',
        'file': candidate.name, 'sha256': sha_after,
        'reference': {'file': template.name, 'sha256': template_sha_after, 'provenance_claim': template_provenance,
                      'authentication_verified': False},
        'checks': checks, 'statistics': stats, 'properties': properties,
        'format_checks_pass': all(checks.values()),
        'strict_whole_array_range_diagnostic': strict_whole_array_pass,
        'strict_diagnostic_note': 'The conservative project gate requires all stored cells finite in [0,1], stricter than the published null/NaN-outside allowance. Portal acceptance is unverified.',
        'ok_to_submit': False,
        'decision': 'NOT AUTHORIZED: format checks cannot authenticate the template, establish scientific performance or uniqueness, or approve a weekly slot.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--template-provenance', default='unspecified / unauthenticated')
    parser.add_argument('--out', type=Path, help='write JSON receipt (default: stdout)')
    args = parser.parse_args()
    try:
        result = validate(args.candidate, args.template, args.template_provenance)
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text)
        else:
            print(text, end='')
        return 0 if result['format_checks_pass'] else 1
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f'VALIDATION FAILED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
