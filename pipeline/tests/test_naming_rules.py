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


def test_bilingual_osm_names_map_to_one_curated_river():
    # Names on the Graz path with OSM Slovenia/Croatia/Hungary, 2026-09-28.
    from downstream.naming import load_curated, lookup_curated

    curated = load_curated()
    for name, en in [
        ("Mur", "Mur"),
        ("Mur / Mura", "Mur"),
        ("Mura", "Mur"),
        ("Drava / Dráva", "Drava"),
        ("Drava", "Drava"),
        ("Dunav / Дунав", "Danube"),
    ]:
        assert lookup_curated(name, curated)["en"] == en, name


def test_hyphenated_border_names_are_variants():
    # Romanian-Bulgarian and Romanian-Ukrainian Danube names in OSM (2026-09-29 Europe run).
    from downstream.naming import load_curated, lookup_curated

    curated = load_curated()
    for name in ("Dunărea - Дунав", "Dunărea - Дунай"):
        assert lookup_curated(name, curated)["en"] == "Danube", name


def test_slash_and_arm_names_are_variants():
    from downstream.naming import load_curated, lookup_curated, name_variants

    curated = load_curated()
    for name in ("Дунав/Dunărea", "Dunav/Dunărea", "Brațul Borcea (Dunărea)"):
        assert lookup_curated(name, curated)["en"] == "Danube", name
    assert name_variants("Main-Donau-Kanal") == ["Main-Donau-Kanal"]


def test_name_order_and_shared_parts_are_one_river():
    # Neighbouring steps from the 2026-09-29 Europe run (Wolkenstein, Tolmin, Brest, Badajoz).
    import geopandas as gpd

    from downstream.naming import chain, display_key, load_curated

    assert display_key("Eisack - Isarco") == display_key("Isarco - Eisack")
    curated = load_curated()
    for a, b, shown in [
        ("Soča", "Isonzo / Soča / Lusinç", "Soča"),
        ("Bug / Заходні Буг", "Bug", "Bug / Заходні Буг"),
        ("Río Guadiana", "Río Guadiana / Rio Guadiana", "Río Guadiana"),
    ]:
        reaches = gpd.GeoDataFrame({"LENGTH_KM": [5.0, 3.0]})
        groups = chain(reaches, [(a, "osm"), (b, "osm")], curated)
        assert len(groups) == 1, (a, b)
        assert (groups[0]["name"].get("en") or groups[0]["name"]["local"]) == shown


def test_different_rivers_sharing_nothing_stay_apart():
    import geopandas as gpd

    from downstream.naming import chain, load_curated

    reaches = gpd.GeoDataFrame({"LENGTH_KM": [5.0, 3.0]})
    groups = chain(reaches, [("Ammer", "osm"), ("Neckar", "osm")], load_curated())
    assert len(groups) == 2
