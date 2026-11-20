"""The paired polling contract uses real captured regional model packets."""

import json
import re
from pathlib import Path

import pytest
from liquid import Environment

from downstream.pair_validation import checked_for_pairs
from downstream.site import (
    BASE_URL,
    MAX_PAIR_BYTES,
    SLOTS,
    _display,
    pair_packet,
    polling_url,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/review/model-pairs.json"


def pairs():
    return json.loads(FIXTURE.read_text())["pairs"]


@pytest.mark.parametrize("pair", pairs(), ids=lambda p: p["region"])
def test_compact_pair_retains_both_complete_display_journeys(pair):
    packet = pair_packet(*pair["towns"])
    assert (
        len(
            json.dumps({**packet, "slot": 7775}, ensure_ascii=False, separators=(",", ":")).encode()
        )
        <= MAX_PAIR_BYTES
    )
    assert packet["primary"] == pair["towns"][0]["town"]["geonameid"]
    # Routes go west to east (test_pair_sides), so match them to their towns by id.
    routes = {r["town"]["geonameid"]: r for r in packet["routes"]}
    assert len(routes) == 2
    for original in pair["towns"]:
        route = routes[original["town"]["geonameid"]]
        expected = _display(original)
        assert route["town"] == {k: original["town"][k] for k in route["town"]}
        for key in ("travel", "distance", "place", "end_text", "polyline", "end"):
            if key == "end":
                assert all(route[key][k] == expected[key].get(k) for k in route[key])
            else:
                assert route[key] == expected[key]
        for old, new in zip(original["chain"], route["chain"], strict=True):
            assert old["kind"] == new["kind"]
            for lang in ("en", "de"):
                old_name = (old["name"] or {}).get(lang) or (old["name"] or {}).get("local")
                new_name = (new["name"] or {}).get(lang) or (new["name"] or {}).get("local")
                assert old_name == new_name
        assert "pair_checks" not in route and "ui" not in route


def test_legacy_published_packets_do_not_pass_source_verification():
    for pair in pairs():
        for town in pair["towns"]:
            assert not checked_for_pairs(town)


@pytest.mark.parametrize("value", [None, False, "", "false", "no", True, "true", "yes"])
@pytest.mark.parametrize(
    "region,folder",
    [
        (None, "mix"),
        ([], "mix"),
        (["eu"], "eu"),
        (["us"], "us"),
        (["ca"], "ca"),
        (["eu", "us"], "eu-us"),
        (["eu", "ca"], "eu-ca"),
        (["us", "ca"], "us-ca"),
        ("eu,us,ca", "mix"),
        ("ca,us", "us-ca"),
    ],
)
def test_polling_url_uses_pair_feed_only_when_enabled(value, region, folder):
    url = (
        Environment()
        .from_string(polling_url())
        .render(region=region, watershed_pairs=value)
        .strip()
    )
    match = re.fullmatch(re.escape(BASE_URL) + r"/([\w-]+)/([tp])/(\d+)\.json", url)
    assert match and match[1] == folder
    enabled = value is True or value in ("true", "yes")
    assert match[2] == ("p" if enabled else "t")
    # p/ has the same slots as t/: today's town, with its companion (D25).
    assert int(match[3]) < SLOTS[folder]


def test_failed_source_verification_preserves_existing_site_and_history(tmp_path, monkeypatch):
    from downstream import site

    old_site = tmp_path / "site"
    old_site.mkdir()
    marker = old_site / "previous-build.txt"
    marker.write_text("Keep this build until its replacement succeeds.")
    for pair in pairs():
        folder = tmp_path / "towns" / pair["region"]
        folder.mkdir(parents=True)
        for town in pair["towns"]:
            (folder / f"{town['town']['geonameid']}.json").write_text(json.dumps(town))
    monkeypatch.setattr(site, "SITE", old_site)
    monkeypatch.setattr(site, "SLOTS", dict.fromkeys(site.SLOTS, 6))
    monkeypatch.setattr(site.regions, "out_dir", lambda kind, region: tmp_path / kind / region.code)
    with pytest.raises(ValueError, match="missing source verification"):
        site.build()
    assert marker.read_text() == "Keep this build until its replacement succeeds."
    assert list(old_site.iterdir()) == [marker]
    assert not list(tmp_path.glob("site-build-*"))
