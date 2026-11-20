"""A companion for every rotation town: the nearby town whose rain ends somewhere else (author
2026-11-20, replacing the separate pair catalogue and its 30-day planner).

Full's comparison mode shows today's town from the normal rotation plus its companion. Rules, in
order (measured on the 8,350 published towns, 2026-11-20: 99.0 % of towns get one):

1. the nearest town that drains to a different sea (`pairs.destination_group`), up to MAX_KM;
2. otherwise the nearest town that reaches the same sea at a mouth at least MOUTH_KM away
   (Texas: the Brazos and the Trinity both end in the Gulf of Mexico, at different places);
3. either way the two town dots at least 20 px apart on the smallest OG frame, so the starts can
   be told apart (calculated as MIN_GAP_PX, with margin for tall cards);
4. under CLOSE_KM both towns must pass the strict source checks (start reach within 1 km, a unique
   source basin, `pair_validation.checked_for_pairs`) and differ in source basin and outlet: a
   small start error could flip which sea it is. Further apart the normal rotation checks suffice.

No companion: the slot shows today's town alone.
"""

import bisect
import itertools
import math

from downstream.pair_validation import checked_for_pairs
from downstream.pairs import destination_group

MAX_KM = 450.0
MOUTH_KM = 150.0
MIN_GAP_PX = 24.0  # aims at 20 px on screen: margin for tall cards (replay, 2026-11-20)
CLOSE_KM = 80.0
# The map area left above Full's two cards on the OG (800 × 480 landscape, 480 × 800 portrait), in
# CSS px after the fit padding, as measured in check-map-labels.mjs over 400 live comparisons
# (2026-11-20): landscape 700 × 211–238, portrait 380 × 430–504. The low end, so tall cards pass too.
FRAMES = ((700.0, 210.0), (380.0, 430.0))
EARTH_KM = 6371.0088
MAX_ZOOM = 12  # the maps' fit limit


def _km(a, b):
    la1, la2 = math.radians(a["lat"]), math.radians(b["lat"])
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin(math.radians(b["lon"] - a["lon"]) / 2) ** 2
    )
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def _merc_y(lat):
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def town(packet):
    """What the choice needs from a rotation town file."""
    from downstream.site import decode_polyline

    points = decode_polyline(packet["polyline"])
    end = packet["end"]
    checks = packet.get("pair_checks") or {}
    return {
        "id": str(packet["town"]["geonameid"]),
        "lon": packet["town"]["lon"],
        "lat": packet["town"]["lat"],
        "group": destination_group(
            (end.get("display") or {}).get("en") or end.get("name") or end["type"]
        ),
        "mouth": {"lon": points[-1][0], "lat": points[-1][1]},
        "points": [(x, _merc_y(y)) for x, y in points],
        "checked": checked_for_pairs(packet),
        "basin": checks.get("basin_id"),
        "outlet": checks.get("outlet_reach"),
    }


def gap_px(a, b):
    """The two town dots' distance on the smallest OG frame when both paths are fitted. Like
    TRMNLMaps.fit (Framework 3.4.0), the zoom is rounded down to a whole level, so the map can be
    up to half the size a continuous fit would give; MapLibre's world is 512 px wide at zoom 0."""
    xs, ys = zip(*itertools.chain(a["points"], b["points"]), strict=True)
    width = max(xs) - min(xs) or 1e-9
    height = max(ys) - min(ys) or 1e-9
    d = math.hypot(a["lon"] - b["lon"], _merc_y(a["lat"]) - _merc_y(b["lat"]))
    gaps = []
    for w, h in FRAMES:
        zoom = max(0, min(MAX_ZOOM, math.floor(math.log2(min(w / width, h / height) * 360 / 512))))
        gaps.append(d * 512 * 2**zoom / 360)
    return min(gaps)


def candidates(primary, towns_by_lat, lats):
    """Companions for one town in rule order: (kind, km, town)."""
    band = MAX_KM / 111.0
    lo = bisect.bisect_left(lats, primary["lat"] - band)
    hi = bisect.bisect_right(lats, primary["lat"] + band)
    near = sorted(
        (_km(primary, o), o["id"], o) for o in towns_by_lat[lo:hi] if o["id"] != primary["id"]
    )
    near = [(km, o) for km, _, o in near if km <= MAX_KM]
    other = [("other_sea", km, o) for km, o in near if o["group"] != primary["group"]]
    mouths = [
        ("other_mouth", km, o)
        for km, o in near
        if o["group"] == primary["group"] and _km(primary["mouth"], o["mouth"]) >= MOUTH_KM
    ]
    for kind, km, other_town in itertools.chain(other, mouths):
        if km < CLOSE_KM and not (
            primary["checked"]
            and other_town["checked"]
            and primary["basin"] != other_town["basin"]
            and primary["outlet"] != other_town["outlet"]
        ):
            continue
        if gap_px(primary, other_town) < MIN_GAP_PX:
            continue
        yield kind, km, other_town


def choose(packets, fits=lambda a, b: True):
    """{geonameid: (kind, km, companion id)} for every town that has one. `packets` maps
    geonameid -> town file; `fits(a_id, b_id)` can veto a pair (the payload budget)."""
    towns = sorted((town(p) for p in packets.values()), key=lambda t: (t["lat"], t["id"]))
    lats = [t["lat"] for t in towns]
    chosen = {}
    for primary in towns:
        for kind, km, other in candidates(primary, towns, lats):
            if fits(primary["id"], other["id"]):
                chosen[primary["id"]] = (kind, round(km, 1), other["id"])
                break
    return chosen
