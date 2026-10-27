"""Read-only format gate; format validity is NOT holdout quality or uniqueness.

Usage: python scripts/validate_tif.py SAMPLE.tif CANDIDATE.tif
Exit 0 only when every format check passes. Never uses assertions (which -O disables).
"""
import argparse
import json
import math
from pathlib import Path


def validate(sample, candidate):
    import numpy as np
    import rasterio

    checks = {}
    with rasterio.open(sample) as ref, rasterio.open(candidate) as src:
        checks['single_band'] = src.count == 1
        checks['crs_match'] = ref.crs is not None and src.crs == ref.crs
        checks['shape_match'] = (src.height, src.width) == (ref.height, ref.width)
        checks['transform_match'] = all(math.isclose(a, b, rel_tol=0, abs_tol=1e-8)
                                        for a, b in zip(src.transform, ref.transform))
        checks['float_dtype'] = src.count == 1 and src.dtypes[0] in ('float32', 'float64')
        checks['not_tiled_multiband'] = src.count == 1
        checks['sample_has_footprint'] = ref.count == 1 and ref.dataset_mask().any()
        if checks['shape_match'] and checks['single_band']:
            footprint = ref.dataset_mask() != 0
            # Masked pixels do not excuse invalid values within the official footprint.
            mask = src.dataset_mask() != 0
            values = src.read(1, masked=False)
            checks['footprint_covered'] = bool(np.all(mask[footprint]))
            checks['finite_inside_footprint'] = bool(np.isfinite(values[footprint]).all())
            checks['range_0_1_inside_footprint'] = bool(np.isfinite(values[footprint]).all() and
                np.all((values[footprint] >= 0) & (values[footprint] <= 1)))
            checks['finite_everywhere'] = bool(np.isfinite(values).all())
            checks['range_0_1_everywhere'] = bool(np.isfinite(values).all() and
                np.all((values >= 0) & (values <= 1)))
        else:
            for key in ('footprint_covered', 'finite_inside_footprint', 'range_0_1_inside_footprint',
                        'finite_everywhere', 'range_0_1_everywhere'):
                checks[key] = False
    return {'sample': str(sample), 'candidate': str(candidate), 'checks': checks,
            'format_valid': all(checks.values()),
            'submission_authorized': False,
            'reason': 'Format alone cannot establish holdout improvement or registry uniqueness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.sample, args.candidate)
    except Exception as exc:
        result = {'format_valid': False, 'submission_authorized': False,
                  'error': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result, indent=2))
    return 0 if result['format_valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
