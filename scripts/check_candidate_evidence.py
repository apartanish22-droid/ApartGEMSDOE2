#!/usr/bin/env python3
"""Run the local evidence selector against the CURRENT automated preflight.

The input JSON is a collection of prospective evidence receipts, not permission
or proof of a weekly slot. Any embedded preflight is ignored. This command does
not generate or submit a raster and returns a negative verdict on missing inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from current_selector import promotion_decision  # noqa: E402
from preflight import inspect  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path, help='JSON containing candidate evidence receipts')
    args = parser.parse_args()
    try:
        evidence = json.loads(args.evidence.read_text())
        if not isinstance(evidence, dict):
            raise ValueError('evidence must be a JSON object')
        allowed = ('lane', 'surface_check', 'final_check', 'canary_aucs', 'holdout',
                   'incumbent', 'same_evaluation', 'validator', 'paired_delta_ci95',
                   'tested_feature_ids')
        payload = {key: evidence[key] for key in allowed if key in evidence}
        # Never trust an authority claim embedded in the supplied receipt.
        result = promotion_decision(**payload, preflight=inspect())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {'verdict': 'negative', 'slot_approved': False,
                  'issues': [f'Cannot evaluate candidate evidence: {type(exc).__name__}: {exc}']}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['verdict'] == 'promote' else 1


if __name__ == '__main__':
    raise SystemExit(main())
