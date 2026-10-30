# Preregistration record — H-CATLOGIT-OOF and H-EQDENS-TOPN (30 Oct 2026)

**Disclosure on timing.** The lane plan (lane name, features, budget-matched N = 37,654, leakage
canary before use, quadrant-out-of-fold training, catalogue masking) was written into the working
notes **before** any candidate code ran. The concrete single-band selection rule for the second
candidate was fixed **after** the first candidate and both canary tables (SGMC and hide-and-recover)
had been printed. That rule is therefore disclosed as post-canary, not as a blind prior choice.
Nothing in this record was tuned on the SGMC truth after it was seen.

## Scope and standing constraints
- Official target: organizer scoring masks known USGS/INGENIOUS pixels (DrivenData forum, thread 11516,
  staff reply, 2026-09-16). Local scores below are **HOLDOUT-DTI** proxies, not organizer scores.
- Budget: three experiments or two hours. Counted experiments in this record: **2** (E1, E2).
  The canary and the nine-site audit are tests and audits, not experiments.
- Submission: no candidate is approved. The selector step is not run.

## H-CATLOGIT-OOF (experiment E1)
- **Layers:** the 19 verified GeoDAWN/USGS/3DEP bands in `training_features.tif`
  (magnetics, gravity, relief, strain, conductivity, depth-to-basement, earthquake density).
- **Mechanism:** a linear discriminant trained on mapped catalogue pixels in three quadrants ranks
  unmapped ground in the fourth. Leave-one-quadrant-out gives out-of-fold scores.
- **Named non-fault mimic:** alluvial-fan and pediment margins (steep relief and gravity gradients
  without slip).
- **Implementation:** `scripts/build_catlogit_candidate.py`; top 37,654 non-catalogue cells, binary.
- **Prediction:** above the random-dot null on the off-catalogue SGMC proxy.

## H-EQDENS-TOPN (experiment E2)
- **Selection rule (fixed before E2 ran, after the canary):** the single band with the highest
  hide-and-recover oriented AUC. That band is `ieq_n100a15` (AUC 0.560). The SGMC canary was not
  used for this choice.
- **Mechanism:** declustered earthquake intensity marks active fault zones.
- **Named non-fault mimic:** Walker Lane seismic clusters around volcanic and hydrothermal centres
  that have no mapped faults.
- **Implementation:** `scripts/build_topn_feature_candidate.py --band ieq_n100a15 --direction high`.

## Canary (protocol item 4)
- `scripts/feature_canary.py`; output `evidence/feature_canary_sgmc_20261030.json`.
- SGMC truth: max oriented AUC 0.755 (`det_elev_slope`). Hide-and-recover truth: max 0.560.
- No feature exceeds 0.90, so no leakage is flagged. A lower AUC is not proof of no leakage.

## Pass criteria (set before the gates ran)
1. G1 format: repo 12-point checker passes for both NaN and zero outside-footprint variants.
2. G2 proxies: SGMC raw and HOLDOUT-DTI CI must clear the matched random null (same N).
3. G3 registry: literal |Spearman| ≤ 0.90 and within-3-px ≤ 70% for every registry raster.
   Space-filling rasters are reported literally. They are not exempted silently.

## Results
See `evidence/run_card_20261030.json` (verdicts) and `evidence/gates_*_20261030.json` (receipts).
Both candidates fail G2 and G3. Verdicts: **negative**.
