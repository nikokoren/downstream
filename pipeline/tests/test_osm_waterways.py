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
    assert "tunnel" in gdf.columns
    # All ways lie in or around the query bbox 47.98-48.02 N, 11.30-11.36 E.
    minx, miny, maxx, maxy = gdf.total_bounds
    assert 11.2 < minx and maxx < 11.5 and 47.9 < miny and maxy < 48.1


def test_extracts_named_lakes_only():
    # Captured fixture: Starnberger See (relation 168892, water=lake) plus two unnamed
    # water=reservoir ways, which must be left out.
    from downstream.osm_waterways import extract_lakes

    lakes = extract_lakes(Path(__file__).parent / "fixtures" / "osm_starnberg_lakes.osm")
    assert list(lakes["name"]) == ["Starnberger See"]
    assert list(lakes["name_en"]) == ["Lake Starnberg"]
    assert lakes.iloc[0]["osm_type"] == "relation" and lakes.iloc[0]["osm_id"] == 168892
    assert lakes.geometry.iloc[0].geom_type in ("Polygon", "MultiPolygon")
    # Assembled polygon measures 56.06 km² in EPSG:3035 (2026-09-28); a broken assembly would not.
    area_km2 = lakes.to_crs("EPSG:3035").area.iloc[0] / 1e6
    assert 50 < area_km2 < 62


def test_tunnelled_ways_are_not_used_for_names():
    from downstream.naming import NameSource

    gdf = extract(FIXTURE)
    tunnelled = gdf["tunnel"].notna() & (gdf["tunnel"] != "no")
    src = NameSource.build("osm", gdf, 600)
    assert len(src.lines) == int((~tunnelled).sum())
