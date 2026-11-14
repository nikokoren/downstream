# Review comparison fixtures

`routes.json` contains two rows, reduced to display fields, from the real Downstream build report:
https://github.com/nikokoren/downstream/releases/download/build-report/towns.csv

Captured 2026-11-13. The source SHA256 is recorded in the JSON. No route geometry or travel
duration was inferred for Nuremberg. The Munich map and duration in the review use the existing
`recipe/preview/munich.json` fixture.

River network: HydroATLAS v1.0, Linke et al. 2019 and Lehner & Grill 2013, CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Changed: routes and distances computed by the
Downstream pipeline; these rows are reduced from its build report. Towns: GeoNames, CC BY 4.0.
Sea names: Natural Earth, public domain.

Contains information from OpenStreetMap (https://www.openstreetmap.org/copyright), available
under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ . © OpenStreetMap contributors. This extract is
available under ODbL 1.0. The complete derivative name table and its notice are published at
https://github.com/nikokoren/downstream/releases/tag/name-table .

## Geographic battle review

`battle-reference.json` contains derived, captured review geometry. Munich's model polyline is
copied from the committed preview fixture. Nürnberg's reference geometry is assembled from the
repository's released OSM Bavaria waterways and Natural Earth 1:10m river/settlement geometry.
It is explicitly marked `geometry_kind: reference`; it is not the deployed HydroATLAS path.
Source URLs, full-input SHA256 values, capture date and between-source joins are in the fixture.

The OSM extract is © OpenStreetMap contributors, ODbL 1.0. This derivative review extract is
available under ODbL 1.0. Source waterways:
https://github.com/nikokoren/downstream/releases/tag/osm-waterways-europe-germany-bayern .
Natural Earth rivers, settlements, coastlines and administrative boundaries are public domain:
https://github.com/nvkelso/natural-earth-vector . `battle-basemap.geojson` clips and simplifies
the coastline/boundaries to the review's European window. Munich's model geometry and the
reported distances retain the HydroATLAS credit above. No NC-licensed data is used.

The selected comparison now reuses the shipping `ds_box` twice, including intermediate steps
and the duration line. Nürnberg's card explicitly marks its missing estimate unavailable.
Munich's committed preview additionally carries the captured Isar/Danube shared OSM vertex
as its hand-off metadata. This is geographic evidence for the preview, not a newly captured
HydroATLAS reach boundary; subsequent model builds export their own source-network vertex.
The review simplifies Nürnberg's reference to the normal map budget while retaining the
three named joins. Its geometry stays a reference, not a replacement production route.

## Pair discovery

`pair-search.json` and `pair-shortlist.json` combine captured rows from the same model report
with GeoNames city coordinates, joined by exact GeoNames ID. Report fields retain the
HydroATLAS, GeoNames, Natural Earth and OpenStreetMap credits/licences above. Coordinates are
GeoNames data (https://www.geonames.org/, CC BY 4.0), distributed in GeoNamesCache 3.0.2:
https://pypi.org/project/geonamescache/3.0.2/ . Its Python package code is MIT; no package code
is copied into the recipe. The data is not relicensed as MIT.

The versioned wheel URL, archive SHA256, city-file SHA256, report URL/SHA256 and capture date
are in the fixtures. Only a reduced source subset and 26 provisional pairs are retained here;
raw package/data downloads stay in ignored `data/`. No routes or travel durations were inferred
from town distances. Candidate discovery is separate from route/basin/time and screen review,
and neither fixture is an approved production catalogue.

`pair-rotation.json` is reduced from the same 417-candidate search and retains its source
credits/licences. It tests complete-pool ordering and repeat intervals, without approving
the candidates. The extra unselected coordinates in `pair-search.json` are actual GeoNames
records for Pasing, Bogenhausen and Unterhaching. They are controls for the existing recipe
eligibility boundary, not additional towns offered by this feature.

## Complete published-rotation search

`drainage-divide-candidates.csv` is a derived review catalogue from the published Europe,
USA and Canada model packets captured on 13 November 2026. At the author's 80 km limit it
retains 6,168 combinations of
eligible towns, their model river chains, destinations, route distances and travel estimates,
with WGS84 town-to-town distances computed for this search. It does not approve the model
routes or add towns to the normal rotation. The 4,447 US candidates and one Canadian candidate
have unknown start offsets. All previous 2,629 candidates at 50 km remain included; the audit
summary records the before/after counts. One European candidate flags a nearest-overall start.

`pair-audit.json` records the source rotation URLs and hashes, capture timestamp, the complete
ignored capture-manifest hash, report hash, derived CSV hash, counts and checks. All source
credits above apply: HydroATLAS CC BY 4.0 for the routed network; HydroLAKES CC BY 4.0 for
lake residence-time estimates; GeoNames CC BY 4.0 for towns; Natural Earth public domain for
marine names; and © OpenStreetMap contributors, ODbL 1.0, for river names. This derived name
extract is available under ODbL 1.0. Full downloaded packets remain in ignored `data/`.

`model-pairs.json` reduces six packets from the same capture to their geographic/model
fields, removing redundant UI/display fields. Coordinates, geometry, chains, distances and
estimated durations are unchanged. Original packet URLs/SHA256 values are retained in each
pair. The HydroATLAS, HydroLAKES, GeoNames, Natural Earth and OpenStreetMap credits and
licences above apply; this derived river-name extract is available under ODbL 1.0.

## Original-source verification subset

`source-network.json.gz` retains only the complete original river routes and relevant basin
polygons for Stuttgart, Ulm, Weißenburg in Bayern, Pfaffenhofen an der Ilm and Mountsorrel.
Geometry and attributes come from **HydroATLAS v1.0** (RiverATLAS file 20087486 and BasinATLAS
file 20087237 on Figshare), Linke et al. 2019 and Lehner & Grill 2013, **CC BY 4.0**:
https://creativecommons.org/licenses/by/4.0/ . Changed: unrelated network features omitted;
original selected geometry/attributes retained as GeoJSON, with captured model fields and
source-name mappings. Archive URLs, derived-file hashes and original packet URLs/hashes are
stored in the fixture; `fixtures/build_pair_source_fixture.py` records the extraction method.

Names and captured model packets retain the OpenStreetMap ODbL, GeoNames CC BY, Natural
Earth public-domain and HydroLAKES CC BY credits above. This derived name extract is available
under ODbL 1.0. Full downloaded source layers remain in ignored `data/`.

`source-checked-pairs.csv` is a further derived subset of the candidate catalogue, adding
measured start distances, basin/outlet IDs and source-backed river-change counts. The same
credits/licences apply. `pair-verification.json` retains source URLs, exact file hashes,
thresholds, exclusions and feed-build results. These establish model-source consistency,
not an independent physical survey of current rivers or engineered drainage.
