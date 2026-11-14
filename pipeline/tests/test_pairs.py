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
    pair_key,
    report_towns,
    rotation_order,
    rotation_slots,
    shortlist,
    stable_rotation_slots,
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


def rotation_fixture():
    path = FIXTURE.with_name("pair-rotation.json")
    return json.loads(path.read_text(encoding="utf-8"))["pairs"]


def test_rotation_keeps_all_417_pairs_instead_of_the_30_review_examples():
    pairs = rotation_fixture()
    order = rotation_order(pairs)
    assert len(order) == len(pairs) == 417
    assert {pair_key(p) for p in order} == {pair_key(p) for p in pairs}
    assert [p["id"] for p in order] == [p["id"] for p in rotation_order(pairs[::-1])]
    assert [p["id"] for p in order] != [p["id"] for p in rotation_order(pairs, seed=20261114)]


def test_reversing_the_towns_does_not_create_another_unique_pair():
    pair = rotation_fixture()[0]
    flipped = {
        **pair,
        "id": "-".join(reversed(pair["id"].split("-"))),
        "towns": pair["towns"][::-1],
    }
    assert len(rotation_order([pair, flipped])) == 1


def test_full_pool_covers_more_than_four_days_at_the_real_recipe_cadence():
    from downstream.site import SLOT_SECONDS

    slots = rotation_slots(rotation_fixture(), slot_minutes=SLOT_SECONDS / 60)
    assert all(p is not None for p in slots)
    assert len({pair_key(p) for p in slots}) == 417
    assert len(slots) * SLOT_SECONDS > 4 * 86400


def test_sparse_regions_use_normal_town_slots_to_keep_a_three_day_pair_cooldown():
    from downstream.site import SLOT_SECONDS

    pairs = rotation_fixture()[:26]
    slots = rotation_slots(pairs, slot_minutes=SLOT_SECONDS / 60)
    assert len(slots) * SLOT_SECONDS == 72 * 3600
    assert sum(p is not None for p in slots) == 26
    assert {pair_key(p) for p in slots if p} == {pair_key(p) for p in pairs}
    assert max(i for i, p in enumerate(slots) if p) > len(slots) * 0.9
    # Replaying the periodic plan cannot repeat a pair until a full cycle has elapsed.
    seen = {}
    for i, pair in enumerate(slots * 2):
        if pair is None:
            continue
        key = pair_key(pair)
        if key in seen:
            assert (i - seen[key]) * SLOT_SECONDS >= 72 * 3600
        seen[key] = i


def test_build_updates_keep_pair_slots_and_reserve_retired_pairs():
    pairs = rotation_fixture()[:20]
    original = stable_rotation_slots(pairs[:10], 288)
    extended = stable_rotation_slots(pairs, 288, original)
    for pid in original:
        if pid:
            assert original.index(pid) == extended.index(pid)
    retired = stable_rotation_slots(pairs[1:], 288, extended)
    assert retired == extended
    restored = stable_rotation_slots(pairs, 288, retired)
    assert restored == extended
    assert {p["id"] for p in pairs} == {pid for pid in restored if pid}


def test_invalid_previous_slots_and_capacity_changes_stop_the_build():
    pairs = rotation_fixture()[:2]
    original = stable_rotation_slots(pairs, 288)
    with pytest.raises(ValueError, match="different capacity"):
        stable_rotation_slots(pairs, 576, original)
    duplicated = list(original)
    duplicated[1] = original[0]
    with pytest.raises(ValueError, match="invalid previous"):
        stable_rotation_slots(pairs, 288, duplicated)
    with pytest.raises(ValueError, match="at least 72 hours"):
        stable_rotation_slots(pairs, 96)
