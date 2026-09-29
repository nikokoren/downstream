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

import pyogrio

from downstream import sources

DATA = Path(__file__).resolve().parents[2] / "data"
RAW = DATA / "raw"

# Europe window for BasinATLAS (global layer). Generous; the D9 polygon does the real cut later.
EUROPE_BBOX = (-25.0, 34.0, 45.0, 72.0)


def _gdal_env() -> None:
    # The Claude Code container routes HTTPS through a proxy with its own CA bundle.
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        os.environ.setdefault("CURL_CA_BUNDLE", ca)
    os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
    os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "5")
    os.environ.setdefault("CPL_VSIL_CURL_CHUNK_SIZE", str(4 * 1024 * 1024))


def _copy_layer(src: str, dst: Path, columns: list[str], bbox=None) -> None:
    if dst.exists():
        print(f"skip {dst.name} (exists)")
        return
    _gdal_env()
    t = time.time()
    df = pyogrio.read_dataframe(src, columns=columns, bbox=bbox)
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
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.rename(dst)
    print(f"{dst.name}: {dst.stat().st_size} bytes")


def reaches() -> None:
    _copy_layer(sources.RIVERATLAS_EU, RAW / "reaches_eu.fgb", sources.REACH_COLUMNS)


def basins() -> None:
    _copy_layer(
        sources.BASINATLAS_L12, RAW / "basins_l12_europe.fgb", sources.BASIN_COLUMNS, EUROPE_BBOX
    )


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
OSM_REGIONS = Path(__file__).with_name("osm_regions.txt")


def osm_regions() -> list[str]:
    lines = OSM_REGIONS.read_text().splitlines()
    return [x.strip() for x in lines if x.strip() and not x.startswith("#")]


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


STEPS = {"reaches": reaches, "basins": basins, "ne": ne, "geonames": geonames, "osm": osm}


def main(argv: list[str]) -> None:
    (RAW / "osm").mkdir(parents=True, exist_ok=True)
    for step in argv or list(STEPS):
        STEPS[step]()


if __name__ == "__main__":
    main(sys.argv[1:])
