"""Estuaries: a stream that ends on the shore of a big river's estuary flows into that river.

HydroATLAS ends big rivers where their estuary begins and counts the estuary as sea, so Lisbon's
stream (34 km2) ended in the "North Atlantic Ocean" although it enters the Tagus estuary; the
Tagus outlet (70,755 km2) is 30 km upstream (2026-09-29). OpenStreetMap draws the river's line on
through the estuary to the open sea, 0.8 km from Lisbon's outlet.

Rule: an outlet gets the estuary of river R when
- an OSM `waterway=river` line within ESTUARY_DIST_M of the outlet has R's name,
- R's HydroATLAS outlet is within BIG_OUTLET_KM and drains at least BIG_RATIO times as much,
- and that OSM line goes on at least MIN_TO_SEA_KM beyond the outlet towards the sea (a stream
  that enters the sea just beside a river mouth is not in the estuary).
Output: HYRIV_ID of the outlet reach, estuary name (as in OSM), km from there to the sea.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

from downstream import reach_names
from downstream.naming import METRIC_CRS, display_key

ESTUARY_DIST_M = 3000.0
BIG_OUTLET_KM = 100.0
BIG_RATIO = 10.0
MIN_TO_SEA_KM = 3.0


def find(reaches: gpd.GeoDataFrame, names: pd.DataFrame, osm_ways: list[Path]) -> pd.DataFrame:
    """reaches: RiverATLAS with geometry; names: reach_names.csv (HYRIV_ID, name)."""
    out = reaches[(reaches["NEXT_DOWN"] == 0) & (reaches["ENDORHEIC"] == 0)]
    out = out.merge(names[["HYRIV_ID", "name"]], on="HYRIV_ID", how="left")
    ends = gpd.GeoSeries(
        [shapely.Point(g.coords[-1]) for g in out.geometry], crs="EPSG:4326", index=out.index
    )
    out = gpd.GeoDataFrame(out.drop(columns="geometry"), geometry=ends, crs="EPSG:4326")
    big = out[out["name"].notna() & (out["UPLAND_SKM"] >= 1000)]
    big_m = big.to_crs(METRIC_CRS)
    starts = [
        shapely.Point(g.coords[0])
        for g in reaches.set_index("HYRIV_ID").loc[big["HYRIV_ID"]].geometry
    ]
    big_up = gpd.GeoSeries(starts, crs="EPSG:4326").to_crs(METRIC_CRS)
    big_keys = np.array([display_key(n) for n in big["name"]], dtype=object)
    big_tree = STRtree(big_m.geometry.values)
    small_m = out.to_crs(METRIC_CRS)
    rows = []
    # Tiles of 1 degree, as in stage 1: OSM read once per tile.
    tile = np.floor(out.geometry.x).astype(int) * 1000 + np.floor(out.geometry.y).astype(int)
    for idx in out.groupby(tile).groups.values():
        sub, sub_m = out.loc[idx], small_m.loc[idx]
        # Candidate big rivers per outlet (straight-line distance first; cheap).
        si, bi = big_tree.query(sub_m.geometry.values, predicate="dwithin",
                                distance=BIG_OUTLET_KM * 1000)  # fmt: skip
        ratio = big["UPLAND_SKM"].to_numpy()[bi] / sub["UPLAND_SKM"].to_numpy()[si]
        si, bi = si[ratio >= BIG_RATIO], bi[ratio >= BIG_RATIO]
        if not len(si):
            continue
        minx, miny, maxx, maxy = sub.total_bounds
        pad = 1.0  # the river's line on to the sea may run well outside the tile
        ways = reach_names._read_bbox(osm_ways, (minx - pad, miny - pad, maxx + pad, maxy + pad))
        ways = reach_names._clean_names(ways)
        ways = ways[ways["waterway"] == "river"].to_crs(METRIC_CRS)
        if not len(ways):
            continue
        keys = np.array([display_key(n) for n in ways["name"]], dtype=object)
        for s in np.unique(si):
            p = sub_m.geometry.iloc[s]
            cands = {big_keys[b]: b for b in bi[si == s]}
            near = ways[(ways.distance(p) <= ESTUARY_DIST_M) & np.isin(keys, list(cands))]
            best = None
            for key in dict.fromkeys(keys[ways.index.get_indexer(near.index)]):
                b = cands[key]
                line = shapely.line_merge(shapely.union_all(ways.geometry.values[keys == key]))
                parts = getattr(line, "geoms", [line])
                part = min(parts, key=lambda g: g.distance(p))
                at = part.project(p)
                # Which way is the sea? Project the river's outlet and a point upstream on its
                # last reach: the sea is on the far side of the outlet from upstream.
                at_end = part.project(big_m.geometry.iloc[b])
                at_up = part.project(big_up.iloc[b])
                if abs(at_up - at_end) > 1.0:
                    sea_high = at_up < at_end
                else:  # the line only covers the estuary: it starts or ends at the outlet
                    sea_high = at_end < part.length / 2
                if sea_high != (at > at_end):
                    continue  # the outlet is upstream of the river's end, not in its estuary
                to_sea = part.length - at if sea_high else at
                if to_sea / 1000 >= MIN_TO_SEA_KM and (best is None or to_sea < best[1]):
                    best = (big["name"].iloc[b], to_sea)
            if best:
                rows.append((int(sub["HYRIV_ID"].iloc[s]), best[0], round(best[1] / 1000, 1)))
    return pd.DataFrame(rows, columns=["HYRIV_ID", "estuary", "km"])
