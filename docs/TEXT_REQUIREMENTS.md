# Text requirements (R14)

**Decided 2026-09-30** (author's answers below). Wording lives in `pipeline/downstream/locales.py`. Lengths below are
characters measured on the 6,918 town files of the current build (`data/towns/*.json`), not yet
on a device. The render sweep (DESIGN_PHILOSOPHY part A §7) turns them into pixel budgets per view
and fails any cut-off text.

## Where the words come from

All words come from the backend in English and German (R13); templates contain none, except the
error screen (below). Every town file carries a `ui` block with both languages (author,
2026-09-30), written by `downstream.site` from `pipeline/downstream/locales.py`, plus `distance`,
pre-formatted for each language and unit.

## Settings

- **Language**: English / Deutsch. Picks `ui.en`/`ui.de`, the curated `en`/`de` names, and the
  number separators ("1,806" / "1.806").
- **Units** (author, 2026-09-30): Metric (km) / Imperial (mi), a separate setting, **default
  metric**; an empty value counts as metric. Not tied to the language. The template shows
  `distance.<language>.<units>`, e.g. `distance.de.imperial` = "1.122 mi".

## Screen states

The brief's list (R9, R18, R19) predates D8 (towns instead of the user's location):

| State | Towns now | Notes |
|---|---|---|
| Ends in a sea | 6,899 | Normal case. In 3,624 the stream's end is not on the named sea's shore (e.g. Limhamn: 26 km, across the Øresund), so the wording must not say "flows straight into". |
| Ends in a lake | 3 | Lake Vegoritida (1), Paralimni Lake (2, no German name: shows the English one). |
| Ends in a sink (no named water) | 16 | Karst and closed basins (Salento, Greek plateaus, Nikšić, Trebinje, …). Headline "Disappears underground" / "Versickert im Boden". |
| Whole path unnamed | 340 | Chain is just "a stream" → endpoint (Limhamn). |
| Start already in the sea / no reach nearby | 0 | Can't reach the screen: such towns are left out of the rotation (D14). |
| Location not set (R19) | — | Gone with D8. |
| Error (R18) | — | Whimsical error screen, words in the template (see below). |
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
| 4 | River chain | all but quadrant | `chain[].name` en/de/local; unnamed → `ui.a_stream` | as source | steps 2 / 6 / 35 before the Finland fix; joined en 23 / 67 / 453 chars; single names 7 / 17 / 53 | full: all steps up to a per-view maximum, then "+N more"; half views ~4 steps; quadrant: none | all |
| 4b | Unnamed step | inside 4 | UI word ("a stream" / "ein Bach") | lower case | — | ≤ 10 | 1,585 towns start unnamed; 151 unnamed steps later in a chain |
| 5 | Distance | full, half | `distance.<language>.<units>` ("1,806 km", "1.806 km", "1,122 mi"; under 10 with one decimal) | — | 224 / 1,806 / 2,922 km | ≤ 9 | all |
| 5b | Label for 5 | full, half | UI word ("Distance" / "Strecke") | sentence case | — | ≤ 10 | all |
| 6 | Credits | all | `ui.credits` | as names | — | 1 line: "HydroATLAS · GeoNames" (21); the map carries the OpenStreetMap credit | all |

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

- On screen: "HydroATLAS · GeoNames". CC BY 4.0 allows attribution "in any reasonable manner based
  on the medium"; the full credits (creators, citations, license links, modification notes) are in
  the README and store listing (D5, R17).
- OpenStreetMap: the map's own "© OpenStreetMap contributors" label (TRMNLMaps, bottom right) is
  enough; no second OSM credit (author, 2026-09-30). It must stay visible in every view.
- Natural Earth: "Made with Natural Earth" in README/listing only (courtesy, not required).

## Error screen (R18)

Shown when the town file can't be read. It can't use the backend's words (they come in the same
file), so this is the one place with words in the template, both languages, picked by the
language setting. Whimsical, with water in it (author, 2026-09-30). **Chosen: B** (author,
2026-09-30), one line plus a smaller second line:

| | English | Deutsch |
|---|---|---|
| A | This stream has run dry for a moment. / The next town will float by soon. | Dieser Bach ist kurz ausgetrocknet. / Der nächste Ort treibt gleich vorbei. |
| B | Our raindrop got lost in a puddle. / It'll find its way back soon. | Unser Regentropfen steckt in einer Pfütze fest. / Er findet bald wieder heraus. |
| C | Low tide. / Back when the water returns. | Ebbe. / Wir sind zurück, wenn das Wasser wiederkommt. |

## Decisions (2026-09-30)

1. UI words: a `ui` block in every town file.
2. Sink: "Disappears underground" / "Versickert im Boden".
3. Unnamed first stretch: "a stream" / "ein Bach".
4. Error screen: text B, "Our raindrop got lost in a puddle. / It'll find its way back soon." / "Unser Regentropfen steckt in einer Pfütze fest. / Er findet bald wieder heraus." Words in the template (above).
5. No further OpenStreetMap credit beyond the map's own label.
6. Units: separate setting, metric by default, independent of language.

## Found while measuring (data, not copy)

- **Iisalmi (Finland) had 35 steps** ("Lake Saimaa → Raudanjoki → Lake Saimaa → …"). Fixed
  2026-09-30 (PROJECT.md status): now 16, the longest chains in the rotation are 16 steps
  (Löbau, Iisalmi, Siilinjärvi); 95 % of towns have ≤ 6.
- **German town name from GeoNames**: Saint-Quentin-en-Yvelines is "Communauté d’agglomération de
  Saint-Quentin-en-Yvelines" (55 chars) in German, the name of the municipal association, not of
  the town. D17 says town names come straight from GeoNames; slot 1's clamp keeps it on one line.
