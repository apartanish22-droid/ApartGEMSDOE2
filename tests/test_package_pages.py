from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from package_pages import package


def test_package_has_identical_root_and_legacy_routes(tmp_path):
    source = tmp_path/'docs'; source.mkdir()
    (source/'index.html').write_text('decision')
    (source/'assets').mkdir()
    (source/'assets'/'style.css').write_text('body{}')
    dest = package(tmp_path)
    for path in ('index.html', 'assets/style.css'):
        assert (dest/path).read_bytes() == (dest/'docs'/path).read_bytes() == (source/path).read_bytes()
    (dest/'obsolete').write_text('old')
    package(tmp_path)
    assert not (dest/'obsolete').exists()


def test_package_rejects_symlinked_destination(tmp_path):
    (tmp_path/'docs').mkdir()
    (tmp_path/'.cache').mkdir()
    other = tmp_path/'other'; other.mkdir()
    (tmp_path/'.cache'/'pages-artifact').symlink_to(other, target_is_directory=True)
    with pytest.raises(ValueError, match='Unsafe'):
        package(tmp_path)
    assert other.exists()
