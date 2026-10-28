# Why GEMSDOE32's `h33-h33-2-b2` (user-reported 0.2778) leads the nine focus sites — and what beating it requires

> **Correction, 2026-10-28:** The scalar marginal rule below applies only in a special isolated case; it is not generally valid for a dot covering multiple or previously covered truth pixels. Archived holdouts also do not establish the requested whole-segment truth-to-visible buffer; see [upstream issue #60](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/60). Treat their CIs as exploratory, not promotion evidence.

*2026-10-28 · session `arena/7ec4400f-apartgemsdoe2`. Every number below is either
recomputed this session from SHA-256-pinned bytes, quoted from an official page fetched
2026-10-28, or clearly marked as user-reported / inference.*

## 1. What "0.2778" is — and is not

- **Evidence class: USER-REPORTED / UNVERIFIED.** No organizer submission-page receipt binds
  the value 0.2778 to a file hash. The same applies to all nine focus-site values.
- The organizer's public leaderboard fetched 2026-10-28 shows rank 1 = **0.4544**
  (33 submissions), rank 2 = 0.3916, and a dense 0.326–0.391 band through rank 23
  ([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)).
  The prompt's 0.4413 and 0.3195 "current high scores" are superseded historical claims.
- The file itself is byte-verified: `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`,
  SHA-256 `c55bafc4…`, 37,654 positive pixels on the 3730×3292 EPSG:32611 grid.

## 2. The lineage is one support, three metric-driven compressions (byte-verified 2026-10-28)

| Step | File (site) | Dots | Operation | User-reported value |
|---|---|---:|---|---:|
| H19-5 | `gems19-h19-5-…-e27054cf-nan` (19GEMSDOE) | 121,131 | continuous multiline-corroborated support | 0.1922 |
| D1.5 | GEMSDOE24 `h25-1-dotted-h19-5-d1-5` | 60,069 | exact subset of H19-5 (verified: `D1.5 & ~H19-5 = ∅`) | 0.2477 |
| D2.8 | GEMSDOE25 = GEMSDOE30 (identical SHA-256 `91eae1ca…`) | 44,090 | exact subset of H19-5 (verified) | 0.2600 |
| B2 | GEMSDOE32 `h33-h33-2-b2` | 37,654 | `(D2.8 & d_catalogue>2px) XOR B2 = 0` (verified); removes 6,436 dots within 200 m of catalogue faults | 0.2778 |

The archived focus-site files are spatially similar (pairwise 3-px overlaps 86.7–100%, `evidence/history_audit.json`), but proximity alone does not prove common pixel lineage for all nine. "Why did B2 win?" is not established by this evidence; thinning and collar pruning are plausible contributors.

## 3. Metric algebra and hypotheses about thinning and collar-pruning

Official metric ([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
fetched 2026-10-28): triangular kernel `k(d)=max(1−d/3px,0)`,
`DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`. With `K` hidden-truth pixels,
`FN_w = K − TP_w`, and for binary dots `FP_w = S − M` (`S` dots, `M` = Σ kernel
proximity of dots to truth), this is exactly (`src/gems32/metric.py`, brute-force-tested):

```
DTI = TP_w / ( 0.2·(TP_w + S − M) + 0.8·K )
```

**Marginal rule (corrected).** For the recorded metric with alpha + beta = 1,
let `T` be weighted true-positive mass, `D` the DTI denominator, `deltaT`
the *total* incremental truth credit, and `k_near` the new dot's proximity to
its nearest truth. Adding one active unit dot gives
`deltaD = 0.2 * (deltaT + 1 - k_near)`, so the dot improves DTI exactly when
`deltaT > DTI * 0.2 * (deltaT + 1 - k_near)` (up to the metric's epsilon).
A dot can improve credit for multiple truth pixels; `deltaT` need not equal
`k_near`. The simpler threshold `k > 0.2 * DTI` applies only when `deltaT =
k_near = k`. The hidden truth is unavailable, so neither criterion is a score
forecast. See [upstream metric issue #50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50).

Two hypotheses about the historical pattern, not established causes:

1. **Dotted thinning (121,131 → 44,090).** On an ideal straight trace with truth exactly on the line and evenly spaced dots, spacing `s`
   leaves each truth pixel within `s/2` of a dot: worst-case credit `1 − s/6`
   (0.53 at s = 2.8 px), mean ≈ 0.77 — while the dot count `S`, hence the FP mass paid on
   the *uncovered* parts of the support, falls ~2.8× versus the continuous line.
   Whether TP falls modestly depends on the unknown truth; thinning reduces the `0.2·S` term but other denominator terms also change. The user-reported values rise from 0.1922 to 0.2600; a causal attribution is not established.
2. **Collar pruning (44,090 → 37,654).** DrivenData staff confirm
   ([forum 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516),
   chrisk-dd, 2026-09-16): *"Pixels corresponding to known USGS/INGENIOUS faults are
   masked / excluded from evaluation."* Dots exactly on catalogue faults are therefore
   free of penalty but also earn nothing; dots 1–2 px *beside* catalogue faults are not
   on masked pixels and incur FP weight depending on their proximity to hidden truth. H19-5-family detectors concentrate near mapped range fronts, and 14.6 % of D2.8
   dots sat in the near-catalogue collar (verified: 6,436 dots at `d_catalogue ≤ 2 px`). Removing
   them cut the denominator by ≈ 0.2 × 6,436 ≈ 1,287 at near-zero TP cost — provided few
   expert-hidden traces run within 200 m of a catalogue trace (inference from the score
   movement, not independently observable). The user-reported values rise from 0.2600 to 0.2778; a causal attribution is not established.

**Why the support may be limiting.** The user-reported value does not establish an optimal dotting or a ceiling. B2 is restricted to the H19-5 support, so its recall and false-positive mass against hidden faults depend on that support. Hidden traces distant from the support receive no kernel credit; traces near it may receive partial credit even without exact pixel overlap. Changing emission can change coverage and FP mass, but thinning cannot add new support outside the existing pixels. (What fraction is missing cannot be measured without the
private labels; organizers explicitly decline to describe the test faults' data
sources or fault types — [forum 11527](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527),
chrisk-dd, 2026-09-23.)

## 4. What beating 0.2778 (and approaching 0.4544) actually requires

1. **A better support, not a better dotting of the same support.** Dotting/B2 are now
   metric-standard (and in the shared emitter). The remaining variance across the
   prompt's ~200 user-reported results supports this: the user-provided results vary widely, but their lineage and file-to-score associations have not all been independently established.
2. **Recall on the *hidden* fault population, which is not the catalogue population.**
   Hide-and-recover on catalogue faults measures recovery of mapped-style faults;
   the test set is defined by *disagreement* with the catalogue. Hence this repo's
   repeated pattern: models can beat fold-honest D28_B2 on hide-recover
   (H-UDSR EXP-2 HOLDOUT-DTI 0.1137 vs 0.0992) while no calibrated statement about the
   leaderboard follows. A holdout win is a **necessary gate, not a score estimate**.
3. **Precision per dot (credit/dot), because α = 0.2 taxes every dot.** At 37,654 dots
   the FP tax term `0.2·S` ≈ 7,531 dwarfs plausible TP (shared-code estimate
   `K ≈ 12,691` hidden pixels, `holdout.ESTIMATED_LB_HIDDEN_TRUTH_PX`, itself calibrated
   from the lattice score — treat as scaffolding, not fact). Raising mean kernel credit
   per dot — dots exactly on coherent traces rather than in speckled posterior blobs —
   is the cheapest remaining lever once support recall is fixed. This is the mechanism
   H-TRACE tests this session.
4. **Far-field mass.** 58.4 % of B2 dots sit > 15 px (1.5 km) from any catalogue fault
   (verified this session). Hidden traces are by construction off-catalogue; lanes that
   crowd the 2–15 px collar (H-UDSR EXP-2: 96.25 %) may win hide-recover while starving
   the far field the experts actually mapped.

**Can a unique new submission score higher than 0.2778?** Possibly — the observed 0.4544 public leader
indicates a higher public leaderboard value exists — but it cannot be *certified* from any local proxy.
The honest deliverable is a candidate that (i) is generated from features, not copied
support, (ii) beats the fold-honest control and the repo's holdout best with paired CIs,
(iii) passes leakage, uniqueness and saved-byte format gates, and (iv) is submitted only
through a separate selector decision, with the organizer receipt archived. Anything
stronger claimed in advance would be a projection written as a score.
