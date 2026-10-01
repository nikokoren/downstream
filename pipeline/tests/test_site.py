"""Rotation without a server (D8 option (a), 2026-09-29): polyline encoding and the Polling URL."""

import re
import time
from pathlib import Path

import pytest
from liquid import Environment

from downstream.paths import encode_polyline
from downstream.site import BASE_URL, REGION, SITE, SLOT_SECONDS, SLOTS, polling_url

RECIPE_URL = Path(__file__).resolve().parents[2] / "recipe" / "polling_url.liquid"


def test_polyline_matches_googles_worked_example():
    # developers.google.com/maps/documentation/utilities/polylinealgorithm: points
    # (38.5, -120.2), (40.7, -120.95), (43.252, -126.453) -> "_p~iF~ps|U_ulLnnqC_mqNvxq`@".
    coords = [(-120.2, 38.5), (-120.95, 40.7), (-126.453, 43.252)]
    assert encode_polyline(coords) == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


def test_polling_url_renders_to_the_current_slot():
    # python-liquid follows Shopify Liquid, which TRMNL uses; not the same engine (Ruby), so the
    # final check is on TRMNL itself.
    n = SLOTS
    before = int(time.time()) // SLOT_SECONDS
    url = Environment().from_string(polling_url()).render()
    after = int(time.time()) // SLOT_SECONDS
    assert url.count("\n") <= 1 and url.strip() == url.rstrip("\n").strip()
    m = re.fullmatch(re.escape(f"{BASE_URL}/{REGION}") + r"/t/(\d+)\.json", url.strip())
    assert m, url
    assert int(m.group(1)) in {before % n, after % n}


@pytest.mark.skipif(
    not (SITE / REGION / "t").exists(), reason="run `python -m downstream.site` first"
)
def test_committed_polling_url_matches_the_site():
    # One file per slot, and the committed URL uses the same fixed slot count.
    assert len(list((SITE / REGION / "t").glob("*.json"))) == SLOTS
    assert RECIPE_URL.read_text(encoding="utf-8") == polling_url()


def test_ui_words_complete_in_both_languages():
    from downstream.locales import UI

    assert set(UI["en"]) == set(UI["de"])
    assert all(v.strip() for lang in UI.values() for v in lang.values())


def test_distance_formats_per_language_and_unit():
    # Real totals from the 2026-09-30 build: Limhamn 1.7 km, and the 95th percentile 1,806 km.
    from downstream.locales import distance_text

    assert distance_text(1.7) == {
        "en": {"metric": "1.7 km", "imperial": "1.1 mi"},
        "de": {"metric": "1,7 km", "imperial": "1,1 mi"},
    }
    d = distance_text(1806.0)
    assert d["en"]["metric"] == "1,806 km" and d["de"]["metric"] == "1.806 km"
    assert d["en"]["imperial"] == "1,122 mi" and d["de"]["imperial"] == "1.122 mi"


def test_travel_text_ranges_and_units():
    from downstream.locales import travel_text

    # Munich's estimate (26.5 days): 17.7–39.8 days -> 2.5–5.7 weeks -> "3–6 weeks".
    assert travel_text(26.5) == {"en": "about 3–6 weeks", "de": "etwa 3–6 Wochen"}
    assert travel_text(0.05)["en"] == "about 1–2 hours"  # 1.2 h: 0.8–1.8 h
    assert travel_text(3)["de"] == "etwa 2–5 Tage"
    assert travel_text(19.57)["en"] == "about 2–4 weeks"  # Vienna


def test_recipe_settings_carry_the_polling_url():
    """recipe/src/settings.yml (the plugin export) must hold the same Polling URL, quoted."""
    settings = Path(__file__).resolve().parents[2] / "recipe" / "src" / "settings.yml"
    line = next(x for x in settings.read_text().splitlines() if x.startswith("polling_url:"))
    assert line == "polling_url: '" + polling_url().strip() + "'"


def test_every_endpoint_line_both_languages():
    from downstream.locales import end_text

    assert end_text({"type": "sink", "name": ""})["de"] == "versickert im Boden"
    assert end_text({"type": "sea", "name": "Black Sea"})["de"] == "endet im Schwarzen Meer"
    lake = end_text({"type": "lake", "name": "Paralimni Lake"})
    assert lake["en"] == "ends in: Paralimni Lake"


@pytest.mark.skipif(
    not (SITE / REGION / "t").exists(), reason="run `python -m downstream.site` first"
)
def test_every_town_has_a_country_line():
    """Every slot file names its town with its country ("Vihti, Finland" / "Vihti, Finnland")."""
    import json

    for f in (SITE / REGION / "t").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["place"]["en"].startswith(d["town"]["en"] + ", "), f
        assert d["place"]["de"].startswith(d["town"]["de"] + ", "), f
