import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import restore_template


def test_readonly_pinned_asset_is_repaired_atomically_and_symlinks_rejected(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.write_bytes(b'upstream pinned bytes')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    (tmp_path / 'registry').mkdir()
    manifest = {'files': [{'id': 'test', 'path': 'src/gems/example.py', 'sha256': digest}]}
    (tmp_path / 'registry/shared-template-pins.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(restore_template, 'ROOT', tmp_path)
    monkeypatch.setattr(restore_template, 'fetch_pin', lambda item, cache: source)
    assert restore_template.restore()[0]['matches_pin']
    dest = tmp_path / '.cache/template-assets/src/gems/example.py'
    assert dest.read_bytes() == source.read_bytes()
    dest.chmod(0o644)
    dest.write_bytes(b'changed')
    dest.chmod(0o444)
    assert restore_template.restore()[0]['matches_pin']
    assert dest.read_bytes() == source.read_bytes()
    dest.unlink()
    dest.symlink_to(source)
    with pytest.raises(ValueError, match='symlink'):
        restore_template.restore()
