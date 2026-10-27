# AP2 Pass-2 amendment — two implementation bugs found and fixed (2026-10-27)

This amendment is written after the first run of EXP1–EXP3 and before the corrected rerun.
The flawed run is retained as `evidence/ap2_experiments_flawed_v1_minsep.json`.
The preregistration itself is **not** edited; this file records the deviations and why.

## Bug 1 — champion control was censorship-biased (invalid comparison)

The first run scored the champion **file** directly under hide-and-recover and got
HOLDOUT-DTI 0.004515. That number is an artefact: the champion file was built with a hard
B=2 exclusion around the *full* catalogue, which includes the very segments the holdout
withholds as truth. Its dots are therefore mechanically prevented from lying within 2 px
of withheld truth, capping their kernel credit near zero (upstream GEMSDOE32 recorded the
same quantity as a "censorship-matched" diagnostic, 0.005176).

Correct control (the upstream convention in `scripts/arena8a_run_experiments.py`:
`d28_mask` + `evaluate_visible_only_holdout(..., b_collar_px=2)`): score the champion's
**parent** raster `dotted-h19-5-d2-8` (44,090 dots, B=0) with the evaluator applying the
B=2 gate using each cell's *visible* faults only. This reconstructs what the champion
recipe would have emitted had it only seen the visible catalogue — the only fair
hide-and-recover counterfactual. The direct-file 0.004515 is kept in the evidence as a
labelled censored diagnostic, never as the control.

## Bug 2 — preregistered emission could not reach its own budget

First run, as literally preregistered (`emitter.emit(..., min_sep_px=2.8)` on the raw
probability field, support caps 140k/40k):

- full-map emission stopped at **20,223 dots** against a 32,000 budget;
- budgets 32,000 / 37,654 / 44,090 produced **identical** holdout DTI (0.090312) —
  the signature of exhaustion, not of a credit bar.

Cause: with `min_sep_px=2.8`, every support pixel within 2.8 px of an accepted dot is
blocked. The top-probability support of an unsharpened HistGB field consists of thick
blobs, so the support is exhausted after ≈20k dots. The template's own runners
(`arena8a_run_experiments.py`, `emit_from_surface`) call `emitter.emit` **without**
`min_sep_px` on a **crest-sharpened** field (`gems32.mdrc.sharpen_ridge_crest`), letting
the exact 300 m marginal-gain rule provide the spacing; upstream measured that
combination at HOLDOUT-DTI 0.1068 vs 0.0989 unsharpened (their EXP2/EXP3 receipts).
Sessions that did use `min_sep_px=2.8` (e.g. GEMSDOE32 H48) applied it to an
NMS-sharpened stationary field, not to a raw probability field.

**Correction (deviation from preregistration §1, disclosed):** the surface, chain gate,
B=2 rule, budgets, evaluator, and gates are unchanged; only the emission stage becomes
the template-standard one — `sharpen_ridge_crest(field)` then
`emitter.emit(..., min_sep_px=0.0)` with upstream support caps (260,000 full / 75,000 per
quadrant). `mdrc.py` is vendored pinned like the other shared modules.

## Experiment counting

EXP1–EXP3 are rerun with the corrected emission and corrected control. They are the same
three preregistered experiments with a tool-usage bug removed — no new geological
hypothesis, surface, or gate is introduced, and the flawed numbers remain in the repo.
First-run results for the record (all HOLDOUT-DTI v3.0, flawed emission):
EXP1 CTRL 0.090312, EXP2 CHAIN 0.088047, EXP3 flat across budgets (saturation artefact);
canary max AUC 0.5840 (unaffected); OOF fold AUCs NW 0.69085, NE 0.74986, SW 0.62004,
SE 0.69153 (unaffected — the OOF surface is reused bit-identically).
