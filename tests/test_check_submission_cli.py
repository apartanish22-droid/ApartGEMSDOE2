"""The user-facing checker must fail closed on masks, sidecars, range and grid."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]


def write(path, data, mask=None, *, internal=True, nodata=None, transform=None):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=internal):
        with rasterio.open(path, 'w', driver='GTiff', width=3, height=3, count=1,
                           dtype='float32', crs='EPSG:32611', nodata=nodata,
                           transform=transform or from_origin(100, 300, 100, 100)) as ds:
            ds.write(np.asarray(data, dtype='float32').reshape(3, 3), 1)
            if mask is not None:
                ds.write_mask(np.asarray(mask, dtype='uint8').reshape(3, 3) * 255)


def check(template, candidate, *args):
    result = subprocess.run([sys.executable, str(ROOT/'scripts/check_submission.py'), str(candidate),
                             '--template', str(template), *args], capture_output=True, text=True)
    return result, json.loads(result.stdout) if result.stdout else None


def test_masked_inside_and_external_mask_fail_even_if_values_in_range(tmp_path):
    template, candidate = tmp_path/'template.tif', tmp_path/'candidate.tif'
    write(template, [0]*9)
    write(candidate, [0.5]+[0]*8, nodata=0.5)
    run, report = check(template, candidate, '--strict-finite')
    assert run.returncode != 0
    assert not report['checks']['no_masked_inside']
    assert not report['ok_to_submit']
    mask = [1]*8+[0]
    write(candidate, [0]*9, mask=mask, internal=False)
    run, report = check(template, candidate)
    assert run.returncode != 0
    assert not report['checks']['candidate_self_contained']


def test_good_diagnostic_and_failures(tmp_path):
    template, candidate = tmp_path/'template.tif', tmp_path/'candidate.tif'
    mask = [1]*8+[0]
    write(template, [0]*9, mask=mask)
    write(candidate, [1]+[0]*8, mask=mask)
    run, report = check(template, candidate)
    assert run.returncode == 0
    assert report['format_checks_pass'] and not report['ok_to_submit']
    write(candidate, [1.1]+[0]*8, mask=mask)
    run, report = check(template, candidate)
    assert run.returncode != 0 and not report['checks']['inside_values_in_0_1']
    write(candidate, [0]*9, mask=mask, transform=from_origin(200, 300, 100, 100))
    run, report = check(template, candidate)
    assert run.returncode != 0 and not report['checks']['transform_matches_reference']
    write(candidate, [0]*8+[float('nan')], nodata=float('nan'))
    run, report = check(template, candidate)
    assert run.returncode != 0 and not report['checks']['conservative_strict_whole_array_0_1']
