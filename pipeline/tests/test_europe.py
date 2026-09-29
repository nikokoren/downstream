"""Europe border (D9) on the real GeoNames and Natural Earth files; skipped if not downloaded.
Each case below was checked in the 2026-09-28 sweep of all 34,146 cities15000 towns."""

from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
NEEDED = [RAW / "geonames_cities15000.zip", RAW / "ne_admin0.zip"]


@pytest.fixture(scope="module")
def europe():
    from downstream.towns import europe_towns

    return europe_towns(RAW)


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="data not downloaded")
def test_europe_border(europe):
    names = set(zip(europe["name"], europe["cc"], strict=True))
    inside = [
        ("Istanbul", "TR"),
        ("Şişli", "TR"),
        ("Tarabya", "TR"),
        ("Gelibolu", "TR"),
        ("Edirne", "TR"),
        ("Sevastopol", "UA"),
        ("Simferopol", "UA"),
        ("Kerch", "UA"),  # Crimea: GeoNames says UA
        ("Reykjavík", "IS"),
        ("Tórshavn", "FO"),
        ("Valletta", "MT"),
        ("Gibraltar", "GI"),
        ("Mariehamn", "AX"),
        ("Palma", "ES"),
        ("Ajaccio", "FR"),
        ("Irákleion", "GR"),
        ("Narva", "EE"),
        ("Munich", "DE"),
    ]
    outside = [
        ("Üsküdar", "TR"),
        ("Çanakkale", "TR"),
        ("Ataşehir", "TR"),  # Asian shore
        ("Kaliningrad", "RU"),
        ("Sovetsk", "RU"),
        ("Pskov", "RU"),
        ("Nicosia", "CY"),
        ("Tbilisi", "GE"),
        ("Las Palmas de Gran Canaria", "ES"),
        ("Funchal", "PT"),
        ("Ponta Delgada", "PT"),
        ("Ceuta", "ES"),
        ("Melilla", "ES"),
    ]
    assert [t for t in inside if t not in names] == []
    assert [t for t in outside if t in names] == []
    assert (europe["cc"] == "RU").sum() == 0
    assert 7000 <= len(europe) <= 7100  # 7,033 on 2026-09-28; 7,048 with the 15 extra towns
