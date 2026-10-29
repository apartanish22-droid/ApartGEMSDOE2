"""Stdlib-unittest checks: official DTI example, exact-vs-bruteforce identity,
and (when competition data is present) the emitted candidate's format gate.

Run: python -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import metric  # noqa: E402


class TestMetric(unittest.TestCase):
    def test_official_worked_example(self) -> None:
        # DrivenData p.967 example: TPw=3.00, FPw=1.89, FNw=2.00 -> DTI 0.60
        self.assertAlmostEqual(metric.dti(3.00, 1.89, 2.00), 0.6027, places=3)
        self.assertEqual(round(metric.dti(3.00, 1.89, 2.00), 2), 0.60)

    def test_kernel_endpoints(self) -> None:
        self.assertEqual(float(metric.kernel(0.0)), 1.0)
        self.assertEqual(float(metric.kernel(3.0)), 0.0)
        self.assertEqual(float(metric.kernel(10.0)), 0.0)
        self.assertAlmostEqual(float(metric.kernel(1.5)), 0.5)

    def test_exact_matches_bruteforce(self) -> None:
        rng = np.random.default_rng(20261027)
        truth = rng.random((24, 24)) > 0.93
        pred = (rng.random((24, 24)) > 0.85).astype(float)
        exact = metric.dti_exact(pred, truth)["dti"]
        brute = metric.dti_bruteforce(pred, truth)["dti"]
        self.assertAlmostEqual(exact, brute, places=9)

    def test_binary_matches_exact(self) -> None:
        rng = np.random.default_rng(7)
        truth = rng.random((20, 20)) > 0.9
        pred = rng.random((20, 20)) > 0.8
        self.assertAlmostEqual(
            metric.dti_binary(pred, truth)["dti"],
            metric.dti_exact(pred.astype(float), truth)["dti"],
            places=9,
        )


class TestCandidateFormat(unittest.TestCase):
    def test_candidate_passes_validator_when_data_present(self) -> None:
        ddir = Path(os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache/gems_data")))
        candidates = sorted((ROOT / "docs" / "downloads").glob("*-zeros.tif"))
        if not (ddir / "sample_submission.tif").exists() or not candidates:
            self.skipTest("competition data or candidate raster not available")
        spec = importlib.util.spec_from_file_location(
            "validate_submission", ROOT / "scripts" / "validate_submission.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        expected_dots = {
            "apartgemsdoe2-ap1-": 37_654,
            "apartgemsdoe2-ap2-": 44_090,
            "apartgemsdoe2-udsr-": 26_173,
            "apartgemsdoe2-trace-": 22_438,
            "apartgemsdoe2-spmd-": 34_500,
        }
        for cand in candidates:
            result = mod.check(cand, ddir / "sample_submission.tif", ddir / "labels.tif")
            self.assertTrue(result["pass"], f"{cand.name}: {result}")
            self.assertEqual(result["outside_footprint_mode"], "all_zero")
            for prefix, n_exp in expected_dots.items():
                if cand.name.startswith(prefix):
                    self.assertEqual(result["positive_pixels_in_footprint"], n_exp)


if __name__ == "__main__":
    unittest.main()
