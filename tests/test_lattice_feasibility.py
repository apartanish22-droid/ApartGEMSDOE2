"""The lattice bound is a geometric impossibility proof, not a DTI score."""
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import pytest

from audit_lattice_feasibility import bounds, budget_bound, occupied_block_bound, run
from fetch_audit_data import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def test_block_bound_holds_for_every_small_separated_subset():
    # 3x3 blocks have diameter sqrt(8), strictly below a 2.9 px separation.
    uncovered = np.array([[1, 1, 0, 1], [1, 0, 1, 1], [1, 1, 1, 0]], bool)
    limit = occupied_block_bound(uncovered, 3, 3)['occupied_blocks_upper_bound']
    points = [tuple(p) for p in np.argwhere(uncovered)]
    for n in range(len(points) + 1):
        for subset in combinations(points, n):
            if all(np.hypot(a[0]-b[0], a[1]-b[1]) >= 2.9
                   for a, b in combinations(subset, 2)):
                assert len(subset) <= limit


def test_budget_bound_is_exact_at_seventy_percent():
    assert budget_bound(3) == 10  # 7/10 covered is allowed
    assert budget_bound(6649) == 22163
    assert budget_bound(0) == 0
    with pytest.raises(ValueError):
        budget_bound(-1)
    with pytest.raises(ValueError):
        budget_bound(True)


def test_empty_and_translated_partitions():
    assert bounds(np.zeros((5, 5), bool))['max_budget_without_spacing_assumption'] == 0
    mask = np.zeros((9, 10), bool)
    mask[3:7, 3:9] = True
    result = occupied_block_bound(mask, 2, 3)
    assert result['occupied_blocks_upper_bound'] == min(result['offset_counts'])
    assert len(result['offset_counts']) == 6
    with pytest.raises(ValueError):
        occupied_block_bound(np.zeros((2, 2, 2), bool), 2, 2)


def test_recorded_geometry_and_replay_when_pins_available():
    saved = json.loads((ROOT/'evidence/lattice_bounds_20261028.json').read_text())
    assert saved['bounds']['uncovered_cells'] == 6649
    assert saved['bounds']['max_budget_without_spacing_assumption'] == 22163
    assert saved['bounds']['if_minimum_spacing_at_least_2_8_px']['max_budget_necessary_not_sufficient'] == 9930
    assert saved['bounds']['if_minimum_spacing_at_least_2_9_px']['max_budget_necessary_not_sufficient'] == 8260
    assert saved['uncovered_cells_within_footprint_edge_distance_pixels']['3'] == 6485
    assert saved['submission_authorized'] is False
    assert all(c['literal_lattice_rule'] == 'FAIL' for c in saved['candidates'])
    assert all(c['all_registry_uniqueness'].startswith('FAIL') for c in saved['candidates'])
    data = ROOT/'data/audit'
    if not (data/'lattice.tif').is_file():
        pytest.skip('run scripts/fetch_audit_data.py to replay pinned comparisons')
    candidates = [ROOT / c['file'] for c in saved['candidates']]
    actual = run(data, ROOT/'evidence/history_manifest.json', candidates)
    # The saved invocation used relative candidate paths; normalize for replay.
    for c in actual['candidates']:
        c['file'] = str(Path(c['file']).relative_to(ROOT))
    actual.pop('observed_utc'); saved.pop('observed_utc')
    assert actual == saved


def test_missing_pins_fail_closed(tmp_path):
    with pytest.raises(ValueError, match='missing or hash-mismatched'):
        run(tmp_path, ROOT/'evidence/history_manifest.json', [])


def test_continuous_probabilities_are_not_silently_binarized(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    profile = dict(driver='GTiff', height=4, width=4, count=1, dtype='float32',
                   crs='EPSG:32611', transform=from_origin(0, 400, 100, 100))
    arrays = {'mirror_sample': np.zeros((4, 4), np.float32),
              'lattice': np.zeros((4, 4), np.float32),
              'candidate': np.full((4, 4), .5, np.float32)}
    arrays['lattice'][0, 0] = 1
    for name, arr in arrays.items():
        with rasterio.open(tmp_path/f'{name}.tif', 'w', **profile) as ds:
            ds.write(arr, 1)
    entries = [dict(id=name, repo='test/test', ref='a'*40, path=f'{name}.tif',
                    sha256=sha256_file(tmp_path/f'{name}.tif'))
               for name in ('mirror_sample', 'lattice')]
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'inputs': entries}))
    with pytest.raises(ValueError, match='continuous probabilities cannot be treated as dots'):
        run(tmp_path, manifest, [tmp_path/'candidate.tif'])
