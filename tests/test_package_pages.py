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


def test_real_site_links_resolve_in_both_packaged_layouts(tmp_path):
    from html.parser import HTMLParser
    from urllib.parse import urlsplit
    import shutil

    class LocalLinks(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in ('href', 'src') and value:
                    self.links.append(value)

    shutil.copytree(ROOT/'docs', tmp_path/'docs')
    dest = package(tmp_path)
    for page in dest.rglob('*.html'):
        parser = LocalLinks(); parser.feed(page.read_text())
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            assert not parts.path.startswith('/'), f'Unexpected absolute link: {link}'
            assert (page.parent / parts.path).resolve().exists(), f'{page.relative_to(dest)} -> {link}'
