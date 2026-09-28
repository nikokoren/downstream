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

## Stages (planned; each writes to `../data/`, git-ignored, and can be re-run on its own)

| Stage | Input | Output |
|---|---|---|
| fetch | figshare zips (range-read: only `RiverATLAS_v10_eu.*` and `BasinATLAS_v10_lev12.*`), Natural Earth, GeoNames | raw files |
| reaches | RiverATLAS `eu` | routing table: `HYRIV_ID`, `NEXT_DOWN`, `LENGTH_KM`, `DIST_DN_KM`, `ENDORHEIC`, `MAIN_RIV`, `ORD_CLAS`, `HYBAS_L12`, geometry (GeoParquet) |
| osm-names | OSM Europe, filtered to `waterway=*` with pyosmium, one country extract at a time | named waterway lines |
| names | reaches + OSM names + Natural Earth + curated table | name table (ODbL, published; D10) |
| endpoints | outlet reaches + Natural Earth marine areas and lakes | endpoint table (P4) |
| towns | GeoNames cities15000 + alternate names + Europe polygon | town list with en/de names (D9) |
| paths | everything above | one JSON per town, plus the build report (P7) |

Written so far (2026-09-28): `fetch` (reaches, basins, Natural Earth, GeoNames), `osm_waterways` (runs in the `osm-waterways` GitHub workflow), `network` (routing), `naming`, `endpoints`, `towns`, and `paths` for the example towns. Not yet: the published name table, the Europe polygon filter, town selection, the build report.

Example run:

```
uv run python -m downstream.fetch
B=https://github.com/nikokoren/downstream/releases/download/osm-waterways-europe-germany-bayern
curl -fL -o ../data/raw/osm_waterways_bayern.fgb $B/waterways-europe-germany-bayern.fgb
curl -fL -o ../data/raw/osm_lakes_bayern.fgb $B/lakes-europe-germany-bayern.fgb
uv run python -m downstream.paths --waterways ../data/raw/osm_waterways_bayern.fgb --lakes ../data/raw/osm_lakes_bayern.fgb
```
