"""Regression tests for the local AP2 validator; no portal acceptance implied."""
import numpy as np
import rasterio
import pytest
from rasterio.transform import from_origin
from scripts.validate_submission import check


def test_nodata_template_and_unmasked_footprint(tmp_path):
    profile = dict(driver='GTiff', height=3, width=3, count=1, dtype='float32',
                   crs='EPSG:32611', transform=from_origin(100, 200, 10, 10))
    def write(name, data, **kw):
        p = tmp_path / name
        with rasterio.open(p, 'w', **(profile | kw)) as ds:
            ds.write(np.asarray(data, dtype='float32'), 1)
        return p
    sample = write('sample.tif', [[-9999, -9999, -9999], [-9999, 0, 0], [-9999, 0, 0]], nodata=-9999)
    labels = write('labels.tif', np.zeros((3, 3)))
    pred = write('pred.tif', [[0, 0, 0], [0, 1, 0], [0, 0, 0]])
    result = check(pred, sample, labels)
    assert result['pass'] and result['footprint_pixels'] == 4
    pred = write('pred.tif', [[0, 0, 0], [0, -9999, 1], [0, 0, 0]], nodata=-9999)
    assert not check(pred, sample, labels)['pass']
    pred = write('pred.tif', [[float('inf'), 0, 0], [0, 1, 0], [0, 0, 0]])
    assert not check(pred, sample, labels)['pass']
    pred = write('pred.tif', [[float('nan'), 0, 0], [0, 1, 0], [0, 0, 0]])
    assert check(pred, sample, labels)['pass']
    shifted = write('labels.tif', np.zeros((3, 3)), transform=from_origin(110, 200, 10, 10))
    with pytest.raises(ValueError, match='Catalogue grid'):
        check(pred, sample, shifted)
