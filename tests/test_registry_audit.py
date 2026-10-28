from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from gems32.registry_audit import _phi_binary, audit_final_dots, audit_surface


def _write(path: Path, arr: np.ndarray) -> dict:
    meta = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": rasterio.transform.from_origin(243350, 4508550, 100, 100),
    }
    with rasterio.open(path, "w", **meta) as ds:
        ds.write(arr.astype(np.float32), 1)
    return meta


def test_phi_handles_products_larger_than_uint64():
    a = np.zeros(200_000, bool)
    b = np.zeros(200_000, bool)
    a[::2] = True
    b[::3] = True
    rho = _phi_binary(a, b)
    assert rho is not None and np.isfinite(rho)


def test_literal_dense_registry_fails_final_not_surface(tmp_path):
    shape = (20, 20)
    foot = np.ones(shape, bool)
    surface = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    dots = np.zeros(shape, bool)
    dots[::4, ::4] = True
    template = tmp_path / "template.tif"
    _write(template, np.zeros(shape, np.float32))
    dense = tmp_path / "dense.tif"
    _write(dense, np.ones(shape, np.float32))
    manifest = {
        "rasters": [{"repo": "R", "path": "dense.tif", "sha256": "x", "local": "dense.tif"}],
        "n_failed": 0,
    }
    surf = audit_surface(surface, foot, manifest, root=tmp_path, template_tif=template)
    final = audit_final_dots(surface, dots, foot, manifest, root=tmp_path, template_tif=template)
    assert surf["passed"]  # constant surface has no rank-correlation above threshold
    assert not final["passed"]
    assert final["worst_within_3px_fraction"] == 1.0


def test_identical_binary_registry_fails_both_checks(tmp_path):
    shape = (20, 20)
    foot = np.ones(shape, bool)
    dots = np.zeros(shape, bool)
    dots[::3, ::3] = True
    surface = dots.astype(np.float32)
    template = tmp_path / "template.tif"
    _write(template, np.zeros(shape, np.float32))
    same = tmp_path / "same.tif"
    _write(same, surface)
    manifest = {
        "rasters": [{"repo": "R", "path": "same.tif", "sha256": "x", "local": "same.tif"}],
        "n_failed": 0,
    }
    assert not audit_surface(surface, foot, manifest, root=tmp_path, template_tif=template)["passed"]
    result = audit_final_dots(surface, dots, foot, manifest, root=tmp_path, template_tif=template)
    assert not result["passed"]
    assert result["worst_abs_spearman"] > 0.99
    assert result["worst_within_3px_fraction"] == 1.0


def test_legacy_lattice_calibration_must_not_authorize_a_candidate(tmp_path):
    """Document upstream nonliteral behavior, not a protocol exemption.

    The calibrated flag can disagree with the required literal rule. Archived
    callers are blocked; a separate future gate must fail if the literal rule fails.
    """
    shape = (60, 60)
    foot = np.ones(shape, bool)
    template = tmp_path / "template.tif"
    _write(template, np.zeros(shape, np.float32))
    lattice = np.zeros(shape, np.float32)
    lattice[::5, ::5] = 1.0
    _write(tmp_path / "lattice.tif", lattice)
    manifest = {"rasters": [{"repo": "R", "path": "lattice.tif", "sha256": "x", "local": "lattice.tif"}], "n_failed": 0}
    rng = np.random.default_rng(0)
    dots = np.zeros(shape, bool)
    dots[rng.integers(0, 60, 150), rng.integers(0, 60, 150)] = True
    surface = rng.random(shape).astype(np.float32)
    lit = audit_final_dots(surface, dots, foot, manifest, root=tmp_path, template_tif=template)
    cal = audit_final_dots(surface, dots, foot, manifest, root=tmp_path, template_tif=template, space_filling_coverage=0.70)
    assert not lit["passed"]                      # literal rule: random dots are "duplicates" of a lattice
    assert cal["passed"] and not cal["literal_rule_passed"]
    row = cal["comparisons"][0]
    assert row["space_filling"] and row["footprint_coverage_3px"] >= 0.70
    # an exact copy of the lattice is still caught by the rank-correlation arm
    copy = audit_final_dots(lattice, lattice > 0, foot, manifest, root=tmp_path, template_tif=template, space_filling_coverage=0.70)
    assert not copy["passed"]


def test_mass_weighted_guard_blocks_low_value_padding(tmp_path):
    """Padding a copied raster with many near-zero 'novel' dots must not buy uniqueness."""
    shape = (80, 80)
    foot = np.ones(shape, bool)
    template = tmp_path / "template.tif"
    _write(template, np.zeros(shape, np.float32))
    reg = np.zeros(shape, np.float32)
    reg[10:70:3, 20] = 1.0
    reg[10:70:3, 50] = 1.0
    _write(tmp_path / "reg.tif", reg)
    manifest = {"rasters": [{"repo": "R", "path": "reg.tif", "sha256": "x", "local": "reg.tif"}], "n_failed": 0}
    vals = reg.copy()
    pad = np.zeros(shape, bool)
    pad[5:75:4, 70:78:4] = True
    pad[70:78:4, 5:75:4] = True
    vals[pad & (vals == 0)] = 0.001          # tiny-value padding far from the registry dots
    dots = vals > 0
    surface = vals + 1e-6 * np.arange(vals.size, dtype=np.float32).reshape(shape)
    res = audit_final_dots(surface, dots, foot, manifest, root=tmp_path, template_tif=template,
                           space_filling_coverage=0.70, candidate_values=vals)
    row = res["comparisons"][0]
    assert row["within_3px_fraction"] <= 0.70      # count-based overlap is fooled by padding...
    assert row["mass_weighted_within_3px"] > 0.70  # ...the mass-weighted overlap is not
    assert not res["passed"]
