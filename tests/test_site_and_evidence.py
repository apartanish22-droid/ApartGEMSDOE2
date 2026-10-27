import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import pytest

from build_scorecard import build_rows
from audit_history import run

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.sites = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('a', 'link', 'script'):
            value = attrs.get('href') or attrs.get('src')
            if value: self.links.append(value)
        if tag == 'tr' and 'data-site' in attrs:
            self.sites.append(attrs['data-site'])


def test_scorecard_matches_machine_audit():
    m = json.loads((ROOT/'evidence/history_manifest.json').read_text())
    a = json.loads((ROOT/'evidence/history_audit.json').read_text())
    page = (ROOT/'docs/index.html').read_text()
    assert build_rows(m, a) in page
    parser = Links(); parser.feed(page)
    assert len(parser.sites) == 9 and len(set(parser.sites)) == 9
    assert 'DOWNLOAD A NEW SUBMISSION: NO' in page
    assert 'OK TO SUBMIT: NO' in page


def test_local_page_links_resolve():
    for page in list((ROOT/'docs').rglob('*.html')) + [ROOT/'index.html']:
        parser = Links(); parser.feed(page.read_text())
        for link in parser.links:
            parsed = urlparse(link)
            if parsed.scheme or link.startswith(('#', '//')):
                continue
            target = (page.parent / parsed.path).resolve()
            if target.is_dir(): target = target / 'index.html'
            assert target.is_file(), f'{page}: missing {link}'


def test_every_site_brief_is_negative_and_contains_its_hash():
    entries = json.loads((ROOT/'evidence/history_manifest.json').read_text())['inputs']
    for entry in entries:
        if entry['kind'] != 'historical': continue
        page = (ROOT/'docs/sites'/f"{entry['id']}.html").read_text()
        assert 'DO NOT SUBMIT' in page
        assert 'USER-REPORTED / UNVERIFIED' in page
        assert entry['sha256'] in page
        assert page.count('<tr><td>GEMSDOE') == 8


def test_single_card_negative_and_no_false_candidate():
    card = json.loads((ROOT/'docs/data/run-card.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['raster_sha256'] is None and card['holdout_dti'] is None
    assert card['submission_note'] is None or len(card['submission_note']) <= 140
    assert card['slot_approved'] is False


def test_recorded_audit_replays_if_inputs_available():
    data = ROOT/'data/audit'
    if not (data/'lattice.tif').exists():
        pytest.skip('fetch pinned historical files for full-pixel audit replay')
    observed = run(ROOT/'evidence/history_manifest.json', data)
    recorded = json.loads((ROOT/'evidence/history_audit.json').read_text())
    for key in ('manifest_sha256', 'grid', 'sample_mirror_canary', 'rasters',
                'directional_comparisons', 'exact_dot_relationships', 'lattice_feasibility'):
        assert observed[key] == recorded[key]
