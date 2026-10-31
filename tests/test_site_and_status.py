from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
sys.path.insert(0, str(ROOT / 'scripts'))
import preflight


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for attr in ('href', 'src'):
            if attr in attrs:
                self.urls.append(attrs[attr])


def test_every_local_site_link_resolves():
    pages = list(DOCS.rglob('*.html'))
    assert len(pages) >= 12
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        for url in parser.urls:
            part = urlsplit(url)
            if part.scheme or part.netloc or not part.path:
                continue
            target = (page.parent / part.path).resolve()
            assert target.exists(), f'{page.relative_to(ROOT)} -> {url}'


def test_site_is_deterministic_and_never_offers_current_submission():
    files = [DOCS/'index.html', DOCS/'executive-summary.html', DOCS/'research.html', *sorted((DOCS/'sites').glob('*.html'))]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    subprocess.run([sys.executable, str(ROOT/'scripts/build_site.py')], check=True, cwd=ROOT)
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    index = (DOCS/'index.html').read_text()
    assert 'Submission download unavailable' in index
    assert 'DO NOT SUBMIT' in index
    assert index.count('USER-REPORTED') == 0 or 'unverified' in index.lower()
    assert 'RESEARCH ONLY' in index
    assert '99.72%' in index and 'DO NOT SUBMIT' in index
    assert 'downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif' in index
    for page in (DOCS/'sites').glob('*.html'):
        text = page.read_text()
        assert 'DO NOT SUBMIT' in text and 'research only' in text
        assert 'Not estimable' in text


def test_site_data_is_not_hidden_by_competition_data_ignore_rule():
    for relative in ('docs/data/source_feed.json', 'docs/data/run_card.json', 'docs/data/historical_audit.json', 'docs/data/parallel_candidate_audit.json', 'docs/data/repo_review_run_card_20261031.json', 'docs/data/preflight.json', 'docs/data/audit_nine_sites_20261030.json'):
        assert (ROOT / relative).is_file()
        # Check ignore rules independently of whether files are already tracked.
        ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-q', relative], cwd=ROOT)
        assert ignored.returncode == 1, f'{relative} must be published with the site'
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', relative], cwd=ROOT, capture_output=True)
        assert tracked.returncode == 0, f'{relative} must be tracked, not only present in a local checkout'


def test_run_card_does_not_invent_measurements_or_approve():
    card = json.loads((ROOT/'evidence/run_card.json').read_text())
    assert card['verdict'] == 'negative'
    audit = json.loads((ROOT/'evidence/parallel_candidate_audit.json').read_text())
    assert card['raster_sha256'] == audit['variants']['zeros']['sha256']
    assert card['holdout_dti']['point'] == audit['parallel_holdout_report']['point']
    assert 'not independently reproduced' in card['holdout_dti']['label']
    assert card['uniqueness']['preplacement_surface_spearman_all_registry'] is None
    assert card['uniqueness']['registered_lattice_final_dot_overlap'] > 0.70
    assert card['submission']['name'] and len(card['submission']['note']) <= 140
    assert not card['submission']['slot_approved']
    assert card['validator']['portal_acceptance'] is None
    assert not card['validator']['outside_null_or_masked']


def test_preflight_never_promotes_in_current_run():
    result = preflight.inspect()
    assert result['status'] == 'BLOCKED'
    assert result['lane_assigned'] is False
    assert result['complete_parallel_registry'] is False
    assert result['candidate'] is None and not result['submission_authorized']
    assert result['lattice_witness']['minimum_overlap'] > .7


def test_latest_review_page_is_explicitly_negative_for_all_nine_sites():
    page = (DOCS / 'repo-review-20261031.html').read_text()
    card = json.loads((ROOT / 'evidence/repo_review_run_card_20261031.json').read_text())
    assert 'DO NOT DOWNLOAD OR SUBMIT A TIFF' in page
    assert 'Not estimable' in page
    for site in ('GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28', 'GEMSDOE30', 'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36'):
        assert f'>{site}<' in page
    assert card['verdict'] == 'negative'
    assert card['holdout_dti'] is None and card['raster_sha256'] is None
    assert card['submission_name'] is None and card['experiments_run_this_review'] == 0
    assert card['weekly_slots_used_this_review'] == 0
