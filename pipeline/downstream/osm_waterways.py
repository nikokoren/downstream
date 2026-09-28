"""Extract named waterway lines and named lakes from an OSM file (PBF or XML) (D10).

Usage: uv run python -m downstream.osm_waterways INPUT.osm.pbf WATERWAYS.fgb LAKES.fgb
"""

import sys
from pathlib import Path

import geopandas as gpd
import osmium
import shapely
from shapely.geometry import LineString

NAME_TAGS = {"name": "name", "name:de": "name_de", "name:en": "name_en"}


def extract(path: str | Path) -> gpd.GeoDataFrame:
    rows = []
    processor = (
        osmium.FileProcessor(str(path))
        .with_locations()
        .with_filter(osmium.filter.KeyFilter("waterway").enable_for(osmium.osm.WAY))
    )
    for obj in processor:
        if not obj.is_way() or "name" not in obj.tags:
            continue
        coords = [(n.lon, n.lat) for n in obj.nodes if n.location.valid()]
        if len(coords) < 2:
            continue
        row = {
            "osm_id": obj.id,
            "waterway": obj.tags.get("waterway"),
            "wikidata": obj.tags.get("wikidata"),
            "geometry": LineString(coords),
        }
        for tag, column in NAME_TAGS.items():
            row[column] = obj.tags.get(tag)
        rows.append(row)
    columns = ["osm_id", "waterway", *NAME_TAGS.values(), "wikidata", "geometry"]
    return gpd.GeoDataFrame(rows, columns=columns, geometry="geometry", crs="EPSG:4326")


def extract_lakes(path: str | Path) -> gpd.GeoDataFrame:
    """Named natural lakes: natural=water + water=lake (reservoirs and river areas excluded)."""
    wkb = osmium.geom.WKBFactory()
    rows = []
    for obj in osmium.FileProcessor(str(path)).with_areas():
        if not obj.is_area():
            continue
        t = obj.tags
        if t.get("natural") != "water" or t.get("water") != "lake" or "name" not in t:
            continue
        try:
            geom = shapely.from_wkb(bytes.fromhex(wkb.create_multipolygon(obj)))
        except RuntimeError:  # incomplete or invalid multipolygon in the extract
            continue
        row = {
            "osm_id": obj.orig_id(),
            "osm_type": "way" if obj.from_way() else "relation",
            "wikidata": t.get("wikidata"),
            "geometry": geom,
        }
        for tag, column in NAME_TAGS.items():
            row[column] = t.get(tag)
        rows.append(row)
    columns = ["osm_id", "osm_type", *NAME_TAGS.values(), "wikidata", "geometry"]
    return gpd.GeoDataFrame(rows, columns=columns, geometry="geometry", crs="EPSG:4326")


def main(argv: list[str]) -> None:
    src, dst, dst_lakes = argv
    gdf = extract(src)
    gdf.to_file(dst, driver="FlatGeobuf")
    print(f"{src}: {len(gdf)} named waterway ways, {gdf['name'].nunique()} distinct names -> {dst}")
    lakes = extract_lakes(src)
    lakes.to_file(dst_lakes, driver="FlatGeobuf")
    print(f"{src}: {len(lakes)} named lakes -> {dst_lakes}")


if __name__ == "__main__":
    main(sys.argv[1:])
