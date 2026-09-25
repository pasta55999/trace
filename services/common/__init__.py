"""Shared primitives: paths, Unknown, provenance envelope, Arabic text utilities."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC = ROOT / "data" / "synthetic"
RUNTIME = ROOT / "data" / "runtime"

PrecisionClass = Literal["footprint", "parcel", "street", "district", "unresolved"]
Lang = Literal["en", "ar"]


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Unknown(BaseModel):
    """An explicit unknown. Rendered as 'unknown' with a reason - never as zero or 'low'."""

    kind: Literal["unknown"] = "unknown"
    reason: str
    reason_ar: str = ""

    def __bool__(self) -> bool:  # an Unknown is never truthy-numeric
        return False


class Range(BaseModel):
    """A bounded estimate when one attribute is missing; carries the driver of the spread."""

    low: float
    high: float
    driver: str

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


class Provenance(BaseModel):
    dataset_versions: dict[str, str] = Field(default_factory=dict)
    engine_version: str = ""
    scenario: dict[str, Any] = Field(default_factory=dict)
    spatial_precision: PrecisionClass | None = None
    assumptions: list[str] = Field(default_factory=list)
    source_records: list[str] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    approval_status: Literal["draft", "reviewed", "approved"] = "draft"
    computed_at: str = Field(default_factory=now_iso)


# --- Arabic text utilities -------------------------------------------------------------------

_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_ARABIC_SEPARATORS = str.maketrans({"٬": ",", "٫": ".", "،": ","})
_TASHKEEL = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalise_digits(text: str) -> str:
    """Map Arabic-Indic and Extended Arabic-Indic digits and separators to ASCII."""
    return text.translate(_ARABIC_INDIC).translate(_ARABIC_SEPARATORS)


def normalise_arabic(text: str) -> str:
    """Light normalisation for matching: strip diacritics, unify alef/yaa/taa-marbuta, drop legal suffixes."""
    t = _TASHKEEL.sub("", text)
    t = re.sub("[إأآا]", "ا", t)
    t = t.replace("ى", "ي").replace("ة", "ه").replace("ـ", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def parse_aed(text: str) -> float | None:
    """Extract an AED amount from a bilingual line, e.g. 'AED 25,000,000' or '١٤٬٠٠٠٬٠٠٠ درهم'."""
    t = normalise_digits(text)
    m = re.search(r"(?:AED|درهم)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:AED|درهم)?", t)
    if not m or not re.search(r"AED|درهم", t):
        return None
    return float(m.group(1).replace(",", ""))


def parse_metres(text: str) -> float | None:
    t = normalise_digits(text)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:m\b|م\b)", t)
    return float(m.group(1)) if m else None
