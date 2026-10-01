# pipeline/

Build-time data preparation (BRIEF §5 as changed by D8–D10 in `PROJECT.md`). Tooling decision: D11.

## Setup

```
cd pipeline
uv sync            # Python 3.12, locked in uv.lock
uv run pytest
uv run ruff check
```

GDAL reads remote files through the environment's HTTPS proxy. In the Claude Code cloud container, set `CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt` first.

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

OSM extracts come from this repo's `osm-waterways-<region>` releases, made by the
`osm-waterways` GitHub workflow from the list in `downstream/osm_regions*.txt`.
