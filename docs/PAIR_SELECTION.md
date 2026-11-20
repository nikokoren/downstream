# Finding towns across the divide

> **Superseded on 2026-11-20 (D25).** The pair catalogue, its 72-hour planner and fixed pair
> capacities are retired. `<region>/p/<n>.json` now holds slot n's town from the normal rotation
> (`t/<n>.json`) plus its companion, chosen by `pipeline/downstream/companions.py`. Source
> verification below still applies to companions closer than 80 km. Kept as history.

Use an automatic geographic search over the existing recipe's eligible town/model results.
Keep every validated pair. A small representative sample helps review, and does not limit the
production catalogue. Town names alone do not establish a watershed: check the actual town
point, source basin and model route.

## What is implemented

The opt-in setting is **Explore drainage divides**, off by default:

> In full screen, follow rain from two nearby towns to different seas. Smaller layouts show one journey.

Only Full can render the comparison. With the setting off, or in either half view or the
quadrant, a paired packet shows its primary town as a normal single journey. A single-town
packet also remains usable with the setting on. The map heading has been removed.

**Map labels** (`map_labels`) is a separate setting, on by default, for town and river-change
callouts in both normal and comparison views. The journey cards and map credit stay visible
when it is off.

The layout/settings and paired-feed builder are ready in source. The local polling URL now
selects `/p/` with the setting enabled; the published recipe still uses its existing feed.
The new builder requires source verification and preserves pair slots across builds.
Execution against the original river/basin geometry is now complete. **2,335 pairs** pass
and are included in the local feed: Europe 1,705, USA 630, Canada zero. See
[source verification](PAIR_VERIFICATION.md) and [feed implementation](PAIR_FEED.md).
The broader 6,168 discovery candidates remain recorded separately. Nothing is deployed.

## Cadence and town eligibility — author clarification, 13 November 2026

The recipe changes data every **15 minutes** (`site.SLOT_SECONDS = 900`), not every 3–5 minutes.
Plan conservatively for continuous display, even though this recipe is normally one entry in a
playlist. The old 20–30-pair launch target was too small.

| Unique pairs | Continuous rotation at 15 minutes |
|---|---|
| 30 | 7½ hours |
| 192 | 2 days |
| 288 | 3 days |
| 417 | 4 days, 8 hours, 15 minutes |
| 500 | 5 days, 5 hours |
| 1,720 | 17 days, 22 hours |

Retain the full validated pool and aim for several hundred pairs where available. The planner
uses a **72-hour minimum pair-repeat interval**. For a smaller regional pool, it distributes
comparisons through at least 288 slots and fills the gaps with the normal single-town rotation.
It never pads the pool by reversing the same pair. These guarantees apply to a stable plan;
published catalogue updates must preserve recent assignments when integrating the feed.

Town eligibility is **exactly the same as the existing recipe**, owned by `towns.region_towns`:
use the current city-size rules, district exclusions, nearby-suburb exclusions (D24), geographic
coverage and explicit extra-town allowlist. Read only the resulting normal-rotation model
files, or its eligible build-report rows. The coordinate cache supplies positions for matching
IDs; it cannot add a neighbourhood or smaller town that the recipe excluded. There is no
separate low-population pool. `towns.py`, its classification policy and the normal rotation
have not been changed.

`rotation_order()` starts with a seeded shuffle and uses bounded lookahead to prefer different
recent towns, geographic areas and river systems. All unique pairs remain in the plan, with no
pair repeated before the whole cycle. Variety constraints are preferences so sparse pools do
not get stuck. `rotation_slots()` uses the real cadence and adds normal-town slots when needed.
The review sample's 75 km separation and no-repeated-town rule apply only to that sample.

## Discovery pass: 80 km across all published rotations, 13 November 2026

Published data is now accessible. All **8,348 unique eligible town packets** were captured
successfully: Europe 5,280, USA 2,816, Canada 252. At the author's widened **80 km** limit,
the complete search retains **1,720 European candidates**, **4,447 preliminary US candidates**
and **one Canadian candidate**. That adds **3,539 pairs**, retaining every pair from the
50 km pass (424/2,205/0). The different-receiver and 100 km minimum-route rules are unchanged.
At discovery time, matching build-report rows supplied the European start-distance check;
North American packets omitted that measurement, leaving those leads awaiting the same
≤1 km check. One European pair used a nearest-overall start fallback and was flagged for
basin review. There are no
qualifying US–Canada cross-border pairs. Town-selection rules are unchanged; `find_pairs()`
and the CLI now default to 80 km.

All downloaded packets pass geometry and display-field completeness checks. Subsequent original
source checks, paired-payload and browser review are complete; **2,335 pairs** enter the local
feed. See [the verification report](PAIR_VERIFICATION.md) for accepted counts and exclusions.
See [the full results and limitations](PAIR_SEARCH_RESULTS.md), the
[6,168-row candidate CSV](../fixtures/review/drainage-divide-candidates.csv) and the
[captured audit summary](../fixtures/review/pair-audit.json). Regional data and review-only
rotation plans are in ignored `data/pair-candidates/2026-11-13/80km/`. Nothing is activated or
published. The earlier European-only search below is retained as provenance.

## Earlier search: captured European report, 13 November 2026

`downstream.pairs` joins the captured model build report to GeoNames coordinates by exact ID,
without fuzzy name matches. Of 5,384 report rows, 5,280 are in the rotation and 5,261 of those
end in a sea. Coordinates matched **5,234 sea-ending towns**; 27 IDs were unavailable in the
GeoNames cache and were left out. Other regions have not been searched in this pass.

Initial filters:

- At most **50 km apart**, measured on the WGS84 ellipsoid between town points.
- Different receiver groups, rather than different spellings or nested marine labels.
- Both model paths at least **100 km**, to favour journeys that explain the contrast clearly.
- A known town-to-start-reach offset no greater than **1 km**. Unknown offsets in older model
  JSONs remain a review requirement, not a verified pass.

The ungrouped pass returned 456 pairs. Consolidating receiver names leaves **417 candidates**.
For example, Baltic Sea and Gulf of Bothnia should not qualify as opposite destinations.
The initial editorial grouping also folds Mediterranean sub-seas, Black Sea/Azov and related
Atlantic/Pacific coastal labels. This is a conservative discovery policy, not a scientific
basin taxonomy. Cards retain their actual named endpoint; the group names stay off screen.

The full pool retains **all 417 candidates**. A distance-first review sample removes repeated
towns and keeps pair midpoints at least **75 km** apart, giving 26 illustrative examples.
These are leads for review, not approved production pairs; the sample is not the catalogue. Nürnberg–Munich, the layout example, is about **150.9 km** apart
and does not meet this tighter proximity rule.

## Review examples from the full pool

Distances are between town points, rounded to 0.1 km. Destinations come from the captured
model report. Full source routes and durations were not available for verification in this
pass; no missing duration was invented.

| Town | Destination | Neighbour | Destination | Apart |
|---|---|---|---|---|
| Saint-Etienne (FR) | Bay of Biscay | Saint-Chamond (FR) | Gulf of Lion | 10.7 km |
| Wednesbury (GB) | North Sea | Halesowen (GB) | Bristol Channel | 11.6 km |
| Valašské Meziříčí (CZ) | Black Sea | Nový Jičín (CZ) | Baltic Sea | 13.9 km |
| Balingen (DE) | North Sea | Albstadt (DE) | Black Sea | 14.3 km |
| Neuchâtel (CH) | North Sea | La Chaux-de-Fonds (CH) | Gulf of Lion | 14.4 km |
| Heidenheim (DE) | Black Sea | Aalen (DE) | North Sea | 18.3 km |
| Suva Reka (XK) | Adriatic Sea | Shtime (XK) | Black Sea | 19.5 km |
| Wangen (DE) | North Sea | Leutkirch (DE) | Black Sea | 20.8 km |
| Spišská Nová Ves (SK) | Black Sea | Kežmarok (SK) | Baltic Sea | 23.2 km |
| Löbau (DE) | North Sea | Görlitz (DE) | Baltic Sea | 23.3 km |
| Eberswalde (DE) | Baltic Sea | Bernau bei Berlin (DE) | North Sea | 23.3 km |
| Jihlava (CZ) | Black Sea | Havlíčkův Brod (CZ) | North Sea | 23.5 km |
| Trutnov (CZ) | North Sea | Kamienna Góra (PL) | Baltic Sea | 26.1 km |
| Sofia (BG) | Black Sea | Pernik (BG) | Aegean Sea | 26.4 km |
| Lviv (UA) | Baltic Sea | Horodok (UA) | Black Sea | 27.6 km |
| Troyan Municipality (BG) | Black Sea | Karlovo (BG) | Aegean Sea | 29.8 km |
| Ivatsevichy (BY) | Baltic Sea | Byaroza (BY) | Black Sea | 31.2 km |
| Sulzbach-Rosenberg (DE) | Black Sea | Neumarkt in der Oberpfalz (DE) | North Sea | 32.0 km |
| Saint-Quentin (FR) | English Channel | Cambrai (FR) | North Sea | 36.6 km |
| Minsk (BY) | Black Sea | Dzyarzhynsk (BY) | Baltic Sea | 37.4 km |
| Waren (DE) | North Sea | Neubrandenburg (DE) | Baltic Sea | 38.7 km |
| Sarajevo (BA) | Black Sea | Konjic (BA) | Adriatic Sea | 38.7 km |
| Loja (ES) | North Atlantic Ocean | Antequera (ES) | Alboran Sea | 40.0 km |
| Zolochiv (UA) | Baltic Sea | Berezhany (UA) | Black Sea | 40.3 km |
| Verdun (FR) | North Sea | Bar-le-Duc (FR) | English Channel | 46.0 km |
| Šumperk (CZ) | Black Sea | Głuchołazy (PL) | Baltic Sea | 48.8 km |

## Verify before selecting the launch catalogue

1. **Check the start, basin and outlet.** Obtain each full model packet, recompute proximity using its stored coordinates,
   and verify that the town point lies in the selected BasinATLAS basin and that its routed reach belongs there. Check
   nearby streams at the divide, nearest-overall fallbacks and towns spanning more than one
   watershed. Confirm genuinely different drainage/outlets, rather than a marine-label artefact.
2. **Require both complete journeys.** Use model geometry, canonical river names, endpoint,
   total distance and the existing river-plus-lake time estimate. Reject incomplete geometry or
   missing duration for the launch catalogue. The captured report is sufficient for discovery,
   not for shipping two finished text boxes.
3. **Render the actual pair.** Check OG/X, both orientations, English/German and km/mi. Keep
   both complete routes, labels, captions and attribution readable. Very close origins can
   coincide at whole-route scale, so inspect whether the town callouts and diverging paths
   remain understandable. Reject pairs that only look good in a large desktop preview.
4. **Curate variety.** Prefer strong contrasts and a spread of divides/countries, mix familiar
   eligible towns, and use the rotation order to spread related comparisons through the cycle.
   Keep all validated GeoNames pairs in a versioned catalogue rather than capping it at the
   review sample. Automate source, route, completeness and rendering checks; review flagged
   cases and a representative sample.
5. **Build and rotate the catalogue.** Resolve approved IDs against model outputs at build time,
   share one UI block per paired packet, enforce the ~6 KB budget, and generate a deterministic
   paired feed respecting Region. Full uses both journeys; smaller layouts keep the primary.
   Wire the polling choice to the setting when the verified feed exists.

Use the same eligible town pool for Europe, the USA and Canada. Grow the catalogue by
validating more combinations among those towns and covering all selected regions, while
retaining the proximity and routing-quality checks. The small-settlement expansion proposed
earlier in the chat was dropped after the author's classification clarification. Raw cache
files do not confer eligibility. The search uses a spatial grid and exact final distances;
it does not reroute every possible combination of towns.

## Reproduce and provenance

From `pipeline/`, after capturing the report and coordinate cache:

```
uv run python -m downstream.pairs \
  --report /tmp/downstream-towns-report.csv \
  --coordinates ../data/raw/review/geonamescache-3.0.2-cities15000.json \
  --max-km 80 \
  --out ../data/pair-candidates/eu
```

The tool writes all candidates to JSON/CSV, a Markdown review sample and `rotation-plan.json`.
Thresholds are adjustable with `--max-km` (default 80), `--max-start-km` and `--min-path-km`.
Use `--max-km 50` to reproduce the historical report-only 417-candidate search above.
`--review-sample` (legacy alias `--shortlist`) changes only the review example count.
`--min-repeat-hours` defaults to 72; cadence is read from the recipe data builder. After a full model build,
use `--towns ../data/towns/eu` (or several normal-rotation regional folders) instead of report/coordinates.
Outputs are candidates only; neither command changes the rotation or publishes data.

Report source: https://github.com/nikokoren/downstream/releases/download/build-report/towns.csv .
Coordinates: GeoNames distributed in GeoNamesCache **3.0.2**, obtained from its PyPI wheel
without installing another dependency. Original dataset credit/licence remains GeoNames,
CC BY; the package code is MIT. Versioned source URLs and SHA256 values are recorded in
`fixtures/review/pair-search.json` and `pair-shortlist.json`; see their `NOTICE.md` for attribution.
Raw inputs and generated full candidate files remain in ignored `data/` / temporary storage.
The small captured shortlist and test subset are retained for review and reproducibility.

The earlier pass was limited by network access. The full-model capture resolved that access
problem and supplied routes and durations for every eligible town. Original-source verification
then selected the accepted subset, recorded in `PAIR_VERIFICATION.md`. The discovery outputs
remain provenance; successful downloads alone did not approve candidates. Latest code and
browser test counts are recorded in `PROJECT.md`.
