"""Fail-closed parallel-run gates. These never allocate competition submission slots."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr


def compare_registry(surface, dots, footprint, registry, *, stage="final"):
    """Numerical diagnostic on a provided subset, never a complete registry pass.

    Array inputs cannot establish manifest completeness, freshness, file hashes,
    grid provenance or pre-placement ordering. The primary ``passed`` flag is
    therefore always false; ``provided_subset_passed`` only describes these
    supplied arrays and must not be used as release authorization.
    """
    if stage not in {"surface", "final"}:
        raise ValueError("stage must be surface or final")
    surface, footprint = np.asarray(surface), np.asarray(footprint)
    if footprint.ndim != 2 or not np.isfinite(footprint).all() or not np.isin(footprint, (0, 1)).all():
        raise ValueError("footprint must be a finite binary 2D mask")
    footprint = footprint.astype(bool)
    if stage == "final" and dots is None:
        raise ValueError("final dot check requires dots")
    dots = np.zeros(footprint.shape, bool) if dots is None else np.asarray(dots)
    if surface.shape != footprint.shape or dots.shape != footprint.shape:
        raise ValueError("surface/dots/footprint shape mismatch")
    if not footprint.any() or not np.isfinite(surface[footprint]).all():
        raise ValueError("empty footprint or nonfinite candidate surface")
    if not np.isfinite(dots).all() or not np.isin(dots, (0, 1)).all() or np.any(dots[~footprint] != 0):
        raise ValueError("dots must be binary and inside the footprint")
    dots = dots.astype(bool)
    rows = []
    for name, (other_surface, other_dots) in registry.items():
        other_surface, other_dots = np.asarray(other_surface), np.asarray(other_dots)
        if other_surface.shape != footprint.shape or other_dots.shape != footprint.shape:
            raise ValueError(f"registry shape mismatch: {name}")
        if not np.isfinite(other_dots).all() or not np.isin(other_dots, (0, 1)).all() or np.any(other_dots[~footprint] != 0):
            raise ValueError(f"invalid registry dot mask: {name}")
        other_dots = other_dots.astype(bool)
        rho = None
        if np.isfinite(other_surface[footprint]).all():
            x, y = surface[footprint], other_surface[footprint]
            if np.ptp(x) > 0 and np.ptp(y) > 0:
                rho = float(spearmanr(x, y).statistic)
        overlap = None
        if dots.any() and other_dots.any():
            overlap = float((distance_transform_edt(~other_dots)[dots] <= 3).mean())
        duplicate = (rho is not None and abs(rho) > .90) or (stage == 'final' and overlap is not None and overlap > .70)
        rows.append(dict(registry=name, spearman=rho, within_3px_fraction=overlap,
                         duplicate=duplicate, measurable=rho is not None and (stage == 'surface' or overlap is not None)))
    subset_passed = bool(rows) and (stage == 'surface' or bool(dots.any())) and all(r['measurable'] and not r['duplicate'] for r in rows)
    return dict(stage=stage, rule="conservative |rho|>0.90 OR directional overlap>0.70; no density exemptions",
                comparisons=rows, provided_subset_passed=subset_passed, registry_complete_verified=False,
                passed=False, stop=True)


REQUIRED_VALIDATOR_CHECKS = frozenset({
    "single_band", "finite", "range_0_1", "crs_match", "shape_match", "transform_match",
})


def _valid_holdout(result):
    """Reject missing provenance and malformed evidence rather than guessing defaults."""
    if not isinstance(result, dict):
        return False
    try:
        ci = result.get("ci95", [])
        dti = result["dti"]
        n = result["n_withheld_positives"]
        return bool(
            isinstance(result.get("evaluator_version"), str)
            and result["evaluator_version"].strip()
            and isinstance(n, int) and not isinstance(n, bool) and n > 0
            and len(ci) == 2 and np.isfinite([dti, *ci]).all()
            and 0 <= ci[0] <= dti <= ci[1] <= 1
        )
    except (KeyError, TypeError, ValueError):
        return False


def promotion_decision(*, lane, surface_check, final_check, canary_aucs,
                       holdout, incumbent, same_evaluation, validator,
                       paired_delta_ci95=None):
    """Return a conservative, currently disabled recommendation.

    These dictionaries are caller assertions, not authenticated evidence. The
    archived shared split, writer and registry audit have unresolved defects;
    no authenticated template, complete registry or independent selector is
    established here. Even favorable-looking assertions must remain negative.
    A future selector must independently verify provenance, matched folds,
    canary coverage, literal uniqueness and weekly-slot policy, rather than
    simply trusting a passed dictionary. No slot is ever used here.
    """
    try:
        aucs = list(canary_aucs)
        canaries_ok = bool(aucs) and all(np.isfinite(a) and 0 <= a <= .90 for a in aucs)
    except (TypeError, ValueError):
        canaries_ok = False
    try:
        paired_win = bool(paired_delta_ci95 is not None
                          and len(paired_delta_ci95) == 2
                          and np.isfinite(paired_delta_ci95).all()
                          and 0 < paired_delta_ci95[0] <= paired_delta_ci95[1] <= 1)
    except (TypeError, ValueError):
        paired_win = False
    holdout_ok = _valid_holdout(holdout) and _valid_holdout(incumbent)
    gates = dict(
        lane=isinstance(lane, str) and bool(lane.strip()),
        surface=isinstance(surface_check, dict) and surface_check.get('stage') == 'surface' and surface_check.get('passed') is True,
        final=isinstance(final_check, dict) and final_check.get('stage') == 'final' and final_check.get('passed') is True,
        canaries=canaries_ok,
        holdout=bool(same_evaluation is True and holdout_ok
                     and holdout['evaluator_version'] == incumbent['evaluator_version']
                     and holdout['n_withheld_positives'] == incumbent['n_withheld_positives']
                     and holdout['dti'] > incumbent['dti']),
        paired_improvement=paired_win,
        format=isinstance(validator, dict)
               and REQUIRED_VALIDATOR_CHECKS.issubset(validator)
               and all(v is True for v in validator.values()),
        # No hash-bound registry/holdout/template provenance or independent
        # slot selector is implemented. Never mistake caller booleans for it.
        independent_evidence_verified=False,
    )
    return dict(gates=gates, verdict='negative',
                assertions_only=True, selector_required=True, slot_used=False)
