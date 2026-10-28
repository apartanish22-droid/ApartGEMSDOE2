import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_reconciles_existing_negative_candidate_and_is_published():
    evidence = (ROOT / 'evidence/current_run_card.json').read_bytes()
    assert evidence == (ROOT / 'docs/data/current_run_card.json').read_bytes()
    card = json.loads(evidence)
    assert card['verdict'] == 'negative' and not card['slot_approved']
    assert card['experiments_run_this_review'] == card['weekly_slots_used_this_review'] == 0
    assert card['holdout_dti'] is None and card['holdout_ci95'] is None
    assert card['raster_sha256'] == 'ce5295029b2f506bed5d49b74432370ba6101d5b810797be78af7502d41828f3'
    assert not card['validator_output']['organizer_template_authenticated']
    assert card['validator_output']['portal_acceptance'] is None
    assert card['correlation_and_overlap_vs_registry']['candidate_surface_spearman'] is None
    assert card['correlation_and_overlap_vs_registry']['candidate_final_dot_overlap'] > 0.70
    assert not card['correlation_and_overlap_vs_registry']['literal_uniqueness_pass']
    assert card['submission_name_status'].startswith('research identifier only')
    assert 0 < len(card['note']) <= 140
    for page in ('docs/index.html', 'docs/executive-summary.html', 'docs/research.html'):
        assert 'data/current_run_card.json' in (ROOT / page).read_text()


def test_legacy_pages_distinguish_archive_from_current_authority():
    ap2 = (ROOT / 'docs/ap2/index.html').read_text()
    assert 'Historical AP2 record — not an approved submission' in ap2
    assert 'SGMC off-catalogue diagnostic' in ap2 and 'not HOLDOUT-DTI' in ap2
    assert 'Note” to paste' not in ap2
    assert 'Historical gate labels — not current authorization' in ap2
    trace = (ROOT / 'docs/trace/index.html').read_text()
    assert 'literal uniqueness failed — DO NOT SUBMIT' in trace
    assert 'generated this session' not in trace
    assert 'not an all-registry pass' in trace


def test_public_feed_never_claims_a_live_drivendata_observation():
    feed = json.loads((ROOT / 'docs/data/source_feed.json').read_text())
    assert feed['leaderboard']['status'] == 'disabled'
    assert feed['leaderboard']['top_public_value'] is None
    assert feed['leaderboard']['last_success_utc'] is None
    assert 'Automatic monitoring disabled' in (ROOT / 'docs/index.html').read_text()
