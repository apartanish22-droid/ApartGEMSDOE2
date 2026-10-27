"""Prevent the historic parallel-run scripts from starting an unapproved new run.

The preflight is deliberately fail-closed. A future implementation must verify a
user-assigned lane, budget, complete registry, both uniqueness stages, and the
shared template before it can expose an explicit new-experiment authorization.
"""
from __future__ import annotations

import sys


def require_current_protocol() -> bool:
    from preflight import inspect

    result = inspect()
    if result.get("status") == "READY" and result.get("new_experiment_authorized") is True:
        return True
    print(
        "BLOCKED: no new experiment or raster emission is authorized. The parallel "
        "run reports its three-experiment budget spent; the AP-1 dots fail the "
        "literal registry lattice rule. See evidence/preflight.json.",
        file=sys.stderr,
    )
    return False
