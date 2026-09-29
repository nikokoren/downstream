"""Name the whole river network of a HydroATLAS region (per-river redesign).

Usage: uv run python -m downstream.build_names [--workers 4]
Writes ../data/names/raw_labels.csv (stage 1) and ../data/names/reach_names.csv (stage 2).
"""

import argparse
import multiprocessing as mp
import os
import time

import numpy as np
import pandas as pd
import pyogrio

from downstream import reach_names, rivers
from downstream.endpoints import load_ne
from downstream.fetch import RAW
from downstream.name_table import NameTable
from downstream.naming import load_curated
from downstream.paths import pd_concat

OUT = RAW.parent / "names"
_G: dict = {}


def _init() -> None:
    _G["reaches"] = pyogrio.read_dataframe(RAW / "reaches_eu.fgb")
    _G["ways"] = sorted((RAW / "osm").glob("waterways-*.fgb"))
    _G["lakes"] = sorted((RAW / "osm").glob("lakes-*.fgb"))
    for f in _G["ways"] + _G["lakes"]:  # file extents once, before forking the workers
        reach_names._extent(f)
    ne = pd_concat([load_ne(RAW / "ne_rivers.zip"), load_ne(RAW / "ne_rivers_europe.zip")])
    _G["ne"] = ne.to_crs("EPSG:4326")
    nel = pd_concat([load_ne(RAW / "ne_lakes.zip"), load_ne(RAW / "ne_lakes_europe.zip")])
    _G["ne_lakes"] = nel[nel["featurecla"].isin(["Lake", "Alkaline Lake"])].to_crs("EPSG:4326")


def _tile(rows: np.ndarray) -> pd.DataFrame:
    sub = _G["reaches"].iloc[rows]
    return reach_names.name_tile(sub, _G["ways"], _G["lakes"], _G["ne"], _G["ne_lakes"])


def stage2() -> None:
    t1 = time.time()
    r = pyogrio.read_dataframe(RAW / "reaches_eu.fgb", read_geometry=False)
    raw = pd.read_csv(OUT / "raw_labels.csv")
    cleaned = rivers.clean(r, raw)
    cleaned.to_csv(OUT / "reach_names.csv", index=False)
    named = cleaned["name"].notna().sum()
    table = NameTable()
    ok = cleaned[cleaned["name"].notna()]
    table.add(ok["HYRIV_ID"], list(zip(ok["name"], ok["source"], strict=True)), load_curated())
    build = (
        os.environ.get("GITHUB_SHA", "local")[:12]
        + " "
        + time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    )
    t = table.write(OUT / "name_table", build)
    english_names(OUT / "name_table" / "name_en.csv")
    print(f"name table: {len(table.rows)} rows -> {t}", flush=True)
    print(
        f"stage 2 in {time.time() - t1:.0f}s; {named} of {len(cleaned)} reaches named", flush=True
    )


def english_names(path) -> None:
    """OSM `name:en` for every Greek or Cyrillic name (the most common one where ways disagree):
    shown on screen instead of the local script (author, 2026-09-29). ODbL, published with the
    name table."""
    import collections
    import csv

    from downstream.latin import NON_LATIN

    counts: dict[str, collections.Counter] = {}
    for f in sorted((RAW / "osm").glob("*.fgb")):
        d = pyogrio.read_dataframe(f, columns=["name", "name_en"], read_geometry=False)
        d = d[d["name"].notna() & d["name_en"].notna()]
        d = d[d["name"].str.contains(NON_LATIN) & ~d["name_en"].str.contains(NON_LATIN)]
        for n, e in zip(d["name"], d["name_en"], strict=True):
            counts.setdefault(n, collections.Counter())[e.strip()] += 1
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "name_en"])
        for n in sorted(counts):
            w.writerow([n, counts[n].most_common(1)[0][0]])
    print(f"english names: {len(counts)} -> {path}", flush=True)


def main(workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    _init()  # parent loads once; forked workers share it
    r = _G["reaches"]
    rp = r.geometry.representative_point()
    key = np.floor(rp.x).astype(int) * 1000 + np.floor(rp.y).astype(int)
    groups = [np.flatnonzero(key.to_numpy() == k) for k in np.unique(key)]
    groups.sort(key=len, reverse=True)
    print(f"{len(r)} reaches in {len(groups)} tiles; loaded in {time.time() - t0:.0f}s", flush=True)
    out = []
    with mp.get_context("fork").Pool(workers) as pool:
        for i, df in enumerate(pool.imap_unordered(_tile, groups), 1):
            out.append(df)
            if i % 100 == 0 or i == len(groups):
                print(f"  {i}/{len(groups)} tiles, {time.time() - t0:.0f}s", flush=True)
    raw = pd.concat(out, ignore_index=True)
    raw.to_csv(OUT / "raw_labels.csv", index=False)
    t1 = time.time()
    cleaned = rivers.clean(r.drop(columns="geometry"), raw)
    cleaned.to_csv(OUT / "reach_names.csv", index=False)
    named = cleaned["name"].notna().sum()
    table = NameTable()
    ok = cleaned[cleaned["name"].notna()]
    table.add(ok["HYRIV_ID"], list(zip(ok["name"], ok["source"], strict=True)), load_curated())
    build = (
        os.environ.get("GITHUB_SHA", "local")[:12]
        + " "
        + time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    )
    t = table.write(OUT / "name_table", build)
    english_names(OUT / "name_table" / "name_en.csv")
    print(f"name table: {len(table.rows)} rows -> {t}", flush=True)
    print(
        f"stage 2 in {time.time() - t1:.0f}s; {named} of {len(cleaned)} reaches named; "
        f"total {time.time() - t0:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--stage2-only", action="store_true", help="re-clean saved raw_labels.csv")
    args = ap.parse_args()
    stage2() if args.stage2_only else main(args.workers)
