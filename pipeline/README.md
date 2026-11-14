# pipeline/

Build-time data preparation (BRIEF §5 as changed by D8–D10 in `PROJECT.md`). Tooling decision: D11.

## Setup

```
cd pipeline
uv sync            # Python 3.12, locked in uv.lock
uv run pytest
uv run ruff check
```

GDAL reads remote files through the inherited HTTPS proxy. The fetch helper selects the
environment's trusted CA bundle and overrides Pyogrio's GDAL-specific certifi default when
needed. TLS verification stays enabled; no Claude-specific CA path is required when the
managed `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE` is available.

## Running a build

Every step reads the region from `DOWNSTREAM_REGION` (`eu`, the default, or `us`; D22,
`downstream/regions.py`) and writes per region: raw files `../data/raw/<kind>_<region>.fgb`,
outputs `../data/<names|paths|towns|report>/<region>/`. The site step combines every region that
has town files (`../data/site/eu/`, `us/`, `mix/`).

```
export DOWNSTREAM_REGION=eu                         # or us
uv run python -m downstream.fetch                   # inputs, incl. the region's OSM extracts
uv run python -m downstream.build_names --workers 4 # name the whole river network
uv run python -m downstream.paths                   # example towns (tests check them)
uv run python -m downstream.paths --all             # every town + build report
uv run python -m downstream.site                    # once, after all regions: Pages site + Polling URL
```

The site step now builds both the ordinary town feed and the source-checked comparison feed.
Use `uv run python -m downstream.site --previous-plans https://nikokoren.github.io/downstream`
for production builds, retaining deployed pair slots. New `paths --all` runs produce the
required source checks; legacy model packets must first pass `downstream.pair_validation`.
Missing evidence stops the build rather than approving unchecked pairs. See
[`docs/PAIR_FEED.md`](../docs/PAIR_FEED.md) for the packet contract, 80 km selection,
stable rotation and captured-packet validation commands. The current local run is complete;
[`docs/PAIR_VERIFICATION.md`](../docs/PAIR_VERIFICATION.md) records its 2,335 source-checked pairs.

OSM extracts come from this repo's `osm-waterways-<region>` releases, made by the
`osm-waterways` GitHub workflow from the list in `downstream/osm_regions*.txt`.
