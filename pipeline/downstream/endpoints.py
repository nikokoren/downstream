"""Name the end of a path: nearest Natural Earth sea/ocean area, or lake for inland ends (P4, R9)."""

import geopandas as gpd
import shapely

from downstream import regions
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
    end_lonlat, endorheic: bool, seas, lakes: gpd.GeoDataFrame, max_km: float = 2.0
) -> dict:
    """Sea by water distance for open rivers (seas.Seas); for inland endings, a named lake within
    max_km, else an unnamed inland sink. (Was 25 km: Cetinje's karst sink became "Lake Skadar",
    which drains to the Adriatic; 2026-09-29.) paths.py first prefers a lake the path itself
    ends in."""
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


# Clip before projecting: whole-ocean polygons distort in a regional projection and then
# appear to cover the region (found 2026-09-28: every path "ended" in the South Pacific).
NE_WINDOW = regions.current().ne_window


def load_ne(path_zip, classes=None) -> gpd.GeoDataFrame:
    g = gpd.read_file(f"zip://{path_zip}")
    # Repair only invalid shapes (a North American one broke the clip, 2026-10-01); valid ones,
    # all of Europe's, are left exactly as they are.
    bad = ~g.is_valid
    if bad.any():
        g.loc[bad, "geometry"] = g.loc[bad, "geometry"].make_valid()
    g = g.clip(shapely.box(*NE_WINDOW))
    g.columns = [c.lower() if c != "geometry" else c for c in g.columns]
    if classes:
        g = g[g["featurecla"].str.lower().isin(classes)]
    return g[g["name"].notna()].to_crs(METRIC_CRS).reset_index(drop=True)
