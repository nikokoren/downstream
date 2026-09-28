"""Naming clean-up rules. Label sequences are shortened from real runs on 2026-09-28
(Munich, Nuremberg paths with OSM Bavaria + Natural Earth), not invented."""

from downstream.naming import _absorb_short_blocks, _collapse_interruptions

D, O, P, R = ("Danube", "ne"), ("Ogosta", "ne"), ("Pegnitz", "osm"), ("Regnitz", "osm")
N = (None, None)


def test_interruption_inside_one_river_is_collapsed():
    # Danube main stem with Natural Earth's Ogosta winning a stretch (Munich path, reaches 466-485).
    labels = [D] * 5 + [O] * 20 + [D] * 5
    assert _collapse_interruptions(labels) == [D] * 30


def test_real_name_change_along_one_river_survives():
    # Pegnitz becomes Regnitz at Fürth; same ORD_CLAS run (Nuremberg path).
    labels = [P] * 4 + [R] * 6
    assert _collapse_interruptions(labels) == labels


def test_short_blips_and_gaps_take_the_upstream_name():
    labels = [D] * 4 + [N] + [O] * 2 + [D] * 4
    assert _absorb_short_blocks(labels, 3) == [D] * 11
