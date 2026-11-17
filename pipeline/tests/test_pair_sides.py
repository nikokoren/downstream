"""Full's comparison puts the first route's card bottom left and the second's bottom right, so
routes go west to east by where their paths lie (captured live packets, 2026-11-17)."""

import json
from pathlib import Path

from downstream.paths import encode_polyline
from downstream.site import _screen_x, decode_polyline, order_west_to_east

PAIRS = json.loads((Path(__file__).parent / "fixtures" / "pair_sides.json").read_text())["pairs"]


def by_towns(*names):
    return next(p for p in PAIRS if {r["town"]["en"] for r in p["routes"]} == set(names))


def towns(routes):
    return [r["town"]["en"] for r in routes]


def test_decoder_reads_back_what_the_pipeline_encodes():
    for pair in PAIRS:
        for route in pair["routes"]:
            assert encode_polyline(decode_polyline(route["polyline"])) == route["polyline"]


def test_leutkirch_goes_right_because_its_path_runs_east():
    # The author's screenshot: Leutkirch (Danube, Black Sea) had the left card and Friedrichshafen
    # (Rhine, North Sea) the right one.
    pair = by_towns("Leutkirch", "Friedrichshafen")
    assert towns(pair["routes"]) == ["Leutkirch", "Friedrichshafen"]  # as published
    assert towns(order_west_to_east(pair["routes"])) == ["Friedrichshafen", "Leutkirch"]


def test_order_does_not_depend_on_input_order():
    for pair in PAIRS:
        routes = pair["routes"]
        assert towns(order_west_to_east(routes)) == towns(order_west_to_east(routes[::-1]))


def test_path_mass_wins_over_the_endpoint_in_north_south_splits():
    # Deltona's St. Johns runs north to the Atlantic near Jacksonville; Lake Butler's water runs
    # south through Lake Okeechobee and ends west, in the Gulf. Most of the Atlantic path lies
    # further west, so it takes the left card although its sea is further east.
    pair = by_towns("Deltona", "Lake Butler")
    left, right = order_west_to_east(pair["routes"])
    ref = decode_polyline(left["polyline"])[0][0]
    assert _screen_x(left, ref) < _screen_x(right, ref)
    assert towns([left, right]) == ["Deltona", "Lake Butler"]
