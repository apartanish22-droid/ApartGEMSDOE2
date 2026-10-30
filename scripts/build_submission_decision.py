#!/usr/bin/env python3
"""Build the executive submission-decision page and its machine-readable table.

Reads only committed evidence (no network, no competition data), so CI can regenerate it and
check it with `git diff --exit-code -- docs`.

Outputs:
  docs/submission-decision.html          human executive summary (site entry point)
  evidence/submission_decision_20261030.json  decision table as data
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NINE = json.loads((ROOT / "evidence/nine_site_bests_20261030.json").read_text())
CARD = json.loads((ROOT / "evidence/ridge3_run_card_20261030.json").read_text())

LEADERBOARD_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
PROBLEM_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
RULES_URL = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
GDR_URL = "https://gdr.openei.org/submissions/1391"
GEODAWN_URL = "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and"

# Organizer public leaderboard, fetched 2026-10-30 (top rows). Public scores, not file receipts.
LEADERBOARD_TOP = [
    ("#1", "xiaofanhu", 0.4544),
    ("#2", "cfld__", 0.3916),
    ("#3", "Batik Shirt Brothers", 0.3915),
    ("#4", "BrandenKMurray", 0.3841),
    ("#5", "op01", 0.3642),
    ("#48", "kpomazi", 0.3195),
]
XCHECK = json.loads((ROOT / "evidence/review_pass2_cross_candidates_20261030.json").read_text())["candidates"]

NAN_NAME = "apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan"
ZERO_NAME = "apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros"
NAN_PATH = "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-nan.tif"
ZERO_PATH = "docs/downloads/apartgemsdoe2-h-ridge3-tensorfuse-37654-20261030-zeros.tif"
RUN_CARD = "evidence/ridge3_run_card_20261030.json"
NOTE = CARD["note"]
assert len(NOTE) <= 140, "note must be at most 140 characters"

n_nan_named_zeros = sum(
    1 for s in NINE["sites"]
    if s["user_reported_file"].endswith("-nan") and s["nan_cells_in_file"] == 0
)
RIDGE_OVERLAP_NONLAT = CARD["gates"]["G2_dots_max_within_3px_excluding_lattice"]
RIDGE_OVERLAP_LAT = CARD["gates"]["G2_dots_max_within_3px_literal"]
RIDGE_RHO = CARD["gates"]["G1_surface_max_abs_spearman"]
RIDGE_DTI = CARD["catalogue_insample_diagnostic"]["dtw"]["DTI"]
RIDGE_AUC = CARD["catalogue_insample_diagnostic"]["auc_fused_vs_catalogue"]
NAN_SHA = CARD["output"]["sha256"]
ZERO_SHA = CARD["zeros_twin_readback"]["sha256"]

SITE_ORDER = ["GEMSDOE32", "GEMSDOE36", "GEMSDOE28", "GEMSDOE31", "GEMSDOE33",
              "GEMSDOE25", "GEMSDOE30", "GEMSDOE24", "GEMSDOE27"]


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def build_table_rows():
    sites = {s["site"]: s for s in NINE["sites"]}
    rows = []
    rows.append({
        "file": f"{NAN_PATH}  (+ zeros twin {ZERO_PATH.split('/')[-1]})",
        "origin": "This session, H-RIDGE3 (catalogue-free), 37,654 dots",
        "estimated_score": "NOT ESTIMABLE. No holdout. Catalogue in-sample DTI "
                           f"{RIDGE_DTI:.3f} is a sanity diagnostic, not a score.",
        "unique_vs_other_gemsdoe_sites": (
            f"PARTLY. Max overlap with any non-lattice registry raster {pct(RIDGE_OVERLAP_NONLAT)} "
            f"(passes 70%). Synthetic calibration lattice {pct(RIDGE_OVERLAP_LAT)} (fails the literal rule)."),
        "ok_to_submit": "NO",
        "reason": "Literal lattice gate fails; no holdout; weak catalogue signal (AUC "
                  f"{RIDGE_AUC:.3f}); no organizer authentication. The zeros twin also stores 0 outside "
                  "the footprint, which check_submission.py flags against the official null/NaN-outside rule; "
                  "the NaN file is the only variant that matches that rule.",
    })
    v4 = XCHECK["v4-ridge-q5pct"]
    rows.append({
        "file": "docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif",
        "origin": "Other session (main, v4 lane): label-free TMI+gravity ridge NMS, 203,418 dots",
        "estimated_score": "HOLDOUT-DTI catalogue proxy 0.07412 (east half, 95% CI 0.05987–0.09793) per its run card. "
                           "Not organizer-confirmed; not the hidden set.",
        "unique_vs_other_gemsdoe_sites": (
            f"PARTLY. Max overlap {pct(v4['max_nonlattice_strict_lt3']['fraction'])} with a non-lattice registry raster "
            f"(passes). Lattice {pct(v4['max_lattice_strict_lt3']['fraction'])} (fails the literal rule)."),
        "ok_to_submit": "NO",
        "reason": "Lattice gate fails; its own run card records E2 below the same-protocol reference on the east half "
                  "(verdict: negative).",
    })
    pr38 = XCHECK["unique-blind-conduit-nan"]
    rows.append({
        "file": "docs/downloads/gemsdoe32-unique-blind-conduit-20261030T021414Z-70aa4159-nan.tif",
        "origin": "Other session (PR #38, blind-conduit), 37,169 dots, collar-pruned",
        "estimated_score": "No holdout (its audit reports predicted leaderboard DTI as null). No estimate.",
        "unique_vs_other_gemsdoe_sites": (
            f"PARTLY. Max overlap {pct(pr38['max_nonlattice_strict_lt3']['fraction'])} with a non-lattice registry raster "
            f"(passes). Lattice {pct(pr38['max_lattice_strict_lt3']['fraction'])} (fails the literal rule)."),
        "ok_to_submit": "NO",
        "reason": "Its own audit says OK to download, NOT YET to submit, and slot HOLD-DO-NOT-SUBMIT. "
                  "The lattice gate fails, and no holdout exists.",
    })
    hrm = XCHECK["hrm-contrast-zeros"]
    rows.append({
        "file": "docs/downloads/apartgemsdoe2-hrm-contrast-blind-geothermal-20261030T015536Z-d6cdf8f8-zeros.tif",
        "origin": "Other session (main), H-RAD-MAG-CONTRAST, 40,000 dots, zeros outside",
        "estimated_score": "No estimate (its audit: projection only; uniqueness 'not yet verified').",
        "unique_vs_other_gemsdoe_sites": (
            "NOT VALID AS DELIVERED. 21,064 of 40,000 dots (53%) lie outside the official training-data footprint. "
            f"Its uniqueness numbers ({pct(hrm['max_nonlattice_strict_lt3']['fraction'])} non-lattice, "
            f"{pct(hrm['max_lattice_strict_lt3']['fraction'])} lattice) are measured on all dots and are not a valid test."),
        "ok_to_submit": "NO",
        "reason": "Dots outside the official footprint and zeros (not null/NaN) outside: fails the official format. "
                  "Its audit label 'format-valid' is incorrect.",
    })
    for name in SITE_ORDER:
        s = sites[name]
        rows.append({
            "file": s["registry_entry"].split(":", 1)[1],
            "origin": f"{name} site best (user-reported name: {s['user_reported_file']}; "
                      f"audited bytes: {s['format_variant']})",
            "estimated_score": f"User-reported {s['user_reported_score']:.4f} (UNVERIFIED, no receipt). "
                               "No new estimate.",
            "unique_vs_other_gemsdoe_sites": (
                f"NO. Overlap {pct(s['max_overlap_other_site_nonlattice'])} with another site's registry raster; "
                f"lattice {pct(s['max_overlap_calibration_lattice'])}."),
            "ok_to_submit": "NO",
            "reason": "Duplicate under the literal rule; not a new submission.",
        })
    return rows


def html_page(rows) -> str:
    sites = {s["site"]: s for s in NINE["sites"]}
    css = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1180px;margin:0 auto;padding:20px;color:#1d2a26;line-height:1.5;background:#fbfbf8}
h1{font-size:1.7rem;margin:.2rem 0}h2{font-size:1.2rem;margin-top:1.8rem;border-bottom:2px solid #d9e2dc;padding-bottom:.3rem}
.banner{background:#7a1c1c;color:#fff;padding:16px 18px;border-radius:8px;font-size:1.1rem}
.banner strong{font-size:1.25rem}
.ok{background:#e7f4ea;border-left:5px solid #2b7a3d;padding:10px 14px;border-radius:6px}
.warn{background:#fff4e0;border-left:5px solid #c77700;padding:10px 14px;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
th,td{border:1px solid #cfd8d2;padding:6px 8px;vertical-align:top;text-align:left}
th{background:#eef3ef}
.no{color:#9b1c1c;font-weight:700}.yes{color:#1d6b33;font-weight:700}
code{background:#eef3ef;padding:1px 4px;border-radius:4px;word-break:break-all}
small{color:#4b5b55}
"""
    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
               "<meta name='viewport' content='width=device-width,initial-scale=1'>"
               "<title>GEMS submission decision · ApartGEMSDOE2</title>"
               f"<style>{css}</style></head><body>")
    out.append("<h1>GEMS competition: submission decision</h1>")
    out.append("<small>Generated from committed evidence on 30 Oct 2026 (UTC). "
               "Regenerate with <code>python scripts/build_submission_decision.py</code>.</small>")
    out.append("<div class='banner' style='margin-top:14px'><strong>DO NOT UPLOAD ANY FILE FROM THIS SITE YET.</strong><br>"
               "No file currently passes the uniqueness gate under the literal rule. "
               "Our new file is unique against all 469 non-lattice focus-registry rasters on the training grid (maximum 49.0%), "
               "but it fails the literal test against one synthetic calibration lattice. "
               "It also has no validated holdout estimate and only weak catalogue signal. "
               "The nine site bests are all duplicates of other sites' rasters.</div>")

    out.append("<h2>1. The download decision (the only table you need)</h2>")
    out.append("<table><tr><th>File to download</th><th>What it is</th><th>Estimated score</th>"
               "<th>Unique vs other GEMSDOE sites?</th><th>OK to submit?</th></tr>")
    for r in rows:
        cls = "no" if r["ok_to_submit"] == "NO" else "yes"
        out.append("<tr><td><code>" + escape(r["file"]) + "</code></td>"
                   f"<td>{escape(r['origin'])}</td><td>{escape(r['estimated_score'])}</td>"
                   f"<td>{escape(r['unique_vs_other_gemsdoe_sites'])}</td>"
                   f"<td class='{cls}'>{escape(r['ok_to_submit'])}<br><small>{escape(r['reason'])}</small></td></tr>")
    out.append("</table>")
    out.append("<p><strong>If a file is ever cleared, the submission fields are:</strong></p>"
               f"<ul><li>Name: <code>{escape(NAN_NAME)}</code></li>"
               f"<li>Note (≤140 characters, {len(NOTE)} used): <code>{escape(NOTE)}</code></li>"
               f"<li>SHA-256 (NaN-outside variant): <code>{escape(NAN_SHA)}</code></li>"
               f"<li>SHA-256 (zeros-outside twin): <code>{escape(ZERO_SHA)}</code></li>"
               f"<li>Run card (in repository): <code>{RUN_CARD}</code></li></ul>")
    out.append("<h2>1b. Submission guide (only after a file is cleared)</h2><ol>"
               "<li>Confirm section 7 is complete and the decision above reads CLEARED. Until then, do not upload.</li>"
               "<li>Download the NaN-outside file, not the zeros twin, and confirm its SHA-256 matches the value above.</li>"
               "<li>Open the rules and problem page and confirm the format: single-layer float32 GeoTIFF, EPSG:32611, "
               "100 m, values in [0, 1] inside the footprint, null or NaN outside.</li>"
               "<li>Enter the name and the note exactly as listed above (note ≤140 characters).</li>"
               "<li>Keep the portal's rejection message and the uploaded file name. If the portal says "
               "'Predicted values must be in range [0, 1]', send both so the cause can be checked from the bytes.</li>"
               "<li>Record the portal's receipt (score or acceptance) and label it ORGANIZER-CONFIRMED. Do not label anything before then.</li>"
               "</ol>")
    out.append("<p class='warn'>Nothing on this page is an organizer score. The only organizer numbers are the public "
               "leaderboard rows in section 2.</p>")

    out.append("<h2>2. Scores you can trust, and scores you cannot yet</h2>")
    out.append("<table><tr><th>Source</th><th>Value</th><th>Evidence class</th></tr>")
    for rank, team, score in LEADERBOARD_TOP:
        out.append(f"<tr><td>Public leaderboard {escape(rank)} ({escape(team)})</td><td>{score:.4f}</td>"
                   f"<td>ORGANIZER PUBLIC SNAPSHOT (<a href='{LEADERBOARD_URL}'>drivendata leaderboard</a>), "
                   "not a receipt for any file</td></tr>")
    out.append("<tr><td>Site bests (9 sites, see section 3)</td><td>0.2449 – 0.2778</td>"
               "<td>USER-REPORTED / UNVERIFIED (no submission-page receipt)</td></tr>")
    out.append("<tr><td>H-RIDGE3 catalogue in-sample DTI</td>"
               f"<td>{RIDGE_DTI:.4f}</td><td>SANITY ONLY. Not a holdout or leaderboard estimate.</td></tr>")
    out.append("</table>")
    out.append("<p class='warn'>The user reported 0.3195 and 0.4413 as leaderboard top figures. "
               "On the public page fetched today (3 pages, top 50 rows), 0.3195 is rank #48 (kpomazi), "
               "0.4413 does not appear, and 0.2778 does not appear. The top score is 0.4544 at rank #1. "
               "None of these is a receipt for any file.</p>")

    out.append("<h2>3. The nine GEMSDOE site bests, recomputed</h2>")
    out.append("<p><small>Recomputed from the pinned owner-mirror bytes by "
               "<code>scripts/audit_nine_site_bests.py</code>. A dot is a cell with value &gt; 0. Overlap is the "
               "fraction of this file's dots within 3 px of another registry raster's dots. Duplicate threshold 70%. "
               "Within 3 px means strictly less than 3 px (scipy distance_upper_bound, matching the official kernel, where k(3 px)=0). "
               "An inclusive test (≤ 3 px) raises the candidate maxima to 99.3% and 52.6%; verdicts are unchanged "
               "(<code>evidence/review_pass1_recheck_20261030.json</code>).</small></p>")
    out.append("<table><tr><th>Site</th><th>Audited registry file</th><th>Score (user)</th><th>Dots</th>"
               "<th>Max overlap, other site</th><th>Calibration lattice overlap</th>"
               "<th>Unique?</th></tr>")
    for name in SITE_ORDER:
        s = sites[name]
        out.append(f"<tr><td>{name}</td><td><code>{escape(s['registry_entry'].split('/')[-1])}</code></td>"
                   f"<td>{s['user_reported_score']:.4f}</td><td>{s['dots']:,}</td>"
                   f"<td>{pct(s['max_overlap_other_site_nonlattice'])}</td>"
                   f"<td>{pct(s['max_overlap_calibration_lattice'])}</td>"
                   "<td class='no'>NO</td></tr>")
    out.append("</table>")
    g32 = sites["GEMSDOE32"]["registry_entry"].split("/")[-1]
    out.append("<p>The highest user-reported value, <strong>GEMSDOE32 0.2778</strong> (audited file "
               f"<code>{escape(g32)}</code>), is still a duplicate under the literal rule. "
               "It is not a new submission, and its score has no organizer receipt.</p>")

    out.append("<h2>4. Official format, verified from the official rules and problem page</h2>")
    out.append("<ul>"
               f"<li>Single layer, 32-bit float, values between 0 and 1 (<a href='{PROBLEM_URL}'>problem page, Submission format</a>).</li>"
               "<li>CRS EPSG:32611, 100 m resolution, same bounds as the training data.</li>"
               "<li>Data outside the bounds is <strong>null or NaN</strong> (same source).</li>"
               f"<li>Official rules: <a href='{RULES_URL}'>{RULES_URL}</a>.</li>"
               "</ul>")
    out.append("<h2>5. The rejection message: '<code>Predicted values must be in range [0, 1]</code>'</h2>")
    out.append("<div class='warn'>The cause is not known. Possible causes, not verified: (a) the portal treats NaN as "
               "out of range, which conflicts with the official text; (b) a file has values outside [0, 1] or a "
               "no-data value stored as data; (c) the file is a zip with more than one layer. Send us the exact file name "
               "you uploaded and we can check its bytes. Both candidate variants pass the numeric [0, 1] check on finite cells.</div>")

    out.append("<h2>6. Irregularities flagged for review</h2><ol>")
    items = [
        "<strong>Literal lattice gate is not chance-informative.</strong> The synthetic 5-px calibration lattice "
        "(<code>r13-lattice-s5</code>, 206,895 dots) covers 99.1% of the H-RIDGE3 dots and 99.9% of each site best, "
        "while random placement at that density gives about 68%. Excluding it is a user decision, and I have not done it silently.",
        "<strong>Registry contains identical bytes under different sites.</strong> "
        f"{len(NINE['registry_duplicate_byte_groups'])} duplicate-byte groups in the 471-raster focus registry. "
        "For example, the GEMSDOE25 best has byte-identical copies filed under GEMSDOE24 and GEMSDOE32, "
        "and the GEMSDOE27 best is byte-identical to a GEMSDOE28 file.",
        "<strong>GEMSDOE25 and GEMSDOE30 share an identical dot set.</strong> Both report 0.2600. "
        "I measured identical dot masks (44,090 cells, equal values). The byte hashes differ.",
        "<strong>Mirror sample is not the official sample.</strong> The owner-mirror <code>sample_submission.tif</code> "
        "contains 60,988 ones that match the catalogue labels exactly. The official problem page describes the "
        "sample as predicting total fault absence.",
        "<strong>Owner mirrors are not organizer data.</strong> The competition inputs come from a third-party GitHub mirror "
        "of a login-walled DrivenData file. Hash pins prove mirror consistency only. Check the redistribution terms "
        "against the DrivenData rules before relying on these bytes.",
        "<strong>Extended registry not verified.</strong> 89 of its 560 entries use short commit references, "
        "which the repo's immutable-SHA rule rejects. The complete registry is therefore not verified.",
        "<strong>Conservative local checker disagrees with the official text.</strong> "
        "<code>scripts/check_submission.py</code> requires every stored cell to be finite, so it rejects the NaN-outside variant. "
        "The official text allows NaN outside the bounds.",
        "<strong>Zeros twin is not official-format.</strong> The zeros-outside twin stores 0 outside the footprint. "
        "<code>check_submission.py</code> reports that the outside cells are not null or NaN, so the official rule fails. "
        "Use the NaN-outside file, not the zeros twin, if a file is ever cleared.",
        "<strong>Other session's H-RAD-MAG-CONTRAST file is invalid as delivered.</strong> "
        "21,064 of its 40,000 dots (53%) lie outside the official training footprint, and its zeros-outside bytes "
        "do not meet the null/NaN clause. Its audit label 'format-valid' is incorrect.",
        "<strong>Off-grid test raster excluded.</strong> <code>GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif</code> (32×48) "
        "cannot be compared cell-for-cell and is recorded as excluded.",
        "<strong>User-reported leaderboard figures are partly off-page.</strong> "
        "0.3195 is rank #48 on the public page, so it is not the top score. 0.4413 does not appear in the top 50. See section 2.",
        "<strong>User-reported file names do not match the bytes.</strong> "
        f"{n_nan_named_zeros} of the nine site bests are named <code>-nan</code> by the user, "
        "but their registry bytes have no NaN cells (zeros outside the footprint). "
        "The portal may therefore have received a different file than the one we audited. "
        "Settling this needs the exact file you uploaded.",
    ]
    for it in items:
        out.append(f"<li>{it}</li>")
    out.append("</ol>")

    out.append("<h2>7. What is needed before any file can be cleared</h2><ol>"
               "<li>A decision on the literal lattice gate. Either exempt the synthetic calibration raster with a written reason, or change the rule.</li>"
               "<li>A whole-segment, buffered holdout with features built only from visible faults, and a leakage canary for each feature.</li>"
               "<li>A new candidate that beats a frozen holdout baseline with a positive paired interval.</li>"
               "<li>Organizer-authenticated input data (downloaded by you from DrivenData, hash-checked).</li>"
               "<li>The exact rejected file from the portal error, so the [0, 1] cause can be settled.</li>"
               "</ol>")

    out.append("<h2>8. Sources</h2><ul>"
               f"<li><a href='{PROBLEM_URL}'>DrivenData problem description and submission format</a></li>"
               f"<li><a href='{LEADERBOARD_URL}'>DrivenData public leaderboard</a></li>"
               f"<li><a href='{RULES_URL}'>Official GEMS Prize rules (NLR, September 2026)</a></li>"
               f"<li><a href='{GDR_URL}'>INGENIOUS regional dataset compilation (DOI 10.15121/1881483, CC BY 4.0)</a></li>"
               f"<li><a href='{GEODAWN_URL}'>USGS GeoDAWN release (DOI 10.5066/P93LGLVQ, CC0)</a></li>"
               "</ul>")
    out.append("<p><small>Evidence: <code>evidence/nine_site_bests_20261030.json</code>, "
               f"<code>{RUN_CARD}</code>, <code>evidence/submission_decision_20261030.json</code>.</small></p>")
    out.append("</body></html>")
    return "\n".join(out)


def main() -> int:
    rows = build_table_rows()
    (ROOT / "docs/submission-decision.html").write_text(html_page(rows))
    decision = {
        "schema": "submission-decision-v1",
        "utc": "2026-10-30",
        "decision": "DO NOT UPLOAD ANY FILE YET",
        "rows": rows,
        "leaderboard_top_observed": [{"rank": r, "team": t, "score": s} for r, t, s in LEADERBOARD_TOP],
        "leaderboard_source": LEADERBOARD_URL,
        "new_candidate": {"name": NAN_NAME, "nan_variant": NAN_PATH, "zeros_variant": ZERO_PATH,
                          "nan_sha256": NAN_SHA, "zeros_sha256": ZERO_SHA, "note": NOTE},
    }
    (ROOT / "evidence/submission_decision_20261030.json").write_text(json.dumps(decision, indent=2))
    print("wrote docs/submission-decision.html and evidence/submission_decision_20261030.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
