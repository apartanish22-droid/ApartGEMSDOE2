#!/usr/bin/env python3
"""Replay both independent, read-only geometry audits without changing receipts.

This does not run a model, a holdout experiment, or a submission selector. Public
pinned comparison files are cached locally and verified by the audit implementations.
"""
from __future__ import annotations

import json
from audit_historical import ROOT, PINS, audit as audit_history
from audit_parallel_candidate import audit as audit_candidate
from recheck_h2 import recheck as audit_h2


def compare_receipt(name: str, actual: dict, recorded: dict) -> None:
    """Compare all receipt fields except the time of this replay."""
    actual = {k: v for k, v in actual.items() if k != "observed_utc"}
    recorded = {k: v for k, v in recorded.items() if k != "observed_utc"}
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
    ):
        recorded = json.loads((ROOT / "evidence" / name).read_text())
        compare_receipt(name, result, recorded)
    h2_recorded = json.loads((ROOT / "evidence/h2_saved_byte_recheck_20261028.json").read_text())
    compare_receipt("h2_saved_byte_recheck_20261028.json", audit_h2(), h2_recorded)
    print("Read-only audit replays passed; no holdout, model or submission was run.")


if __name__ == "__main__":
    main()
