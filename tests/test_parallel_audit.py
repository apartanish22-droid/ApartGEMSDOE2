"""Reconcile the archived parallel artifact without running another experiment."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from audit_parallel_ap1 import run
from src.validate_submission import validate_submission

ROOT = Path(__file__).resolve().parents[1]


def test_parallel_raster_readback_if_inputs_available():
    if not (ROOT/'data/audit/lattice.tif').exists():
        pytest.skip('fetch pinned inputs to replay the saved-byte forensic audit')
    actual = run()
    recorded = json.loads((ROOT/'evidence/parallel_ap1_audit.json').read_text())
    for key in ('candidate_sha256', 'candidate_dots_inside', 'directional_comparisons',
                'literal_lattice_duplicate', 'parallel_holdout_arithmetic_only'):
        assert actual[key] == recorded[key]
    assert actual['candidate_dots_inside'] == 37654
    assert actual['directional_comparisons']['lattice']['within_3px_count'] == 37548
    assert actual['literal_lattice_duplicate']
    assert actual['format_diagnostic']['ok_to_submit'] is False
    checks = actual['format_diagnostic']['checks']
    # 31 Oct 2026: the retired check 'reference_zeros_on_its_valid_footprint' required the official sample to be
    # all zeros; the official sample is binary (0/1) inside its footprint. Its replacement must pass on the sample.
    assert 'reference_zeros_on_its_valid_footprint' not in checks
    assert checks['reference_values_in_0_1_inside_footprint'] is True
    assert not checks['outside_null_or_masked']


@pytest.mark.parametrize('script', [
    'scripts/run_experiment.py', 'scripts/run_experiment_oof.py',
    'scripts/build_final.py', 'src/generate_submission.py',
])
def test_archived_lane_entry_points_stop_before_running(script):
    result = subprocess.run([sys.executable, str(ROOT/script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert ('BLOCKED' in result.stderr or 'STOP: archived parallel lane' in result.stderr)
    assert 'lattice' in result.stderr.lower()


def test_legacy_format_check_never_authorizes(tmp_path):
    tif = tmp_path/'candidate.tif'
    grid = tmp_path/'grid.json'
    tr = from_origin(100, 200, 100, 100)
    with rasterio.open(tif, 'w', driver='GTiff', width=2, height=2, count=1,
                       dtype='float32', crs='EPSG:32611', transform=tr) as out:
        out.write(np.zeros((2, 2), dtype='float32'), 1)
    grid.write_text(json.dumps({'crs':'EPSG:32611', 'width':2, 'height':2, 'transform':list(tr)[:6]}))
    result = validate_submission(tif, grid)
    assert result['format_checks_only_passed'] is True
    assert result['ok'] is False and result['submission_authorized'] is False
