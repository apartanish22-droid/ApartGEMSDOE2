# Repo review — 2026-10-28 (solo session, no slot used)

**Decision: NO FILE IS APPROVED FOR SUBMISSION.** This session could not generate a new,
data-driven submission and did not invent one. Every number below is labelled with its
evidence class.

Evidence labels used: `TECH-CHECK` (automated format check by this session),
`REPO-CLAIM` (stated in an existing repo file, not re-verified here),
`UNVERIFIED-EXTERNAL` (external page that this sandbox could not reach),
`HOLDOUT-DTI` / `ORGANIZER-CONFIRMED` (not available for any file in this session).

## 1. Hard blockers (measured this session)

Measured with `curl` from the sandbox on 2026-10-28:

| Source | Needed for | HTTP result | Source link |
|---|---|---|---|
| DrivenData data tab | `training_features.tif`, `labels.tif`, `sample_submission.tif` | `000` (unreachable) | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ |
| DrivenData leaderboard | Verify the `0.4544` leader claim | `000` (unreachable) | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| Dropbox mirrors (example_submission.tif, existing_faults.tif, features) | Competition data fallback | `000` (unreachable) | https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif |
| GDR (DOE data package) | Public data alternative | `000` (unreachable) | https://gdr.openei.org/submissions/1391 |
| NLR submission guide PDF | Submission rules | `000` (unreachable) | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| GitHub, PyPI | Code and dependencies | `200` | https://github.com , https://pypi.org |
| Other sites' GitHub Pages (e.g. GEMSDOE32) | Verify the 9 focus-site receipts | `000` (unreachable) | https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html |

Consequences:

- `data/` contains no competition rasters (`ls data/` shows only manifests and hashes).
  `.cache/` does not exist, although `data/restore_receipt.json` describes it.
- Without the template, no candidate can be checked against the official footprint.
  No holdout DTI can be computed, so no score (even an estimate) can be attached to any file.
- The "0.4544 leader" figure is `REPO-CLAIM` only. It traces to
  [`docs/data/source_feed.json`](../data/source_feed.json) and is not re-verified here.
  The user-supplied 0.4413 and 0.3195 figures are also unverified.
- The nine focus-site receipts (GEMSDOE24/25/27/28/30/31/32/33/36) were not re-checked.
  Their pages in `docs/forensics/` and `docs/sites/` are `REPO-CLAIM`.

## 2. What was verified locally

- Dependencies installed from `requirements.txt` (pinned numpy 2.4.6, rasterio 1.4.4).
- Test suite: **132 passed, 8 skipped** after the fix below (was 131 passed).
- Canonical grid, from `src/gems32/grid.py` and `data/prepared_manifest.json`:
  EPSG:32611, width 3292, height 3730, 100 m, origin (243350, 4508550).
  Re-derived in the audit script.
- Full file audit: [`evidence/download_audit_20261028.json`](../../evidence/download_audit_20261028.json),
  produced by the new [`scripts/audit_downloads.py`](../../scripts/audit_downloads.py).

### File audit (TECH-CHECK only; not a scientific verdict)

| File | Grid | NaN px | Non-zero px | Technical result | sha256 (first 16) |
|---|---|---|---|---|---|
| `docs/downloads/…-udsr-exp3-…-zeros.tif` | match | 0 | 26,173 | PASS | `1f2c28e9eba172fe` |
| `docs/downloads/…-ap1-dilatcond-…-zeros.tif` | match | 0 | 37,654 | PASS | `973e1615098e5636` |
| `docs/downloads/…-ap2-oofctrl-…-zeros.tif` | match | 0 | 44,090 | PASS | `edf60fd492cc18b8` |
| `docs/downloads/…-trace-exp-2-…-zeros.tif` | match | 0 | 22,438 | PASS | `32716d4851e9de2d` |
| `docs/downloads/gems-h2-fractal-faultzone-…tif` | match | 0 | 61,396 | PASS (format only) | `5a6da02c45e8cc96` |
| `docs/downloads/…-ap1-dilatcond-…-nan.tif` | match | 7,111,787 | 37,654 | **FAIL** (NaN outside footprint) | `c12f17f3e7dac142` |
| `docs/downloads/…-ap2-oofctrl-…-nan.tif` | match | 7,111,787 | 44,090 | **FAIL** (NaN) | `f9206a4aab5f7cdec` |
| `docs/downloads/…-trace-exp-2-…-nan.tif` | match | 7,111,787 | 22,438 | **FAIL** (NaN) | `252d12f5d2c1f521` |
| `assets/submission.tif` | **mismatch** (1200×1200, origin 500000/4500000) | 0 | 1,324,262 | **FAIL** (grid) | `250d2a554fd0c54c` |
| `assets/gems-h1-…tif` | **mismatch** (same as above) | 0 | 1,324,262 | **FAIL** (grid) | `250d2a554fd0c54c` |

Interpretation:

- The `-nan` downloads fail the whole-array range rule. This is the most likely cause of the
  user's portal error "Predicted values must be in range [0, 1]". The `-zeros` variants avoid it.
  This is `TECH-CHECK` reasoning, not a portal receipt. Portal behaviour is not confirmed.
- A `TECH-PASS` only means the file is well-formed. It is not a score, and does not show the
  content is useful or unique. The repo's own run cards mark the UDSR, AP1, AP2 and TRACE
  zero-variants as `negative` or `do not submit`.
- `gems-h2-fractal-faultzone-…tif` passes format checks but was generated from **seeded
  pseudo-features** (`docs/data/run_card_h2.json`, `holdout_dti: null`). It must not be
  submitted, despite its files still saying "PASSED" (see §3).

## 3. Irregularities flagged for review

1. **Wrong-grid files named like submissions.** `assets/submission.tif` and
   `assets/gems-h1-…tif` are 1200×1200 on origin (500000, 4500000). They do not match the
   canonical grid, and are byte-identical (same sha256). A user downloading `submission.tif`
   would be rejected. Recommend deletion or quarantine in a follow-up; **not removed here**
   pending owner review.
2. **Stale PASS claim.** `assets/SUBMISSION_STATUS.txt` contains an older block that reads
   "VALIDATION: ✅ PASSED / Portal-safe: YES" for the H2 file, with a correction banner above
   it. It also names branch `arena/17f40661-apartgemsdoe2`, which is not this session's branch
   (`arena/f73c8f6a-apartgemsdoe2`). Both are flagged; the file is not edited here.
3. **Validator crash (fixed).** `src/gemsdoe32/submission.py` raised `IndexError` on any
   shape-mismatched submission instead of returning FAILED. This reproduced on
   `assets/submission.tif`. Fixed by adding a shape guard; regression test
   `tests/test_submission.py::test_shape_mismatch_fails_cleanly_instead_of_raising`.
   Shared-tool rule: this is the single template fix, reported here.
4. **Footprint not available.** `scripts/check_submission.py` needs
   `data/sample_submission.tif`, which is absent. A proxy template built from `grid.py`
   (all-NaN) makes the `in_footprint_range` check fail with an empty footprint. The
   validator is therefore **not fully runnable** in this checkout. Recorded as a limitation.
5. **Conflict on NaN outside footprint.** `src/gems32/grid.py` says NaN outside the footprint
   "is legal in a legal submission". The user's portal error and the repo's
   `--strict-finite` rule say the opposite for whole-array checks. This is unresolved until
   the organizer's rule text or a receipt is available. Flag for owner review.
6. **Unverifiable leaderboard values.** 0.4544 (repo), 0.4413 and 0.3195 (user prompt) are
   inconsistent and unverified in this session. The README calls 0.4544 the "organizer-
   published" value; it is `REPO-CLAIM`.
7. **External citations not re-checked.** `docs/research/why-02778-and-how-to-beat-it-20261028.md`
   answers "why 0.2778" with external citations. Those sources were not reachable here (§1),
   so every such claim remains `REPO-CLAIM`.

## 4. The question "can we beat 0.2778?" — status

No new candidate was generated and tested, because the holdout requires competition features,
labels and the template. That data is unreachable (§1). The only candidates in the repo that
pass format checks have no holdout receipt, or are already marked negative. So the honest
answer is: **unknown in this session**. Any projection would be a made-up number.

## 5. Next steps (in order, no manual input needed once data is present)

1. Place authenticated competition files under `data/` (manual download; the sandbox cannot do it).
   Then run `scripts/prepare_data.py`, and `scripts/check_submission.py` against the real
   `sample_submission.tif`.
2. Re-run `scripts/audit_downloads.py` and `pytest`. Record the sha256 of any new candidate.
3. Holdout-evaluate one new candidate with `HOLDOUT-DTI` labels (evaluator version, withheld
   positives, 95% CI). Leakage canary first (single-feature AUC > 0.90 means leakage).
4. Only a candidate that beats the current holdout best AND clears the uniqueness gate may
   take a weekly slot. The selector step is separate.
5. Resolve irregularities 1, 2 and 5 above (owner decision).

## 6. Run card (JSON)

```json
{
  "session": "2026-10-28 repo review (solo)",
  "branch": "arena/f73c8f6a-apartgemsdoe2",
  "hypothesis": "Repo state can be verified and hardened without competition data; no new submission is justified.",
  "mechanism": "Local format audit against canonical grid + validator crash fix; no science run.",
  "non_fault_mimic": "Not applicable: no scientific output produced this session.",
  "holdout_dti": null,
  "holdout_ci95": null,
  "organizer_confirmed_score": null,
  "correlation_overlap_vs_registry": "not computed (registry rasters absent)",
  "raster_sha256_downloads": {
    "udsr_exp3_zeros": "1f2c28e9eba172fe6a4da138b98afa28a43420549e174c801a02af658ef180b9",
    "ap1_zeros": "973e1615098e5636e9348a3ae1e12d9de392fda2b14f0313c81554cc26274d28",
    "ap2_zeros": "edf60fd492cc18b835abee8cb7479825f47cd1077aa8609de37f1d9de5ccf50e",
    "trace_exp2_zeros": "32716d4851e9de2df406eeb2386c8ddcf9aa970c985643c7e5484973dd023b4f",
    "h2_seeded_demo": "5a6da02c45e8cc96399763c1eba4f95bddd781f0ff2223c9d9a7f1dc3e90a801"
  },
  "validator_output": {
    "tests": "132 passed, 8 skipped",
    "format_audit": "evidence/download_audit_20261028.json",
    "no_nan_in_footprint": "NOT VERIFIED (footprint absent)",
    "values_in_0_1": "TECH-PASS for -zeros files, FAIL for -nan files",
    "crs_shape_transform": "TECH-PASS for downloads on canonical grid; FAIL for assets/submission.tif and gems-h1"
  },
  "submission_name": "none",
  "submission_note": "none (no file approved)",
  "verdict": "negative"
}
```
