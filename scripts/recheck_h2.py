#!/usr/bin/env python3
"""Re-read the archived H2 demo and compare it with one pinned lattice witness.

No model, new TIFF, holdout or submission is produced. The sample is an owner
mirror, not an authenticated organizer template. The calculation is directional:
the numerator counts candidate dots within a Euclidean 3-pixel disk of lattice
positives inside the mirrored footprint.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from recheck_udsr import verify as verify_lattice
from validate_raster import validate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'assets/gems-h2-fractal-faultzone-20261028T054632Z-8c5870c5.tif'
CANDIDATE_SHA = '5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801'
LATTICE = ROOT / 'data/audit/lattice.tif'
SAMPLE = ROOT / 'data/audit/mirror_sample.tif'
MANIFEST = ROOT / 'evidence/history_manifest.json'


def recheck(candidate=CANDIDATE, lattice=LATTICE, sample=SAMPLE, manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text())
    comparison = verify_lattice(Path(candidate), Path(lattice), Path(sample),
                                {'raster_sha256': CANDIDATE_SHA}, manifest)
    readback = validate(Path(candidate), Path(sample), 'pinned public owner mirror; not organizer-authenticated')
    with rasterio.open(sample) as t, rasterio.open(candidate) as c:
        footprint = t.read_masks(1) != 0
        data = c.read(1)
        valid = c.read_masks(1) != 0
        positive = np.isfinite(data) & (data > 0) & valid
        counts = {
            'mirror_footprint_pixels': int(footprint.sum()),
            'masked_inside_mirror_footprint': int((footprint & ~valid).sum()),
            'positive_inside_mirror_footprint': int((footprint & positive).sum()),
            'positive_outside_mirror_footprint': int((~footprint & positive).sum()),
            'positive_whole_raster': int(positive.sum()),
        }
    return {
        'schema': 'h2-saved-byte-recheck-v1',
        'artifact_type': 'pre-existing synthetic pseudo-feature demo; never a geological submission',
        'pixel_counts': counts,
        'single_lattice_comparison': comparison,
        'saved_byte_validator': readback,
        'holdout_dti': None,
        'full_registry_audit': None,
        'organizer_template_authenticated': False,
        'portal_acceptance': None,
        'verdict': 'negative',
        'scope': 'Read-only audit, not a holdout experiment, score, portal receipt, or complete registry assessment.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='optional JSON receipt; default is stdout')
    args = parser.parse_args()
    try:
        result = recheck()
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text)
        else:
            print(text, end='')
    except (OSError, ValueError, KeyError) as exc:
        print(f'H2 RECHECK FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
