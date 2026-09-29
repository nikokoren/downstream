"""Static files for the rotation (D8, option (a) chosen by the author 2026-09-29).

No server: TRMNL's Polling URL is a Liquid template, so it works out which town is on from the
clock and fetches that town's file from GitHub Pages:

    slot = unix time // SLOT_SECONDS, file = slot mod SLOTS

SLOTS is fixed, not the town count: GeoNames changes daily, so the count moves between builds
(6,918 locally vs 6,920 on GitHub, 2026-09-29), and a count in the URL would need a recipe update
after every build. File n holds town n mod count, so a few towns come round twice per cycle.

The towns are in a fixed shuffled order, so consecutive slots jump around Europe. Every install
shows the same town at the same time.

Usage: uv run python -m downstream.site   (after `downstream.paths --all`)
Writes ../data/site/ (the Pages site; Europe under eu/) and ../recipe/polling_url.liquid (the recipe's Polling URL).
"""

import json
import random
import shutil
from pathlib import Path

from downstream.fetch import RAW

SITE = RAW.parent / "site"
RECIPE = Path(__file__).resolve().parents[2] / "recipe"
BASE_URL = "https://nikokoren.github.io/downstream"
# Files live under a region folder (eu/t/<n>.json) so more regions, or an "everything" list, can
# sit beside Europe later without moving the URL existing installs use (author, 2026-09-29).
REGION = "eu"
SLOTS = 7200  # ≥ town count; the build fails if the towns ever outgrow it
SLOT_SECONDS = 900  # 15 min: TRMNL's default account minimum refresh (2026-09-29)
SEED = 20260929  # fixed, so the order only changes when the set of towns changes

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


def polling_url(n: int = SLOTS) -> str:
    """The recipe's Polling URL. One line: TRMNL splits the rendered URL field on line breaks."""
    return (
        '{%- assign slot = "now" | date: "%s" | divided_by: ' + str(SLOT_SECONDS) + " -%}"
        "{%- assign n = slot | modulo: "
        + str(n)
        + " -%}"
        + BASE_URL
        + f"/{REGION}/t/{{{{ n }}}}.json\n"
    )


def build() -> int:
    towns = sorted((RAW.parent / "towns").glob("*.json"), key=lambda p: int(p.stem))
    order = list(towns)
    random.Random(SEED).shuffle(order)
    if SITE.exists():
        shutil.rmtree(SITE)
    out = SITE / REGION
    (out / "t").mkdir(parents=True)
    if len(order) > SLOTS:
        raise ValueError(f"{len(order)} towns but {SLOTS} slots: raise SLOTS (and the recipe URL)")
    rows = ["n,geonameid,town"]
    cache: dict[Path, dict] = {}
    for n in range(SLOTS):
        f = order[n % len(order)]
        result = dict(cache.setdefault(f, json.loads(f.read_text())))
        result["slot"] = n
        (out / "t" / f"{n}.json").write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )
        rows.append(f'{n},{f.stem},"{result["town"]["en"]}"')
    (out / "rotation.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
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
    (RECIPE / "polling_url.liquid").write_text(polling_url(), encoding="utf-8")
    return len(order)


if __name__ == "__main__":
    n = build()
    print(
        f"{n} towns in {SLOTS} slot files -> {SITE}; polling URL -> {RECIPE / 'polling_url.liquid'}"
    )
