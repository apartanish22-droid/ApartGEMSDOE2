"""Verification of official sources, data provenance, and score ledger integrity."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class OfficialSource:
    source_id: str
    title: str
    organization: str
    url: str
    verified_date: str
    description: str
    document_doi: Optional[str] = None


OFFICIAL_SOURCES: List[OfficialSource] = [
    OfficialSource(
        source_id="NLR-GEMS-RULES",
        title="DOE GEMS Prize Official Rules (September 2026)",
        organization="National Laboratory of the Rockies (NLR) / US DOE Geothermal Technologies Office",
        url="https://docs.nlr.gov/docs/fy26osti/96647.pdf",
        verified_date="2026-10-04",
        description="Official competition rules document outlining two prize rounds, 3 weekly submissions limit, DTI evaluation metric, and data permissions.",
    ),
    OfficialSource(
        source_id="DRIVENDATA-OVERVIEW",
        title="DrivenData DOE GEMS Prize Problem Description",
        organization="DrivenData / US DOE",
        url="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
        verified_date="2026-10-04",
        description="Problem overview, metric formulation (R=300m, alpha=0.2, beta=0.8), GeoTIFF submission schema, and submission guidelines.",
    ),
    OfficialSource(
        source_id="DRIVENDATA-LEADERBOARD",
        title="DrivenData DOE GEMS Prize Leaderboard",
        organization="DrivenData",
        url="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
        verified_date="2026-10-04",
        description="Public competition leaderboard displaying current top score of 0.3195 (DARD) and benchmark clusters.",
    ),
    OfficialSource(
        source_id="USGS-GEODAWN",
        title="Earth MRI / GeoDAWN Airborne Magnetic and Radiometric Survey (NV / CA)",
        organization="US Geological Survey",
        url="https://doi.org/10.5066/P93LGLVQ",
        verified_date="2026-10-04",
        description="High-resolution airborne geophysical survey covering West-Central Nevada and Eastern California geothermal corridors.",
        document_doi="10.5066/P93LGLVQ",
    ),
    OfficialSource(
        source_id="GDR-INGENIOUS",
        title="INGENIOUS Project Great Basin Regional Geothermal Dataset Compilation",
        organization="Geothermal Data Repository (GDR) / DOE",
        url="https://gdr.openei.org/submissions/1391",
        verified_date="2026-10-04",
        description="Compilation of geothermal play fairway data, 2m shallow temperature probes, Quaternary faults, volcanic vents, and hydrothermal springs.",
        document_doi="10.15121/1881483",
    ),
    OfficialSource(
        source_id="USGS-SGMC",
        title="USGS State Geologic Map Compilation (SGMC) Fault Network",
        organization="US Geological Survey",
        url="https://mrdata.usgs.gov/geology/state/",
        verified_date="2026-10-04",
        description="Digital statewide geologic map compilation providing independent mapping of Cenozoic and Quaternary structural contacts.",
    ),
]


def export_sources_json(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sources": [asdict(s) for s in OFFICIAL_SOURCES],
        "count": len(OFFICIAL_SOURCES),
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
