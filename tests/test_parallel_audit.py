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
    assert not actual['format_diagnostic']['checks']['reference_zeros_on_its_valid_footprint']
    assert not actual['format_diagnostic']['checks']['outside_null_or_masked']


@pytest.mark.parametrize('script', [
    'scripts/run_experiment.py', 'scripts/run_experiment_oof.py',
    'scripts/build_final.py', 'src/generate_submission.py',
    'scripts/run_trace_experiments.py', 'scripts/emit_trace_deliverable.py',
    'scripts/run_udsr_experiments.py', 'scripts/emit_and_audit_deliverables.py',
    'scripts/run_ap2.py', 'scripts/finalize_ap2.py',
    'scripts/build_rad_scarp_submission.py',
    'scripts/run_h_dil_grav_experiment.py', 'scripts/run_h_mag_edge_slope_experiment.py',
    'scripts/run_h_depth_cond_experiment.py',
    'src/generate_h2_fractal_submission.py',
])
def test_archived_lane_entry_points_stop_before_running(script):
    result = subprocess.run([sys.executable, str(ROOT/script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert ('BLOCKED' in result.stderr or 'STOP: archived parallel lane' in result.stderr)
    assert 'lattice' in result.stderr.lower()


def test_ready_preflight_cannot_unretire_an_unsafe_legacy_runner(monkeypatch):
    import experiment_guard
    import preflight
    monkeypatch.setattr(preflight, 'inspect', lambda: {
        'status': 'READY', 'new_experiment_authorized': True, 'assigned_lane': 'H-TRACE'
    })
    assert not experiment_guard.require_current_protocol(expected_lane='H-TRACE')
    assert not experiment_guard.require_current_protocol()


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
