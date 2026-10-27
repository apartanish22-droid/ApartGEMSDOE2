# Executive summary — ApartGEMSDOE2 (2026-10-27)

**Decision: NO file is OK TO SUBMIT.** Download the new unique AP-1 GeoTIFF for research only
(`docs/downloads/apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros.tif`, SHA-256
`973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28`). It is unique (max 20.1% within
3 px of any focus-9 best) and format-valid (13/13 strict audit), but failed the holdout gate
(HOLDOUT-DTI 0.0389 [0.0282, 0.0491], GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld, vs champion
fold-local 0.0992 [0.0860, 0.1127]; paired Δ −0.0603 [−0.0859, −0.0401]) and SGMC gate
(0.0190 vs 0.0641 calibrated). Leaderboard estimate: **NOT ESTIMABLE** (no validated transfer).
Best historical submission remains GEMSDOE32 B2 at **0.2778 OWNER-REPORTED** (no receipt) — already
submitted, do not resubmit. Live #1 fetched 2026-10-27: **0.4544** (xiaofanhu).

Why 0.2778 leads the family (measured geometry + OWNER-REPORTED ladder): champion = d2.8 (44,090)
minus 6,436 dots with d_cat ≤ 2 px. DTI (α=0.2, β=0.8, R=300 m) charges 0.2 per uncredited dot;
thinning to the break-even (k > 0.2·DTI) and collaring raised mean credit. Add-backs scored less
(33: 0.2632; 36: 0.2750). Beating it needs a better *field* (≈+25% mean credit for 0.3195 on the old
ladder; more today), not more emission tuning. AP-1's field was worse — a negative result, recorded.

Per-site detail, hypotheses AP-1…AP-5, and irregularities IR-AP-01…06: `docs/executive-summary.html`.
Pre-registration: `knowledge/preregistration-20261027.md`. Evidence: `evidence/*.json`.

## Run card (final)

```json
{
  "hypothesis": "Blind dilatational stepovers coincide in geodetic strain, conductivity edge, basement step and gravity edge (AP-1).",
  "mechanism": "Geometric-mean percentile-rank coincidence (bands 4/7/8 x grad17 x grad15 x grad13), score-ordered Poisson min-sep 2.8px, B=2, 37,654 dots.",
  "named_non_fault_mimic": "Basin-margin depocentre edges, buried volcanic/pluton contacts, aquifer lithologic boundaries.",
  "holdout_dti": 0.0389,
  "holdout_ci95": [0.0282, 0.0491],
  "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
  "n_withheld_positives": 22232,
  "correlation_overlap_vs_registry": "surface Spearman ~0.01 (300k sample); final dots max 20.1% within 3px vs focus-9; lattice 99.7% (IR-AP-01)",
  "raster_sha256": "973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28",
  "validator_output": "PASS 13/13 strict audit, both -zeros (whole-array [0,1]) and -nan modes; 0 NaN in footprint; CRS/shape/transform match template",
  "submission_name": "apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros",
  "submission_note": "AP-1 dilat+cond+base+grav coincidence 37654d B2 | HOLDOUT-DTI 0.0389 vs champ 0.0992 | 1f26aa05 | DO NOT SUBMIT",
  "verdict": "negative"
}
```
