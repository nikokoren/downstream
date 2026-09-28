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
    end_lonlat,
    endorheic: bool,
    marine: gpd.GeoDataFrame,
    lakes: gpd.GeoDataFrame,
    max_km: float = 25.0,
) -> dict:
    pt = gpd.GeoSeries([shapely.Point(end_lonlat)], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
    layers = [("lake", lakes)] if endorheic else [("sea", marine), ("lake", lakes)]
    best = None
    for kind, layer in layers:
        d = layer.geometry.distance(pt)
        i = d.idxmin()
        if d[i] <= max_km * 1000 and (best is None or d[i] < best[2]):
            best = (kind, layer.loc[i], d[i])
    if best is None:
        return {"type": "sink" if endorheic else "unknown", "name": None, "distance_km": None}
    kind, row, dist = best
    return {
        "type": kind,
        "name": row["name"],
        "featurecla": row.get("featurecla"),
        "distance_km": round(dist / 1000, 1),
    }


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
