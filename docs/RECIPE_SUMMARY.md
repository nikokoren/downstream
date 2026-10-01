# Downstream: what the recipe does

A briefing for writing marketing texts (store listing, announcement, social posts). Facts only;
numbers are from the current build (2026-09-30). The section "Must be in the store listing" is
required by the data licences.

## In one sentence

Downstream is a TRMNL recipe that answers a question almost nobody knows the answer to: if a
raindrop falls on this town, where does it end up? Every 15 minutes it picks another town and
follows the water on a map, stream by stream and river by river, all the way to the sea.

## What you see on the screen

- **A map of the whole journey**, filling the screen: a black line from the town to where the
  water ends, a solid dot where it starts and a hollow dot where it arrives. The map always zooms
  so that the whole path fits, from a few kilometres through a city to nearly 3,000 km across a
  continent.
- **A text box** over the map, bottom left, with:
  1. the town and its country, the largest text ("Munich, Germany");
  2. every stream, river and lake the water passes, in order ("a stream → Isar → Danube");
  3. where it ends ("Ends in the Black Sea");
  4. how far it travels and roughly how long it takes ("2,588 km · about 3–8 weeks").
- The map is drawn for e-ink: clean outlines, water shaded, only the biggest roads and place
  names, so the path stands out.

## Examples (real output)

| Town | The water's path | Ends in | Distance · time |
|---|---|---|---|
| Munich, Germany | a stream → Isar → Danube | the Black Sea | 2,588 km · about 3–8 weeks |
| Vienna, Austria | Donaukanal → Danube | the Black Sea | 2,066 km · about 3–6 weeks |
| Hamburg, Germany | Alster → Norderelbe → Elbe | the North Sea | 12 km · about 4–10 hours |
| Konstanz, Germany | Bodensee (Lake Constance) → Rhine | the North Sea | 1,058 km · about 3–7 years (it waits in Lake Constance) |
| Lisbon, Portugal | a stream → Tagus | the North Atlantic | 7.5 km · about 8–17 hours |
| Cetinje, Montenegro | — | disappears underground (karst) | 3.7 km · about 3–6 hours |
| Minneapolis, USA | Mississippi River → Lake Pepin → Mississippi River | the Gulf of Mexico | 3,002 km · about 3–6 weeks |
| Denver, USA | Cherry Creek → South Platte River → Platte River → Missouri River → Mississippi River | the Gulf of Mexico | 3,938 km · about 1–3 months |
| Salt Lake City, USA | City Creek → Jordan River → Great Salt Lake | the Great Salt Lake (no outlet) | 140 km · about 2–5 days |
| Duluth, USA | Lake Superior → … → Lake Erie → Niagara River → Lake Ontario → St. Lawrence | the Gulf of Saint Lawrence | 2,707 km · about 102–230 years (on average water stays about 130 years in Lake Superior, HydroLAKES) |

Surprises the recipe turns up:
- **The longest trip** starts in Donaueschingen, Germany, where the Danube begins: 2,922 km to
  the Black Sea, about 4–9 weeks.
- **The slowest** are towns above big lakes. A raindrop in Nässjö, Sweden, travels only 274 km
  but needs "about 49–111 years", because it waits in Lake Vättern on the way to the Baltic Sea.
- **Some water never reaches the sea.** In karst country it seeps into the ground; in a few
  closed basins it ends in a lake.
- **Neighbouring towns can send their water to different seas**, when a watershed runs between
  them.

## How it works (for the curious)

- Nothing is live and nothing is tracked. For each town, the path is worked out in advance from
  a global river network. The water flows from the town's nearest stream, downhill through every
  river it joins, until it reaches the sea (or a lake, or the ground).
- **10,223 towns** in Europe and the United States (towns with more than about 15,000 people,
  from GeoNames, plus a handful chosen by hand). A new town every 15 minutes, in a fixed shuffled
  order that jumps around the map: the full tour takes about 11 weeks for Europe, 6 weeks for the
  US, 18 weeks for both. Every Downstream screen with the same region setting shows the same town
  at the same time.
- **About 6,800 differently named rivers, streams and lakes** appear in the paths; 42 different
  endpoints. The median path is 209 km; the longest passes 20 named waters (Hibbing, Minnesota,
  through all five Great Lakes).
- **Travel time is a rough estimate** and always shown as a range starting with "about": water
  runs faster in big rivers than in small streams (speed estimated from each stretch's average
  flow), and lakes hold water for their average residence time. It ignores dams, floods and
  droughts. On screen it is always marked as an estimate.
- Stream names come from OpenStreetMap, so they are the names people actually use locally.
  Unnamed first stretches show as "a stream".

## Settings

- **Region**: Europe, the USA, or both (the default): about 6,900 European and 3,300
  US towns.
- **Language**: English or Deutsch. Everything on screen, including river and sea names where a
  German name exists ("Donau", "Schwarzes Meer", "Endet im Schwarzen Meer").
- **Units**: Metric (km, the default) or Imperial (miles), independent of the language.
- No account, no location, no API key: install and it runs.

## Works everywhere on TRMNL

- All four layouts: full screen, half horizontal, half vertical and quadrant, so it fits in any
  mashup (even twice on one screen).
- TRMNL OG and TRMNL X, landscape and portrait, black-and-white and greyscale screens; larger
  type on the X.
- If the data can't be fetched, a friendly screen appears instead: "Our raindrop got lost in a
  puddle. It'll find its way back soon."

## Tone and angles for the copy

- Curiosity and "huh, I didn't know that": everyone lives downstream of somewhere.
- Geography you can glance at: a small daily lesson in how continents drain.
- Calm, not urgent: it's an ambient, slowly changing picture, not a data feed.
- Honest: the times are playful estimates, not measurements. Don't promise live data, tracking,
  "your location", or exact times.
- Avoid hydrology jargon on screen and in copy (no "catchment", "confluence", "estuary").

## Must be in the store listing (licences)

River network: HydroATLAS (RiverATLAS v1.0), Linke et al. 2019 and Lehner & Grill 2013, CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Lake residence times: HydroLAKES v1.0, Messager
et al. 2016, CC BY 4.0. Both simplified and changed (one path per town, simplified geometry).
Towns: GeoNames, CC BY 4.0. Stream, river and lake names and the map: © OpenStreetMap
contributors, ODbL. Seas: Natural Earth. Source and method: https://github.com/nikokoren/downstream
