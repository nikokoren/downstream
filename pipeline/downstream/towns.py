"""Towns from GeoNames cities15000 plus the author's extra towns, with English and German names (D9)."""

import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path

CITY_COLS = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "lat",
    "lon",
    "fclass",
    "fcode",
    "cc",
    "cc2",
    "a1",
    "a2",
    "a3",
    "a4",
    "pop",
    "elev",
    "dem",
    "tz",
    "modified",
]


def load_cities(zip_path: Path) -> dict[str, dict]:
    with zipfile.ZipFile(zip_path) as z, z.open("cities15000.txt") as f:
        rows = csv.reader(
            io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE
        )
        return {r[0]: dict(zip(CITY_COLS, r, strict=True)) for r in rows}


EXTRA_TOWNS = Path(__file__).with_name("extra_towns.csv")


def extra_town_ids() -> dict[str, str]:
    """geonameid -> country code for the author's extra towns."""
    lines = [
        x for x in EXTRA_TOWNS.read_text(encoding="utf-8").splitlines() if not x.startswith("#")
    ]
    return {r["geonameid"]: r["cc"] for r in csv.DictReader(lines)}


def load_extra_towns(raw_dir: Path) -> dict[str, dict]:
    """The extra towns' rows from the GeoNames country dumps (same columns as cities15000)."""
    wanted = extra_town_ids()
    out = {}
    for cc in sorted(set(wanted.values())):
        with zipfile.ZipFile(raw_dir / f"geonames_{cc}.zip") as z, z.open(f"{cc}.txt") as f:
            rows = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE
            )
            out |= {r[0]: dict(zip(CITY_COLS, r, strict=True)) for r in rows if r[0] in wanted}
    missing = set(wanted) - set(out)
    if missing:
        raise ValueError(f"extra towns not found in the GeoNames dumps: {sorted(missing)}")
    return out


def load_alt_names(path: Path, ids: set[str]) -> dict[str, dict[str, list]]:
    """geonameid -> lang -> [(name, preferred, short, colloquial, historic)]."""
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[1] in ids and p[2] in ("de", "en"):
                flags = [x == "1" for x in p[4:8]]
                out[p[1]][p[2]].append((p[3], *flags))
    return out


def pick_name(town: dict, alts: dict[str, list], lang: str) -> str:
    """Preferred alternate name, else first plain one, else GeoNames `name` (D9)."""
    usable = [a for a in alts.get(lang, []) if not a[3] and not a[4]]  # not colloquial/historic
    for a in usable:
        if a[1]:
            return a[0]
    for a in usable:
        if not a[2]:
            return a[0]
    return town["name"]


def region_towns(raw_dir: Path, region):
    """The region's towns (D9, D22) as a GeoDataFrame (EPSG:4326), thinned around cities (D24)."""
    if region.code == "eu":
        found = europe_towns(raw_dir)
    elif region.code == "us":
        found = us_towns(raw_dir)
    elif region.code == "ca":
        cities = load_cities(raw_dir / "geonames_cities15000.zip")
        found = _frame({k: c for k, c in cities.items() if c["cc"] == "CA"})
    else:
        raise ValueError(region.code)
    return found[~near_city(found, set(extra_town_ids()))].reset_index(drop=True)


# D24 (author 2026-10-15): a better mix of town and country. cities15000 lists city districts
# (feature code PPLX: Pasing in Munich, Albany Park in Chicago) and dense rings of suburbs as
# towns of their own; the rotation shows the city instead.
CITY_POP = 100_000  # a city: a no-go zone around it for smaller towns
ZONE_KM_AT_CITY_POP = 3.0  # zone radius 3 km × √(population / 100,000): Munich 1.26 M → 10.6 km
ZONE_MAX_KM = 30.0
KEEP_POP = 250_000  # never dropped for a zone: Aurora by Denver, Mississauga by Toronto
# Boroughs over KEEP_POP that GeoNames doesn't mark PPLX (found 2026-10-15 by listing places over
# 250,000 inside a bigger city's zone); the city itself stays.
DISTRICTS = {
    "5110266": "The Bronx",
    "5110302": "Brooklyn",
    "5125771": "Manhattan",
    "5133273": "Queens",
    "5139568": "Staten Island",
    "2646003": "Islington",
    "5950268": "Etobicoke",
}


def near_city(df, keep: set[str]):
    """Boolean Series: towns to drop. City districts (PPLX and DISTRICTS), and towns under
    KEEP_POP inside a bigger city's zone. Towns in `keep` (the author's extra towns) always stay."""
    import numpy as np
    import pandas as pd

    pop = df["pop"].to_numpy()
    lat = np.radians(df["lat"].to_numpy())
    lon = np.radians(df["lon"].to_numpy())
    district = ((df["fcode"] == "PPLX") | df["geonameid"].isin(DISTRICTS)).to_numpy()
    drop = district.copy()
    for i in np.flatnonzero((pop >= CITY_POP) & ~district):
        radius = min(ZONE_MAX_KM, ZONE_KM_AT_CITY_POP * (pop[i] / CITY_POP) ** 0.5)
        a = (
            np.sin((lat - lat[i]) / 2) ** 2
            + np.cos(lat) * np.cos(lat[i]) * np.sin((lon - lon[i]) / 2) ** 2
        )
        km = 12_742 * np.arcsin(np.sqrt(a))  # haversine, Earth's mean diameter
        drop |= (km < radius) & (pop < pop[i]) & (pop < KEEP_POP)
    drop &= ~df["geonameid"].isin(keep).to_numpy()
    return pd.Series(drop, index=df.index)


def _frame(cities: dict):
    import geopandas as gpd

    df = gpd.GeoDataFrame(list(cities.values()))
    df["lon"] = df["lon"].astype(float)
    df["lat"] = df["lat"].astype(float)
    df["pop"] = df["pop"].astype(int)
    return df.set_geometry(gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")


def us_towns(raw_dir: Path):
    """cities15000 towns in the United States without Hawaii (D22: no HydroATLAS coverage).
    GeoNames lists Puerto Rico and the other territories under their own country codes."""
    cities = load_cities(raw_dir / "geonames_cities15000.zip")
    us = {k: c for k, c in cities.items() if c["cc"] == "US" and c["a1"] != "HI"}
    return _frame(us).reset_index(drop=True)


def europe_towns(raw_dir: Path):
    """cities15000 towns plus the extra towns, inside the Europe border (D9), as a GeoDataFrame
    (EPSG:4326)."""

    from downstream.europe import Europe

    cities = load_cities(raw_dir / "geonames_cities15000.zip") | load_extra_towns(raw_dir)
    df = _frame(cities)
    inside = Europe(raw_dir / "ne_admin0.zip").contains(df)
    return df[inside].reset_index(drop=True)
