# River changes and two journeys on one map

The author selected two separate cards at the bottom edges (2026-11-13).
The **Explore drainage divides** setting (`watershed_pairs`, default off) enables the comparison
only in Full. The map heading has been removed. Other views, and Full with the setting off,
use the primary journey from a paired packet. A single-town packet still works in either mode.
See `PAIR_SELECTION.md` for the full candidate pool, review sample and 15-minute rotation policy.
**Map labels** (`map_labels`) is on by default and controls town/river callouts independently
in every view. Turning it off keeps the journey cards, path markers, globe and map credit. Each now uses the
existing text-box layout: intro, town and country, intermediate rivers, destination, distance
and approximate travel time. Town names identify the paths. Both strokes and start markers
match. Letter badges and labels at the sea are removed; endpoint rings remain.

The normal views now use the same town and river-change callouts. The approved optional globe
remains available on the single full view. Labels use Framework typography/paint and SVG
leaders, avoiding routes, other labels, cards, globe and attribution. Small mashups can omit a
label if there is no clear position; they retain the existing text explanation.

## Implementation

- `recipe/src/shared.liquid`: `ds_box` accepts a left/right position; `ds_route` supplies escaped,
  scoped town/transition metadata. The map code draws one or two paths with identical treatment.
- `recipe/src/full.liquid`: a normal town packet shows the existing view; with the setting on, a packet with exactly
  two `routes` shows two copies of `ds_box` on a shared map, framing the union above both cards.
- Other views keep their normal single-town layout, with map labels added.
- `recipe/tools/map-labels.js`: shared collision placement, bundled into Shared by
  `bundle-map-labels.mjs`. There is no separate review implementation of the labels or cards.
- `pipeline/downstream/naming.py` retains the first source-reach index of each named group
  through cleanup. `paths.map_changes()` exports the actual hand-off vertex and canonical
  names. `simplify_to()` protects those vertices within the 120-point budget. Positions are
  never inferred from the cleaned chain's accumulated km.
  Only river-to-river changes are labeled: cleaned lake runs can omit returns to the same
  river, so consecutive displayed lakes are not assumed to meet directly.
- New builds add `changes: [{at: [lon, lat], from: {en/de/local}, to: {en/de/local}}]` to normal
  packets. Older packets still label their start town; rebuilding data supplies the hand-offs.
- `paths.main_all()` now includes `travel_days` and `lake_days` in the build report so future
  captured report rows carry the real estimate too.

Full's paired packet has one shared `ui` and two complete route/display objects in `routes`.
Each route supplies `town`, `place`, `chain`, `end_text`, `distance`, `travel`, `polyline` and
`changes`. Units and language apply to both cards. Missing time data is explicitly marked
unavailable. The polling URL and existing single-town rotation have not been changed; no new
mode was activated or published.

## Review data and remaining limit

Munich uses `recipe/preview/munich.json`'s actual model path and estimate: **about 3–8 weeks**.
Its preview hand-off at Isar/Danube is a captured shared OSM vertex; new model builds export
the corresponding source-network boundary directly.

Nürnberg's captured build-report row has the real model distance and river chain but **no
travel duration**. Its review map follows actual OSM Pegnitz/Regnitz and Natural Earth
Main/Rhine/Nederrijn/Lek linework, explicitly marked as reference geometry. It is not the
published HydroATLAS model path. Its card therefore says the time estimate is unavailable;
no duration was inferred from reference linework or distance. River joins use actual source
vertices. Two cross-dataset transfers span about 732 m and 142 m; delta arms fold into Rhine
as in D12. The review simplification retains all named hand-offs.

`fixtures/review/battle-reference.json`, `battle-basemap.geojson` and `NOTICE.md` record the
source URLs, input checksums, licensing and resolution limits. The offline basemap is real
Natural Earth 1:10m coastline/borders. No raw downloads or generated captures are committed.

Access to `nikokoren.github.io` is still blocked by this environment's active network policy,
so the exact published Nürnberg geometry and duration could not be captured. Saved domain
additions have not applied to the running environment. No environment publication or live
recipe deployment was performed. Hosted TRMNL tiles and physical devices remain unverified.

## Review and reproduce

Prefer the plain images in `recipe/tools/out/battle/`:

- `watershed-pair-v4.png`: the updated cards and map;
- `watershed-pair-portrait-v4.png`: the narrow portrait layout;
- `normal-labels-v4.png`: the normal view with town, river hand-off and globe;
- `layout-comparison.png`: the updated paired and normal views together.

`watershed-battle-light.html` is an optional small board that requests one adjacent PNG at a
time. It never embeds the screenshot corpus. Keep it beside the PNGs when downloading it.
The older shared-footer option has been removed from the board.

From the repository root, with Framework/MapLibre/font assets cached and Ruby Liquid available:

```
export PATH="/workspace/.tools/ruby-3.4.7/bin:$PATH"
export GEM_HOME="/workspace/.tools/gems"
node recipe/tools/bundle-map-labels.mjs --check
node recipe/tools/battle-preview.mjs
node recipe/tools/battle-gallery.mjs
```

The prepared environment uses `pipeline/.venv/bin/python` for `battle-payload.py` (`DS_PYTHON`
can override it). This formats both cards from backend locales and the captured data; it does
not invent missing values. The pair has one UI block and stays within the ~6 KB payload budget.
The browser sweep covers two modes × four devices/orientations × en/de × metric/imperial ×
river changes on/off (town labels stay on): 64 captures. It checks the complete card values,
clamping, label/obstacle collisions, route framing and actual ink on every path. `results.json`
records each result. Subsets use `BATTLE_MODES`, `BATTLE_DEVICES`, `BATTLE_LANGS` and
`BATTLE_UNITS`; `BATTLE_APPEND=1` merges a corrected subset into an existing sweep. Only merge
when the untouched cases remain applicable to the change.

For normal views and mashups, use `OFFLINE_BASEMAP=1 WORLD_MAP=both UNITS=all` with
`recipe/tools/render-check.mjs --preview` and Chromium configured. This checks the real
Framework layouts, multiple scoped plugin instances, globe and labels. Pipeline tests cover
source-vertex preservation in both geometry directions and source-piece name boundaries.
These checks establish browser layout and source-geometry behavior, not hosted-tile or
physical-device results. Latest validation counts are recorded in `PROJECT.md`.
