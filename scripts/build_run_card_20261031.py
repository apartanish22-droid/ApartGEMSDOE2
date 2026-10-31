#!/usr/bin/env python3
"""Write evidence/run_card_20261031.json: what was run on 31 Oct 2026, with input/output SHA-256s.

Hashes are computed from the files on disk, so the card cannot drift from the evidence it describes.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence/run_card_20261031.json"

INPUTS = [
    "registry/focus_registry_manifest.json",
    "registry/historical-pins.json",
    "data/shared_tool_hashes.txt",
]
OUTPUTS = [
    "evidence/nine_site_verification_20261031.json",
    "evidence/proxy_controls_20261031.json",
    "evidence/gates_s31_20261031.json",
    "evidence/verdict_table_20261031.json",
    "docs/verdict-20261031.html",
    "docs/submission-decision.html",
    "docs/index.html",
    "evidence/submission_decision_20261030.json",
]
SCRIPTS = [
    "scripts/verify_nine_sites_20261031.py",
    "scripts/proxy_controls_20261031.py",
    "scripts/build_verdict_20261031.py",
    "scripts/build_submission_decision.py",
    "scripts/build_site.py",
    "scripts/build_run_card_20261031.py",
]


def sha256(rel: str) -> dict:
    p = ROOT / rel
    if not p.exists():
        return {"path": rel, "present": False}
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"path": rel, "present": True, "sha256": h, "bytes": p.stat().st_size}


card = {
    "schema": "run-card-20261031-v1",
    "date_utc": "2026-10-31",
    "branch": "arena/ba20222e-apartgemsdoe2",
    "label_key": {
        "HOLDOUT-DTI": "scored on the repo's own withheld holdout or proxy, not the organizer target",
        "ORGANIZER-CONFIRMED": "value shown on the official DrivenData leaderboard (public board, read 31 Oct)",
        "OWNER-REPORTED": "value shown on a third-party owner page; not verified",
    },
    "experiments": [
        {"id": "E1", "name": "nine-site byte verification and 3-px overlap matrix",
         "script": "scripts/verify_nine_sites_20261031.py", "output": "evidence/nine_site_verification_20261031.json",
         "label": "byte-level facts (not scores)"},
        {"id": "E2", "name": "same-evaluator proxy controls on nine pinned files + two S31 files",
         "script": "scripts/proxy_controls_20261031.py", "output": "evidence/proxy_controls_20261031.json",
         "label": "HOLDOUT-DTI (proxy): SGMC-CAL-v3.0 calibrated; HIDE-RECOVER-v3.0 for the second column",
         "evaluators": {"sgmc": "GEMSDOE32-SGMC-CAL-v3.0", "hide_recover": "GEMSDOE32-HIDE-RECOVER-v3.0"},
         "truth_pixels_sgmc": 62703, "withheld_positives_hide_recover": 22232},
        {"id": "E3", "name": "full-registry literal gate on the two S31 files",
         "script": "scripts/gate_candidates.py (run with GEMS_DATA_DIR=.cache/gems_data)",
         "output": "evidence/gates_s31_20261031.json",
         "label": "rule check (G1 format, G3 uniqueness); not an organizer score"},
    ],
    "weekly_submission_slots_used": 0,
    "final_submission_used": False,
    "new_hypotheses_preregistered_this_session": 0,
    "candidate_tif_generated": False,
    "candidate_tif_reason": "no file clears the literal uniqueness rule (lattice 99.9% within 3 px)",
    "inputs": [sha256(p) for p in INPUTS],
    "scripts": [sha256(p) for p in SCRIPTS],
    "outputs": [sha256(p) for p in OUTPUTS],
    "limitations": [
        "Training rasters are third-party owner mirrors, SHA-256 pinned, not organizer-authenticated.",
        "Owner-reported scores (0.2449-0.2778) have no organizer receipt.",
        "Proxies are not the organizer target; the hide-and-recover proxy is anti-aligned for pruned files.",
        "Only nine focus files, the 13GEMSDOE lattice and two S31 files were overlap-checked; global uniqueness is not established.",
        "Full registry gate uses 511 focus rasters (two malformed or missing); the other listed repos were not fetched in this run.",
        "Portal behaviour on NaN vs zeros outside the footprint has not been tested from here.",
    ],
    "reproduce": [
        "scripts/restore_data.py --references-only --target-dir .cache/gems_data",
        "scripts/verify_nine_sites_20261031.py",
        "scripts/proxy_controls_20261031.py",
        "GEMS_DATA_DIR=.cache/gems_data scripts/gate_candidates.py S31_far65=.cache/nine/s31_far65.tif S31_midband=.cache/nine/s31_midband.tif --out evidence/gates_s31_20261031.json",
        "scripts/build_verdict_20261031.py",
        "scripts/build_run_card_20261031.py",
    ],
}
OUT.write_text(json.dumps(card, indent=2) + "\n")
print(f"wrote {OUT.relative_to(ROOT)}")
