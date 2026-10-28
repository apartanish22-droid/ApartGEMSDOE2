"""Technical diagnostic must not bless a sheared or non-self-contained raster."""
import sys
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_downloads as audit_module


def write(path, *, transform, data=None, external_mask=False):
    data = np.array([[1, 0], [0, 0]], dtype='float32') if data is None else data
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=not external_mask):
        with rasterio.open(path, 'w', driver='GTiff', width=2, height=2, count=1,
                           dtype='float32', crs='EPSG:32611', transform=transform) as ds:
            ds.write(data, 1)
            if external_mask:
                ds.write_mask(np.full((2, 2), 255, dtype='uint8'))


def setup_grid(monkeypatch, tmp_path):
    monkeypatch.setattr(audit_module, 'ROOT', tmp_path)
    monkeypatch.setattr(audit_module, 'W', 2)
    monkeypatch.setattr(audit_module, 'H', 2)
    return Affine(100, 0, 243350, 0, -100, 4508550)


def test_reject_shear_and_external_mask(monkeypatch, tmp_path):
    t = setup_grid(monkeypatch, tmp_path)
    p = tmp_path/'shear.tif'
    write(p, transform=Affine(t.a, 1, t.c, 0, t.e, t.f))
    assert not audit_module.audit(p)['grid_match']
    p = tmp_path/'masked.tif'
    write(p, transform=t, external_mask=True)
    result = audit_module.audit(p)
    assert not result['self_contained']
    assert result['technical_verdict'] == 'TECHNICAL-FAIL'


def test_nan_and_infinity_are_counted_separately(monkeypatch, tmp_path):
    t = setup_grid(monkeypatch, tmp_path)
    p = tmp_path/'bad.tif'
    write(p, transform=t, data=np.array([[np.nan, np.inf], [0, 1]], dtype='float32'))
    result = audit_module.audit(p)
    assert result['nan_pixels'] == 1 and result['infinite_pixels'] == 1
    assert not result['conservative_whole_array_finite_in_0_1']
    assert result['technical_verdict'] == 'TECHNICAL-FAIL'
