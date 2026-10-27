#!/usr/bin/env python3
"""Restore hash-pinned upstream tools read-only under ignored data/.

No copied source is committed. These pins intentionally restore only the files
listed in the upstream protocol manifest; additional imports and the cache may
be needed before any evaluator can run. Never treat restoration as authorization
for an experiment, an upload or a private fork of the shared template.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import sys

from fetch_audit_data import fetch_one

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "evidence/shared_tool_pins.json"
DESTINATION = ROOT / "data/shared_template"


def main() -> int:
    try:
        pins = json.loads(PINS.read_text())
        ref = pins['source_commit']
        for entry in pins['inputs']:
            if entry['repo'] != 'buffedlizard55-lab/GEMSDOE24' or entry['ref'] != ref:
                raise ValueError('unexpected upstream repo or ref')
            if not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
                raise ValueError('invalid pinned SHA-256')
            upstream = Path(entry['path'])
            if upstream.is_absolute() or '..' in upstream.parts or not upstream.parts:
                raise ValueError('unsafe path in pins')
            status = fetch_one(entry, DESTINATION / upstream)
            print(f"{upstream}: {status}")
        print('Partial read-only restoration only; the cache, all imports and a lane remain prerequisites.')
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'RESTORE FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
