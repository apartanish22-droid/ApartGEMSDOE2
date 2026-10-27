#!/usr/bin/env python3
"""Demonstrate a pinned upstream format-label ambiguity without modifying it."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from fetch_audit_data import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    pins = json.loads((ROOT/'evidence/shared_tool_pins.json').read_text())
    base = ROOT/'data/shared_template'
    for pin in pins['inputs']:
        file = base/pin['path']
        if not file.is_file() or sha256_file(file) != pin['sha256']:
            print('Shared tool not restored or hash mismatch; run restore_shared_tools.py', file=sys.stderr)
            return 1
    sys.path.insert(0, str(base/'src'))
    from gems.submission import check_variants
    candidate = ROOT/'data/audit/GEMSDOE32.tif'
    sample = ROOT/'data/audit/mirror_sample.tif'
    manifest = json.loads((ROOT/'evidence/history_manifest.json').read_text())
    entries = {e['id']: e for e in manifest['inputs']}
    for id_, p in [('GEMSDOE32', candidate), ('mirror_sample', sample)]:
        if not p.is_file() or sha256_file(p) != entries[id_]['sha256']:
            print(f'Input missing or hash mismatch: {id_}', file=sys.stderr)
            return 1
    result = check_variants(candidate, sample)
    output = {
        'upstream_commit': pins['source_commit'],
        'upstream_file': 'https://github.com/buffedlizard55-lab/GEMSDOE24/blob/2521cb676e172c141a4417e4925b73b6a896c1eb/src/gems/submission.py',
        'candidate_sha256': sha256_file(candidate), 'unauthenticated_reference_sha256': sha256_file(sample),
        'format_valid': result['format_valid'],
        'official_format_compliant': result['official_format_compliant'],
        'submission_authorized': result['submission_authorized'],
        'official_template_grid_and_footprint': result['checks']['official_template_grid_and_footprint'],
        'outside_is_nan_official_text': result['checks']['outside_is_nan_official_text'],
        'finding': 'The official-template-named check uses grid/footprint numbers, not template origin or hash. This owner mirror fails the official all-absence sample canary. format_valid can be true while official_format_compliant is false. This demonstrates a labeling/gating ambiguity, not portal acceptance.',
        'action': 'Do not rely on format_valid alone. Upstream repository is read-only for this account; no private fork or upstream modification was made.',
    }
    (ROOT/'evidence/shared_validator_diagnostic.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
