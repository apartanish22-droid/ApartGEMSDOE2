from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

from validate_raster import validate


def make(path, data, *, valid=None, internal=True, transform=None, nodata=None, count=1, dtype='float32'):
    options = {'driver': 'GTiff', 'width': data.shape[1], 'height': data.shape[0],
               'count': count, 'dtype': dtype, 'crs': 'EPSG:32611',
               'transform': transform or from_origin(243350, 4508550, 100, 100), 'nodata': nodata}
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=internal):
        with rasterio.open(path, 'w', **options) as dst:
            for band in range(1, count + 1):
                dst.write(data.astype(dtype), band)
            if valid is not None:
                dst.write_mask(valid.astype('uint8') * 255)
    return path


def fixtures(tmp_path):
    valid = np.array([[0, 1, 1], [0, 1, 1], [0, 0, 0]], bool)
    arr = np.zeros(valid.shape, 'float32')
    t = make(tmp_path/'sample.tif', arr, valid=valid)
    return valid, arr, t


def test_valid_internal_mask_still_never_authorizes(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    arr[1, 1] = 1
    c = make(tmp_path/'candidate.tif', arr, valid=valid)
    result = validate(c, t, 'unit test, not organizer')
    assert result['format_checks_pass']
    assert result['strict_whole_array_range_diagnostic']
    assert result['statistics']['outside_not_null_or_masked'] == 0
    assert result['reference']['authentication_verified'] is False
    assert result['ok_to_submit'] is False


def test_outside_nan_allowed_by_published_text_but_strict_diagnostic_fails(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    arr[~valid] = np.nan
    c = make(tmp_path/'candidate.tif', arr, nodata=np.nan)
    result = validate(c, t, 'unit test')
    assert result['checks']['outside_null_or_masked']
    assert not result['checks']['conservative_strict_whole_array_0_1']
    assert not result['format_checks_pass']


def test_unmasked_zeros_outside_and_nonzero_sample_fail(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    arr[1, 1] = 1
    t = make(tmp_path/'bad-template.tif', arr, valid=valid)
    c = make(tmp_path/'candidate.tif', np.zeros_like(arr))
    result = validate(c, t, 'unit test')
    assert not result['checks']['reference_zeros_on_its_valid_footprint']
    assert not result['checks']['outside_null_or_masked']
    assert result['strict_whole_array_range_diagnostic']


def test_external_mask_is_not_single_tiff(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    c = make(tmp_path/'candidate.tif', arr, valid=valid, internal=False)
    result = validate(c, t, 'unit test')
    assert not result['checks']['candidate_self_contained']
    assert not result['format_checks_pass']


def test_nonfinite_out_of_range_inside_and_masked(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    arr[0, 1] = np.nan; arr[0, 2] = 1.01; arr[1, 1] = -0.01
    candidate_mask = valid.copy(); candidate_mask[1, 2] = 0
    c = make(tmp_path/'candidate.tif', arr, valid=candidate_mask)
    result = validate(c, t, 'unit test')
    assert result['statistics']['nonfinite_inside'] == 1
    assert result['statistics']['out_of_range_inside'] == 2
    assert result['statistics']['masked_inside'] == 1
    assert not result['format_checks_pass']


def test_public_cli_reads_masked_saved_bytes_and_never_authorizes(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    arr[1, 1] = 1
    candidate = make(tmp_path/'candidate.tif', arr, nodata=0)
    script = Path(__file__).resolve().parents[1] / 'scripts/check_submission.py'
    result = subprocess.run([sys.executable, str(script), str(candidate), '--template', str(t),
                             '--strict-finite'], capture_output=True, text=True)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert not report['checks']['no_masked_inside']
    assert report['reference']['authentication_verified'] is False
    assert report['ok_to_submit'] is False


def test_grid_and_band_mismatch_fails_without_crashing(tmp_path):
    valid, arr, t = fixtures(tmp_path)
    c = make(tmp_path/'candidate.tif', np.zeros((4, 3), 'float32'), count=2,
             transform=from_origin(1, 2, 100, 100))
    result = validate(c, t, 'unit test')
    assert not result['checks']['shape_matches_reference']
    assert not result['checks']['transform_matches_reference']
    assert not result['checks']['single_band']
    assert result['statistics']['nonfinite_inside'] is None
    assert not result['ok_to_submit']
