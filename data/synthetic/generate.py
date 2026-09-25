"""Generate the ILLUSTRATIVE synthetic flood-depth grid and its STAC-like catalog item.

The grid is a smooth blob over a fictional industrial district. It is not a hydraulic model.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "hazard"

BBOX = [55.220, 25.120, 55.260, 25.150]  # lon_min, lat_min, lon_max, lat_max
NX, NY = 100, 75  # ~40 m cells
CENTER = (55.2405, 25.1352)
SIGMA = (0.0060, 0.0040)
MAX_DEPTH_M = 1.25


def main() -> None:
    OUT.mkdir(exist_ok=True)
    lons = np.linspace(BBOX[0], BBOX[2], NX)
    lats = np.linspace(BBOX[1], BBOX[3], NY)
    lon_g, lat_g = np.meshgrid(lons, lats)
    z = np.exp(-(((lon_g - CENTER[0]) / SIGMA[0]) ** 2 + ((lat_g - CENTER[1]) / SIGMA[1]) ** 2) / 2)
    depth = MAX_DEPTH_M * z
    depth[depth < 0.05] = 0.0
    np.save(OUT / "flood_depth_rp100_2050.npy", depth.astype("float32"))
    item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "flood_pluvial_illustrative_rp100_2050_ssp245",
        "properties": {
            "title": "ILLUSTRATIVE pluvial flood depth, 1-in-100, 2050, SSP2-4.5",
            "title_ar": "عمق فيضان سطحي توضيحي، 1 في 100، 2050، SSP2-4.5",
            "hazard": "flood_depth",
            "unit": "m",
            "version": "2026.1-synthetic",
            "spatial_resolution_m": 40,
            "pathway": "SSP2-4.5",
            "horizon": 2050,
            "return_period": 100,
            "validation_status": "illustrative",
            "licence": "synthetic - no real data",
            "grid": {"nx": NX, "ny": NY, "order": "row-major, lat ascending"},
            "asset_file": "flood_depth_rp100_2050.npy",
        },
        "bbox": BBOX,
    }
    (OUT / "flood_item.json").write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")
    heat = {
        "id": "heat_days_cmip6_district_illustrative",
        "properties": {
            "title": "District-level count of days > 45C (illustrative, 25 km source resolution)",
            "hazard": "heat_days_gt45c",
            "unit": "days/yr",
            "version": "2026.1-synthetic",
            "spatial_resolution_m": 25000,
            "precision_class": "district",
            "validation_status": "illustrative",
        },
        "values": {"D-AQ3": {"baseline": 9, "2050": 21}, "D-JAI": {"baseline": 8, "2050": 19}, "D-DIFC": {"baseline": 7, "2050": 17}},
    }
    (OUT / "heat_item.json").write_text(json.dumps(heat, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
