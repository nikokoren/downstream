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

import json
import random
import shutil
from pathlib import Path

from downstream import regions
from downstream.locales import UI, distance_text, end_text, place_text, travel_text
from downstream.regions import DATA

SITE = DATA / "site"
RECIPE = Path(__file__).resolve().parents[2] / "recipe"
BASE_URL = "https://nikokoren.github.io/downstream"
# One folder per region (<code>/t/<n>.json), so more regions sit beside Europe without moving the
# URL existing installs use (author, 2026-09-29), one per combination of ticked regions
# ("eu-us", D23), and "mix" for all of them or none (D22: nothing ticked = a mix). Slot counts are
# fixed, ≥ the town count; the build fails if one is outgrown. Europe's 7,200 is what the Polling
# URL has used since 2026-09-29.
SLOTS = {
    "eu": 7200,
    "us": 4000,
    "ca": 600,
    "eu-us": 12000,
    "eu-ca": 8000,
    "us-ca": 4600,
    "mix": 12000,
}
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
            + f"{{%- assign n = slot | modulo: {SLOTS['eu']} -%}}"
            + BASE_URL
            + "/eu/t/{{ n }}.json\n"
        )
    url = '{%- assign r = region | join: "," -%}{%- assign k = "" -%}'
    for code in published:
        url += f'{{%- if r contains "{code}" -%}}{{%- assign k = k | append: "-{code}" -%}}{{%- endif -%}}'
    url += f'{{%- assign f = "mix" -%}}{{%- assign c = {SLOTS["mix"]} -%}}{{%- case k -%}}'
    for name in folders(published):
        if name == "mix":
            continue
        key = "".join("-" + c for c in name.split("-"))
        url += (
            f'{{%- when "{key}" -%}}{{%- assign f = "{name}" -%}}{{%- assign c = {SLOTS[name]} -%}}'
        )
    url += "{%- endcase -%}"
    return (
        url + slot + "{%- assign n = slot | modulo: c -%}" + BASE_URL + "/{{ f }}/t/{{ n }}.json\n"
    )


def _display(town: dict) -> dict:
    """A town file plus the words and pre-formatted numbers the templates show (R13): the language
    setting picks ui.en or ui.de, the units setting (metric by default) distance.<lang>.<units>."""
    result = dict(town)
    result["distance"] = distance_text(result["total_km"])
    result["travel"] = travel_text(result["travel_days"])
    result["end_text"] = end_text(result["end"])
    result["place"] = place_text(result["town"], result["town"]["cc"])
    result["ui"] = UI
    return result


# Fixed towns for previews (the marketplace screenshot follows Munich, acceptance test #1; author
# 2026-10-01): site preview/<name>.json, and a committed copy in recipe/preview/ to load by hand.
PREVIEWS = {"munich": ("eu", "2867714")}


def write_previews() -> list[Path]:
    written = []
    for name, (code, gid) in PREVIEWS.items():
        town = regions.out_dir("towns", regions.REGIONS[code]) / f"{gid}.json"
        text = json.dumps(_display(json.loads(town.read_text())), ensure_ascii=False, indent=1)
        for d in (SITE / "preview", RECIPE / "preview"):
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.json").write_text(text + "\n", encoding="utf-8")
            written.append(d / f"{name}.json")
    return written


def _write_folder(name: str, order: list[Path], cache: dict) -> None:
    out = SITE / name
    (out / "t").mkdir(parents=True)
    if len(order) > SLOTS[name]:
        raise ValueError(f"{name}: {len(order)} towns but {SLOTS[name]} slots: raise SLOTS")
    rows = ["n,geonameid,town"]
    for n in range(SLOTS[name]):
        f = order[n % len(order)]
        result = _display(cache.setdefault(f, json.loads(f.read_text())))
        result["slot"] = n
        (out / "t" / f"{n}.json").write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )
        rows.append(f'{n},{f.stem},"{result["town"]["en"]}"')
    (out / "rotation.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build() -> dict[str, int]:
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
    if SITE.exists():
        shutil.rmtree(SITE)
    cache: dict[Path, dict] = {}
    for name, order in lists.items():
        _write_folder(name, order, cache)
    write_previews()
    (SITE / "NOTICE.md").write_text(NOTICE, encoding="utf-8")
    (SITE / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Downstream</title>"
        "<p>Data files for the Downstream TRMNL recipe. "
        '<a href="NOTICE.md">Sources and licenses</a> · '
        '<a href="https://github.com/nikokoren/downstream">Source</a></p>\n',
        encoding="utf-8",
    )
    (SITE / ".nojekyll").write_text("")
    RECIPE.mkdir(exist_ok=True)
    (RECIPE / "polling_url.liquid").write_text(polling_url(published), encoding="utf-8")
    return {name: len(order) for name, order in lists.items()}


if __name__ == "__main__":
    counts = build()
    print(f"{counts} towns per folder -> {SITE}; polling URL -> {RECIPE / 'polling_url.liquid'}")
