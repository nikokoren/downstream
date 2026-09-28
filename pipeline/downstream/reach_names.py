"""Name every river segment once, region by region (per-river redesign, 2026-09-28).

Stage 1 of the network naming: the raw name of each reach, independent of any path. Same rules as
`naming.NameSource.vote` / `naming._first_name` / `naming.mark_lakes`, vectorised per 1° tile:
- OSM first (600 m): natural rivers vote first; if no river name covers >= 50 % of the sample
  points, all lines vote with weights river 1, canal 1.5, other 2. Tunnelled ways are skipped.
- Where OSM has any line within 600 m but no name wins, the reach stays unnamed (OSM is
  authoritative); Natural Earth (3 km, weighted by scalerank) only where OSM has nothing nearby.
- A reach at least 50 % and 500 m inside a named lake becomes that lake (OSM lakes first, then
  Natural Earth lakes).
"""

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely import STRtree

from downstream.naming import METRIC_CRS

SAMPLE_M = 200
OSM_DIST, NE_DIST = 600.0, 3000.0
MIN_SHARE = 0.5
LAKE_SHARE, LAKE_MIN_M = 0.5, 500.0
OSM_WEIGHTS = {"river": 1.0, "canal": 1.5}  # everything else 2.0


def sample_points(geoms: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Points every ~200 m (at least 3) along each reach: (points, owner reach index, n per reach)."""
    lengths = shapely.length(geoms)
    n = np.maximum(3, (lengths // SAMPLE_M).astype(int) + 1)
    owner = np.repeat(np.arange(len(geoms)), n)
    frac = np.concatenate([np.linspace(0, 1, k) for k in n]) if len(n) else np.array([])
    pts = shapely.line_interpolate_point(geoms[owner], frac, normalized=True)
    return pts, owner, n


def _nearest_by_class(pts, classes: list[tuple[np.ndarray, np.ndarray, float]], max_dist):
    """classes: (geometries, names, weight). Best line per point by distance x weight."""
    best_eff = np.full(len(pts), np.inf)
    best_name = np.full(len(pts), None, dtype=object)
    for geoms, names, w in classes:
        if len(geoms) == 0:
            continue
        tree = STRtree(geoms)
        (pi, gi), d = tree.query_nearest(
            pts, max_distance=max_dist, return_distance=True, all_matches=False
        )
        eff = d * w
        better = eff < best_eff[pi]
        best_eff[pi[better]] = eff[better]
        best_name[pi[better]] = names[gi[better]]
    return best_name


def _majority(owner, names, n, min_share) -> dict[int, str]:
    ok = pd.notna(names)
    if not ok.any():
        return {}
    df = pd.DataFrame({"r": owner[ok], "name": names[ok]})
    counts = df.groupby(["r", "name"]).size().reset_index(name="c")
    counts = counts.sort_values(["r", "c", "name"], ascending=[True, False, True])
    top = counts.drop_duplicates("r")
    top = top[top["c"] / n[top["r"]] >= min_share]
    return dict(zip(top["r"], top["name"], strict=True))


def vote_osm(geoms, lines: gpd.GeoDataFrame) -> tuple[dict[int, str], dict[int, bool], np.ndarray]:
    """Per reach index: name, canal flag; plus covered mask (any line within OSM_DIST)."""
    pts, owner, n = sample_points(geoms)
    g = lines.geometry.values
    names = lines["name"].to_numpy(dtype=object)
    ww = lines["waterway"].fillna("").to_numpy(dtype=object)
    river = ww == "river"
    canal = ww == "canal"
    other = ~river & ~canal
    tier1 = _nearest_by_class(pts, [(g[river], names[river], 1.0)], OSM_DIST)
    result = _majority(owner, tier1, n, MIN_SHARE)
    rest = np.array([i for i in range(len(geoms)) if i not in result], dtype=int)
    if len(rest):
        sel = np.isin(owner, rest)
        classes = [(g[m], names[m], w) for m, w in ((river, 1.0), (canal, 1.5), (other, 2.0))]
        tier2 = _nearest_by_class(pts[sel], classes, OSM_DIST)
        result.update(_majority(owner[sel], tier2, n, MIN_SHARE))
    canal_names = set(names[canal]) - set(names[~canal])
    is_canal = {r: nm in canal_names for r, nm in result.items()}
    covered = np.zeros(len(geoms), dtype=bool)
    if len(g):
        ri, _ = STRtree(g).query(geoms, predicate="dwithin", distance=OSM_DIST)
        covered[np.unique(ri)] = True
    return result, is_canal, covered


def vote_ne(geoms, lines: gpd.GeoDataFrame) -> dict[int, str]:
    pts, owner, n = sample_points(geoms)
    w = 1.0 + lines["scalerank"].fillna(10).clip(0, 12) / 6.0
    classes = []
    for wv in np.unique(w):
        m = (w == wv).to_numpy()
        classes.append(
            (lines.geometry.values[m], lines["name"].to_numpy(dtype=object)[m], float(wv))
        )
    return _majority(owner, _nearest_by_class(pts, classes, NE_DIST), n, MIN_SHARE)


def lake_of(geoms, lakes: gpd.GeoDataFrame) -> dict[int, str]:
    if len(lakes) == 0:
        return {}
    lg = lakes.geometry.values
    ri, li = STRtree(lg).query(geoms, predicate="intersects")
    if len(ri) == 0:
        return {}
    inside = shapely.length(shapely.intersection(geoms[ri], lg[li]))
    share = inside / shapely.length(geoms[ri])
    ok = (inside >= LAKE_MIN_M) & (share >= LAKE_SHARE)
    df = pd.DataFrame(
        {"r": ri[ok], "name": lakes["name"].to_numpy(dtype=object)[li[ok]], "x": inside[ok]}
    )
    df = df.sort_values(["r", "x"], ascending=[True, False]).drop_duplicates("r")
    return dict(zip(df["r"], df["name"], strict=True))


def _read_bbox(files: Iterable[Path], bbox, columns=None) -> gpd.GeoDataFrame:
    frames = [pyogrio.read_dataframe(f, bbox=bbox, columns=columns) for f in files]
    frames = [f for f in frames if len(f)]
    if not frames:
        empty = {c: pd.Series([], dtype=object) for c in ("name", "waterway", "tunnel")}
        return gpd.GeoDataFrame(empty, geometry=[], crs="EPSG:4326")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)


def _clean_names(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    g = g[g["name"].notna() & (g["name"].str.strip() != "")]
    if "tunnel" in g:
        g = g[g["tunnel"].isna() | (g["tunnel"] == "no")]
    return g


def name_tile(
    reaches: gpd.GeoDataFrame,
    osm_ways: list[Path],
    osm_lakes: list[Path],
    ne_lines: gpd.GeoDataFrame,
    ne_lakes: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Raw labels for the reaches of one tile: HYRIV_ID, name, source."""
    minx, miny, maxx, maxy = reaches.total_bounds
    pad = 0.05
    bbox = (minx - pad, miny - pad, maxx + pad, maxy + pad)
    geoms = reaches.to_crs(METRIC_CRS).geometry.values
    ways = _clean_names(_read_bbox(osm_ways, bbox)).to_crs(METRIC_CRS)
    names, is_canal, covered = vote_osm(geoms, ways)
    label = np.full(len(geoms), None, dtype=object)
    source = np.full(len(geoms), None, dtype=object)
    for r, nm in names.items():
        label[r], source[r] = nm, "osm:canal" if is_canal[r] else "osm"
    open_ = np.array(
        [i for i in range(len(geoms)) if label[i] is None and not covered[i]], dtype=int
    )
    if len(open_):
        ne = ne_lines.cx[bbox[0] : bbox[2], bbox[1] : bbox[3]].to_crs(METRIC_CRS)
        for r, nm in vote_ne(geoms[open_], ne).items():
            label[open_[r]], source[open_[r]] = nm, "naturalearth"
    lakes_osm = _clean_names(_read_bbox(osm_lakes, bbox)).to_crs(METRIC_CRS)
    lakes_osm["geometry"] = lakes_osm.geometry.make_valid()
    lakes_ne = ne_lakes.cx[bbox[0] : bbox[2], bbox[1] : bbox[3]].to_crs(METRIC_CRS)
    for src, lk in (("lake:naturalearth", lakes_ne), ("lake:osm", lakes_osm)):  # OSM wins: last
        for r, nm in lake_of(geoms, lk).items():
            label[r], source[r] = nm, src
    return pd.DataFrame(
        {"HYRIV_ID": reaches["HYRIV_ID"].to_numpy(), "name": label, "source": source}
    )
