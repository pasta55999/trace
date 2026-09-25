"""Location resolution over a bilingual gazetteer.

Returns ranked candidates with a precision class and confidence. Choosing and committing a
candidate is a separate step (done by the Location agent under its genome's thresholds) so
that the decision is auditable and evolvable while the geometry lookup stays deterministic.
"""
from __future__ import annotations

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from services.common import SYNTHETIC, PrecisionClass, has_arabic, new_id, normalise_arabic, normalise_digits
from services.register import Location, PhysicalAsset, Store

SITE_ASSET_TYPES = {"industrial_building", "warehouse", "distribution_centre", "cold_store"}


class Candidate(BaseModel):
    feature_id: str | None
    label: str
    precision: PrecisionClass
    confidence: float
    method: str
    lon: float | None = None
    lat: float | None = None
    footprint: list[list[float]] | None = None
    district_id: str | None = None
    kind: str | None = None
    warning: str | None = None


@lru_cache(maxsize=1)
def gazetteer(path: str = str(SYNTHETIC / "gazetteer.json")) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _centroid(fp: list[list[float]]) -> tuple[float, float]:
    return sum(p[0] for p in fp) / len(fp), sum(p[1] for p in fp) / len(fp)


def _norm(s: str) -> str:
    s = normalise_digits(s)
    s = normalise_arabic(s) if has_arabic(s) else s
    return re.sub(r"[^\w\s\-]", " ", s.lower()).strip()


def _ngrams(text: str, max_n: int = 4) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + n]) for n in range(1, max_n + 1) for i in range(len(words) - n + 1)]


def _feature_candidate(f: dict[str, Any], precision: PrecisionClass, conf: float, method: str) -> Candidate:
    lon, lat = _centroid(f["footprint"])
    warn = "corporate office / HQ - not a production site" if f["kind"] == "office" else None
    return Candidate(feature_id=f["id"], label=f"{f['name_en']} / {f['name_ar']}", precision=precision, confidence=conf, method=method, lon=lon, lat=lat, footprint=f["footprint"], district_id=f["district_id"], kind=f["kind"], warning=warn)


def candidates(asset: PhysicalAsset, aliases: dict[str, str] | None = None, fuzzy_cutoff: float = 0.82) -> list[Candidate]:
    """Generate candidates from plot reference, facility name, address text and district mention."""
    g = gazetteer()
    aliases = aliases or {}
    out: list[Candidate] = []
    from services.ingestion import content_firewall

    # address fields are untrusted input too: instruction-like text is dropped, not obeyed
    texts = [t for t in (asset.recorded_address, asset.description) if not content_firewall(t)]
    plot = asset.attributes.get("plot_ref")
    all_text = _norm(" ".join(texts))
    # aliases learned by the evolution loop (e.g. transliteration variants) expand the query text
    for alias, canonical in aliases.items():
        if _norm(alias) in all_text:
            all_text += " " + _norm(canonical)

    # 1. explicit plot reference from documents
    if plot:
        for f in g["features"]:
            if f.get("plot_ref") and f["plot_ref"].lower() == normalise_digits(plot).lower():
                out.append(_feature_candidate(f, "footprint", 0.95, "plot_ref:document"))
    # 2. plot number embedded in address text (Arabic-Indic digits normalised)
    m = re.search(r"(?:plot|قطع[ةه] رقم|قطع[ةه])\s*([a-z]{2,3}\d?-)?(\d{2,4})", all_text)
    if m:
        num = m.group(2)
        for f in g["features"]:
            if f.get("plot_ref") and f["plot_ref"].endswith(f"-{num}"):
                out.append(_feature_candidate(f, "parcel", 0.85, "plot_ref:address"))
    # 3. facility / feature name match, exact then fuzzy
    for f in g["features"]:
        names = [_norm(f["name_en"]), _norm(f["name_ar"])]
        if any(n and n in all_text for n in names):
            out.append(_feature_candidate(f, "footprint", 0.9, "name:exact"))
            continue
        best_r = max((difflib.SequenceMatcher(None, n, chunk).ratio() for n in names if n for chunk in _ngrams(all_text)), default=0.0)
        if best_r >= fuzzy_cutoff:
            out.append(_feature_candidate(f, "footprint", round(0.6 + 0.3 * best_r, 3), f"name:fuzzy({best_r:.2f})"))
    # 4. district-only mention
    for d in g["districts"]:
        if _norm(d["name_en"]) in all_text or _norm(d["name_ar"]) in all_text:
            out.append(Candidate(feature_id=None, label=f"{d['name_en']} (district centroid)", precision="district", confidence=0.5, method="district:mention", lon=d["centroid"][0], lat=d["centroid"][1], district_id=d["id"], kind="district"))
    # HQ trap: an office is never a site for a production/storage asset
    if asset.asset_type in SITE_ASSET_TYPES:
        for c in out:
            if c.kind == "office":
                c.confidence = 0.0
                c.warning = "recorded address is a corporate office; site location is not evidenced"
    # dedupe by (feature_id, precision) keeping best confidence
    best: dict[tuple[str | None, str], Candidate] = {}
    for c in out:
        k = (c.feature_id, c.precision)
        if k not in best or c.confidence > best[k].confidence:
            best[k] = c
    return sorted(best.values(), key=lambda c: c.confidence, reverse=True)


def commit(store: Store, asset: PhysicalAsset, chosen: Candidate | None, reason: str, actor: str) -> Location:
    if chosen is None:
        loc = Location(id=new_id("LOC"), asset_id=asset.id, lon=None, lat=None, precision="unresolved", confidence=0.0, source="none", note=reason)
    else:
        loc = Location(id=new_id("LOC"), asset_id=asset.id, lon=chosen.lon, lat=chosen.lat, footprint=chosen.footprint, precision=chosen.precision, confidence=chosen.confidence, source=chosen.method, matched_feature_id=chosen.feature_id, district_id=chosen.district_id, note=reason)
        asset.district_id = chosen.district_id
    store.s.locations[loc.id] = loc
    asset.location_id = loc.id
    store.audit(actor, "location_committed", asset_id=asset.id, precision=loc.precision, confidence=loc.confidence, method=loc.source)
    return loc
