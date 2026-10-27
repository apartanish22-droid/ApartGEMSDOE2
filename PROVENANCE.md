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
`scripts/audit_uniqueness.py`, `scripts/restore_data.py`. If a vendored tool is found wrong,
fix it here once and report it — do not keep a private fork elsewhere.
