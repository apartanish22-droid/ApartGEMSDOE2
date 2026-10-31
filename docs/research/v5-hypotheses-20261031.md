# V5 candidate hypotheses (31 Oct 2026)

**Status: proposals only. None of H5-A to H5-D is validated, and none is a submission.**
Every holdout number below is HOLDOUT-DTI (catalogue proxy, GEMSDOE32-HIDE-RECOVER-v3.0) and is not an organizer score.

## What the 31 Oct experiments changed

Three pre-registered experiments on the label-free v4 ridge base are negative. Pre-registration:
[knowledge/preregistration_v5_visible_exclusion_20261031.md](../../knowledge/preregistration_v5_visible_exclusion_20261031.md).

| Experiment | Question | Result (HOLDOUT-DTI) | Verdict |
|---|---|---|---|
| E1 visible-catalogue exclusion (B = 2 px) | Does removing dots within 2 px of visible faults help? | C0 0.03313 → B2 0.03385; paired Δ +0.00072, 95% CI [+0.00034, +0.00117]. Random thinning at the same retained fraction: 0.03387 (5 seeds). | **Negative.** The gain is a density effect, not a catalogue-proximity effect. |
| E2 budget-matched ridge ranking | Does the top-N ridge score beat N random ridge pixels? | Top-37,654 0.02064 vs random 0.04337 (Δ −0.02273, CI [−0.02904, −0.01618]). Top-44,090 0.02269 vs random 0.04671. | **Negative.** Top-ranked ridge pixels score below random. |
| E3 block-stratified ranking | Is E2 just spatial clustering? | Stratified top-37,654 0.01852 vs random 0.04337. | **Negative.** Clustering does not explain the gap. The within-block ranking is also below random. |

Two consequences shape the hypotheses below:

1. The **gradient-ridge score carries no usable fault information on this holdout.** Its top-ranked pixels are below chance even after the spatial confound is removed.
2. **Budget dominates on this proxy.** Random placement at 37,654 dots (0.0434) beats the full 203,418-dot base (0.0331). A holdout that rewards fewer false-positive dots can reward budget reduction without any geology, so budget gains must be checked against a random control before they count.

## Ranked hypotheses

Ranking is by expected improvement per unit of implementation cost. The improvement values are **not measured**. They are qualitative judgements from the experiments above.

| Rank | Hypothesis | Layers (band index, name from `data/prepared_manifest.json`) | Physical signature targeted | Why it could find a fault absent from the USGS/INGENIOUS catalogue | Named non-fault mimic | How it differs from what is in this repo | Data (status) | Cost |
|---|---|---|---|---|---|---|---|---|
| **1** | **H5-A: hydrothermal magnetic-low troughs.** Keep linear valleys of low total-field magnetisation, not horizontal-gradient maxima. | 14 `tmi` (primary); 2 `rtp` (check); 15 `depth_to_base_surf` (conditioning) | Hydrothermal alteration destroys magnetite and lowers magnetisation. Altered fault corridors can therefore appear as elongated lows. Sources: [OSTI, Coso KGRA low-altitude aeromagnetic survey (USDOE)](https://www.osti.gov/biblio/5598190) reports a magnetic low attributed to magnetite destruction by hydrothermal solutions. [Springer, Aso Volcano UAV magnetic study (2026)](https://link.springer.com/article/10.1186/s40645-026-00800-3) reports magnetisation lows matching altered zones. | Alteration corridors are a fluid-pathway signature that does not need a surface scarp or a catalogued trace. | Broad magnetic lows from sediment-filled basins, non-magnetic intrusions, or low-latitude or topographic effects. | Negative-valued valleys rather than gradient maxima. E1–E3 show gradient maxima are anti-informative here, so this is the direct physical alternative. | Data in the sandbox (training stack, restored and SHA-verified). Uses no catalogue labels. | Low–medium |
| 2 | **H5-B: budget calibration under random placement.** Find the dot budget that maximises holdout DTI for random placement, then test any structured signal only at that budget. | 14 `tmi` only for the mask footprint; no structured feature | Not a geological signature. It calibrates the metric's false-positive term against the holdout. | Not applicable. This is a calibration hypothesis, not a fault detector. | Any holdout reward for simply emitting fewer dots. | Repository tools so far used fixed budgets (37,654; 44,090; 203,418). This scans the budget. | Data in the sandbox. | Very low |
| 3 | **H5-C: strain-axis-coherent ridge filter.** Keep ridge pixels whose orientation agrees with the principal shear-strain axis. | 7 `geod_shearrate`; 8 `geod_dilaterate`; 4 `geod_2ndinv`; 3 `tmi_hg` | Faults localise shear. The ridge normal should align with the principal strain direction. | Strain is measured independently of magnetics, so coherence can flag faults with no magnetic expression. | Topographic or creep strain, and lithologic contacts aligned with regional strain. | A variant of slate H3 and H-SHEAR in [v4-hypotheses.md](v4-hypotheses.md) and [hypotheses.md](../../research/hypotheses.md). It adds an orientation-coherence constraint that the repo does not yet test. | Data in the sandbox. | Medium |
| 4 | **H5-D: BLM closed claim proximity × radiometric anomaly.** This is slate item H-C1 in [hypotheses_untried.md](hypotheses_untried.md). | BLM closed claim distance (external), GeoDAWN K/Th/U/TC (external; `training_features` bands 1–19 do not include K, Th or U) | Claims staked over alteration and geothermal targets, co-located with radiometric alteration. | Claims are staked over unmapped systems, so off-catalogue claims are discovery targets. | Mineral claim staking over lithologic or radiometric anomalies that are not faults. | Adds an external land-status layer. | **Not verified.** The owner mirror holds a derived BLM raster (`data/external/audit_sources/blm_closed_claim_distance_m.tif`). It is third-party, not an official BLM download, and BLM is not reachable from this sandbox. | High |

## Validation plan (applies to every hypothesis)

1. Pre-register the mechanism, the named mimic and the decision rule before running.
2. Build every label-dependent feature from visible faults only. Use `b_visible_px` for exclusions.
3. Run the single-feature leakage canary (AUC above 0.90 means leakage until proven otherwise).
4. Compare pooled HOLDOUT-DTI with its spatial-block 95% CI against a **budget-matched random control**, using paired resampling.
5. Run the full-registry uniqueness gate (`scripts/focus_registry_uniqueness.py`) on the final dots.
6. Stop at the experiment budget. Nothing is promoted without a receipt from the submission page.

## Irregularities for review

- The 0.07412 figure in the submission decision record (east half, 95% CI 0.05987–0.09793) is a **catalogue proxy**, not a holdout score. For the same v4 base, the pooled hide-and-recover HOLDOUT-DTI (E1 control C0, reproduced byte-identical in E2) is 0.03313 [0.02694, 0.03920], 22,232 withheld positives. The two numbers use different protocols and should not be compared.
- The GEMSDOE32 explanation and the metric's known-fault masking disagree in the repo. Some documents say masked known faults make near-catalogue deletions worthless. Others say near-catalogue dots add false-positive weight. The organizer thread that would settle this (community.drivendata.org/t/…/11516) is not reachable from this sandbox.
- The whole-array checker (`scripts/check_submission.py`) has two outside-footprint rules that cannot both pass on any file tested: the official sample is NaN outside, and the strict [0, 1] whole-array rule fails it. This is unresolved and is not hidden in any score.
