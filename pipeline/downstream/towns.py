"""Towns from GeoNames cities15000 with English and German names (D9)."""

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


def europe_towns(raw_dir: Path):
    """cities15000 towns inside the Europe border (D9), as a GeoDataFrame (EPSG:4326)."""
    import geopandas as gpd

    from downstream.europe import Europe

    cities = load_cities(raw_dir / "geonames_cities15000.zip")
    df = gpd.GeoDataFrame(list(cities.values()))
    df["lon"] = df["lon"].astype(float)
    df["lat"] = df["lat"].astype(float)
    df["pop"] = df["pop"].astype(int)
    df = df.set_geometry(gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
    inside = Europe(raw_dir / "ne_admin0.zip").contains(df)
    return df[inside].reset_index(drop=True)
