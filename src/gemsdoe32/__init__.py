"""GEMSDOE32: Bayesian Optimization and Geological Discovery System for DOE GEMS Prize."""

__version__ = "0.1.0"

from .metric import compute_dti, compute_dti_components, triangular_kernel, dti_from_counts
from .surrogate import BayesOptSurrogate, EvaluationRecord, AcquisitionType
from .emission import poisson_disk_select, edge_select, score_ordered_dots
from .geology import compute_dilation_tendency, compute_vent_corridor_prior, compute_stepover_stress
from .scarp import extract_scarp_features, compute_profile_curvature
from .losses import MetricShapedBoundaryLoss, CombinedTverskyBoundaryLoss
from .submission import write_submission_geotiff, validate_submission_geotiff

__all__ = [
    "compute_dti",
    "compute_dti_components",
    "triangular_kernel",
    "dti_from_counts",
    "BayesOptSurrogate",
    "EvaluationRecord",
    "AcquisitionType",
    "poisson_disk_select",
    "edge_select",
    "score_ordered_dots",
    "compute_dilation_tendency",
    "compute_vent_corridor_prior",
    "compute_stepover_stress",
    "extract_scarp_features",
    "compute_profile_curvature",
    "MetricShapedBoundaryLoss",
    "CombinedTverskyBoundaryLoss",
    "write_submission_geotiff",
    "validate_submission_geotiff",
]
