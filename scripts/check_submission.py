#!/usr/bin/env python3
"""Read saved bytes against a reference; a local format check never authorizes a slot.

The supplied template may be an owner mirror, not an authenticated organizer
sample. The diagnostic requires both the published outside-null/mask reading
and a stricter whole-array finite [0,1] condition; a failure is not proof of a
portal rejection, and a pass is not proof of acceptance.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from gems32.paths import data_dir  # noqa: E402
from validate_raster import validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geotiff', type=Path, help='GeoTIFF whose saved bytes are checked')
    parser.add_argument('--template', type=Path, default=data_dir() / 'sample_submission.tif')
    parser.add_argument('--template-provenance', default='unspecified; not authenticated by this diagnostic')
    parser.add_argument('--strict-finite', action='store_true',
                        help='legacy flag; strict whole-array finite range is always checked')
    args = parser.parse_args()
    try:
        report = validate(args.geotiff, args.template, args.template_provenance)
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(json.dumps({'format_checks_pass': False, 'ok_to_submit': False,
                          'error': f'{type(exc).__name__}: {exc}'}, indent=2))
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report['format_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
