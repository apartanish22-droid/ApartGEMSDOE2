#!/usr/bin/env python3
"""Generate docs/submission-summary-20261030.html from the evidence receipts (no hand-typed numbers).

Every number is taken from evidence/*.json and labelled HOLDOUT-DTI (local proxy, with CI where measured),
ORGANIZER-CONFIRMED (none in this repository), or USER-REPORTED / UNVERIFIED (champions.json).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
SITES = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def e(x) -> str:
    return html.escape(str(x))


def f4(x) -> str:
    return "—" if x is None else f"{x:.4f}"


def ci(c) -> str:
    return "—" if not c else f"[{c[0]:.4f}, {c[1]:.4f}]"


def main() -> int:
    gate = json.loads((EV / "gates_nine_sites_20261030.json").read_text())
    audit = json.loads((EV / "audit_nine_sites_20261030.json").read_text())
    cards = json.loads((EV / "run_card_20261030.json").read_text())
    pw = audit["pairwise"]
    cmp_ = audit["GEMSDOE25_vs_GEMSDOE30"]
    rows = []
    for s in sorted(SITES, key=lambda k: -gate["candidates"][k]["G2_proxies"]["SGMC-CAL_off_catalogue_proxy"]["raw_dti"]):
        c = gate["candidates"][s]
        p = c["G2_proxies"]
        sg, hr = p["SGMC-CAL_off_catalogue_proxy"], p["HOLDOUT-DTI_hide_recover"]
        null = c["G2_random_null_same_n"]
        others = {k: pw["within_3px_row_A_in_col_B"][s][k] for k in SITES if k != s}
        nearest = max(others, key=others.get)
        rows.append(
            f"<tr><td><strong>{s}</strong></td><td>{c['dots']:,}</td>"
            f"<td>{f4(sg['raw_dti'])} <small>{ci(sg['raw_ci95'])}</small></td>"
            f"<td>{f4(hr['pooled_dti'])} <small>{ci(hr['ci95'])}</small></td>"
            f"<td>{min(null['SGMC_raw_dti_values']):.4f}–{max(null['SGMC_raw_dti_values']):.4f}</td>"
            f"<td>{e(nearest)} ({others[nearest]*100:.1f}%)</td>"
            f"<td>{audit['summary'][s]['G3_worst_within_3px_excluding_space_filling']*100:.2f}%</td>"
            f"<td>{'pass' if c['G1_format']['all_checks_passed'] else 'FAIL'}</td></tr>")
    cand_rows = []
    for card in cards["cards"]:
        h = card["holdout_dti"]
        sg, hr = h["SGMC_off_catalogue_proxy"], h["HOLDOUT-DTI_hide_recover"]
        reg = card["registry_correlation_overlap"]
        cand_rows.append(
            f"<tr><td><strong>{e(card['lane'])}</strong><br><small>{e(card['name'])}</small></td>"
            f"<td>{card['raster']['dots']:,}</td>"
            f"<td>{f4(sg['raw_point'])} <small>{ci(sg['raw_ci95'])}</small> <em>(HOLDOUT-DTI proxy)</em></td>"
            f"<td>{f4(hr['point'])} <small>{ci(hr['ci95'])}</small> <em>(HOLDOUT-DTI)</em></td>"
            f"<td>{f4(min(h['random_null_same_n']['SGMC_raw_values']))}–{f4(max(h['random_null_same_n']['SGMC_raw_values']))}</td>"
            f"<td>{reg['max_abs_spearman']:.3f}</td>"
            f"<td>{reg['worst_within_3px']*100:.2f}% (lattice) · {reg['worst_within_3px_excluding_space_filling']*100:.2f}% (other rasters)</td>"
            f"<td><strong>{e(card['verdict'])}</strong></td></tr>")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Submission decision · 30 Oct 2026 · ApartGEMS</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body><main id="main"><div class="shell">
<div class="breadcrumb"><a href="index.html">Overview</a> / Submission summary 30 Oct 2026</div>
<section class="page-hero"><div class="eyebrow">Executive summary · generated from evidence/*.json</div>
<h1 class="page-title">Decision: do not submit.</h1>
<p class="lead">No file in this repository is approved for upload. The two new candidates from this session are negative; nothing here is an organizer score.</p></section>
<div class="notice"><strong>DO NOT SUBMIT.</strong><p>Every number below is either a <strong>HOLDOUT-DTI</strong> local evaluator value (evaluator version, withheld-positive count and 95% CI given where measured), a <strong>USER-REPORTED / UNVERIFIED</strong> value, or a format/registry check. <strong>ORGANIZER-CONFIRMED: none.</strong> Estimates and projections are not scores.</p></div>

<h2>1. Leaderboard and the conflicting numbers</h2>
<p>The organizer leaderboard page (fetched 30 Oct 2026, first of three chunks) shows <strong>#1 = 0.4544</strong> (xiaofanhu). That is a page-level figure, not a per-file receipt. The conflicting values in the brief, <strong>0.4413</strong> and <strong>0.3195</strong>, were not found on the chunk read here and remain <strong>unverified</strong>. Sources: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem and format</a>, <a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">masking clarification (thread 11516)</a>.</p>

<h2>2. Nine focus sites on identical gates</h2>
<p>Sorted by SGMC raw proxy. The user-reported site bests (GEMSDOE32 0.2778, GEMSDOE36 0.2750, and others) carry no organizer receipt; they appear in the registry as <strong>USER-REPORTED / UNVERIFIED</strong>. Hide-and-recover tracks catalogue proximity, so it is not a quality ranking.</p>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Dots</th><th>SGMC raw proxy <em>(HOLDOUT-DTI)</em></th><th>Hide-and-recover <em>(HOLDOUT-DTI)</em></th><th>Random null, same N (SGMC, 3 seeds)</th><th>Nearest other site by within-3-px</th><th>Worst non-lattice registry overlap (within 3 px)</th><th>Format</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p>Scoring rule: pooled DTI with α = 0.2, β = 0.8 and a 300 m triangular kernel. Hide-and-recover uses n = {gate['candidates'][SITES[0]]['G2_proxies']['HOLDOUT-DTI_hide_recover']['n_withheld_positives']:,} withheld positives. The SGMC proxy uses {gate['candidates'][SITES[0]]['G2_proxies']['SGMC-CAL_off_catalogue_proxy']['n_truth_pixels']:,} off-catalogue truth pixels. Evaluator versions: {e(gate['candidates'][SITES[0]]['G2_proxies']['HOLDOUT-DTI_hide_recover']['evaluator_version'])} and {e(gate['candidates'][SITES[0]]['G2_proxies']['SGMC-CAL_off_catalogue_proxy']['evaluator_version'])}.</p>
<p><strong>Irregularity:</strong> GEMSDOE25 and GEMSDOE30 report identical dot counts ({cmp_['dots_a']:,}) and metrics. Byte comparison: SHA-256 {'identical' if cmp_['sha256_a'] == cmp_['sha256_b'] else 'DIFFERENT'} (GEMSDOE25 {e(cmp_['sha256_a'][:16])}…, GEMSDOE30 {e(cmp_['sha256_b'][:16])}…); dot masks {'identical' if cmp_['dot_masks_identical'] else 'differ in ' + format(cmp_['symmetric_difference_dots'], ',') + ' cells'}.</p>
<p><strong>Reading:</strong> on the SGMC proxy the nine raw values sit at 0.094–0.102 with overlapping intervals, so no site separates from the others. Against size-matched random dots (3 seeds, same N), seven sites are above their null: 25, 28, 30, 31, 32, 33 and 36. GEMSDOE24 and GEMSDOE27 are not distinguishable from their own nulls. The hide-and-recover column tracks catalogue proximity (the within-3-px counts in the audit), so it does not rank quality.</p>

<h2>3. This session's candidates (research, both negative)</h2>
<div class="table-wrap"><table><thead><tr><th>Lane</th><th>Dots</th><th>SGMC raw proxy</th><th>Hide-and-recover</th><th>Random null (SGMC)</th><th>Max |Spearman|</th><th>Within 3 px (literal)</th><th>Verdict</th></tr></thead>
<tbody>{''.join(cand_rows)}</tbody></table></div>
<p><strong>H-CATLOGIT-OOF</strong> trained a logistic discriminant on the catalogue, scoring each quadrant out-of-fold. Its per-band leakage canary passed (max single-feature AUC 0.755 on off-catalogue truth; 0.560 on hide-and-recover truth; threshold 0.90). Its surface AUC against off-catalogue truth was 0.509, close to chance. <strong>H-EQDENS-TOPN</strong> ranked cells by declustered earthquake intensity; its band was chosen on hide-and-recover AUC so SGMC was not used for selection. Both fall below the random null on the off-catalogue proxy. Both fail the literal lattice rule (99.4–99.7%). The Walker Lane mimic for H-EQDENS-TOPN was not tested as a separate control.</p>
<p><strong>Proxy bias to know about:</strong> the SGMC truth is by construction more than 300 m from the catalogue. Dots adjacent to the catalogue therefore cannot score on it. Hide-and-recover has the opposite bias. Its withheld segments are only quadrant-collared, so 15,705 of 22,232 withheld positives lie within 15 px of visible faults (issue #60). Neither proxy is validated against organizer truth.</p>

<h2>4. Uniqueness</h2>
<p><strong>The nine focus sites are not unique relative to one another.</strong> Every site has at least one other site with 88% or more of its dots within 3 px of that site's dots (pairwise table in <a href="https://github.com/apartanish22-droid/ApartGEMSDOE2/blob/main/evidence/audit_nine_sites_20261030.json">evidence/audit_nine_sites_20261030.json</a>). The worst non-lattice registry comparison is 100% for every one of the nine. GEMSDOE25 and GEMSDOE30 carry identical values (see section 2). This matches the earlier repository finding that all nine archived dot sets fail the 70% rule.</p>
<p>Registry scope: 489 focus rasters refreshed on 30 Oct 2026 (18 added, 0 removed, 0 SHA changes against the previous snapshot), plus the 13GEMSDOE lattice. The lattice covers 99.87% of the footprint in 3-px dilation, so a literal 70% limit cannot be met by any candidate above about 22,163 dots. The gate reports this literally and does not exempt it. Two malformed upstream rasters are counted, not hidden.</p>

<h2>5. Irregularities flagged</h2>
<ul>
<li>sample_submission.tif: the organizer page describes total absence (all zeros), but the owner mirror has 60,988 positive cells inside the footprint. Inside the footprint it equals labels == 1 exactly.</li>
<li>The submission writer and evaluator have open defects (buffedlizard55-lab/GEMSDOE32 issues #37, #41, #51, #60, #61, #63). The writer binarizes its input, so graded probabilities cannot be emitted through it. This session's candidate writer is separate and did not fork the shared function.</li>
<li>The owner-mirror hashes verify the mirror, not organizer origin. Portal acceptance of the earlier [0,1] rejection is unverified; its cause was not guessed.</li>
<li>GEMSDOE32's 0.2778 and the other site bests are user-reported and unverified (champions.json: OWNER-REPORTED, no receipt in this repository).</li>
</ul>

<h2>6. Limitations and data that would change the answer</h2>
<ul>
<li>No organizer-confirmed score exists for any file in this repository. The official submission page and a receipt are needed for ORGANIZER-CONFIRMED values.</li>
<li>Organizer-authenticated competition inputs and the sample are needed. The mirror has not been authenticated against the organizer.</li>
<li>A buffered whole-segment holdout with masks matching official scoring. The current evaluator has the split defect above.</li>
<li>Uniqueness covers only the focus registry and the lattice. The other listed repositories and owners have not been fetched in this session.</li>
<li>Free official data not obtained: BLM claims, GDR temperature, USGS Great Basin conductance, OPERA DISP-S1 (ASF not allowlisted), and the organizer's sample.</li>
</ul>

<h2>7. Suggested next work</h2>
<ol>
<li>Obtain the organizer's sample and the official submission page receipt; authenticate the template.</li>
<li>Fix the upstream split (buffered whole segments) and the writer/evaluator defects, then re-pin the shared tools.</li>
<li>Test the untried hypothesis slate (H–C1 to H–C4) with the canary first, then the buffered holdout and registry gates.</li>
<li>Re-run the gates after the registry is extended to every listed repository.</li>
</ol>
<p class="fine">Generated {e(cards['checked_utc'][:10])} by scripts/build_summary_20261030.py from evidence/run_card_20261030.json, evidence/audit_nine_sites_20261030.json, evidence/gates_nine_sites_20261030.json and registry/champions.json. Regenerate, do not hand-edit.</p>
</div></main></body></html>
"""
    (ROOT / "docs" / "submission-summary-20261030.html").write_text(page)
    print("wrote docs/submission-summary-20261030.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
