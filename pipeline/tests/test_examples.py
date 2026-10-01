"""End-to-end check of the example towns (R20) against the real downloaded data in ../data.

Skipped when the data isn't there (it's git-ignored; run `python -m downstream.fetch` and fetch the
OSM release asset first). Expected chains were checked by hand against a map on 2026-09-28.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from downstream.naming import name_key

DATA = Path(__file__).resolve().parents[2] / "data"
OSM_DIR = DATA / "raw" / "osm"
RAW_NE_OCEAN = DATA / "raw" / "ne_ocean.zip"
NEEDED = [
    DATA / "raw" / "reaches_eu.fgb",
    DATA / "raw" / "basins_l12_eu.fgb",
    OSM_DIR / "waterways-europe-germany-bayern.fgb",
    OSM_DIR / "lakes-europe-germany-bayern.fgb",
    OSM_DIR / "waterways-europe-austria.fgb",
    OSM_DIR / "waterways-europe-germany-berlin.fgb",
    OSM_DIR / "waterways-europe-croatia.fgb",
    OSM_DIR / "waterways-europe-hungary.fgb",
    OSM_DIR / "waterways-europe-slovenia.fgb",
    OSM_DIR / "waterways-europe-italy-nord-est.fgb",
    OSM_DIR / "waterways-europe-portugal.fgb",
    DATA / "names" / "eu" / "estuaries.csv",
    RAW_NE_OCEAN,
    DATA / "names" / "eu" / "reach_names.csv",  # from `python -m downstream.build_names`
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
    # Per-river redesign (2026-09-29): the start reach is the last 3.7 km of a river OSM names
    # Alster for 20.6 km just upstream, so it's now "Alster". Confirmed by the author 2026-09-29.
    "hamburg": (["Alster", "Norderelbe", "Elbe"], "North Sea"),
    "berlin": (["Spree", "Havel", "Jungfernsee", "Tiefer See", "Havel", "Elbe"], "North Sea"),
    "leipzig": (["Pleiße", "Weiße Elster", "Luppe", "Saale", "Elbe"], "North Sea"),
    "kiel": (["Mühlenau"], "Baltic Sea"),
    "innsbruck": (["Inn", "Danube"], "Black Sea"),
    "salzburg": (["Salzach", "Inn", "Danube"], "Black Sea"),
    # Approved by the author 2026-09-28 (after the tunnel re-extraction and OSM SI/HR/HU):
    "graz": ([None, "Mur", "Drava", "Danube"], "Black Sea"),
    "stuttgart": ([None, "Neckar", "Rhine"], "North Sea"),
    # 2026-09-29: were "Eisack - Isarco → Fossa di Laives - Leiferergraben → Fossa Grande →
    # Etsch - Adige" (ditches beside the Adige) and "Tolminka → Soča → Isonzo / Soča / Lusinç".
    "bolzano": (["Eisack - Isarco", "Etsch - Adige"], "Adriatic Sea"),
    "tolmin": (["Tolminka", "Soča"], "Adriatic Sea"),
    # 2026-09-29: was "(stream)" only; the stream enters the Tagus estuary, which HydroATLAS
    # counts as sea.
    "lisbon": ([None, "Tagus"], "North Atlantic Ocean"),
    # 2026-09-30: were "River Cam → River Great Ouse or Ely Ouse → Great Ouse or Ten Mile River →
    # Great Ouse Relief Channel → River Great Ouse" and "... → Río Guadaira → Río Guadaíra → ...".
    "cambridge": (["River Cam", "River Great Ouse"], "North Sea"),
    "el-viso-del-alcor": (
        ["Arroyo de la Alcantarilla", "Arroyo del Salado", "Río Guadaíra", "Río Guadalquivir"],
        "North Atlantic Ocean",
    ),
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
        r = json.loads((DATA / "paths" / "eu" / f"{slug}.json").read_text())
        # Compared like the pipeline compares names (case and accents ignored): which spelling of
        # a river covers more km changes with OSM edits ("Río Guadaíra" here, "Río Guadaira" on
        # GitHub's fresh OSM download, build 18, 2026-09-30); the step structure is what's locked.
        assert [name_key(label(g)) for g in r["chain"]] == [name_key(c) for c in chain], slug
        assert r["end"]["type"] == "sea" and r["end"]["name"] == sea, slug
        compact = json.dumps(r, ensure_ascii=False, separators=(",", ":")).encode()
        assert len(compact) < 6000, slug  # R3


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="real data not downloaded")
def test_name_table_is_written_with_notice():
    # Written by `python -m downstream.build_names` (network-wide since 2026-09-29).
    import csv

    table = DATA / "names" / "eu" / "name_table" / "name_table.csv"
    with open(table, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    names = {r["name"] for r in rows}
    assert {"Isar", "Würm", "Starnberger See"} <= names
    assert {r["source"] for r in rows} <= {
        "osm",
        "osm:canal",
        "naturalearth",
        "lake:osm",
        "lake:naturalearth",
    }
    notice = (table.parent / "NOTICE.md").read_text(encoding="utf-8")
    assert "Open Database License" in notice and "openstreetmap.org/copyright" in notice


TOWNS = DATA / "towns" / "eu"


@pytest.mark.skipif(not TOWNS.exists(), reason="run `python -m downstream.paths --all` first")
def test_every_sea_endpoint_has_a_german_name():
    # D7: German names only from the curated table, so every sea a town can end in needs a row.
    missing = {}
    for f in TOWNS.glob("*.json"):
        end = json.loads(f.read_text())["end"]
        if end["type"] == "sea" and not (end.get("display") or {}).get("de"):
            missing[end["name"]] = missing.get(end["name"], 0) + 1
    assert not missing, missing


@pytest.mark.skipif(not TOWNS.exists(), reason="run `python -m downstream.paths --all` first")
def test_lake_time_counts_lakes_on_the_path_only():
    # 2026-09-30 build: Lake Constance's Res_time is 1,626 days (HydroLAKES); Konstanz drains
    # through it. Geneva sits at Lake Geneva's outlet, below the lake. Basel is below Constance.
    towns = {}
    for f in TOWNS.glob("*.json"):
        d = json.loads(f.read_text())
        towns.setdefault(d["town"]["en"], d)
    assert 1500 < towns["Konstanz"]["lake_days"] < 1800
    assert towns["Geneva"]["lake_days"] < 30
    assert towns["Basel"]["lake_days"] < 30


@pytest.mark.skipif(not TOWNS.exists(), reason="run `python -m downstream.paths --all` first")
def test_every_sea_endpoint_has_a_phrase():
    # "Ends in the Black Sea" / "Endet im Schwarzen Meer" (D20): each sea needs its article and case.
    from downstream.locales import END_PHRASES

    missing = set()
    for f in TOWNS.glob("*.json"):
        end = json.loads(f.read_text())["end"]
        if end["type"] == "sea" and (end.get("display") or {}).get("en") not in END_PHRASES:
            missing.add(end["name"])
    assert not missing, missing
