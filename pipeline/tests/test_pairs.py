"""Pair discovery against captured report/GeoNames records, not invented town locations."""

import csv
import json
from itertools import combinations
from pathlib import Path

import pytest

from downstream.pairs import (
    GEOD,
    destination_group,
    find_pairs,
    report_towns,
    shortlist,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/review/pair-search.json"


def captured():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("max_km", [50, 80])
def test_spatial_search_matches_an_exhaustive_geodesic_search(max_km):
    towns = captured()["towns"]
    expected = set()
    for a, b in combinations(towns, 2):
        if destination_group(a["destination"]) == destination_group(b["destination"]):
            continue
        if min(a["total_km"], b["total_km"]) < 100:
            continue
        if max(a["start_dist_km"], b["start_dist_km"]) > 1:
            continue
        if GEOD.inv(a["lon"], a["lat"], b["lon"], b["lat"])[2] <= max_km * 1000:
            expected.add(tuple(sorted((a["geonameid"], b["geonameid"]))))
    result = find_pairs(towns, max_km=max_km)
    assert {tuple(t["geonameid"] for t in p["towns"]) for p in result} == expected
    assert expected
    assert [p["id"] for p in result] == [p["id"] for p in find_pairs(towns[::-1], max_km=max_km)]


def test_eighty_km_default_includes_captured_canadian_pair_but_fifty_does_not():
    audit = json.loads(FIXTURE.with_name("pair-audit.json").read_text(encoding="utf-8"))
    pair = audit["canada_proximity_diagnostic_only"]["nearest_examples"][0]
    towns = pair["towns"]
    assert {t["name"] for t in towns} == {"Amos", "Rouyn-Noranda"}
    result = find_pairs(towns)
    assert len(result) == 1
    assert result[0]["id"] == "5884588-6128577"
    assert result[0]["distance_km"] == pytest.approx(76.537)
    assert find_pairs(towns, max_km=50) == []


def test_baltic_and_its_gulf_do_not_qualify_as_opposing_destinations():
    towns = [t for t in captured()["towns"] if t["name"] in {"Ludvika", "Borlänge"}]
    assert {t["destination"] for t in towns} == {"Baltic Sea", "Gulf of Bothnia"}
    assert (
        39000
        < GEOD.inv(towns[0]["lon"], towns[0]["lat"], towns[1]["lon"], towns[1]["lat"])[2]
        < 41000
    )
    assert find_pairs(towns) == []


def test_report_join_uses_captured_ids_and_keeps_the_modeled_destinations(tmp_path):
    data = captured()
    report = tmp_path / "towns.csv"
    with report.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data["report_rows"][0]))
        writer.writeheader()
        writer.writerows(data["report_rows"])
    coords = tmp_path / "cities.json"
    coords.write_text(json.dumps({**data["coordinates"], **data["unselected_coordinates"]}))
    towns, stats = report_towns(report, coords)
    assert towns == data["towns"]
    assert stats["missing_ids"] == []
    # Extra GeoNames neighbourhood/suburb records cannot enter through the coordinate cache.
    assert {t["geonameid"] for t in towns}.isdisjoint(data["unselected_coordinates"])


def test_shortlist_does_not_repeat_towns_or_pack_every_pair_onto_one_local_divide():
    selected = shortlist(find_pairs(captured()["towns"]))
    assert selected
    ids = [t["geonameid"] for p in selected for t in p["towns"]]
    assert len(ids) == len(set(ids))
    assert all(
        GEOD.inv(*a["midpoint"], *b["midpoint"])[2] >= 75000 for a, b in combinations(selected, 2)
    )
