# ApartGEMS — evidence-led GEMS research

> **Current verdict: negative. No file is approved to upload.** This review
> produced no new geological experiment, submission TIFF, holdout score or
> competition submission. The requested unique, higher-scoring file remains
> unfulfilled. See the [executive summary](docs/EXECUTIVE_SUMMARY.md), the
> [nine-site scorecard](docs/index.html#scorecard), and the
> [current JSON card](evidence/current_run_card.json) and
> [three-pass review](docs/research/three-pass-reconciliation-20261028.md).

The goal is to **Maximize P(Win)** and **Own the Outcome**: use evidence to
protect limited submission slots, report negative results, and never rename an
old raster or a synthetic demo as a new geological model.

## What we know

- The nine best historical values supplied for GEMSDOE24/25/27/28/30/31/32/33/36
  are **user-reported, not verified organizer receipts**. The scorecard gives
  each claimed filename, value, archival comparison, uniqueness and decision.
  No calibrated hidden-leaderboard estimate is available for a new file.
- GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` reportedly scored
  0.2778. Its audited dot set is a subset of GEMSDOE31: 2,545 removed dots lie
  within two pixels of the mirrored catalogue. Pruning could reduce redundant
  prediction mass, but hidden truth and a matching receipt are unavailable, so
  the actual cause of the reported score is unknown. See the
  [forensic note](docs/research/why-02778-and-how-to-beat-it-20261028.md).
- AP-1, H-UDSR and H-TRACE are prior research artifacts, **not approved**.
  H-UDSR's archived SHA-256 is
  `1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9`.
  Its previously reported HOLDOUT-DTI was 0.0947 [0.0822, 0.1073]
  (`GEMSDOE32-HIDE-RECOVER-v3.0`, 22,232 withheld positive instances); its
  saved dots independently overlap the pinned lattice by 99.85%. The holdout
  was **not** independently rerun here.
- A concurrent branch produced [RAD-SCARP](docs/downloads/apartgemsdoe2-rad-scarp-offcatalogue-geothermal-20261028T224529Z-04053573-zeros.tif) for research. Its earlier uniqueness-pass and portal-safe claims are withdrawn: **10,421 of 10,457 dots (99.66%)** overlap the pinned lattice, and no comparable visible-only holdout with CI is established. **DO NOT SUBMIT.** [Independent saved-byte recheck](evidence/rad_scarp_saved_byte_recheck_20261028.json).
- H2 is a seeded pseudo-feature demo, not a real fault detector. Saved-byte
  checks found `nodata=0` masks 5,140,874 cells inside the owner-mirrored
  footprint; 26,478 of its 26,499 inside dots overlap the lattice within 3 px.
  Earlier conditional-upload guidance and score projections are withdrawn.
  [H2 correction](docs/EXECUTIVE_SUMMARY_H2.md) ·
  [reproducible read-back](evidence/h2_saved_byte_recheck_20261028.json).
- At a 37,654-dot budget, only 6,649 mirrored-footprint cells are beyond the
  lattice's 3-pixel neighborhood, so at least 82.34% must overlap it; the
  requested literal maximum is 70%. This bound is conditional on that witness
  and does not rule out every smaller candidate. Do not game the rule by moving
  predictions into lattice holes.

## Next research, not an assigned lane

The [ranked research slate](research/hypotheses.md) proposes paired drainage
profiles, magnetic flight-line stability, cross-depth conductance contrasts and
fluid-chemistry contrasts. It states the layers, physical mechanisms, non-fault
mimics, differences, costs and public-source limitations. These ideas have not
been run here and are not established globally novel.

The prompt refers to a single assigned method paragraph, but none is visible in
the available charter. A complete parallel registry, authenticated organizer
sample, validated prepared shared feature stack, `existing_faults.tif`, and an
independently comparable holdout best are not established. Owner-mirrored inputs
can be hash-consistent without being organizer-authenticated. The mirror sample
contains 60,988 positive pixels matching the labels, unlike the described
all-absence example.

Before a new experiment: establish the lane and immutable complete registry;
reuse the shared cache/evaluator/writer; withhold whole segments with a spatial
buffer; derive all catalogue-dependent features from visible faults only; mask
visible faults pixel-exactly; test each feature for leakage; and compare pooled
HOLDOUT-DTI and a 95% CI against the same evaluator and fold assignment. Apply
literal surface and final-dot uniqueness thresholds. Verify saved GeoTIFF bytes
against an authenticated sample and require a separate automated weekly-slot
selector. A format-only pass is not an upload approval. Stop at three
experiments or two hours.

The known upstream shared-tool issues remain open: probability binarization
[GEMSDOE32 #37](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/37),
zero-truth FP accounting [#41](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41),
whole-segment truth-to-visible buffering [#60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60),
static holdout evidence labeling [#61](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/61),
masked in-footprint validation [#66](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/66),
incomplete and non-literal registry results [#63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63),
release-selector evidence gaps [#67](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/67),
template-origin terminology [GEMSDOE24 #74](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74),
and registry grid checks [#77](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/77).
This account cannot push to the canonical template; no private shared-tool fix
was substituted.

## Reproduce the read-only review

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_audit_data.py       # pinned public research comparators
.venv/bin/python scripts/restore_shared_tools.py  # pinned read-only subset
.venv/bin/python scripts/verify_independent_replays.py
.venv/bin/python scripts/preflight.py              # currently BLOCKED
.venv/bin/pytest -q
node --test tests/js/*.test.cjs
node tests/feed_ui.cjs
```

The data and virtual environment are ignored, not committed. The optional
`restore_data.py` retrieves approximately 400 MB of hash-pinned public mirrors,
not authenticated organizer files. The preflight is deliberately fail-closed.
The public-format diagnostic `scripts/check_submission.py` reads the saved
bytes, footprint masks and reference grid; even a pass cannot authorize a slot
or establish portal acceptance. The rejected file itself was not available, so
the cause of the reported `[0,1]` error is unknown.

## Official sources and freshness

[Competition task, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[Pixel-exact mask clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) ·
[Prize rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) ·
[Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) ·
[USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) ·
[USGS 3DEP](https://www.usgs.gov/3d-elevation-program) ·
[USGS conductance maps](https://doi.org/10.5066/P9TWT2LU) ·
[INGENIOUS](https://gdr.openei.org/submissions/1391).

DrivenData's [Terms of Use](https://www.drivendata.org/termsofuse/) prohibit
automatic website monitoring. The scheduled Pages workflow now checks **GitHub
source heads only** and links to the leaderboard; it does not scrape or refresh
leaderboard values. A dated historical observation is not a live score or a
file-bound receipt. GitHub HEAD movement is not a new scientific audit.
