> **2026-10-27 reconciliation:** These are archived GEMSDOE32 snapshots from a parallel session, not the mandated GEMSDOE24 shared-tool pin or evidence of an assigned lane. Do not run the stopped AP-1 entry points or treat a format check as a slot selector. Fix shared defects in the canonical upstream repository; do not maintain a private fork. See [the current review](docs/EXECUTIVE_REVIEW.md) and [upstream issue](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/74).

# Provenance — vendored canonical tools (reuse, don't rebuild)

Vendored verbatim on 2026-10-27 from `buffedlizard55-lab/GEMSDOE32` (cloned at `main`,
2026-10-27; file SHA-256 checked at copy time, e.g. `src/gems32/metric.py`
`382de3eb6d77d549e01bafa718fd01f5a7132263be0b6925dbd5a40a24025289`):

| This repo | Upstream |
|---|---|
| `src/gems32/metric.py`, `holdout.py`, `emission.py`, `submission.py`, `grid.py`, `__init__.py` | `GEMSDOE32/src/gems32/*` |
| `src/gemsdoe32/submission.py` (writer/validator) | `GEMSDOE32/src/gemsdoe32/submission.py` |
| `scripts/evaluate_holdout.py`, `scripts/check_submission.py` | `GEMSDOE32/scripts/*` (path shim only if noted in-file) |
| `tests/test_metric.py` | `GEMSDOE32/tests/test_metric.py` |

Competition rasters are **owner-supplied mirrors** of DrivenData files (login-walled at
https://www.drivendata.org/competitions/306/competition-doe-gems/data/), restored via
`scripts/restore_data.py` and SHA-256-verified against the pinned manifest in
`registry/data_manifest.json` (copied from GEMSDOE32 `registry/data_manifest.json`, 2026-10-27).
They are integrity-pinned, **not organizer-authenticated**. Official problem/metric text:
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (fetched 2026-10-27).
Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution

New code in this repo (this session's lane): `src/apart/*`, `scripts/build_candidate.py`,
`scripts/audit_uniqueness.py`, `scripts/restore_data.py`. If a shared tool is found wrong, report and fix it in the canonical upstream repository; these snapshots are retained only to explain the archived results.
