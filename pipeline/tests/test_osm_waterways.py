from pathlib import Path

from downstream.osm_waterways import extract

FIXTURE = Path(__file__).parent / "fixtures" / "osm_starnberg.osm"


def test_extracts_named_waterways_from_captured_osm():
    gdf = extract(FIXTURE)
    names = set(gdf["name"])
    # Present by name in the captured file (grep of k="name" on waterway ways).
    assert {"Würm", "Georgenbach", "Maisinger Bach"} <= names
    # Cross-checked with a plain ElementTree parse of the same file: 20 ways, 9 names.
    assert len(gdf) == 20
    assert gdf["name"].nunique() == 9
    assert gdf["name"].notna().all()
    assert (gdf.geometry.geom_type == "LineString").all()
    assert gdf.crs.to_epsg() == 4326
    # All ways lie in or around the query bbox 47.98-48.02 N, 11.30-11.36 E.
    minx, miny, maxx, maxy = gdf.total_bounds
    assert 11.2 < minx and maxx < 11.5 and 47.9 < miny and maxy < 48.1
