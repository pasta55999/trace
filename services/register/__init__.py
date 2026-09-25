"""Asset & relationship register.

Prototype storage is an in-process store persisted as JSON; the production design targets
PostgreSQL + PostGIS with schema-per-tenant. The entity model is the same.
"""
from .models import (
    Borrower,
    Case,
    CollateralLink,
    Document,
    ExtractedField,
    Facility,
    InsuranceArrangement,
    Investigation,
    Location,
    PendingLink,
    PhysicalAsset,
)
from .store import Store

__all__ = [
    "Borrower", "Case", "CollateralLink", "Document", "ExtractedField", "Facility",
    "InsuranceArrangement", "Investigation", "Location", "PendingLink", "PhysicalAsset", "Store",
]
