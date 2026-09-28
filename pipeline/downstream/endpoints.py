"""Name the end of a path: nearest Natural Earth sea/ocean area, or lake for inland ends (P4, R9)."""

import geopandas as gpd
import shapely

from downstream.naming import METRIC_CRS

SEA_CLASSES = {
    "ocean",
    "sea",
    "gulf",
    "bay",
    "strait",
    "channel",
    "sound",
    "fjord",
    "lagoon",
    "inlet",
}


def classify(
    end_lonlat, endorheic: bool, seas, lakes: gpd.GeoDataFrame, max_km: float = 25.0
) -> dict:
    """Sea by water distance for open rivers (seas.Seas); nearest named lake for inland sinks."""
    if not endorheic:
        name, km = seas.drains_into(*end_lonlat)
        if name:
            return {"type": "sea", "name": name, "featurecla": "sea", "distance_km": km}
        return {"type": "sea", "name": None, "featurecla": None, "distance_km": None}
    pt = gpd.GeoSeries([shapely.Point(end_lonlat)], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
    d = lakes.geometry.distance(pt)
    i = d.idxmin()
    if d[i] <= max_km * 1000:
        return {
            "type": "lake",
            "name": lakes.loc[i, "name"],
            "featurecla": lakes.loc[i, "featurecla"],
            "distance_km": round(d[i] / 1000, 1),
        }
    return {"type": "sink", "name": None, "featurecla": None, "distance_km": None}


# Clip before projecting: whole-ocean polygons distort in a Europe projection and then
# appear to cover Europe (found 2026-09-28: every path "ended" in the South Pacific).
EUROPE_WINDOW = (-35.0, 25.0, 60.0, 75.0)


def load_ne(path_zip, classes=None) -> gpd.GeoDataFrame:
    g = gpd.read_file(f"zip://{path_zip}")
    g = g.clip(shapely.box(*EUROPE_WINDOW))
    g.columns = [c.lower() if c != "geometry" else c for c in g.columns]
    if classes:
        g = g[g["featurecla"].str.lower().isin(classes)]
    return g[g["name"].notna()].to_crs(METRIC_CRS).reset_index(drop=True)
