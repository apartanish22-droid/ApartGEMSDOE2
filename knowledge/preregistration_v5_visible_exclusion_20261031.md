# Pre-registration — V5 visible-catalogue exclusion (experiment 1 of 3)

Registered 2026-10-31, **before** the run. Script: `scripts/run_v5_visible_exclusion.py`.
Output: `evidence/v5_visible_exclusion_20261031.json`.

## Hypothesis

Dots from the label-free v4 ridge base (`docs/downloads/apartgems-v4-ridge-tmi-isohg-nms-q5pct-20261030.tif`,
203,418 dots) that lie within B pixels (B = 1, 2, 3) of a **visible** catalogue fault contribute
false-positive mass under the hide-and-recover holdout. Excluding them should raise pooled HOLDOUT-DTI.

This is the mechanism the repository attributes to GEMSDOE32's 0.2778 file (a 6,436-dot removal from
GEMSDOE30), tested here in a leakage-safe form.

## Why this is leakage-safe

`gems32.holdout.evaluate_hide_and_recover(..., b_visible_px=B)` excludes only pixels within B px of the
**visible** faults of each withheld cell (`cell.d_vis_sub`). Withheld-segment labels are never used.
The base dots are label-free. Nothing in the base or the exclusion sees the withheld truth.

## Named non-fault mimic

Lithologic contacts and magnetic/density edges that run parallel to a mapped fault. Excluding dots
near visible faults removes true fault-parallel signal as well as false positives, so a gain would be
partly a density artefact.

## Controls

- **C0** v4 base, B = 0 (the reference).
- **C-rand** random thinning of the v4 base to the same retained count as B = 2, with 5 seeds. If the
  B = 2 gain is matched by random thinning, the gain is a density effect, not a catalogue-proximity effect.

## Decision rule (fixed now)

- **Promote to a candidate** only if, for some B in {1, 2, 3}, the **paired** HOLDOUT-DTI difference
  from C0 has a 95% cluster-bootstrap CI whose lower bound is > 0, AND the B-variant exceeds the
  random-thinning control mean at the same retained count.
- Otherwise: **negative**. Report it. Do not re-tune B after seeing results.

## Labels

- Every number is **HOLDOUT-DTI** (evaluator `GEMSDOE32-HIDE-RECOVER-v3.0`), with withheld-positive
  count and cluster-bootstrap 95% CI. Paired differences use identical resampling indices (same seed).
- Also reported: the **SGMC off-catalogue** proxy (`GEMSDOE32-SGMC-CAL-v3.0`) as a second, independent check.
- Nothing here is an organizer score. Nothing here authorises a submission.

## Budget

Experiment 1 of at most 3 (protocol item 6). No selector run. No weekly slot used.

---

# Pre-registration addendum — V5 experiment 2 of 3 (budget-matched ridge ranking vs random)

Registered 2026-10-31, **before** the run. Script: `scripts/run_v5_budget_rank_experiment.py`.
Output: `evidence/v5_budget_rank_experiment_20261031.json`.

## Why this experiment

Experiment 1 showed that thinning the v4 base barely moves holdout DTI (random thinning at 95.6%
retention gives the same value as the catalogue-proximity rule). The unanswered question is whether
the **ranking** carries any fault information at all. Test it directly: at the same dot budget, does
the top-N ridge score beat N random ridge pixels?

## Design

- Score = `hg + iso` (z-scored tmi_hg band 3 + z-scored iso_grav_anom_hg band 18), NMS across the TMI
  normal, all label-free. Reproduce the v4 base first; the saved file must match byte-for-byte or the
  experiment is void.
- Budgets N in {37,654 (GEMSDOE32 count), 44,090 (GEMSDOE30 count)}, chosen before the run.
- **A_N**: top-N ridge pixels by score over the whole footprint (ranking is label-free).
- **R_N**: N ridge pixels drawn uniformly at random, 5 seeds (11, 22, 33, 44, 55).
- Scoring: `holdout.evaluate_hide_and_recover`, `b_visible_px = 0`, 2,000 cluster-bootstrap reps,
  identical resampling indices for A and R (paired).

## Decision rule (fixed now)

- **Promote** only if, for some N, A_N's pooled HOLDOUT-DTI exceeds the random-control mean AND the
  paired 95% CI of (A_N − mean R_N) has a lower bound > 0.
- Otherwise **negative**: the ridge score does not beat chance at that budget on this holdout.

## Labels

HOLDOUT-DTI (evaluator GEMSDOE32-HIDE-RECOVER-v3.0), with withheld-positive count and CI. Not an organizer
score. No submission is authorised by this experiment. Experiment 2 of at most 3.

---

# Pre-registration addendum — V5 experiment 3 of 3 (block-stratified ridge ranking)

Registered 2026-10-31, **before** the run. Script: `scripts/run_v5_stratified_experiment.py`.
Output: `evidence/v5_stratified_experiment_20261031.json`. This is the last experiment in the budget.

## Why this experiment

Experiment 2 found that the top-N ridge ranking scores far below random placement at the same budget.
Two explanations are possible: (a) the ranking carries no fault information, or (b) the top-N pixels
cluster spatially, so they cover few withheld segments. Experiment 3 separates these. It keeps the
spatial allocation of ridge pixels proportional (as random placement does in expectation) and changes
only the ranking within each block.

## Design

- Spatial blocks: the evaluator's 16 x 16 grid (`holdout._spatial_block_index`, grid_n = 16).
- For each block b: c_b = ridge pixels in b; k_b = round(N x c_b / total ridge pixels).
- **S_N** = within each block, the top-k_b ridge pixels by score (score = hg + iso, label-free).
- Controls: uniform random ridge pixels at the same N, 5 seeds (identical to experiment 2's design).
- Budgets N in {37,654, 44,090} (same as experiment 2). Scoring and paired CI as in experiment 2.

## Decision rule (fixed now)

- **Promote** only if S_N's pooled HOLDOUT-DTI exceeds the random-control mean AND the paired 95% CI of
  (S_N − mean random) has a lower bound > 0 for some N.
- Interpretation if negative: the ranking does not carry usable fault information on this holdout, even
  after the spatial confound is removed. If positive: the experiment-2 gap was largely a spatial-coverage
  effect, and a stratified allocation is the next candidate to pre-register.

## Labels

HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0) with withheld-positive count and CI. Not an organizer score.
This is experiment 3 of 3. The budget is then spent. No submission is authorised by it.
