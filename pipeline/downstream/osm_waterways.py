"""Extract named waterway lines from an OSM file (PBF or XML) into a FlatGeobuf (D10).

Usage: uv run python -m downstream.osm_waterways INPUT.osm.pbf OUTPUT.fgb
"""

import sys
from pathlib import Path

import geopandas as gpd
import osmium
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


def main(argv: list[str]) -> None:
    src, dst = argv
    gdf = extract(src)
    gdf.to_file(dst, driver="FlatGeobuf")
    print(f"{src}: {len(gdf)} named waterway ways, {gdf['name'].nunique()} distinct names -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1:])
