"""End-to-end check of the example towns (R20) against the real downloaded data in ../data.

Skipped when the data isn't there (it's git-ignored; run `python -m downstream.fetch` and fetch the
OSM release asset first). Expected chains were checked by hand against a map on 2026-09-28.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[2] / "data"
OSM_DIR = DATA / "raw" / "osm"
RAW_NE_OCEAN = DATA / "raw" / "ne_ocean.zip"
NEEDED = [
    DATA / "raw" / "reaches_eu.fgb",
    DATA / "raw" / "basins_l12_europe.fgb",
    OSM_DIR / "waterways-europe-germany-bayern.fgb",
    OSM_DIR / "lakes-europe-germany-bayern.fgb",
    OSM_DIR / "waterways-europe-austria.fgb",
    OSM_DIR / "waterways-europe-germany-berlin.fgb",
    RAW_NE_OCEAN,
]

# Checked by hand against a map; a leading None is "a stream" (BRIEF R6). Munich's first reach
# runs 4.8 km through the city past several channels and no name covers half of it (2026-09-28).
EXPECTED = {
    "munich": ([None, "Isar", "Danube"], "Black Sea"),
    "garmisch-partenkirchen": (["Partnach", "Loisach", "Isar", "Danube"], "Black Sea"),
    "starnberg": ([None, "Lake Starnberg", "Würm", "Amper", "Isar", "Danube"], "Black Sea"),
    "nuremberg": (["Pegnitz", "Regnitz", "Main", "Rhine"], "North Sea"),
    "cologne": (["Rhine"], "North Sea"),
    "vienna": (["Donaukanal", "Danube"], "Black Sea"),
    # Approved by the author 2026-09-28 (Austria + Germany OSM):
    "hamburg": ([None, "Norderelbe", "Elbe"], "North Sea"),
    "berlin": (["Spree", "Havel", "Jungfernsee", "Tiefer See", "Havel", "Elbe"], "North Sea"),
    "leipzig": (["Pleiße", "Weiße Elster", "Luppe", "Saale", "Elbe"], "North Sea"),
    "kiel": (["Mühlenau"], "Baltic Sea"),
    "innsbruck": (["Inn", "Danube"], "Black Sea"),
    "salzburg": (["Salzach", "Inn", "Danube"], "Black Sea"),
}


def label(group):
    n = group["name"]
    return None if n is None else n.get("en") or n.get("local")


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="real data not downloaded")
def test_example_paths():
    subprocess.run(
        [sys.executable, "-m", "downstream.paths"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
    )
    for slug, (chain, sea) in EXPECTED.items():
        r = json.loads((DATA / "paths" / f"{slug}.json").read_text())
        assert [label(g) for g in r["chain"]] == chain, slug
        assert r["end"]["type"] == "sea" and r["end"]["name"] == sea, slug
        compact = json.dumps(r, ensure_ascii=False, separators=(",", ":")).encode()
        assert len(compact) < 6000, slug  # R3
