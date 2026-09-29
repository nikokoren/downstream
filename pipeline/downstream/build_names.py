"""Name the whole river network of a HydroATLAS region (per-river redesign).

Usage: uv run python -m downstream.build_names [--workers 4]
Writes ../data/names/raw_labels.csv (stage 1) and ../data/names/reach_names.csv (stage 2).
"""

import argparse
import multiprocessing as mp
import time

import numpy as np
import pandas as pd
import pyogrio

from downstream import reach_names, rivers
from downstream.endpoints import load_ne
from downstream.fetch import RAW
from downstream.paths import pd_concat

OUT = RAW.parent / "names"
_G: dict = {}


def _init() -> None:
    _G["reaches"] = pyogrio.read_dataframe(RAW / "reaches_eu.fgb")
    _G["ways"] = sorted((RAW / "osm").glob("waterways-*.fgb"))
    _G["lakes"] = sorted((RAW / "osm").glob("lakes-*.fgb"))
    ne = pd_concat([load_ne(RAW / "ne_rivers.zip"), load_ne(RAW / "ne_rivers_europe.zip")])
    _G["ne"] = ne.to_crs("EPSG:4326")
    nel = pd_concat([load_ne(RAW / "ne_lakes.zip"), load_ne(RAW / "ne_lakes_europe.zip")])
    _G["ne_lakes"] = nel[nel["featurecla"].isin(["Lake", "Alkaline Lake"])].to_crs("EPSG:4326")


def _tile(rows: np.ndarray) -> pd.DataFrame:
    sub = _G["reaches"].iloc[rows]
    return reach_names.name_tile(sub, _G["ways"], _G["lakes"], _G["ne"], _G["ne_lakes"])


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
    print(
        f"stage 2 in {time.time() - t1:.0f}s; {named} of {len(cleaned)} reaches named; "
        f"total {time.time() - t0:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    main(ap.parse_args().workers)
