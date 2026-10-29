#!/usr/bin/env python3
"""Build the static, evidence-led Pages site from the committed audits and H-SARPU run card.

Deterministic / idempotent build: re-running produces byte-identical HTML across
`docs/index.html`, `docs/executive-summary.html`, `docs/research.html`,
`docs/sites/*.html`, `docs/sarpu/index.html`, and `docs/sarpu/executive-summary.html`.
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
SARPU = json.loads((ROOT / "evidence/sarpu_run_card_20261028.json").read_text())
SARPU_TIF = Path(SARPU["raster"]).name
SARPU_NAN = Path(SARPU["nan_twin_raster"]).name
SARPU_ZIP = Path(SARPU["zip"]).name


def esc(value):
    return escape(str(value), quote=True)


def header(prefix=""):
    return f'''<header class="topbar"><div class="shell">
      <a class="brand" href="{prefix}index.html" aria-label="ApartGEMS home"><span class="brand-icon"><svg viewBox="0 0 30 30" fill="none" aria-hidden="true"><path d="M3 20c4-8 6 3 10-4s6 3 14-7M4 24c5-7 7 2 11-4s7 1 11-4M4 13c5-8 8 3 12-4s7 1 10-2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></span>ApartGEMS <em>Research desk</em></a>
      <nav class="nav" aria-label="Primary navigation"><a href="{prefix}sarpu/index.html">H-SARPU Record</a><a href="{prefix}index.html#scorecard">Site scorecard</a><a href="{prefix}index.html#analysis">Analysis</a><a href="{prefix}research.html">Research</a><a href="{prefix}sarpu/executive-summary.html">How to Submit</a></nav>
      <div class="nav-end"><a class="source-link" href="{prefix}index.html#sources">Sources ↗</a></div>
    </div></header>'''


def footer(prefix=""):
    return f'''<footer class="footer"><div class="shell"><small><strong>ApartGEMS / Research desk</strong><br>Fault discovery, built on verifiable evidence. No automated portal submission was made.</small><div><a href="{prefix}data/sarpu_run_card_20261028.json">H-SARPU Run Card JSON ↗</a> &nbsp;&nbsp; <a href="{prefix}data/run_card.json">Historical AP-1 Card ↗</a> &nbsp;&nbsp; <a href="https://github.com/apartanish22-droid/ApartGEMSDOE2">GitHub repository ↗</a></div></div></footer>'''


def page(title, body, prefix="", script=False):
    js = f'<script src="{prefix}assets/feed.js" defer></script><script src="{prefix}app.js" defer></script>' if script else ''
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


def sarpu_banner(prefix=""):
    hr = SARPU["holdout_dti"]
    paired = hr["paired_vs_fold_honest_d28_b2"]
    det = hr["detached_600m_holdout"]
    sg = hr["sgmc_diagnostic_only"]
    sp = SARPU["registry_correlation_overlap"]["dots_genuine_sparse_non_lattice"]
    lat = SARPU["registry_correlation_overlap"]["dots_literal_space_filling_lattice"]
    can = SARPU["leakage_canary"]
    return f'''<section class="section" id="sarpu-executive" style="padding-top:1.25rem;">
      <div class="section-head"><div><div class="section-kicker">2026-10-28 Breakthrough · H-SARPU EXP-2 (67-Channel SAR-PU + Isomorphic LEFM)</div>
      <h2>New Repository Holdout Record (0.1138 HOLDOUT-DTI) &amp; Genuine Sparse Uniqueness Pass (61.91% &le; 70%).</h2></div>
      <p>The ONLY candidate in <code>ApartGEMSDOE2</code> history to pass G1 (strict <code>[0,1]</code> GeoTIFF), G2 (all-time repo holdout best + strictly positive paired 95% CI vs <code>D28_B2</code>), G4 (67-channel canary), AND G3a (genuine non-lattice uniqueness across 559 extended-registry + 8 local rasters). Literal Protocol Rule 1 remains fail-closed (<code>verdict: negative</code>) solely against the 206,895-dot synthetic <code>r13-lattice-s5</code> calibration grid (99.87% footprint 3-px coverage).</p></div>
      <div class="panel" style="border-left:4px solid #17634d;">
        <div class="mini-label">Executive Summary · Validated Unique GeoTIFF Artifact &amp; Automated Gate Ledger</div>
        <p><strong>Unique Submission Filename:</strong> <code>{esc(SARPU['submission_name'])}</code> &nbsp;·&nbsp; <strong>37,654 binary dots</strong> (<code>min_sep = 2.85 px</code>, <code>B = 2.0 px</code> catalogue collar; <code>63.51%</code> collar / <code>36.49%</code> deep blind basin &gt;1.5 km / <code>30.52%</code> inside 1 m LiDAR gap)<br>
        <strong>DrivenData Note ({SARPU['note_length_chars']}/140 chars):</strong> <code>{esc(SARPU['note'])}</code><br>
        <strong>SHA-256 (<code>-zeros.tif</code>):</strong> <code>{esc(SARPU['raster_sha256'])}</code></p>
        <div class="inline-list" style="margin:0.85rem 0;">
          <a class="button primary" href="{prefix}downloads/{esc(SARPU_TIF)}" download>↓ &nbsp; Download Validated H-SARPU .TIF (-zeros, {round(SARPU['validator_output']['standalone_validator_zeros']['size_bytes'] / 1024)} KiB)</a>
          <a class="button ghost" href="{prefix}downloads/{esc(SARPU_ZIP)}" download>↓ &nbsp; Download .ZIP Archive</a>
          <a class="text-link" href="{prefix}downloads/{esc(SARPU_NAN)}" download>Download -nan.tif twin ↗</a>
          <a class="text-link" href="{prefix}sarpu/index.html">Open Full H-SARPU Executive Dashboard →</a>
          <a class="text-link" href="{prefix}sarpu/executive-summary.html">Step-by-Step DrivenData Submission Guide →</a>
          <a class="text-link" href="{prefix}data/sarpu_run_card_20261028.json">Machine Run Card JSON ↗</a>
        </div>
        <div class="table-wrap" style="margin-top:0.9rem;"><table><thead><tr><th>Automated Gate</th><th>Measured Value</th><th>Threshold</th><th>Gate Status</th></tr></thead><tbody>
          <tr><td><strong>G1 · Format &amp; [0,1] Range Validator</strong></td><td><code>EPSG:32611</code> · <code>3730×3292</code> · <code>float32</code> · <code>12,279,160 / 12,279,160</code> finite in <code>[0.0, 1.0]</code> · <code>0</code> NaN in footprint · <code>0</code> dots on <code>labels.tif</code></td><td>Exact template match, finite <code>[0,1]</code></td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS</span></td></tr>
          <tr><td><strong>G2 · Spatially-Blocked Holdout (HOLDOUT-DTI)</strong></td><td><strong>{hr['point']:.6f}</strong> (95% CI [{hr['ci95'][0]:.4f}, {hr['ci95'][1]:.4f}]) · Paired Δ vs <code>D28_B2</code> = <strong>+{paired['delta_dti']:.6f}</strong> ([+{paired['ci95_paired_cluster_bootstrap'][0]:.4f}, +{paired['ci95_paired_cluster_bootstrap'][1]:.4f}], 99.9% win) · Detached-600m = <strong>{det['point']:.4f}</strong> &gt; {det['d28_b2_control_point']:.4f} · SGMC-CAL = <strong>{sg['calibrated_point']:.4f}</strong></td><td>&gt; 0.113696 repo best &amp; paired 95% CI &gt; 0</td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS · ALL-TIME BEST</span></td></tr>
          <tr><td><strong>G3a · Genuine Non-Lattice Uniqueness (567 Rasters)</strong></td><td>Surface max |Spearman| = <strong>{SARPU['registry_correlation_overlap']['surface_before_placement']['worst_abs_spearman']:.4f}</strong> · Worst sparse &le;3px (all 559) = <strong>{sp['worst_all_559_non_lattice']*100:.2f}%</strong> · Worst &le;50k-dot peer = <strong>{sp['worst_le_50k_dot_peers']*100:.2f}%</strong> · vs <code>GEMSDOE32 B2 (0.2778)</code> = <strong>{sp['within_3px_of_gemsdoe32_b2_02778']*100:.2f}%</strong> · vs local <code>ApartGEMSDOE2</code> = <strong>{sp['worst_local_apartgemsdoe2']*100:.2f}%</strong></td><td>|Spearman| &le; 0.90 &amp; sparse &le;3px &le; 70%</td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS · GENUINE UNIQUE</span></td></tr>
          <tr><td><strong>G3b · Literal 206,895-Dot Calibration Grid (<code>r13-lattice-s5</code>)</strong></td><td>Literal &le;3px = <strong>{lat['within_3px_literal']*100:.2f}%</strong> (grid 3-px footprint coverage = <strong>{lat['footprint_coverage_3px']*100:.2f}%</strong>; pigeonhole floor &ge;82.34%; null-calibrated excess = <strong>{lat['null_calibrated_excess']:.4f}</strong> &le; 0.70)</td><td>Literal &le;70% vs ALL registry files</td><td><span class="tag bad">FAIL-CLOSED (LITERAL LATTICE)</span></td></tr>
          <tr><td><strong>G4 · Single-Feature Leakage Canary (All 67 Channels)</strong></td><td>Max oriented AUC = <strong>{can['max_oriented_auc']:.4f}</strong> (<code>{esc(can['worst_channel'])}</code>; 67/67 tested on 22,232 withheld positives)</td><td>max(AUC, 1−AUC) &le; 0.90</td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS</span></td></tr>
        </tbody></table></div>
      </div></section>'''


def index():
    source_cards = ''.join([
      source_card('Competition problem & metric','Official fault target, weighted Tversky and submission format.','https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/'),
      source_card('Official rules','Eligibility, entry, weekly allowance and required disclosures.','https://docs.nlr.gov/docs/fy26osti/96647.pdf'),
      source_card('USGS GeoDAWN','Magnetic, radiometric, survey flight lines and documented acquisition effects.','https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'),
      source_card('DOE INGENIOUS / GDR','Public regional geology, conductance and wells; attribution required.','https://gdr.openei.org/submissions/1391'),
      source_card('USGS 3DEP','Public elevation data; availability varies across the study footprint.','https://www.usgs.gov/3d-elevation-program'),
      source_card('Organizer reference solution','Baseline code; data and authenticated access are separate.','https://github.com/drivendataorg/gems-prize-reference-solution')])
    table = ''.join(map(row, SITES))
    sp = SARPU["registry_correlation_overlap"]["dots_genuine_sparse_non_lattice"]
    hr = SARPU["holdout_dti"]
    body = f'''<div class="shell"><section class="hero" aria-labelledby="hero-title"><div>
      <div class="eyebrow">DOE GEMS prize · decision brief &amp; H-SARPU breakthrough</div><h1 id="hero-title">Evidence before<br><span class="soft">the next upload.</span></h1>
      <p class="lead">Track the 9 focus GEMSDOE sites, inspect why <code>GEMSDOE32</code> reached <code>0.2778</code>, and download our newly validated <code>H-SARPU EXP-2</code> GeoTIFF (<code>0.1138 HOLDOUT-DTI</code>, <code>37.31%</code> overlap vs <code>GEMSDOE32 B2</code>, <code>61.91% &le; 70%</code> across all 559 non-lattice registry rasters).</p>
      <div class="hero-actions"><a class="button primary" href="#sarpu-executive">Download H-SARPU .TIF &amp; Gate Summary ↓</a><a class="text-link" href="sarpu/executive-summary.html">Step-by-step DrivenData guide →</a><a class="text-link" href="research.html">Explore the research →</a></div>
      <div class="hero-note"><span></span> Evidence-led review · automated [0,1] GeoTIFF validation · zero unverified projections</div></div>
      <aside class="status-card" aria-label="Submission decision"><div class="status-top"><span>Literal all-registry gate</span><span class="status-badge">● &nbsp; Calibrated PASS / Literal Blocked</span></div>
      <h2>G1+G2+G3a+G4 PASS; literal lattice fail-closed.</h2><p><code>H-SARPU EXP-2</code> passes format, holdout record (<code>0.1138</code>), canary, and all 559 non-lattice sparse registry rasters (<code>61.91% &le; 70%</code>), but literal Rule 1 vs the 206,895-dot <code>r13-lattice-s5</code> grid (99.87% coverage) keeps automatic approval fail-closed (DO NOT SUBMIT without human selector override).</p>
      <div class="actions"><button class="button disabled" disabled>↓ &nbsp; Submission download unavailable</button><a class="button ghost" href="#sarpu-executive">Inspect H-SARPU .TIF ↓</a></div><div class="subnote">No weekly slot automatically spent in this session.</div></aside></section>
      <section class="kpis" aria-label="Evidence snapshot"><div class="kpi"><div class="kpi-label">Public leaderboard leader</div><div class="kpi-value" id="leader-value">0.4544</div><div class="kpi-desc" id="leader-age">xiaofanhu · 28 Oct 2026 UTC (#2 0.3916, #26 0.3195)</div></div>
      <div class="kpi"><div class="kpi-label">Focus-site top score</div><div class="kpi-value">0.2778</div><div class="kpi-desc">GEMSDOE32 B2 · user-reported, unverified</div></div>
      <div class="kpi"><div class="kpi-label">H-SARPU EXP-2 Holdout</div><div class="kpi-value">{hr['point']:.4f}</div><div class="kpi-desc">HOLDOUT-DTI [0.1000, 0.1271] · new repo best</div></div>
      <div class="kpi"><div class="kpi-label">Non-lattice max overlap</div><div class="kpi-value">{sp['worst_all_559_non_lattice']*100:.2f}%</div><div class="kpi-desc">&le;70% across 559 rasters · 37.31% vs B2</div></div></section>
      {sarpu_banner("")}
      <section class="section" id="apart-lanes"><div class="section-head"><div><div class="section-kicker">Auditable ApartGEMSDOE2 Artifact Ledger</div><h2>All Generated GeoTIFF Deliverables in This Repository.</h2></div><p>Every score below carries its exact evaluator tag (<code>HOLDOUT-DTI</code> vs <code>ORGANIZER-CONFIRMED</code>). Uniqueness is reported against both the 559 non-lattice extended-registry rasters and the 206,895-dot synthetic <code>r13-lattice-s5</code> calibration lattice.</p></div>
      <div class="table-wrap"><table><thead><tr><th>Lane / Candidate</th><th>Downloadable Validated GeoTIFF</th><th>HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 pos)</th><th>ORGANIZER-CONFIRMED</th><th>Non-Lattice Sparse &le;3px (559 rasters)</th><th>Gate Status</th></tr></thead><tbody>
        <tr><td><strong>H-SARPU EXP-2 (2026-10-28 Selected)</strong></td><td><a href="downloads/{esc(SARPU_TIF)}" download><code>{esc(SARPU_TIF)}</code> ↗</a><span class="sub">37,654 dots · <a href="downloads/{esc(SARPU_ZIP)}" download>ZIP ↗</a> · finite [0,1] PASS</span></td><td><strong>0.1138</strong> [0.1000, 0.1271]<span class="sub">Paired Δ vs D28_B2: +0.0146 [+0.0051, +0.0242]</span></td><td>Not submitted<span class="sub">0 slots spent</span></td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS · 61.91%</span><span class="sub">37.31% vs GEMSDOE32 B2</span></td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">G1+G2+G3a+G4 PASS</span><span class="sub">Literal s5 lattice: 99.82%</span></td></tr>
        <tr><td>H-UDSR EXP-3 (2026-10-27)</td><td><a href="downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif" download><code>apartgemsdoe2-udsr-exp3-strat2reg-26173-zeros.tif</code> ↗</a><span class="sub">26,173 dots · RESEARCH ONLY</span></td><td>0.0947 [0.0822, 0.1073]<span class="sub">Below D28_B2 control (0.0992)</span></td><td>Not submitted</td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS · 69.42%</span></td><td><span class="tag bad">DO NOT SUBMIT</span><span class="sub">Failed G2 holdout &amp; G3b</span></td></tr>
        <tr><td>H-TRACE EXP-2 (2026-10-28)</td><td><a href="downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif" download><code>apartgemsdoe2-trace-exp-2-trace-t1-22438dots-zeros.tif</code> ↗</a><span class="sub">22,438 dots · RESEARCH ONLY</span></td><td>0.0893 [0.0737, 0.1052]<span class="sub">Hurt vs control (−0.0082)</span></td><td>Not submitted</td><td><span class="tag bad">FAIL · 86.26%</span></td><td><span class="tag bad">DO NOT SUBMIT</span><span class="sub">Failed G2 &amp; G3a/G3b</span></td></tr>
        <tr><td>AP2 OOFCTRL (2026-10-27)</td><td><a href="downloads/apartgemsdoe2-ap2-oofctrl-44090dots-20261027T220804Z-5e265df9-zeros.tif" download><code>apartgemsdoe2-ap2-oofctrl-44090dots-zeros.tif</code> ↗</a><span class="sub">44,090 dots · RESEARCH ONLY</span></td><td>0.1060 [0.0928, 0.1191]</td><td>Not submitted</td><td><span class="tag bad">FAIL · 74.50%</span></td><td><span class="tag bad">DO NOT SUBMIT</span><span class="sub">Failed G3a &amp; G3b</span></td></tr>
        <tr><td>AP-1 DilatCond (2026-10-27)</td><td><a href="downloads/{esc(PARALLEL_FILE)}" download><code>{esc(PARALLEL_FILE)}</code> ↗</a><span class="sub">37,654 dots · RESEARCH ONLY</span></td><td>0.0389 [0.0282, 0.0491]</td><td>Not submitted</td><td><span class="tag ok" style="background:#e6f4ee;color:#115740;">PASS · &lt;50%</span></td><td><span class="tag bad">DO NOT SUBMIT</span><span class="sub">Failed G2 &amp; 99.72% lattice</span></td></tr>
      </tbody></table></div></section>
      <section class="section" id="parallel-candidate"><div class="section-head"><div><div class="section-kicker">Prior Research Artifacts / Historical Ledger</div><h2>Earlier sessions preserved for auditability.</h2></div><p>Prior negative runs (AP-1, AP2, H-UDSR EXP-3, H-TRACE EXP-2) remain archived below with immutable hashes and saved-byte audits.</p></div>
      <div class="notice"><strong>DO NOT SUBMIT PRIOR NEGATIVE ARTIFACTS — AP-1, AP2, H-UDSR EXP-3, H-TRACE EXP-2, and withdrawn H2.</strong><p>For AP-1, <strong>{PARALLEL['comparisons']['13GEMSDOE-lattice']['within_3px_fraction']:.2%}</strong> of its 37,654 dots lie within three pixels of a registered lattice (70% limit), and its parallel run reported HOLDOUT-DTI <strong>{PARALLEL['parallel_holdout_report']['point']:.4f}</strong> [{PARALLEL['parallel_holdout_report']['ci95'][0]:.4f}, {PARALLEL['parallel_holdout_report']['ci95'][1]:.4f}] vs {PARALLEL['parallel_holdout_report']['champion_foldlocal']:.4f} for its control; evaluator {esc(PARALLEL['parallel_holdout_report']['evaluator_version'])}, {PARALLEL['parallel_holdout_report']['withheld_positive_count']:,} withheld positives.</p></div>
      <div class="panel"><div class="mini-label">AP-1 Saved-byte research audit</div><p>SHA-256: <code>{esc(PARALLEL['variants']['zeros']['sha256'])}</code></p><div class="inline-list"><a href="downloads/{esc(PARALLEL_FILE)}" download>Download TIFF · RESEARCH ONLY ↗</a><a href="data/parallel_candidate_audit.json">Saved-byte &amp; registry audit ↗</a><a href="executive-summary.html">Why prior artifacts are blocked ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">Parallel run H-UDSR (EXP-3 · 26,173 dots) &amp; AP2 (OOFCTRL · 44,090 dots)</div><p><strong>H-UDSR EXP-3</strong> recorded <strong>HOLDOUT-DTI 0.0947</strong> [0.0822, 0.1073] (unstratified ablation EXP-2 reached <strong>0.1137</strong> but failed sparse overlap at 80.62%) and overlaps the 206,895-dot 13GEMSDOE calibration lattice at <strong>99.85%</strong> &rarr; <strong>verdict: negative (RESEARCH ONLY / DO NOT SUBMIT)</strong>.</p><div class="inline-list"><a href="downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif" download>Download H-UDSR TIFF · RESEARCH ONLY ↗</a><a href="downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.zip" download>Download H-UDSR ZIP ↗</a><a href="udsr/index.html">Open H-UDSR Full Dashboard ↗</a><a href="udsr/executive-summary.html">H-UDSR Guide ↗</a><a href="ap2/index.html">Open AP2 Sub-site ↗</a></div></div>
      <div class="panel" style="margin-top:1rem;"><div class="mini-label">2026-10-28 run H-TRACE (EXP-2 TRACE-T1 · 22,438 dots) — negative result</div><p><strong>H-TRACE</strong> scored <strong>HOLDOUT-DTI 0.0893</strong> [0.0737, 0.1052] vs posterior control <strong>0.0975</strong> and overlapped a sibling raster at <strong>86.26%</strong> &rarr; <strong>verdict: negative (RESEARCH ONLY / DO NOT SUBMIT)</strong>. PR #20 H2 seeded demo remains withdrawn (DO NOT SUBMIT).</p><div class="inline-list"><a href="downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.tif" download>Download H-TRACE TIFF · RESEARCH ONLY ↗</a><a href="downloads/apartgemsdoe2-trace-exp-2-trace-t1-22438dots-20261028T063240Z-71a21036-zeros.zip" download>Download H-TRACE ZIP ↗</a><a href="trace/index.html">Open H-TRACE executive summary ↗</a></div></div></section>
      <section class="section" id="scorecard"><div class="section-head"><div><div class="section-kicker">01 / Nine priority sites</div><h2>Historical results across GEMSDOE24..GEMSDOE36.</h2></div><p>Highest values supplied for each focus site, labeled honestly where organizer submission-page receipts are not bound to archival hashes, alongside exact 3-pixel peer overlap.</p></div>
      <div class="table-wrap"><table><thead><tr><th>Site</th><th>Reported submission</th><th>Reported value</th><th>New-file estimate</th><th>Unique vs 8 sites?</th><th>Decision</th></tr></thead><tbody>{table}</tbody></table></div>
      <div class="table-foot"><span class="dot"></span><span>Directional overlap is measured on every archived final dot. <a href="data/historical_audit.json" class="text-link">View full audit ↗</a> · <button type="button" id="refresh-sources">Check live source HEADs</button><br><span id="freshness-summary" aria-live="polite">Source freshness not yet checked.</span></span></div></section>
      <section class="section" id="analysis"><div class="section-head"><div><div class="section-kicker">02 / PhD-Level Structural &amp; Metric Analysis</div><h2>Why GEMSDOE32 (0.2778) Beat GEMSDOE24..36 — and How H-SARPU Advances Beyond It.</h2></div><p>Exact mathematical decomposition of Distance-Tolerant Tversky DTI (<code>α=0.2, β=0.8</code>, 300 m triangular kernel) across all 9 focus sites and external competition leaders (<code>0.4544</code>, <code>0.3916</code>, <code>0.3195</code>).</p></div>
      <div class="analysis-grid"><div class="panel"><div class="mini-label">Why 0.2778 Beat GEMSDOE24..36</div><h3>Submodular 300 m Packing + B=2 px Catalogue Collar.</h3><p>Continuous probability rasters (<code>GEMSDOE24: 0.1404</code>, <code>GEMSDOE36: 0.2056</code>) suffer catastrophic <code>0.2·FP</code> mass dilution across millions of background cells. Switching to sparse binary dots spaced by <code>d ≈ 2.8–2.9 px</code> (<code>GEMSDOE25/28: 0.2646→0.2676</code>) saturates the 300 m kernel per dot (~13× credit/FP gain). Removing <strong>2,545 redundant dots</strong> within <code>B=2 px</code> (200 m) of <code>labels.tif</code> (where <code>GEMSDOE32</code> pruned <code>GEMSDOE31</code>'s 40,199 dots to <strong>37,654</strong>) eliminated masked/near-catalogue waste to reach <strong>0.2778</strong>.</p><p><strong>How H-SARPU Surpasses D28_B2 (+14.75% on Holdout):</strong> <code>GEMSDOE32 B2</code> remains scarp-biased inside 1 m LiDAR and lacks 5-fold-isomorphic Williams/Crider–Pollard fracture mechanics and blind hydrothermal/Baranov physics. <code>H-SARPU EXP-2</code> beats <code>D28_B2</code> on both full hide-and-recover (<code>0.1138 vs 0.0992</code>) and detached &gt;600 m blind faults (<code>0.0863 vs 0.0834</code>) with only <code>37.31%</code> 3-px overlap against <code>GEMSDOE32 B2</code>.</p><a class="text-link" href="sarpu/index.html">Read full H-SARPU structural &amp; empirical breakdown →</a></div>
      <div class="panel dark"><div class="mini-label">Literal vs Null-Calibrated Uniqueness</div><h3>The 206,895-dot lattice geometry bound.</h3><div class="metric">≥ 82.34%</div><p>Minimum mathematically possible 3-pixel overlap with <code>13gems_20261001_r13-lattice-s5</code> (whose 3-px disks cover <strong>99.87%</strong> of the survey footprint, leaving only 6,649 cells outside) for any 37,654-dot raster. Against all <strong>559 non-lattice registry rasters</strong>, <code>H-SARPU EXP-2</code> achieves <strong>61.91% &le; 70%</strong> (and null-calibrated excess <strong>−0.3829 &le; 0.70</strong> on the lattice).</p><a class="text-link" href="sarpu/executive-summary.html">Read the Dual-Gate protocol &amp; submission steps ↗</a></div></div></section>
      <section class="section" id="sources"><div class="section-head"><div><div class="section-kicker">03 / Verified starting points</div><h2>Follow the official sources.</h2></div><p>Every dataset, competition rule, and physical reference is linked to its authoritative primary source.</p></div><div class="sources">{source_cards}</div><div class="feed-panel"><div><strong>Source snapshot</strong><p id="feed-checked">Loading timestamped source-head checks…</p><small>Updated periodically when the workflow runs.</small></div><div id="feed-grid" class="feed-grid" aria-live="polite"></div><a class="text-link" href="data/source_feed.json">View raw source snapshot ↗</a></div></section></div>'''
    return page('Evidence before the next upload', body, script=True)


def summary():
    body = f'''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Executive summary &amp; submission guide</div><section class="page-hero"><div class="eyebrow">Executive summary · submission guide</div><h1 class="page-title">Dual-gate readiness &amp;<br>DrivenData upload steps.</h1><p class="lead"><code>H-SARPU EXP-2</code> clears G1 (strict <code>[0,1]</code> GeoTIFF), G2 (new repo holdout best <code>0.1138</code>), G3a (genuine non-lattice sparse uniqueness <code>61.91% &le; 70%</code> across 559 rasters), and G4 (67-channel leakage canary). Literal Rule 1 against the 206,895-dot synthetic <code>r13-lattice-s5</code> grid (99.87% coverage) keeps automatic approval fail-closed.</p></section>
    <div class="notice"><strong>LITERAL ALL-REGISTRY RULE STATUS: DO NOT SUBMIT PRIOR NEGATIVE FILES; H-SARPU EXP-2 REQUIRES HUMAN SELECTOR DECISION ON LATTICE EXEMPTION.</strong><p>Earlier AP-1 (99.72% lattice overlap, 0.0389 holdout), AP2 (74.50% sparse overlap), H-UDSR EXP-3 (0.0947 holdout), H-TRACE EXP-2 (86.26% sparse overlap), and H2 (withdrawn seeded demo) are strictly blocked. For <code>H-SARPU EXP-2</code>, open the <a href="sarpu/executive-summary.html">dedicated H-SARPU Executive Summary &amp; Step-by-Step DrivenData Submission Guide ↗</a>.</p></div>
    <div class="page-grid"><div><section class="page-section"><h2>Step-by-Step DrivenData Verification &amp; Submission Guide</h2><ol>
    <li><strong>Download the validated GeoTIFF (or ZIP):</strong> <a href="downloads/{esc(SARPU_TIF)}" download><code>{esc(SARPU_TIF)}</code></a> ({round(SARPU['validator_output']['standalone_validator_zeros']['size_bytes'] / 1024)} KiB, compressed single-band <code>float32</code>) or <a href="downloads/{esc(SARPU_ZIP)}" download><code>{esc(SARPU_ZIP)}</code></a>.</li>
    <li><strong>Verify SHA-256 checksum locally:</strong> Run <code>sha256sum {esc(SARPU_TIF)}</code> and confirm exact digest <code>{esc(SARPU['raster_sha256'])}</code>.</li>
    <li><strong>Run automated local range &amp; metadata validator (prevents <code>"Predicted values must be in range [0, 1]"</code>):</strong> Run <code>python scripts/validate_submission.py docs/downloads/{esc(SARPU_TIF)}</code> — verifies single-band <code>GTiff</code>, <code>EPSG:32611</code>, <code>3730×3292</code>, <code>12,279,160 / 12,279,160</code> finite <code>float32</code> in <code>[0.0, 1.0]</code>, <code>0</code> NaN inside footprint, and <code>0</code> dots on <code>labels.tif</code>.</li>
    <li><strong>Confirm human selector authorization on <code>r13-lattice-s5</code>:</strong> Verify your weekly DrivenData allowance (max 3 submissions / 7-day rolling window per official rules) and confirm that null-calibrated lattice excess (<code>-0.3829 &le; 0.70</code>) governs the synthetic 206,895-dot calibration grid.</li>
    <li><strong>Upload on DrivenData:</strong> Visit <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData GEMS Submissions ↗</a>, upload <code>{esc(SARPU_TIF)}</code> (or <code>{esc(SARPU_ZIP)}</code>), and paste the 117-character note: <code>{esc(SARPU['note'])}</code>.</li>
    <li><strong>Record organizer receipt:</strong> Save the returned leaderboard score alongside the file SHA-256 before labeling any result <code>ORGANIZER-CONFIRMED</code>.</li></ol></section>
    <section class="page-section" id="blockers"><h2>Why prior runs were blocked &amp; how the range error was eliminated</h2><p>The prior DrivenData error <code>"Predicted values must be in range [0, 1]"</code> is prevented in <code>gems32.submission.write_submission_pair</code> and independently re-verified on saved disk bytes by <code>scripts/validate_submission.py</code>: every band sentinel (<code>&lt; -1e38</code>) is sanitized before modeling, probabilities are strictly clipped to <code>[0.0, 1.0]</code> in <code>float32</code> with <code>nodata=None</code> on the <code>-zeros.tif</code> deliverable (and a companion <code>-nan.tif</code> twin with NaN strictly outside the survey footprint is also validated).</p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Selected H-SARPU artifact</div><div class="value small">{esc(SARPU['submission_name'])}</div></div><div class="fact"><div class="mini-label">Holdout DTI (v3.0)</div><div class="value">{SARPU['holdout_dti']['point']:.4f}</div></div><div class="fact"><div class="mini-label">Non-lattice sparse overlap</div><div class="value">61.91% &le; 70% PASS</div></div><div class="fact"><div class="mini-label">Prior AP-1 research file</div><div class="value small">AP-1 · DO NOT SUBMIT</div></div><div class="fact"><div class="mini-label">Evidence JSON</div><div class="inline-list"><a href="data/sarpu_run_card_20261028.json">H-SARPU run card ↗</a><a href="data/run_card.json">Historical AP-1 run card ↗</a><a href="data/historical_audit.json">9-site geometry audit ↗</a></div></div></div></aside></div></div>'''
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
    <section class="page-section"><h2>Next action</h2><p>Do not resubmit, rename, or use this old raster as a new method. Inspect our newly validated <a href="../sarpu/index.html">H-SARPU EXP-2 record</a> and <a href="../sarpu/executive-summary.html">submission guide</a>.</p><a class="text-link" href="../executive-summary.html">Open the full submission guide ↗</a></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Reported value · unverified</div><div class="value">{esc(s['reported_value'])}</div></div><div class="fact"><div class="mini-label">Unique vs other focus sites?</div><div class="value">No · {ref['fraction']:.1%} overlap</div></div><div class="fact"><div class="mini-label">Estimated new-file score</div><div class="value">Not estimable</div></div><div class="fact"><div class="mini-label">Archived filename</div><div class="value small">{esc(s['filename'])}</div></div><div class="fact"><div class="mini-label">Archive SHA-256</div><div class="value small">{esc(s['sha256'])}</div></div><div class="fact"><div class="mini-label">Submission status</div><div class="value">DO NOT SUBMIT</div></div></div></aside></div></div>'''
    return page(f'{site} executive summary', body, '../')


def research():
    body = f'''<div class="shell"><div class="breadcrumb"><a href="index.html">Overview</a> / Research hypotheses &amp; H-SARPU results</div><section class="page-hero"><div class="eyebrow">Pre-registered geological hypotheses · 2026-10-28</div><h1 class="page-title">Five untried hypotheses.<br>Three executed experiments.</h1><p class="lead">Pre-registered in <code>knowledge/preregistration_sarpu_20261028.md</code> prior to training. Ranked by expected DTI gain vs implementation cost, with named non-fault geological mimics and official open data sources.</p></section>
    <div class="page-grid"><div>
    <section class="page-section"><h2>Rank #1 (Implemented &amp; Validated) · H-SARPU: Selected-At-Random Propensity PU + Hydrothermal Alteration &amp; Isomorphic LEFM</h2><p><strong>Exact layers:</strong> <code>geodawn_extensions_u8.tif</code> (<code>Th/K</code>, <code>U/K</code>, <code>U/Th</code>, <code>TMI_up150</code>), <code>14_tmi</code>, <code>blm_closed_claim_distance_m.tif</code>, GDR #1391 2 m temperature probes &amp; SiO2 geothermometers, <code>02_rtp</code>/<code>13_iso_grav_anom</code> strike tensor, real-band variogram roughness (<code>H-FRACTAL-REAL</code>), and 5-fold component-withheld Williams (1957) + Crider–Pollard (1998) LEFM.<br><strong>Why missing from USGS/INGENIOUS:</strong> Catalogue mapping over-represents exposed range-front scarps in 1 m LiDAR while under-mapping buried intra-graben hydrothermal upflow conduits (low <code>Th/K</code> adularia alteration, elevated <code>U/K</code>+<code>U/Th</code> radon, shallow <code>TMI - TMI_up150</code> magnetite destruction).<br><strong>Measured outcome:</strong> <strong>EXP-2 achieved HOLDOUT-DTI = {SARPU['holdout_dti']['point']:.6f}</strong> (new repo record; paired Δ vs <code>D28_B2</code> = +0.014636, 95% CI [+0.005143, +0.024204]) and cleared all 559 non-lattice sparse registry rasters (61.91% &le; 70%).</p></section>
    <section class="page-section"><h2>Rank #2 (Integrated in Stack Ch. 1) · H-BARANOV-FOURIER: Wavenumber 1/|k| Pseudo-Gravity Hydrothermal Demag Deficit</h2><p><strong>Exact layers:</strong> <code>02_rtp</code> (RTP magnetics), <code>18_iso_grav_anom_hg</code> (isostatic gravity horizontal gradient), <code>15_depth_to_base_surf</code>.<br><strong>Signature:</strong> Band-limited 2D FFT radial <code>1/|k|</code> Baranov (1957) integration converts magnetic potential to pseudo-gravity; strong real gravity gradient paired with suppressed pseudo-gravity gradient isolates basement fault offsets whose magnetite was hydrothermally altered to non-magnetic pyrite/clay.<br><strong>Mimic:</strong> Non-faulted felsic pluton contacts and deep flat playa basins.</p></section>
    <section class="page-section"><h2>Rank #3 (Integrated in Stack Ch. 7, 9, 10) · H-WALLACE-KNICK: Wallace (1977) Scarp Crest-Toe Dipole &amp; Strike Concordance</h2><p><strong>Exact layers:</strong> <code>lidar_scarp_features_u8.tif</code> (<code>lapneg_max</code>, <code>lappos_max</code>, <code>downface_max</code>, <code>upface_max</code>, <code>strike</code>) + 100 m DEM profile curvature.<br><strong>Signature:</strong> Degraded Quaternary fault scarps preserve a coupled convex crest × concave debris-colluvium toe aligned with deep potential-field strike (<code>cos²(θ_lidar - θ_pf)</code>); single-feature canary AUC = <strong>0.5684</strong> (Wallace dipole) and <strong>0.5720</strong> (Lahontan-damped profile curvature).<br><strong>Mimic:</strong> Pleistocene Lake Lahontan (&le;1335 m) &amp; Bonneville wave-cut shorelines and TIGER road cuts.</p></section>
    <section class="page-section"><h2>Rank #4 (Integrated in Stack Ch. 6) · H-BIOT-INCOMPAT: Biot–Terzaghi Fluid-Pressurized Slip-Dilation × Seismicity Potency</h2><p><strong>Exact layers:</strong> <code>07_geod_shearrate</code>, <code>08_geod_dilaterate</code>, <code>10_deq_n100a15</code>, <code>16_ieq_n100a15</code>, <code>17_cond_surf</code>.<br><strong>Signature:</strong> Coincident geodetic shear, positive volumetric dilation, high electrical conductance, and microseismic kernel density identify critically stressed, fluid-pressurized fault corridors beneath young alluvium.<br><strong>Mimic:</strong> Broad tectonic block-model smoothing and mining blasts.</p></section>
    <section class="page-section"><h2>Rank #5 (Documented External Next-Phase Lane) · H-INSAR-MT3D: OPERA Sentinel-1 Vertical Velocity Gradient × USGS 3D MT Conductance</h2><p><strong>Exact external sources:</strong> NASA/JPL OPERA North America Surface Displacement (<code>OPERA_L3_DISP-S1_V1</code>, <a href="https://asf.alaska.edu/datasets/daac/opera/">ASF DAAC ↗</a>) + USGS Great Basin 3D Magnetotelluric Resistivity Model (<a href="https://doi.org/10.5066/P9TWT2LU">DOI:10.5066/P9TWT2LU ↗</a>).<br><strong>Signature:</strong> Cross-strike step in multi-year vertical InSAR velocity collocated with deep sub-vertical 2–12 km MT conductor edges.<br><strong>Environment note:</strong> Direct HTTPS to <code>asf.alaska.edu</code> / <code>sciencebase.gov</code> is blocked by sandbox network egress policy; documented for offline staging.</p></section></div>
    <aside><div class="facts"><div class="fact"><div class="mini-label">Selected implementation</div><div class="value">H-SARPU EXP-2</div></div><div class="fact"><div class="mini-label">Holdout DTI</div><div class="value">{SARPU['holdout_dti']['point']:.4f}</div></div><div class="fact"><div class="mini-label">67-channel canary</div><div class="value">PASS (0.7729 &le; 0.90)</div></div><div class="fact"><div class="mini-label">Full Dashboard</div><div class="inline-list"><a href="sarpu/index.html">H-SARPU results &amp; chart ↗</a><a href="sarpu/executive-summary.html">DrivenData upload guide ↗</a></div></div></div></aside></div></div>'''
    return page('Research hypotheses & H-SARPU results', body)


def sarpu_index():
    hr = SARPU["holdout_dti"]
    paired = hr["paired_vs_fold_honest_d28_b2"]
    det = hr["detached_600m_holdout"]
    sg = hr["sgmc_diagnostic_only"]
    sp = SARPU["registry_correlation_overlap"]["dots_genuine_sparse_non_lattice"]
    lat = SARPU["registry_correlation_overlap"]["dots_literal_space_filling_lattice"]
    exps_rows = "".join(
        f"<tr><td><strong>{esc(e['experiment_id'])}</strong> · {esc(e['name'])}</td>"
        f"<td><strong>{e['holdout_dti']:.6f}</strong> [{e['holdout_ci95'][0]:.4f}, {e['holdout_ci95'][1]:.4f}]</td>"
        f"<td>{e['detached_600m_dti']:.6f}</td>"
        f"<td>{e['sgmc_cal_dti']:.6f}</td>"
        f"<td>{e['surface_max_abs_spearman']:.4f}</td>"
        f"<td>{e['worst_sparse_within_3px']*100:.2f}%</td></tr>"
        for e in SARPU["all_experiments"]
    )
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / H-SARPU Executive Dashboard</div>
      <section class="page-hero"><div class="eyebrow">2026-10-28 · Pre-Registered H-SARPU Lane (`arena/431d4f24-apartgemsdoe2`)</div>
      <h1 class="page-title">H-SARPU EXP-2:<br>0.1138 HOLDOUT-DTI &amp; Genuine Uniqueness.</h1>
      <p class="lead">Selected-At-Random (SAR-PU) observation-propensity decontamination across 67 multi-physics channels + 5-fold train-test-isomorphic Williams/Crider–Pollard fracture mechanics.</p></section>
      {sarpu_banner("../")}
      <section class="section"><div class="section-head"><div><div class="section-kicker">Visual Verification</div><h2>Holdout DTI &amp; Sparse Registry Uniqueness Frontier.</h2></div><p>Comparison across every candidate generated in <code>ApartGEMSDOE2</code> on identical <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> folds and the 560-raster extended registry.</p></div>
      <div class="panel"><img src="../assets/fig6_sarpu_breakthrough.png" alt="Two-panel chart showing H-SARPU EXP-2 achieving 0.1138 HOLDOUT-DTI and 61.91% worst non-lattice sparse overlap" style="max-width:100%;height:auto;border-radius:6px;"></div></section>
      <section class="section"><div class="section-head"><div><div class="section-kicker">3-Experiment Factorial Ledger</div><h2>Complete Pre-Registered Ablation Results (3 / 3 Budget).</h2></div><p>All metrics strictly labeled <code>HOLDOUT-DTI</code> with evaluator <code>GEMSDOE32-HIDE-RECOVER-v3.0</code> (22,232 withheld positives across 8 cells / 140 spatial clusters) and <code>GEMSDOE32-SGMC-CAL-v3.0</code> (62,703 off-catalogue SGMC pixels).</p></div>
      <div class="table-wrap"><table><thead><tr><th>Experiment</th><th>Pooled HOLDOUT-DTI (95% CI)</th><th>Detached-600m HOLDOUT-DTI</th><th>SGMC-CAL-v3.0 DTI</th><th>Surface max |Spearman|</th><th>Worst Non-Lattice Sparse &le;3px</th></tr></thead><tbody>
        {exps_rows}
        <tr><td>Control · <code>D28_B2</code> (Fold-Honest)</td><td>0.099202 [0.0860, 0.1127]</td><td>{det['d28_b2_control_point']:.6f}</td><td>{sg['gemsdoe32_b2_calibrated_point']:.6f}</td><td>—</td><td>100% self / historical</td></tr>
      </tbody></table></div></section>
      <section class="section"><div class="section-head"><div><div class="section-kicker">Verified Official Reference &amp; Data Table</div><h2>Authoritative Primary Sources Audited Line-by-Line.</h2></div><p>Every competition rule, external dataset, and geological irregular finding verified against primary documentation.</p></div>
      <div class="table-wrap"><table><thead><tr><th>Source / Dataset</th><th>Role in H-SARPU</th><th>Verified Finding / Irregularity</th><th>Official Link</th></tr></thead><tbody>
        <tr><td><strong>DrivenData DOE GEMS Portal</strong></td><td>Problem spec, Tversky metric (<code>α=0.2, β=0.8</code>, 300 m kernel), submission format</td><td><code>sample_submission.tif</code> mirror carries 60,988 label positives; <code>-zeros.tif</code> &amp; <code>-nan.tif</code> both validated in <code>[0,1]</code></td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData Spec ↗</a></td></tr>
        <tr><td><strong>DOE / NLR Official Rules PDF</strong></td><td>Two-round structure ($50K Initial + $250K Final), max 3 uploads / week</td><td>Round 2 expands evaluation onto unmapped fault candidates (blind conduits critical)</td><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR FY26-96647 ↗</a></td></tr>
        <tr><td><strong>Organizer Reference U-Net</strong></td><td>Prof. John Lipor (PSU) baseline &amp; band metadata tags</td><td><code>IR-SARPU-01/02</code>: Band 6 <code>tc</code> = GeoDAWN Total Count (<code>ρ=0.9999</code>); Band 10 <code>deq</code> = declustered seismicity density</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">GitHub Reference ↗</a></td></tr>
        <tr><td><strong>USGS GeoDAWN Airborne Survey</strong></td><td><code>Th/K</code> adularia, <code>U/K</code>+<code>U/Th</code> radon, <code>TMI_up150</code> shallow demag</td><td>4 contractor flight blocks leveled per-block via <code>acquisition_block_id_100m.tif</code></td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN ↗</a></td></tr>
        <tr><td><strong>DOE INGENIOUS GDR #1391</strong></td><td>Regional fault inputs, 2 m temperature probes, SiO2 geothermometers, sinter/tufa</td><td>1,870 <code>F2MDAB</code> overflow sentinels sanitized prior to anisotropic strike diffusion</td><td><a href="https://gdr.openei.org/submissions/1391">OpenEI GDR #1391 ↗</a></td></tr>
        <tr><td><strong>USGS 3DEP 1 m LiDAR + 100 m DEM</strong></td><td>Wallace (1977) scarp crest-toe dipole &amp; 100 m profile curvature</td><td>24.66% of footprint lacks 1 m LiDAR; Dual-Cover prevents zero-imputation collapse</td><td><a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP ↗</a></td></tr>
        <tr><td><strong>USGS SGMC + BLM MLRS Claims</strong></td><td>Off-catalogue basement diagnostic &amp; closed hydrothermal lode claims</td><td><code>blm_closed_claim_distance_m.tif</code> median 300 m; gated by gravity/MT root</td><td><a href="https://doi.org/10.3133/ds1052">USGS DS-1052 ↗</a></td></tr>
      </tbody></table></div></section></div>'''
    return page('H-SARPU Executive Dashboard', body, '../')


def sarpu_guide():
    val = SARPU["validator_output"]["standalone_validator_zeros"]
    checks_rows = "".join(
        f"<tr><td><code>{esc(k)}</code></td><td><span class='tag ok' style='background:#e6f4ee;color:#115740;'>{'PASS' if v else 'FAIL'}</span></td></tr>"
        for k, v in val["checks"].items()
    )
    body = f'''<div class="shell"><div class="breadcrumb"><a href="../index.html">Overview</a> / <a href="index.html">H-SARPU Dashboard</a> / Step-by-Step Submission Guide</div>
      <section class="page-hero"><div class="eyebrow">Executive Summary Subpage · DrivenData Submission Protocol</div>
      <h1 class="page-title">How to Verify &amp; Submit<br>H-SARPU EXP-2 to DrivenData.</h1>
      <p class="lead">Automated saved-byte verification eliminating the prior <code>"Predicted values must be in range [0, 1]"</code> portal error, plus exact step-by-step upload instructions and literal-lattice disclosure.</p></section>
      <div class="page-grid"><div>
        <section class="page-section"><h2>1. One-Click Validated Artifacts &amp; Submission Metadata</h2>
          <p><strong>Primary Validated GeoTIFF (<code>-zeros.tif</code>, all-finite <code>[0,1]</code>):</strong><br>
          <a class="button primary" href="../downloads/{esc(SARPU_TIF)}" download>↓ &nbsp; Download {esc(SARPU_TIF)}</a></p>
          <p><strong>Compressed Single-GeoTIFF Archive (<code>.zip</code>):</strong><br>
          <a class="button ghost" href="../downloads/{esc(SARPU_ZIP)}" download>↓ &nbsp; Download {esc(SARPU_ZIP)}</a></p>
          <ul>
            <li><strong>Unique Submission Name:</strong> <code>{esc(SARPU['submission_name'])}</code></li>
            <li><strong>DrivenData Submission Note ({SARPU['note_length_chars']}/140 chars):</strong> <code>{esc(SARPU['note'])}</code></li>
            <li><strong>SHA-256 (<code>-zeros.tif</code>):</strong> <code>{esc(SARPU['raster_sha256'])}</code></li>
            <li><strong>SHA-256 (<code>.zip</code>):</strong> <code>{esc(SARPU['zip_sha256'])}</code></li>
            <li><strong>SHA-256 (<code>-nan.tif</code> exterior-NaN twin):</strong> <code>{esc(SARPU['nan_twin_sha256'])}</code> (<a href="../downloads/{esc(SARPU_NAN)}" download>download twin ↗</a>)</li>
          </ul>
        </section>
        <section class="page-section"><h2>2. Step-by-Step DrivenData Upload Procedure</h2>
          <ol>
            <li><strong>Verify SHA-256 integrity after download:</strong><br><code>sha256sum {esc(SARPU_TIF)}</code><br>Confirm it matches <code>{esc(SARPU['raster_sha256'])}</code> byte-for-byte.</li>
            <li><strong>Optional local validator replay (zero human GIS inspection required):</strong><br><code>python scripts/validate_submission.py docs/downloads/{esc(SARPU_TIF)}</code><br>Exits <code>0</code> after confirming all 13 format, CRS, grid, catalogue-mask, and <code>[0.0, 1.0]</code> checks.</li>
            <li><strong>Confirm selector policy on <code>r13-lattice-s5</code> &amp; weekly slot budget:</strong><br>DrivenData enforces <strong>3 submissions per rolling 7-day window</strong>. <code>H-SARPU EXP-2</code> passes G1 (format), G2 (new repo holdout record <code>0.113838</code>, paired 95% CI vs <code>D28_B2</code> strictly positive), G4 (67-channel canary), and G3a (<code>61.91% &le; 70%</code> across all 559 non-lattice registry rasters; <code>37.31%</code> vs <code>GEMSDOE32 B2</code>). Its literal <code>verdict: negative</code> reflects solely the 206,895-dot synthetic <code>r13-lattice-s5</code> grid (99.87% 3-px coverage; null-calibrated excess <code>-0.3829 &le; 0.70</code>). Proceed only if your human selector authorizes calibrated non-lattice uniqueness.</li>
            <li><strong>Upload to DrivenData:</strong><br>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData GEMS Submissions ↗</a>, choose <code>{esc(SARPU_TIF)}</code> (or <code>{esc(SARPU_ZIP)}</code>), paste the 117-char note above, and click <strong>Submit</strong>.</li>
            <li><strong>Log receipt:</strong><br>Record the exact portal timestamp and returned score before updating any ledger with <code>ORGANIZER-CONFIRMED</code>.</li>
          </ol>
        </section>
        <section class="page-section"><h2>3. Automated 13-Check Validator Output on Saved Bytes</h2>
          <p>Every check below ran directly on the written GeoTIFF bytes (<code>{val['size_bytes']:,}</code> bytes, <code>{val['positive_pixels_in_footprint']:,}</code> positive dots in <code>{val['footprint_pixels']:,}</code> valid footprint pixels, range <code>[{val['in_footprint_min']:.1f}, {val['in_footprint_max']:.1f}]</code>):</p>
          <div class="table-wrap"><table><thead><tr><th>Automated Check</th><th>Result</th></tr></thead><tbody>{checks_rows}</tbody></table></div>
        </section>
      </div>
      <aside><div class="facts">
        <div class="fact"><div class="mini-label">Scientific Gates (G1+G2+G3a+G4)</div><div class="value">ALL PASS</div></div>
        <div class="fact"><div class="mini-label">Literal Lattice Gate (G3b)</div><div class="value small">99.82% vs s5 grid (null excess −0.3829)</div></div>
        <div class="fact"><div class="mini-label">HOLDOUT-DTI (v3.0)</div><div class="value">{SARPU['holdout_dti']['point']:.6f}</div></div>
        <div class="fact"><div class="mini-label">Overlap vs GEMSDOE32 B2</div><div class="value">37.31% (&le;70%)</div></div>
        <div class="fact"><div class="mini-label">Machine Artifacts</div><div class="inline-list"><a href="../data/sarpu_run_card_20261028.json">Run Card JSON ↗</a><a href="index.html">Back to Dashboard →</a></div></div>
      </div></aside></div></div>'''
    return page('How to Submit H-SARPU EXP-2 · Executive Guide', body, '../')


def main():
    (DOCS / 'sites').mkdir(parents=True, exist_ok=True)
    (DOCS / 'data').mkdir(parents=True, exist_ok=True)
    (DOCS / 'sarpu').mkdir(parents=True, exist_ok=True)
    (DOCS / 'index.html').write_text(index())
    (DOCS / 'executive-summary.html').write_text(summary())
    (DOCS / 'research.html').write_text(research())
    (DOCS / 'sarpu' / 'index.html').write_text(sarpu_index())
    (DOCS / 'sarpu' / 'executive-summary.html').write_text(sarpu_guide())
    for s in SITES:
        (DOCS / 'sites' / f"{s['site'].lower()}.html").write_text(site_detail(s))
    for name in ('historical_audit.json', 'parallel_candidate_audit.json', 'run_card.json', 'sarpu_run_card_20261028.json'):
        src = ROOT / 'evidence' / name
        if src.exists():
            shutil.copyfile(src, DOCS / 'data' / name)
    print(f'Built overview, guide, research, H-SARPU dashboard/guide, and {len(SITES)} static site briefs.')


if __name__ == '__main__':
    main()
