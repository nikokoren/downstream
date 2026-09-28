"""Attach names to the reaches of one path (BRIEF R6, P3; D7, D10).

A reach takes the name of the named line that runs along most of it: sample points along the
reach and count, per name, the share of points within `max_dist_m` of a line with that name.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from shapely import STRtree

METRIC_CRS = "EPSG:3035"  # ETRS89 / LAEA Europe, metres
CURATED = Path(__file__).with_name("curated_names.csv")


@dataclass
class NameSource:
    label: str
    lines: gpd.GeoDataFrame  # columns: name, weight, geometry (METRIC_CRS)
    tree: STRtree
    max_dist_m: float

    @classmethod
    def build(cls, label: str, gdf: gpd.GeoDataFrame, max_dist_m: float) -> "NameSource":
        g = gdf[gdf["name"].notna() & (gdf["name"].str.strip() != "")].copy()
        g["weight"] = line_weights(g)
        g = g[["name", "weight", "geometry"]].to_crs(METRIC_CRS).reset_index(drop=True)
        return cls(label, g, STRtree(g.geometry.values), max_dist_m)

    def best_name(self, reach_m: shapely.LineString, min_share: float) -> str | None:
        """Each sample point votes for its closest line (distance x weight) within max_dist_m."""
        n = max(3, int(reach_m.length // 200) + 1)
        pts = shapely.line_interpolate_point(reach_m, np.linspace(0, 1, n), normalized=True)
        cand = self.tree.query(reach_m, predicate="dwithin", distance=self.max_dist_m)
        if len(cand) == 0:
            return None
        lines = self.lines.iloc[cand]
        d = shapely.distance(pts[:, None], np.asarray(lines.geometry.values)[None, :])
        eff = np.where(d <= self.max_dist_m, d * lines["weight"].to_numpy()[None, :], np.inf)
        best = eff.argmin(axis=1)
        valid = np.isfinite(eff[np.arange(n), best])
        if not valid.any():
            return None
        votes = lines["name"].to_numpy()[best[valid]]
        names, counts = np.unique(votes, return_counts=True)
        k = counts.argmax()
        return str(names[k]) if counts[k] / n >= min_share else None


def line_weights(g: gpd.GeoDataFrame) -> np.ndarray:
    """Bigger rivers count as closer: OSM river 1, canal 1.5, others 2; Natural Earth by scalerank."""
    if "waterway" in g:
        return g["waterway"].map({"river": 1.0, "canal": 1.5}).fillna(2.0).to_numpy()
    if "scalerank" in g:
        return (1.0 + g["scalerank"].fillna(10).clip(0, 12) / 6.0).to_numpy()
    return np.ones(len(g))


def load_curated() -> dict[str, dict[str, str]]:
    table = {}
    with open(CURATED, encoding="utf-8") as f:
        rows = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in rows:
            for v in row["variants"].split("|"):
                table[v.strip()] = {"en": row["en"], "de": row["de"]}
    return table


def runs(reaches: gpd.GeoDataFrame) -> list[list[int]]:
    """Split a path into rivers: consecutive reaches with the same classical order (ORD_CLAS).

    ORD_CLAS is 1 on a basin's main stem, 2 on its tributaries, and so on; along a downstream path
    it only changes where the water joins a bigger river.
    """
    out: list[list[int]] = []
    prev = None
    for i, order in enumerate(reaches["ORD_CLAS"].to_numpy()):
        if order != prev:
            out.append([])
            prev = order
        out[-1].append(i)
    return out


def name_reaches(
    reaches: gpd.GeoDataFrame, sources: list[NameSource], min_share=0.5, min_block=3
) -> list[tuple]:
    """Per reach: (name, source label) or (None, None).

    1. Each reach gets its own best name (first source that has one).
    2. Within a river (see `runs`), stretches of one name shorter than `min_block` reaches are
       absorbed into the neighbouring name (confluence blips, a tributary touching one reach).
       Longer stretches stay, so a name change along one river survives (Pegnitz -> Regnitz).
    3. A river with no per-reach names falls back to one vote over the whole river.
    """
    geoms = reaches.to_crs(METRIC_CRS).geometry.values
    out: list[tuple] = []
    for geom in geoms:
        out.append(_first_name(geom, sources, min_share))
    for run in runs(reaches):
        labels = [out[i] for i in run]
        labels = _absorb_short_blocks(labels, min_block)
        labels = _collapse_interruptions(labels)
        if all(label[0] is None for label in labels):
            line = shapely.line_merge(shapely.MultiLineString([geoms[i] for i in run]))
            labels = [_first_name(line, sources, min_share)] * len(run)
        for i, label in zip(run, labels, strict=True):
            out[i] = label
    return out


def _first_name(geom, sources: list[NameSource], min_share: float) -> tuple:
    for src in sources:
        name = src.best_name(geom, min_share)
        if name:
            return (name, src.label)
    return (None, None)


def _blocks(labels: list[tuple]) -> list[list]:
    blocks: list[list] = []
    for label in labels:
        if blocks and blocks[-1][0][0] == label[0]:
            blocks[-1][1] += 1
        else:
            blocks.append([label, 1])
    return blocks


def _collapse_interruptions(labels: list[tuple]) -> list[tuple]:
    """Within one river, A -> B -> A means B is an interruption (a nearby line), not a new river.

    A real name change along one river (Pegnitz -> Regnitz) never returns to the first name.
    """
    while True:
        blocks = _blocks(labels)
        for k in range(1, len(blocks) - 1):
            if blocks[k - 1][0][0] and blocks[k - 1][0][0] == blocks[k + 1][0][0]:
                start = sum(b[1] for b in blocks[:k])
                labels = (
                    labels[:start]
                    + [blocks[k - 1][0]] * blocks[k][1]
                    + labels[start + blocks[k][1] :]
                )
                break
        else:
            return labels


def _absorb_short_blocks(labels: list[tuple], min_block: int) -> list[tuple]:
    blocks = _blocks(labels)
    named = [b for b in blocks if b[0][0] is not None and b[1] >= min_block]
    if not named:
        # Nothing long enough: keep the most frequent name for the whole river, if any.
        counts: dict = {}
        for label in labels:
            if label[0]:
                counts[label] = counts.get(label, 0) + 1
        return [max(counts, key=counts.get)] * len(labels) if counts else labels
    # Replace short or unnamed blocks by the nearest long named block (prefer the upstream one).
    result: list[tuple] = []
    last_good = None
    for k, (label, size) in enumerate(blocks):
        good = label[0] is not None and size >= min_block
        if good:
            last_good = label
            result.extend([label] * size)
            continue
        fill = last_good
        if fill is None:
            fill = next(b[0] for b in blocks[k + 1 :] if b[0][0] is not None and b[1] >= min_block)
        result.extend([fill] * size)
    return result


def chain(reaches: gpd.GeoDataFrame, names: list[tuple], curated: dict) -> list[dict]:
    """Group consecutive reaches by display name; lengths in km."""
    groups: list[dict] = []
    for (name, src), length in zip(names, reaches["LENGTH_KM"], strict=True):
        disp = curated.get(name) if name else None
        key = disp["en"] if disp else name
        if groups and groups[-1]["key"] == key:
            groups[-1]["km"] += float(length)
            groups[-1]["reaches"] += 1
            continue
        groups.append(
            {
                "key": key,
                "name": {"en": disp["en"], "de": disp["de"]}
                if disp
                else ({"local": name} if name else None),
                "source": src,
                "km": float(length),
                "reaches": 1,
            }
        )
    for g in groups:
        g["km"] = round(g["km"], 1)
    return groups
