"""All deployed HTML local links should stay within the Pages package."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'docs'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        self.refs.extend(value for key, value in attrs if key in {'href', 'src'} and value)


def test_relative_html_links_resolve_inside_deployed_docs():
    root = ROOT.resolve()
    failures = []
    for page in root.rglob('*.html'):
        parser = Links()
        parser.feed(page.read_text())
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or not url.path or url.path.startswith('/'):
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(root):
                failures.append((str(page.relative_to(root)), ref, 'outside Pages package'))
                continue
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                failures.append((str(page.relative_to(root)), ref, 'missing'))
    assert not failures, failures
