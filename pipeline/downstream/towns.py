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
    """The region's towns (D9, D22) as a GeoDataFrame (EPSG:4326)."""
    if region.code == "eu":
        return europe_towns(raw_dir)
    if region.code == "us":
        return us_towns(raw_dir)
    if region.code == "ca":
        cities = load_cities(raw_dir / "geonames_cities15000.zip")
        return _frame({k: c for k, c in cities.items() if c["cc"] == "CA"}).reset_index(drop=True)
    raise ValueError(region.code)


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
