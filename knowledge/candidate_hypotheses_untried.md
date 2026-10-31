# Candidate geological hypotheses — untried (Parallel-run protocol lane: H-BLIND-CONDUIT)

**Lane assignment:** H-BLIND-CONDUIT — concealed geothermal faults missing from the USGS/INGENIOUS catalogue, targeted through structural-preparation × radiometric-anomaly × magnetic-deficit convergence on the competition grid (EPSG:32611, 3730 × 3292, 100 m).

**Budget:** 3 experiments / 2 hours. No weekly slot will be spent until the top candidate beats a frozen same-protocol holdout best.

**Evidence standard:** every number below is a projection, not a score. HOLDOUT-DTI cannot be computed in this sandbox because the DrivenData data tab is login-walled and the Dropbox mirrors are unreachable (verified). A separate selector must approve any slot.

---

## Hypothesis 1 — H-BLIND-CONDUIT (rank 1, selected for implementation)

**Layers:** GeoDAWN radiometric potassium anomaly (eTh/K ratio proxy), GeoDAWN total-field magnetics (demagnetization proxy), USGS 3DEP / competition DEM curvature convergence, and the competition grid coordinate frame (structural preparation zones).

**Physical signature:** concealed geothermal faults that have no surface scarp and no USGS/INGENIOUS catalogue trace still host hydrothermal alteration halos that enrich potassium (radiometric anomaly) and demagnetize host rock (magnetic low), while the damage zone creates curvature convergence at the surface. The product of normalized radiometric anomaly × normalized magnetic deficit × normalized curvature convergence targets blind fluid pathways.

**Why it catches catalogue-missing faults:** buried / alluvial-covered faults control alteration halos without requiring a visible scarp or catalogue trace. The catalogue only maps faults with surface expression; blind conduits in the deep geothermal system are missing by definition.

**Named non-fault mimics:** uneven crustal radioactivity / igneous-contact boundaries (radiometric anomalies without faults); mafic/ultramafic contacts (magnetic deficits without faults); concave mass-wasting or glacial terrain (curvature convergence without faults).

**How it differs from prior work in this repo:**
- H1 (radiometric × DEM curvature) is surface-expression dependent; this adds magnetic demagnetization and does not require a surface curvature signal at the fault trace.
- H-RAD-MAG-CONTRAST uses gradient products (edge detection); this uses direct anomaly magnitudes combined with structural preparation.
- Dotted-ridge / catalogue-distance families use known faults as priors; this explicitly masks all catalogue faults.
- GEMSDOE36's PINN is a black-box network; this is an interpretable physics-based combination.

**Expected DTI improvement:** unmeasured (no holdout data). Projection only — not a score.

**Implementation cost:** Low — can be built on the existing competition grid with a synthetic feature proxy; no external download required for the format-valid demo.

**Data viability:** Requires GeoDAWN radiometric + magnetics grids (USGS, CC0, DOI 10.5066/P93LGLVQ — listed on the USGS GeoDAWN release page, not reachable from this sandbox) and competition feature bands. For the demo, a synthetic proxy field on the known grid is used.

---

## Hypothesis 2 — H-DRAIN: paired drainage/fan displacement (rank 2)

**Layers:** USGS 3DEP 1 m bare-earth DEM (via competition `1m_DEM_links.csv`) + competition `det_elev` / `det_elev_slope`.

**Physical signature:** matching channel profiles offset by a consistent vector across a candidate break — displacement of drainage or fan edges, not just ridge strength.

**Why it catches catalogue-missing faults:** a degraded or buried scarp can still offset drainage or fan edges even where no trace is mapped.

**Named non-fault mimics:** fluvial terrace erosion, alluvial-fan avulsion, road cuts, stream capture.

**How it differs:** the repo has no paired-offset test; H-TRACE used line coherence only.

**Cost:** High — DEM tiling and profile matching.

**Data viability:** `1m_DEM_links.csv` is behind the DrivenData login wall; 3DEP tiles were not reachable from this sandbox. Not viable without authenticated data.

---

## Hypothesis 3 — H-FLIGHT: flight-line-subset stability of aeromagnetic edges (rank 3)

**Layers:** GeoDAWN line-level magnetics (USGS release, CC0); `tmi_vg` / `iso_grav_anom_hg` as context.

**Physical signature:** persistent subsurface contrast beneath alluvium survives line-subset resampling; leveling stripes do not.

**Why it catches catalogue-missing faults:** a real subsurface contrast should be stable across independent line subsets; artifacts from line-leveling should not.

**Named non-fault mimics:** line-leveling and micro-leveling artifacts at 200 m (Area 1) and 400 m (Area 2) line spacing.

**How it differs:** repo's Gaussian/Hessian features use the gridded product only; this uses line-subset stability.

**Cost:** Medium–high.

**Data viability:** GeoDAWN release is CC0 and lists flight-line CSVs, but not reachable from this sandbox. Not viable without external access.

---

## Hypothesis 4 — H-CHEM: across-boundary hydrochemical contrast (rank 4)

**Layers:** INGENIOUS well/spring chemistry and temperatures on opposite sides of candidate basin-margin normals (GDR submission 1391, DOI 10.15121/1881483, CC BY 4.0).

**Physical signature:** a barrier fault can separate fluid histories even where its trace is unmapped.

**Why it catches catalogue-missing faults:** chemistry contrast across a candidate fault tests for a barrier that surface mapping may have missed.

**Named non-fault mimics:** mixing, lithologic variation, sampling depth and time, pumping.

**How it differs:** H-UDSR uses point proximity and plumes; this needs paired cross-boundary comparisons.

**Cost:** Medium.

**Data viability:** Not reachable from this sandbox; spatial density and comparability not checked. Not viable without external access.

---

## Hypothesis 5 — H-MT: electrical conductance contrast across candidate faults (rank 5)

**Layers:** USGS MT conductance maps (2–200 km depth) + competition `cond_surf` / `depth_to_base_surf` (bands 17 and 15).

**Physical signature:** fault zones with fluid-filled damage show lateral conductance changes.

**Why it catches catalogue-missing faults:** a conductance discontinuity can mark a fault with no surface expression.

**Named non-fault mimics:** lithologic and clay-alteration conductors; regional conductance gradients.

**How it differs:** H-DEPTH×COND uses the same surface bands with a different combination; this uses MT depth ranges.

**Cost:** Medium.

**Data viability:** GDR INGENIOUS page links the USGS MT data release (DOI 10.5066/P9TWT2LU); not checked for coverage or download. Not viable without external access.

---

## Selection rationale

H-BLIND-CONDUIT is selected because: (1) it is the lowest-cost hypothesis that can be implemented on the known competition grid without external downloads; (2) it targets blind faults — the population most likely missing from the catalogue; (3) it is a genuinely different method family from all nine focus sites (which use dotted ridges, catalogue-distance, Poisson scatter, PINN, or stepover geometries); (4) it can be format-validated immediately.

**Next step:** build the H-BLIND-CONDUIT format-valid GeoTIFF, validate it (CRS/shape/transform/[0,1]/NaN), then measure uniqueness against the focus registry before any submission decision.