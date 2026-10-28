"""Regression tests for the standalone diagnostic, not a promotion gate."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

spec = importlib.util.spec_from_file_location("standalone_validator", Path(__file__).resolve().parents[1] / "scripts/validate_submission.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write(path, values, *, nodata=None, transform=None, driver="GTiff"):
    with rasterio.open(path, "w", driver=driver, width=3, height=3, count=1,
                       dtype="float32", crs="EPSG:32611",
                       transform=transform or from_origin(100, 300, 100, 100), nodata=nodata) as ds:
        ds.write(np.asarray(values, dtype="float32").reshape(3, 3), 1)


def test_masked_in_range_nodata_cannot_pass(tmp_path):
    sample, labels, candidate = (tmp_path / x for x in ("sample.tif", "labels.tif", "candidate.tif"))
    write(sample, [0]*9)
    write(labels, [0]*9)
    write(candidate, [1, 0.5] + [0]*7, nodata=0.5)
    result = validator.check(candidate, sample, labels)
    assert not result["pass"]
    assert not result["checks"]["in_footprint_unmasked"]


def test_finite_reference_nodata_is_not_footprint(tmp_path):
    sample, labels, candidate = (tmp_path / x for x in ("sample.tif", "labels.tif", "candidate.tif"))
    write(sample, [-9999] + [0]*8, nodata=-9999)
    write(labels, [0]*9)
    write(candidate, [0, 1] + [0]*7)
    assert validator.check(candidate, sample, labels)["footprint_pixels"] == 8


def test_wrong_catalogue_grid_fails_closed(tmp_path):
    sample, labels, candidate = (tmp_path / x for x in ("sample.tif", "labels.tif", "candidate.tif"))
    write(sample, [0]*9)
    write(labels, [0]*9, transform=from_origin(200, 300, 100, 100))
    write(candidate, [1] + [0]*8)
    with pytest.raises(ValueError, match="Catalogue grid"):
        validator.check(candidate, sample, labels)


def test_empty_footprint_fails_closed(tmp_path):
    sample, labels, candidate = (tmp_path / x for x in ("sample.tif", "labels.tif", "candidate.tif"))
    write(sample, [-9999]*9, nodata=-9999)
    write(labels, [0]*9)
    write(candidate, [1] + [0]*8)
    with pytest.raises(ValueError, match="empty"):
        validator.check(candidate, sample, labels)
