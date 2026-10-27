"""Bayesian Optimization Surrogate Model for GEMS Fault Discovery.

Treats each weekly submission as an expensive, rate-limited query in a formal search.
With at most 3 scored submissions per week and 1 slot counting for both prize rounds,
the surrogate balances exploration and exploitation using a Gaussian Process
with Matérn 5/2 covariance, evaluates Expected Improvement (EI), formalizes
the submission decision rule, and tracks holdout-to-leaderboard distribution drift.
"""

from __future__ import annotations

import json
import math
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

warnings.filterwarnings("ignore", category=ConvergenceWarning)


class AcquisitionType(str, Enum):
    EXPECTED_IMPROVEMENT = "expected_improvement"
    UPPER_CONFIDENCE_BOUND = "upper_confidence_bound"
    PROBABILITY_OF_IMPROVEMENT = "probability_of_improvement"


@dataclass
class EvaluationRecord:
    """Record of a candidate configuration evaluated on holdout or live leaderboard."""
    candidate_id: str
    timestamp_utc: str
    design_vector: Dict[str, float]  # spacing_px, prob_threshold, scarp_weight, vent_weight, dilation_weight, loss_weight
    holdout_dti: float
    live_score: Optional[float] = None
    submitted: bool = False
    surrogate_predicted_mean: Optional[float] = None
    surrogate_predicted_std: Optional[float] = None
    expected_improvement: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BayesOptSurrogate:
    """Gaussian Process Surrogate over holdout and live evaluation landscapes."""

    FEATURE_KEYS = [
        "spacing_px",
        "prob_threshold",
        "scarp_weight",
        "vent_weight",
        "dilation_weight",
        "loss_boundary_weight",
    ]

    def __init__(
        self,
        exploration_xi: float = 0.01,
        ucb_kappa: float = 1.96,
        ei_submission_threshold: float = 0.005,
        random_state: int = 42,
    ):
        self.exploration_xi = float(exploration_xi)
        self.ucb_kappa = float(ucb_kappa)
        self.ei_submission_threshold = float(ei_submission_threshold)
        self.random_state = random_state

        kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
            length_scale=[1.0] * len(self.FEATURE_KEYS),
            length_scale_bounds=(1e-2, 1e2),
            nu=2.5,
        ) + WhiteKernel(noise_level=1e-4, noise_level_bounds=(1e-6, 1e-1))

        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=2,
            random_state=random_state,
        )
        self.records: List[EvaluationRecord] = []
        self._is_fitted: bool = False

    def vector_from_dict(self, d: Dict[str, float]) -> np.ndarray:
        return np.array([float(d.get(k, 0.0)) for k in self.FEATURE_KEYS], dtype=np.float64)

    def add_evaluation(self, record: EvaluationRecord) -> None:
        self.records.append(record)
        self._is_fitted = False

    def fit(self) -> None:
        """Fit GP on all available holdout evaluations."""
        if len(self.records) < 3:
            # Need at least a few points to fit GP
            self._is_fitted = False
            return

        X = np.array([self.vector_from_dict(r.design_vector) for r in self.records])
        y = np.array([r.holdout_dti for r in self.records])

        self.gp.fit(X, y)
        self._is_fitted = True

    def predict(self, design_vector: Dict[str, float]) -> Tuple[float, float]:
        """Return (mean, std) prediction for a design candidate."""
        if not self._is_fitted:
            self.fit()
        if not self._is_fitted:
            # Fallback if insufficient data
            scores = [r.holdout_dti for r in self.records] if self.records else [0.20]
            return float(np.mean(scores)), float(np.std(scores) if len(scores) > 1 else 0.05)

        x_vec = self.vector_from_dict(design_vector).reshape(1, -1)
        mean, std = self.gp.predict(x_vec, return_std=True)
        return float(mean[0]), float(std[0])

    def expected_improvement(
        self,
        design_vector: Dict[str, float],
        current_best: Optional[float] = None,
    ) -> float:
        """Compute Expected Improvement (EI) for a candidate configuration."""
        if current_best is None:
            if not self.records:
                return 0.05
            current_best = max(r.holdout_dti for r in self.records)

        mean, std = self.predict(design_vector)
        if std < 1e-9:
            return 0.0

        improvement = mean - current_best - self.exploration_xi
        z = improvement / std
        ei = improvement * norm.cdf(z) + std * norm.pdf(z)
        return float(max(0.0, ei))

    def upper_confidence_bound(self, design_vector: Dict[str, float]) -> float:
        """Compute Upper Confidence Bound (UCB)."""
        mean, std = self.predict(design_vector)
        return float(mean + self.ucb_kappa * std)

    def should_submit_decision_rule(
        self,
        candidate_record: EvaluationRecord,
        current_best_holdout: float,
        current_best_live: float = 0.2600,
    ) -> Dict[str, Any]:
        """Formal decision rule on whether to spend an expensive weekly submission slot."""
        ei = self.expected_improvement(candidate_record.design_vector, current_best=current_best_holdout)
        mean, std = self.predict(candidate_record.design_vector)
        beats_holdout_best = candidate_record.holdout_dti > current_best_holdout
        ei_sufficient = ei >= self.ei_submission_threshold
        predicted_live_advantage = mean > current_best_live

        decision = beats_holdout_best and (ei_sufficient or predicted_live_advantage)

        reasons = []
        if not beats_holdout_best:
            reasons.append(f"Holdout DTI ({candidate_record.holdout_dti:.4f}) did not beat best holdout ({current_best_holdout:.4f})")
        if not ei_sufficient:
            reasons.append(f"Expected Improvement ({ei:.5f}) is below threshold ({self.ei_submission_threshold:.5f})")
        if decision:
            reasons.append("Surrogate uncertainty and predicted gain justify spending a rate-limited submission slot.")

        return {
            "spend_slot_recommendation": decision,
            "candidate_id": candidate_record.candidate_id,
            "holdout_dti": candidate_record.holdout_dti,
            "current_best_holdout": current_best_holdout,
            "expected_improvement": ei,
            "surrogate_mean": mean,
            "surrogate_std": std,
            "justification": "; ".join(reasons),
        }

    def detect_distribution_drift(self) -> Dict[str, Any]:
        """Analyze systematic gaps between surrogate predictions and leaderboard returns."""
        submitted_records = [r for r in self.records if r.submitted and r.live_score is not None]
        if len(submitted_records) < 2:
            return {
                "drift_detected": False,
                "sample_count": len(submitted_records),
                "mean_residual": 0.0,
                "message": "Fewer than 2 submitted anchors available to estimate drift.",
            }

        residuals = []
        for r in submitted_records:
            pred_mean, _ = self.predict(r.design_vector)
            residuals.append(r.live_score - pred_mean)

        mean_res = float(np.mean(residuals))
        std_res = float(np.std(residuals))
        # Drift threshold: systematic bias > 0.03 DTI
        is_drift = abs(mean_res) > 0.03

        return {
            "drift_detected": is_drift,
            "sample_count": len(submitted_records),
            "mean_residual": mean_res,
            "std_residual": std_res,
            "message": (
                f"Systematic gap of {mean_res:+.4f} DTI detected between holdout predictions and leaderboard. "
                "Holdout masking distribution has drifted from live test set."
                if is_drift
                else "Holdout predictions and live scores are aligned within expected surrogate uncertainty."
            ),
        }

    def save_ledger(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_evaluations": len(self.records),
            "records": [r.to_dict() for r in self.records],
            "drift_analysis": self.detect_distribution_drift(),
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load_ledger(cls, path: Path) -> BayesOptSurrogate:
        surrogate = cls()
        if not path.is_file():
            return surrogate
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("records", []):
            rec = EvaluationRecord(**item)
            surrogate.add_evaluation(rec)
        surrogate.fit()
        return surrogate
