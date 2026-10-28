#!/usr/bin/env python3
"""Conservative saved-byte diagnostic; it never approves a competition upload.

The shared writer is deliberately unchanged. Its legacy validator ignores raster
masks; use the independent read-back audit here until the upstream defect is fixed.
Passing this diagnostic is not template authentication, score validation, novelty,
portal acceptance, or selector approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems32.paths import data_dir  # noqa: E402
from validate_raster import validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geotiff', type=Path, help='Candidate TIFF to read back')
    parser.add_argument('--template', type=Path, default=data_dir() / 'sample_submission.tif',
                        help='Reference grid; its authenticity is not established by this check')
    # Kept for compatibility with documented commands. The stricter whole-array
    # check is always applied, including when this flag is omitted.
    parser.add_argument('--strict-finite', action='store_true',
                        help='Compatibility flag: strict whole-array checking is always enabled')
    args = parser.parse_args()
    try:
        report = validate(args.geotiff, args.template, 'caller-provided; not authenticated')
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f'VALIDATION FAILED: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    if report['format_checks_pass']:
        print('\n[LOCAL FORMAT CHECK PASSED] Not authorization to submit.', file=sys.stderr)
        return 0
    print('\n[LOCAL FORMAT CHECK FAILED] Do not submit.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
