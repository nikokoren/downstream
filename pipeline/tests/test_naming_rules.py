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


def test_delta_arms_fold_into_the_main_river():
    # Cologne path, 2026-09-28: 75 reaches, all ORD_CLAS 1; before folding, Natural Earth names
    # were Rhine x41, Nederrijn x11, Lek x23.
    import pandas as pd

    from downstream.naming import fold_delta

    rhine, nederrijn, lek = ("Rhine", "ne"), ("Nederrijn", "ne"), ("Lek", "ne")
    reaches = pd.DataFrame({"ORD_CLAS": [1] * 75})
    labels = [rhine] * 41 + [nederrijn] * 11 + [lek] * 23
    assert fold_delta(reaches, labels) == [rhine] * 75


def test_fold_only_touches_the_last_river():
    # Nuremberg shape: Regnitz (order 3) -> Main (2) -> Rhine (1) -> Lek (1).
    import pandas as pd

    from downstream.naming import fold_delta

    regnitz, main, rhine, lek = R, ("Main", "osm"), ("Rhine", "ne"), ("Lek", "ne")
    reaches = pd.DataFrame({"ORD_CLAS": [3] * 3 + [2] * 4 + [1] * 6})
    labels = [regnitz] * 3 + [main] * 4 + [rhine] * 4 + [lek] * 2
    assert fold_delta(reaches, labels) == [regnitz] * 3 + [main] * 4 + [rhine] * 6
