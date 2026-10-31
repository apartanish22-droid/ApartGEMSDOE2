#!/usr/bin/env python3
"""Build the 31 Oct 2026 submission verdict page (site entry point) from committed evidence only.

Reads (no network, no competition data):
  evidence/nine_site_verification_20261031.json   byte-level format, dots, overlap matrix, subset facts
  evidence/proxy_controls_20261031.json           same-evaluator HOLDOUT-DTI proxies (SGMC-CAL, hide-recover)
  evidence/gates_s31_20261031.json                full 511-raster literal gate for the two S31 files
  registry/historical-pins.json                   pinned focus files and owner-reported scores

Writes docs/verdict-20261031.html and evidence/verdict_table_20261031.json. CI regenerates and runs
`git diff --exit-code -- docs`, so the page must be deterministic.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
VER = json.loads((ROOT / "evidence/nine_site_verification_20261031.json").read_text())
PROXY = json.loads((ROOT / "evidence/proxy_controls_20261031.json").read_text())
GATES = json.loads((ROOT / "evidence/gates_s31_20261031.json").read_text())
PINS = json.loads((ROOT / "registry/historical-pins.json").read_text())

HTML_OUT = ROOT / "docs/verdict-20261031.html"
JSON_OUT = ROOT / "evidence/verdict_table_20261031.json"

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]
LEADERBOARD_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
PROBLEM_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
RULES_URL = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
DATA_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
GDR_URL = "https://gdr.openei.org/submissions/1391"

# Live leaderboard fetched 31 Oct 2026 (ranks 1-50, drivendata.org). Public-board numbers, not receipts.
LEADERBOARD_FETCH = {
    "fetched": "2026-10-31",
    "top": [("#1", "xiaofanhu", 0.4544), ("#2", "cfld__", 0.3934), ("#3", "Batik Shirt Brothers", 0.3917),
            ("#4", "BrandenKMurray", 0.3860), ("#5", "op01", 0.3642)],
    "rank_50": ("#50", "kpomazi", 0.3195),
    "searched_ranks": "1-50",
    "found_0_4413": False,
}

LATTICE_COV = VER["lattice_geometry"]["lattice_coverage_fraction"]
LATTICE_UNCOVERED = VER["lattice_geometry"]["cells_NOT_within_3px_of_lattice"]
LATTICE_BOUND = VER["lattice_geometry"]["literal_70pct_upper_bound_on_total_dots"]
FOOT = VER["lattice_geometry"]["footprint_cells"]


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.2f}%"


def worst_other(site: str) -> tuple[float, str]:
    row = VER["overlap_matrix_A_within_3px_of_B"][site]
    others = [(row[b], b) for b in FOCUS if b != site]
    val, name = max(others)
    return val, name


def build() -> dict:
    # Owner-reported scores from the pins (strings in the pins; floats here).
    reported = {p["site"]: float(p["reported_value"]) for p in PINS["focus"]}
    named = {s: VER["user_named_variants"][s] for s in FOCUS}
    pin_by_site = {p["site"]: p for p in PINS["focus"]}
    pinned = {s: VER["files"][s] for s in FOCUS}
    # Proxy values: keys in the proxy file are "GEMSDOE24" etc. for the pinned copies.
    proxies = {s: PROXY["candidates"][s] for s in FOCUS if s in PROXY["candidates"]}
    rows = []
    for s in FOCUS:
        worst, vs = worst_other(s)
        pr = proxies.get(s) or {}
        rows.append({
            "site": s,
            "user_named_file": named[s]["file_name"],
            "user_named_encoding": named[s]["outside_footprint_encoding"],
            "user_named_nan_cells": named[s]["outside_footprint_nan_cells"],
            "download_instead": pin_by_site[s]["path"].split("/")[-1],
            "download_source": pin_by_site[s]["source_url"],
            "download_sha256": pinned[s]["sha256"],
            "dots": pinned[s]["dots"],
            "dot_set_same_as_user_named": named[s]["dot_set_identical_to_pinned_copy"],
            "reported_score_owner": reported[s],
            "estimate": "NOT ESTIMABLE (no organizer receipt; no validated model)",
            "proxy_sgmc_cal": pr.get("SGMC_CAL_prevalence_calibrated"),
            "proxy_sgmc_cal_ci95": pr.get("SGMC_CAL_calibrated_ci95"),
            "proxy_hide_recover": pr.get("HOLDOUT_DTI_hide_recover_pooled"),
            "worst_overlap_other_eight": worst,
            "worst_overlap_vs": vs,
            "overlap_vs_lattice": VER["overlap_matrix_A_within_3px_of_B"][s]["LATTICE"],
            "unique_literal": worst <= 0.70 and VER["overlap_matrix_A_within_3px_of_B"][s]["LATTICE"] <= 0.70,
        })
    s31 = []
    for key, label in [("S31_FAR65", "GEMSDOE28 S31 far65 (31 Oct)"),
                       ("S31_MIDBAND", "GEMSDOE28 S31 midband (31 Oct)")]:
        pr_key = "S31_far65 (GEMSDOE28 main, 31 Oct)" if key == "S31_FAR65" else \
            "S31_midband (GEMSDOE28 main, 31 Oct)"
        pr = PROXY["candidates"][pr_key]
        g = GATES["candidates"]["S31_far65" if key == "S31_FAR65" else "S31_midband"]["G3_registry"]
        m = VER["overlap_matrix_A_within_3px_of_B"]
        s31.append({
            "label": label,
            "file": ("gemsdoe28-s31-far65-dispfill-20261031-zeros.tif" if key == "S31_FAR65"
                     else "gemsdoe28-s31-midband-random-budgetfill-20261031-zeros.tif"),
            "source_url": VER["files"][key]["source_url"],
            "sha256": VER["files"][key]["sha256"],
            "dots": pr["dots"],
            "candidate_dots_within_3px_of_gemsdoe32": m[key]["GEMSDOE32"],
            "gemsdoe32_dots_within_3px_of_candidate": m["GEMSDOE32"][key],
            "candidate_dots_not_exact_in_gemsdoe32": (VER["subset_and_mechanism"]["S31_FAR65_dots_not_in_GEMSDOE32"]
                                                      if key == "S31_FAR65" else
                                                      VER["subset_and_mechanism"]["S31_MIDBAND_dots_not_in_GEMSDOE32"]),
            "overlap_vs_lattice": m[key]["LATTICE"],
            "gate_literal_pass": g["literal_rule_passed"],
            "gate_worst_overlap_registry": g["worst_within_3px_fraction"],
            "gate_worst_overlap_registry_raster": g["worst_overlap_raster"],
            "gate_worst_overlap_excluding_lattice": g["worst_within_3px_excluding_space_filling"],
            "gate_worst_overlap_excluding_lattice_raster": g["worst_within_3px_excluding_space_filling_raster"],
            "gate_worst_abs_spearman": g["worst_abs_spearman"],
            "gate_registry_rasters": g["registry_rasters"],
            "proxy_sgmc_cal": pr["SGMC_CAL_prevalence_calibrated"],
            "proxy_sgmc_cal_ci95": pr["SGMC_CAL_calibrated_ci95"],
            "proxy_hide_recover": pr["HOLDOUT_DTI_hide_recover_pooled"],
        })
    # Rank agreement between owner-reported and SGMC-CAL proxy across the nine pinned files (n = 9).
    rep = [reported[s] for s in FOCUS]
    prx = [proxies[s]["SGMC_CAL_prevalence_calibrated"] for s in FOCUS]
    rho, p = spearmanr(rep, prx)
    hr = [proxies[s]["HOLDOUT_DTI_hide_recover_pooled"] for s in FOCUS]
    rho_hr, p_hr = spearmanr(rep, hr)
    null = PROXY["random_null_37654_dots"]
    null_sgmc = [n["SGMC_CAL_prevalence_calibrated"] for n in null]
    return {"rows": rows, "s31": s31, "spearman_reported_vs_sgmc": [rho, p],
            "spearman_reported_vs_hide_recover": [rho_hr, p_hr],
            "null_sgmc": null_sgmc, "null_hide_recover": [n["HOLDOUT_DTI_hide_recover_pooled"] for n in null]}


CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1200px;margin:0 auto;padding:18px;color:#1d2a26;line-height:1.5;background:#fbfbf8}
h1{font-size:1.6rem;margin:.3rem 0}h2{font-size:1.2rem;margin-top:1.8rem;border-bottom:2px solid #d9e2dc;padding-bottom:.25rem}
.banner{background:#7a1c1c;color:#fff;padding:16px 18px;border-radius:8px;font-size:1.05rem}
.banner strong{font-size:1.25rem}
.box{background:#fff;border:1px solid #cfd8d2;border-left:5px solid #173c35;padding:10px 14px;border-radius:6px;margin:10px 0}
.warn{background:#fff4e0;border-left:5px solid #c77700;padding:10px 14px;border-radius:6px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.84rem;margin:.6rem 0}
th,td{border:1px solid #cfd8d2;padding:5px 7px;vertical-align:top;text-align:left}
th{background:#eef3ef}
.no{color:#9b1c1c;font-weight:700}.yes{color:#1d6b33;font-weight:700}
code{font-size:.85em;word-break:break-all}
"""


def esc(x) -> str:
    return escape(str(x))


def html_page(d: dict) -> str:
    rows = d["rows"]
    s31 = d["s31"]
    rho, rp = d["spearman_reported_vs_sgmc"]
    rho_hr, rp_hr = d["spearman_reported_vs_hide_recover"]
    lb = LEADERBOARD_FETCH
    o = []
    o.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
             "<meta name='viewport' content='width=device-width,initial-scale=1'>"
             "<title>31 Oct 2026 submission verdict · ApartGEMS</title>"
             f"<style>{CSS}</style></head><body>")
    o.append("<h1>GEMS submission verdict · 31 Oct 2026</h1>")
    o.append("<div class='banner'><strong>VERDICT: NO FILE IS OK TO DOWNLOAD AND SUBMIT.</strong><br>"
             "No file on the nine GEMSDOE sites, and neither GEMSDOE28 S31 candidate, is both "
             "unique under the literal rule and not a copy of an earlier submission. "
             "No file has a validated estimate in leaderboard units, so none can be shown to beat 0.3195. "
             "Nothing here is an organizer score.</div>")
    o.append("<div class='box'><b>Leaderboard, fetched 31 Oct 2026 (ranks 1–50):</b> the top score is "
             f"<b>{lb['top'][0][2]:.4f}</b> ({lb['top'][0][0]} {esc(lb['top'][0][1])}). "
             f"<b>0.3195 is rank {lb['rank_50'][0]}</b> ({esc(lb['rank_50'][1])}), not the top. "
             "<b>0.4413 does not appear</b> in ranks 1–50. "
             f"Source: <a href='{LEADERBOARD_URL}'>DrivenData leaderboard</a>.</div>")

    o.append("<h2>1. Executive summary: which file, what estimate, is it unique?</h2>")
    o.append("<p><b>Estimate column:</b> there is no organizer receipt for any file, so no leaderboard "
             "estimate is defensible. The proxy column is a <i>HOLDOUT-DTI proxy</i> (evaluator "
             "GEMSDOE32-SGMC-CAL-v3.0, prevalence-calibrated, 95% CI, 62,703 off-catalogue truth pixels; "
             "closest local proxy for new faults, not the organizer target). Random dots of the same "
             "count score about 0.046 on that proxy.</p>")
    o.append("<table><tr><th>Site</th><th>File to download (pinned zeros copy)</th>"
             "<th>User-named file &amp; outside-footprint encoding</th><th>Reported score (owner, unverified)</th>"
             "<th>Estimated score</th><th>Proxy HOLDOUT-DTI (SGMC-CAL)</th>"
             "<th>Unique vs the other 8 (worst 3-px overlap)</th><th>Overlap vs 13GEMSDOE lattice</th>"
             "<th>OK to download and submit?</th></tr>")
    for r in sorted(rows, key=lambda x: -x["reported_score_owner"]):
        uniq = (f"<span class='no'>NO</span> · {pct(r['worst_overlap_other_eight'])} vs {esc(r['worst_overlap_vs'])}"
                if not r["unique_literal"] else f"<span class='yes'>yes</span> ({pct(r['worst_overlap_other_eight'])})")
        ci = r["proxy_sgmc_cal_ci95"]
        proxy = (f"{r['proxy_sgmc_cal']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]" if r["proxy_sgmc_cal"] is not None else "n/a")
        o.append("<tr>"
                 f"<td><b>{r['site']}</b></td>"
                 f"<td><code>{esc(r['download_instead'])}</code><br><small>sha256 {esc(r['download_sha256'][:16])}… · "
                 f"{r['dots']:,} dots · <a href='{esc(r['download_source'])}'>source</a></small></td>"
                 f"<td><code>{esc(r['user_named_file'])}</code><br><small>{esc(r['user_named_encoding'])} outside "
                 f"({r['user_named_nan_cells']:,} NaN cells); dot set identical to pinned copy: "
                 f"{'yes' if r['dot_set_same_as_user_named'] else 'NO'}</small></td>"
                 f"<td>{r['reported_score_owner']:.4f}</td>"
                 f"<td>{esc(r['estimate'])}</td>"
                 f"<td>{proxy}</td>"
                 f"<td>{uniq}</td>"
                 f"<td>{pct(r['overlap_vs_lattice'])} <span class='no'>fails 70%</span></td>"
                 f"<td><span class='no'>NO</span></td></tr>")
    for x in s31:
        o.append("<tr>"
                 f"<td><b>GEMSDOE28 (31 Oct)</b></td>"
                 f"<td><code>{esc(x['file'])}</code><br><small>{x['dots']:,} dots · "
                 f"<a href='{esc(x['source_url'])}'>source</a></small></td>"
                 "<td>n/a (candidate, not a reported score)</td><td>n/a</td>"
                 "<td>NOT ESTIMABLE</td>"
                 f"<td>{x['proxy_sgmc_cal']:.4f} [{x['proxy_sgmc_cal_ci95'][0]:.4f}, {x['proxy_sgmc_cal_ci95'][1]:.4f}]</td>"
                 f"<td><span class='no'>NO</span> · {pct(x['gemsdoe32_dots_within_3px_of_candidate'])} of GEMSDOE32's dots "
                 "within 3 px of this file (copy question, section 2)</td>"
                 f"<td>{pct(x['overlap_vs_lattice'])} <span class='no'>fails 70%</span></td>"
                 "<td><span class='no'>NO</span> under the literal rule; see section 2</td></tr>")
    o.append("</table>")
    o.append("<p><small>Proxy rank agreement with owner-reported scores across the nine pinned files: "
             f"Spearman ρ = {rho:.2f} (p = {rp:.3f}, n = 9) for SGMC-CAL; ρ = {rho_hr:.2f} (p = {rp_hr:.3f}) "
             "for hide-and-recover. The nine files are one family (pairwise overlaps 0.97–1.00), so the agreement may reflect "
             "shared structure rather than predictive power. Owner scores are unverified. This is an observation, not a validation.</small></p>")

    o.append("<h2>2. The two GEMSDOE28 S31 files (dated 31 Oct, labelled 'OK TO SUBMIT' on the owner page)</h2>")
    f65, mid = s31[0], s31[1]
    o.append("<div class='warn'><b>Our verdict: NO, under the literal rule.</b> The owner page says OK to download and "
             "submit. Measured here: "
             f"(a) <b>literal lattice gate fails</b>: {pct(f65['gate_worst_overlap_registry'])} of far65's dots are within 3 px "
             "of the 13GEMSDOE lattice. "
             f"<b>This verdict depends on that lattice decision (section 5).</b> If the lattice were exempt, far65's worst "
             f"non-lattice overlap is {pct(f65['gate_worst_overlap_excluding_lattice'])} "
             f"({esc(f65['gate_worst_overlap_excluding_lattice_raster'].split(':', 1)[-1].split('/')[-1])}), below the 70% line "
             "with a margin of about 2 points. "
             f"(b) <b>Copy question:</b> {pct(f65['gemsdoe32_dots_within_3px_of_candidate'])} of GEMSDOE32's dots lie within 3 px "
             f"of far65, and far65 is {pct(f65['candidate_dots_within_3px_of_gemsdoe32'])} within 3 px of GEMSDOE32. "
             f"{pct(mid['gemsdoe32_dots_within_3px_of_candidate'])} of GEMSDOE32's dots lie within 3 px of a midband dot, which is "
             "close to a copy. Your rule says a copy of a previous submission is not allowed, so this is a judgement "
             "call for you. (c) Proxy: far65 is not better than its parent, and midband is better only within "
             "overlapping confidence intervals.</div>")
    o.append("<table><tr><th>File</th><th>Dots</th><th>GEMSDOE32 dots within 3 px of candidate</th>"
             "<th>Candidate dots within 3 px of GEMSDOE32</th>"
             "<th>Full registry gate (rule: no density exemptions)</th><th>Proxy HOLDOUT-DTI (SGMC-CAL)</th>"
             "<th>Verdict</th></tr>")
    for x in s31:
        o.append("<tr>"
                 f"<td><code>{esc(x['file'])}</code></td><td>{x['dots']:,}</td>"
                 f"<td>{pct(x['gemsdoe32_dots_within_3px_of_candidate'])}</td>"
                 f"<td>{pct(x['candidate_dots_within_3px_of_gemsdoe32'])}"
                 f" ({x['candidate_dots_not_exact_in_gemsdoe32']:,} dots not exact in GEMSDOE32)</td>"
                 f"<td>literal pass: <span class='no'>{x['gate_literal_pass']}</span> · worst overlap "
                 f"{pct(x['gate_worst_overlap_registry'])} (lattice) · excluding lattice "
                 f"{pct(x['gate_worst_overlap_excluding_lattice'])} · worst |ρ| {x['gate_worst_abs_spearman']:.3f}"
                 f" · {x['gate_registry_rasters']} rasters</td>"
                 f"<td>{x['proxy_sgmc_cal']:.4f} [{x['proxy_sgmc_cal_ci95'][0]:.4f}, {x['proxy_sgmc_cal_ci95'][1]:.4f}]</td>"
                 "<td><span class='no'>DO NOT SUBMIT</span></td></tr>")
    o.append("</table>")

    o.append("<h2>3. Why did GEMSDOE32 (0.2778) score highest? (verified mechanism, not a proven score cause)</h2>")
    sm = VER["subset_and_mechanism"]
    rem = sm["GEMSDOE30_minus_GEMSDOE32_within_3px_of_catalogue"]
    kept = sm["GEMSDOE32_dots_kept_within_3px_of_catalogue"]
    o.append("<ul>"
             "<li><b>Verified (bytes):</b> GEMSDOE32's best file (37,654 dots, binary 0/1 values) is a "
             f"<b>strict subset</b> of GEMSDOE30's file (44,090 dots). The {rem[1]:,} dots removed from GEMSDOE30 are "
             f"<b>{rem[0]:,} of {rem[1]:,} within 3 px of the USGS/INGENIOUS catalogue</b>. Only {kept[0]:,} of GEMSDOE32's "
             f"{kept[1]:,} dots ({100*kept[0]/kept[1]:.1f}%) sit that close.</li>"
             "<li><b>Owner-reported difference:</b> 0.2778 (GEMSDOE32) versus 0.2600 (GEMSDOE30), +0.0178. "
             "Neither is an organizer receipt.</li>"
             "<li><b>Hypothesis (labelled, not measured):</b> the hidden test set is new faults that are <i>not</i> in the "
             "catalogue. Dots that sit on known catalogue faults are then likely false positives, and removing them "
             "reduces false positives on the hidden set. The recall cost of removing them "
             "is not measured here. A receipt-free test: remove catalogue-adjacent dots "
             "from a fixed base and measure the off-catalogue proxy and its recall cost.</li>"
             "<li><b>Why the repo's own holdout does not show it:</b> the hide-and-recover proxy rewards catalogue "
             f"recovery. GEMSDOE32 scores {proxies_hr('GEMSDOE32'):.4f} "
             f"there, below the random-dot null of about {sum(d['null_hide_recover'])/len(d['null_hide_recover']):.3f}. "
             "That proxy is therefore anti-aligned with pruning and cannot rank these files.</li>"
             "</ul>")

    o.append("<h2>4. Why the portal said 'Predicted values must be in range [0, 1]'</h2>")
    o.append("<ul>"
             "<li><b>Verified (bytes):</b> the user-named <code>-nan</code> files for GEMSDOE24, 25, 27, 28 and 31 each carry "
             f"{nan_cells_per_nan_file():,} NaN cells outside the footprint. The user-named files for 30, 32, 33 and 36 carry none. "
             "For all nine sites, the dot set inside the footprint is identical to the pinned zeros copy.</li>"
             "<li><b>Hypothesis:</b> the portal's [0,1] check fails on NaN. That is consistent with the error, "
             "but the portal itself has not been tested from here.</li>"
             "<li><b>Practical fix to try:</b> use the zeros-outside copy of the same dot set (table above). It "
             "satisfies [0,1] and has no NaN.</li>"
             "<li><b>Rule conflict (flag for review):</b> the official rules say data outside the bounds is "
             "'null or nan' (<a href='" + RULES_URL + "'>rules PDF</a>, " + PROBLEM_URL + "). A zeros-outside file is "
             "not literally 'null or nan' outside. Only an organizer answer can settle this; a forum question is the "
             "right channel.</li>"
             "</ul>")

    o.append("<h2>5. Why no dense file can pass the literal uniqueness rule</h2>")
    o.append("<div class='box'>The 13GEMSDOE lattice raster (<code>r13-lattice-s5</code>, 206,895 dots on a 5-px grid, "
             "in the 13GEMSDOE repo) covers "
             f"<b>{100*LATTICE_COV:.2f}%</b> of the {FOOT:,}-cell footprint within 3 px. Only <b>{LATTICE_UNCOVERED:,}</b> "
             "cells lie farther than 3 px from every lattice dot. The 70% rule needs at least 30% of a file's dots to lie "
             "in those cells, and each cell holds at most one dot, so the file has at most 6,649 such dots. Therefore the total "
             "is at most 6,649 / 0.30 = "
             f"<b>{LATTICE_BOUND:,}</b> dots in total. Every file above that size fails the literal rule by construction, "
             "including all nine sites and both S31 files. Sparser files can satisfy the bound. The best sparse record in this repo "
             "(H-SARPU, HOLDOUT-DTI 0.1138 [0.1000, 0.1271], <code>evidence/sarpu_run_card_20261028.json</code>) is well below the bar."
             "</div>"
             "<p><b>Decision needed (for you, not a manual step in the pipeline):</b> does the 13GEMSDOE lattice count as a "
             "'registry raster' under your 70% rule? If it does, the rule cannot be met by any file with more than about "
             "22,000 dots. If it does not, the 37k–52k-dot S31 files pass the overlap test (about 0.68), and the copy question in "
             "section 2 becomes the deciding one. The repo has a null-calibrated option for space-filling rasters "
             "(<code>space_filling_coverage</code>, <code>src/gems32/registry_audit.py</code>); the official rule text does "
             "not provide it, so using it would be a governance choice.</p>")

    o.append("<h2>6. Irregularities flagged for review</h2><ol>"
             "<li><b>Competition data source.</b> The training rasters used by this repo come from third-party GitHub "
             "copies. DrivenData's <a href='" + DATA_URL + "'>data tab</a> is login-walled from this sandbox. The mirrors are "
             "SHA-256 pinned but not organizer-authenticated, so any final check should use an official download from your "
             "own DrivenData account.</li>"
             "<li><b>The 0.3195 framing.</b> 0.3195 is not the highest score. It is rank #50 on the fetched board, and "
             "the repo previously said #48. The repo's 30 Oct table also had stale values for #2–#4.</li>"
             "<li><b>0.4413</b> does not appear in ranks 1–50 of the fetched board.</li>"
             "<li><b>Owner overlap label is imprecise.</b> The GEMSDOE28 S31 page gives 0.6800 as far65's worst overlap against the "
             "nine-site registry. Our nine-site worst for far65 is 67.29% (GEMSDOE27). The 68.00% figure is the full-registry "
             "worst excluding the lattice (GEMSDOE32 h47), a different set. The owner's 0.6688 versus the 0.2778 parent "
             "matches our 66.88%. Our nine-site worst for midband is 68.00%.</li>"
             "<li><b>Owner pages say 'already submitted'.</b> GEMSDOE32's page says its 0.2778 file is already submitted. "
             "No receipt is archived here.</li>"
             "<li><b>Holdout proxy is anti-aligned.</b> On the hide-and-recover evaluator the best reported file scores 0.0045, "
             "below random dots. Its known split defect is that 15,705 of 22,232 withheld positives lie within 15 px of "
             "visible faults.</li>"
             "<li><b>Registry refreshed.</b> <code>registry/focus_registry_manifest.json</code> now lists 511 rasters "
             "(was 489, none removed). The 22 additions are dated 28–31 Oct 2026: GEMSDOE27 (11), GEMSDOE24 (5), "
             "GEMSDOE25 (3) and GEMSDOE28 (3). They enter the uniqueness gate but were not individually scored here.</li>"
             "</ol>")

    o.append("<h2>7. What would produce an OK-to-submit file</h2><ol>"
             "<li>A decision on the lattice rule (section 5), and a decision on whether the portal accepts "
             "zeros-outside files (section 4). Both are governance questions.</li>"
             "<li>Training data from your own DrivenData download, placed in <code>data/</code>, replacing the mirror.</li>"
             "<li>A new method, pre-registered, with a catalogue-free or pruning-aware proxy on the authenticated data and a "
             "paired confidence interval against the same-evaluator baseline. A file that only beats the proxy by "
             "overlapping intervals is not enough.</li>"
             "<li>Full 511-raster gate on the final bytes, and a single format-test submission to see whether the "
             "portal accepts the zeros-outside encoding.</li>"
             "</ol>")

    o.append("<h2>8. Sources and reproduction</h2><ul>"
             f"<li><a href='{PROBLEM_URL}'>DrivenData problem description and submission format</a> (fetched 31 Oct 2026)</li>"
             f"<li><a href='{LEADERBOARD_URL}'>DrivenData leaderboard</a> (ranks 1–50 fetched 31 Oct 2026)</li>"
             f"<li><a href='{RULES_URL}'>Official GEMS Prize rules, NLR, September 2026</a></li>"
             f"<li><a href='{GDR_URL}'>INGENIOUS regional dataset compilation (DOI 10.15121/1881483)</a></li>"
             "<li>Evidence: <code>evidence/nine_site_verification_20261031.json</code>, "
             "<code>evidence/proxy_controls_20261031.json</code>, <code>evidence/gates_s31_20261031.json</code>, "
             "<code>evidence/verdict_table_20261031.json</code>.</li>"
             "<li>Reproduce: <code>scripts/restore_data.py --references-only</code>, "
             "<code>scripts/verify_nine_sites_20261031.py</code>, <code>scripts/proxy_controls_20261031.py</code>, "
             "<code>scripts/gate_candidates.py</code>, <code>scripts/build_verdict_20261031.py</code>.</li>"
             "</ul>")
    o.append("</body></html>")
    return "".join(o)


def proxies_hr(site: str) -> float:
    return PROXY["candidates"][site]["HOLDOUT_DTI_hide_recover_pooled"]


def nan_cells_per_nan_file() -> int:
    vals = {v["outside_footprint_nan_cells"] for v in VER["user_named_variants"].values()
            if v["outside_footprint_encoding"] == "NaN"}
    assert len(vals) == 1, vals
    return vals.pop()


def main() -> int:
    d = build()
    HTML_OUT.write_text(html_page(d))
    JSON_OUT.write_text(json.dumps({"schema": "verdict-table-20261031-v1", **d}, indent=2, default=float) + "\n")
    print(f"wrote {HTML_OUT.relative_to(ROOT)} and {JSON_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
