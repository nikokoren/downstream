"""Primary-geometry regressions from five actual published towns and original HydroATLAS."""

import gzip
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely import STRtree

from downstream.network import Network
from downstream.pair_validation import augment, checked_for_pairs, source_checks
from downstream.regions import EUROPE

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/review/source-network.json.gz"


@pytest.fixture(scope="module")
def primary():
    data = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    reaches = gpd.GeoDataFrame.from_features(data["reaches"], crs="EPSG:4326")
    reaches = reaches.set_index("HYRIV_ID", drop=False)
    basins = gpd.GeoDataFrame.from_features(data["basins"], crs="EPSG:4326")
    return {
        "net": Network(reaches, STRtree(reaches.geometry.values)),
        "basins": basins,
        "tree": STRtree(basins.geometry.values),
        "labels": {int(k): tuple(v) for k, v in data["labels"].items()},
        "name_en": data["name_en"],
        "towns": {d["town"]["en"]: d for d in data["towns"]},
    }


def checked(primary, name):
    return augment(
        primary["towns"][name],
        primary["net"],
        primary["basins"],
        primary["tree"],
        EUROPE,
        primary["labels"],
        primary["name_en"],
    )


@pytest.mark.parametrize(
    "name,basin,outlet,offset",
    [
        ("Stuttgart", 2120458450, 20323928, 0.332967),
        ("Ulm", 2120469530, 20498112, 0.517956),
        ("Weißenburg in Bayern", 2121143100, 20323928, 0.995227),
    ],
)
def test_actual_source_basins_routes_and_offsets_pass(
    primary, monkeypatch, name, basin, outlet, offset
):
    monkeypatch.setenv("DOWNSTREAM_REGION", "eu")
    result = checked(primary, name)
    check = result["pair_checks"]
    assert checked_for_pairs(result)
    assert check["basin_id"] == check["reach_basin_id"] == basin
    assert check["outlet_reach"] == outlet
    assert check["start_distance_km"] == pytest.approx(offset, abs=1e-6)


def test_close_reach_in_wrong_basin_does_not_pass(primary, monkeypatch):
    monkeypatch.setenv("DOWNSTREAM_REGION", "eu")
    result = checked(primary, "Pfaffenhofen an der Ilm")
    check = result["pair_checks"]
    assert not checked_for_pairs(result)
    assert check["start_distance_km"] == pytest.approx(0.288917, abs=1e-6)
    assert check["basin_id"] == 2121148790
    assert check["reach_basin_id"] == 2121147730
    assert "start_reach_outside_town_basin" in check["issues"]


def test_normal_journey_keeps_source_labels_when_pair_offset_is_too_large(primary, monkeypatch):
    monkeypatch.setenv("DOWNSTREAM_REGION", "eu")
    result = checked(primary, "Mountsorrel")
    assert not checked_for_pairs(result)
    assert result["pair_checks"]["start_distance_km"] == pytest.approx(1.17004, abs=1e-6)
    assert result["pair_checks"]["issues"] == ["start_reach_more_than_1km_from_town"]
    assert [(c["from"]["local"], c["to"]["local"]) for c in result["changes"]] == [
        ("Rothley Brook", "River Soar"),
        ("River Soar", "River Trent"),
    ]
    source_vertices = {tuple(c) for line in primary["net"].reaches.geometry for c in line.coords}
    assert all(tuple(c["at"]) in source_vertices for c in result["changes"])


def test_incomplete_source_graph_is_rejected(primary):
    packet = primary["towns"]["Stuttgart"]
    path = primary["net"].downstream(packet["start"]["reach"])
    reaches = primary["net"].reaches.drop(path[1])
    net = Network(reaches, STRtree(reaches.geometry.values))
    check = source_checks(packet, net, primary["basins"], primary["tree"], EUROPE)
    assert check["status"] == "rejected"
    assert "source_route_incomplete_or_cyclic" in check["issues"]


def test_verification_hash_binds_river_change_metadata(primary, monkeypatch):
    monkeypatch.setenv("DOWNSTREAM_REGION", "eu")
    result = checked(primary, "Stuttgart")
    assert result["changes"] and checked_for_pairs(result)
    result.pop("changes")
    assert not checked_for_pairs(result)
