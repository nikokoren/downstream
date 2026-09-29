"""Per-river clean-up on real river chains from the 2026-09-29 Europe run (RiverATLAS eu, OSM)."""

import pandas as pd

from downstream.rivers import clean, river_mouths


def frame(rows):
    return pd.DataFrame(
        rows, columns=["HYRIV_ID", "NEXT_DOWN", "ORD_CLAS", "LENGTH_KM", "DIST_DN_KM"]
    )


def test_river_mouths_follow_same_order_only():
    # a -> b -> c same order, c -> d bigger river (lower order), d is an outlet.
    r = frame([(1, 2, 3, 1, 30), (2, 3, 3, 1, 20), (3, 4, 3, 1, 10), (4, 0, 2, 1, 0)])
    assert list(river_mouths(r)) == [3, 3, 3, 4]


def test_hamburg_alster_fills_its_unnamed_last_reach():
    # The Alster river chain in Hamburg: raw OSM names upstream -> downstream; the last reach
    # (20282122, the town's start) had no name of its own.
    ids = [
        20279445,
        20279045,
        20278397,
        20278295,
        20278207,
        20279222,
        20280464,
        20281450,
        20281558,
        20282122,
    ]
    km = [2.81, 12.5, 0.54, 2.18, 3.27, 5.75, 8.59, 5.83, 0.46, 3.71]
    raw_names = [
        None,
        None,
        "Bunsbach",
        "Ammersbek",
        "Ammersbek",
        "Alster",
        "Alster",
        "Alster",
        "Alster",
        None,
    ]
    rows, dist = [], sum(km)
    for i, (rid, k) in enumerate(zip(ids, km, strict=True)):
        dist -= k
        rows.append((rid, ids[i + 1] if i + 1 < len(ids) else 99, 3, k, dist))
    rows.append((99, 0, 2, 1.0, 0.0))  # the Elbe reach it joins
    raw = pd.DataFrame(
        {"HYRIV_ID": ids, "name": raw_names, "source": ["osm" if n else None for n in raw_names]}
    )
    out = clean(frame(rows), raw).set_index("HYRIV_ID")
    assert out.loc[20282122, "name"] == "Alster"
    assert out.loc[20278397, "name"] == "Ammersbek"  # short Bunsbach blip absorbed


def test_no_trusted_name_means_no_guess():
    # Graz: Ragnitzbach (1 reach, 3.56 km), Leonhardbach (1 reach, 1.44 km), unnamed start
    # (4.46 km): nothing long enough, so the start stays unnamed (was a 1:1 tie guess).
    r = frame(
        [(1, 2, 4, 3.56, 9.0), (2, 3, 4, 1.44, 7.5), (3, 4, 4, 4.46, 3.0), (4, 0, 3, 3.0, 0.0)]
    )
    raw = pd.DataFrame(
        {
            "HYRIV_ID": [1, 2, 3],
            "name": ["Ragnitzbach", "Leonhardbach", None],
            "source": ["osm", "osm", None],
        }
    )
    out = clean(r, raw).set_index("HYRIV_ID")
    assert pd.isna(out.loc[3, "name"]) or out.loc[3, "name"] is None
