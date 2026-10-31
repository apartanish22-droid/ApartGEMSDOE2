"""Consistency checks for the 31 Oct 2026 verdict evidence and page (no competition data needed).

Every assertion reads committed evidence files, so CI can run this without the .cache data directory.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

VER = json.loads((ROOT / "evidence/nine_site_verification_20261031.json").read_text())
PROXY = json.loads((ROOT / "evidence/proxy_controls_20261031.json").read_text())
GATES = json.loads((ROOT / "evidence/gates_s31_20261031.json").read_text())
TABLE = json.loads((ROOT / "evidence/verdict_table_20261031.json").read_text())
HTML = (ROOT / "docs/verdict-20261031.html").read_text()

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
NAN_SITES = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE31"}


def test_user_named_files_match_pinned_dot_sets_and_manifest_hashes():
    named = VER["user_named_variants"]
    assert set(named) == set(FOCUS)
    for site, rec in named.items():
        assert rec["dot_set_identical_to_pinned_copy"] is True, site
        assert rec["sha256_recomputed_matches_manifest"] is True, site
        assert rec["dots"] == VER["files"][site]["dots"], site


def test_nan_encoding_is_exactly_the_five_named_files_and_count_is_fixed():
    named = VER["user_named_variants"]
    nan_sites = {s for s, r in named.items() if r["outside_footprint_encoding"] == "NaN"}
    assert nan_sites == NAN_SITES
    counts = {named[s]["outside_footprint_nan_cells"] for s in nan_sites}
    assert counts == {7111787}
    for s in set(FOCUS) - NAN_SITES:
        assert named[s]["outside_footprint_nan_cells"] == 0, s
        assert named[s]["outside_footprint_encoding"] == "zeros", s


def test_pinned_copies_are_zeros_outside_and_binary():
    for site in FOCUS + ["S31_FAR65", "S31_MIDBAND"]:
        rec = VER["files"][site]
        assert rec["outside_footprint_encoding"] == "zeros", site
        assert rec["outside_footprint_nan_cells"] == 0, site
        assert rec["in_footprint_binary_0_1"] is True, site


def test_gemsdoe32_is_a_strict_subset_of_gemsdoe30_with_catalogue_pruning():
    sm = VER["subset_and_mechanism"]
    assert sm["GEMSDOE32_dots_subset_of_GEMSDOE30"] is True
    assert sm["GEMSDOE32_dots_not_in_GEMSDOE30"] == 0
    removed, total = sm["GEMSDOE30_minus_GEMSDOE32_within_3px_of_catalogue"]
    assert removed == total == 6436
    kept, n32 = sm["GEMSDOE32_dots_kept_within_3px_of_catalogue"]
    assert n32 == 37654 and kept == 2171


def test_lattice_bound_arithmetic():
    geo = VER["lattice_geometry"]
    u = geo["cells_NOT_within_3px_of_lattice"]
    assert u == 6649
    # A file with c covered dots and u uncovered-cell dots passes the 70% rule only if u/(u+c) >= 0.30.
    # The largest total is therefore floor(u / 0.30).
    assert geo["literal_70pct_upper_bound_on_total_dots"] == int(u / 0.30)
    assert geo["literal_70pct_upper_bound_on_total_dots"] == 22163


def test_s31_gate_fails_literal_lattice_rule_and_margin_without_lattice_is_recorded():
    for key in ("S31_far65", "S31_midband"):
        g = GATES["candidates"][key]["G3_registry"]
        assert g["literal_rule_passed"] is False
        assert g["worst_within_3px_fraction"] > 0.70
        assert g["worst_overlap_raster"].startswith(("GEMSDOE24:", "buffedlizard55-lab/13GEMSDOE:"))
        assert g["registry_rasters"] == 511
    far = GATES["candidates"]["S31_far65"]["G3_registry"]
    assert far["worst_within_3px_excluding_space_filling"] < 0.70


def test_proxy_controls_cover_all_nine_sites_and_two_s31_files():
    cands = PROXY["candidates"]
    assert set(FOCUS) <= set(cands)
    assert "S31_far65 (GEMSDOE28 main, 31 Oct)" in cands
    assert "S31_midband (GEMSDOE28 main, 31 Oct)" in cands
    for name, rec in cands.items():
        lo, hi = rec["SGMC_CAL_calibrated_ci95"]
        assert lo <= rec["SGMC_CAL_prevalence_calibrated"] <= hi, name
        assert rec["SGMC_CAL_truth_pixels"] == 62703, name


def test_table_rows_are_all_not_unique_under_literal_rule_and_not_estimable():
    assert len(TABLE["rows"]) == 9
    assert len(TABLE["s31"]) == 2
    for row in TABLE["rows"]:
        assert row["unique_literal"] is False, row["site"]
        assert row["estimate"].startswith("NOT ESTIMABLE"), row["site"]
        assert row["overlap_vs_lattice"] > 0.70, row["site"]
    for row in TABLE["s31"]:
        assert row["gate_literal_pass"] is False


def test_leaderboard_facts_on_the_page_and_no_0_3195_top_claim():
    assert "0.4544" in HTML
    assert "rank #50" in HTML and "kpomazi" in HTML
    assert "0.4413 does not appear" in HTML
    # 0.3195 must never be called the top score on the page.
    assert not re.search(r"0\.3195 is the (highest|top)", HTML)


def test_page_has_verdict_and_executive_summary_at_top():
    head = HTML[: HTML.index("<h2>1. Executive summary")]
    assert "NO FILE IS OK TO DOWNLOAD AND SUBMIT" in head
    table = HTML[HTML.index("<h2>1. Executive summary"): HTML.index("<h2>2. ")]
    for site in FOCUS:
        assert site in table, site
    assert "Estimated score" in table and "OK to download and submit" in table


def test_page_is_deterministic_and_matches_generator():
    import build_verdict_20261031 as b
    assert b.html_page(b.build()) == HTML


def test_site_root_redirects_to_verdict_page():
    root = (ROOT / "index.html").read_text()
    assert "docs/verdict-20261031.html" in root
    assert "docs/verdict-20261031.html" in (ROOT / "docs/index.html").read_text() or \
        "verdict-20261031.html" in (ROOT / "docs/index.html").read_text()


def test_ci_regenerates_verdict_page_before_committed_docs_check():
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "scripts/build_verdict_20261031.py" in ci
    assert ci.index("build_verdict_20261031") < ci.index("git diff --exit-code -- docs")


def test_run_card_hashes_match_files_on_disk():
    import hashlib
    card = json.loads((ROOT / "evidence/run_card_20261031.json").read_text())
    assert card["weekly_submission_slots_used"] == 0
    assert card["candidate_tif_generated"] is False
    for rec in card["outputs"] + card["inputs"] + card["scripts"]:
        assert rec["present"] is True, rec["path"]
        digest = hashlib.sha256((ROOT / rec["path"]).read_bytes()).hexdigest()
        assert digest == rec["sha256"], rec["path"]
