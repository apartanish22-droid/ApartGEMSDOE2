"""Prevent the historic parallel-run scripts from starting an unapproved new run.

The preflight is deliberately fail-closed. A future implementation must verify a
user-assigned lane, budget, complete registry, both uniqueness stages, and the
shared template before it can expose an explicit new-experiment authorization.
"""
from __future__ import annotations

import sys


def require_current_protocol() -> bool:
    # These callers are archived lanes, not a new authorized selector. A future
    # change to preflight must not accidentally resurrect a spent experiment or
    # make a caller-supplied READY flag sufficient for raster emission.
    print(
        "BLOCKED: no new experiment or raster emission is authorized. Archived "
        "lanes spent their budgets; their candidates fail the literal lattice rule "
        "and shared-tool issues remain unresolved. Run scripts/preflight.py for current blockers.",
        file=sys.stderr,
    )
    return False
