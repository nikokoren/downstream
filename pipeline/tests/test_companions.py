"""Companion choice (D25) on captured published town files: every published town within the
companion distance of Leutkirch, Houston and Hamburg (other-sea towns only for Leutkirch and
Hamburg), captured 2026-11-20. Published files carry no source checks, so every town counts as
unchecked here, as a legacy packet does in the build."""

import json
from pathlib import Path

from downstream import companions
from downstream.pair_validation import checked_for_pairs

TOWNS = json.loads((Path(__file__).parent / "fixtures" / "companions.json").read_text())["towns"]
PACKETS = {t["town"]["geonameid"]: t for t in TOWNS}
BY_NAME = {(t["town"]["en"], t["town"]["cc"]): t["town"]["geonameid"] for t in TOWNS}


def gid(name, cc):
    return BY_NAME[(name, cc)]


def name(geonameid):
    return PACKETS[geonameid]["town"]["en"]


def test_published_files_count_as_unchecked():
    assert not any(checked_for_pairs(t) for t in TOWNS)


def test_dots_too_close_on_screen_skip_nearer_towns():
    # Leutkirch's Danube path to the Black Sea makes a wide map at a whole zoom level: every North
    # Sea town nearer than Brackenheim (Wangen 21 km, ..., Reutlingen 96 km) would sit too close to
    # it on the OG.
    table = companions.choose(PACKETS)
    kind, km, other = table[gid("Leutkirch", "DE")]
    assert (kind, name(other)) == ("other_sea", "Brackenheim")
    assert 155 < km < 156
    leutkirch = companions.town(PACKETS[gid("Leutkirch", "DE")])
    wangen = companions.town(PACKETS[gid("Wangen", "DE")])
    reutlingen = companions.town(PACKETS[gid("Reutlingen", "DE")])
    assert companions.gap_px(leutkirch, wangen) < companions.MIN_GAP_PX
    assert companions.gap_px(leutkirch, reutlingen) < companions.MIN_GAP_PX


def test_close_pairs_need_the_strict_source_checks():
    # Bad Oldesloe (Baltic Sea) is 38 km from Hamburg (North Sea) and clear on screen, but neither
    # file carries a passed source check, so the companion is the first town beyond 80 km.
    hamburg = companions.town(PACKETS[gid("Hamburg", "DE")])
    oldesloe = companions.town(PACKETS[gid("Bad Oldesloe", "DE")])
    assert companions._km(hamburg, oldesloe) < companions.CLOSE_KM
    assert companions.gap_px(hamburg, oldesloe) >= companions.MIN_GAP_PX
    kind, km, other = companions.choose(PACKETS)[gid("Hamburg", "DE")]
    assert kind == "other_sea" and km >= companions.CLOSE_KM
    assert PACKETS[other]["end"]["name"] == "Baltic Sea"


def test_same_sea_counts_when_the_mouth_is_far_away():
    # No town within 450 km of Houston drains anywhere but the Gulf of Mexico. Its suburbs share
    # its mouth (Galveston Bay); Bay City's river reaches the Gulf over 150 km further along.
    kind, _, other = companions.choose(PACKETS)[gid("Houston", "US")]
    assert (kind, name(other)) == ("other_mouth", "Bay City")
    houston = companions.town(PACKETS[gid("Houston", "US")])
    bay_city = companions.town(PACKETS[other])
    assert companions._km(houston["mouth"], bay_city["mouth"]) >= companions.MOUTH_KM


def test_a_pair_over_the_payload_budget_is_never_chosen():
    # The fixture holds no candidate beyond Brackenheim, so Leutkirch is left alone.
    leutkirch = gid("Leutkirch", "DE")
    first = companions.choose(PACKETS)[leutkirch][2]
    asked = []

    def fits(a, b):
        asked.append((a, b))
        return first not in (a, b)

    assert leutkirch not in companions.choose(PACKETS, fits)
    assert (leutkirch, first) in asked


def test_no_companion_beyond_the_distance_limit():
    alone = {k: v for k, v in PACKETS.items() if v["town"]["en"] in ("Leutkirch", "Houston")}
    assert companions.choose(alone) == {}
