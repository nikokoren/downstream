"""Static files for the rotation (D8, option (a) chosen by the author 2026-09-29).

No server: TRMNL's Polling URL is a Liquid template, so it works out which town is on from the
clock and fetches that town's file from GitHub Pages:

    slot = unix time // SLOT_SECONDS, file = slot mod SLOTS

SLOTS is fixed, not the town count: GeoNames changes daily, so the count moves between builds
(6,918 locally vs 6,920 on GitHub, 2026-09-29), and a count in the URL would need a recipe update
after every build. File n holds town n mod count, so a few towns come round twice per cycle.

The towns are in a fixed shuffled order, so consecutive slots jump around Europe. Every install
shows the same town at the same time.

Usage: uv run python -m downstream.site   (after `downstream.paths --all` for each region)
Writes ../data/site/ (the Pages site: one folder per region and combination, mix/) and ../recipe/polling_url.liquid (the recipe's
Polling URL).
"""

import argparse
import json
import random
import shutil
import tempfile
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from downstream import regions
from downstream.locales import UI, distance_text, end_text, place_text, travel_text
from downstream.pair_validation import checked_for_pairs
from downstream.pairs import find_pairs, model_towns, stable_rotation_slots
from downstream.regions import DATA

SITE = DATA / "site"
RECIPE = Path(__file__).resolve().parents[2] / "recipe"
BASE_URL = "https://nikokoren.github.io/downstream"
# One folder per region (<code>/t/<n>.json), so more regions sit beside Europe without moving the
# URL existing installs use (author, 2026-09-29), one per combination of ticked regions
# ("eu-us", D23), and "mix" for all of them or none (D22: nothing ticked = a mix). Slot counts are
# fixed, ≥ the town count, about 2 % over it (GeoNames changes daily); the build fails if one is
# outgrown. Resized 2026-10-15 for D24 (author: a new Polling URL is fine); file n holds town n mod
# count, so the slots over the count show a town a second time.
SLOTS = {
    "eu": 5400,
    "us": 2900,
    "ca": 260,
    "eu-us": 8250,
    "eu-ca": 5650,
    "us-ca": 3150,
    "mix": 8500,
}
# Fixed multiples of the 288-slot/72-hour minimum. Pair IDs retain their slot across builds.
PAIR_SLOTS = {
    "eu": 2016,
    "us": 864,
    "ca": 288,
    "eu-us": 2880,
    "eu-ca": 2016,
    "us-ca": 864,
    "mix": 2880,
}
MAX_PAIR_BYTES = 6144
SLOT_SECONDS = 900  # 15 min: TRMNL's default account minimum refresh (2026-09-29)
SEED = 20260929  # fixed, so the order only changes when the set of towns changes
REGION = "eu"  # kept for the tests and tools that read the Europe folder
# Regions the published recipe offers, in Region-setting order (D22 USA, D23 Canada). The build
# checks that the site it writes matches, so a build without one fails instead of publishing a
# URL to nothing.
PUBLISHED = ["eu", "us", "ca"]


NOTICE = """# Downstream: town files

One file per rotation slot (`<region>/t/<n>.json`; `eu` is Europe): where a raindrop falling in that town ends up.

- River network: HydroATLAS (RiverATLAS v1.0), CC BY 4.0, Linke et al. 2019 and Lehner & Grill 2013.
  Changed: routing columns only, one path per town, simplified geometry.
- Lake residence-time estimates: HydroLAKES v1.0, Messager et al. 2016, CC BY 4.0.
  Changed: residence times applied to routed journeys. https://creativecommons.org/licenses/by/4.0/
- Stream, river and lake names contain information from OpenStreetMap
  (https://www.openstreetmap.org/copyright), made available under the Open Database License (ODbL)
  1.0. These files are a Derivative Database under the ODbL; the full name table is published at
  https://github.com/nikokoren/downstream/releases/tag/name-table .
- Towns: GeoNames, CC BY 4.0. Seas: Natural Earth (public domain).

Source and method: https://github.com/nikokoren/downstream
"""


def folder_of(codes: list[str], published: list[str] | None = None) -> str:
    """The site folder for a set of ticked regions: one region its own, all or none "mix"."""
    published = published or PUBLISHED
    ticked = [c for c in published if c in codes]
    if not ticked or len(ticked) == len(published):
        return "mix"
    return "-".join(ticked)


def folders(published: list[str] | None = None) -> list[str]:
    """Every folder the site needs for these regions."""
    from itertools import combinations

    published = published or PUBLISHED
    out = []
    for k in range(1, len(published) + 1):
        for combo in combinations(published, k):
            out.append(folder_of(list(combo), published))
    return out


def polling_url(published: list[str] | None = None) -> str:
    """The recipe's Polling URL. One line: TRMNL splits the rendered URL field on line breaks.

    Europe only: the URL used since 2026-09-29. With more regions, the Region setting (form field
    `region`, multi-select) picks the folder for the ticked ones; none or all ticked picks "mix".
    `join` makes the value text whether TRMNL passes a list or comma-separated text
    (undocumented, 2026-10-01). Region codes must not contain each other ("eu", "us", "ca").
    """
    published = published or PUBLISHED
    slot = '{%- assign slot = "now" | date: "%s" | divided_by: ' + str(SLOT_SECONDS) + " -%}"
    if published == ["eu"]:
        return (
            slot
            + f"{{%- assign c = {SLOTS['eu']} -%}}{{%- assign p = {PAIR_SLOTS['eu']} -%}}"
            + _pair_url_switch()
            + "{%- assign n = slot | modulo: c -%}"
            + BASE_URL
            + "/eu/{{ mode }}/{{ n }}.json\n"
        )
    url = '{%- assign r = region | join: "," -%}{%- assign k = "" -%}'
    for code in published:
        url += f'{{%- if r contains "{code}" -%}}{{%- assign k = k | append: "-{code}" -%}}{{%- endif -%}}'
    url += (
        f'{{%- assign f = "mix" -%}}{{%- assign c = {SLOTS["mix"]} -%}}'
        f"{{%- assign p = {PAIR_SLOTS['mix']} -%}}{{%- case k -%}}"
    )
    for name in folders(published):
        if name == "mix":
            continue
        key = "".join("-" + c for c in name.split("-"))
        url += (
            f'{{%- when "{key}" -%}}{{%- assign f = "{name}" -%}}{{%- assign c = {SLOTS[name]} -%}}'
            f"{{%- assign p = {PAIR_SLOTS[name]} -%}}"
        )
    url += "{%- endcase -%}"
    return (
        url
        + _pair_url_switch()
        + slot
        + "{%- assign n = slot | modulo: c -%}"
        + BASE_URL
        + "/{{ f }}/{{ mode }}/{{ n }}.json\n"
    )


def _pair_url_switch():
    return (
        '{%- assign mode = "t" -%}'
        '{%- if watershed_pairs == true or watershed_pairs == "true" or watershed_pairs == "yes" -%}'
        '{%- assign mode = "p" -%}{%- assign c = p -%}{%- endif -%}'
    )


def _display(town: dict) -> dict:
    """A town file plus the words and pre-formatted numbers the templates show (R13): the language
    setting picks ui.en or ui.de, the units setting (metric by default) distance.<lang>.<units>."""
    result = dict(town)
    result.pop("pair_checks", None)  # Build evidence is not product copy or polling payload.
    result["distance"] = distance_text(result["total_km"])
    result["travel"] = (
        travel_text(result["travel_days"])
        if result.get("travel_days") is not None
        else {lang: words["travel_unavailable"] for lang, words in UI.items()}
    )
    result["end_text"] = end_text(result["end"])
    result["place"] = place_text(result["town"], result["town"]["cc"])
    result["ui"] = UI
    return result


# Fixed towns for previews (the marketplace screenshot follows Munich, acceptance test #1; author
# 2026-10-01): site preview/<name>.json, and a committed copy in recipe/preview/ to load by hand.
PREVIEWS = {"munich": ("eu", "2867714")}


def write_previews(site=SITE, write_recipe=True) -> list[Path]:
    written = []
    for name, (code, gid) in PREVIEWS.items():
        town = regions.out_dir("towns", regions.REGIONS[code]) / f"{gid}.json"
        text = json.dumps(_display(json.loads(town.read_text())), ensure_ascii=False, indent=1)
        destinations = [site / "preview"]
        if write_recipe:
            destinations.append(RECIPE / "preview")
        for d in destinations:
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.json").write_text(text + "\n", encoding="utf-8")
            written.append(d / f"{name}.json")
    return written


def _write_folder(name: str, order: list[Path], cache: dict, site=SITE) -> None:
    out = site / name
    (out / "t").mkdir(parents=True)
    if len(order) > SLOTS[name]:
        raise ValueError(f"{name}: {len(order)} towns but {SLOTS[name]} slots: raise SLOTS")
    rows = ["n,geonameid,town"]
    for n in range(SLOTS[name]):
        f = order[n % len(order)]
        result = _display(_town(f, cache))
        result["slot"] = n
        (out / "t" / f"{n}.json").write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )
        rows.append(f'{n},{f.stem},"{result["town"]["en"]}"')
    (out / "rotation.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _town(path, cache):
    if path not in cache:
        cache[path] = json.loads(path.read_text())
    return cache[path]


def _wire_name(name):
    if not name:
        return None
    base = name.get("local") or name.get("en") or name.get("de")
    return {
        "local": base,
        **{lang: name[lang] for lang in ("en", "de") if name.get(lang) and name[lang] != base},
    }


def pair_packet(first, second):
    """Both original cards and model geometry, one UI block, without unused build fields."""
    routes = []
    for raw in (first, second):
        town = _display(raw)
        route = {k: town[k] for k in ("place", "distance", "travel", "end_text", "polyline")}
        route["town"] = {k: town["town"][k] for k in ("geonameid", "en", "de", "cc", "lon", "lat")}
        route["end"] = {k: town["end"].get(k) for k in ("type", "name", "display")}
        route["chain"] = [{"kind": s["kind"], "name": _wire_name(s["name"])} for s in town["chain"]]
        route["changes"] = [
            {"at": c["at"], "from": _wire_name(c["from"]), "to": _wire_name(c["to"])}
            for c in town.get("changes", [])
        ]
        routes.append(route)
    return {"ui": UI, "routes": routes}


def _compact(packet):
    return json.dumps(packet, ensure_ascii=False, separators=(",", ":"))


def _write_pair_folder(name, order, cache, previous, site=SITE):
    out = site / name / "p"
    out.mkdir(parents=True)
    good = set()
    rejected = Counter()
    for file in order:
        packet = _town(file, cache)
        if packet["end"]["type"] != "sea":
            continue
        if "pair_checks" not in packet:
            raise ValueError(
                f"missing source verification: {file}; run paths or pair_validation first"
            )
        if checked_for_pairs(packet):
            good.add(file)
        else:
            rejected.update(packet["pair_checks"].get("issues") or ["invalid_source_proof"])
    towns = [
        t for t in model_towns(sorted({f.parent for f in order})) if Path(t["model_file"]) in good
    ]
    candidates = find_pairs(towns)
    packets, approved = {}, []
    for pair in candidates:
        a, b = [_town(Path(t["model_file"]), cache) for t in pair["towns"]]
        qa, qb = a["pair_checks"], b["pair_checks"]
        if qa["outlet_reach"] == qb["outlet_reach"] or qa["basin_id"] == qb["basin_id"]:
            rejected["pair_shares_source_basin_or_outlet"] += 1
            continue
        packet = pair_packet(a, b)
        # Allow for the largest slot index before accepting a packet into the catalogue.
        packet["slot"] = PAIR_SLOTS[name] - 1
        if len(_compact(packet).encode()) > MAX_PAIR_BYTES:
            rejected["pair_payload_over_6144_bytes"] += 1
            continue
        packets[pair["id"]] = packet
        approved.append(pair)
    slots = stable_rotation_slots(approved, PAIR_SLOTS[name], previous)
    maximum = 0
    for index, pid in enumerate(slots):
        if pid in packets:
            result = {**packets[pid], "slot": index}
        else:
            result = _display(_town(order[index % len(order)], cache))
            result["slot"] = index
        text = _compact(result)
        maximum = max(maximum, len(text.encode()))
        (out / f"{index}.json").write_text(text)
    (out / "plan.json").write_text(_compact({"version": 1, "slots": slots}) + "\n")
    report = {
        "version": 1,
        "max_town_distance_km": 80,
        "source_checked_towns": len(good),
        "pairs": len(approved),
        "slots": len(slots),
        "slot_minutes": 15,
        "minimum_repeat_hours": 72,
        "reserved_pair_ids": sum(pid is not None for pid in slots),
        "normal_town_slots": sum(pid not in packets for pid in slots),
        "maximum_payload_bytes": maximum,
        "rejected": dict(rejected),
        "pair_ids": [p["id"] for p in approved],
    }
    (out / "catalogue.json").write_text(_compact(report) + "\n")
    return report


def previous_plans(url=None):
    """A missing root manifest means the first launch; partial/history failures stop the build."""

    def read(path):
        if url:
            with urllib.request.urlopen(url.rstrip("/") + "/" + path, timeout=25) as response:
                return json.load(response)
        return json.loads((SITE / path).read_text())

    try:
        manifest = read("pair-feed.json")
    except FileNotFoundError:
        return {}
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return {}
        raise
    if manifest.get("version") != 1 or manifest.get("capacities") != PAIR_SLOTS:
        raise ValueError("previous pair feed has an incompatible version or capacity")
    return {name: read(f"{name}/p/plan.json")["slots"] for name in manifest["folders"]}


def build(previous=None) -> dict[str, int]:
    """Every published region with town files (data/towns/<code>/), plus a folder for each
    combination of them (D23)."""
    files = {}
    for code in PUBLISHED:
        found = sorted(
            regions.out_dir("towns", regions.REGIONS[code]).glob("*.json"),
            key=lambda p: int(p.stem),
        )
        if found:
            files[code] = found
    if not files:
        raise ValueError("no town files: run `downstream.paths --all` first")
    published = [c for c in PUBLISHED if c in files]
    lists = {}
    for name in folders(published):
        codes = published if name == "mix" else name.split("-")
        order = sorted((f for c in codes for f in files[c]), key=lambda p: int(p.stem))
        random.Random(SEED).shuffle(order)
        lists[name] = order
    previous = previous_plans() if previous is None else previous
    # A failed source check/build must not destroy the previous stable slot assignments.
    SITE.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="site-build-", dir=SITE.parent))
    try:
        cache: dict[Path, dict] = {}
        for name, order in lists.items():
            _write_folder(name, order, cache, staging)
        reports = {
            name: _write_pair_folder(name, order, cache, previous.get(name), staging)
            for name, order in lists.items()
        }
        (staging / "pair-feed.json").write_text(
            _compact(
                {
                    "version": 1,
                    "capacities": PAIR_SLOTS,
                    "folders": list(lists),
                    "pairs": {name: report["pairs"] for name, report in reports.items()},
                }
            )
            + "\n"
        )
        write_previews(staging, write_recipe=False)
        (staging / "NOTICE.md").write_text(NOTICE, encoding="utf-8")
        (staging / "index.html").write_text(
            "<!doctype html><meta charset=utf-8><title>Downstream</title>"
            "<p>Data files for the Downstream TRMNL recipe. "
            '<a href="NOTICE.md">Sources and licenses</a> · '
            '<a href="https://github.com/nikokoren/downstream">Source</a></p>\n',
            encoding="utf-8",
        )
        (staging / ".nojekyll").write_text("")
        backup = None
        if SITE.exists():
            backup = Path(tempfile.mkdtemp(prefix="site-previous-", dir=SITE.parent))
            backup.rmdir()
            SITE.rename(backup)
        try:
            staging.rename(SITE)
        except OSError:
            if backup:
                backup.rename(SITE)
            raise
        if backup:
            shutil.rmtree(backup)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    write_previews(SITE)
    RECIPE.mkdir(exist_ok=True)
    (RECIPE / "polling_url.liquid").write_text(polling_url(published), encoding="utf-8")
    return {name: len(order) for name, order in lists.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--previous-plans", help="Previously deployed site URL; preserve pair slots"
    )
    args = parser.parse_args()
    counts = build(previous_plans(args.previous_plans) if args.previous_plans else None)
    print(f"{counts} towns per folder -> {SITE}; polling URL -> {RECIPE / 'polling_url.liquid'}")
