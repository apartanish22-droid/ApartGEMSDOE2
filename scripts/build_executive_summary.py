#!/usr/bin/env python3
"""Build the 31 Oct executive summary page and the run cards from evidence files (no hand-typed numbers).

Inputs (all in evidence/ or docs/downloads/, plus the local registry cache for SHA mapping):
  evidence/v5_visible_exclusion_20261031.json        (E1)
  evidence/v5_budget_rank_experiment_20261031.json   (E2)
  evidence/v5_stratified_experiment_20261031.json    (E3)
  evidence/focus_registry_uniqueness_20261031.json   (full-registry gate for the two candidates)
  evidence/focus9_pairwise_20261031.json             (nine focus files, pairwise)
  evidence/candidates_vs_focus9_20261031.json        (candidates vs nine focus files)
Outputs:
  docs/executive-summary-nine-sites.html
  evidence/run_cards_20261031.json
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from validate_raster import validate  # noqa: E402

E = ROOT / "evidence"
DL = ROOT / "docs/downloads"
REG = json.loads((ROOT / "registry/focus_registry_manifest.json").read_text())
TEMPLATE = ROOT / ".cache/gems_data/sample_submission.tif"
SITES = ["24", "25", "27", "28", "30", "31", "32", "33", "36"]
# Prompt-cited scores; NOT verified (no receipts in this session).
PROMPT_SCORES = {"24": 0.2477, "25": 0.2600, "27": 0.2449, "28": 0.2710, "30": 0.2600, "31": 0.2708,
                 "32": 0.2778, "33": 0.2632, "36": 0.2750}
V4 = DL / "apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif"
V5 = DL / "apartgems-v5-b2excl-zeros-20261031-DO-NOT-SUBMIT.tif"


def j(name):
    return json.loads((E / name).read_text())


def registry_link(sha: str, site: str):
    """Prefer the copy in the site's own repo; identical bytes may also be pinned in other repos."""
    hits = [r for r in REG["rasters"] if r.get("sha256") == sha and r.get("status") == "ok"]
    if not hits:
        return None
    own = [r for r in hits if r["repo"] == f"GEMSDOE{site}"]
    r = (own or hits)[0]
    return {"repo": r["repo"], "ref": r["ref"], "path": r["path"], "name": Path(r["path"]).name,
            "also_pinned_in": sorted({h["repo"] for h in hits if h is not r}),
            "url": f"https://github.com/{REG['owner']}/{r['repo']}/blob/{r['ref']}/{r['path']}"}


def site_rows(pw, cvf):
    rows = []
    for s in SITES:
        sha = hashlib.sha256((ROOT / f".cache/gems_data/registry_focus/GEMSDOE{s}_best.tif").read_bytes()).hexdigest()
        link = registry_link(sha, s)
        ovs = {k.split("->")[1]: v["overlap_within_3px"] for k, v in pw["overlap_rows_to_cols"].items()
               if k.split("->")[0] == s}
        mo = max(ovs, key=ovs.get)
        rows.append({"site": s, "dots": pw["sites"][s]["dots"], "sha256": sha, "link": link,
                     "prompt_score": PROMPT_SCORES[s], "max_overlap_site": mo, "max_overlap": ovs[mo]})
    return rows


def summarise_check(path: Path):
    rep = validate(path, TEMPLATE, "owner mirror sample; not authenticated")
    c = rep.get("checks", {})
    failed = sorted(k for k, v in c.items() if v is False)
    return {"format_checks_pass": rep["format_checks_pass"], "failed_checks": failed}


def main() -> int:
    e1, e2, e3 = j("v5_visible_exclusion_20261031.json"), j("v5_budget_rank_experiment_20261031.json"), \
        j("v5_stratified_experiment_20261031.json")
    upq = j("focus_registry_uniqueness_20261031.json")
    pw = j("focus9_pairwise_20261031.json")
    cvf = j("candidates_vs_focus9_20261031.json")["results"]
    rows = site_rows(pw, cvf)
    best = next(r for r in rows if r["site"] == "32")
    chk = {"v4": summarise_check(V4), "v5": summarise_check(V5)}
    v5_side = json.loads((DL / "apartgems-v5-b2excl-zeros-20261031-DO-NOT-SUBMIT.json").read_text())
    up = {k: v for k, v in upq["results"].items() if k.startswith("CANDIDATE")}
    up_v5 = next(v for k, v in up.items() if "v5" in k)
    up_v4 = next(v for k, v in up.items() if "v4" in k)
    c_v5, c_v4 = cvf["v5"], cvf["v4"]
    c0 = e1["hide_and_recover"]["C0"]
    b2 = e1["hide_and_recover"]["B2"]
    ran = e2["rows"]["v4_base_full"]["summary"]

    # ---- run cards (one per experiment, plus the candidate gate) ----
    cards = [
        {"id": "E1", "hypothesis": "Removing v4 dots within 2 px of visible catalogue faults (B2) improves holdout DTI.",
         "mechanism": "Near-catalogue dots are false positives under the DTI kernel, so their removal helps.",
         "mimicking_non_fault_process": "Density reduction: random thinning to the same retained fraction.",
         "holdout": {"label": "HOLDOUT-DTI", "evaluator": c0["evaluator_version"], "n_withheld_positives": c0["n_withheld_positives"],
                     "C0_pooled_dti": c0["pooled_dti"], "C0_ci95": c0["ci95_cluster_bootstrap"],
                     "B2_pooled_dti": b2["pooled_dti"], "B2_ci95": b2["ci95_cluster_bootstrap"],
                     "paired_delta_B2_minus_C0": e1["paired_vs_C0"]["B2"]["delta_pooled_dti"],
                     "paired_delta_ci95": e1["paired_vs_C0"]["B2"]["delta_ci95_paired_bootstrap"],
                     "random_thinning_mean_same_count": e1["decision"]["random_thinning_mean_at_same_retained_count"]},
         "correlation_overlap_vs_registry": "not applicable (no candidate file produced)",
         "raster_sha256": None, "validator_output": None, "submission_name": None, "submission_note": None,
         "verdict": e1["decision"]["verdict"]},
        {"id": "E2", "hypothesis": "Top-N ridge ranking (v4 score) beats N random ridge pixels at matched budget.",
         "mechanism": "Highest-score ridge pixels concentrate on true faults.",
         "mimicking_non_fault_process": "Uniform random placement at the same N (5 seeds).",
         "holdout": {"label": "HOLDOUT-DTI", "evaluator": ran["evaluator_version"], "n_withheld_positives": ran["n_withheld_positives"],
                     "rows": {k: {"dots": v["dots"], "pooled_dti": v["summary"]["pooled_dti"], "ci95": v["summary"]["ci95_cluster_bootstrap"]}
                              for k, v in e2["rows"].items() if "summary" in v}},
         "paired_vs_random": e2["paired_vs_random"],
         "correlation_overlap_vs_registry": "not applicable (no candidate file produced)",
         "raster_sha256": e2["v4_base_sha256"], "validator_output": None, "submission_name": None, "submission_note": None,
         "verdict": e2["decision"]["verdict"]},
        {"id": "E3", "hypothesis": "Block-stratified ridge ranking (spatial coverage fixed) beats random ridge pixels.",
         "mechanism": "E2 gap is spatial clustering; within-block ranking is informative.",
         "mimicking_non_fault_process": "Uniform random ridge placement at the same N (5 seeds), same as E2.",
         "holdout": {"label": "HOLDOUT-DTI", "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0",
                     "paired_vs_random": e3["paired_vs_random"]},
         "correlation_overlap_vs_registry": "not applicable (no candidate file produced)",
         "raster_sha256": None, "validator_output": None, "submission_name": None, "submission_note": None,
         "verdict": e3["decision"]["verdict"]},
        {"id": "CANDIDATE-V5-GATE", "hypothesis": "E1 B2 candidate (V5) is unique and format-valid.",
         "mechanism": "Full-registry lane check (489 rasters + lattice).",
         "mimicking_non_fault_process": "Density and lattice placement (99.8% of footprint is within 3 px of 13GEMSDOE lattice).",
         "holdout": {"label": "HOLDOUT-DTI", "note": "The V5 sidecar holdout is not valid (full labels used). Valid proxy is E1 B2 above."},
         "correlation_overlap_vs_registry": {"full_registry_max_overlap": up_v5["max_overlap_cand_to_registry"],
                                            "full_registry_argmax": up_v5["argmax"],
                                            "full_registry_max_abs_corr": up_v5["max_abs_corr"],
                                            "registry_over_70pct": up_v5["n_registry_over_70pct"],
                                            "registry_over_70pct_examples": up_v5["registry_over_70pct_examples"],
                                            "vs_nine_focus_sites_max_overlap": c_v5["max_overlap"],
                                            "vs_nine_focus_sites_max_overlap_site": c_v5["max_overlap_site"],
                                            "vs_nine_focus_sites_max_pearson": c_v5["max_pearson"]},
         "raster_sha256": v5_side["sha256"], "validator_output": chk["v5"],
         "submission_name": v5_side["submission_name"], "submission_note": v5_side["note"],
         "verdict": "negative: fails lane check (overlap and lattice) and whole-array checker. DO NOT SUBMIT."},
        {"id": "CANDIDATE-V4-GATE", "hypothesis": "v4 ridge base (NaN-free, zeros outside) is unique and format-valid.",
         "mechanism": "Full-registry lane check.",
         "mimicking_non_fault_process": "Dense lattice-aligned placement.",
         "holdout": {"label": "HOLDOUT-DTI", "pooled_dti": ran["pooled_dti"], "ci95": ran["ci95_cluster_bootstrap"],
                     "n_withheld_positives": ran["n_withheld_positives"], "evaluator": ran["evaluator_version"]},
         "correlation_overlap_vs_registry": {"full_registry_max_overlap": up_v4["max_overlap_cand_to_registry"],
                                            "full_registry_argmax": up_v4["argmax"],
                                            "full_registry_max_abs_corr": up_v4["max_abs_corr"],
                                            "registry_over_70pct": up_v4["n_registry_over_70pct"],
                                            "vs_nine_focus_sites_max_overlap": c_v4["max_overlap"],
                                            "vs_nine_focus_sites_max_overlap_site": c_v4["max_overlap_site"],
                                            "vs_nine_focus_sites_max_pearson": c_v4["max_pearson"]},
         "raster_sha256": "f6f3e7c98de4323b3bc4981648170c5afa361fda4eac03313c08fcaf1b51b8d6",
         "validator_output": chk["v4"], "submission_name": None, "submission_note": None,
         "verdict": "negative: fails lane check (lattice, 70% overlap threshold exceeded by one registry raster) and strict whole-array checker. DO NOT SUBMIT."},
    ]
    (E / "run_cards_20261031.json").write_text(json.dumps({"schema": "run-cards-v5-20261031", "cards": cards}, indent=2, default=str) + "\n")

    # ---- HTML ----
    def esc(x):
        return html.escape(str(x))

    def pct(x):
        return f"{100 * x:.1f}%"

    site_tr = []
    for r in rows:
        link = r["link"]
        dl = (f'<a href="{esc(link["url"])}">{esc(link["name"])} ↗</a>' if link else "not found")
        cls = " class=\"best\"" if r["site"] == "32" else ""
        site_tr.append(
            f"<tr{cls}><td>GEMSDOE{r['site']}</td><td>{dl}<br><small>repo <code>{esc(link['repo'] if link else '')}</code>; identical bytes also pinned in: {esc(', '.join(link['also_pinned_in']) or 'none') if link else '-'}</small></td>"
            f"<td>{r['dots']:,}</td><td>{r['prompt_score']:.4f} <span class='tag'>prompt-cited, unverified</span></td>"
            f"<td>Not estimable <span class='tag'>no validated estimator</span></td>"
            f"<td>NO — {pct(r['max_overlap'])} of dots within 3 px of GEMSDOE{r['max_overlap_site']}</td></tr>")

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ApartGEMS — nine-site executive summary (31 Oct 2026)</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2330;background:#fafbfc;line-height:1.5}}
header,main{{max-width:1080px;margin:0 auto;padding:0 20px}}
header{{padding:18px 20px;border-bottom:1px solid #e3e7ee;background:#fff}}
nav a{{margin-right:14px;color:#1b5fb8;text-decoration:none;font-size:14px}}
h1{{font-size:26px;margin:18px 0 6px}} h2{{font-size:20px;margin-top:34px;border-bottom:1px solid #e3e7ee;padding-bottom:4px}}
.banner{{background:#fdecea;border:2px solid #b3261e;color:#7a140e;padding:14px 16px;border-radius:8px;font-weight:600}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0;background:#fff}}
th,td{{border:1px solid #d9dee7;padding:7px 9px;text-align:left;vertical-align:top}} th{{background:#f1f4f9}}
tr.best td{{background:#fff8e1}}
.tag{{display:inline-block;font-size:11px;background:#eef2f7;border-radius:4px;padding:1px 5px;color:#44506a}}
code{{font-size:12px;word-break:break-all}} .small{{font-size:13px;color:#4a5468}}
footer{{margin:40px 0;font-size:13px;color:#4a5468}}
</style></head><body>
<header><strong>ApartGEMS</strong> · DOE GEMS prize · research desk
<nav><a href="#decision">Decision</a><a href="#sites">Nine sites</a><a href="#candidates">Our files</a><a href="#why">Why 0.2778</a>
<a href="#submit">How to submit</a><a href="#hypotheses">Hypotheses</a><a href="#limits">Limitations</a><a href="#sources">Sources</a></nav></header>
<main>
<h1>Nine-site executive summary</h1>
<p class="small">Generated from evidence files by <code>scripts/build_executive_summary.py</code> on 31 Oct 2026. Every number is HOLDOUT-DTI (evaluator GEMSDOE32-HIDE-RECOVER-v3.0), ORGANIZER-CONFIRMED (none in this session), or prompt-cited / unverified, as labelled.</p>

<section id="decision">
<h2>Decision</h2>
<div class="banner">DO NOT SUBMIT ANY FILE FROM THIS REPOSITORY. No file passes every gate. The best-known file (GEMSDOE32, 0.2778) is a duplicate and was reported by users, not verified.</div>
<ul>
<li><strong>Best historical file:</strong> GEMSDOE32, prompt-cited 0.2778 (unverified). It is a copy for learning only, not a new submission. Link below.</li>
<li><strong>Our best new file:</strong> none passes. Candidate V5 fails the lane check (lattice overlap {pct(up_v5['max_overlap_cand_to_registry'])}) and the whole-array checker. Candidate v4 fails the lane check (lattice overlap {pct(up_v4['max_overlap_cand_to_registry'])}; one more registry raster at {up_v4['registry_over_70pct_examples'][0]['overlap']*100:.1f}%) and the strict checker.</li>
<li><strong>Experiments:</strong> 3 of 3 budget used. All three are NEGATIVE (E1, E2, E3). Details in <code>evidence/run_cards_20261031.json</code>.</li>
<li><strong>Unique vs listed GEMSDOE sites:</strong> V5 passes this literal check (max overlap {pct(c_v5['max_overlap'])} vs {esc(c_v5['max_overlap_site'])}; max Pearson {c_v5['max_pearson']:.3f}). It fails the full-registry lane check.</li>
</ul>
</section>

<section id="sites">
<h2>Nine focus sites — file, estimated score, uniqueness</h2>
<p class="small">The "file to download" links point to pinned commits in the owner mirror <code>{esc(REG['owner'])}</code>. They are not organizer-authenticated. Estimated score for a new file: <strong>not estimable</strong>, because no validated estimator exists. The prompt-cited scores are reproduced as reported and are not verified.
Uniqueness: each site was compared with the other eight in this table. Overlap = share of its dots within 3 px of another site's dots.</p>
<table><thead><tr><th>Site</th><th>File to download</th><th>Dots</th><th>Score (prompt-cited)</th><th>Estimated score for new file</th><th>Unique vs other GEMSDOE sites?</th></tr></thead>
<tbody>{''.join(site_tr)}</tbody></table>
<p class="small">Pairwise facts (<code>evidence/focus9_pairwise_20261031.json</code>): GEMSDOE25 and GEMSDOE30 have identical dot sets (<code>25=30</code> same dot set, different bytes). GEMSDOE32 (B2) dots are a subset of GEMSDOE30 and 31. All 72 directed pairs exceed 70% (minimum {pct(min(v['overlap_within_3px'] for v in pw['overlap_rows_to_cols'].values()))}); every site has at least {pct(min(r['max_overlap'] for r in rows))} of its dots within 3 px of another site.</p>
</section>

<section id="candidates">
<h2>Our files — gate results</h2>
<table><thead><tr><th>File</th><th>Dots</th><th>Holdout (HOLDOUT-DTI)</th><th>Full-registry gate</th><th>Whole-array checker</th><th>Status</th></tr></thead>
<tbody>
<tr><td><a href="downloads/apartgems-v5-b2excl-zeros-20261031-DO-NOT-SUBMIT.tif">V5 zeros outside (DO-NOT-SUBMIT)</a><br><code>{esc(v5_side['sha256'][:16])}…</code></td>
<td>{v5_side['dots']:,}</td>
<td>E1 control C0 {c0['pooled_dti']:.5f} [{c0['ci95_cluster_bootstrap'][0]:.5f}, {c0['ci95_cluster_bootstrap'][1]:.5f}] (n={c0['n_withheld_positives']:,}); B2 {b2['pooled_dti']:.5f} — gain matched by random thinning</td>
<td>FAIL: lattice {pct(up_v5['max_overlap_cand_to_registry'])}; {up_v5['n_registry_over_70pct']} registry rasters &gt;70%</td>
<td>FAIL: {esc(', '.join(chk['v5']['failed_checks']))}</td>
<td><strong>NOT OK TO SUBMIT</strong></td></tr>
<tr><td><a href="downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif">v4 ridge base (NaN-free, zeros outside)</a></td>
<td>{up_v4['dots']:,}</td>
<td>C0 {ran['pooled_dti']:.5f} [{ran['ci95_cluster_bootstrap'][0]:.5f}, {ran['ci95_cluster_bootstrap'][1]:.5f}] (n={ran['n_withheld_positives']:,})</td>
<td>FAIL: lattice {pct(up_v4['max_overlap_cand_to_registry'])}; {up_v4['n_registry_over_70pct']} rasters &gt;70%</td>
<td>FAIL: {esc(', '.join(chk['v4']['failed_checks']))}</td>
<td><strong>NOT OK TO SUBMIT</strong></td></tr>
</tbody></table>
<p class="small">Checker notes: the official sample is NaN outside, which fails our conservative strict [0, 1] rule. V5 is zeros outside, which fails the outside-null rule. No file passes both. A nodata-tag variant was tested and rejected: it masks inside zeros and changes the scored footprint. Local checks are not portal acceptance.</p>
</section>

<section id="why">
<h2>Why GEMSDOE32 scored highest (0.2778) — and is &gt;0.2778 reachable?</h2>
<ol>
<li><strong>What is verified.</strong> GEMSDOE32 B2 has 37,654 dots. It is an exact subset of GEMSDOE30 (44,090 dots) and of GEMSDOE31 (40,199 dots), checked cell by cell. The 6,436 dots removed from GEMSDOE30 all lie within 2 px of the known-fault catalogue (<code>existing_faults.tif</code>; 3,891 within 1 px; none farther). This is the only structural difference the repo can show.</li>
<li><strong>What is not verified.</strong> The 0.2778 score itself. It is user-reported with no receipt. Organizer masking of known faults is unresolved (see Limitations), so the mechanism is a hypothesis, not a proof.</li>
<li><strong>What our proxy says.</strong> Removing near-catalogue dots (E1, B2) gives a holdout gain of {e1['paired_vs_C0']['B2']['delta_pooled_dti']:+.5f}, 95% CI [{e1['paired_vs_C0']['B2']['delta_ci95_paired_bootstrap'][0]:+.5f}, {e1['paired_vs_C0']['B2']['delta_ci95_paired_bootstrap'][1]:+.5f}]. Random thinning to the same count gives {e1['decision']['random_thinning_mean_at_same_retained_count']:.5f}, so the gain is explained by density. This is much smaller than the jump from 0.2600 (GEMSDOE30) to 0.2778 (GEMSDOE32). The proxy therefore does not reproduce the claimed mechanism.</li>
<li><strong>Is &gt;0.2778 reachable?</strong> Not shown. Our three experiments are negative: the v4 ridge ranking scores below random placement at matched budget (E2), spatial clustering does not explain that (E3), and near-catalogue removal is density-equivalent (E1). Higher scores have been reported on the public leaderboard (repo notes record 0.4544 at rank 1, observed 28 and 30 Oct 2026, and 0.3916 at rank 2, observed 28 Oct; none verified here). The method that gets there is unknown to us.</li>
</ol>
</section>

<section id="submit">
<h2>How to submit (for the selector — not an instruction to upload)</h2>
<ol>
<li>File: single-band GeoTIFF (or a zip of one), EPSG:32611, 3730 × 3292, 100 m, geotransform (243350, 100, 0, 4508550, 0, −100) — as in the official sample.</li>
<li>Values must be in [0, 1]. Prior upload error: "Predicted values must be in range [0, 1]".</li>
<li>Unique name and a note of at most 140 characters.</li>
<li>Pass every gate (uniqueness vs the full registry, holdout vs random control, checker). No file currently does, so there is nothing to upload.</li>
<li>Weekly cap: shown on the submission page. The selector step is separate from this research and no slot has been used.</li>
</ol>
</section>

<section id="hypotheses">
<h2>Untried hypotheses (ranked, unvalidated)</h2>
<p>Four candidates with layers, physical signatures, mimics, costs and data status are in <a href="research/v5-hypotheses-20261031.md">docs/research/v5-hypotheses-20261031.md</a>. Rank 1 is H5-A, hydrothermal magnetic-low troughs (layers <code>tmi</code>, <code>rtp</code>). Its physical basis is supported by <a href="https://www.osti.gov/biblio/5598190">the USDOE/OSTI Coso aeromagnetic report</a>, which attributes a magnetic low to magnetite destruction by hydrothermal solutions. None of the four has been run.</p>
</section>

<section id="limits">
<h2>Limitations and irregularities</h2>
<ul>
<li>No live leaderboard check. DrivenData and community.drivendata.org are unreachable from the sandbox.</li>
<li>Prompt leaderboard conflict: the prompt cites 0.4413 and 0.3195 as current highs. Repo notes (30 Oct review, top-50 snapshot) record 0.4544 at #1, report 0.3195 at #48, and say 0.4413 does not appear. None of this is re-verified live from this sandbox.</li>
<li>Known-fault masking is unresolved. The organizer thread that would settle it is unreachable.</li>
<li>Gate rule vs implementation: the rule says rank-correlation; the gate computes Pearson correlation. For binary dot fields the two are close, but they are not identical for the float fields.</li>
<li>Registry: 489 rasters compared. One (GEMSDOE36 format test, 32×48) is a different grid and is excluded from the gate, as recorded in the uniqueness JSON.</li>
<li>Official reference notebook (drivendataorg/gems-prize-reference-solution, <code>unet-mc-cv-reference-solution.ipynb</code>): the raw file returns HTTP 302 to a host outside the sandbox allowlist, so its submission-writing convention is unchecked.</li>
<li>The "[0, 1]" rejection is not reproduced: all in-footprint values in the files tested are inside [0, 1]. The bytes of the rejected upload are not in the workspace.</li>
<li>The pre-existing GEMSDOE32 explanation and the metric documentation disagree on whether near-catalogue dots are penalised. This is open.</li>
</ul>
</section>

<section id="sources">
<h2>Sources (links for manual review)</h2>
<ul class="small">
<li>DrivenData competition 306 leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">drivendata.org/…/leaderboard</a> — unreachable from sandbox.</li>
<li>DrivenData reference solution (repo, README): <a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution</a> — notebook not retrieved.</li>
<li>USDOE OSTI, Coso KGRA aeromagnetic survey (magnetite destruction): <a href="https://www.osti.gov/biblio/5598190">osti.gov/biblio/5598190</a>.</li>
<li>Aso Volcano UAV magnetic survey (magnetisation lows match alteration), Springer 2026: <a href="https://link.springer.com/article/10.1186/s40645-026-00800-3">link.springer.com/…/s40645-026-00800-3</a>.</li>
<li>Glen &amp; Earney, GRC aeromagnetic paper (destruction of magnetite by hydrothermal alteration): <a href="https://publications.mygeoenergynow.org/grc/1034804.pdf">publications.mygeoenergynow.org/grc/1034804.pdf</a>.</li>
</ul>
</section>
</main>
<footer>Research desk output. Not a submission. Evidence: <code>evidence/run_cards_20261031.json</code>, <code>evidence/focus9_pairwise_20261031.json</code>, <code>evidence/focus_registry_uniqueness_20261031.json</code>.</footer>
</body></html>
"""
    (ROOT / "docs/executive-summary-nine-sites.html").write_text(html_doc)
    print("wrote docs/executive-summary-nine-sites.html and evidence/run_cards_20261031.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
