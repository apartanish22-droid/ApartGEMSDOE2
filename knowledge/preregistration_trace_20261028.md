# Pre-Registration: H-TRACE — Oriented Trace-Coherence Emission (2026-10-28 session)

- **Repository / branch**: `apartanish22-droid/ApartGEMSDOE2` · `arena/7ec4400f-apartgemsdoe2`
  (fast-forwarded to `main` `e971255` at session start; includes PR #15–#20 fail-closed corrections).
- **Protocol**: PARALLEL-RUN PROTOCOL as restated in `README.md` (≤3 experiments, ≤2 h,
  shared `gems32` stack + `scripts/evaluate_holdout.py`/`src/gems32/holdout.py` +
  `scripts/submission_writer.py`, leakage canary AUC ≤ 0.90, lane gates
  surface |Spearman| ≤ 0.90 and final-dot ≤ 70 % within 3 px).
- **Lane assignment irregularity (IR-TRACE-01)**: the supplied prompt again contains no distinct
  single method paragraph. This session's lane is taken from the user's explicit instruction
  *"Work on the next steps from the previous sessions first"* combined with the previous
  session's recorded next step in `README.md` ("Replace pixelwise far-field crest extraction
  with a 5–15 km Geodesic / Oriented Radon Minimal-Path Curve Tracer operating on the
  updip-migrated H-UDSR Dual-Cover posterior"). This is declared, not silently self-invented.
- **H2 irregularity (IR-TRACE-02)**: PR #20 merged an H2 "fractal" raster whose own run card
  (`docs/data/run_card_h2.json`) states it was generated in DEMO MODE from *seeded
  pseudo-features* with `holdout_dti: null`, yet `docs/EXECUTIVE_SUMMARY_H2.md` says
  "OK TO SUBMIT: CONDITIONALLY YES" with a dot-count score projection. That guidance is
  withdrawn in this session; H2 verdict is corrected to `negative` (synthetic demo).

## Verified starting facts (recomputed this session on restored, SHA-256-pinned bytes)

1. Lineage: H19-5 121,131 px ⊃ D1.5 60,069 ⊃-support D2.8 44,090 (exact subset of H19-5);
   `(D2.8 & d_catalogue>2px) XOR GEMSDOE32_B2 == 0` (37,654 dots; 6,436 collar dots removed).
2. 13GEMSDOE lattice (206,895 dots) 3-px dilation covers 5,160,724 / 5,167,373 footprint
   cells (99.8713 %); 6,649 uncovered ⇒ any 37,654-dot raster has ≥ 82.34 % literal lattice
   overlap, and even a 26,173-dot raster ≥ 74.60 %. Literal ≤ 70 % is attainable only with
   ≤ 22,163 dots *and* ≥ 30 % of dots forced into the 6,649 lattice-hole cells.
3. Public leaderboard snapshot fetched 2026-10-28 (organizer-published page, not a receipt):
   rank 1 = 0.4544, rank 2 = 0.3916, ranks 3–23 ≈ 0.326–0.391.
   The prompt's 0.3195 / 0.4413 figures are superseded historical claims.
4. Current same-evaluator holdout best in this repo (`GEMSDOE32-HIDE-RECOVER-v3.0`,
   22,232 withheld positives): H-UDSR EXP-2 `HOLDOUT-DTI 0.113696 [0.101306, 0.126712]`
   (failed sparse-uniqueness, 80.62 % vs a sibling raster); fold-honest D28_B2 control
   `0.099202 [0.085951, 0.112668]`.

## Five candidate hypotheses (ranked before implementation)

| Rank | ID | Layers | Physical signature | Why it may catch catalogue-missing faults | Difference vs this repo | Non-fault mimic | Data obtainable? | Expected lift / cost |
|---:|---|---|---|---|---|---|---|---|
| 1 | **H-TRACE** (adopted) | H-UDSR Dual-Cover OOF posterior (53 pure-physical channels: 35-ch shared stack + 18-ch updip stack) | Oriented line-integral coherence: max over 8 orientations of (segment mean × segment support fraction) at 1.5 km and 3.1 km, geometric-mean across scales; optional hysteresis gap-bridging along orientation | Expert-hidden faults are long quasi-linear traces; pixelwise GBDT posteriors speckle (isolated high pixels from lithologic noise pay FP mass), while real traces give sustained collinear support. Coherence gating raises credit/dot and bridges small sediment-covered gaps without copying any registry support | AP-1/AP2/H-UDSR all emitted from pixelwise fields with only local (≤5 px) crest/NMS logic; no km-scale oriented line integral or hysteresis tracing exists in this repo | Roads/rail embankments, Lake Lahontan shoreline benches, GeoDAWN flight-line stripes (all long linear features) | YES — all inputs restored & hash-verified locally | Medium-high / medium (~30 min CPU) |
| 2 | H-PU | Same 53 channels | Positive-unlabeled (spy/Elkan–Noto) GBDT: off-catalogue treated as unlabeled, not negative | Supervised negatives contain the very blind faults sought; PU removes that label bias | Not implemented in this repo; sister-repo PU lanes scored 0.0206–0.1890 (user-reported list) | Same lithologic mimics as base features | YES | Medium / medium |
| 3 | H-FRACTAL-REAL | Bands 12/19 (DEM), 2/3/14 (mag), GeoDAWN rad u8 | Multi-scale box-counting fractal dimension × azimuthal anisotropy (PR #20 H2 idea, but on real bands as extra GBDT channels) | Fault-zone fracture networks raise scale-invariant roughness even where scarps are buried | PR #20 H2 used seeded pseudo-features only; no real-data fractal channel exists here | Lithologic contacts, volcanic flow margins, fan toes | YES | Low-medium / low (channels only) |
| 4 | H-SEG | Posterior support components | Connected-component length × linearity (eigenvalue ratio) reweighting; drop speckles | Removes the 1-px speckle FP mass measured in historical supports | Partially subsumed by H-TRACE; cheaper fallback | Long thin cultural features survive the same filter | YES | Low / low |
| 5 | H-INSAR | NASA OPERA DISP-S1 LOS velocity (ASF DAAC) + bands 8/15 | mm/yr vertical-velocity step across blind hydraulic baffle faults | Direct poroelastic signature of concealed intrabasin faults | No InSAR layer anywhere in this repo | Groundwater pumping cones, geothermal production subsidence | **NO in sandbox** — `asf.alaska.edu` outside outbound allowlist (GitHub/PyPI/npm only); documented, not viable this session | High theoretical / blocked |

## Frozen lane (H-TRACE) and 3-experiment budget

> **Lane**: Starting only from the leak-free H-UDSR Dual-Cover OOF posterior (no catalogue-distance
> feature, trained per holdout cell on visible faults only), reshape the emission field by
> km-scale oriented trace coherence (1.5 km + 3.1 km, 8 orientations, continuity-weighted),
> then emit 37,654 binary dots with the shared exact-gain emitter logic
> (`emit_axial_crest_budget`, min-sep 2.9 px) outside the B = 2 px visible-catalogue collar.

- **EXP-1 CTRL-T0**: posterior F0 alone → axial-crest emission. (Internal control; counts as experiment 1.)
- **EXP-2 TRACE-T1**: field = F0 × (0.2 + 0.8·Tn), Tn = trace coherence normalised by its
  footprint p99.5 → same emission.
- **EXP-3 TRACE-T2**: hysteresis support (orientation-wise binary closing, 5-px line, of the
  EXP-2 seed support; field zero outside support ∪ top-posterior seeds) → same emission.

No parameter tuning after holdout results are seen. Bug fixes only, documented.

## Evaluation & gates (all numbers labelled HOLDOUT-DTI or ORGANIZER-CONFIRMED; neither available ⇒ null)

- Holdout: `GEMSDOE32-HIDE-RECOVER-v3.0` (8 cells, 22,232 withheld positives, pooled DTI
  α=0.2 β=0.8, 300 m triangular kernel, 140-cluster bootstrap 95 % CI), paired vs fold-honest
  D28_B2 recomputed this session. Secondary diagnostic only: `GEMSDOE32-SGMC-CAL-v3.0`
  (62,703 withheld positives) — **not a promotion gate**, because a direct SGMC emission is
  user-reported at 0.0512 on the leaderboard while B2 (SGMC_cal 0.0641) is user-reported at
  0.2778; SGMC is therefore demonstrably not the hidden truth.
- **G1 format**: saved bytes = 1-band float32 GTiff, EPSG:32611, shape/transform equal to the
  owner-mirrored template, finite [0,1] in footprint, whole-array finite [0,1] for `-zeros`,
  zero positive pixels on catalogue labels. (Mirror is not organizer-authenticated;
  portal acceptance stays `null`.)
- **G2 holdout**: point HOLDOUT-DTI > 0.113696 (current repo best) **and** paired 95 % CI
  vs fold-honest D28_B2 strictly positive.
- **G3 canary**: label-free trace fields T15/T31 (from S_phys channel 14) single-feature
  oriented AUC ≤ 0.90 against withheld positives.
- **G4 uniqueness**: surface |Spearman| ≤ 0.90 vs all 500 extended-registry rasters
  (451 live focus + 49 extra, fetched 2026-10-28) before placement; final dots ≤ 70 %
  within 3 px vs every non-space-filling registry raster and vs this repo's AP-1/AP2/H-UDSR/H2
  masks. Literal overlap vs the space-filling lattice is reported exactly; per repo precedent
  the literal rule remains binding for a `promote` verdict, with the shared
  `registry_audit` null-calibrated excess reported alongside.
- **Verdict**: `promote` only if G1–G4 all pass including the literal lattice rule;
  otherwise `negative` (research artifact). No leaderboard estimate will be produced:
  no calibrated mapping from catalogue hide-recover to the expert-hidden test set exists.
