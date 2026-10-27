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
    assert build_rows(m, a).count('data-site=') == 9
    parser = Links(); parser.feed(page)
    assert len(parser.sites) == 9 and len(set(parser.sites)) == 9
    assert 'Submission download unavailable' in page
    assert 'DO NOT SUBMIT' in page


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
        page = (ROOT/'docs/forensics'/f"{entry['id']}.html").read_text()
        assert 'DO NOT SUBMIT' in page
        assert 'USER-REPORTED / UNVERIFIED' in page
        assert entry['sha256'] in page
        assert page.count('<tr><td>GEMSDOE') == 8


def test_single_card_negative_and_no_false_candidate():
    card = json.loads((ROOT/'docs/data/run_card.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['raster_sha256'] == '973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28'
    assert card['holdout_dti']['point'] == pytest.approx(0.03891061479186361)
    assert 'not independently reproduced' in card['holdout_dti']['label']
    assert card['holdout_dti']['withheld_positives'] == 22232
    assert card['holdout_dti']['ci95'] == pytest.approx([0.028166529159799374, 0.04914995757513441])
    assert card['uniqueness']['registered_lattice_final_dot_overlap'] > 0.70
    assert card['uniqueness']['registered_lattice_overlap_counts'] == {'within_3px': 37548, 'candidate_dots': 37654}
    assert card['validator']['published_format_conservative_local_check'] is False
    assert len(card['submission']['note']) <= 140
    assert card['submission']['slot_approved'] is False


def test_recorded_audit_replays_if_inputs_available():
    data = ROOT/'data/audit'
    if not (data/'lattice.tif').exists():
        pytest.skip('fetch pinned historical files for full-pixel audit replay')
    observed = run(ROOT/'evidence/history_manifest.json', data)
    recorded = json.loads((ROOT/'evidence/history_audit.json').read_text())
    for key in ('manifest_sha256', 'grid', 'sample_mirror_canary', 'rasters',
                'directional_comparisons', 'exact_dot_relationships', 'lattice_feasibility'):
        assert observed[key] == recorded[key]


def test_both_site_generators_are_deterministic_and_do_not_clobber_each_other():
    import hashlib
    import subprocess
    import sys
    files = [ROOT/'docs/index.html', ROOT/'docs/executive-summary.html',
             ROOT/'docs/research.html', *sorted((ROOT/'docs/sites').glob('*.html')),
             *sorted((ROOT/'docs/forensics').glob('*.html'))]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    subprocess.run([sys.executable, str(ROOT/'scripts/build_scorecard.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT/'scripts/build_site.py')], check=True, cwd=ROOT)
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def test_long_identifiers_can_wrap_and_mobile_research_is_reachable():
    css = (ROOT/'docs/assets/style.css').read_text()
    assert 'code, .value.small { overflow-wrap:anywhere' in css
    page = (ROOT/'docs/index.html').read_text()
    assert 'href="research.html">Explore the research' in page
    assert 'class="skip-link" href="#main"' in page
