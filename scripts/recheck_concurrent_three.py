#!/usr/bin/env python3
"""Re-read three pre-existing concurrent TIFFs against one pinned lattice.

This is a saved-byte audit, not a model, holdout rerun, full registry review,
portal receipt, or weekly-slot selection. The reference is an owner mirror.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from recheck_udsr import verify
from validate_raster import validate

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'data/audit/mirror_sample.tif'
LATTICE = ROOT / 'data/audit/lattice.tif'
MANIFEST = ROOT / 'evidence/history_manifest.json'
FILES = {
    'H-DIL-GRAV': ('gemsdoe32-h-dil-grav-dilate-x-gravlow-top37654-20261028T224631Z-3df650f1-zeros.tif',
                   'a16afeba152e58592b764ad9ddf766c7a256556f03a9fe7d2a52a4b2a3d196f1'),
    'H-MAG-EDGE-SLOPE': ('gemsdoe32-h-mag-edge-slope-mag-x-slope-top37654-20261028T224750Z-2c00c25b-zeros.tif',
                         '69a76559ff303c7604b0e35a0cec3af5fe0f7b742b8720e979857b01618a2d35'),
    'H-DEPTH-COND': ('gemsdoe32-h-depth-cond-conductive-under-thin-cover-top37654-20261028T224836Z-e34db98d-zeros.tif',
                     '621334388274c4a114e5c2a20c26d4e11bc3e3a44efb7ce09fcf483a3e2c49a0'),
}


def recheck(sample=SAMPLE, lattice=LATTICE, manifest_path=MANIFEST, files=FILES):
    manifest = json.loads(Path(manifest_path).read_text())
    reports = {}
    paths = {}
    for name, (filename, expected_sha) in files.items():
        path = ROOT / 'docs/downloads' / filename
        paths[name] = path
        lattice_result = verify(path, Path(lattice), Path(sample),
                                {'raster_sha256': expected_sha}, manifest)
        readback = validate(path, Path(sample), 'pinned owner mirror; not organizer-authenticated')
        if readback['sha256'] != expected_sha:
            raise ValueError(f'{name} hash differs from the recorded raster')
        reports[name] = {'file': filename, 'single_lattice_comparison': lattice_result,
                         'saved_byte_validator': readback, 'verdict': 'negative'}
    with rasterio.open(paths['H-MAG-EDGE-SLOPE']) as mag, rasterio.open(paths['H-DEPTH-COND']) as depth:
        mag_data, depth_data = mag.read(1), depth.read(1)
        m = np.isfinite(mag_data) & (mag_data > 0)
        d = np.isfinite(depth_data) & (depth_data > 0)
        intersection = int(np.count_nonzero(m & d))
        pair = {'mag_positive_cells': int(m.sum()), 'depth_positive_cells': int(d.sum()),
                'intersection_cells': intersection,
                'mag_dotset_is_subset_of_depth': bool(not (m & ~d).any()),
                'dotsets_identical': bool(np.array_equal(m, d)),
                'byte_identical': files['H-MAG-EDGE-SLOPE'][1] == files['H-DEPTH-COND'][1]}
    return {'schema': 'concurrent-three-saved-byte-recheck-v1', 'candidates': reports,
            'mag_depth_pair': pair, 'holdout_dti': None, 'full_registry_audit': None,
            'organizer_template_authenticated': False, 'portal_acceptance': None,
            'verdict': 'negative', 'scope': 'Read-only audit; no experiment or weekly-slot selection.'}


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
        print(f'CONCURRENT RECHECK FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
