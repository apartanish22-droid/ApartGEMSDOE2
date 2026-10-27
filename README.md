# ApartGEMSDOE2 — H-UDSR Updip-Migrated Tilt-Depth & Transtensional Hydrothermal Fault-Trace Inversion

**Competition:** [DrivenData — Find the Faults: DOE Geothermal Exploration (GEMS Prize #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)  
**GitHub Pages Dashboard:** `docs/index.html` & `docs/executive-summary.html`  
**Core Values (Arena AI):** **Maximize P(Win)** · **Own the Outcome**

---

## Arena AI Core Values in Execution

- **Maximize P(Win):** Never waste a DrivenData submission slot on an `H19-5` duplicate or a collar-crowded OOF overfit. Pre-register physical hypotheses before touching models, test every single feature through an automated Leakage Canary (`AUC <= 0.90`), audit both continuous surfaces (`|Spearman| <= 0.90`) and emitted dots (`within_3px <= 0.70`) against **488** focus/historical/sibling rasters, and report paired 256-block spatial cluster-bootstrap confidence intervals without cherry-picking or score projections.
- **Own the Outcome:** Verify every external file byte-for-byte via SHA-256, sanitize unflagged upstream corruptions (`IR-APART2-01`: `1,870` overflow `F2mDAB` records up to `5.47e12` in raw 2m probe DBF), eliminate the DrivenData `"Predicted values must be in range [0, 1]"` portal rejection programmatically (`nodata=None`, `12,279,160 / 12,279,160` finite `float32` values strictly in `{0.0, 1.0}`), and verify everything through automated `pytest` and CLI validators with **zero human inspection**.

---

## Immediate Deliverable & Clear DrivenData Submission Status

| Field | Verified Value |
|---|---|
| **Unique GeoTIFF File** | [`docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif`](docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif) (`164,130` bytes) |
| **Single-TIF ZIP Archive** | [`docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.zip`](docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.zip) (`127,938` bytes) |
| **GeoTIFF SHA-256** | `1f2c28e9eba172fe775672c07a0b859712838893787d4423f44459c6c84b175c` |
| **DrivenData Submission Name** | `apartgemsdoe2-udsr-exp3-strat2reg-26173-zeros` |
| **Short Note (105 / 140 chars)** | `ApartGEMSDOE2 H-UDSR EXP-3: updip grav/RTP/MT + DualCover OOF + 2-stage 300m submod (26173d, [0,1] zeros)` |
| **Automated Validator (`--strict-finite`)** | **PASS (`exit_code = 0`)** — `EPSG:32611`, `3730 × 3292`, single band, `min = 0.0`, `max = 1.0`, `0` NaNs anywhere (`12,279,160` finite cells), `0` public-catalogue overlap |
| **Uniqueness Gate (488 Rasters)** | **PASS** — **`46.52%`** 3-px overlap vs `GEMSDOE32 B2` (`<= 70%`); max sparse 3-px across all 488 rasters = **`69.42%`**; max surface `|Spearman|` = **`0.1189`** (`<= 0.90`) |
| **`HOLDOUT-DTI` (`GEMSDOE32-HIDE-RECOVER-v3.0`)** | **`0.094698`** (`95% CI [0.082240, 0.107307]`, `n_withheld_positives = 22,232`; `EXP-2` unstratified ablation = **`0.113696`** `[0.101306, 0.126712]`) |
| **`HOLDOUT-DTI` (`GEMSDOE32-SGMC-CAL-v3.0`)** | **`0.039808`** calibrated (`95% CI [0.034404, 0.045291]`, raw SGMC `0.054310`, `n_withheld_positives = 62,703`) |
| **Clear Submit / Hold Guidance** | **1. DO NOT SUBMIT any raster from `GEMSDOE24..36` (all 9 are `86.7%–100.0%` overlapping `H19-5` duplicates).**<br>**2. OK TO DOWNLOAD & SUBMIT `apartgemsdoe2-...-zeros.tif` if allocating an orthogonal, genuinely unique, portal-safe `[0, 1]` exploration submission.**<br>**3. Protocol Run Card `verdict: "negative"` (HOLD scarce weekly slot if strictly requiring paired superiority over both fold-honest `D28_B2 = 0.099202` and `SGMC = 0.064121`).** |

---

## 1. Executive Summary Table Across All 9 Focus Sites & `ApartGEMSDOE2`

Every score below follows **Protocol Rule 3 (Strict Score Labeling)**: either `ORGANIZER-CONFIRMED` (from repository leaderboard ledgers; note `IR-APART2-06` flags that raw DrivenData portal screenshot PNGs were not committed in prior sessions) or `HOLDOUT-DTI` (with exact evaluator version, `n_withheld_positives`, and 256-block spatial cluster-bootstrap 95% CI). **Zero projections are reported.**

| Site | Best File | Dots & Outside Encoding | Repo LB Score (`ORGANIZER-CONFIRMED`*) | `HOLDOUT-DTI` (`GEMSDOE32-HIDE-RECOVER-v3.0`, n=22,232) | `HOLDOUT-DTI` (`GEMSDOE32-SGMC-CAL-v3.0`, n=62,703) | 3-px Overlap vs `GEMSDOE32 B2` | Uniqueness & Submit Status |
|---|---|---|---|---|---|---|---|
| **ApartGEMSDOE2 (Ours · EXP-3)** | `apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif` | `26,173` (`0.0` `-zeros`, `nodata=None`) | *Unsubmitted (no projection)* | **`0.09470`** `[0.08224, 0.10731]` *(fold-honest OOF)* | **`0.03981`** `[0.03440, 0.04529]` | **`46.52%`** (max 488-reg: `69.42%`) | **UNIQUE & `[0,1]` VERIFIED** — Only non-duplicate file; exploratory slot OK (`verdict: negative` vs `0.0992`) |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | `37,654` (`0.0` `-zeros`) | **`0.2778`** | `0.00452` static / **`0.09920`** fold-honest `B=2` `[0.08595, 0.11267]` | **`0.06412`** `[0.05673, 0.07165]` | `100.0%` (`(D28 & d>2) ^ B2 == 0`) | **DO NOT SUBMIT** (Already scored; `D2.8` subset) |
| **GEMSDOE36** | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | `38,854` (`0.0` `-zeros`) | **`0.2750`** (`kpl36`: `0.1647`) | `0.00458` `[0.00349, 0.00580]` | `0.06444` `[0.05704, 0.07195]` | `97.4%` (`B2 - G36 == 0`, `+1,200`d) | **DO NOT SUBMIT** (Strict superset of `B2`) |
| **GEMSDOE28** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | `37,660` (`NaN` `-nan`) | **`0.2710`** (`s21`: `0.0206`) | `0.02936` `[0.02350, 0.03578]` | `0.06297` `[0.05582, 0.07027]` | `95.5%` | **DO NOT SUBMIT** (Duplicate + `NaN` outside) |
| **GEMSDOE31** | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | `40,199` (`NaN` `-nan`) | **`0.2708`** | `0.03052` `[0.02495, 0.03638]` | `0.06301` `[0.05579, 0.07040]` | `95.4%` (`G31 - D28 == 0`) | **DO NOT SUBMIT** (Subset of `D2.8` + `NaN`) |
| **GEMSDOE33** | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | `41,865` (`0.0` `-zeros`) | **`0.2632`** (`s33`: `0.0963`) | `0.05197` `[0.04422, 0.05988]` | `0.06255` `[0.05535, 0.06982]` | `92.6%` | **DO NOT SUBMIT** (Duplicate `D2.8` graft) |
| **GEMSDOE25** | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | `44,090` (`NaN` `-nan`) | **`0.2600`** | `0.09674` `[0.08416, 0.10953]` | `0.06059` `[0.05355, 0.06773]` | `88.2%` | **DO NOT SUBMIT** (`D2.8` + `NaN` outside) |
| **GEMSDOE30** | `gemsdoe30-d28-poisson300m-offcat-44090-20261003-8cf893ea-zeros.tif` | `44,090` (`0.0` `-zeros`) | **`0.2600`** | `0.09674` `[0.08416, 0.10953]` | `0.06059` `[0.05355, 0.06773]` | `88.2%` (`G25 ^ G30 == 0`) | **DO NOT SUBMIT** (Pixel-identical twin of `G25`) |
| **GEMSDOE24** | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | `60,069` (`NaN` `-nan`) | **`0.2477`** (`gvc1`: `0.0859`) | `0.09315` `[0.08069, 0.10574]` | `0.05793` `[0.05121, 0.06478]` | `88.5%` | **DO NOT SUBMIT** (Over-dense `D1.5` + `NaN`) |
| **GEMSDOE27** | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | `61,328` (`NaN` `-nan`) | **`0.2449`** | `0.09275` `[0.08036, 0.10531]` | `0.05826` `[0.05152, 0.06512]` | `86.7%` | **DO NOT SUBMIT** (Over-dense `D1.5` + `NaN`) |

---

## 2. Deep PhD-Level Study: Why `GEMSDOE32` Achieved `0.2778` & How to Beat It

1. **Exact Set-Algebra & Metric Arithmetic (`DTI = TP / (TP + 0.2*FP + 0.8*FN)`, `R = 300 m`):**
   - `13GEMSDOE`'s space-filling `5 px` lattice (`206,895` dots -> `0.0904`) calibrates the hidden organizer fault mask in Nevada at `|G| ≈ 12,691` pixels.
   - Thinning `19GEMSDOE`'s continuous lineament skeleton `H19-5` (`121,131` px -> `0.1922`) to `d = 2.8 px` spacing (`D2.8`, `44,090` dots -> `0.2600` in `GEMSDOE25` & `GEMSDOE30`) eliminated redundant 300 m kernel overlap, cutting `0.2 * FP` by `15,408` units.
   - Byte-level XOR proves **`(D28 & (d_catalogue > 2.0)) ^ GEMSDOE32_B2 == 0`**. Removing the `6,436` near-catalogue flank dots (`1 <= d_cat <= 2 px`) cut the denominator by `-0.2 * 6,436 = -1,287.2` while losing virtually zero hidden off-catalogue truth, lifting `4,932 / 18,971 = 0.2600` to **`4,932 / 17,683.8 = 0.2789` theoretical (`0.2778` actual)**.
   - Byte-level XOR also proves **`GEMSDOE25 ^ GEMSDOE30 == 0`** (both scored `0.2600`), proving `-zeros.tif` (`nodata=None`) and valid `-nan.tif` score identically while `-zeros.tif` completely prevents portal `[0, 1]` NaN validation failures.

2. **Why `0.2778` Plateaued & Why Recent OOF ML Entries Collapsed Below `0.10`:**
   - **Dipping-Fault Hanging-Wall Offset:** Basin-and-Range normal faults dip `45°–60°` into low-density grabens, shifting mid-depth (`0.5–2.5 km`) gravity, magnetic, and MT horizontal-gradient peaks `300–1,000 m` basinward — **outside** the `R = 300 m` DTI kernel on the surface fault break.
   - **24.66% 1 m LiDAR Gap:** `1,272,913` of `5,167,373` footprint cells lack 1 m USGS 3DEP LiDAR.
   - **10,099 Single-Pixel Speckles & Score-Blind Thinning:** `H19-5` carries `10,099` isolated 1-px noise fragments (`~28%` of `B2` FP penalty) and used raster-scanline greedy order instead of submodular 300 m marginal gain.
   - **The Collar-Crowding Trap:** Recent OOF GBDTs (`s21 = 0.0206`, `gvc1 = 0.0859`, `s33 = 0.0963`, and our own unstratified `EXP-2`) packed `88%–96.2%` of all dots into `2 < d_cat <= 15 px`, starving blind far-field faults (`d_cat > 15 px`, where `52%–58.4%` of winning submissions' dots reside).

3. **Scientific Finding from Our 3 Controlled `H-UDSR` Experiments (`EXP-1`, `EXP-2`, `EXP-3`):**
   - Pre-registered in [`knowledge/preregistration_udsr_20261027.md`](knowledge/preregistration_udsr_20261027.md) (5 ranked hypotheses: `#1 H-UDSR`, `#2 H-CGSC`, `#3 H-ARAD`, `#4 H-MKPA`, `#5 H-INSAR`).
   - All **55 channels** passed the **Protocol Rule 4 Leakage Canary** (`max single-feature oriented ROC-AUC = 0.7680 <= 0.90`; [`evidence/leakage_canary_55ch.json`](evidence/leakage_canary_55ch.json)).
   - **`EXP-1 (UDSR-PurePhysics)`:** `HOLDOUT-DTI = 0.045000` (`[0.036552, 0.053887]`), `SGMC_cal = 0.044914`, `>15px = 57.0%`, `max_sparse_3px = 0.4839`.
   - **`EXP-2 (UDSR-DualCover-OOF)`:** **`HOLDOUT-DTI = 0.113696` (`[0.101306, 0.126712]`)** — beating fold-honest `D28_B2` (`0.099202`) by `+0.014494` (`97.2%` of cluster bootstraps positive) and `H19-5` (`0.073424`) by `+0.040272` (`100%` positive), **but** crowded `96.2%` of dots into `2 < d <= 15 px` (`>15px = 3.8%`) and breached the 70% overlap gate (`80.62%` vs sibling `WBGGEMSDOE3 hce1`).
   - **`EXP-3 (UDSR-Stratified-TwoRegime)`:** Enforced 50/50 two-stage residual submodular crest packing (`50.43% > 15 px`, `26.73%` inside the `24.66%` 1 m LiDAR gap, `0.00%` in flat deep playas), passing **every** 488-raster uniqueness gate (`46.52%` vs `B2`, `69.42% <= 70%` max across 488 rasters, surface `|Spearman| = 0.1189 <= 0.90`), beating static `B2` (`+0.090183`, 95% CI `[+0.077929, +0.102499]`) and `H19-5` (`+0.021274`, 95% CI `[+0.009482, +0.032789]`), while finishing statistically tied with fold-honest `D28_B2` (`0.094698` vs `0.099202`) and below `B2` on 1:500k `SGMC` (`0.039808` vs `0.064121`).
   - **How to Reach `0.3195` & `0.4413` Next Session:** Replace pixelwise far-field crest extraction with a **5–15 km Geodesic / Oriented Radon Minimal-Path Curve Tracer** operating directly on our updip-migrated `H-UDSR` Dual-Cover posterior (`0.7028` blind far-field ROC-AUC), uniting `H19-5`-class multi-kilometer lineament continuity with footwall dip-correction and full LiDAR-gap parity.

---

## 3. Reproducible Automated Pipeline & Verification (Zero Human Inspection)

```bash
# 1. Restore SHA-256 verified competition + external data & 442 focus-site rasters
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/fetch_focus_registry.py --jobs 8
.venv/bin/python scripts/build_extended_registry.py

# 2. Run all 37+ automated unit & deliverable format/uniqueness tests
.venv/bin/pytest -q

# 3. Validate the emitted GeoTIFF programmatically (strict whole-array [0, 1] finite check)
.venv/bin/python scripts/check_submission.py \
  docs/downloads/apartgemsdoe2-udsr-exp3-strat2reg-26173-20261027T223500Z-017adbb0-zeros.tif \
  --strict-finite
```

---

## 4. Limitations, Needed Access & Next Steps

1. **Pixelwise vs. Geodesic Lineament Continuity:** `HistGradientBoostingClassifier` + local 4-azimuth NMS resolves `100–500 m` crests well (`EXP-2 = 0.1137` HR DTI) but lacks `5–15 km` curve-integral regularization across dissected bajadas (`SGMC_cal = 0.0398` vs `B2 = 0.0641`).
2. **Sandbox Outbound Host Allowlist:** Outbound HTTPS in this sandbox is restricted to `github.com`, `codeload.github.com`, `api.github.com`, `pypi.org`, `files.pythonhosted.org`, and `registry.npmjs.org`. Direct download of NASA OPERA L3 DISP-S1 Sentinel-1 InSAR velocity grids (`asf.alaska.edu` / Earthdata) and live USGS ScienceBase queries was unavailable; staging OPERA DISP-S1 into the mirrored manifest is recommended for next session.
3. **Leaderboard Screenshot Provenance:** Repo-reported live scores (`0.2778`, `0.3195`, `0.4413`) come from sibling git ledgers without archived portal screenshot PNGs (`IR-APART2-06`).

---

## 5. Official Parallel-Run Protocol Run Card

Full JSON stored in [`evidence/apartgemsdoe2_run_card_20261027.json`](evidence/apartgemsdoe2_run_card_20261027.json):

```json
{
  "hypothesis": "H-UDSR (Updip-Migrated Tilt-Depth & Transtensional Hydrothermal Fault-Trace Inversion — EXP-3 Stratified Two-Regime)",
  "mechanism": "Projects hanging-wall mid-depth gravity, RTP magnetic, and MT electrical conductance horizontal-gradient/tilt contacts 250-800 m up-dip along +grad(depth_to_base_surf) & -grad(iso_grav_anom) onto the footwall surface fault break; fuses sanitized DOE GDR #1391 silica geothermometry + 2m probes + 281 paleo-sinters + 4-block leveled GeoDAWN K/Th & 214Bi radon ridges via a Dual-Cover OOF GBDT (53-ch M_Full + 50-ch LiDAR-free M_Gap) and exact bit-partition 2nd-component relay bridges, emitted via two-stage 300 m submodular crest packing.",
  "mimic_process": "Pleistocene Lake Lahontan wave-cut paleo-shoreline benches, closed evaporative playa brine/clay pans (depth_to_base_surf > 300 m & slope < 2 deg), TIGER/Line highway embankments, and GeoDAWN radiometric contractor flight-block boundary steps.",
  "holdout_dti": {
    "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
    "label": "HOLDOUT-DTI",
    "n_withheld_positives": 22232,
    "dti": 0.094698,
    "exp2_unstratified_ablation_dti": 0.113696,
    "sgmc_cal_v3_dti": 0.039808
  },
  "ci": [0.08224, 0.107307],
  "registry_correlation_overlap": {
    "passed": true,
    "n_focus_rasters_checked": 442,
    "n_extended_rasters_checked": 488,
    "surface_max_abs_spearman": 0.118932,
    "dots_max_sparse_within_3px_488": 0.694189,
    "dots_within_3px_vs_gemsdoe32_b2": 0.46521
  },
  "raster_sha256": "1f2c28e9eba172fe775672c07a0b859712838893787d4423f44459c6c84b175c",
  "validator_output": {
    "passed": true,
    "no_nan_inside_footprint": true,
    "no_nan_whole_raster": true,
    "values_in_0_1": true,
    "crs_shape_transform_match": true
  },
  "submission_name": "apartgemsdoe2-udsr-exp3-strat2reg-26173-zeros",
  "note": "ApartGEMSDOE2 H-UDSR EXP-3: updip grav/RTP/MT + DualCover OOF + 2-stage 300m submod (26173d, [0,1] zeros)",
  "verdict": "negative"
}
```

---

## 6. Archived Session Prompt & Competition Protocol Charter

<details>
<summary><strong>Click to expand exact session charter & Parallel-Run Protocol</strong></summary>

- **Competition:** `https://www.drivendata.org/competitions/306/competition-doe-gems/`
- **Focus Sites Studied:** `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`.
- **Core Mandates:**
  1. Review repository first, complete pending next steps autonomously, and verify all facts from official, free, auditable sources with zero hallucinations.
  2. Deeply study `GEMSDOE32` (`0.2778`) and all 9 focus sites; provide an executive summary table with exact file, labeled score (`HOLDOUT-DTI` vs `ORGANIZER-CONFIRMED`), uniqueness vs all sites, and submit/do-not-submit status.
  3. Formulate 3–5 concrete geological hypotheses before implementing; rank by expected DTI gain vs implementation cost; validate top candidate on spatially-blocked hide-and-recover holdout.
  4. Generate a genuinely unique `.tif` submission fixing `"Predicted values must be in range [0, 1]"` (`[0, 1]`, no NaNs inside footprint, single-band `EPSG:32611` matching `example_submission.tif`), verified purely via automated project gates without human inspection.
  5. Follow the **Parallel-Run Protocol**:
     - *Lane / Duplication Gate:* Continuous surface `|Spearman| <= 0.90` AND final dots `within_3px <= 0.70` vs registry rasters.
     - *Reuse, Don't Rebuild:* Reuse cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; fix shared bugs in-place.
     - *Strict Score Labeling:* Every number labeled `HOLDOUT-DTI` (evaluator version, `n_withheld_positives`, 95% CI) or `ORGANIZER-CONFIRMED`. Never write a projection as a score.
     - *Leakage Canary:* Single-feature holdout `AUC <= 0.90` across all channels before trusting results.
     - *Run Card & Budget:* At most 3 experiments; end with single JSON Run Card.
  6. Execute 3-pass quality audit (Pass 1: build & verify; Pass 2: fix bugs/edge cases/assumptions; Pass 3: full re-check vs prompt), publish clean GitHub Pages (`docs/`), and open + merge PR onto `main`.

</details>
