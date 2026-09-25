"""Ingestion & extraction: portfolio spreadsheets and bilingual documents.

Documents are UNTRUSTED INPUT. A content firewall flags instruction-like text before any field
is extracted, and flagged lines never become fields.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from services.common import SYNTHETIC, has_arabic, new_id, normalise_digits, parse_aed, parse_metres
from services.register import (
    Borrower,
    CollateralLink,
    Document,
    ExtractedField,
    Facility,
    InsuranceArrangement,
    PhysicalAsset,
    Store,
)

INSTRUCTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard .*instructions",
    r"(record|mark|set|treat) .*(risk|exposure).* as (low|zero|none|minimal)",
    r"تجاهل .*التعليمات",
    r"اعتبر .*(المخاطر|التعرض).* (منخفض|معدوم)",
    r"you are now",
    r"system prompt",
]
_INSTRUCTION_RE = re.compile("|".join(INSTRUCTION_PATTERNS), re.IGNORECASE)

ASSET_TYPE_BY_KEYWORD = [
    ("cold store", "cold_store"), ("warehouse", "warehouse"), ("مستودع", "warehouse"),
    ("distribution", "distribution_centre"), ("توزيع", "distribution_centre"),
]


def content_firewall(line: str) -> bool:
    """True if the line looks like an instruction to the system rather than document content."""
    return bool(_INSTRUCTION_RE.search(line))


# --- portfolio -------------------------------------------------------------------------------

def load_portfolio(store: Store, path: Path = SYNTHETIC / "portfolio.csv") -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    borrowers_by_name: dict[str, Borrower] = {}
    for r in rows:
        key = r["borrower_name_en"].strip().lower()
        if key not in borrowers_by_name:
            b = Borrower(id=new_id("B"), name_en=r["borrower_name_en"], name_ar=r["borrower_name_ar"], sector=r["sector"])
            borrowers_by_name[key] = b
            store.s.borrowers[b.id] = b
        b = borrowers_by_name[key]
        fid = r["facility_id"]
        if fid not in store.s.facilities:
            store.s.facilities[fid] = Facility(id=fid, borrower_id=b.id, outstanding_aed=float(r["outstanding_aed"]), maturity_year=int(r["maturity_year"]))
        aid = r["collateral_ref"]
        desc = r["collateral_description"]
        atype = next((t for kw, t in ASSET_TYPE_BY_KEYWORD if kw in desc.lower()), "industrial_building")
        if aid not in store.s.assets:
            store.s.assets[aid] = PhysicalAsset(id=aid, description=desc, asset_type=atype, recorded_address=r["recorded_address"])
        store.s.links.append(CollateralLink(facility_id=fid, asset_id=aid))
    _apply_allocation_rules(store)
    store.audit("service:ingestion", "portfolio_loaded", rows=len(rows), file=str(path.name))
    return {"borrowers": len(store.s.borrowers), "facilities": len(store.s.facilities), "assets": len(store.s.assets)}


def _apply_allocation_rules(store: Store) -> None:
    """Facility exposure is split across its securing assets; equal split until values are known."""
    by_fac: dict[str, list[CollateralLink]] = {}
    for l in store.s.links:
        by_fac.setdefault(l.facility_id, []).append(l)
    for links in by_fac.values():
        vals = [store.s.assets[l.asset_id].replacement_value_aed for l in links]
        if all(vals) and len(links) > 1:
            total = sum(vals)  # type: ignore[arg-type]
            for l, v in zip(links, vals):
                l.allocation_share, l.rule = round(v / total, 4), "pro-rata by replacement value across assets securing the facility"  # type: ignore[operator]
        else:
            for l in links:
                l.allocation_share = round(1 / len(links), 4)
                l.rule = "equal split across assets securing the facility (values pending)" if len(links) > 1 else "sole collateral"


# --- documents -------------------------------------------------------------------------------

FIELD_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("replacement_value_building", re.compile(r"replacement value \(building\)|قيمة الاستبدال \(المبنى\)", re.I), "aed"),
    ("replacement_value_equipment", re.compile(r"replacement value \(plant|قيمة الاستبدال \(المعدات", re.I), "aed"),
    ("stock_value", re.compile(r"stock at risk|قيمة المخزون", re.I), "aed"),
    ("market_value", re.compile(r"market value|القيمة السوقية", re.I), "aed"),
    ("ground_floor_elevation_m", re.compile(r"ground floor elevation|منسوب الطابق الأرضي", re.I), "metres"),
    ("basement", re.compile(r"^basement|الطابق السفلي", re.I), "yesno"),
    ("switchboard_location", re.compile(r"switchboard|لوحات التوزيع", re.I), "switchboard"),
    ("sum_insured", re.compile(r"sum insured|مبلغ التأمين", re.I), "aed"),
    ("flood_deductible", re.compile(r"flood deductible|تحمل الفيضان", re.I), "aed"),
    ("flood_covered", re.compile(r"flood cover|تغطية الفيضان", re.I), "covered"),
    ("bi_indemnity_days", re.compile(r"business interruption|توقف الأعمال", re.I), "days"),
    ("plot_ref", re.compile(r"property:|العقار:", re.I), "plot"),
    ("valuation_date", re.compile(r"valuation date|تاريخ التقييم", re.I), "date"),
]


def _parse(kind: str, line: str) -> tuple[Any, float]:
    t = normalise_digits(line)
    if kind == "aed":
        v = parse_aed(t)
        return v, 0.95 if v is not None else 0.0
    if kind == "metres":
        v = parse_metres(t)
        return v, 0.9 if v is not None else 0.0
    if kind == "yesno":
        low = t.lower()
        if re.search(r"\byes\b|نعم|يوجد(?! لا)", low) and "لا يوجد" not in low and re.search(r"\bno\b", low) is None:
            return "true", 0.9
        if re.search(r"\bno\b|لا يوجد", low):
            return "false", 0.9
        return None, 0.0
    if kind == "switchboard":
        low = t.lower()
        if "basement" in low or "السفلي" in low:
            return "basement", 0.85
        if "raised" in low or "plinth" in low or "مرتفع" in low:
            return "raised", 0.85
        if "ground" in low or "الأرضي" in low:
            return "ground_floor", 0.85
        return None, 0.0
    if kind == "covered":
        low = t.lower()
        if "excluded" in low or "مستثنا" in low:
            return "false", 0.9
        if "included" in low or "مشمول" in low:
            return "true", 0.9
        return None, 0.0
    if kind == "days":
        m = re.search(r"(\d+)\s*(days|يوم)", t, re.I)
        return (int(m.group(1)), 0.85) if m else (None, 0.0)
    if kind == "plot":
        m = re.search(r"plot\s+([A-Z]{2,3}\d?-\d{2,4})|قطعة رقم\s*(\d{2,4})", t, re.I)
        if m:
            return (m.group(1) or f"AQ3-{m.group(2)}"), 0.8 if m.group(1) else 0.65
        return None, 0.0
    if kind == "date":
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", t)
        return (f"{m.group(3)}-{m.group(2)}-{m.group(1)}", 0.9) if m else (None, 0.0)
    return None, 0.0


def extract_document(raw: dict[str, Any]) -> Document:
    doc = Document(id=raw["doc_id"], type=raw["type_hint"], language=raw["language"], related_collateral=raw.get("related_collateral"), pages=raw["pages"])
    for page in raw["pages"]:
        for i, line in enumerate(page["lines"]):
            lang = "ar" if has_arabic(line) and not re.search(r"[A-Za-z]{4,}", line) else ("mixed" if has_arabic(line) else "en")
            if content_firewall(line):
                doc.firewall_flags.append(f"p{page['page']}:l{i}: instruction-like content quarantined")
                doc.fields.append(ExtractedField(doc_id=doc.id, page=page["page"], line_no=i, field="_quarantined", value=None, raw=line, lang=lang, confidence=1.0, flagged_instruction=True))
                continue
            for field, pat, kind in FIELD_RULES:
                if pat.search(line):
                    value, conf = _parse(kind, line)
                    if value is not None:
                        doc.fields.append(ExtractedField(doc_id=doc.id, page=page["page"], line_no=i, field=field, value=value, raw=line, lang=lang, confidence=conf))
                    break
    return doc


def load_documents(store: Store, path: Path = SYNTHETIC / "documents.json") -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    for d in raw["documents"]:
        doc = extract_document(d)
        store.s.documents[doc.id] = doc
        _apply_fields(store, doc)
    _apply_allocation_rules(store)
    store.audit("service:ingestion", "documents_extracted", count=len(raw["documents"]))
    return {"documents": len(store.s.documents), "fields": sum(len(d.fields) for d in store.s.documents.values()), "firewall_flags": sum(len(d.firewall_flags) for d in store.s.documents.values())}


def _apply_fields(store: Store, doc: Document) -> None:
    aid = doc.related_collateral
    if not aid or aid not in store.s.assets:
        return
    asset = store.s.assets[aid]
    ins = store.insurance_of(aid)
    for f in doc.fields:
        if f.flagged_instruction:
            continue
        if f.field == "replacement_value_building":
            asset.replacement_value_aed = f.value
        elif f.field == "replacement_value_equipment":
            asset.equipment_value_aed = f.value
        elif f.field == "stock_value":
            asset.stock_value_aed = f.value
        elif f.field == "market_value":
            asset.market_value_aed = f.value
        elif f.field in ("ground_floor_elevation_m", "basement", "switchboard_location", "plot_ref"):
            asset.attributes[f.field] = str(f.value)
            asset.attribute_sources[f.field] = f.ref
        elif f.field in ("sum_insured", "flood_deductible", "flood_covered", "bi_indemnity_days"):
            if ins is None:
                ins = InsuranceArrangement(id=new_id("INS"), asset_id=aid, source_doc=doc.id)
                store.s.insurance[ins.id] = ins
            if f.field == "sum_insured":
                ins.sum_insured_aed = f.value
            elif f.field == "flood_deductible":
                ins.flood_deductible_aed = f.value
            elif f.field == "flood_covered":
                ins.flood_covered = f.value == "true"
            elif f.field == "bi_indemnity_days":
                ins.bi_indemnity_days = f.value
    for key in ("basement", "switchboard_location"):
        asset.attributes.setdefault(key, "unknown")
