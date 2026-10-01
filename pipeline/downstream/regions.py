"""Regions the pipeline can build (D22): everything that differs between Europe and the United
States lives here. The region is picked once per process by the environment variable
DOWNSTREAM_REGION (default "eu"), so every module sees the same one.

Usage: DOWNSTREAM_REGION=us uv run python -m downstream.fetch   (and the other steps likewise)
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Region:
    code: str  # folder and file suffix: data/<kind>/<code>/..., <code>/t/<n>.json on the site
    riveratlas: tuple[str, ...]  # RiverATLAS v1.0 region files (whole basins, no river crosses)
    bbox: tuple[float, float, float, float]  # lon/lat window for BasinATLAS and HydroLAKES
    metric_crs: str  # equal-area, metres: distances and buffers
    ne_window: tuple[float, float, float, float]  # Natural Earth clip before projecting
    sea_window: tuple[float, float, float, float]  # seas a river mouth can belong to
    ne_extra: tuple[str, ...]  # Natural Earth regional supplements (rivers, lakes)
    osm_regions: str  # file next to this module: the Geofabrik regions to name rivers from
    # Natural Earth lakes at least this big (km²) name the reaches inside them even over OSM river
    # names; None: off. For lakes OSM's regional extracts can't hold whole (the Great Lakes
    # straddle the US-Canada border, so their outlines are incomplete in every extract).
    ne_big_lake_km2: float | None = None
    # Fold a short river stub at a lake's outlet into the lake (naming._drop_outlet_stubs). Off in
    # Europe so its chains stay as built (it would change 1 of 6,918 towns, Katrineholm).
    outlet_stubs: bool = False


EUROPE = Region(
    code="eu",
    riveratlas=("eu",),
    bbox=(-25.0, 34.0, 45.0, 72.0),
    metric_crs="EPSG:3035",  # ETRS89 / LAEA Europe
    ne_window=(-35.0, 25.0, 60.0, 75.0),
    sea_window=(-30.0, 28.0, 55.0, 74.0),
    ne_extra=("rivers_europe", "lakes_europe"),
    osm_regions="osm_regions.txt",
)

# Contiguous 48 states and Alaska (D22; Hawaii has no HydroATLAS coverage). The window also holds
# where US water ends abroad: the St. Lawrence and Hudson Bay (Canada), the Gulf of California.
UNITED_STATES = Region(
    code="us",
    riveratlas=("na", "ar"),
    bbox=(-180.0, 14.0, -50.0, 72.0),
    # US National Atlas Equal Area's parameters (EPSG:9311, LAEA, covers Alaska) on WGS84, so no
    # NAD27 datum shift is needed.
    metric_crs="+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs",
    ne_window=(-180.0, 5.0, -40.0, 80.0),
    sea_window=(-180.0, 5.0, -45.0, 78.0),
    ne_extra=("rivers_north_america", "lakes_north_america"),
    osm_regions="osm_regions_us.txt",
    ne_big_lake_km2=1000.0,
    outlet_stubs=True,
)

REGIONS = {r.code: r for r in (EUROPE, UNITED_STATES)}

DATA = Path(__file__).resolve().parents[2] / "data"


def current() -> Region:
    code = os.environ.get("DOWNSTREAM_REGION", "eu")
    if code not in REGIONS:
        raise ValueError(f"DOWNSTREAM_REGION={code!r}: expected one of {sorted(REGIONS)}")
    return REGIONS[code]


def osm_regions_file(region: Region) -> Path:
    return Path(__file__).with_name(region.osm_regions)


def out_dir(kind: str, region: Region | None = None) -> Path:
    """Build output per region: data/<kind>/<code> (names, paths, towns, report)."""
    return DATA / kind / (region or current()).code
