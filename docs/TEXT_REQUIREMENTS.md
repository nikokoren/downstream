# Text requirements (R14)

**Draft, 2026-09-30.** Not approved yet; no copy is written until it is. Lengths below are
characters measured on the 6,918 town files of the current build (`data/towns/*.json`), not yet
on a device. The render sweep (DESIGN_PHILOSOPHY part A §7) turns them into pixel budgets per view
and fails any cut-off text.

## Where the words come from

All words come from the backend in English and German (R13); templates contain none. The town files
already carry the data words (town, rivers, endpoint, with `en`/`de` where curated). The fixed UI
words (labels, "a stream", credits) are not in the payload yet. Proposal: a small `ui` block in
every town file with both languages (~300 B; payload max 4.1 KB today, budget 6 KB), and a
language setting (English / Deutsch) that picks one. Alternative: a second Polling URL with a
shared `locales.json`, which renames every variable to `IDX_0`/`IDX_1`.

## Screen states

The brief's list (R9, R18, R19) predates D8 (towns instead of the user's location):

| State | Towns now | Notes |
|---|---|---|
| Ends in a sea | 6,899 | Normal case. In 3,624 the stream's end is not on the named sea's shore (e.g. Limhamn: 26 km, across the Øresund), so the wording must not say "flows straight into". |
| Ends in a lake | 3 | Lake Vegoritida (1), Paralimni Lake (2, no German name: shows the English one). |
| Ends in a sink (no named water) | 16 | Karst and closed basins (Salento, Greek plateaus, Nikšić, Trebinje, …). Needs its own headline wording. |
| Whole path unnamed | 340 | Chain is just "a stream" → endpoint (Limhamn). |
| Start already in the sea / no reach nearby | 0 | Can't reach the screen: such towns are left out of the rotation (D14). |
| Location not set (R19) | — | Gone with D8. |
| Error (R18) | — | Open question below: if the file can't be fetched, the backend's words are missing too. |
| Map failed to draw | any | Text still shows (DESIGN_PHILOSOPHY §4). |

## Slots

Text order from DESIGN_PHILOSOPHY part B. Budgets are proposals; "clamp" means the framework's
`clamp` truncation.

| # | Slot | Views | Source | Casing | Length now (median / p95 / max) | Budget proposal | States |
|---|---|---|---|---|---|---|---|
| 1 | Town | all | `town.en` / `town.de` (GeoNames, D17) | as GeoNames | en 8 / 19 / 40; de 9 / 19 / 55 | 1 line, clamp | all |
| 2 | Endpoint (headline) | all | `end.display.en/de` (curated), else `end.name` | as curated | en 9 / 20 / 20; de 10 / 18 / 21 | 1 line, never clamped (max 21 fits) | sea, lake |
| 2b | Sink headline | all | UI word | sentence case | — | ≤ 24 | sink |
| 3 | Label for 2 | all but quadrant | UI word ("Ends in" / "Endet in") | sentence case | — | ≤ 12 | all |
| 4 | River chain | all but quadrant | `chain[].name` en/de/local; unnamed → UI word | as source | steps 2 / 6 / 35; joined en 23 / 67 / 453 chars; single names 7 / 17 / 53 | full: all steps up to a per-view maximum, then "+N more"; half views ~4 steps; quadrant: none | all |
| 4b | Unnamed step | inside 4 | UI word ("a stream" / "ein Bach") | lower case | — | ≤ 10 | 1,585 towns start unnamed; 151 unnamed steps later in a chain |
| 5 | Distance | full, half | `total_km`, formatted per language (en "1,806 km", de "1.806 km") | — | 224 / 1,806 / 2,922 km | ≤ 9 | all |
| 5b | Label for 5 | full, half | UI word ("Distance" / "Strecke") | sentence case | — | ≤ 10 | all |
| 6 | Credits | all | UI words | as names | — | 1 line: "HydroATLAS · GeoNames · © OpenStreetMap" (≈ 40) | all |

Quadrant (DESIGN_PHILOSOPHY §3): map plus one strip, town and endpoint (slots 1 and 2), plus
credits.

## Wording rules

- **Label + value, not sentences**: German needs a case and an article per name ("im Schwarzen
  Meer", "in der Ostsee", "in den Bodensee"). A label ("Endet in") next to the plain name avoids a
  grammar table for 30 endpoints and thousands of rivers.
- Plain language (R15): no "catchment", "estuary", "confluence" on screen.
- No estimates are shown today (distances come from the river data, not from an assumption), so no
  estimate label (R10) yet. It becomes required if travel time (D3) is ever added.
- Numbers use the language's own separators.

## Attribution strings (R16)

- On screen: one line, e.g. "HydroATLAS · GeoNames · © OpenStreetMap". CC BY 4.0 allows attribution
  "in any reasonable manner based on the medium"; the full credits (creators, citations, license
  links, modification notes) are in the README and store listing (D5, R17).
- The map adds its own "© OpenStreetMap contributors" label (TRMNLMaps, bottom right). Whether that
  label also covers the OSM river names, or the credit line must name OSM again, is open.
- Natural Earth: "Made with Natural Earth" in README/listing only (courtesy, not required).

## Open questions for the author

1. UI words in every town file (`ui` block) or a shared `locales.json`?
2. Wording for the sink state (16 towns), e.g. "Disappears underground" / "Versickert im Boden".
3. "a stream" / "ein Bach" for unnamed first steps: fine?
4. Error state (R18): TRMNL keeps showing the last screen when a fetch fails (not verified). Is a
   dedicated error screen still needed? It would have to use words not from the backend.
5. Credit line: does the map's own OSM label suffice?

## Found while measuring (data, not copy)

- **Iisalmi (Finland) has 35 steps**: "Lake Saimaa → Raudanjoki → Lake Saimaa → Onkivesi → …".
  Finland's lakes are named both by basin ("Kallavesi", "Pihlajavesi") and as "Lake Saimaa"/"Saimaa",
  so the lake-zigzag merge doesn't catch them. Chains with 12+ steps: 22 towns. To look at before
  the views.
- **German town name from GeoNames**: Saint-Quentin-en-Yvelines is "Communauté d’agglomération de
  Saint-Quentin-en-Yvelines" (55 chars) in German, the name of the municipal association, not of
  the town. D17 says town names come straight from GeoNames; slot 1's clamp keeps it on one line.
