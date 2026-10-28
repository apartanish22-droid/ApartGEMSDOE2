"""Prevent the historic parallel-run scripts from starting an unapproved new run.

The preflight is deliberately fail-closed. A future implementation must verify a
user-assigned lane, budget, complete registry, both uniqueness stages, and the
shared template before it can expose an explicit new-experiment authorization.
"""
from __future__ import annotations

import sys


def require_current_protocol(expected_lane: str | None = None) -> bool:
    # These historical entry points predate the mandatory pre-placement stop,
    # final literal audit and two-hour runtime enforcement. A future READY
    # preflight alone cannot make those runners safe. Keep them retired until
    # they are redesigned around the canonical shared tools and current selector.
    from preflight import inspect

    result = inspect()
    lane = f" ({expected_lane})" if expected_lane else ""
    print(
        f"BLOCKED: no new experiment or raster emission is authorized via archived "
        f"runner{lane} (current preflight: {result.get('status', 'unknown')}). "
        "Its prior budget was spent, and "
        "the AP-1 dots fail the literal registry lattice rule. A new pipeline "
        "must enforce the pre-placement, final-dot and time-budget gates.",
        file=sys.stderr,
    )
    return False
