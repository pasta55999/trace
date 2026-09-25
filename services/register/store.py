from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from services.common import RUNTIME

from .models import (
    Borrower,
    Case,
    CollateralLink,
    Document,
    Facility,
    InsuranceArrangement,
    Investigation,
    Location,
    PendingLink,
    PhysicalAsset,
)


class _State(BaseModel):
    borrowers: dict[str, Borrower] = Field(default_factory=dict)
    facilities: dict[str, Facility] = Field(default_factory=dict)
    assets: dict[str, PhysicalAsset] = Field(default_factory=dict)
    links: list[CollateralLink] = Field(default_factory=list)
    insurance: dict[str, InsuranceArrangement] = Field(default_factory=dict)
    locations: dict[str, Location] = Field(default_factory=dict)
    pending: dict[str, PendingLink] = Field(default_factory=dict)
    documents: dict[str, Document] = Field(default_factory=dict)
    cases: dict[str, Case] = Field(default_factory=dict)
    investigations: dict[str, Investigation] = Field(default_factory=dict)
    runs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    audit: list[dict[str, Any]] = Field(default_factory=list)


class Store:
    """Tenant-scoped register. One Store per tenant; the prototype uses one tenant."""

    def __init__(self, tenant_id: str = "demo-bank", path: Path | None = None):
        self.tenant_id = tenant_id
        self.path = path or RUNTIME / f"{tenant_id}.json"
        self.s = _State()

    # --- persistence
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.s.model_dump_json(indent=1), encoding="utf-8")

    def load(self) -> "Store":
        if self.path.exists():
            self.s = _State.model_validate_json(self.path.read_text(encoding="utf-8"))
        return self

    def reset(self) -> None:
        self.s = _State()
        if self.path.exists():
            self.path.unlink()

    # --- audit (append-only, hash-chained in production)
    def audit(self, actor: str, action: str, **detail: Any) -> None:
        from services.common import now_iso

        self.s.audit.append({"at": now_iso(), "actor": actor, "action": action, **detail})

    # --- convenience queries
    def facilities_for_asset(self, asset_id: str) -> list[Facility]:
        return [self.s.facilities[l.facility_id] for l in self.s.links if l.asset_id == asset_id]

    def assets_for_facility(self, facility_id: str) -> list[PhysicalAsset]:
        return [self.s.assets[l.asset_id] for l in self.s.links if l.facility_id == facility_id]

    def borrower_for_asset(self, asset_id: str) -> Borrower | None:
        facs = self.facilities_for_asset(asset_id)
        return self.s.borrowers[facs[0].borrower_id] if facs else None

    def allocation(self, facility_id: str, asset_id: str) -> float:
        for l in self.s.links:
            if l.facility_id == facility_id and l.asset_id == asset_id:
                return l.allocation_share
        return 0.0

    def location_of(self, asset_id: str) -> Location | None:
        a = self.s.assets.get(asset_id)
        return self.s.locations.get(a.location_id) if a and a.location_id else None

    def insurance_of(self, asset_id: str) -> InsuranceArrangement | None:
        return next((i for i in self.s.insurance.values() if i.asset_id == asset_id), None)

    def open_questions(self) -> list[PendingLink]:
        return [p for p in self.s.pending.values() if p.status == "open"]

    def coverage(self) -> dict[str, Any]:
        """Transparent coverage measures - never a single blended readiness score."""
        assets = list(self.s.assets.values())
        located = [a for a in assets if (loc := self.location_of(a.id)) and loc.precision in ("footprint", "parcel")]
        docs = list(self.s.documents.values())
        return {
            "assets_total": len(assets),
            "assets_location_confirmed": len(located),
            "assets_unresolved": len([a for a in assets if not (loc := self.location_of(a.id)) or loc.precision == "unresolved"]),
            "assets_district_only": len([a for a in assets if (loc := self.location_of(a.id)) and loc.precision == "district"]),
            "documents_total": len(docs),
            "documents_with_firewall_flags": len([d for d in docs if d.firewall_flags]),
            "open_questions": len(self.open_questions()),
            "cases_open": len([c for c in self.s.cases.values() if c.status != "decided"]),
        }

    def dump(self) -> dict[str, Any]:
        return json.loads(self.s.model_dump_json())
