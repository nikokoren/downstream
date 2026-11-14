"""Map hand-offs use captured source vertices, including after path simplification."""

import json
from pathlib import Path

import geopandas as gpd
import shapely

from downstream.naming import METRIC_CRS, chain, load_curated
from downstream.paths import MAX_MAP_POINTS, map_changes, simplify_to

ROOT = Path(__file__).resolve().parents[2]


def reference():
    return json.loads((ROOT / "fixtures/review/battle-reference.json").read_text())["routes"][0]


def test_source_hand_offs_survive_the_map_point_budget_in_both_directions():
    route = reference()
    keep = [c["at"] for c in route["changes"]]
    for coords in (route["coords"], route["coords"][::-1]):
        simple = simplify_to(shapely.LineString(coords), MAX_MAP_POINTS, keep=keep)
        points = list(simple.coords)
        assert len(points) <= MAX_MAP_POINTS
        assert points[0] == tuple(coords[0]) and points[-1] == tuple(coords[-1])
        assert all(tuple(at) in points for at in keep)


def test_names_locate_the_next_source_piece_instead_of_a_share_of_total_km():
    route = reference()
    coords = route["coords"]
    starts = [0, *[coords.index(c["at"]) for c in route["changes"]]]
    ends = [*starts[1:], len(coords) - 1]
    # Pieces are cut from the captured OSM/Natural Earth river trace at its real joins.
    geometry = gpd.GeoSeries(
        [shapely.LineString(coords[a : b + 1]) for a, b in zip(starts, ends, strict=True)],
        crs="EPSG:4326",
    )
    reaches = gpd.GeoDataFrame(
        {"LENGTH_KM": geometry.to_crs(METRIC_CRS).length / 1000}, geometry=geometry
    )
    names = [route["changes"][0]["from"], *[c["to"] for c in route["changes"]]]
    groups = chain(
        reaches, [(n["en"], "osm" if i < 2 else "ne") for i, n in enumerate(names)], load_curated()
    )
    changes = map_changes(groups, reaches)
    assert [c["at"] for c in changes] == [c["at"] for c in route["changes"]]
    assert [c["from"].get("en") or c["from"].get("local") for c in changes] == [
        c["from"]["en"] for c in route["changes"]
    ]
    assert [c["to"].get("en") or c["to"].get("local") for c in changes] == [
        c["to"]["en"] for c in route["changes"]
    ]


def test_display_preserves_the_complete_estimate_and_handles_missing_capture_data():
    from downstream.site import _display

    town = json.loads((ROOT / "recipe/preview/munich.json").read_text())
    assert _display(town)["travel"] == {"en": "about 3–8 weeks", "de": "etwa 3–8 Wochen"}
    # The captured Nürnberg report omits durations; missing data must never turn into 0 days.
    del town["travel_days"]
    missing = _display(town)["travel"]
    assert missing == {"en": "time estimate unavailable", "de": "Dauer unbekannt"}
