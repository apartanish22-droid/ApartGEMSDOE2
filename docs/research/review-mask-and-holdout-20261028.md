# Review: mask-aware diagnostic and holdout caveat

**Decision: DO NOT SUBMIT.** This session made no new TIFF, ran no scientific
experiment, and used no competition slot. No assigned single method paragraph
was identified. An existing research TIFF and a valid format alone do not
establish a new candidate, a full-registry pass, or an organizer score.

## Findings

1. **High — false-positive format check.** The pinned
   [`gemsdoe32/submission.py`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/73485f27cf230af770167397c2b72cb9ce3b3f25/src/gemsdoe32/submission.py)
   checks numerical values but not the candidate's mask. On a synthetic single-band
   template containing all zeros, a matching candidate with one `0.5` cell and
   `nodata=0.5` returned `passed=True`, including in strict mode, despite one
   masked in-footprint cell. The exact real file behind the user's portal error
   is unknown; this finding does not explain that error. [Shared issue #66](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/66).
   The shared file was not modified. The documented `scripts/check_submission.py`
   now delegates to the independent `validate_raster.py` read-back diagnostic,
   which checks masks, sidecars, reference/target grids, in-footprint values,
   exterior and whole-array range. The old `--strict-finite` remains accepted;
   this conservative check is now always active. A pass is **not** upload approval.
   It may reject a portal-accepted file, especially an unmasked-zero exterior,
   or a genuine template that does not have zero values in its footprint.
2. **High — holdout contract not established.** In the pinned
   [`holdout.py`](../../src/gems32/holdout.py), the collar is a dilation of
   the quadrant used to pick training IDs, not a buffer excluding visible faults
   near each withheld truth segment. Selected connected components are clipped
   by the scoring domain. [Upstream issue #60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60)
   reports an independent mirror replay; we inspected the pinned source but did
   not reproduce that real-data replay in this session. Prior H-TRACE and UDSR
   holdouts and confidence intervals are exploratory, not evidence that the
   requested segment-buffer gate passed. The shared evaluator requires a central
   fix and a matched replay before comparing candidates for promotion.
3. **High — registry pass may be fail-open.** Upstream
   [issue #63](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/63)
   reports missing-file and literal-lattice pass failures. Local pinned source
   can return missing arrays; complete inventory and hashes are not established
   in this checkout. Do not treat a registry `passed` field as a full gate.
4. **Medium — metric interpretation.** The previous B2 analysis treated the
   isolated-dot break-even rule as universal; one dot can credit multiple truth
   pixels. The [analysis](why-02778-and-how-to-beat-it-20261028.md) now gives
   the general marginal condition and flags causality as unknown. Related shared
   metric documentation is reported in [issue #50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50).
5. **Blocked data and authenticity.** This checkout's current preflight finds
   no core raster inputs, cached features, or pinned template assets. Historical
   restore receipts do not attest present files or organizer authenticity. The
   sandbox cannot directly download from DrivenData or Dropbox; the shared
   repository mirrors do not establish authorization or provenance. The full
   registry and an explicit current lane are also not established. The literal
   covering-lattice rule remains in force until changed by the protocol owner.

## Evidence and next steps

The highest of the nine supplied values is **USER-REPORTED / UNVERIFIED 0.2778**
for GEMSDOE32 B2; no file-bound organizer receipt was checked. The former audit
reports B2 equals its D2.8 comparator after a two-pixel catalogue collar is
removed. Thinning and removing potentially penalized flank dots may explain some
improvement, but without hidden labels and verified receipts this is not causal
proof or a basis for a numerical leaderboard forecast. A higher score is possible,
not guaranteed. The [public organizer leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
was observed at **0.4544** on 2026-10-28; this is a public leaderboard observation,
not a file-bound submission receipt. Official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
explains that the targets are faults and that the final round involves expert
review; algorithmic validation cannot replace the organizers' process.

For the existing ranked geological hypotheses, layers, non-fault mimics, costs,
and data-access caveats, see [research slate](../../research/hypotheses.md). They
are proposals, not proven globally new or verified viable. Establish the lane,
authenticate and restore inputs and complete registry, resolve shared defects,
then preregister and replay a buffered holdout with feature canaries and both
novelty checks. Only after independent saved-byte validation and a separate
selector should any candidate be approved. No weekly cap was checked on an
authenticated page in this session.

## Three passes

1. Reproduced the masked-cell false pass using synthetic TIFFs; routed the
   user-facing checker to the existing conservative independent validator and
   reported the shared defect upstream.
2. Added CLI tests for masked/nodata cells, external masks, out-of-range values,
   mismatched transforms, strict finite behavior, and a valid internal mask;
   inspected the evaluator and registry warnings. Corrected the marginal formula.
3. Rebuilt the generated site and checked the no-submission decision and blocker
   documentation. Ran the full local Python and JavaScript tests; cache-dependent
   tests skip when inputs are absent. None establishes model skill or authenticity.
