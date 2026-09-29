"""Rotation without a server (D8 option (a), 2026-09-29): polyline encoding and the Polling URL."""

import re
import time
from pathlib import Path

import pytest
from liquid import Environment

from downstream.paths import encode_polyline
from downstream.site import BASE_URL, SITE, SLOT_SECONDS, polling_url

RECIPE_URL = Path(__file__).resolve().parents[2] / "recipe" / "polling_url.liquid"


def test_polyline_matches_googles_worked_example():
    # developers.google.com/maps/documentation/utilities/polylinealgorithm: points
    # (38.5, -120.2), (40.7, -120.95), (43.252, -126.453) -> "_p~iF~ps|U_ulLnnqC_mqNvxq`@".
    coords = [(-120.2, 38.5), (-120.95, 40.7), (-126.453, 43.252)]
    assert encode_polyline(coords) == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


def test_polling_url_renders_to_the_current_slot():
    # python-liquid follows Shopify Liquid, which TRMNL uses; not the same engine (Ruby), so the
    # final check is on TRMNL itself.
    n = 6918
    before = int(time.time()) // SLOT_SECONDS
    url = Environment().from_string(polling_url(n)).render()
    after = int(time.time()) // SLOT_SECONDS
    assert url.count("\n") <= 1 and url.strip() == url.rstrip("\n").strip()
    m = re.fullmatch(re.escape(BASE_URL) + r"/t/(\d+)\.json", url.strip())
    assert m, url
    assert int(m.group(1)) in {before % n, after % n}


@pytest.mark.skipif(not (SITE / "t").exists(), reason="run `python -m downstream.site` first")
def test_committed_polling_url_matches_the_site():
    files = len(list((SITE / "t").glob("*.json")))
    assert RECIPE_URL.read_text(encoding="utf-8") == polling_url(files)
