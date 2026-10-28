#!/usr/bin/env python3
"""Read-only, hash-pinned RAD-SCARP saved-byte and lattice recheck.

This does not rerun the model or holdout, authenticate the owner mirror, prove
portal acceptance, audit the full registry, or authorize a weekly slot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from recheck_udsr import verify
from validate_raster import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = 'apartgemsdoe2-rad-scarp-offcatalogue-geothermal-20261028T224529Z-04053573'
ZEROS = ROOT / 'docs/downloads' / f'{BASE}-zeros.tif'
NAN = ROOT / 'docs/downloads' / f'{BASE}-nan.tif'
ZEROS_SHA = 'ce5295029b2f506bed5d49b74432370ba6101d5b810797be78af7502d41828f3'
NAN_SHA = '87ca7f2c430250fa6eab20a8e9ab179e947f6f74c84f13647d19d976be08b954'
LATTICE = ROOT / 'data/audit/lattice.tif'
SAMPLE = ROOT / 'data/audit/mirror_sample.tif'
MANIFEST = ROOT / 'evidence/history_manifest.json'


def recheck(zeros=ZEROS, nan=NAN, lattice=LATTICE, sample=SAMPLE, manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text())
    comparison = verify(Path(zeros), Path(lattice), Path(sample),
                        {'raster_sha256': ZEROS_SHA}, manifest)
    zero_readback = validate(Path(zeros), Path(sample), 'pinned owner mirror; not organizer-authenticated')
    nan_readback = validate(Path(nan), Path(sample), 'pinned owner mirror; not organizer-authenticated')
    if zero_readback['sha256'] != ZEROS_SHA or nan_readback['sha256'] != NAN_SHA:
        raise ValueError('RAD-SCARP saved raster hash differs from the recorded bytes')
    return {
        'schema': 'rad-scarp-saved-byte-recheck-v1',
        'artifact_type': 'pre-existing concurrent RAD-SCARP research raster',
        'single_lattice_comparison': comparison,
        'saved_byte_validator': {'zeros': zero_readback, 'nan': nan_readback},
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
        print(f'RAD-SCARP RECHECK FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
