#!/usr/bin/env python3
"""Build the static, evidence-led Pages site from the committed audit.

The build does not generate a model, GeoTIFF, forecast, or approval.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
AUDIT = json.loads((ROOT / "evidence/historical_audit.json").read_text())
SITES = AUDIT["sites"]


def esc(value):
    return escape(str(value), quote=True)


def header(prefix=""):
    return f'''<header class="topbar"><div class="shell">
      <a class="brand" href="{prefix}index.html" aria-label="ApartGEMS home"><span class="brand-icon"><svg viewBox="0 0 30 30" fill="none" aria-hidden="true"><path d="M3 20c4-8 6 3 10-4s6 3 14-7M4 24c5-7 7 2 11-4s7 1 11-4M4 13c5-8 8 3 12-4s7 1 10-2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></span>ApartGEMS <em>Research desk</em></a>
      <nav class="nav" aria-label="Primary navigation"><a href="{prefix}index.html#scorecard">Site scorecard</a><a href="{prefix}index.html#analysis">Analysis</a><a href="{prefix}research.html">Research</a><a href="{prefix}executive-summary.html">Submission guide</a></nav>
      <div class="nav-end"><a class="source-link" href="{prefix}index.html#sources">Sources ↗</a></div>
    </div></header>'''


def footer(prefix=""):
    return f'''<footer class="footer"><div class="shell"><small><strong>ApartGEMS / Research desk</strong><br>Fault discovery, built on verifiable evidence. No submission was made.</small><div><a href="{prefix}data/run_card.json">Run card JSON ↗</a> &nbsp;&nbsp; <a href="https://github.com/apartanish22-droid/ApartGEMSDOE2">GitHub repository ↗</a></div></div></footer>'''


def page(title, body, prefix="", script=False):
    js = '<script src="assets/feed.js" defer></script>' if script else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#173c35"><meta name="description" content="An evidence-led, fail-closed GEMS fault-discovery and submission research desk."><title>{esc(title)} · ApartGEMS</title><link rel="stylesheet" href="{prefix}assets/style.css">{js}</head><body>{header(prefix)}<main id="main">{body}</main>{footer(prefix)}</body></html>\n'''


def source_card(name, description, link, label="Review source ↗"):
    return f'<div class="source-card"><strong>{esc(name)}</strong><span>{esc(description)}</span><a href="{esc(link)}">{esc(label)}</a></div>'


def row(s):
    site = s['site']
    overlap = s['max_overlap_other_focus_site']
    return f'''<tr><td><a class="site-name" href="sites/{site.lower()}.html">{site} ↗</a></td>
    <td class="file-cell"><a href="sites/{site.lower()}.html">{esc(s['reported_submission_name'])}</a><span class="sub">Archived variant in site detail</span></td>
    <td><span class="reported">{esc(s['reported_value'])}</span><span class="sub">User-reported; unverified</span></td>
    <td>Not estimable<span class="sub">No calibrated transfer</span></td>
    <td><span class="tag bad">NO · {overlap['fraction']:.1%}</span><span class="sub">within 3 px of {esc(overlap['reference'])}</span></td>
    <td><span class="tag bad">DO NOT SUBMIT</span><span class="sub">Historical / duplicate</span></td></tr>'''


def index():
    source_cards = ''.join([
      source_card('Competition problem & metric','Official fault target, weighted Tversky and submission format.','https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/'),
      source_card('Official rules','Eligibility, entry, weekly allowance and required disclosures.','https://docs.nlr.gov/docs/fy26osti/96647.pdf'),
      source_card('USGS GeoDAWN','Magnetic, radiometric, survey flight lines and documented acquisition effects.','https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'),
      source_card('DOE INGENIOUS / GDR','Public regional geology, conductance and wells; attribution required.','https://gdr.openei.org/submissions/1391'),
      source_card('USGS 3DEP','Public elevation data; availability varies across the study footprint.','https://www.usgs.gov/3d-elevation-program'),
      source_card('Organizer reference solution','Baseline code; data and authenticated access are separate.','https://github.com/drivendataorg/gems-prize-reference-solution')])
    table = ''.join(map(row, SITES))
    body = f'''<div class="shell"><section class="hero" aria-labelledby="hero-title"><div>
      <div class="eyebrow">DOE GEMS prize · decision brief</div><h1 id="hero-title">Evidence before<br><span class="soft">the next upload.</span></h1>
      <p class="lead">A clearer path from fault-discovery research to a competition submission. Track the strongest historical work, the evidence behind it, and the gates that protect the next slot.</p>
      <div class="hero-actions"><a class="button primary" href="#scorecard">Explore the scorecard <span aria-hidden="true">↗</span></a><a class="text-link" href="executive-summary.html">Read the submission guide →</a></div>
      <div class="hero-note"><span></span> Evidence-led review · no automated portal submissions</div></div>
      <aside class="status-card" aria-label="Submission decision"><div class="status-top"><span>Current submission decision</span><span class="status-badge">● &nbsp; Negative</span></div>
      <h2>Not ready to submit.</h2><p>No new TIFF has passed the required lane, holdout, uniqueness and format gates. A past file or a different name is not a new submission.</p>
      <div class="actions"><button class="button disabled" disabled>↓ &nbsp; Submission download unavailable</button><a class="button ghost" href="data/run_card.json">View run card ↗</a></div><div class="subnote">No weekly slot selected or used in this run.</div></aside></section>
      <section class="kpis" aria-label="Evidence snapshot"><div class="kpi"><div class="kpi-label">Public leaderboard leader</div><div class="kpi-value" id="leader-value">0.4544</div><div class="kpi-desc" id="leader-age">Observed 27 Oct 2026 UTC</div></div>
      <div class="kpi"><div class="kpi-label">Best historical claim</div><div class="kpi-value">0.2778</div><div class="kpi-desc">GEMSDOE32 · user-reported, unverified</div></div>
      <div class="kpi"><div class="kpi-label">New-file score estimate</div><div class="kpi-value">Unknown</div><div class="kpi-desc">No validated transfer to hidden truth</div></div>
      <div class="kpi"><div class="kpi-label">Experiments this run</div><div class="kpi-value">0 / 3</div><div class="kpi-desc">Stopped at preflight · 0 slots used</div></div></section>
      <section class="section" id="scorecard"><div class="section-head"><div><div class="section-kicker">01 / Nine priority sites</div><h2>Historical results, in context.</h2></div><p>Highest values supplied for each site, not verified organizer receipts. The linked archival variant may differ in bytes from the file named in the claim.</p></div>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Reported submission</th><th>Reported value</th><th>New-file estimate</th><th>Unique vs 8 sites?</th><th>Decision</th></tr></thead><tbody>{table}</tbody></table></div>
      <div class="table-foot"><span class="dot"></span><span>Directional overlap is measured on every archived final dot. The audit covers these nine pinned variants, not every private or future submission. A different hash alone does not establish uniqueness. <a href="data/historical_audit.json" class="text-link">View full audit ↗</a></span></div></section>
      <section class="section" id="analysis"><div class="section-head"><div><div class="section-kicker">02 / What the evidence says</div><h2>Why did the leader stand out?</h2></div><p>We can explain the geometry, not establish the cause of a reported score without the hidden labels and a file-bound receipt.</p></div>
      <div class="analysis-grid"><div class="panel"><div class="mini-label">Verified file geometry</div><h3>Less redundancy, not a new detector.</h3><p>The GEMSDOE32 archival dot set is contained in the GEMSDOE31 set. The former removes <strong>2,545 dots</strong>; every removed dot lies within two pixels of the mirrored known catalogue. This is a <strong>geometry audit</strong>, not a leaderboard result.</p><p>Under the organizer’s distance-weighted metric, tightly clustered predictions can compete for the same nearby credit while contributing prediction mass. Pruning could help, but this does not prove why the reported value was higher or that it will generalize.</p><a class="text-link" href="data/historical_audit.json">Inspect the reconstruction ↗</a> &nbsp; <a class="text-link" href="https://github.com/apartanish22-droid/ApartGEMSDOE2/blob/main/research/findings.md">Full analysis ↗</a></div>
      <div class="panel dark"><div class="mini-label">The gate that stops this run</div><h3>A literal uniqueness conflict.</h3><div class="metric">≥ 82.34%</div><p>Minimum possible 3-pixel overlap with one registered calibration lattice at the champion’s 37,654-dot count — above the requested 70% limit. Only 6,649 mirrored-footprint cells are outside the lattice’s 3-pixel neighborhood.</p><p>This is a counting bound, not a score. It does not rule out every smaller candidate, and it does not justify moving dots into holes to game the rule.</p><a class="text-link" href="executive-summary.html#blockers">Read the full stop rationale ↗</a></div></div></section>
      <section class="section" id="gates"><div class="section-head"><div><div class="section-kicker">03 / Release protocol</div><h2>Four gates. One clear decision.</h2></div><p>Format validity is necessary, but it cannot by itself establish scientific quality or permission to use a slot.</p></div>
      <div class="steps"><div class="step"><span class="step-no">01 / PREREGISTER</span><h3>Assigned method lane</h3><p>Use the shared, pinned template and feature stack. The prompt supplies no single assigned method paragraph.</p><span class="tag bad">BLOCKED</span></div>
      <div class="step"><span class="step-no">02 / VALIDATE</span><h3>Leakage-safe holdout</h3><p>Whole segments, buffered spatial blocks, visible-only catalogue features and standalone feature canaries.</p><span class="tag bad">NOT RUN</span></div>
      <div class="step"><span class="step-no">03 / COMPARE</span><h3>Prove uniqueness</h3><p>Check surface correlation before placement and final-dot proximity against every registry raster.</p><span class="tag bad">BLOCKED</span></div>
      <div class="step"><span class="step-no">04 / RELEASE</span><h3>Validate saved bytes</h3><p>Check range, mask, grid and provenance; a separate automated selector must approve a slot.</p><span class="tag bad">NO FILE</span></div></div></section>
      <section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">04 / Verified starting points</div><h2>Follow the source.</h2></div><p>Official sources describe the problem and data. A catalogue holdout is not the organizer’s hidden-label score.</p></div><div class="sources">{source_cards}</div><div class="feed-panel"><div><strong>Source snapshot</strong><p id="feed-checked">Loading timestamped source-head checks…</p><small>Updated periodically when the workflow runs. A changed repository has not been re-audited automatically.</small></div><div id="feed-grid" class="feed-grid" aria-live="polite"></div><a class="text-link" href="data/source_feed.json">View raw source snapshot ↗</a></div></section></div>'''
    return page('Evidence before the next upload', body, script=True)


def summary():
    body = '''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Executive summary</div><section class="page-hero"><div class="eyebrow">Executive summary · submission guide</div><h1 class="page-title">One decision before<br>you download.</h1><p class="lead">The process is designed to make upload readiness obvious. Right now, there is no approved new file.</p></section>
    <div class="notice"><strong>DO NOT SUBMIT — no new candidate TIFF exists.</strong><p>The historical files are for research only. No leaderboard estimate, format pass, or uniqueness pass is asserted for a nonexistent new raster.</p></div>
    <div class="page-grid"><div><section class="page-section"><h2>What happens when a candidate clears the gates?</h2><ol>
    <li>Prerecord the explicitly assigned method, feature sources, non-fault mimic, budget and immutable registry snapshot. Stop if the surface exceeds the specified correlation or proximity threshold.</li>
    <li>Run the shared holdout with whole buffered withheld segments. Rebuild every catalogue-derived feature from visible faults only; mask visible catalogue pixels exactly. Test each feature individually for leakage.</li>
    <li>Compare pooled HOLDOUT-DTI and its spatial-block 95% confidence interval against a frozen same-protocol best. Do not turn the proxy into a leaderboard forecast.</li>
    <li>Check final dots against all registry entries. Use the shared writer and re-open the saved bytes against an authenticated competition template: single float32 GeoTIFF, matching CRS, dimensions and transform; finite values in [0,1] inside the footprint; null/NaN outside as stated by the organizer.</li>
    <li>Have a separate <strong>automated</strong> selector verify the evidence and the current authenticated weekly allowance. Only after approval should the site expose one clearly named download and a note of at most 140 characters.</li>
    <li>On DrivenData, select that exact file, paste its note, and submit only if the selector has approved it. Save the organizer receipt and file SHA-256 together. This project does not automatically spend a slot.</li></ol>
    <p>These are future steps, not a claim that the current checkout implements a complete training or release pipeline. The official rules PDF states three submissions per week; the authenticated submission page is the authoritative current allowance.</p></section>
    <section class="page-section" id="blockers"><h2>Why is this run blocked?</h2><ul><li>No single method lane was actually supplied in the prompt. We did not invent an assignment.</li><li>The shared registry snapshot is incomplete, the prepared feature stack is absent, and no frozen same-protocol best is available in this checkout.</li><li>One registered lattice proves that a 37,654-dot candidate must overlap at least 82.34% within 3 pixels. The literal limit is 70%. This is a conditional geometry bound, not a result for every smaller candidate.</li><li>The public mirror called <code>sample_submission.tif</code> contains 60,988 positive pixels identical to the mirrored labels; the official page describes the sample as predicting total absence. The mirror is not organizer-authenticated.</li></ul></section>
    <section class="page-section"><h2>About the range error</h2><p>The reported message “Predicted values must be in range [0, 1]” is real, but the rejected bytes are not present here, so its cause is unknown. Negative sentinels such as <code>-9999</code>, infinities, values outside the range, NaNs inside the footprint, or incompatible mask/nodata handling are possibilities—not a diagnosis.</p><p>The published format requests null or NaN outside the bounds; some older all-finite files use zeros outside. We cannot infer which representation the live portal accepts from a local diagnostic. Do not blindly clip values or change the exterior to claim a fix. Validate the exact saved file against the authenticated template and retain the portal receipt.</p></section>
    <section class="page-section"><h2>Current best does not mean current permission</h2><p>GEMSDOE32’s 0.2778 is a user-reported historical value, not an authenticated receipt. All nine audited archival dot sets fail the requested uniqueness rule against another focus-site raster. They are not candidates for a new upload, and the true cause of their reported ranking remains unknown.</p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Upload decision</div><div class="value">No file approved</div></div><div class="fact"><div class="mini-label">Estimated new-file score</div><div class="value">Not estimable</div></div><div class="fact"><div class="mini-label">File / submission name</div><div class="value">None generated</div></div><div class="fact"><div class="mini-label">Weekly slots used</div><div class="value">0 this run</div></div><div class="fact"><div class="mini-label">Evidence</div><div class="inline-list"><a href="data/run_card.json">Run card ↗</a><a href="data/historical_audit.json">Geometry audit ↗</a></div></div></div></aside></div></div>'''
    return page('Executive summary & submission guide', body)


def site_detail(s):
    site = s['site']
    ref = s['max_overlap_other_focus_site']
    archive = s['source_url'].replace('/blob/', '/raw/')
    parent_link = f'https://buffedlizard55-lab.github.io/{site}/'
    if site == 'GEMSDOE31':
        parent_link += 'docs/'
    if site in ('GEMSDOE32', 'GEMSDOE36'):
        parent_link += 'docs/'
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / <a href="../index.html#scorecard">Nine-site scorecard</a> / {site}</div><section class="page-hero"><div class="eyebrow">Priority site / historical review</div><h1 class="page-title">{site}<br>evidence brief.</h1><p class="lead">The highest user-supplied historical result is an unverified claim, not permission to spend a submission slot.</p></section>
    <div class="notice"><strong>DO NOT SUBMIT THIS HISTORICAL FILE.</strong><p>This archival variant is for research only. Its final-dot geography exceeds the requested overlap threshold against another focus-site raster; the complete registry and pre-placement surface were not evaluated.</p></div>
    <div class="page-grid"><div><section class="page-section"><h2>Historical result</h2><p>Reported submission name: <code>{esc(s['reported_submission_name'])}</code>. The claimed value <strong>{esc(s['reported_value'])}</strong> is <strong>USER-REPORTED / UNVERIFIED</strong>. No organizer submission-page receipt linking the value to this file hash was found.</p><p>The pinned archival variant below was independently retrieved for learning and comparison. Its filename or exterior encoding may differ from the reported submitted file, so the association is not proof of byte identity.</p><div class="inline-list"><a href="{esc(archive)}">Download archival variant · research only ↗</a><a href="{esc(parent_link)}">Visit source site ↗</a></div></section>
    <section class="page-section"><h2>Uniqueness &amp; format</h2><p>In the exact archival comparison, <strong>{ref['fraction']:.2%}</strong> of this file’s positive dots fall within three pixels of {esc(ref['reference'])}; the literal stop threshold is 70%. This proves a failure against that one reference, not a complete all-registry audit.</p><p>The archived TIFF matches the owner-mirrored grid and has finite in-footprint values in [0,1]. It has finite values rather than null/NaN in the mirrored exterior. The independent local checks do not prove organizer acceptance or identify the cause of the reported portal rejection.</p><p>Estimated leaderboard score of a new candidate: <strong>not estimable</strong>. The experiment and hidden-label transfer needed for a credible estimate have not been established.</p></section>
    <section class="page-section"><h2>Next action</h2><p>Do not resubmit, rename, or use this old raster as a new method. Restore an assigned lane and shared feature stack, perform leakage-safe holdout and complete registry comparisons, then let a separate automated selector decide whether a weekly slot is justified.</p><a class="text-link" href="../executive-summary.html">Open the full submission guide ↗</a></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Reported value · unverified</div><div class="value">{esc(s['reported_value'])}</div></div><div class="fact"><div class="mini-label">Unique vs other focus sites?</div><div class="value">No · {ref['fraction']:.1%} overlap</div></div><div class="fact"><div class="mini-label">Estimated new-file score</div><div class="value">Not estimable</div></div><div class="fact"><div class="mini-label">Archived filename</div><div class="value small">{esc(s['filename'])}</div></div><div class="fact"><div class="mini-label">Archive SHA-256</div><div class="value small">{esc(s['sha256'])}</div></div><div class="fact"><div class="mini-label">Submission status</div><div class="value">DO NOT SUBMIT</div></div></div></aside></div></div>'''
    return page(f'{site} executive summary', body, '../')


def research():
    body = '''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Research directions</div><section class="page-hero"><div class="eyebrow">Research slate · untested</div><h1 class="page-title">Four ideas. No<br>manufactured scores.</h1><p class="lead">These are qualitative hypotheses, not assigned lanes or predictions. Their ranking is a planning judgment, and novelty beyond this checkout is not established.</p></section>
    <div class="notice"><strong>No hypothesis was run in this session.</strong><p>Data access, lane assignment, registry completeness and the literal uniqueness rule block a valid experiment. Expected improvement is unknown for every idea.</p></div>
    <div class="page-grid"><div>
    <section class="page-section"><h2>01 / Paired drainage offsets</h2><p><strong>Layers:</strong> 3DEP DEM, detrended elevation and isostatic gravity gradient. <strong>Signature:</strong> paired channel or terrace profiles displaced across a persistent topographic break, corroborated by a subsurface gradient. Concealed basin-margin displacements could persist away from mapped traces. <strong>Mimic:</strong> fluvial terrace erosion and alluvial-fan avulsion. <strong>Difference:</strong> paired opposite-side profiles, not a single ridge or stream-χ score; not implemented in this empty checkout. <strong>Cost:</strong> high; requires actual DEM tiles and coverage checks.</p></section>
    <section class="page-section"><h2>02 / Flight-line robustness</h2><p><strong>Layers:</strong> GeoDAWN magnetic grids plus individual magnetic flight-line measurements and position/altitude. <strong>Signature:</strong> require a candidate edge to survive independent leave-flight-line-out reconstructions at a common height. This may reduce acquisition artifacts while preserving concealed magnetic contacts. <strong>Mimic:</strong> lithological contacts without fault displacement. <strong>Difference:</strong> independent line-withholding stability, not only grid-level smoothing. <strong>Cost:</strong> high; published line data have not been downloaded here.</p></section>
    <section class="page-section"><h2>03 / Cross-depth conductance contrast</h2><p><strong>Layers:</strong> USGS Great Basin MT conductance maps for 2–12 km and 12–20 km, plus gravity gradient. <strong>Signature:</strong> a laterally persistent change in the ratio of depth-integrated conductances coincident with a basin margin. It may expose a concealed structural transition even where a surface catalogue is incomplete. <strong>Mimic:</strong> non-fault clay or salinity variation and inversion artifacts. <strong>Difference:</strong> explicit cross-depth contrast rather than a single conductance layer. <strong>Cost:</strong> medium–high; coarse resolution limits surface inference.</p></section>
    <section class="page-section"><h2>04 / Geochemical discontinuity</h2><p><strong>Layers:</strong> INGENIOUS well/spring chemistry and temperatures, DEM and gravity. <strong>Signature:</strong> cross-margin contrast in spatially blocked, uncertainty-weighted fluid chemistry rather than treating every spring as a fault. <strong>Mimic:</strong> lithology or groundwater mixing unrelated to displacement. <strong>Difference:</strong> paired chemical contrast, not point proximity. <strong>Cost:</strong> high; coverage, chemistry fields and licence must be checked for the actual area.</p></section>
    <section class="page-section"><h2>What is needed before testing?</h2><p>Verify a method assignment, restore the original licensed data and cached stack, freeze a complete registry and a same-evaluator best, pre-register the experiment, and resolve the literal lattice issue without silently exempting it. Whole-component buffered validation, one-feature leakage canaries, both uniqueness stages and a separate selector remain mandatory.</p><p>A surface fault prediction is not a confirmed geothermal vent, reservoir, heat flow or active fluid pathway. <a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">Organizer task context ↗</a></p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Ranking</div><div class="value">Qualitative only</div></div><div class="fact"><div class="mini-label">Leaderboard improvement</div><div class="value">Unknown</div></div><div class="fact"><div class="mini-label">External data availability</div><div class="value">Published, not restored</div><p class="sub">Official pages list downloadable data; bytes and study-area coverage have not been verified in this environment.</p></div><div class="fact"><div class="mini-label">Official data sources</div><div class="inline-list"><a href="https://www.usgs.gov/3d-elevation-program">3DEP ↗</a><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">GeoDAWN ↗</a><a href="https://doi.org/10.5066/P9TWT2LU">USGS MT ↗</a><a href="https://gdr.openei.org/submissions/1391">INGENIOUS ↗</a></div></div></div></aside></div></div>'''
    return page('Research directions', body)


def main():
    (DOCS / 'sites').mkdir(parents=True, exist_ok=True)
    (DOCS / 'data').mkdir(parents=True, exist_ok=True)
    (DOCS / 'index.html').write_text(index())
    (DOCS / 'executive-summary.html').write_text(summary())
    (DOCS / 'research.html').write_text(research())
    for s in SITES:
        (DOCS / 'sites' / f"{s['site'].lower()}.html").write_text(site_detail(s))
    for name in ('historical_audit.json', 'run_card.json'):
        shutil.copyfile(ROOT / 'evidence' / name, DOCS / 'data' / name)
    print(f'Built overview, guide, research, and {len(SITES)} static site briefs.')


if __name__ == '__main__':
    main()
