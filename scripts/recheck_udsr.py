#!/usr/bin/env python3
"""Read-only UDSR saved-byte/lattice diagnostic. Not a holdout or approval."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage

from fetch_audit_data import sha256_file
from audit_historical import disk

ROOT = Path(__file__).resolve().parents[1]


def verify(candidate: Path, lattice: Path, sample: Path, card: dict, manifest: dict) -> dict:
    pins = {x['id']: x for x in manifest['inputs']}
    for path, expected in ((candidate, card['raster_sha256']),
                           (lattice, pins['lattice']['sha256']),
                           (sample, pins['mirror_sample']['sha256'])):
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f'Missing or hash mismatch: {path}')
    with rasterio.open(candidate) as c, rasterio.open(lattice) as l, rasterio.open(sample) as s:
        if not (c.shape == l.shape == s.shape and c.crs == l.crs == s.crs and c.transform == l.transform == s.transform):
            raise ValueError('Comparison grid mismatch')
        if c.count != 1 or l.count != 1 or s.count != 1:
            raise ValueError('Expected single-band rasters')
        ca, la, sa = c.read(1), l.read(1), s.read(1)
        footprint = np.isfinite(sa) & (s.read_masks(1) != 0)
        cmask, lmask = c.read_masks(1) != 0, l.read_masks(1) != 0
        if not footprint.any():
            raise ValueError('Empty mirror footprint')
        dots = (ca > 0) & np.isfinite(ca) & cmask & footprint
        ref = (la > 0) & np.isfinite(la) & lmask & footprint
        count = int(dots.sum())
        if not count or not ref.any():
            raise ValueError('Empty dot set; overlap undefined')
        near = ndimage.binary_dilation(ref, structure=disk(3))
        n = int(np.count_nonzero(dots & near))
        return {
            'candidate_sha256': sha256_file(candidate), 'lattice_sha256': sha256_file(lattice),
            'mirror_sample_sha256': sha256_file(sample), 'reference_authentication': 'owner mirror only; not organizer-authenticated',
            'comparison_grid_matches_mirror': True, 'shape': list(c.shape), 'crs': str(c.crs),
            'transform': list(c.transform)[:6], 'driver': c.driver, 'bands': c.count,
            'candidate_positive_pixels_inside_mirror': count, 'lattice_positive_pixels_inside_mirror': int(ref.sum()),
            'candidate_dots_within_3px': n, 'overlap_fraction': n/count,
            'literal_overlap_gate_pass': n/count <= 0.70,
            'candidate_finite_inside_mirror': bool(np.isfinite(ca[footprint]).all()),
            'candidate_unmasked_inside_mirror': bool(cmask[footprint].all()),
            'candidate_range_inside_mirror': bool(np.all(np.isfinite(ca[footprint]) & (ca[footprint] >= 0) & (ca[footprint] <= 1))),
            'whole_array_finite_range': bool(np.all(np.isfinite(ca) & (ca >= 0) & (ca <= 1))),
            'outside_null_or_masked': bool(np.all(~np.isfinite(ca[~footprint]) | ~cmask[~footprint])),
            'external_mask_sidecar_present': Path(str(candidate) + '.msk').exists(),
            'portal_acceptance': None,
            'verdict': 'negative',
            'scope': 'Read-only comparison against one pinned raster. No holdout rerun, full-registry pass, authenticated format validation or slot selection.',
        }


def main():
    card = json.loads((ROOT / 'evidence/apartgemsdoe2_run_card_20261027.json').read_text())
    manifest = json.loads((ROOT / 'evidence/history_manifest.json').read_text())
    try:
        result = verify(ROOT / card['artifact_paths']['geotiff'], ROOT / 'data/audit/lattice.tif', ROOT / 'data/audit/mirror_sample.tif', card, manifest)
    except (OSError, ValueError, KeyError) as exc:
        print(f'RECHECK FAILED: {exc}', file=sys.stderr)
        return 1
    result['checked_utc'] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
