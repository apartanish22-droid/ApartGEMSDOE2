from pathlib import Path
import json
import math
import sys

import numpy as np
from scipy import ndimage, stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_historical import binary_spearman, directional_overlap, disk, format_checks, unavoidable_overlap


def test_three_pixel_disk_is_euclidean_and_bounded():
    structure = disk(3)
    assert structure.shape == (7, 7)
    assert structure[3, 0] and structure[3, 6]
    assert structure[1, 1]  # sqrt(8) < 3
    assert not structure[0, 0]
    ref = np.zeros((9, 9), dtype=bool)
    ref[0, 0] = True
    covered = ndimage.binary_dilation(ref, structure=structure)
    assert covered[0, 3] and covered[2, 2]
    assert not covered[3, 3] and not covered[-1, -1]  # no wrapping


def test_exact_binary_spearman_agrees_with_midrank_implementation():
    a = np.array([[1, 0, 1, 0], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=bool)
    b = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 0, 1]], dtype=bool)
    foot = np.array([[1, 1, 1, 1], [1, 0, 1, 1], [1, 1, 1, 1]], dtype=bool)
    expected = stats.spearmanr(a[foot].astype(int), b[foot].astype(int)).statistic
    assert math.isclose(binary_spearman(a, b, foot), expected, abs_tol=1e-14)
    assert binary_spearman(np.zeros_like(a), b, foot) is None
    assert binary_spearman(a, b, np.zeros_like(foot)) is None


def test_directionality_and_counting_bound():
    candidate = np.zeros((3, 3), bool)
    candidate[0, 0] = candidate[1, 1] = True
    covered = np.zeros((3, 3), bool)
    covered[1, 1] = True
    assert directional_overlap(candidate, covered) == (1, 2, 0.5)
    assert directional_overlap(np.zeros((3, 3), bool), covered) == (0, 0, None)
    assert unavoidable_overlap(37654, 6649) > 0.70
    assert math.isclose(unavoidable_overlap(37654, 6649), 0.8234184947150369)
    assert unavoidable_overlap(2, 5) == 0
    assert unavoidable_overlap(0, 5) is None


def test_local_format_check_keeps_mask_and_whole_array_diagnostics_separate():
    grid = {'shape': [2, 2], 'crs': 'EPSG:32611', 'transform': [100, 0, 0, 0, -100, 0], 'bands': 1, 'dtype': 'float32', 'driver': 'GTiff'}
    foot = np.array([[True, True], [False, False]])
    arr = np.array([[0, 1], [-9999, -9999]], dtype=np.float32)
    valid = foot.copy()
    checks = format_checks(arr, valid, grid, grid, foot)
    assert checks['outside_null_or_masked']
    assert checks['all_footprint_finite_in_range']
    assert not checks['whole_array_finite_in_range_diagnostic']
    assert checks['portal_acceptance'] == 'not tested'
    assert checks['epsg32611_and_100m_pixels']
    masked_inside = valid.copy()
    masked_inside[0, 0] = False
    assert not format_checks(arr, masked_inside, grid, grid, foot)['footprint_all_unmasked']
    assert not format_checks(arr, masked_inside, grid, grid, foot)['published_format_conservative_local_check']
    arr[0, 0] = np.nan
    assert not format_checks(arr, valid, grid, grid, foot)['all_footprint_finite_in_range']
    arr[0, 0] = 1.001
    assert not format_checks(arr, valid, grid, grid, foot)['all_footprint_finite_in_range']
    assert not format_checks(arr, valid, {**grid, 'crs': 'EPSG:4326'}, grid, foot)['grid_matches_owner_mirror']


def test_committed_audit_is_scope_limited_and_reproduces_bound():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads((root / 'evidence/historical_audit.json').read_text())
    assert len(audit['sites']) == 9
    assert len(audit['focus_pair_comparisons']) == 72
    assert all(x['duplicate_vs_other_focus_site'] for x in audit['sites'])
    witness = audit['lattice_witness']
    assert witness['uncovered_footprint_pixels'] == 6649
    assert math.isclose(witness['champion_sized_minimum_overlap'], unavoidable_overlap(37654, 6649))
    assert audit['forensics']['gems31_only_pixels'] == 2545
    assert audit['forensics']['gems31_only_at_most_2px_from_catalogue'] == 2545
    assert audit['sample_mirror']['identical_to_labels_in_footprint']
    assert not audit['new_tiff_generated']
