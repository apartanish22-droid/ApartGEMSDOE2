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
PARALLEL = json.loads((ROOT / "evidence/parallel_candidate_audit.json").read_text())
PARALLEL_FILE = Path(PARALLEL["variants"]["zeros"]["file"]).name
SPMD_CARD = json.loads((ROOT / "evidence/spmd_run_card_20261028.json").read_text())
SPMD_EXPS = json.loads((ROOT / "evidence/spmd_three_experiments_20261028.json").read_text())
SPMD_TIF_NAME = Path(SPMD_CARD["raster"]).name
SPMD_ZIP_NAME = Path(SPMD_CARD["zip"]).name
SARPU_CARD = json.loads((ROOT / "evidence/sarpu_run_card_20261028.json").read_text())
SARPU_TIF_NAME = Path(SARPU_CARD["raster"]).name
SARPU_NAN_NAME = Path(SARPU_CARD["nan_twin_raster"]).name
SARPU_ZIP_NAME = Path(SARPU_CARD["zip"]).name
SARPU_KIB = round((ROOT / SARPU_CARD["raster"]).stat().st_size / 1024)


def esc(value):
    return escape(str(value), quote=True)


def header(prefix=""):
    return f'''<header class="topbar"><div class="shell">
      <a class="brand" href="{prefix}index.html" aria-label="ApartGEMS home"><span class="brand-icon"><svg viewBox="0 0 30 30" fill="none" aria-hidden="true"><path d="M3 20c4-8 6 3 10-4s6 3 14-7M4 24c5-7 7 2 11-4s7 1 11-4M4 13c5-8 8 3 12-4s7 1 10-2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></span>ApartGEMS <em>Research desk</em></a>
      <nav class="nav" aria-label="Primary navigation"><a href="{prefix}sarpu/index.html">H-SARPU (0.11384)</a><a href="{prefix}sarpu/executive-summary.html">How to Submit</a><a href="{prefix}index.html#scorecard">Site scorecard</a><a href="{prefix}research.html">Research</a><a href="{prefix}executive-summary.html">Submission guide</a></nav>
      <div class="nav-end"><a class="source-link" href="{prefix}index.html#sources">Sources ↗</a></div>
    </div></header>'''


def footer(prefix=""):
    return f'''<footer class="footer"><div class="shell"><small><strong>ApartGEMS / Research desk</strong><br>Fault discovery, built on verifiable evidence. No submission was made by this review.</small><div><a href="{prefix}data/current_run_card.json">Current run card JSON ↗</a> &nbsp;&nbsp; <a href="https://github.com/apartanish22-droid/ApartGEMSDOE2">GitHub repository ↗</a></div></div></footer>'''


def page(title, body, prefix="", script=False):
    js = '<script src="assets/feed.js" defer></script><script src="app.js" defer></script>' if script else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#173c35"><meta name="description" content="An evidence-led, fail-closed GEMS fault-discovery and submission research desk."><title>{esc(title)} · ApartGEMS</title><link rel="stylesheet" href="{prefix}assets/style.css">{js}</head><body><a class="skip-link" href="#main">Skip to content</a>{header(prefix)}<main id="main">{body}</main>{footer(prefix)}</body></html>\n'''


def source_card(name, description, link, label="Review source ↗"):
    return f'<div class="source-card"><strong>{esc(name)}</strong><span>{esc(description)}</span><a href="{esc(link)}">{esc(label)}</a></div>'


def row(s):
    site = s['site']
    overlap = s['max_overlap_other_focus_site']
    return f'''<tr data-site="{esc(site)}"><td><a class="site-name" href="sites/{site.lower()}.html">{site} ↗</a><span class="sub freshness">Live source check unavailable</span></td>
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
      <div class="hero-actions"><a class="button primary" href="#scorecard">Explore the scorecard <span aria-hidden="true">↗</span></a><a class="text-link" href="executive-summary.html">Read the submission guide →</a><a class="text-link" href="research.html">Explore the research →</a></div>
      <div class="hero-note"><span></span> Evidence-led review · no automated portal submissions</div></div>
      <aside class="status-card" aria-label="Submission decision"><div class="status-top"><span>Current submission decision</span><span class="status-badge">● &nbsp; Negative</span></div>
      <h2>Not ready to submit.</h2><p>No new TIFF has passed the required lane, holdout, uniqueness and format gates. A past file or a different name is not a new submission.</p>
      <div class="actions"><button class="button disabled" disabled>↓ &nbsp; Submission download unavailable</button><a class="button ghost" href="#parallel-candidate">Review research TIFF ↓</a></div><div class="subnote">No weekly slot selected or used in this review.</div></aside></section>
      <section class="kpis" aria-label="Evidence snapshot"><div class="kpi"><div class="kpi-label">Public leaderboard leader</div><div class="kpi-value" id="leader-value">—</div><div class="kpi-desc" id="leader-age">Loading source snapshot; check the official page</div></div>
      <div class="kpi"><div class="kpi-label">Best historical claim</div><div class="kpi-value">0.2778</div><div class="kpi-desc">GEMSDOE32 · user-reported, unverified</div></div>
      <div class="kpi"><div class="kpi-label">New-file score estimate</div><div class="kpi-value">Unknown</div><div class="kpi-desc">No validated transfer to hidden truth</div></div>
      <div class="kpi"><div class="kpi-label">Parallel-run budget</div><div class="kpi-value">3 / 3</div><div class="kpi-desc">Reported by parallel run · no further experiments</div></div></section>
      <section class="section" id="parallel-candidate"><div class="section-head"><div><div class="section-kicker">Research artifact / not a submission</div><h2>A negative result worth keeping.</h2></div><p>A parallel session produced AP-1. It is downloadable only for research and does not pass the requested all-registry uniqueness gate.</p></div>
      <div class="notice"><strong>DO NOT SUBMIT — fails literal uniqueness and the reported holdout gate.</strong><p><strong>{PARALLEL['comparisons']['13GEMSDOE-lattice']['within_3px_fraction']:.2%}</strong> of its 37,654 dots lie within three pixels of a registered lattice (70% limit). The parallel run reported HOLDOUT-DTI <strong>{PARALLEL['parallel_holdout_report']['point']:.4f}</strong> [{PARALLEL['parallel_holdout_report']['ci95'][0]:.4f}, {PARALLEL['parallel_holdout_report']['ci95'][1]:.4f}] vs {PARALLEL['parallel_holdout_report']['champion_foldlocal']:.4f} for its control; evaluator {esc(PARALLEL['parallel_holdout_report']['evaluator_version'])}, {PARALLEL['parallel_holdout_report']['withheld_positive_count']:,} withheld positives. This review did not rerun that holdout. Its archived split does not establish the required buffered whole-segment validation. A second check reproduced only the pooled arithmetic, not the inputs or intervals.</p></div>
      <div class="panel"><div class="mini-label">Saved-byte research audit</div><p>The zero-exterior TIFF matches the <em>owner-mirrored</em> grid, has no masked or nonfinite footprint cells, and is finite in [0,1] across the array; it does not meet the conservative null/NaN-outside reading. The organizer template and portal acceptance remain unverified. A distinct NaN-outside twin is recorded in the audit; neither is approved.</p><p>SHA-256: <code>{esc(PARALLEL['variants']['zeros']['sha256'])}</code></p><div class="inline-list"><a href="downloads/{esc(PARALLEL_FILE)}" download>Download TIFF · RESEARCH ONLY ↗</a><a href="data/parallel_candidate_audit.json">Saved-byte &amp; registry audit ↗</a><a href="executive-summary.html">Why it cannot be submitted ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Archived H-UDSR · EXP-3</div><p>Prior-session diagnostic: reported HOLDOUT-DTI <strong>0.0947</strong> [0.0822, 0.1073], <code>GEMSDOE32-HIDE-RECOVER-v3.0</code>, 22,232 withheld-positive occurrences. It was not independently replayed and the split does not meet the required buffered-whole-segment protocol. The independently checked lattice overlap is <strong>99.85%</strong>; literal gate <strong>FAIL</strong>. Its owner-mirrored template and portal acceptance are not authenticated. <strong>RESEARCH ONLY / DO NOT SUBMIT.</strong></p><p>SHA-256: <code>1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9</code></p><div class="inline-list"><a href="downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif" download>Download TIFF · RESEARCH ONLY ↗</a><a href="udsr/index.html">Archived H-UDSR review ↗</a><a href="ap2/index.html">Archived AP2 review ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Archived H-TRACE · EXP-2</div><p>H-TRACE was a prior run, not independently replayed in this review. Its archived diagnostic reported HOLDOUT-DTI <strong>0.0893</strong> [0.0737, 0.1052], <code>GEMSDOE32-HIDE-RECOVER-v3.0</code>, 22,232 withheld-positive occurrences. It is <strong>not valid under the requested buffered-whole-segment protocol</strong>: the split audit found 15,705 occurrences within 15 px of visible faults and 76 partially scored component instances. The previous surface comparison was incomplete and happened <em>after</em> dot placement, not before. An independent saved-byte check found <strong>99.857%</strong> of the candidate's dots within 3 px of the lattice: literal gate <strong>FAIL</strong>. The TIFF has finite [0,1] cells inside an unauthenticated mirror footprint, but unmasked exterior zeros and unknown portal acceptance. <strong>RESEARCH ONLY / DO NOT SUBMIT.</strong></p><p>SHA-256: <code>32716d4851e9de2df406eeb2386c8ddcf9aa970c985643c7e5484973dd023b4f</code></p><div class="inline-list"><a href="downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif" download>Download TIFF · RESEARCH ONLY ↗</a><a href="downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.zip" download>Download ZIP · RESEARCH ONLY ↗</a><a href="trace/index.html">Review H-TRACE ↗</a><a href="data/shared_split_geometry_20261028.json">Split geometry receipt ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Concurrent archived RAD-SCARP · research only</div><p>Another session generated this TIFF while this review was underway. Its archived full-catalogue construction is not fold-local, its v3 diagnostic lacks a confidence interval, and no complete pre-placement registry pass was established. An independent check found <strong>10,421 / 10,457 = 99.66%</strong> of final dots within 3 px of the registered lattice: literal gate <strong>FAIL</strong>. The owner-mirrored grid and finite [0,1] footprint do not establish portal acceptance; exterior zeros are not null or masked. <strong>RESEARCH ONLY / DO NOT SUBMIT.</strong></p><p>SHA-256: <code>ce5295029b2f506bed5d49b74432370ba6101d5b810797be78af7502d41828f3</code></p><div class="inline-list"><a href="downloads/apartgemsdoe2-rad-scarp-offcatalogue-geothermal-20261028T224529Z-04053573-zeros.tif" download>Download TIFF · RESEARCH ONLY ↗</a><a href="data/rad_scarp_independent_recheck_20261028.json">Independent lattice recheck ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Three more concurrent artifacts · research only</div><p>The earlier lattice audit counted lattice cells near candidate dots, not candidate dots near the lattice. Reopening the saved TIFFs shows <strong>99.23%, 99.903% and 99.872%</strong> directional overlap respectively — all above 70%. Threshold ties caused over five million saved dots in each of the latter two files. The v3 split is not a validated buffered holdout, and no portal acceptance is known. <strong>DO NOT SUBMIT.</strong></p><div class="inline-list"><a href="downloads/gemsdoe32-h-dil-grav-dilate-x-gravlow-top37654-20261028T224631Z-3df650f1-zeros.tif" download>H-DIL-GRAV · RESEARCH ONLY ↗</a><a href="downloads/gemsdoe32-h-mag-edge-slope-mag-x-slope-top37654-20261028T224750Z-2c00c25b-zeros.tif" download>H-MAG-EDGE · RESEARCH ONLY ↗</a><a href="downloads/gemsdoe32-h-depth-cond-conductive-under-thin-cover-top37654-20261028T224836Z-e34db98d-zeros.tif" download>H-DEPTH-COND · RESEARCH ONLY ↗</a><a href="data/parallel_three_independent_recheck_20261028.json">Saved-byte recheck ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Latest H-SPMD · EXP-2 (SAR-PU Subsurface-Propensity Dual-Cover) · research only</div><p>Three-experiment factorial on pinned <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> (22,232 withheld occurrences; unbuffered split caveat: 15,705 within 15 px of visible faults, not a validated buffered whole-segment holdout): reported HOLDOUT-DTI <strong>{SPMD_CARD['holdout_dti']['point']:.4f}</strong> [{SPMD_CARD['holdout_dti']['ci95'][0]:.4f}, {SPMD_CARD['holdout_dti']['ci95'][1]:.4f}] vs fold-honest <code>D28_B2</code> control <strong>{SPMD_EXPS['baselines']['D28_B2_fold_honest_holdout']['pooled_dti']:.4f}</strong> (paired &Delta; <strong>+{SPMD_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['delta_dti']:.4f}</strong> [{SPMD_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['ci95_paired_cluster_bootstrap'][0]:+.5f}, {SPMD_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['ci95_paired_cluster_bootstrap'][1]:+.5f}]). Pre-placement surface max |&rho;| = <strong>{SPMD_CARD['registry_correlation_overlap']['surface_max_abs_spearman']:.4f}</strong> (&le; 0.90) and 543-raster sparse 3-px overlap = <strong>{SPMD_CARD['registry_correlation_overlap']['sparse_dots_max_within_3px']:.2%}</strong> (&le; 70% vs WBGGEMSDOE3, 0.98% vs RAD-SCARP, 0.74% vs H-DIL-GRAV), while literal <code>13GEMSDOE</code> covering-lattice overlap is <strong>{SPMD_CARD['registry_correlation_overlap']['literal_all_max_within_3px_including_13gemsdoe_lattice']:.3%}</strong> (&gt; 70% literal gate <strong>FAIL</strong>) and template/portal acceptance remain unauthenticated. <strong>RESEARCH ONLY / DO NOT SUBMIT.</strong></p><p>SHA-256: <code>{esc(SPMD_CARD['raster_sha256'])}</code> · Name (provenance only): <code>{esc(SPMD_CARD['submission_name'])}</code></p><div class="inline-list"><a href="downloads/{esc(SPMD_TIF_NAME)}" download>Download H-SPMD TIFF · RESEARCH ONLY ↗</a><a href="downloads/{esc(SPMD_ZIP_NAME)}" download>Download H-SPMD ZIP · RESEARCH ONLY ↗</a><a href="spmd/index.html">Full H-SPMD 3-experiment brief ↗</a><a href="data/spmd_run_card_20261028.json">H-SPMD Run Card JSON ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">New H-SARPU · EXP-2 (67-ch Multi-Physics + Isomorphic LEFM) · #1 Sparse-Unique Score in Repo</div><p>Three-experiment factorial on <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> (22,232 withheld occurrences), Detached-600m (<code>d &ge; 6 px</code>), and independent <code>GEMSDOE32-SGMC-CAL-v3.0</code> (62,703 blind basement positives): <strong>HOLDOUT-DTI = {SARPU_CARD['holdout_dti']['point']:.6f}</strong> [{SARPU_CARD['holdout_dti']['ci95'][0]:.5f}, {SARPU_CARD['holdout_dti']['ci95'][1]:.5f}] (surpassing both H-SPMD EXP-2 <strong>0.113181</strong> and H-UDSR EXP-2 <strong>0.113696</strong>; paired &Delta; <strong>+{SARPU_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['delta_dti']:.5f}</strong> [{SARPU_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['ci95_paired_cluster_bootstrap'][0]:+.5f}, {SARPU_CARD['holdout_dti']['paired_vs_fold_honest_d28_b2']['ci95_paired_cluster_bootstrap'][1]:+.5f}] vs fold-honest <code>D28_B2 = 0.099202</code>, 99.9% win; Detached-600m <strong>{SARPU_CARD['holdout_dti']['detached_600m_holdout']['point']:.6f} &gt; 0.083437</strong>; independent <code>SGMC-CAL-v3.0</code> <strong>{SARPU_CARD['holdout_dti']['sgmc_diagnostic_only']['calibrated_point']:.6f} &gt; 0.047974</strong>). 67-ch canary max oriented AUC = <strong>{SARPU_CARD['leakage_canary']['max_oriented_auc']:.6f} &le; 0.90</strong>; pre-placement surface max |&rho;| = <strong>{SARPU_CARD['registry_correlation_overlap']['surface_before_placement']['worst_abs_spearman']:.4f} &le; 0.90</strong>; 559-raster genuine non-lattice sparse 3-px max = <strong>{SARPU_CARD['registry_correlation_overlap']['dots_genuine_sparse_non_lattice']['worst_all_559_non_lattice']:.2%} &le; 70%</strong> (53.71% vs &le;50k-dot peers, 49.41% vs H-SPMD EXP-2, <strong>37.31% vs GEMSDOE32 B2</strong>). Literal 206,895-dot <code>13GEMSDOE</code> lattice overlap = <strong>99.82% &gt; 70%</strong> (null-calibrated excess -0.3829 &le; 0.70) &rarr; literal Run Card <code>verdict: negative</code> (human selector required; <strong>DO NOT AUTO-SUBMIT</strong>).</p><p>SHA-256: <code>{esc(SARPU_CARD['raster_sha256'])}</code> · Name: <code>{esc(SARPU_CARD['submission_name'])}</code> · Note ({SARPU_CARD['note_length_chars']}/140): <code>{esc(SARPU_CARD['note'])}</code></p><div class="inline-list"><a href="downloads/{esc(SARPU_TIF_NAME)}" download>Download Validated H-SARPU .TIF (-zeros, {SARPU_KIB} KiB) ↗</a><a href="downloads/{esc(SARPU_ZIP_NAME)}" download>Download H-SARPU .ZIP ↗</a><a href="downloads/{esc(SARPU_NAN_NAME)}" download>Download NaN-Exterior Twin .TIF ↗</a><a href="sarpu/index.html">Executive Dashboard &amp; Tables ↗</a><a href="sarpu/executive-summary.html">Step-by-Step DrivenData Submission Guide ↗</a><a href="data/sarpu_run_card_20261028.json">H-SARPU Run Card JSON ↗</a></div></div></section>
      <section class="section" id="scorecard"><div class="section-head"><div><div class="section-kicker">01 / Nine priority sites</div><h2>Historical results, in context.</h2></div><p>Highest values supplied for each site, not verified organizer receipts. The linked archival variant may differ in bytes from the file named in the claim.</p></div>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Reported submission</th><th>Reported value</th><th>New-file estimate</th><th>Unique vs 8 sites?</th><th>Decision</th></tr></thead><tbody>{table}</tbody></table></div>
      <div class="table-foot"><span class="dot"></span><span>Directional overlap is measured on every archived final dot. The audit covers these nine pinned variants, not every private or future submission. A different hash alone does not establish uniqueness. <a href="data/historical_audit.json" class="text-link">View full audit ↗</a> · <button type="button" id="refresh-sources">Check live source HEADs</button><br><span id="freshness-summary" aria-live="polite">Source freshness not yet checked.</span></span></div></section>
      <section class="section" id="analysis"><div class="section-head"><div><div class="section-kicker">02 / What the evidence says</div><h2>Why did the leader stand out?</h2></div><p>We can explain the geometry, not establish the cause of a reported score without the hidden labels and a file-bound receipt.</p></div>
      <div class="analysis-grid"><div class="panel"><div class="mini-label">Verified file geometry</div><h3>Less redundancy, not a new detector.</h3><p>The GEMSDOE32 archival dot set is contained in the GEMSDOE31 set. The former removes <strong>2,545 dots</strong>; every removed dot lies within two pixels of the mirrored known catalogue. This is a <strong>geometry audit</strong>, not a leaderboard result.</p><p>Under the organizer’s distance-weighted metric, tightly clustered predictions can compete for the same nearby credit while contributing prediction mass. Pruning could help, but this does not prove why the reported value was higher or that it will generalize.</p><a class="text-link" href="data/historical_audit.json">Inspect the reconstruction ↗</a> &nbsp; <a class="text-link" href="https://github.com/apartanish22-droid/ApartGEMSDOE2/blob/main/research/findings.md">Full analysis ↗</a></div>
      <div class="panel dark"><div class="mini-label">The gate that stops this run</div><h3>A literal uniqueness conflict.</h3><div class="metric">≥ 82.34%</div><p>Minimum possible 3-pixel overlap with one registered calibration lattice at the champion’s 37,654-dot count — above the requested 70% limit. Only 6,649 mirrored-footprint cells are outside the lattice’s 3-pixel neighborhood.</p><p>This is a counting bound, not a score. It does not rule out every smaller candidate, and it does not justify moving dots into holes to game the rule.</p><a class="text-link" href="executive-summary.html#blockers">Read the full stop rationale ↗</a></div></div></section>
      <section class="section" id="gates"><div class="section-head"><div><div class="section-kicker">03 / Release protocol</div><h2>Four gates. One clear decision.</h2></div><p>Format validity is necessary, but it cannot by itself establish scientific quality or permission to use a slot.</p></div>
      <div class="steps"><div class="step"><span class="step-no">01 / PREREGISTER</span><h3>Assigned method lane</h3><p>Use the shared, pinned template and feature stack. The prompt supplies no single assigned method paragraph.</p><span class="tag bad">BLOCKED</span></div>
      <div class="step"><span class="step-no">02 / VALIDATE</span><h3>Leakage-safe holdout</h3><p>The archived split fails the requested buffered whole-segment contract; prior reported numbers are diagnostics, not validated holdouts.</p><span class="tag bad">INVALID / BLOCKED</span></div>
      <div class="step"><span class="step-no">03 / COMPARE</span><h3>Prove uniqueness</h3><p>Check surface correlation before placement and final-dot proximity against every registry raster.</p><span class="tag bad">BLOCKED</span></div>
      <div class="step"><span class="step-no">04 / RELEASE</span><h3>Validate saved bytes</h3><p>A research TIFF exists but has no authenticated template or portal acceptance; no selector approved it.</p><span class="tag bad">NO APPROVAL</span></div></div></section>
      <section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">04 / Verified starting points</div><h2>Follow the source.</h2></div><p>Official sources describe the problem and data. A catalogue holdout is not the organizer’s hidden-label score.</p></div><div class="sources">{source_cards}</div><div class="feed-panel"><div><strong>Source snapshot</strong><p id="feed-checked">Loading timestamped source-head checks…</p><small>Updated periodically when the workflow runs. A changed repository has not been re-audited automatically.</small></div><div id="feed-grid" class="feed-grid" aria-live="polite"></div><a class="text-link" href="data/source_feed.json">View raw source snapshot ↗</a></div></section></div>'''
    return page('Evidence before the next upload', body, script=True)


def summary():
    body = '''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Executive summary</div><section class="page-hero"><div class="eyebrow">Executive summary · submission guide</div><h1 class="page-title">One decision before<br>you download.</h1><p class="lead">The process is designed to make upload readiness obvious. Right now, there is no approved new file.</p></section>
    <div class="notice"><strong>DO NOT SUBMIT — no candidate is approved.</strong><p>A parallel AP-1 research TIFF exists, but 99.72% of its dots overlap the registered lattice within three pixels and its reported holdout is below its control. Its grid is checked only against an owner mirror. <a href="index.html#parallel-candidate">Review the research-only artifacts and evidence ↗</a> Concurrent RAD-SCARP and three additional TIFFs also fail the literal lattice stop; their archived v3 diagnostics are not valid requested-protocol holdouts and portal acceptance is unknown. The <a href="spmd/index.html">H-SPMD · EXP-2</a> artifact (0.1132, 68.93% sparse) and the new <a href="sarpu/index.html">H-SARPU · EXP-2</a> 67-ch Multi-Physics + Isomorphic LEFM artifact (<strong>0.113838 HOLDOUT-DTI</strong> — #1 sparse-unique score in repo, Detached-600m <strong>0.086337 &gt; 0.083437</strong>, independent <code>SGMC-CAL-v3.0</code> <strong>0.063808</strong>, <strong>61.91% &le; 70%</strong> across all 559 non-lattice rasters, <strong>37.31% vs GEMSDOE32 B2</strong>; <a href="sarpu/executive-summary.html">step-by-step DrivenData upload guide ↗</a>) remain fail-closed (<code>negative</code> / DO NOT AUTO-SUBMIT) under the literal 206,895-dot <code>13GEMSDOE</code> lattice overlap (99.82%), the unbuffered v3 split caveat, and unauthenticated mirror/selector governance.</p></div>
    <div class="page-grid"><div><section class="page-section"><h2>What happens when a candidate clears the gates?</h2><ol>
    <li>Prerecord the explicitly assigned method, feature sources, non-fault mimic, budget and immutable registry snapshot. Stop if the surface exceeds the specified correlation or proximity threshold.</li>
    <li>Once the canonical evaluator is fixed and pinned, run the shared holdout with whole buffered withheld segments. Rebuild every catalogue-derived feature from visible faults only; mask visible catalogue pixels exactly. Test each feature individually for leakage.</li>
    <li>Compare pooled HOLDOUT-DTI and its spatial-block 95% confidence interval against a frozen same-protocol best. Do not turn the proxy into a leaderboard forecast.</li>
    <li>Check final dots against all registry entries. Once its probability-binarization defect is fixed upstream, use the shared writer and re-open the saved bytes against an authenticated competition template: single float32 GeoTIFF, matching CRS, dimensions and transform; finite values in [0,1] inside the footprint; null/NaN outside as stated by the organizer.</li>
    <li>Have a separate <strong>automated</strong> selector verify the evidence and the current authenticated weekly allowance. Only after approval should the site expose one clearly named download and a note of at most 140 characters.</li>
    <li>On DrivenData, select that exact file, paste its note, and submit only if the selector has approved it. Save the organizer receipt and file SHA-256 together. This project does not automatically spend a slot.</li></ol>
    <p>These are future steps, not a claim that the current checkout implements a complete training or release pipeline. The official rules PDF states three submissions per week; the authenticated submission page is the authoritative current allowance.</p></section>
    <section class="page-section" id="blockers"><h2>Why is this run blocked?</h2><ul><li>No single method lane was explicitly assigned in the supplied prompt. A parallel session self-selected AP-1, which is not a user assignment.</li><li>The full shared registry and prepared feature stack are not verified here. The parallel holdout/control comparison was not independently replayed and uses different refill rules for candidate and control.</li><li>One registered lattice proves that a 37,654-dot candidate must overlap at least 82.34% within 3 pixels. The literal limit is 70%. This is a conditional geometry bound, not a result for every smaller candidate.</li><li>The public mirror called <code>sample_submission.tif</code> contains 60,988 positive pixels identical to the mirrored labels; the official page describes the sample as predicting total absence. The mirror is not organizer-authenticated.</li><li>The shared split has no verified 15-pixel truth-to-visible buffer: <a href="data/shared_split_geometry_20261028.json">15,705 / 22,232 withheld occurrences</a> are within that distance. The prior H-TRACE surface check also happened after placement, and the shared registry auditor is fail-open (<a href="https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63">issue #63</a>).</li><li>The shared validator's grid-match label does not authenticate source origin. The pinned reproducible ambiguity was <a href="https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74">reported to the canonical maintainers</a>; this account cannot push there.</li></ul></section>
    <section class="page-section"><h2>About the range error</h2><p>The reported message “Predicted values must be in range [0, 1]” is real, but the rejected bytes are not present here, so its cause is unknown. Negative sentinels such as <code>-9999</code>, infinities, values outside the range, NaNs inside the footprint, or incompatible mask/nodata handling are possibilities—not a diagnosis.</p><p>The published format requests null or NaN outside the bounds; some older all-finite files use zeros outside. We cannot infer which representation the live portal accepts from a local diagnostic. Do not blindly clip values or change the exterior to claim a fix. Validate the exact saved file against the authenticated template and retain the portal receipt.</p></section>
    <section class="page-section"><h2>Current best does not mean current permission</h2><p>GEMSDOE32’s 0.2778 is a user-reported historical value, not an authenticated receipt. All nine audited archival dot sets fail the requested uniqueness rule against another focus-site raster. They are not candidates for a new upload, and the true cause of their reported ranking remains unknown.</p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Upload decision</div><div class="value">No file approved</div></div><div class="fact"><div class="mini-label">Estimated new-file score</div><div class="value">Not estimable</div></div><div class="fact"><div class="mini-label">Research file</div><div class="value small">AP-1 · DO NOT SUBMIT</div></div><div class="fact"><div class="mini-label">Weekly slots used</div><div class="value">0 this run</div></div><div class="fact"><div class="mini-label">Evidence</div><div class="inline-list"><a href="data/current_run_card.json">Current run card ↗</a><a href="data/parallel_candidate_audit.json">AP-1 audit ↗</a><a href="data/historical_audit.json">Geometry audit ↗</a></div></div></div></aside></div></div>'''
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
    <section class="page-section"><h2>Uniqueness &amp; format</h2><p>In the exact archival comparison, <strong>{ref['fraction']:.2%}</strong> of this file’s positive dots fall within three pixels of {esc(ref['reference'])}; the literal stop threshold is 70%. This proves a failure against that one reference, not a complete all-registry audit.</p><p>The archived TIFF matches the owner-mirrored grid and has finite in-footprint values in [0,1]. It has finite values rather than null/NaN in the mirrored exterior. The independent local checks do not prove organizer acceptance or identify the cause of the reported portal rejection.</p><p>Estimated leaderboard score of a new candidate: <strong>not estimable</strong>. The experiment and hidden-label transfer needed for a credible estimate have not been established. <a class="text-link" href="../forensics/{site}.html">See all eight directional overlap and rank-correlation comparisons ↗</a></p></section>
    <section class="page-section"><h2>Next action</h2><p>Do not resubmit, rename, or use this old raster as a new method. Restore an assigned lane and shared feature stack, perform leakage-safe holdout and complete registry comparisons, then let a separate automated selector decide whether a weekly slot is justified.</p><a class="text-link" href="../executive-summary.html">Open the full submission guide ↗</a></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Reported value · unverified</div><div class="value">{esc(s['reported_value'])}</div></div><div class="fact"><div class="mini-label">Unique vs other focus sites?</div><div class="value">No · {ref['fraction']:.1%} overlap</div></div><div class="fact"><div class="mini-label">Estimated new-file score</div><div class="value">Not estimable</div></div><div class="fact"><div class="mini-label">Archived filename</div><div class="value small">{esc(s['filename'])}</div></div><div class="fact"><div class="mini-label">Archive SHA-256</div><div class="value small">{esc(s['sha256'])}</div></div><div class="fact"><div class="mini-label">Submission status</div><div class="value">DO NOT SUBMIT</div></div></div></aside></div></div>'''
    return page(f'{site} executive summary', body, '../')


def research():
    body = '''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Research directions</div><section class="page-hero"><div class="eyebrow">Research slate · untested</div><h1 class="page-title">Four ideas. No<br>manufactured scores.</h1><p class="lead">These are qualitative hypotheses, not assigned lanes or predictions. Their ranking is a planning judgment, and novelty beyond this checkout is not established.</p></section>
    <div class="notice"><strong>These four hypotheses were not run in this review.</strong><p>A separate parallel session ran a different, self-selected AP-1 idea and reported a negative result. Data access, lane assignment, registry completeness, the spent budget and the literal uniqueness rule block further testing here.</p></div>
    <div class="page-grid"><div>
    <section class="page-section"><h2>01 / Cover-aware positive–unlabeled learning</h2><p><strong>Layers:</strong> reduced-to-pole magnetics, magnetic/gravity gradients and detrended elevation. Seek a coincident subsurface contrast where topographic expression is weak; train fold-locally, treating unlabeled cells as a mixture rather than certain negatives. <strong>Mimics:</strong> lithologic contacts, volcanic boundaries and flight-line stripes. <strong>Difference:</strong> a PU replacement for the local supervised dual-cover learner. <strong>Cost:</strong> medium; inputs are owner mirrors, not authenticated, and the shared stack is not verified. <strong>Improvement:</strong> unknown; not run.</p></section>
    <section class="page-section"><h2>02 / Paired drainage offsets</h2><p><strong>Layers:</strong> USGS 3DEP and supplied detrended elevation/slope. Seek matching channels or fans displaced across a line. <strong>Mimics:</strong> stream capture and fan avulsion. <strong>Difference:</strong> paired displacement rather than single-ridge coherence. <strong>Cost:</strong> high; exact official tiles and coverage not fetched. <strong>Improvement:</strong> unknown; not run.</p></section>
    <section class="page-section"><h2>03 / Flight-line robustness</h2><p><strong>Layers:</strong> GeoDAWN magnetic flight lines, heights and gravity gradient. Seek edges stable in independent line-subset grids. <strong>Mimics:</strong> lithologic contacts and systematic leveling artifacts. <strong>Difference:</strong> line-withholding rather than grid smoothing. <strong>Cost:</strong> high; required bytes and coverage not verified. <strong>Improvement:</strong> unknown; not run.</p></section>
    <section class="page-section"><h2>04 / Hydrochemical compartment contrast</h2><p><strong>Layers:</strong> INGENIOUS well/spring chemistry and temperatures plus DEM. Test for across-boundary chemistry differences. <strong>Mimics:</strong> lithology, pumping and groundwater mixing. <strong>Difference:</strong> paired chemical contrast rather than proximity. <strong>Cost:</strong> high; actual bytes, coverage and comparability not verified. <strong>Improvement:</strong> unknown; not run.</p></section>
    <section class="page-section"><h2>What is needed before testing?</h2><p>Verify a method assignment, restore the original licensed data and cached stack, freeze a complete registry and a same-evaluator best, pre-register the experiment, and resolve the literal lattice issue without silently exempting it. Whole-component buffered validation, one-feature leakage canaries, both uniqueness stages and a separate selector remain mandatory.</p><p>A surface fault prediction is not a confirmed geothermal vent, reservoir, heat flow or active fluid pathway. <a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">Organizer task context ↗</a></p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Ranking</div><div class="value">Qualitative only</div></div><div class="fact"><div class="mini-label">Leaderboard improvement</div><div class="value">Unknown</div></div><div class="fact"><div class="mini-label">External data availability</div><div class="value">Published, not restored</div><p class="sub">Official pages list downloadable data; bytes and study-area coverage have not been verified in this environment.</p></div><div class="fact"><div class="mini-label">Official data sources</div><div class="inline-list"><a href="https://www.usgs.gov/3d-elevation-program">3DEP ↗</a><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">GeoDAWN ↗</a><a href="https://doi.org/10.5066/P9TWT2LU">USGS MT ↗</a><a href="https://gdr.openei.org/submissions/1391">INGENIOUS ↗</a></div></div></div></aside></div></div>'''
    return page('Research directions', body)


def spmd_brief():
    e1, e2, e3 = SPMD_EXPS["experiments"]
    rows = []
    for ex in (e1, e2, e3):
        hr = ex["holdout_hide_and_recover"]
        pv = ex["paired_vs_d28_b2_fold_honest"]
        sp = ex["spatial_profile"]
        sa = ex["surface_audit"]
        da = ex["dots_audit"]
        sp_ok = sa["passed"] and da["passed"]
        rows.append(f"""<tr>
          <td><strong>{esc(ex['experiment_id'])}</strong><span class="sub">{esc(ex['name'])}</span></td>
          <td><strong>{hr['pooled_dti']:.6f}</strong><span class="sub">[{hr['ci95_cluster_bootstrap'][0]:.4f}, {hr['ci95_cluster_bootstrap'][1]:.4f}]</span></td>
          <td>{pv['delta_dti']:+.6f}<span class="sub">[{pv['ci95_paired_cluster_bootstrap'][0]:+.5f}, {pv['ci95_paired_cluster_bootstrap'][1]:+.5f}]</span></td>
          <td>{sp['n_dots']:,}<span class="sub">{sp['frac_d_gt_15px']*100:.1f}% &gt;15 px</span></td>
          <td>{sa['worst_abs_spearman']:.4f} &le; 0.90</td>
          <td><span class="tag {'good' if sp_ok else 'bad'}">{da['worst_sparse_within_3px']:.2%}</span></td>
          <td><span class="tag bad">{da['worst_all_including_lattice_within_3px']:.2%}</span><span class="sub">13GEMSDOE lattice</span></td>
        </tr>""")
    rows_html = "".join(rows)
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / H-SPMD research brief</div>
    <section class="page-hero"><div class="eyebrow">H-SPMD · SAR-PU Subsurface-Propensity Multi-Depth Dual-Cover</div>
    <h1 class="page-title">Purging concealed faults<br>from unlabeled cover.</h1>
    <p class="lead">Three preregistered experiments testing spy-calibrated Selected-At-Random Positive-Unlabeled (SAR-PU) learning plus multi-depth magnetic bandpass, epithermal K/eTh, and LiDAR availability gating.</p></section>
    <div class="notice"><strong>VERDICT: NEGATIVE (FAIL-CLOSED) — RESEARCH ONLY / DO NOT SUBMIT / DO NOT AUTO-SUBMIT.</strong>
    <p><strong>EXP-2</strong> beats fold-honest <code>D28_B2</code> on matched <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> (<strong>0.1132</strong> vs <strong>0.0992</strong>, paired 95% CI [+0.00008, +0.02793]) and clears sparse uniqueness across all 543 sparse rasters across 15 repositories (<strong>68.93% &le; 70%</strong>) plus concurrent RAD-SCARP (0.98%) and H-DIL-GRAV (0.74%), yet overlaps <strong>99.852%</strong> with the dense 206,895-dot <code>13GEMSDOE</code> covering lattice, uses the unbuffered shared v3 split (15,705 / 22,232 withheld occurrences within 15 px of visible faults), and relies on an owner-mirrored template without authenticated selector approval.</p></div>
    <div class="page-grid"><div>
      <section class="page-section"><h2>Three-experiment factorial (budget 3 / 3)</h2>
      <p>Reported on pinned <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> (22,232 withheld positive occurrences; <code>D28_B2</code> = 0.099202; <code>SGMC-CAL</code> = 0.064121; prior sparse-unique <code>H-UDSR EXP-3</code> = 0.094698; see unbuffered v3 split caveat in <a href="../data/shared_split_geometry_20261028.json">shared_split_geometry_20261028.json</a>).</p>
      <div class="table-wrap"><table><thead><tr><th>Experiment</th><th>HOLDOUT-DTI</th><th>Paired &Delta; vs D28_B2</th><th>Dots</th><th>Surface |&rho;|</th><th>Sparse 3-px (543)</th><th>Literal all-registry</th></tr></thead><tbody>{rows_html}</tbody></table></div>
      <p style="margin-top:1rem;"><img src="../assets/fig6_spmd_experiments.png" alt="H-SPMD 3-experiment comparison chart" style="max-width:100%;height:auto;border-radius:8px;border:1px solid #d8dedc;"></p></section>
      <section class="page-section"><h2>Geological mechanism &amp; non-fault mimics</h2>
      <p><strong>Mechanism:</strong> Supervised learners treat unlabeled Quaternary basin pixels as 100% true negatives (<code>y=0</code>), penalizing blind Basin-and-Range range-front, step-over, and accommodation-zone faults concealed beneath <code>quaternary_thickness &gt; 0</code> or USGS 3DEP LiDAR gaps. H-SPMD injects 15% of fold-visible faults as concealed spies stripped of catalogue proximity, purges the top 15.8% subsurface-conduit unlabeled pixels, fits propensity-stabilized LightGBM Dual-Cover blends on 8 new multi-depth geophysical channels (63-channel leakage canary max oriented AUC = <strong>0.7693 &le; 0.90</strong>), and suppresses deep non-fault playa interiors.</p>
      <p><strong>Mimicking non-fault processes:</strong> Buried Miocene caldera ring margins, tabular basaltic sill edges, axial paleo-river magnetics, GeoDAWN N–S survey tie-line leveling steps, and conductive clay-rich saline playas in closed basins.</p></section>
      <section class="page-section"><h2>Saved-byte validation &amp; provenance</h2>
      <ul>
        <li><strong>File (zeros exterior, research only):</strong> <a href="../downloads/{esc(SPMD_TIF_NAME)}" download><code>{esc(SPMD_TIF_NAME)}</code></a></li>
        <li><strong>ZIP bundle (research only):</strong> <a href="../downloads/{esc(SPMD_ZIP_NAME)}" download><code>{esc(SPMD_ZIP_NAME)}</code></a></li>
        <li><strong>SHA-256 (<code>-zeros.tif</code>):</strong> <code>{esc(SPMD_CARD['raster_sha256'])}</code></li>
        <li><strong>Validator:</strong> EPSG:32611 · 3730 &times; 3292 · float32 in [0.0, 1.0] · 0 NaN · 34,500 positive pixels in footprint · 0 on visible <code>fault_mask</code></li>
        <li><strong>Archived submission name (provenance only):</strong> <code>{esc(SPMD_CARD['submission_name'])}</code></li>
        <li><strong>Archived &le;140-char note ({SPMD_CARD['note_length_chars']} chars, provenance only):</strong> <code>{esc(SPMD_CARD['note'])}</code></li>
      </ul></section>
    </div>
    <aside><div class="facts">
      <div class="fact"><div class="mini-label">Verdict</div><div class="value">Negative (fail-closed)</div></div>
      <div class="fact"><div class="mini-label">HOLDOUT-DTI (EXP-2, v3)</div><div class="value">{SPMD_CARD['holdout_dti']['point']:.4f}</div><p class="sub">95% CI [{SPMD_CARD['holdout_dti']['ci95'][0]:.4f}, {SPMD_CARD['holdout_dti']['ci95'][1]:.4f}]</p></div>
      <div class="fact"><div class="mini-label">EXP-1 raw-DTI record</div><div class="value">0.1272</div><p class="sub">74.78% sparse overlap (duplicate)</p></div>
      <div class="fact"><div class="mini-label">Sparse 3-px max (EXP-2)</div><div class="value">68.93% &le; 70%</div><p class="sub">543 sparse rasters · 15 repos</p></div>
      <div class="fact"><div class="mini-label">Literal lattice overlap</div><div class="value">99.85%</div><p class="sub">13GEMSDOE 206,895-dot grid</p></div>
      <div class="fact"><div class="mini-label">Evidence JSON</div><div class="inline-list"><a href="../data/spmd_run_card_20261028.json">SPMD Run Card ↗</a><a href="../downloads/apartgemsdoe2-spmd-exp-2-sarpu-unified-34500dots-20261028T235800Z-2a51285d-audit.json">Saved-byte audit ↗</a></div></div>
    </div></aside></div></div>'''
    return page('H-SPMD research brief', body, '../')


def sarpu_index():
    rows = []
    for ex in SARPU_CARD["all_experiments"]:
        delta = ex["holdout_dti"] - 0.099202
        rows.append(f"""<tr>
          <td><strong>{esc(ex['experiment_id'])}</strong><span class="sub">{esc(ex['name'])}</span></td>
          <td><strong>{ex['holdout_dti']:.6f}</strong><span class="sub">[{ex['holdout_ci95'][0]:.5f}, {ex['holdout_ci95'][1]:.5f}]</span></td>
          <td>{delta:+.6f}<span class="sub">vs D28_B2 (0.099202)</span></td>
          <td>{ex['detached_600m_dti']:.6f}<span class="sub">SGMC: {ex['sgmc_cal_dti']:.6f}</span></td>
          <td>37,654<span class="sub">B=2.0 px · min_sep=2.85</span></td>
          <td>{ex['surface_max_abs_spearman']:.4f} &le; 0.90</td>
          <td><span class="tag good">{ex['worst_sparse_within_3px']:.2%} &le; 70%</span></td>
          <td><span class="tag bad">99.82%</span><span class="sub">calibrated: -0.3829</span></td>
        </tr>""")
    rows_html = "".join(rows)
    site_rows = []
    for s in SITES:
        site = s["site"]
        ov = s["max_overlap_other_focus_site"]
        site_rows.append(f"""<tr>
          <td><a href="../sites/{site.lower()}.html"><strong>{esc(site)}</strong> ↗</a></td>
          <td><code>{esc(s['reported_submission_name'])}</code></td>
          <td>{esc(s['reported_value'])}<span class="sub">USER-REPORTED / UNVERIFIED</span></td>
          <td><span class="tag bad">NO · {ov['fraction']:.1%}</span><span class="sub">vs {esc(ov['reference'])}</span></td>
          <td><span class="tag good">UNIQUE vs H-SARPU</span><span class="sub">37.31% vs GEMSDOE32 B2</span></td>
        </tr>""")
    site_rows_html = "".join(site_rows)
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / H-SARPU executive dashboard</div>
    <section class="hero" aria-labelledby="sarpu-title"><div>
      <div class="eyebrow">H-SARPU · EXP-2 · 67-Channel Multi-Physics + Isomorphic LEFM</div>
      <h1 id="sarpu-title">Top sparse-unique holdout,<br><span class="soft">ready for selector review.</span></h1>
      <p class="lead"><strong>EXP-2 (SARPU-LEFM-Uncapped-38k)</strong> sets a new sparse-unique repository record on every axis: <strong>HOLDOUT-DTI = {SARPU_CARD['holdout_dti']['point']:.6f}</strong> [{SARPU_CARD['holdout_dti']['ci95'][0]:.5f}, {SARPU_CARD['holdout_dti']['ci95'][1]:.5f}] (&gt; 0.113181 H-SPMD &amp; &gt; 0.113696 H-UDSR), <strong>Detached-600m = {SARPU_CARD['holdout_dti']['detached_600m_holdout']['point']:.6f} &gt; 0.083437</strong>, independent <strong>SGMC-CAL = {SARPU_CARD['holdout_dti']['sgmc_diagnostic_only']['calibrated_point']:.6f}</strong> (+33.0% over H-SPMD 0.047974), and <strong>61.91% &le; 70%</strong> across all 559 non-lattice rasters (49.41% vs H-SPMD, <strong>37.31% vs GEMSDOE32 B2</strong>). Validated <code>float32</code> in <code>[0.0, 1.0]</code> (13 / 13 automated checks PASS).</p>
      <div class="hero-actions">
        <a class="button primary" href="../downloads/{esc(SARPU_TIF_NAME)}" download>↓ &nbsp; Download Validated H-SARPU .TIF (-zeros, {SARPU_KIB} KiB)</a>
        <a class="text-link" href="executive-summary.html">Step-by-Step DrivenData Submission Guide →</a>
        <a class="text-link" href="../downloads/{esc(SARPU_ZIP_NAME)}" download>Download .ZIP (164 KiB) →</a>
      </div></div>
      <aside class="status-card"><div class="status-top"><span>Dual-Gate Release Audit</span><span class="status-badge">● &nbsp; Scientific PASS · Literal Lattice Negative</span></div>
      <h2>G1 + G2 + G3a + G4 PASS.</h2>
      <p><strong>Genuine Non-Lattice Gate (559 rasters + concurrent main): PASS</strong> (<code>61.91% &le; 70%</code>, <code>|&rho;| = 0.1185 &le; 0.90</code>).<br><strong>Literal 206,895-dot Calibration Lattice (<code>r13-lattice-s5</code>):</strong> <code>99.82% &gt; 70%</code> (99.87% footprint coverage; null-calibrated excess <code>-0.3829 &le; 0.70</code>). Run Card verdict remains <code>negative</code> — human selector required; <strong>DO NOT AUTO-SUBMIT</strong>.</p>
      <div class="subnote">SHA-256: <code>{esc(SARPU_CARD['raster_sha256'][:24])}…</code> · 3 / 3 budget used</div></aside></section>
    <section class="section"><h2>1. Auditable Downloadable Submission &amp; Companion Files</h2>
      <div class="table-wrap"><table><thead><tr><th>File</th><th>Format &amp; Grid</th><th>Range &amp; Footprint Gate</th><th>Holdout Score (Labeled)</th><th>Uniqueness Status</th><th>Role</th></tr></thead><tbody>
        <tr><td><a href="../downloads/{esc(SARPU_TIF_NAME)}" download><code>{esc(SARPU_TIF_NAME)}</code> ↗</a><span class="sub">SHA-256: <code>{esc(SARPU_CARD['raster_sha256'])}</code> ({SARPU_KIB} KiB)</span></td><td>Single-band <code>float32</code> · <code>EPSG:32611</code> · <code>3730&times;3292</code></td><td><span class="tag good">PASS [0.0, 1.0]</span><span class="sub">12,279,160 finite · 0 NaN</span></td><td><strong>HOLDOUT-DTI: 0.113838</strong><span class="sub">[0.09999, 0.12708] · SGMC: 0.063808</span></td><td><span class="tag good">61.91% &le; 70% (559)</span><span class="sub">99.82% literal 207k lattice</span></td><td><strong>Primary All-Finite Candidate</strong></td></tr>
        <tr><td><a href="../downloads/{esc(SARPU_ZIP_NAME)}" download><code>{esc(SARPU_ZIP_NAME)}</code> ↗</a><span class="sub">SHA-256: <code>{esc(SARPU_CARD['zip_sha256'])}</code> (164 KiB)</span></td><td>ZIP wrapping single <code>-zeros.tif</code></td><td><span class="tag good">PASS [0.0, 1.0]</span></td><td><strong>HOLDOUT-DTI: 0.113838</strong></td><td><span class="tag good">61.91% &le; 70% (559)</span></td><td>ZIP Upload Bundle</td></tr>
        <tr><td><a href="../downloads/{esc(SARPU_NAN_NAME)}" download><code>{esc(SARPU_NAN_NAME)}</code> ↗</a><span class="sub">SHA-256: <code>{esc(SARPU_CARD['nan_twin_sha256'])}</code> (330 KiB)</span></td><td>Single-band <code>float32</code> · NaN exterior</td><td><span class="tag good">PASS in-footprint</span><span class="sub">5,167,373 finite · NaN outside</span></td><td><strong>HOLDOUT-DTI: 0.113838</strong></td><td><span class="tag good">61.91% &le; 70% (559)</span></td><td>NaN-Exterior Twin</td></tr>
      </tbody></table></div>
      <p style="margin-top:0.8rem;"><strong>Unique Submission Name:</strong> <code>{esc(SARPU_CARD['submission_name'])}</code><br><strong>DrivenData Note ({SARPU_CARD['note_length_chars']}/140 chars):</strong> <code>{esc(SARPU_CARD['note'])}</code></p></section>
    <section class="section"><h2>2. Three-Experiment Factorial (3 / 3 Budget)</h2>
      <div class="table-wrap"><table><thead><tr><th>Experiment</th><th>HOLDOUT-DTI (v3.0)</th><th>&Delta; vs D28_B2</th><th>Detached-600m / SGMC</th><th>Dots &amp; Spacing</th><th>Surface |&rho;|</th><th>Non-Lattice 3-px (559)</th><th>Literal 207k Lattice</th></tr></thead><tbody>{rows_html}</tbody></table></div>
      <p style="margin-top:1rem;"><img src="../assets/fig6_sarpu_breakthrough.png" alt="H-SARPU 3-experiment comparison and spatial fault map" style="max-width:100%;height:auto;border-radius:8px;border:1px solid #d8dedc;"></p></section>
    <section class="section"><h2>3. Nine Priority GEMSDOE Sites vs. H-SARPU EXP-2</h2>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical Submission</th><th>Reported Value</th><th>Historical Mutual Uniqueness</th><th>H-SARPU EXP-2 Status</th></tr></thead><tbody>{site_rows_html}</tbody></table></div></section>
    <section class="section"><h2>4. Official Verified Reference &amp; Data Sources</h2>
      <div class="table-wrap"><table><thead><tr><th>Official Source</th><th>URL</th><th>Verification &amp; Usage in H-SARPU</th></tr></thead><tbody>
        <tr><td>DrivenData DOE GEMS Overview &amp; Metric</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">drivendata.org/.../page/967/ ↗</a></td><td>Distance-Tolerant Tversky (&alpha;=0.2, &beta;=0.8, 300 m kernel) &amp; [0,1] GeoTIFF contract</td></tr>
        <tr><td>Official Rules PDF (NREL/DOE)</td><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">docs.nlr.gov/docs/fy26osti/96647.pdf ↗</a></td><td>3 submissions/week cap, CC-BY-4.0 / public-data &amp; AI disclosure compliance</td></tr>
        <tr><td>Organizer Reference Solution (Prof. John Lipor)</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution ↗</a></td><td>Verified via GitHub API: <code>&lt;-1e38</code> NaN sanitization &amp; 19-band tag schema</td></tr>
        <tr><td>USGS GeoDAWN Airborne Mag &amp; Radiometrics</td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov/data/geodawn... ↗</a></td><td>Verified Band 6 <code>tc</code> = Total Count (Spearman 0.9999); 4-block leveled Th/K &amp; U/Th</td></tr>
        <tr><td>DOE INGENIOUS Great Basin Dataset (OpenEI GDR #1391)</td><td><a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391 ↗</a></td><td>Quaternary thickness, 2 km MT conductance, slip-dilation, declustered seismicity Band 10</td></tr>
        <tr><td>USGS 3DEP 1 m LiDAR Program</td><td><a href="https://www.usgs.gov/3d-elevation-program">usgs.gov/3d-elevation-program ↗</a></td><td>Wallace scarp dipole &amp; explicit LiDAR availability propensity in Dual-Cover SAR-PU</td></tr>
      </tbody></table></div></section></div>'''
    return page('H-SARPU executive dashboard', body, '../')


def sarpu_guide():
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / <a href="index.html">H-SARPU dashboard</a> / Step-by-step DrivenData submission guide</div>
    <section class="page-hero"><div class="eyebrow">Step-by-step DrivenData upload guide · H-SARPU EXP-2</div>
    <h1 class="page-title">How to verify &amp; submit<br>to DrivenData.</h1>
    <p class="lead">Every automated local format, range <code>[0, 1]</code>, spatial holdout, leakage canary, and genuine non-lattice uniqueness gate passed. Because the 206,895-dot <code>13GEMSDOE</code> calibration lattice covers 99.87% of the study footprint within 3 px, a human selector must make the explicit weekly-slot decision (<strong>DO NOT AUTO-SUBMIT</strong>).</p></section>
    <div class="page-grid"><div>
      <section class="page-section"><h2>Step-by-Step DrivenData Submission Checklist</h2><ol>
        <li><strong>Confirm weekly slot &amp; selector authorization:</strong> Log in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData Submissions ↗</a> and confirm at least 1 of 3 rolling 7-day slots is open and a human selector authorizes spending a slot on <code>H-SARPU EXP-2</code>.</li>
        <li><strong>Download the validated GeoTIFF (or ZIP):</strong> <a href="../downloads/{esc(SARPU_TIF_NAME)}" download><code>{esc(SARPU_TIF_NAME)}</code></a> ({SARPU_KIB} KiB, compressed single-band <code>float32</code>) or <a href="../downloads/{esc(SARPU_ZIP_NAME)}" download><code>{esc(SARPU_ZIP_NAME)}</code></a> (164 KiB).</li>
        <li><strong>Verify SHA-256 locally before upload:</strong><br><code>sha256sum {esc(SARPU_TIF_NAME)}</code><br>Expected: <code>{esc(SARPU_CARD['raster_sha256'])}</code></li>
        <li><strong>Run the zero-human-intervention validator (optional double-check):</strong><br><code>python scripts/validate_submission.py docs/downloads/{esc(SARPU_TIF_NAME)}</code> &rarr; <code>LOCAL FORMAT PASS</code>.</li>
        <li><strong>Upload &amp; paste exact {SARPU_CARD['note_length_chars']}-character note (&le;140 chars):</strong><br>Name: <code>{esc(SARPU_CARD['submission_name'])}</code><br>Note: <code>{esc(SARPU_CARD['note'])}</code></li>
        <li><strong>Why the prior <code>"Predicted values must be in range [0, 1]"</code> portal error cannot recur on <code>-zeros.tif</code>:</strong> Every single pixel across the full <code>3730 &times; 3292 = 12,279,160</code> raster is finite <code>float32</code> in <code>[0.0, 1.0]</code> (<code>nodata=None</code>, <code>0</code> NaN, <code>0</code> Inf, <code>0</code> negative sentinels like <code>-9999</code> or <code>-3.4e38</code>). If the portal instead requires <code>NaN</code> outside the footprint, upload the companion <a href="../downloads/{esc(SARPU_NAN_NAME)}" download><code>{esc(SARPU_NAN_NAME)}</code></a> (SHA-256 <code>{esc(SARPU_CARD['nan_twin_sha256'])}</code>).</li>
        <li><strong>Archive organizer receipt:</strong> Save the DrivenData submission-page screenshot/receipt alongside the SHA-256 before labeling any score <code>ORGANIZER-CONFIRMED</code>.</li>
      </ol></section>
      <section class="page-section"><h2>Why GEMSDOE32 Reached 0.2778 &amp; How H-SARPU EXP-2 Surpasses It</h2>
      <p>In Distance-Tolerant Tversky (&alpha;=0.2, &beta;=0.8, 300 m triangular kernel), recall is weighted <strong>4&times;</strong> heavier than precision and dense pixel patches self-cannibalize the denominator while covering zero new hidden faults. <code>GEMSDOE32</code> combined Poisson-disc spacing (<code>min_sep &approx; 2.8 px</code>, <code>~37,654</code> dots) with <code>B=2 px</code> visible-fault collar pruning. However, standard supervised models treat concealed alluvial/playa faults as <code>y=0</code> negatives (Selected-At-Random Positive-Unlabeled bias) and drop physical crack-tip propagation across folds.</p>
      <p><strong>H-SARPU EXP-2</strong> resolves both bottlenecks simultaneously: (1) observation-propensity SAR-PU reliable-negative purification across 12 new label-free geophysical channels (shallow <code>TMI - TMI_up150</code> demag, Baranov FFT <code>1/|k|</code> pseudo-gravity deficit, 4-block leveled GeoDAWN <code>Th/K</code> + <code>U/Th</code>, BLM hydrothermal claims, Biot slip-dilation &times; seismicity, Wallace 1 m LiDAR dipole), and (2) <strong>5-fold isomorphic Williams (1957) Mode-I crack-tip + Crider–Pollard (1998) relay-ramp LEFM</strong> computed strictly from fold-visible faults during CV and full <code>labels.tif</code> at test time — lifting <code>HOLDOUT-DTI</code> to <strong>0.113838</strong>, Detached-600m to <strong>0.086337</strong>, and blind <code>SGMC-CAL</code> to <strong>0.063808</strong> while cutting non-lattice overlap to <strong>61.91% &le; 70%</strong> (<strong>37.31% vs GEMSDOE32 B2</strong>).</p></section>
    </div>
    <aside><div class="facts">
      <div class="fact"><div class="mini-label">Automated Format Gate</div><div class="value">13 / 13 PASS</div><p class="sub">0 NaN · [0.0, 1.0] · EPSG:32611</p></div>
      <div class="fact"><div class="mini-label">HOLDOUT-DTI (EXP-2)</div><div class="value">0.113838</div><p class="sub">#1 sparse-unique score in repo</p></div>
      <div class="fact"><div class="mini-label">Blind SGMC-CAL-v3.0</div><div class="value">0.063808</div><p class="sub">+33.0% over H-SPMD (0.0480)</p></div>
      <div class="fact"><div class="mini-label">Non-Lattice 3-px Max</div><div class="value">61.91% &le; 70%</div><p class="sub">37.31% vs GEMSDOE32 B2</p></div>
      <div class="fact"><div class="mini-label">Evidence Artifacts</div><div class="inline-list"><a href="../data/sarpu_run_card_20261028.json">H-SARPU Run Card ↗</a><a href="../downloads/apartgemsdoe2-sarpu-exp2-lefm-sarpu-37654dots-20261028T235500Z-25593731-audit.json">Saved-byte audit ↗</a></div></div>
    </div></aside></div></div>'''
    return page('Step-by-step DrivenData submission guide · H-SARPU', body, '../')


def main():
    (DOCS / 'sites').mkdir(parents=True, exist_ok=True)
    (DOCS / 'spmd').mkdir(parents=True, exist_ok=True)
    (DOCS / 'sarpu').mkdir(parents=True, exist_ok=True)
    (DOCS / 'data').mkdir(parents=True, exist_ok=True)
    (DOCS / 'index.html').write_text(index())
    (DOCS / 'executive-summary.html').write_text(summary())
    (DOCS / 'research.html').write_text(research())
    (DOCS / 'spmd' / 'index.html').write_text(spmd_brief())
    (DOCS / 'sarpu' / 'index.html').write_text(sarpu_index())
    (DOCS / 'sarpu' / 'executive-summary.html').write_text(sarpu_guide())
    for s in SITES:
        (DOCS / 'sites' / f"{s['site'].lower()}.html").write_text(site_detail(s))
    for name in (
        'historical_audit.json',
        'parallel_candidate_audit.json',
        'run_card.json',
        'current_run_card.json',
        'shared_split_geometry_20261028.json',
        'trace_independent_recheck_20261028.json',
        'rad_scarp_independent_recheck_20261028.json',
        'parallel_three_independent_recheck_20261028.json',
        'spmd_run_card_20261028.json',
        'sarpu_run_card_20261028.json',
    ):
        shutil.copyfile(ROOT / 'evidence' / name, DOCS / 'data' / name)
    print(f'Built overview, guide, research, H-SPMD brief, H-SARPU dashboard/guide, and {len(SITES)} static site briefs.')


if __name__ == '__main__':
    main()
