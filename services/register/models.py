from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from services.common import PrecisionClass, now_iso


class Borrower(BaseModel):
    id: str
    name_en: str
    name_ar: str
    sector: str


class Facility(BaseModel):
    """A loan / financing facility."""

    id: str
    borrower_id: str
    outstanding_aed: float
    maturity_year: int


class CollateralLink(BaseModel):
    """Many-to-many edge with an allocation rule to prevent double counting."""

    facility_id: str
    asset_id: str
    allocation_share: float = 1.0
    rule: str = "pro-rata by outstanding across facilities secured by the asset"


class PhysicalAsset(BaseModel):
    id: str
    description: str
    asset_type: Literal["industrial_building", "warehouse", "distribution_centre", "cold_store"] = "industrial_building"
    recorded_address: str
    replacement_value_aed: float | None = None
    equipment_value_aed: float | None = None
    stock_value_aed: float | None = None
    market_value_aed: float | None = None
    # attribute -> value ("unknown" allowed and meaningful)
    attributes: dict[str, str] = Field(default_factory=dict)
    attribute_sources: dict[str, str] = Field(default_factory=dict)
    location_id: str | None = None
    district_id: str | None = None


class InsuranceArrangement(BaseModel):
    id: str
    asset_id: str
    sum_insured_aed: float | None = None
    flood_deductible_aed: float | None = None
    flood_covered: bool | None = None  # None = unknown
    bi_indemnity_days: int | None = None
    source_doc: str | None = None


class Location(BaseModel):
    id: str
    asset_id: str
    lon: float | None
    lat: float | None
    footprint: list[list[float]] | None = None
    precision: PrecisionClass
    confidence: float
    source: str
    matched_feature_id: str | None = None
    district_id: str | None = None
    resolved_at: str = Field(default_factory=now_iso)
    note: str = ""


class PendingLink(BaseModel):
    id: str
    asset_id: str
    kind: str  # "location", "entity", or the name of the missing attribute
    question_en: str
    question_ar: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    status: Literal["open", "answered", "dismissed"] = "open"
    answer: str | None = None
    created_by: str = "agent:evidence_gap"
    created_at: str = Field(default_factory=now_iso)


class ExtractedField(BaseModel):
    doc_id: str
    page: int
    line_no: int
    field: str
    value: Any
    raw: str
    lang: str
    confidence: float
    flagged_instruction: bool = False

    @property
    def ref(self) -> str:
        return f"doc://{self.doc_id}#p{self.page}:l{self.line_no}:{self.field}"


class Document(BaseModel):
    id: str
    type: str
    language: str
    related_collateral: str | None
    pages: list[dict[str, Any]]
    fields: list[ExtractedField] = Field(default_factory=list)
    firewall_flags: list[str] = Field(default_factory=list)


class Case(BaseModel):
    id: str
    title: str
    owner: str
    status: Literal["open", "in_review", "decided"] = "open"
    evidence_request: list[str] = Field(default_factory=list)
    deadline: str | None = None
    decision: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)
    linked_results: list[str] = Field(default_factory=list)


class Investigation(BaseModel):
    id: str
    tenant_id: str = "demo-bank"
    state: Literal["uploaded", "extracted", "linked", "located", "assessed", "aggregated", "reviewed", "reported"] = "uploaded"
    history: list[dict[str, Any]] = Field(default_factory=list)
    last_run_id: str | None = None
    previous_run_id: str | None = None
