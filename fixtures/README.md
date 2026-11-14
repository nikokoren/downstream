Captured payloads only (working method #1), plus the planned storefront fixture generator
(R23: Munich, en + de).

`review/drainage-divide-candidates.csv` retains all **6,168 model-based candidates** from the
13 November 2026 capture of the published Europe/USA/Canada rotations. Each row contains both
town IDs, intermediate rivers, model destinations, distances and bilingual travel ranges.
`review/pair-audit.json` records coverage, thresholds, source hashes and outstanding checks.
At the author's widened **80 km** limit, Europe has 1,720 candidates with known start offsets;
the 4,447 US leads and one Canadian lead still need that check. One European pair is flagged
for a nearest-overall start fallback. All 2,629 previous 50 km candidates remain included.
These derived review outputs are not an approved catalogue.
See `docs/PAIR_SEARCH_RESULTS.md` and the fixture notice for sources and limitations.

`review/model-pairs.json` retains reduced actual model packets for Stuttgart/Ulm,
Butte/Helena and Amos/Rouyn-Noranda, with the original capture URLs and hashes. They exercise
paired-payload compaction, bilingual river chains, native Liquid settings and real browser
frames. These are rendering/contract fixtures, not evidence of source-basin verification.

`review/source-checked-pairs.csv` is the **2,335-pair source-checked subset**, distinct from
the 6,168 discovery candidates. `review/pair-verification.json` records the actual source
checks, file hashes, exclusion reasons and complete local feed integrity results.

`review/source-network.json.gz` contains **1,027 original HydroATLAS reaches and six original
basin polygons** for five captured towns, with their original model packets and released
source names. `build_pair_source_fixture.py` regenerates it from the cached original data.
It tests real basin/offset/outlet checks, incomplete coverage, the nearby wrong-basin
Pfaffenhofen reach and normal labels for Mountsorrel's rejected comparison. See the notice
and `docs/PAIR_VERIFICATION.md` for sources, modifications and the limits of these checks.

`review/routes.json` contains two real build-report rows for the paired-journey visual.
`review/battle-reference.json` captures geographic reference geometry and real river joins;
`battle-basemap.geojson` contains the offline review coastlines/borders. Source, capture date,
checksums and attribution are recorded with the fixtures and their NOTICE.md. Nürnberg's
captured report has no duration; the review must not invent one. Munich's existing model
estimate remains in `recipe/preview/munich.json`.

`review/pair-search.json` is a small real report/GeoNames subset for spatial-search regression
tests. `review/pair-shortlist.json` records the 26 provisional European pairs, thresholds,
coverage, source versions and checksums. These are discovery evidence, not an approved or
activated comparison catalogue. See `docs/PAIR_SELECTION.md` for the full process and results.

`review/pair-rotation.json` retains all 417 captured candidate identities for rotation tests.
The review sample is not a catalogue cap. `pair-search.json` also includes real coordinate
records for unselected Munich neighbourhoods/suburbs to prove that the coordinate cache
cannot admit places absent from the normal recipe town list.
