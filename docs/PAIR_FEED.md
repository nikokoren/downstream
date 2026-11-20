# Drainage-divide feed implementation — 13 November 2026

> **Superseded on 2026-11-20 (D25).** The pair catalogue, its 72-hour planner and fixed pair
> capacities are retired. `<region>/p/<n>.json` now holds slot n's town from the normal rotation
> (`t/<n>.json`) plus its companion, chosen by `pipeline/downstream/companions.py`. Source
> verification below still applies to companions closer than 80 km. Kept as history.

The local implementation now connects `watershed_pairs` to a separate static feed at
`<region>/p/<slot>.json`. The existing town feed remains at `<region>/t/<slot>.json`.
Region combinations, the 15-minute cadence, Full-only comparison, primary-town fallback in
smaller layouts, optional labels and the existing town eligibility policy are preserved.
Nothing has been published or deployed.

## Source verification gates

`downstream.paths` now writes internal `pair_checks` evidence and the measured
`start.distance_km`. `downstream.pair_validation` can also verify the previously captured
normal-rotation packets using the original **RiverATLAS and BasinATLAS v1.0, CC BY 4.0**
geometry and the released ODbL name table. It measures against the complete starting reach,
never the simplified display polyline.

The gate requires a unique containing source basin, a start reach assigned to that same
basin, selection within the basin rather than a nearest-overall fallback, an offset ≤1 km,
a complete acyclic downstream route to its recorded outlet, matching reach count/distance,
a positive travel estimate and a sea endpoint. Explicitly canal-sourced chains are excluded
from the comparison catalogue. Verification of captured packets also checks that source
names reproduce the published chain, then exports river-change coordinates from real reach
vertices and simplifies the map while preserving those vertices. Disconnected geometry is
rejected. A hash binds the evidence to the packet's geographic and model fields.

The site builder requires that evidence. Legacy packets with missing checks cannot silently
become approved pairs. Pairs must also have distinct source basins and terminal reaches,
different receiver groups, ≥100 km routes and ≤80 km between town points. Each paired
payload has one UI block and both complete display journeys, with unused source metadata
removed. Packets above **6,144 bytes** are excluded and counted in the build report.
Internal verification fields are removed from all polling payloads.

These are checks against the recipe's source network, not a claim that urban drains,
diversions, dams, seasonal flow or lake residence-time estimates have been independently
surveyed. The existing model caveats remain in the recipe description.

## Rotation and build continuity

The polling URL uses the setting's native true/false values and supported string forms.
The normal feed is the default. The pair feed uses fixed capacities so changes to the town
count do not require another polling URL:

| Region selection | Pair-feed slots | Cycle |
|---|---:|---:|
| Europe | 2,016 | 21 days |
| USA | 864 | 9 days |
| Canada | 288 | 3 days |
| Europe + USA | 2,880 | 30 days |
| Europe + Canada | 2,016 | 21 days |
| USA + Canada | 864 | 9 days |
| All / none | 2,880 | 30 days |

Each accepted pair occupies one slot per cycle. Normal-town screens fill spare slots.
Existing pair IDs keep their positions across builds. Retired IDs remain reserved, so a
subsequently restored pair also returns to its old position. Duplicate/corrupt history,
capacity changes and capacity exhaustion stop the build. This preserves the ≥72-hour
pair-repeat interval for a stable region selection, including catalogue updates.

The build reads the previous deployed manifest/plans before generating a replacement.
HTTP 404 for the root manifest identifies the initial launch; an incomplete existing feed
or another retrieval error fails the build. GitHub workflow concurrency serializes builds.
The local site is generated in a staging directory and swapped only after success, retaining
the previous build/history on failure. `/p/catalogue.json` records accepted pairs and
rejection reasons; `/p/plan.json` persists slot assignments; root `pair-feed.json` identifies
the feed version and capacities.

## Source-data run completed

The published access change is active and both official archives support range reads through
the Cloudflare storage host. Pyogrio's GDAL-specific certifi default initially rejected the
managed proxy certificate; `fetch._gdal_env` now selects the inherited trusted CA bundle
without disabling verification. Regional geometry was captured successfully: **938,544
European reaches**, **1,310,541 North American reaches**, **72,859 European basins**,
**163,620 US-window basins** and **157,368 Canadian-window basins**.

All **8,348 captured towns** were source-checked. The local feed includes **1,705 European
pairs and 630 US pairs**, with no Canadian pair passing the unchanged rules. Normal map
metadata was also generated for every captured town. The original 6,168-row CSV remains
discovery evidence; the accepted source-checked subset is retained separately. See
[the completed verification report](PAIR_VERIFICATION.md),
[source-checked CSV](../fixtures/review/source-checked-pairs.csv) and
[source/hash/build record](../fixtures/review/pair-verification.json).

To reproduce using the existing captured pool:

1. Fetch `reaches` and `basins` for `eu`, `us`, `ca` with `downstream.fetch` (range reads from
   the permitted HydroATLAS archives, never HydroRIVERS/HydroBASINS downloads).
2. The cleaned `name_table.csv`, `name_table_us.csv`, `name_table_ca.csv` and `name_en.csv`
   have already been captured from the repository's `name-table` release under
   `data/raw/pair-validation/`. `sources.json` retains their URLs, byte counts and hashes;
   reuse that capture for this run.
3. For each region, use `DOWNSTREAM_REGION=<region> uv run python -m downstream.pair_validation
   --towns ../data/captured-site/2026-11-13/<region>/t --names <released-table.csv>
   --name-en <released-name_en.csv> --out ../data/towns/<region>`.
4. Inspect `data/towns/<region>-pair-validation.json` and investigate flagged cases. The
   original capture stays unchanged. `fixtures/review/source-network.json.gz` retains the
   primary-geometry regression subset; `fixtures/build_pair_source_fixture.py` regenerates it.
5. Run `uv run python -m downstream.site --previous-plans https://nikokoren.github.io/downstream`.
   Inspect every regional catalogue/rejection count, all payload sizes and repeat plans;
   render the resulting source-checked packets on the supported frames. Review device output.

The ordinary full pipeline build also produces this evidence and feed. Its source checks
run while the original network and basins are already loaded, before the site step.

## Validation assets

`fixtures/review/model-pairs.json` contains reduced **actual captured** Stuttgart/Ulm,
Butte/Helena and Amos/Rouyn-Noranda packets with their source URLs and hashes. They exercise
the polling contract and rendering; they are explicitly not source-verified catalogue entries.
Their compact paired payloads are **3,072 / 3,664 / 4,297 bytes** before the small slot field.
The browser checker now checks both routes against both cards, both town callouts, map
credit and screenshot pixels. Real US packets exposed clipped portrait river steps; allowing
up to eight wrapped chain lines preserves the existing typography and shortening policy.
Paired town/country and destination fields allow three lines so Rouyn-Noranda and the Gulf
of Saint Lawrence remain readable in portrait. Normal Full retains its existing limits.

Current checks: **149 pipeline tests passed, nine data/site-dependent skips**, plus the real
primary-geometry regressions. **37,360 actual-card cases pass** across all 2,335 accepted pairs,
both languages/units and four distinct Full frames, with zero truncation. The integrity run
checked **45,918 generated JSON files**, preserved every original town ID, verified every
served comparison against its bound source evidence and enforced the payload budget.
`recipe/tools/out/pair-feed/all-pair-card-checks.json` records the full card sweep.

`test-pair-url.mjs` passes **80 native Ruby Liquid cases** with the current capacities.
`test-pair-mode.mjs` passes **1,920 native layout/setting cases** with real generated fixtures
through `DS_PAIR_PAYLOADS`; `DS_CASE_KINDS=single` covers empty-region fallbacks.
**72 current-source browser scenarios pass**: six frames × two languages × two unit systems
for each of Stuttgart/Ulm, Radford/Roanoke and Canada's ordinary Rouyn-Noranda fallback.
The existing collision policy omits a crowded river-change callout in eight Canadian portrait
cases; complete cards, routes, starting-town labels and attribution pass. EU landscape and US
portrait output were visually reviewed. Generated regional results and PNGs are under
`recipe/tools/out/pair-feed/source-checked/`. Earlier candidate screenshots remain historical
review assets; they do not override source rejection of Butte or Rouyn-Noranda. Screenshots
are individual PNGs; no large embedded gallery was generated.

Re-run pipeline pytest/Ruff, the native Liquid setting sweep with `DS_PAIR_PAYLOADS` set to
each compact regional fixture, and the real Framework browser sweep before relying on future
changes. Physical-device results and full-source validation remain separate checks.

Deploy the verified data feed before updating an installed recipe to the new polling URL.
Environment publication for data-host access does not deploy the recipe or GitHub Pages.
