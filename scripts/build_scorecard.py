#!/usr/bin/env python3
"""Render eight-peer comparison briefs from the independent pinned audit."""
from __future__ import annotations
import html
import json
from pathlib import Path
from fetch_audit_data import sha256_file

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- SCORECARD:START -->', '<!-- SCORECARD:END -->'
SITE_URLS = {
    'GEMSDOE24': 'https://buffedlizard55-lab.github.io/GEMSDOE24/',
    'GEMSDOE25': 'https://buffedlizard55-lab.github.io/GEMSDOE25/',
    'GEMSDOE27': 'https://buffedlizard55-lab.github.io/GEMSDOE27/',
    'GEMSDOE28': 'https://buffedlizard55-lab.github.io/GEMSDOE28/',
    'GEMSDOE30': 'https://buffedlizard55-lab.github.io/GEMSDOE30/',
    'GEMSDOE31': 'https://buffedlizard55-lab.github.io/GEMSDOE31/docs/',
    'GEMSDOE32': 'https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html',
    'GEMSDOE33': 'https://buffedlizard55-lab.github.io/GEMSDOE33/',
    'GEMSDOE36': 'https://buffedlizard55-lab.github.io/GEMSDOE36/docs/',
}


def build_rows(manifest, audit):
    escape = html.escape
    rows = []
    for entry in manifest['inputs']:
        if entry['kind'] != 'historical':
            continue
        site = entry['id']
        comparisons = audit['directional_comparisons'][site]
        peers = [(v['directional_overlap'], name) for name, v in comparisons.items() if name != 'lattice']
        overlap, peer = max(peers)
        if overlap <= .70:
            raise ValueError(f'Expected duplicate witness not found for {site}; review before publishing')
        filename = Path(entry['path']).name
        source = entry['reference_source'] + '?raw=1'
        rows.append(f'''        <tr data-site="{escape(site)}">
          <td><a class="site-link" href="sites/{escape(site.lower())}.html">{escape(site)} brief →</a><small><a href="{escape(SITE_URLS[site], quote=True)}">Original site ↗</a></small><small class="freshness">Source check unavailable</small></td>
          <td><a class="file-link" href="{escape(source, quote=True)}">{escape(filename)} ↗</a><small>Pinned variant · research only</small></td>
          <td><strong>{entry['reported_public_value']:.4f}</strong><small>USER-REPORTED<br>not receipt-confirmed</small></td>
          <td>Not estimable</td>
          <td><strong class="no">No</strong><small>{overlap*100:.2f}% within 3 px of {escape(peer)}</small></td>
          <td><span class="pill">No</span></td>
        </tr>''')
    if len(rows) != 9:
        raise ValueError('expected nine historical files')
    return '\n'.join(rows)


def build_site_pages(manifest, audit):
    """Write a brief per focus site from the same pinned audit, not new results."""
    e = html.escape
    dest = ROOT/'docs/forensics'
    dest.mkdir(exist_ok=True)
    for entry in manifest['inputs']:
        if entry['kind'] != 'historical':
            continue
        site = entry['id']
        raster = audit['rasters'][site]
        comparisons = audit['directional_comparisons'][site]
        peers = [(v['directional_overlap'], k) for k, v in comparisons.items() if k != 'lattice']
        best, peer = max(peers)
        rows = []
        for other in sorted(k for k in comparisons if k != 'lattice'):
            record = comparisons[other]
            rho = record['binary_spearman_within_footprint']
            rho_text = 'undefined' if rho is None else f'{rho:.4f}'
            rows.append(f"<tr><td>{e(other)}</td><td>{record['directional_overlap']*100:.2f}%</td><td>{rho_text}</td><td>{record['exact_dot_intersection']:,}</td></tr>")
        table_rows = '\n'.join(rows)
        filename = Path(entry['path']).name
        source = entry['reference_source'] + '?raw=1'
        page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(site)} brief | GEMS Fieldnotes</title><link rel="stylesheet" href="../style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><div class="wrap nav"><a class="brand" href="../"><span class="brand-mark" aria-hidden="true">⌁</span><span class="brand-name">GEMS Fieldnotes<small>Fault discovery desk</small></span></a><nav class="nav-links" aria-label="Primary navigation"><a href="../">Overview</a><a href="../executive-summary.html">Submission guide</a><a href="../research.html">Research</a><a class="external-nav" href="{e(SITE_URLS[site], quote=True)}">Original site ↗</a></nav></div></header>
<main id="main"><div class="wrap"><div class="page-heading"><div class="eyebrow">Priority site / historical file review</div><h1>{e(site)}: no file is cleared.</h1><p>Independently checked historic TIFF bytes, not a new submission or an organizer-reconciled score.</p></div><div class="prose">
<div class="alert" role="status"><span aria-hidden="true">⚑</span><div><strong>RESEARCH DOWNLOAD ONLY · DO NOT SUBMIT</strong><p>This historical file is not unique under the requested proximity rule. No submission approval or reliable score forecast exists here.</p></div></div>
<section class="panel"><div class="mini-label">Site executive summary</div><h2>Historical reference</h2><p><a href="{e(source, quote=True)}">{e(filename)} ↗</a><br><small>Research only; the filename may identify a format variant rather than the exact uploaded bytes.</small></p><ul><li>Highest supplied result: <strong>{entry['reported_public_value']:.4f} USER-REPORTED / UNVERIFIED</strong>. No file-bound submission-page receipt is available.</li><li>Leaderboard estimate for a new file: <strong>not estimable</strong>. No proxy-to-hidden-score calibration is established.</li><li>Uniqueness against the eight pinned peer files: <strong>NO</strong>. {best*100:.2f}% of this file's positive pixels fall within 3 pixels of {e(peer)}.</li><li>SHA-256: <span class="code">{e(entry['sha256'])}</span>; {raster['dots_inside']:,} positive pixels inside the unauthenticated mirror footprint.</li><li>Format diagnostics: {raster['dtype']}, single band, grid matches the unverified mirror; {raster['nonfinite_inside']:,} nonfinite and {raster['out_of_range_inside']:,} out-of-range cells inside it. {raster['outside_not_null_or_masked']:,} cells outside that mirror footprint are not null or masked. This is not organizer acceptance.</li></ul><p><a href="../executive-summary.html">Why no submission is approved →</a></p></section>
<section class="panel"><div class="mini-label">Literal uniqueness / source to peer</div><h2>All eight comparisons</h2><p>Overlap is directional: the percentage of <strong>this file's</strong> dots within 3 Euclidean pixels of the peer. The correlation is binary Spearman on the mirror footprint; no original pre-placement surface was tested. This is not the complete registry.</p><div class="table-wrap"><table><thead><tr><th scope="col">Peer</th><th scope="col">3-px overlap</th><th scope="col">Binary Spearman</th><th scope="col">Exact shared dots</th></tr></thead><tbody>{table_rows}</tbody></table></div><p><a href="https://github.com/apartanish22-droid/ApartGEMSDOE2/blob/main/evidence/history_audit.json">Open the complete audit ↗</a> · <a href="../#scorecard">Back to nine-site scorecard →</a></p></section>
</div></div></main><footer><div class="wrap footer-inner"><span>GEMS Fieldnotes · evidence before upload</span><span><a href="../">Overview</a> &nbsp;·&nbsp; <a href="{e(SITE_URLS[site], quote=True)}">Original {e(site)} site</a></span></div></footer></body></html>
'''
        (dest/f'{site}.html').write_text(page)


def main():
    manifest = json.loads((ROOT/'evidence/history_manifest.json').read_text())
    audit = json.loads((ROOT/'evidence/history_audit.json').read_text())
    if audit['manifest_sha256'] != sha256_file(ROOT/'evidence/history_manifest.json'):
        raise ValueError('Audit does not match the pinned input manifest; rerun it first')
    build_site_pages(manifest, audit)
    print('Rendered nine independent peer-comparison briefs; no submissions approved.')


if __name__ == '__main__':
    main()
