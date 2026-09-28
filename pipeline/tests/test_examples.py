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
OSM = DATA / "raw" / "osm_waterways_bayern.fgb"
NEEDED = [DATA / "raw" / "reaches_eu.fgb", DATA / "raw" / "basins_l12_europe.fgb", OSM]

EXPECTED = {
    "munich": (["Isar", "Danube", "Bratul Chillia"], "Black Sea"),
    "garmisch-partenkirchen": (
        ["Partnach", "Loisach", "Isar", "Danube", "Bratul Chillia"],
        "Black Sea",
    ),
    "starnberg": ([None, "Würm", "Amper", "Isar", "Danube", "Bratul Chillia"], "Black Sea"),
    "nuremberg": (["Pegnitz", "Regnitz", "Main", "Rhine", "Lek"], "North Sea"),
    "cologne": (["Rhine", "Lek"], "North Sea"),
    "vienna": ([None, "Danube", "Bratul Chillia"], "Black Sea"),
}


def label(group):
    n = group["name"]
    return None if n is None else n.get("en") or n.get("local")


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="real data not downloaded")
def test_example_paths():
    subprocess.run(
        [sys.executable, "-m", "downstream.paths", str(OSM)],
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
