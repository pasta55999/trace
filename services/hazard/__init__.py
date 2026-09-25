"""Versioned hazard data service.

Layers are catalogued STAC-style. Sampling returns the value plus dataset id, version and
native resolution. Outside coverage the answer is Unknown - never zero.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel
from shapely.geometry import Point, Polygon

from services.common import SYNTHETIC, Unknown

HAZARD_DIR = SYNTHETIC / "hazard"


class HazardSample(BaseModel):
    dataset_id: str
    version: str
    hazard: str
    unit: str
    resolution_m: int
    value: float | Unknown
    method: str
    validation_status: str


class _FloodLayer:
    def __init__(self, item_path: Path):
        self.item = json.loads(item_path.read_text(encoding="utf-8"))
        p = self.item["properties"]
        self.grid = np.load(item_path.parent / p["asset_file"])
        self.bbox = self.item["bbox"]
        self.ny, self.nx = self.grid.shape

    def _ij(self, lon: float, lat: float) -> tuple[int, int] | None:
        x0, y0, x1, y1 = self.bbox
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            return None
        i = int(round((lat - y0) / (y1 - y0) * (self.ny - 1)))
        j = int(round((lon - x0) / (x1 - x0) * (self.nx - 1)))
        return i, j

    def sample_point(self, lon: float, lat: float) -> float | None:
        ij = self._ij(lon, lat)
        return None if ij is None else float(self.grid[ij])

    def sample_footprint(self, footprint: list[list[float]]) -> float | None:
        """Max depth over cells whose centres fall in the footprint; falls back to vertices + centroid."""
        poly = Polygon(footprint)
        minx, miny, maxx, maxy = poly.bounds
        vals: list[float] = []
        x0, y0, x1, y1 = self.bbox
        for i in range(self.ny):
            lat = y0 + (y1 - y0) * i / (self.ny - 1)
            if lat < miny or lat > maxy:
                continue
            for j in range(self.nx):
                lon = x0 + (x1 - x0) * j / (self.nx - 1)
                if minx <= lon <= maxx and poly.contains(Point(lon, lat)):
                    vals.append(float(self.grid[i, j]))
        if not vals:
            c = poly.centroid
            pts = footprint + [[c.x, c.y]]
            vals = [v for v in (self.sample_point(x, y) for x, y in pts) if v is not None]
        return max(vals) if vals else None


@lru_cache(maxsize=1)
def catalog() -> dict[str, Any]:
    flood = json.loads((HAZARD_DIR / "flood_item.json").read_text(encoding="utf-8"))
    heat = json.loads((HAZARD_DIR / "heat_item.json").read_text(encoding="utf-8"))
    return {"flood": flood, "heat": heat}


@lru_cache(maxsize=1)
def _flood() -> _FloodLayer:
    return _FloodLayer(HAZARD_DIR / "flood_item.json")


def dataset_versions() -> dict[str, str]:
    c = catalog()
    return {f"hazard:{c['flood']['id']}": c["flood"]["properties"]["version"], f"hazard:{c['heat']['id']}": c["heat"]["properties"]["version"]}


def sample_flood(lon: float | None, lat: float | None, footprint: list[list[float]] | None, precision: str) -> HazardSample:
    layer = _flood()
    p = layer.item["properties"]
    base = dict(dataset_id=layer.item["id"], version=p["version"], hazard=p["hazard"], unit=p["unit"], resolution_m=p["spatial_resolution_m"], validation_status=p["validation_status"])
    if precision == "unresolved" or lon is None or lat is None:
        return HazardSample(**base, value=Unknown(reason="asset location unresolved", reason_ar="موقع الأصل غير محدد"), method="none")
    if precision == "district":
        return HazardSample(**base, value=Unknown(reason="location known only to district level; 40 m flood layer cannot be applied to a district centroid", reason_ar="الموقع معروف على مستوى المنطقة فقط؛ لا يمكن تطبيق طبقة فيضان بدقة 40 م على مركز المنطقة"), method="refused:precision")
    v = layer.sample_footprint(footprint) if footprint else layer.sample_point(lon, lat)
    if v is None:
        return HazardSample(**base, value=Unknown(reason="outside dataset coverage", reason_ar="خارج نطاق تغطية مجموعة البيانات"), method="none")
    return HazardSample(**base, value=round(v, 3), method="footprint_max" if footprint else "point")


def sample_heat(district_id: str | None, horizon: str = "2050") -> HazardSample:
    item = catalog()["heat"]
    p = item["properties"]
    base = dict(dataset_id=item["id"], version=p["version"], hazard=p["hazard"], unit=p["unit"], resolution_m=p["spatial_resolution_m"], validation_status=p["validation_status"])
    vals = item["values"].get(district_id or "")
    if not vals:
        return HazardSample(**base, value=Unknown(reason="district not in coverage", reason_ar="المنطقة خارج التغطية"), method="none")
    return HazardSample(**base, value=float(vals[horizon]), method="district_lookup")
