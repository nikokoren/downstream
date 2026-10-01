"""Download the inputs into data/ (git-ignored). Each step skips files that already exist.

Usage: uv run python -m downstream.fetch [reaches|basins|ne|geonames ...]
"""

import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio

from downstream import regions, sources
from downstream.regions import DATA

RAW = DATA / "raw"
REGION = regions.current()


def _gdal_env() -> None:
    # The Claude Code container routes HTTPS through a proxy with its own CA bundle.
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        os.environ.setdefault("CURL_CA_BUNDLE", ca)
    os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
    os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "5")
    os.environ.setdefault("CPL_VSIL_CURL_CHUNK_SIZE", str(4 * 1024 * 1024))


def _copy_layer(src: str | list[str], dst: Path, columns: list[str], bbox=None) -> None:
    if dst.exists():
        print(f"skip {dst.name} (exists)")
        return
    _gdal_env()
    t = time.time()
    srcs = [src] if isinstance(src, str) else src
    frames = [pyogrio.read_dataframe(s, columns=columns, bbox=bbox) for s in srcs]
    df = frames[0]
    if len(frames) > 1:
        df = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)
    tmp = dst.with_suffix(".tmp.fgb")
    pyogrio.write_dataframe(df, tmp, driver="FlatGeobuf")
    tmp.rename(dst)
    print(f"{dst.name}: {len(df)} features in {time.time() - t:.0f}s")


def _download(url: str, dst: Path) -> None:
    if dst.exists():
        print(f"skip {dst.name} (exists)")
        return
    tmp = dst.with_suffix(dst.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "downstream-pipeline/0.1"})
    # Server errors and dropped connections are retried: GitHub's release downloads answered 500
    # once in 244 files (build run 11, 2026-09-29). 4xx (e.g. a missing release) fails at once.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            client_error = isinstance(e, urllib.error.HTTPError) and e.code < 500
            if client_error or attempt == 3:
                raise
            print(f"retry {dst.name} after {e}", flush=True)
            time.sleep(2 ** (attempt + 1))
    tmp.rename(dst)
    print(f"{dst.name}: {dst.stat().st_size} bytes")


def reaches_file(region: regions.Region = REGION) -> Path:
    return RAW / f"reaches_{region.code}.fgb"


def basins_file(region: regions.Region = REGION) -> Path:
    return RAW / f"basins_l12_{region.code}.fgb"


def lakes_file(region: regions.Region = REGION) -> Path:
    return RAW / f"hydrolakes_points_{region.code}.fgb"


def reaches() -> None:
    # Several RiverATLAS files for a region (US: na + ar) just add up: each holds whole basins.
    files = [sources.riveratlas(r) for r in REGION.riveratlas]
    _copy_layer(files, reaches_file(), sources.REACH_COLUMNS)


def basins() -> None:
    _copy_layer(sources.BASINATLAS_L12, basins_file(), sources.BASIN_COLUMNS, REGION.bbox)


def ne() -> None:
    for name, url in sources.NE_LAYERS.items():
        _download(url, RAW / f"ne_{name}.zip")


def geonames() -> None:
    for name in ["cities15000.zip", "alternateNamesV2.zip", "countryInfo.txt"]:
        _download(f"{sources.GEONAMES_DUMP}/{name}", RAW / f"geonames_{name}")
    from downstream.towns import extra_town_ids

    for cc in sorted(set(extra_town_ids().values())):  # country dumps for the extra towns
        _download(f"{sources.GEONAMES_DUMP}/{cc}.zip", RAW / f"geonames_{cc}.zip")
    alt = RAW / "geonames_alternateNamesV2.zip"
    out = RAW / "geonames_alt_de_en.txt"
    if not out.exists():
        # Keep only German and English names; the full file is 785 MB unzipped.
        with (
            zipfile.ZipFile(alt) as z,
            z.open("alternateNamesV2.txt") as src,
            open(out, "wb") as dst,
        ):
            for line in src:
                if line.split(b"\t", 3)[2] in (b"de", b"en"):
                    dst.write(line)
        print(f"{out.name}: {out.stat().st_size} bytes")


RELEASES = "https://github.com/nikokoren/downstream/releases/download"


def osm_regions(region: regions.Region = REGION) -> list[str]:
    lines = regions.osm_regions_file(region).read_text().splitlines()
    return [x.strip() for x in lines if x.strip() and not x.startswith("#")]


def osm_files(kind: str, region: regions.Region = REGION) -> list[Path]:
    """The region's OSM files ("waterways" or "lakes") that exist locally."""
    paths = [RAW / "osm" / f"{kind}-{r.replace('/', '-')}.fgb" for r in osm_regions(region)]
    return sorted(p for p in paths if p.exists())


def osm() -> None:
    """OSM waterways and lakes per region, from this repo's releases (ODbL, D10)."""
    for region in osm_regions():
        slug = region.replace("/", "-")
        for kind in ("waterways", "lakes"):
            url = f"{RELEASES}/osm-waterways-{slug}/{kind}-{slug}.fgb"
            try:
                _download(url, RAW / "osm" / f"{kind}-{slug}.fgb")
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
                print(f"missing {kind}-{slug}.fgb (release not published yet?)")


def lakes() -> None:
    """HydroLAKES pour points inside the region's window (Res_time for the travel time, D3)."""
    zp = RAW / "hydrolakes_points_v10_shp.zip"
    _download(sources.HYDROLAKES_POINTS, zp)
    with zipfile.ZipFile(zp) as z:
        shp = next(n for n in z.namelist() if n.endswith(".shp"))
    _copy_layer(f"/vsizip/{zp}/{shp}", lakes_file(), sources.LAKE_COLUMNS, REGION.bbox)


def framework() -> None:
    """TRMNL Framework files for the recipe's render check (not used by the pipeline itself)."""
    out = RAW / "framework" / sources.FRAMEWORK_VERSION
    out.mkdir(parents=True, exist_ok=True)
    for name, url in sources.FRAMEWORK_FILES.items():
        _download(url, out / name)
    for name, url in sources.MAPLIBRE_FILES.items():
        _download(url, out / name)
    (out / "fonts").mkdir(exist_ok=True)
    for name in sources.FRAMEWORK_FONTS:
        _download(f"https://trmnl.com/fonts/{name}", out / "fonts" / name)


STEPS = {
    "reaches": reaches,
    "basins": basins,
    "ne": ne,
    "geonames": geonames,
    "lakes": lakes,
    "osm": osm,
    "framework": framework,
}


def main(argv: list[str]) -> None:
    (RAW / "osm").mkdir(parents=True, exist_ok=True)
    for step in argv or list(STEPS):
        STEPS[step]()


if __name__ == "__main__":
    main(sys.argv[1:])
