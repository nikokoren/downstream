"""D24: districts and suburbs next to big cities leave the rotation (real GeoNames data in ../data;
skipped without it). Cases checked by hand on 2026-10-15."""

from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
CITIES = RAW / "geonames_cities15000.zip"


@pytest.fixture(scope="module")
def kept():
    from downstream import regions, towns

    names = {}
    for code in ("us", "ca"):
        df = towns.region_towns(RAW, regions.REGIONS[code])
        names[code] = set(df["name"])
    return names


@pytest.mark.skipif(not CITIES.exists(), reason="run `python -m downstream.fetch geonames` first")
def test_cities_stay_and_districts_and_suburbs_go(kept):
    us, ca = kept["us"], kept["ca"]
    assert {"Chicago", "Denver", "Aurora", "New York City", "Arvada"} <= us  # Arvada: 11 km out
    assert not {"Albany Park", "North Lawndale", "Brooklyn"} & us
    assert {"Toronto", "Mississauga", "Montréal", "Laval"} <= ca
    assert not {"Willowdale", "Moss Park", "Etobicoke", "Westmount"} & ca


@pytest.mark.skipif(
    not (RAW / "ne_admin0.zip").exists(), reason="run `python -m downstream.fetch` first"
)
def test_munich_keeps_its_neighbour_towns_and_loses_what_touches_it():
    # Author 2026-10-15: Dachau (17 km), Garching (14 km) and Starnberg (23 km) stay.
    from downstream import regions, towns

    eu = set(towns.region_towns(RAW, regions.EUROPE)["name"])
    assert {"Munich", "Dachau", "Garching", "Starnberg", "Tolmin"} <= eu  # Tolmin: extra town
    assert not {"Pasing", "Bogenhausen", "Unterhaching", "Ottobrunn bei München"} & eu
