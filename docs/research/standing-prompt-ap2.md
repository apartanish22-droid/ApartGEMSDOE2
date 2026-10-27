# Standing prompt (condensed, read at the start of every session)

> This is a faithful condensation of the owner's long brief, kept because the original
> text is thousands of lines. It is **not** a verbatim copy. Where the original brief and
> measured evidence conflict (e.g. "current leaderboard top"), the measured evidence wins.

## Mission
Produce one unique, competition-ready GeoTIFF for DrivenData Competition 306 (GEMS:
mapping blind/unmapped faults for geothermal exploration) and an executive summary over
the focus sites GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36 that makes it **obvious** which
single file to download, what score it is credibly expected to get, and whether it is
unique versus every earlier GEMSDOE submission. Keep iterating until no further
holdout-supported improvement is available; analyse the owner's best result
(GEMSDOE32 `h33-h33-2-b2-...-zeros`, OWNER-REPORTED 0.2778) at PhD depth and try to beat it.

## Hard requirements
1. **Unique, valid file.** Single-band GeoTIFF matching the sample submission's
   CRS/shape/geotransform; finite values in [0,1] everywhere in the footprint (the portal
   rejects anything else: "Predicted values must be in range [0, 1]"). Not a copy,
   subset, or near-duplicate of any prior submission: surface rank-correlation ≤0.90 and
   ≤70% of dots within 3 px of any registry raster, checked on the surface and final dots.
   One-click download at the top of the site, unique filename, and a ≤140-character note.
2. **Evidence discipline.** Official/verified sources only, links for manual review, no
   hallucinations; flag inconsistencies (e.g. 0.3195 vs 0.4413 leaderboard claims).
   Label every number HOLDOUT-DTI (evaluator version, N withheld, 95% CI) or
   ORGANIZER-CONFIRMED (from a receipt). A projection is never written as a score.
   Negative results are deliverables.
3. **Method.** 3–5 new geological hypotheses with layers, physical signature, why they
   catch catalogue-missing faults, and difference from prior repo work; rank by expected
   DTI gain vs cost. Validate on spatially-blocked/hide-and-recover holdout (whole
   segments + buffer hidden, catalogue features from visible faults only, visible faults
   masked pixel-exactly; DTI α=0.2, β=0.8, 300 m kernel) before spending a weekly slot.
   Leakage canary per feature (AUC >0.90 = leakage until proven otherwise). Budget:
   stop after 3 experiments or 2 hours; this session never picks the real submission
   slot — promotion is a separate selector step.
4. **Reuse, don't rebuild.** Use the shared feature stack, `evaluate_holdout.py`, and
   `submission_writer.py` (here: pinned GEMSDOE32 copies, see `registry/PROVENANCE.md`).
   Fix shared bugs once, transparently; no private forks.
5. **Deliverables.** Run card JSON (hypothesis, mechanism, named mimic, holdout DTI+CI,
   registry correlation/overlap, sha256, validator output, name, note, verdict);
   user-friendly GitHub Pages site + executive-summary subpage + exact submit steps;
   this prompt stored in the repo; three passes (implement+verify, bug/edge review,
   re-check vs brief); PR to `main`.

## Values
"Maximize P(Win)" — do the work most likely to produce a lasting result, especially when
it is not the comfortable local fix. "Own the Outcome" — if it's broken, fix it; raise the
bar, don't deflect. Publish negatives; never dress an estimate as a score.

## Current status pointer (2026-10-27)
AP2 session complete: see `evidence/ap2_run_card.json` (verdict `negative` on 2 of 7
preregistered gates), `docs/index.html`, and the README decision banner. The emitted
file is unique vs every scored submission and format-valid; it is **not** auto-promoted.
