"""Submission artifacts: geometry, range, footprint and the four ways a file can be illegal."""
import numpy as np
import pytest
import rasterio

from gems32 import grid, submission

H, W = 32, 24


def _fake_template(tmp_path):
    """A miniature stand-in for the official grid: same geometry rules, tiny raster."""
    p = tmp_path / "sample_submission.tif"
    meta = dict(driver="GTiff", dtype="float32", count=1, crs="EPSG:32611",
                transform=rasterio.transform.from_origin(243350, 4508550, 100, 100),
                width=W, height=H, nodata=np.nan)
    a = np.full((H, W), np.nan, np.float32)
    a[2:H - 2, 2:W - 2] = 0.0
    with rasterio.open(p, "w", **meta) as d:
        d.write(a, 1)
    return p, a


def test_written_file_is_legal_and_receipt_reproduces(tmp_path):
    tpl, a = _fake_template(tmp_path)
    fp = np.isfinite(a)
    mask = np.zeros((H, W), np.float32)
    mask[5, 5:12] = 1.0
    out = tmp_path / "sub.tif"
    grid.write_submission(mask, tpl, out, footprint=fp, outside="nan")
    with rasterio.open(out) as s:
        got = s.read(1)
        assert s.crs.to_string() == "EPSG:32611"
        assert (s.height, s.width) == (H, W)
        assert s.dtypes[0] == "float32"
    assert got[5, 5] == 1.0
    inside = got[fp]
    assert np.isfinite(inside).all()
    assert inside.min() >= 0.0 and inside.max() <= 1.0
    assert np.isnan(got[~fp]).all()


def test_zeros_variant_has_no_nan_at_all(tmp_path):
    tpl, a = _fake_template(tmp_path)
    fp = np.isfinite(a)
    out = tmp_path / "sub0.tif"
    grid.write_submission(np.zeros((H, W), np.float32), tpl, out, footprint=fp, outside="zero")
    with rasterio.open(out) as s:
        got = s.read(1)
    assert np.isfinite(got).all()
    assert got.min() >= 0.0 and got.max() <= 1.0


def test_non_finite_or_out_of_range_inside_footprint_is_rejected(tmp_path):
    tpl, a = _fake_template(tmp_path)
    fp = np.isfinite(a)
    bad_nan = np.zeros((H, W), np.float32)
    bad_nan[4, 4] = np.nan
    with pytest.raises(AssertionError):
        grid.write_submission(bad_nan, tpl, tmp_path / "x.tif", footprint=fp)
    bad_hi = np.zeros((H, W), np.float32)
    bad_hi[4, 4] = 1.5
    with pytest.raises(AssertionError):
        grid.write_submission(bad_hi, tpl, tmp_path / "y.tif", footprint=fp)
    bad_lo = np.zeros((H, W), np.float32)
    bad_lo[4, 4] = -0.01
    with pytest.raises(AssertionError):
        grid.write_submission(bad_lo, tpl, tmp_path / "z.tif", footprint=fp)


def test_valid_range_mask_matches_the_competition_rule():
    a = np.array([[0.0, 1.0, np.nan], [0.5, -0.001, 1.000001]], np.float32)
    ok = grid.valid_range_mask(a)
    assert ok[0, 0] and ok[0, 1] and ok[1, 0]
    assert not ok[0, 2] and not ok[1, 1] and not ok[1, 2]


def test_shape_mismatch_fails_cleanly_instead_of_raising(tmp_path):
    """Regression: a 1200x1200 file on the 3292x3730 grid crashed with IndexError.

    Found 2026-10-28 in assets/submission.tif. It must return a FAILED report.
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    from gemsdoe32.submission import validate_submission_geotiff

    tpl = tmp_path / "tpl.tif"
    sub = tmp_path / "sub.tif"
    with rasterio.open(tpl, "w", driver="GTiff", width=4, height=3, count=1, dtype="float32",
                       crs="EPSG:32611", transform=from_origin(0, 300, 100, 100), nodata=np.nan) as d:
        d.write(np.ones((3, 4), dtype="float32"), 1)
    with rasterio.open(sub, "w", driver="GTiff", width=2, height=2, count=1, dtype="float32",
                       crs="EPSG:32611", transform=from_origin(0, 300, 100, 100), nodata=np.nan) as d:
        d.write(np.zeros((2, 2), dtype="float32"), 1)
    report = validate_submission_geotiff(sub, tpl, strict_whole_array_finite=True)
    assert report.passed is False
    names = {c.name: c.passed for c in report.checks}
    assert names["dimensions"] is False
    assert names["in_footprint_range"] is False
