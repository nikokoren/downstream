# Downstream: brief and requirements

TRMNL recipe. Status: working brief, ready to start. Last updated September 2026.

> Stored in the repo verbatim on 2026-09-28 from the author's message. Treat this file as the requirements source. Changes to decisions go in `PROJECT.md` (dated); edit this file only when the brief itself changes.

This document replaces the original brief, which is no longer available. Source facts (licenses, data fields, API behavior) were checked against each source's own documentation in September 2026; links are in section 14. Re-fetch every source before relying on it; where the web and this document disagree, the web wins.

## Working method (adopted 2026-09-27, applies to every TRMNL recipe)

1. Never verify against input you invented. Test payloads must be captured from the live API, or come from the fixture corpus built from captured responses. A bug found only in made-up data isn't a bug.
2. Sweep the state space, don't spot-check. Render every combination that matters (states x languages x voices x views x devices) and compare outputs. Report results as numbers (for example "6/6 identical before, 0/6 after"); that number is also the proof of the fix.
3. Re-fetch versioned docs; memory is stale. Use unversioned URLs, stamp what was verified and when, and the web wins on disagreement.
4. "Not there" needs proof, not recall. Search every relevant place and say what was searched: "checked X and Y, zero hits" is a different claim from "I don't think so".
5. Prove fixes, don't assert them. Reproduce the failure, show it gone, and diff outputs before and after (for example "removed 3, added 0, kept 25"). Where only a device can prove it, say "not confirmed on device" instead of "fixed".
6. Run real data through new copy before shipping it. Every new phrase goes through real payloads in every state it can appear in, so contradictions show up before users see them.
7. State corrections in one line, then move on.
8. Write memory down, dated, with a re-check instruction. Agents have no memory across sessions; the repo is the memory. Every stated fact about an outside system carries its version, date, and "re-fetch before relying on this".
9. Assume concurrent agents. In a long session, re-read a file before editing it; don't trust your last-known main.

## 1. What it is

From the user's location, show where a raindrop falling there would end up: the chain of streams and rivers it follows, the total distance, and where it ends (a sea, or an inland lake for closed basins). For Munich the expected answer is Isar, then Danube, then the Black Sea; that is the first acceptance test.

The path only changes if the location changes, so the screen needs a small live element to stay worth looking at (decision D2).

## 2. Licensing position (decided)

The recipe is released for free, but TRMNL's Creator Fund may pay the author. That fund is paid from company revenue (80% of TRMNL+ subscription revenue, plus 10 to 15% of hardware sales), and plugin author payouts are calculated automatically from playlist age, playlist presence and impressions (times displayed on devices), above a threshold of 50 installs plus forks.

Creative Commons NonCommercial licenses define noncommercial as "not primarily intended for or directed towards commercial advantage or monetary compensation". The test is the primary purpose, and CC itself describes it as intent-based with gray areas. Because Creator Fund payouts scale with how often the licensed material is displayed and come from a company's sales, this project treats itself as potentially commercial.

**Rule:** no NC-licensed data (CC BY-NC, CC BY-NC-SA, or similar) unless the data owner grants written permission, stored in the repo. Only public domain, CC0, CC BY, and sources whose own terms explicitly allow commercial use. This is a cautious reading, not legal advice.

Consequence for this project: the Global River Runner API (CC BY-NC-SA) is out unless its maintainers grant permission. The primary source is self-hosted HydroRIVERS, which allows commercial use.

## 3. Decisions still open

- **D1** Coverage for v1: global, or selected regions first. The pipeline is the same either way; the difference is output size and build time. Recommended: global, if the prepared data fits Cloudflare R2's free storage allowance (to verify after a first build).
- **D2** Live element: for example "raining here now" from Open-Meteo, with a rough "rain that falls today reaches the Black Sea in about N days" (clearly labeled as an estimate), or a rotating fact about a river on the path.
- **D3** Travel time: show it at all? Any flow speed assumption is rough.
- **D4** Ask the River Runner maintainers for permission anyway? If granted, its API could serve as a quick fallback for locations the self-hosted data handles badly. Not needed for v1.

## 4. Data sources

### 4.1 HydroRIVERS (primary, river network)

- Global vector river network: about 8.5 million reaches, average length 4.2 km, covering every river with a catchment of at least 10 km² or an average flow of at least 0.1 m³/s.
- Per reach (confirmed field names): `HYRIV_ID`, `NEXT_DOWN` (ID of the next reach downstream), `MAIN_RIV` (the basin's most downstream reach), `LENGTH_KM`, `DIST_DN_KM` (distance to the network's outlet), `ENDORHEIC` (whether it drains to an inland sink), discharge estimate, stream orders, and `HYBAS_L12` (its HydroBASINS level 12 sub-basin).
- License: free for scientific, educational and commercial use under the HydroSHEDS license agreement, which requires a specific attribution statement (section 10).
- Gaps: no river names; lower quality above 60 degrees north (source elevation data).
- Known quirk: a user report shows some reaches flagged as ocean outlets (`NEXT_DOWN` 0, `ENDORHEIC` 0) that actually end inland in Central Asia. Endpoint classification must not rely on those flags alone (R9).

### 4.2 HydroBASINS level 12 (primary, point lookup)

Sub-basin polygons, same license family as HydroRIVERS, sharing the `HYBAS_L12` ID. Used to find which reach a raindrop starts on (R5).

### 4.3 Natural Earth (primary, names and sea areas)

- River and lake centerlines at 1:10 million with names, and marine area polygons for naming the endpoint (for example Black Sea).
- License: public domain, no restrictions on use.
- Names are English-first; German names come from the curated table (R8).
- A denser supplementary river set exists for Europe and North America, derived from European Commission research data; its terms need checking before use. Not needed for v1.

### 4.4 USGS NLDI (optional, US only)

Public, official US river network routing. Could back US locations in a later version. Not needed for v1.

### 4.5 Global River Runner API (excluded unless permission, D4)

Live global flow path API (`merit.internetofwater.app`), verified working in September 2026, but its data is CC BY-NC-SA and it is an explicitly unsupported proof of concept.

## 5. Data preparation pipeline (build time)

The core of the project. Runs as a script (GitHub Actions or locally), not at request time.

- **P1** Download HydroRIVERS and HydroBASINS level 12 for the chosen coverage (D1), and Natural Earth rivers, lakes and marine areas.
- **P2** Reduce HydroRIVERS to a compact routing table: `HYRIV_ID`, `NEXT_DOWN`, `LENGTH_KM`, `DIST_DN_KM`, `ENDORHEIC`, main river ID, and a simplified geometry per reach (enough for a map at country scale).
- **P3** Name join: match Natural Earth river centerlines to HydroRIVERS reaches spatially (for example: reaches within a small distance of a named centerline and roughly parallel to it inherit its name). Only major rivers get names; everything else stays unnamed.
- **P4** Endpoint table: for each outlet reach, find which Natural Earth marine area or lake it ends in; for endorheic basins, the named sink if one exists. Correct the known Central Asia outlet quirk here.
- **P5** Tiling: split the routing table and the sub-basin polygons into geographic tiles (for example 1 degree squares) so a request loads only the tile around the user plus the reaches along one path.
- **P6** Upload tiles to Cloudflare R2, versioned (for example `v1/tiles/...`), so a rebuild never breaks running requests.
- **P7** Build report: counts, output size, and a list of test points with their computed endpoints (section 12), checked by hand before publishing.

## 6. Request-time architecture

- **R1** Cloudflare Worker. The recipe polls the Worker with the user's coordinates (from the native `lat_lon` field).
- **R2** Permanent result cache: the path for a location never changes, so cache the processed result in KV forever, keyed by coordinates rounded to about 100 m plus the data version.
- **R3** Payload under about 6 KB. TRMNL polling handles that (Aurora Watch runs at about 7 KB); webhooks would be capped at 2 KB (5 KB with TRMNL+).

## 7. Content and logic

- **R4** Start point: find the HydroBASINS level 12 sub-basin containing the user's location, then the nearest reach within that sub-basin. Fall back to the nearest reach overall if the sub-basin has none. The on-screen wording says "the nearest stream", since HydroRIVERS leaves out the smallest creeks.
- **R5** Follow `NEXT_DOWN` until 0, collecting reaches.
- **R6** River chain: consecutive reaches grouped by name, each with its length; unnamed stretches at the start become "a stream" (or "streams").
- **R7** Total distance from the start reach's `DIST_DN_KM`.
- **R8** Names in en/de for major rivers, seas and lakes from a curated table in the repo (Danube/Donau, Black Sea/Schwarzes Meer, Rhine/Rhein, North Sea/Nordsee, and so on), falling back to the Natural Earth name.
- **R9** Endpoint types, each with its own screen state: sea, inland lake, inland sink with no named water body, start point already in the sea, no reach found nearby.
- **R10** Honesty rule: anything estimated (travel time, "reaches the sea in N days") is labeled as an estimate, with the assumption documented in PROJECT.md. The source's own caveat that engineered drainage (dams, canals, city sewers) isn't modeled goes into the store listing.

## 8. Views

Same four views as Aurora Watch, all native Framework 3.3.

- **Full:** map of the whole path with a "you are here" dot and an end marker; headline and river chain beside it (landscape) or below it (portrait).
- **Half Vertical:** map on top, headline and a short chain below.
- **Half Horizontal:** headline and chain; map on TRMNL X only (`hidden lg:block`), as in Aurora Watch.
- **Quadrant:** headline and total distance; map on X only.
- **R11** Portrait handled in every view.
- **R12** Map: MapLibre via TRMNLMaps, framed on the path's bounding box; path drawn as our own GeoJSON source and line layer after load. All map rules from Aurora Watch's CLAUDE.md apply (never mutate the preset's style object, `idle` for measuring, literal stretch axes, loading fallbacks).

## 9. Text and languages

- **R13** English and German from day one with the LOCALES pattern; all words from the backend, none in templates.
- **R14** A TEXT_REQUIREMENTS.md (slots, casing, length budgets, which lines share the screen) before writing any copy.
- **R15** Plain language, no hydrology jargon on screen.

## 10. Attribution on screen

- **R16** Every view credits the data. HydroSHEDS requires its attribution statement (short form on screen, for example "River data: HydroSHEDS © WWF", with the full statement in the README and store listing; confirm the short form satisfies the license agreement). Natural Earth needs no credit but gets one ("Made with Natural Earth"). The basemap carries its own OpenStreetMap credit.
- **R17** The README and store listing include the full HydroSHEDS statement and citation (Lehner and Grill 2013).

## 11. Error and empty states

- **R18** Localized error screen in all four views.
- **R19** Location not set: prompt to set it, in both languages.

## 12. Testing and acceptance

- **R20** Acceptance paths, checked by hand against a map: Munich (Isar, Danube, Black Sea), a Rhine city (North Sea), a coastal point, a closed-basin point (for example near the Caspian), a Central Asia point affected by the outlet quirk, a point above 60 degrees north, a US point (compare with NLDI).
- **R21** Pipeline tests on a small region before the full build.
- **R22** Worker tests with recorded tiles, including a missing tile.
- **R23** Storefront fixture: Munich, en and de, with a generator script as in Aurora Watch's `fixtures/`.
- **R24** Device checks: OG 1-bit and 2-bit, BWRY, TRMNL X, both orientations, all four views.

## 13. Out of scope for v1

Upstream watershed display; water quality; animations; NLDI backend for the US; Natural Earth's supplementary rivers.

## 14. Sources

- HydroRIVERS: https://hydrosheds.org/page/hydrorivers
- HydroRIVERS technical documentation: https://data.hydrosheds.org/file/technical-documentation/HydroRIVERS_TechDoc_v10.pdf
- Natural Earth rivers: https://www.naturalearthdata.com/?p=466
- Global River Runner (excluded, for reference): https://ksonda.github.io/global-river-runner/
- TRMNL Creator Fund: https://trmnl.com/blog/creator-fund
- CC NonCommercial interpretation: https://wiki.creativecommons.org/NonCommercial_interpretation
- TRMNL webhook limits: https://docs.trmnl.com/go/private-plugins/webhooks

## 15. Risks

- The data preparation (section 5) is most of the work, especially the name join (P3).
- Output size for global coverage is unknown until a first build (D1).
- Names are missing for smaller rivers; the chain may start with several unnamed stretches.
