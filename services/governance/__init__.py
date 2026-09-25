"""Governance registry: model/dataset versions, regulatory mapping, and agent proposals.

Human-owned. Agents have read access and may only file proposals (Tier C changes).
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from services import hazard, vulnerability
from services.common import RUNTIME, new_id, now_iso
from services.fin_engine import ENGINE_VERSION

PROPOSALS = RUNTIME / "proposals.jsonl"

REGULATORY_MAPPING = {
    "jurisdiction": "UAE",
    "version": "2026-09-draft",
    "status": "requires current legal review - not a compliance determination",
    "items": [
        {"requirement": "CBUAE Climate-related Financial Risk Management Regulation - identification of physical risk drivers", "output": "asset-level hazard samples with provenance", "coverage": "partial (flood only, illustrative data)"},
        {"requirement": "CBUAE Principles - scenario analysis and stress testing", "output": "scenario runs with immutable definitions; concentration view", "coverage": "prototype"},
        {"requirement": "Data quality and traceability", "output": "document-level source references, coverage counters, audit log", "coverage": "prototype"},
    ],
}


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: new_id("PROP"))
    tier: str = "C"
    target: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    suggested_patch: str = ""
    proposed_by: str
    status: str = "awaiting_model_validator"
    created_at: str = Field(default_factory=now_iso)


def registry() -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "datasets": hazard.dataset_versions(),
        "hazard_catalog": {k: v.get("properties", {}) for k, v in hazard.catalog().items()},
        "damage_functions": {fid: {"version": f["version"], "validation_status": f["validation_status"]} for fid, f in vulnerability.registry()["functions"].items()},
        "regulatory_mapping": REGULATORY_MAPPING,
        "proposals": list_proposals(),
    }


def file_proposal(p: Proposal) -> Proposal:
    PROPOSALS.parent.mkdir(parents=True, exist_ok=True)
    with PROPOSALS.open("a", encoding="utf-8") as f:
        f.write(p.model_dump_json() + "\n")
    return p


def list_proposals() -> list[dict[str, Any]]:
    if not PROPOSALS.exists():
        return []
    return [json.loads(l) for l in PROPOSALS.read_text(encoding="utf-8").splitlines() if l.strip()]
