#!/usr/bin/env python3
"""Refresh the recorded public GitHub HEADs, not scores or submission status."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'evidence/history_manifest.json'
OUTPUT = ROOT / 'docs/data/source_heads.json'


def main() -> int:
    try:
        entries = json.loads(MANIFEST.read_text())['inputs']
        heads = {}
        for entry in entries:
            if entry['kind'] != 'historical':
                continue
            raw = subprocess.check_output(['gh', 'api', f"repos/{entry['repo']}/commits/main"], text=True)
            j = json.loads(raw)
            if not re.fullmatch('[0-9a-f]{40}', j['sha']):
                raise ValueError('GitHub returned an invalid commit ID')
            archive_ref = entry['ref']
            if not re.fullmatch('[0-9a-f]{40}', archive_ref):
                raise ValueError('Historical audit reference is invalid')
            heads[entry['id']] = {
                'repo': entry['repo'], 'sha': j['sha'],
                'commit_utc': j['commit']['committer']['date'],
                'audited_archive_ref': archive_ref,
                'head_differs_from_archive': j['sha'] != archive_ref,
            }
        if len(heads) != 9:
            raise ValueError('expected exactly nine focus-site HEADs')
        output = {'observed_utc': datetime.now(timezone.utc).isoformat(),
                  'scope': 'Observed GitHub repository HEADs and pinned archival references only; not current site scores, audits of newer files, or submission authorization.',
                  'sites': heads}
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=OUTPUT.parent, delete=False) as tmp:
            temp_name = tmp.name
            json.dump(output, tmp, indent=2)
            tmp.write('\n')
        Path(temp_name).replace(OUTPUT)
        print(f'Wrote {OUTPUT}; no scores were fetched.')
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f'HEAD REFRESH FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
