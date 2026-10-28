#!/usr/bin/env python3
"""Replay independent, read-only geometry audits without changing receipts.

This does not run a model, a holdout experiment, or a submission selector. Public
pinned comparison files are cached locally and verified by the audit implementations.
"""
from __future__ import annotations

import json
from audit_historical import ROOT, PINS, audit as audit_history
from audit_parallel_candidate import audit as audit_candidate
from recheck_trace import inspect_trace
from recheck_rad_scarp import inspect_rad_scarp
from recheck_parallel_three import inspect_parallel_three


def compare_receipt(name: str, actual: dict, recorded: dict) -> None:
    """Compare all receipt fields except the time of this replay."""
    actual = {k: v for k, v in actual.items() if k not in {"observed_utc", "checked_utc"}}
    recorded = {k: v for k, v in recorded.items() if k not in {"observed_utc", "checked_utc"}}
    if actual != recorded:
        missing = object()
        differing = sorted(k for k in actual.keys() | recorded.keys()
                           if actual.get(k, missing) != recorded.get(k, missing))
        raise ValueError(f"{name} differs in {', '.join(differing)}")
    print(f"{name}: all recorded fields match (except observation time)")


def main() -> None:
    cache = ROOT / ".cache/audit"
    pins = json.loads(PINS.read_text())
    for name, result in (
        ("historical_audit.json", audit_history(pins, cache)),
        ("parallel_candidate_audit.json", audit_candidate(cache)),
        ("trace_independent_recheck_20261028.json", inspect_trace()),
        ("rad_scarp_independent_recheck_20261028.json", inspect_rad_scarp()),
        ("parallel_three_independent_recheck_20261028.json", inspect_parallel_three()),
    ):
        recorded = json.loads((ROOT / "evidence" / name).read_text())
        compare_receipt(name, result, recorded)
    print("Read-only audit replays passed; no holdout, model or submission was run.")


if __name__ == "__main__":
    main()
