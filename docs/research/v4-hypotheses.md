# v4 geological hypotheses (ranked) — 30 Oct 2026

Scope: fault discovery on the GEMS 100 m UTM 11N grid (EPSG:32611, 3,730 x 3,292). Layer names are the
`training_features.tif` band descriptions verified from the restored file (19 bands).
Every ranking below is a **prior**, not a result. Only H1 was run; H2–H4 are pre-registered
for the next session and have **not** been tested.

Competition metric and format: [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
(distance-weighted Tversky, alpha 0.2, beta 0.8, 300 m triangular kernel, float32 in [0,1], NaN/null outside bounds).
Rules: [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).

| Rank | ID | Layers (band #) | Physical signature targeted | Why it may find a fault absent from the USGS/INGENIOUS catalogue | Named non-fault mimic | How it differs from what is already implemented | Cost | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | **H1** ridge-NMS on magnetic + gravity horizontal gradients | `tmi_hg` (3), `iso_grav_anom_hg` (18), normal from `tmi` (14) | Local maxima of horizontal gradient across the lineament normal (Canny-style edge) | Uses only gradient ridges, not catalogue geometry, so it can flag unmapped contacts | Lithologic/intrusive contacts | Implemented as E2 (`scripts/ridge_candidate_v4.py`). **Result: negative** (proxy 0.0741). | Low | RUN, negative |
| 2 | **H2** tilt-angle zero-contour consensus | `tc` (6) tilt/curvature, `tmi_vg` (9) | Zero contour of the tilt angle (Miller & Singh 1994, [J. Appl. Geophys. 32, 213–217, doi:10.1016/0926-9851(94)90022-1](https://doi.org/10.1016/0926-9851(94)90022-1)) lying on a high-|grad| ridge | Zero-contour location is depth-independent and less sensitive to amplitude than H1, so it may recover subtler, lower-contrast faults | Magnetic lithology boundaries with the same tilt zero contour | Uses a **zero-crossing** of a derived field instead of gradient magnitude. Different signature from H1. | Low | NOT RUN (budget) |
| 3 | **H3** geodetic shear-strain localisation | `geod_shearrate` (7), `geod_2ndinv` (4), `geod_dilaterate` (8) | Ridges of strain rate, where deformation localises on an active fault | Strain is measured independently of magnetics/gravity, so it can flag faults with no magnetic contrast | Subsidence, irrigation, and network/interpolation artefacts in the geodetic product | Uses the geodetic channels, which none of the implemented candidates use. Resolution of the strain product is coarse, so expected gain is uncertain. | Low | NOT RUN |
| 4 | **H4** basement-step edge | `depth_to_base_surf` (15), `det_elev` (12) | Abrupt step in basement depth (basin-bounding normal faults) | Vertical offset of basement is a direct fault signature, not a magnetic one | Sedimentary facies change and erosional unconformities | Operates on the depth-to-basement layer, which is not used by H1–H3. **Provenance of this layer must be verified before use** (it may be derived from catalogue faults). | Low–medium | NOT RUN, provenance check required |
| 5 | **H5** 1 m DEM lineament (outside the stack) | 1 m DEM tiles listed in `1m_DEM_links.csv` (competition data tab) | Sub-metre scarp and lineament morphology | Highest-resolution independent evidence for surface traces | Erosion, roads, field boundaries | Requires the DrivenData data tab (login) and per-tile downloads. **Not obtainable from this sandbox** (drivendata.org not reachable). | High | BLOCKED — needs authenticated data placement |

## Ranking rationale

* Expected improvement and cost are judgement, not measured. H2 is ranked first among untested ideas because
  it is a different signature from H1 at low cost. H3 is ranked after H2 because the strain product has coarse resolution.
* H4 is held back until the provenance of `depth_to_base_surf` is verified. If it is catalogue-derived, using it would leak.
* H5 is the most promising in principle but is currently blocked by data access. Per the standing protocol it is not called viable until the data is obtained.

## Leakage and canary status

Per-feature leakage canary (AUC of each band vs catalogue fault pixels inside the footprint) ranges from 0.500 to 0.570
(`scripts/feature_canary_v4.py`, saved in `evidence/v4_feature_canary.json`). This is far below the 0.90 leakage threshold, but it is a single-pixel
measure and says nothing about spatial dependence.

## Sources

* [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (metric, format, feature list), fetched 30 Oct 2026.
* [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), fetched 30 Oct 2026.
* [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), fetched 30 Oct 2026.
* Miller, H.G. and Singh, V. (1994), J. Appl. Geophys. 32, 213–217, [DOI 10.1016/0926-9851(94)90022-1](https://doi.org/10.1016/0926-9851(94)90022-1); citation confirmed via [SCIRP reference listing](https://www.scirp.org/reference/referencespapers?referenceid=2306834).
