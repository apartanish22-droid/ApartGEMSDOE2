import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import restore_data


def digest(b):
    return hashlib.sha256(b).hexdigest()


def test_streamed_core_is_atomic_and_hash_checked(tmp_path):
    root = tmp_path/'data'; root.mkdir()
    content = b'part-one' + b'part-two'
    entry = {'id': 'training_features', 'repo': 'owner/repo', 'ref': 'abc',
             'dest': 'features.tif', 'parts': ['one', 'two'], 'sha256': digest(content)}
    def stream(repo, ref, path, out):
        out.write({'one': b'part-one', 'two': b'part-two'}[path])
    output = restore_data.restore_core_entry(entry, root, stream=stream)
    assert output.read_bytes() == content
    output.write_bytes(b'keep until a valid download is ready')
    bad = entry | {'sha256': digest(b'not the downloaded parts')}
    with pytest.raises(ValueError, match='Hash mismatch'):
        restore_data.restore_core_entry(bad, root, stream=stream)
    assert output.read_bytes() == b'keep until a valid download is ready'
    assert not list(root.glob('*.partial')) and not list(root.glob('.*.partial'))


def test_reference_restore_includes_lattice_and_rejects_tampering(tmp_path):
    root = tmp_path/'data'; root.mkdir()
    source = tmp_path/'source'; source.write_bytes(b'pin')
    good = {'sha256': digest(b'pin')}
    pins = {'focus': [good | {'site': 'GEMSDOE24'}], 'lattice': good}
    restored = restore_data.restore_reference_pins(root, pins, tmp_path, fetch=lambda p, c: source)
    assert {p.name for p in restored} == {'GEMSDOE24_best.tif', 'LATTICE_r13.tif'}
    assert all(p.read_bytes() == b'pin' for p in restored)
    source.write_bytes(b'tampered')
    with pytest.raises(ValueError, match='Hash mismatch'):
        restore_data.restore_reference_pins(root, pins, tmp_path, fetch=lambda p, c: source)


def test_restore_rejects_unsafe_destination(tmp_path):
    with pytest.raises(ValueError):
        restore_data.safe_destination(tmp_path, '../escape.tif')
    outside = tmp_path/'outside'; outside.mkdir()
    root = tmp_path/'root'; root.mkdir()
    (root/'redirect').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        restore_data.safe_destination(root, 'redirect/evil.tif')
