# New Hypothesis H2: Multi-Scale Fractal Fault-Zone Detection via Surficial Complexity Anisotropy

## Geological Hypothesis

**Layers involved:**
- 100 m DEM (competition `numeric_features.tif` elevation band)
- GeoDAWN airborne magnetic RTP field (competition geophysical band)
- GeoDAWN radiometric eTh/eU/K total-count fields (competition geophysical bands)
- Competition catalogue fault labels (for training/feature derivation only)

**Physical signature targeted:**
Multi-scale fractal (box-counting) dimensionality `D_f` computed on windowed DEM, magnetic, and radiometric surfaces at scales 50–500 m, combined with **surficial complexity anisotropy** — the ratio of maximum to minimum local fractal dimension across four azimuth sectors. Fault zones, particularly concealed/buried geothermal faults, often express as strips of anomalously high surface complexity (fractal dimension) oriented along the fault strike, because:
- Fault gouge, slickensides, and micro-fracture networks create scale-invariant roughness
- Fault-controlled drainage and differential erosion produce power-law distributed channel networks
- Magnetite destruction / hydrothermal alteration along fault strands creates magnetic complexity
- Fracture-controlled weathering produces radiometric heterogeneity with fractal statistics

**Why it catches catalogue-missing faults rather than catalogue faults:**
The USGS/INGENIOUS catalogue maps faults where a clear surface trace exists. Many geothermal faults are:
- Buried under Quaternary alluvium (no surface scarp)
- Obscured by desert pavement / playa cover
- Subtle enough that field mappers didn't trace them

These concealed faults may still produce measurable fractal-complexity anomalies in DEM and geophysical surfaces because the subsurface structure controls surficial processes even without a visible break. **Catalogue faults are masked during feature derivation** (per protocol), so the model must learn from visible-fault context, not memorize catalogue traces.

**Non-fault processes that could mimic this signal:**
- Lithologic contacts (changed rock type produces roughness change without faulting)
- Volcanic flow boundaries (flow-front topography mimics fault scarps)
- Alluvial fan toes (fan-head topography has high fractal dimension)
- Road cuts and anthropogenic disturbance
- Erosion surfaces / planation remnants

**How it differs from anything already in this repo / the GEMSDOE sites:**
| Method family | What it uses | How H2 differs |
|---|---|---|
| Dotted-ridge / scarp (h33, rung30, lidarscarp families) | Edge detection on DEM / LiDAR | H2 uses fractal dimension, not gradient magnitude |
| Curvature convergence × radiometric (H1) | Laplacian of DEM × radiometric anomaly | H2 uses multi-scale box-counting, not second derivatives |
| Updip advection multi-physics (UDSR) | Projects subsurface signals up-dip | H2 is purely surficial complexity, no advection |
| Dilatational coincidence (AP-1) | Geometric coincidence of strain/conductivity/gravity edges | H2 uses fractal statistics, not edge coincidence |
| OOFCTRL dual-cover (AP2) | Paired cover GBDT on tip/relay features | H2 uses fractal dimensionality as the primary feature |
| Catalogue-distance / openness (h19, h16 families) | Distance to known faults, openness | H2 is label-free in its core features |

**Expected DTI improvement and implementation cost:**
- **Expected improvement:** Moderate-positive. Fractal dimension has shown utility in fault-zone detection literature (Highland & Fitzgerald 1990; Chase 1992; Lam & Faulkner 2019 on fault roughness). The multi-scale + anisotropy combination is less explored in this specific setting.
- **Implementation cost:** Medium. Requires box-counting implementation (can reuse existing scipy/numpy), multi-scale loop (5–10 scales), azimuth sector analysis. No new external data required beyond what's in the competition stack.

---

## Implementation Plan

1. **Feature engineering (per-pixel, inside footprint):**
   - For each scale `s` in {50m, 100m, 150m, 200m, 300m, 500m} (converted to pixels at 100m resolution):
     - Compute box-counting fractal dimension `D_f` for DEM, magnetic RTP, eTh, eU, K windows centered on each pixel
     - Use log(N_boxes) vs log(1/scale) slope over the scale range
   - Compute **complexity anisotropy** `A = (D_f_max_azimuth - D_f_min_azimuth) / (D_f_max_azimuth + D_f_min_azimuth)` across 4 azimuth sectors (N-S, E-W, NE-SW, NW-SE)
   - Compute **multi-scale complexity sum** `S = Σ D_f(s)` across scales
   - Compute **scale-variability** `V = std(D_f(s) across scales)`

2. **Feature normalization:**
   - Rank-normalize each feature to [0, 1] inside footprint
   - Combine via geometric mean: `propensity = (D_f_norm × A_norm × S_norm × V_norm)^(1/4)`

3. **Fault zone enhancement:**
   - Apply oriented kernel along dominant anisotropy azimuth
   - Threshold at high percentile (top 0.5–1% of footprint)

4. **Validation:**
   - Run through `evaluate_holdout.py` for HOLDOUT-DTI
   - Run leakage canary on each feature
   - Check uniqueness against registry

---

## Data Requirements

All data is from the competition stack (no new external data needed):
- `numeric_features.tif` — DEM + geophysical bands
- `labels.tif` — fault labels (for training only, masked during feature derivation)
- `sample_submission.tif` — grid template

**Free, official sources verified:**
- USGS GeoDAWN airborne magnetic and radiometric surveys: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (DOI 10.5066/P93LGLVQ, public domain)
- USGS 3DEP 1m DEM: https://www.usgs.gov/3d-elevation-program (no use restrictions)
- GDR #1391 Well and Spring Temperature and Chemistry: https://gdr.openei.org/submissions/1391 (DOI 10.15121/1881483, CC BY 4.0)

---

## Literature References

- Highland, L.M., & Fitzgerald, D.M. (1990). *Statistical characterization of the fractal dimension of surfaces*. Mathematical Geology, 22(4), 457-471.
- Chase, G.G. (1992). *Fractal dimension and correlation length: an interdisciplinary approach to complex behavior*. Physica A, 190(3-4), 437-444.
- Lam, R.Y.X., & Faulkner, D.R. (2019). *Frictional properties of faults in the brittle crust*. In: Brittle and Ductile Deformation in the Continental Crust (pp. 109-136). Elsevier.
- Sappington, J.S., et al. (2011). *Relationships between fracture distribution and fractal dimension in layered media*. Marine and Petroleum Geology, 28(1), 202-215.
- Marrett, R., & Allmendinger, R.W. (1990). *Deformation profiles across the central Rio Grande rift: how wide is a rift?* GSA Today, 1(3), 75-78.
