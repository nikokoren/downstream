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
    lines: gpd.GeoDataFrame  # columns: name, weight, primary, geometry (METRIC_CRS)
    tree: STRtree
    max_dist_m: float
    authoritative: bool = False  # where it has lines nearby, later sources aren't asked

    @classmethod
    def build(
        cls, label: str, gdf: gpd.GeoDataFrame, max_dist_m: float, authoritative: bool = False
    ) -> "NameSource":
        g = gdf[gdf["name"].notna() & (gdf["name"].str.strip() != "")].copy()
        if "tunnel" in g:  # culverts and sewer mains (e.g. Nesenbach-Hauptsammler) aren't named
            g = g[g["tunnel"].isna() | (g["tunnel"] == "no")]
        g["weight"] = line_weights(g)
        g["primary"] = g["waterway"].eq("river") if "waterway" in g else True
        g["canal"] = g["waterway"].eq("canal") if "waterway" in g else False
        cols = ["name", "weight", "primary", "canal", "geometry"]
        g = g[cols].to_crs(METRIC_CRS).reset_index(drop=True)
        return cls(label, g, STRtree(g.geometry.values), max_dist_m, authoritative)

    def best_name(self, reach_m: shapely.LineString, min_share: float) -> str | None:
        return self.vote(reach_m, min_share)[0]

    def is_canal(self, name: str) -> bool:
        rows = self.lines[self.lines["name"] == name]
        return bool(len(rows)) and bool(rows["canal"].all())

    def vote(self, reach_m: shapely.LineString, min_share: float) -> tuple[str | None, bool]:
        """(name, covered). Each sample point votes for its closest line (distance x weight)
        within max_dist_m. Natural rivers vote first; canals and streams only if no river wins.
        `covered` says whether this source has any line near the reach at all."""
        n = max(3, int(reach_m.length // 200) + 1)
        pts = shapely.line_interpolate_point(reach_m, np.linspace(0, 1, n), normalized=True)
        cand = self.tree.query(reach_m, predicate="dwithin", distance=self.max_dist_m)
        if len(cand) == 0:
            return None, False
        lines = self.lines.iloc[cand]
        primary = lines["primary"].to_numpy(dtype=bool)
        for mask in (primary, np.ones(len(lines), dtype=bool)):
            if not mask.any():
                continue
            sub = lines[mask]
            d = shapely.distance(pts[:, None], np.asarray(sub.geometry.values)[None, :])
            eff = np.where(d <= self.max_dist_m, d * sub["weight"].to_numpy()[None, :], np.inf)
            best = eff.argmin(axis=1)
            valid = np.isfinite(eff[np.arange(n), best])
            if not valid.any():
                continue
            names, counts = np.unique(sub["name"].to_numpy()[best[valid]], return_counts=True)
            k = counts.argmax()
            if counts[k] / n >= min_share:
                return str(names[k]), True
        return None, True


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


@dataclass
class LakeSource:
    label: str
    lakes: gpd.GeoDataFrame  # columns: name, geometry (METRIC_CRS)
    tree: STRtree

    @classmethod
    def build(cls, label: str, gdf: gpd.GeoDataFrame) -> "LakeSource":
        g = gdf[gdf["name"].notna() & (gdf["name"].str.strip() != "")][["name", "geometry"]]
        g = g.to_crs(METRIC_CRS).reset_index(drop=True)
        g["geometry"] = g.geometry.make_valid()
        return cls(label, g, STRtree(g.geometry.values))

    def lake_of(self, reach_m, min_share: float, min_len_m: float) -> str | None:
        """Name of the lake holding at least min_share (and min_len_m) of the reach, if any."""
        for i in self.tree.query(reach_m, predicate="intersects"):
            inside = reach_m.intersection(self.lakes.geometry.iloc[i]).length
            if inside >= min_len_m and inside / reach_m.length >= min_share:
                return str(self.lakes["name"].iloc[i])
        return None


def mark_lakes(reaches, labels: list[tuple], lakes: list[LakeSource], min_share=0.5, min_len_m=500):
    """Reaches that lie mostly inside a named lake become that lake (a step of its own)."""
    geoms = reaches.to_crs(METRIC_CRS).geometry.values
    out = list(labels)
    for i, geom in enumerate(geoms):
        for src in lakes:
            name = src.lake_of(geom, min_share, min_len_m)
            if name:
                out[i] = (name, src.label)
                break
    return out


def name_key(name: str | None) -> str | None:
    """Spelling-insensitive key: 'Weisse Elster' and 'Weiße Elster' are the same river."""
    if not name:
        return None
    return " ".join(name.casefold().replace("ß", "ss").split())


_CURATED: dict | None = None


def display_key(name: str | None) -> str | None:
    """Compare names as they'll be shown: through the curated table (Donau, Duna, Dunav are all
    the Danube), otherwise spelling-insensitively on the last part of a bilingual OSM name."""
    global _CURATED
    if not name:
        return None
    if _CURATED is None:
        _CURATED = load_curated()
    disp = lookup_curated(name, _CURATED)
    return name_key(disp["en"] if disp else name_variants(name)[-1])


def _key(label: tuple) -> str | None:
    return display_key(label[0])


def is_lake(label: tuple) -> bool:
    return bool(label[1]) and label[1].startswith("lake:")


def fold_delta(reaches, labels: list[tuple]) -> list[tuple]:
    """Delta arms join the main river (author, 2026-09-28): in the last river of the path (the run
    that reaches the outlet), later names become the first name, e.g. Rhine -> Lek is Rhine.
    Lakes are left alone."""
    last = runs(reaches)[-1]
    first = next((labels[i] for i in last if labels[i][0] and not is_lake(labels[i])), None)
    if first is None:
        return labels
    out = list(labels)
    seen = False
    for i in last:
        if is_lake(labels[i]):
            continue
        seen = seen or _key(labels[i]) == _key(first)
        if seen:
            out[i] = first
    return out


def name_reaches(
    reaches: gpd.GeoDataFrame,
    sources: list[NameSource],
    lakes: list[LakeSource] = (),
    min_share=0.5,
    min_block=3,
    min_block_km=5.0,
) -> list[tuple]:
    """Per reach: (name, source label) or (None, None). Lake reaches get (lake name, "lake:...").

    1. Each reach gets its own best name (first source that has one).
    2. Reaches mostly inside a named lake become that lake (D13); the rules below skip them.
    3. Within a river (see `runs`): a name stretch shorter than `min_block` reaches and
       `min_block_km` is absorbed (confluence blips); A -> B -> A becomes A (a nearby line, not a
       new river), shortest B first; a river with no names falls back to one vote over all of it.
    4. Delta arms fold into the main river (D12).
    """
    geoms = reaches.to_crs(METRIC_CRS).geometry.values
    lengths = reaches["LENGTH_KM"].to_numpy(dtype=float)
    out = [_first_name(g, sources, min_share) for g in geoms]
    out = mark_lakes(reaches, out, list(lakes))
    for run in runs(reaches):
        idx = [i for i in run if not is_lake(out[i])]
        if not idx:
            continue
        labels = [out[i] for i in idx]
        km = [lengths[i] for i in idx]
        labels = _absorb_short_blocks(labels, min_block, km, min_block_km)
        labels = _collapse_interruptions(labels, km)
        if all(label[0] is None for label in labels):
            line = shapely.line_merge(shapely.MultiLineString([geoms[i] for i in idx]))
            labels = [_first_name(line, sources, min_share)] * len(idx)
        for i, label in zip(idx, labels, strict=True):
            out[i] = label
    return fold_delta(reaches, out)


def _first_name(geom, sources: list[NameSource], min_share: float) -> tuple:
    for src in sources:
        name, covered = src.vote(geom, min_share)
        if name:
            # Canal names are weak: engineered routes aren't modeled, so they never become a step
            # of their own inside a river (e.g. Main-Donau-Kanal between Regnitz and Main).
            return (name, f"{src.label}:canal" if src.is_canal(name) else src.label)
        if covered and src.authoritative:
            return (None, None)  # OSM has lines here but none fits: don't guess from coarser data
    return (None, None)


def _blocks(labels: list[tuple], km: list[float] | None = None) -> list[list]:
    """[label, count, km] for each run of equal names."""
    km = km if km is not None else [1.0] * len(labels)
    blocks: list[list] = []
    for label, k in zip(labels, km, strict=True):
        if blocks and _key(blocks[-1][0]) == _key(label):
            blocks[-1][1] += 1
            blocks[-1][2] += k
        else:
            blocks.append([label, 1, k])
    return blocks


def _collapse_interruptions(labels: list[tuple], km: list[float] | None = None) -> list[tuple]:
    """A -> B -> A means B is an interruption (a nearby line or a side arm), not a new river.

    Shortest B first. A real name change (Pegnitz -> Regnitz) never returns to the first name.
    """
    while True:
        blocks = _blocks(labels, km)
        cands = [
            k
            for k in range(1, len(blocks) - 1)
            if blocks[k - 1][0][0] and _key(blocks[k - 1][0]) == _key(blocks[k + 1][0])
        ]
        if not cands:
            return labels
        k = min(cands, key=lambda c: blocks[c][2])
        start = sum(b[1] for b in blocks[:k])
        n = blocks[k][1]
        labels = labels[:start] + [blocks[k - 1][0]] * n + labels[start + n :]


def _absorb_short_blocks(
    labels: list[tuple], min_block: int, km: list[float] | None = None, min_km: float = float("inf")
) -> list[tuple]:
    """Blocks shorter than min_block reaches and min_km take the neighbouring long name."""
    blocks = _blocks(labels, km)

    def long(b) -> bool:
        weak = bool(b[0][1]) and b[0][1].endswith(":canal")
        return b[0][0] is not None and not weak and (b[1] >= min_block or b[2] >= min_km)

    named = [b for b in blocks if long(b)]
    if not named:
        # Nothing long enough to trust: leave the labels as they are. (Guessing the most frequent
        # name here named Graz's start after a 1:1 tie between Ragnitzbach and Leonhardbach once
        # whole rivers were cleaned, 2026-09-29.)
        return labels
    result: list[tuple] = []
    last_good = None
    for k, b in enumerate(blocks):
        if long(b):
            last_good = b[0]
            result.extend([b[0]] * b[1])
            continue
        fill = last_good or next(x[0] for x in blocks[k + 1 :] if long(x))
        result.extend([fill] * b[1])
    return result


def name_variants(name: str) -> list[str]:
    """OSM border, bilingual and arm names -> the whole name first, then each part.

    Forms seen in OSM (Europe run, 2026-09-29): "Mur / Mura", "Dunav/Dunărea", "Dunărea - Дунав",
    "a;b", and delta arms "Brațul Borcea (Dunărea)", "Dunărea (Brațul Sulina)". Hyphens without
    spaces ("Main-Donau-Kanal") are part of a name and are not split.
    """
    s = name
    for sep in (";", " - ", " – ", "(", ")"):
        s = s.replace(sep, "/")
    parts = [p.strip() for p in s.split("/") if p.strip()]
    return [name, *parts] if len(parts) > 1 else [name]


def lookup_curated(name: str, curated: dict) -> dict | None:
    for v in name_variants(name):
        if v in curated:
            return curated[v]
    return None


def chain(reaches: gpd.GeoDataFrame, names: list[tuple], curated: dict) -> list[dict]:
    """Group consecutive reaches by display name; lengths in km.

    Across rivers too, river A -> river B -> river A becomes A (a side arm such as Hamburg's
    Norderelbe), but never across a lake. The spelling shown is the one covering most km.
    """
    groups: list[dict] = []
    for (name, src), length in zip(names, reaches["LENGTH_KM"], strict=True):
        disp = lookup_curated(name, curated) if name else None
        key = display_key(name)
        kind = "lake" if src and src.startswith("lake:") else "river"
        if groups and groups[-1]["key"] == key and groups[-1]["kind"] == kind:
            g = groups[-1]
            g["km"] += float(length)
            g["reaches"] += 1
            if name:
                g["spellings"][name] = g["spellings"].get(name, 0.0) + float(length)
            continue
        groups.append(
            {
                "key": key,
                "disp": disp,
                "spellings": {name: float(length)} if name else {},
                "source": src,
                "kind": kind,
                "km": float(length),
                "reaches": 1,
            }
        )
    groups = _lakes_named_like_river(groups)
    groups = _merge_side_arms(groups)
    groups = _merge_repeated_lakes(groups)
    for g in groups:
        g["km"] = round(g["km"], 1)
        if g["disp"]:
            g["name"] = {"en": g["disp"]["en"], "de": g["disp"]["de"]}
        elif g["spellings"]:
            g["name"] = {"local": max(g["spellings"], key=g["spellings"].get)}
        else:
            g["name"] = None
    return groups


def _merge_repeated_lakes(groups: list[dict], max_gap_km: float = 5.0) -> list[dict]:
    """A path that zigzags through one lake (Hamar: Glomma -> Øyeren -> Glomma -> Øyeren) shows
    the lake once: lake L, river bits shorter than max_gap_km in total, lake L -> one L step."""
    out: list[dict] = []
    for g in groups:
        if g["kind"] == "lake":
            j = len(out) - 1
            gap = 0.0
            while j >= 0 and out[j]["kind"] == "river" and gap + out[j]["km"] <= max_gap_km:
                gap += out[j]["km"]
                j -= 1
            if (
                j >= 0
                and j < len(out) - 1
                and out[j]["kind"] == "lake"
                and out[j]["key"] == g["key"]
            ):
                lake = out[j]
                for mid in out[j + 1 :]:
                    lake["km"] += mid["km"]
                    lake["reaches"] += mid["reaches"]
                lake["km"] += g["km"]
                lake["reaches"] += g["reaches"]
                del out[j + 1 :]
                continue
        out.append(g)
    return out


def _lakes_named_like_river(groups: list[dict]) -> list[dict]:
    """A 'lake' named like the river next to it is a widening of that river (OSM maps parts of
    the Havel as water=lake named Havel), so it joins the river instead of being a step."""
    for k, g in enumerate(groups):
        if g["kind"] != "lake":
            continue
        for j in (k - 1, k + 1):
            if (
                0 <= j < len(groups)
                and groups[j]["kind"] == "river"
                and groups[j]["key"] == g["key"]
            ):
                g["kind"] = "river"
                g["disp"] = groups[j]["disp"]
                break
    merged: list[dict] = []
    for g in groups:
        if merged and merged[-1]["key"] == g["key"] and merged[-1]["kind"] == g["kind"]:
            m = merged[-1]
            m["km"] += g["km"]
            m["reaches"] += g["reaches"]
            for n, v in g["spellings"].items():
                m["spellings"][n] = m["spellings"].get(n, 0.0) + v
        else:
            merged.append(g)
    return merged


def _merge_side_arms(groups: list[dict]) -> list[dict]:
    while True:
        cands = [
            k
            for k in range(1, len(groups) - 1)
            if all(groups[j]["kind"] == "river" for j in (k - 1, k, k + 1))
            and groups[k - 1]["key"]
            and groups[k - 1]["key"] == groups[k + 1]["key"]
        ]
        if not cands:
            return groups
        k = min(cands, key=lambda c: groups[c]["km"])
        a, b, c = groups[k - 1], groups[k], groups[k + 1]
        a["km"] += b["km"] + c["km"]
        a["reaches"] += b["reaches"] + c["reaches"]
        for n, v in c["spellings"].items():
            a["spellings"][n] = a["spellings"].get(n, 0.0) + v
        groups = groups[:k] + groups[k + 2 :]
