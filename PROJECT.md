# PROJECT.md — Downstream

Working memory for the project. Every fact about an outside system carries **what, version, date verified, and "re-fetch before relying on this"**. Newest entries at the top of each section.

## Status

- 2026-10-01 — **US trial (D22), Natural Earth names only** (OSM extracts blocked, entry below). Example towns: Minneapolis "Mississippi" → Gulf of Mexico, 3,002 km, about 3–6 weeks (**acceptance test #2 passes**); Denver "stream → South Platte → Platte → Missouri → Mississippi" → Gulf of Mexico, 3,938 km; Pittsburgh "Monongahela → Ohio → Mississippi", 3,203 km; Salt Lake City "stream → Jordan → Great Salt Lake" (lake without outlet); Seattle 0.7 km → Salish Sea; Anchorage 13.8 km → Cook Inlet. All US towns: 3,361 found, 3,305 in the rotation, 56 left out (start > 5 km: Key West, Biloxi, …), 0 errors; payload max 2.7 KB. Endpoints: Gulf of Mexico 1,143, North Atlantic 921, North Pacific 492, Gulf of Saint Lawrence 300 (was "Saint Lawrence River", Natural Earth's estuary polygon, now skipped like "Inner Seas"), Gulf of Maine 120, Straits of Florida 77, Golfo de California 76 (Natural Earth's Spanish name), Salish Sea 67, Great Salt Lake 47, sinks 34, Salton Sea 13, Pyramid Lake 6, Hudson Bay 5, Bering Sea 2, Cook Inlet 2. Two fixes on the way: Natural Earth's North American lakes file has an invalid shape that broke clipping (now repaired; the 2 invalid lakes in the base file are in Canada and Siberia, outside Europe's window). **Travel time check**: the US National Park Service says water from Lake Itasca reaches the Gulf in about three months (nps.gov/miss/riverfacts.htm, checked 2026-10-01). Our model from Itasca: 40 river days (our speed formula is about twice too fast for the dammed upper Mississippi) plus 1,434 lake days from HydroLAKES residence times (Cass Lake 579, Winnibigoshish 385, ...), "about 3–6 years". Open for the author: keep lake residence time as is (it is what makes Konstanz "3–7 years"), cap it, or count only part of it; and whether to recalibrate the river speed.
- 2026-10-01 — **Pipeline builds per region** (D22, commit 3393b83): `downstream/regions.py`, `DOWNSTREAM_REGION` (default `eu`), outputs under `data/<kind>/<region>/`, site folders `eu/`, `us/`, `mix/`. Proof: with the same inputs, 6,918/6,918 Europe town files byte-identical to the build before the change. US inputs fetched (1,310,541 reaches = RiverATLAS `na` + `ar`; BasinATLAS level 12: 163,620; HydroLAKES points: 977,692; Natural Earth North America supplements). **Geofabrik downloads fail from GitHub's runners since today** (osm-waterways runs 9–11, 2026-10-01 07:34–07:58 UTC): every extract URL, Europe too (`europe/liechtenstein`, which worked on 2026-09-29), answers `301` to the same URL with a trailing slash, which answers `301` to itself (curl: "Maximum (50) redirects followed"); Geofabrik's front page shows no notice. Nothing was uploaded, and the nightly build uses the extracts already in this repo's releases. Fallback if it persists: OpenStreetMap France's extracts (ODbL; `download.openstreetmap.fr/extracts/north-america/`: `us-midwest`, `us-northeast`, `us-south`, `us-west` as whole files, only some states separately, Canadian provinces and Mexican states). Re-check before relying on this.
- 2026-10-01 — **D22: United States as a second region** (author's answers to the plan). Checked the same day: TRMNL's form builder has a multi-select (`field_type: select`, `multiple: true`, help article "Custom plugin form builder", updated 2026-09-28), but neither that article nor "Dynamic polling URLs" (updated 2026-03-08) says whether its value reaches Liquid as a list or as comma-separated text; the Polling URL will `join` it so both work (**not confirmed on TRMNL**). RiverATLAS v1.0 region files (listed remotely 2026-10-01): `na` (986,463 reaches, lon −137.9…−52.7, lat 5.5…62.7: contiguous US, southern Canada, Mexico, Central America, Alaska's panhandle), `ar` (324,078, lon −180…−61.1, lat 51.2…83.2: Alaska and northern Canada); none of the 11 files (af, ar, as, au, eu, gr, na, sa_north, sa_south, si) has a reach in the Hawaii box (lon −160.5…−154.5, lat 18.5…22.5), so Hawaii is out. Region files follow whole basins, so no river crosses between them. US water often ends abroad (Great Lakes → St. Lawrence, Red River of the North → Hudson Bay, Colorado → Gulf of California), so the network and OSM names must include Canada and Mexico along those paths. Plan: (1) make the pipeline region-aware with Europe's output byte-identical, (2) North American data and a five-town trial (Minneapolis, Denver, Salt Lake City, Pittsburgh, Seattle; Minneapolis → Mississippi → Gulf of Mexico is acceptance test #2), (3) all US towns, `us/` and mixed rotation folders, the Region setting, phrases and German names, checks.
- 2026-10-01 — **Builds 18 and 19 failed** (author saw the GitHub mails): `test_example_paths` pinned "Río Guadaíra" for El Viso del Alcor, but GitHub rebuilds the name table from a fresh OSM download, where "Río Guadaira" covers more km. The examples now compare names case- and accent-insensitively, like the pipeline does; the site stayed on build 17 (2026-09-30) until the fix.
- 2026-10-01 — **The box reads as one sentence** (author, from an OG screenshot of Bagnolet): "A raindrop falling on / Bagnolet, France / travels along Seine → / ends in the English Channel / 354 km · about 4–9 days"; German "Ein Regentropfen in / … / fließt durch einen Bach → Isar → Donau → / endet im Schwarzen Meer". New `ui.intro`, `ui.along`; endpoint lines start in lower case; German unnamed stream "einen Bach". Quadrant unchanged. Quick check 64/64.
- 2026-09-30 — **One river under several OSM names** folded into one step: names are compared without accents ("Río Guadaira" = "Río Guadaíra"), English "X or Y" names and a leading/trailing "River" count as the same river, and a side arm between two such steps folds in; a step shows a plain spelling over an "X or Y" one. 50 chains changed (45 GB, 5 ES), 0 endpoints; towns with ≥ 6 steps 439 → 419. Cambridge "River Cam → River Great Ouse or Ely Ouse → Great Ouse or Ten Mile River → Great Ouse Relief Channel → River Great Ouse" → "River Cam → River Great Ouse"; Milton Keynes 7 → 2 steps. Cambridge and El Viso del Alcor locked in the tests (36/36 pass). **Render checks** (author): a quick check after each change (`npm run check`: 4 views × OG 1-bit and X landscape × Munich, Iisalmi, Saint-Quentin-en-Yvelines, Cambridge × en/de, 64/64 pass, 4½ min, was 12 min before dropping a redundant wait), the full sweep (`npm run check:full`, 448 cases) only before shipping a version. The path line starts and ends with an arrow (author).
- 2026-09-30 — **Device feedback round 1 (author, OG screenshot of Vihti)**: (1) The path showed "Liquid syntax error (ds_chain line 9)": Ruby Liquid, which TRMNL runs, ends `{{ }}` at the first `}`, and the "+{n} more" placeholder had one inside. Reproduced with Ruby Liquid 5.14.0 (same message), fixed by moving it into an `{% assign %}`; the render check now renders with Ruby Liquid (`recipe/tools/render.rb`) instead of liquidjs, which had accepted it. (2) The town line now names the country ("Vihti, Finland" / "Vihti, Finnland"): town files carry `town.cc` (GeoNames) and `place` en/de from `locales.COUNTRIES` (48 countries; German names are the titles of their German Wikipedia articles, checked 2026-09-30, 48/48, no redirects; English not checked, rate-limited). Lines over 32 characters get one type size smaller; over 45 (15 towns in German, 1 in English) the clamp may shorten them. (3) Units setting options renamed "Metric" / "Imperial". Marketing brief: `docs/RECIPE_SUMMARY.md`.
- 2026-09-30 — **The four views, in Liquid on Framework 3.4** (`recipe/src/`, TRMNL's plugin export layout: `settings.yml`, Shared tab, one file per view). Full-bleed `outline` map, fitted to the whole path at integer zoom beside or above the text box (D19, D21); box bottom left with town, path, "Ends in …", distance · travel time (D20); quadrant: "town → endpoint" and distance · time. Settings: About This Plugin (data credits), Language, Units. "Ends in …" is now one curated phrase per endpoint (`locales.END_PHRASES`, TEXT_REQUIREMENTS). Checked with `recipe/tools/render-check.mjs` (real Framework 3.4.0 CSS/JS, MapLibre 5.24.0, TRMNL tiles, real town files; liquidjs, not TRMNL's Ruby Liquid); **Not confirmed on TRMNL or a device.** Found while checking: (1) the Framework's clamp takes a flex item's own width as the space it has, so a text line in a left-aligned flex column (`flex--left`) could clamp to its pre-font width ("Muni…"); each line is now `w--full`. (2) Maps on the X only drew partly until `TRMNLMaps.refresh()`, which the Framework's JSDoc says the screenshot service calls after setting the capture pixel ratio; the check now calls it too. (3) Chromium's tile fetches through this sandbox's proxy failed (ERR_TOO_MANY_RETRIES), leaving maps half drawn; the check now serves tiles from a Node-side cache, and it samples screenshot pixels along the path, since the old check (path layers exist) passed maps with nothing painted. On the X the Framework scales the screen (a map 1,000 CSS px wide is 1,800 px on the page), which the position checks now account for. (4) The text box covered the map's OpenStreetMap credit in the quadrant and, on the X, in half vertical and full portrait: boxes now sit `bottom--3`, `lg:bottom--6`, and the check fails any overlap. (5) Half horizontal clamped the shortened path of 16-step chains (Löbau, Iisalmi) at one line: now two lines. **Render sweep: 256/256 cases pass** (4 views × OG 1-bit, OG 2-bit, X landscape, X portrait × Munich, Löbau, Cetinje, Limhamn, Konstanz, Iisalmi, Lisbon, error screen × en/imperial, de/metric; before these fixes: 244/256 with credits unchecked, 12 fails all half-horizontal path clamps).
- 2026-09-30 — **Lake time in the travel estimate**: HydroLAKES v1.0 (CC BY 4.0, direct download, no registration) residence times added for lakes and reservoirs on each path (Estimate assumptions). New fetch step `lakes`; credits now "HydroATLAS · HydroLAKES · GeoNames" (settings about text, D20).
- 2026-09-30 — **Travel time estimate** (D3): every town file has `travel_days` and `travel` ("about 3–6 weeks" / "etwa 3–6 Wochen"), shown after the distance. Method and limits under "Estimate assumptions". `dis_m3_pyr` added to the fetched RiverATLAS columns.
- 2026-09-30 — **D20 (author's comment on the wireframes)**: new text order, and data credits move from the screen to the settings' about text. "Ends in <endpoint>" as one phrase needs a per-endpoint wording in both languages ("the Black Sea", "im Schwarzen Meer", "in der Ostsee"); decided later the same day as a curated phrase per endpoint (entry above).
- 2026-09-30 — **Text decisions and Finland lakes.** `docs/TEXT_REQUIREMENTS.md` decided (UI words in every town file, sink "Disappears underground" / "Versickert im Boden", "a stream" / "ein Bach", whimsical error screen with words in the template, no second OSM credit, units a separate setting defaulting to metric). Town files now carry `ui` (en/de, `pipeline/downstream/locales.py`) and `distance` pre-formatted per language and unit. Finland: Natural Earth's generalised "Lake Saimaa" overwrote OSM rivers and the gaps between OSM basins; NE lakes now only name reaches with no OSM name and no named OSM lake within 600 m (43 chains changed, "Lake Saimaa" 77 → 1, also removed a wrong "Lago di Como" from Verbania's path). Then a river through a string of lakes shows only where it starts and ends, each lake once (54 chains changed). Longest chain 35 → 16 steps; towns with ≥ 12 steps 22 → 15; 0 endpoints changed; payload max 4.1 → 2.4 KB (2.8 KB with `ui`); 30/30 tests pass.
- 2026-09-30 — **Design rules from On the Move** copied into `docs/DESIGN_PHILOSOPHY.md` (on_the_move commit 03f8c7f, fetched raw; part A verbatim) with a Downstream proposal (part B, not approved). On the Move's own "For Downstream" notes assume live stream readings; Downstream has none, so part B maps the "animal" to the raindrop's path instead.
- 2026-09-29 — **D18 confirmed on TRMNL** (author's private plugin, Polling strategy, Force Refresh ~21:15–21:30 UTC): TRMNL's Liquid rendered the Polling URL to slot 2485, the slot for that window, and "Your Variables" held the whole file (town Limhamn, chain, end with `display` en/de, `polyline`, `slot`, `start`, `reaches`, `total_km`). So `"now" | date: "%s" | divided_by | modulo` works in TRMNL's Liquid. Next: views.
- 2026-09-29 — **Town files live on GitHub Pages** (build run 12 on `main`, deploy re-run after the author allowed `main` in the github-pages environment). Checked from here: the Polling URL rendered to `eu/t/2485.json` (200, application/json, 432 B, Limhamn), `eu/t/7199.json` 200, `eu/t/7200.json` 404 as expected, `NOTICE.md` 200. Default branch is now `main`; `claude/wizardly-goldberg-dut9iy` is kept in step. Confirmed on TRMNL the same evening (entry above).
- 2026-09-29 — **D18 wired up (option (a))**: `pipeline/downstream/site.py` writes one file per rotation slot (`data/site/eu/t/<n>.json`, 6,918 towns in a fixed shuffled order, seed 20260929) and `recipe/polling_url.liquid`: `slot = unix time // 900`, `n = slot mod 7200` (fixed slot count, see correction below), URL `https://nikokoren.github.io/downstream/eu/t/<n>.json` (region folder added the same day, before any install, so more regions can sit beside Europe). The build workflow deploys `data/site` to GitHub Pages (needs the one-time Pages source setting "GitHub Actions"). The path is now a Google encoded polyline: payload median 1.9 → 1.1 KB, max 4.9 → 4.1 KB. Checked: the polyline encoder reproduces Google's worked example; the URL template renders to the current slot with python-liquid 2.3.3 (Shopify Liquid; TRMNL's engine is Ruby Liquid, so **not confirmed on TRMNL**). Every install shows the same town at the same time; a per-install offset is possible only if TRMNL exposes a per-install value to the Polling URL (not checked). GitHub Pages terms (checked 2026-09-29): not for running an online business or commercial SaaS; 1 GB site, 100 GB/month soft bandwidth. The recipe is free; if Creator Fund payouts ever make that doubtful, move the files to Cloudflare (R2 or Workers static assets).
- 2026-09-29 — **TRMNL docs re-checked** (help centre, docs.trmnl.com, Framework releases and Map docs): webhooks now 5 KB; no documented polling limit; Framework 3.4 with built-in maps (TRMNLMaps: route, fit, dot, decodePolyline, free TRMNL tiles); on-demand refresh; saved state and Serverless scripts. Excerpts in `docs/sources/TRMNL_2026-09-29.md`.
- 2026-09-29 — **German endpoint names** (D7) for all 24 seas towns end in, plus Lake Vegoritida (Vegoritida-See): taken from the German Wikipedia article linked from the English one, each title checked on de.wikipedia. Lake Paralimni (Boeotia, 2 towns) has no German article and stays uncurated ("Paralimni-See" on de.wikipedia is a lake on Cyprus). English "Golfe du Lion" (Natural Earth) shows as "Gulf of Lion". A test now fails if any sea endpoint lacks a German name.
- 2026-09-29 — **Estuaries**: towns on a big river's estuary shore now end with that river (Lisbon: "(stream) → Tagus"). 84 chains changed, 0 endpoints; 24/24 tests pass (Lisbon locked).
- 2026-09-29 — D15–D17 decided: Greek and Cyrillic names in English, prefixes kept, town names from GeoNames. 24/24 tests pass.
- 2026-09-29 — **Same river under two names, and ditches beside big rivers** (details under "OSM for all of Europe"). 144 chains changed, 0 endpoints; 23/23 tests pass (Bolzano and Tolmin locked).
- 2026-09-29 — **15 extra towns added by the author** (`pipeline/downstream/extra_towns.csv`, by GeoNames id from the per-country dumps, CC BY 4.0): Köflach, Unterjesingen, Ballmertshofen, Bad Endorf, Stoob, Wolkenstein in Gröden, Le Bourg-d'Oisans, Bormio, Sölden, Zambratija, Tolmin, Kobarid, Sutrio, Gröbming, Königssee (the village at the lake, 2885778, not Königsee in Thuringia). Braunschweig, Tübingen, Ludwigsburg, Linz, Lübeck, Lindau and Konstanz were already in cities15000. 7,048 towns, 6,918 in the rotation; all 22 requested towns are in it (start ≤ 2.5 km).
- 2026-09-29 — **OSM names for all of Europe** (122 Geofabrik regions, release `osm-waterways-<slug>` each): 323,717 of 938,544 reaches named; first step "a stream" 61 % → 23 % of towns; OSM names cover a median 100 % of path km. 21/21 tests pass. Details under "OSM for all of Europe" below.
- 2026-09-28 — **First end-to-end pipeline run on 6 example towns (Munich, Garmisch-Partenkirchen, Starnberg, Nuremberg, Cologne, Vienna): 6/6 reach the right sea, acceptance test #1 passes (Munich → Isar → Danube → Black Sea).** OSM names for Bavaria come from the `osm-waterways` GitHub workflow (release `osm-waterways-europe-germany-bayern`). Results and open questions under "Pipeline test results" below. TRMNL design postponed by the author until the pipeline is set up.
- 2026-09-28 — D10 decided (OSM names). D11 decided: pipeline tooling (Python 3.12 + uv, geopandas/pyogrio/shapely, pyosmium); `pipeline/` project set up and locked.
- 2026-09-28 — OSM names checked (license and a sample); D10 proposed: name streams from OpenStreetMap (ODbL).
- 2026-09-28 — D9 decided: GeoNames cities15000, language-tagged names, geographic Europe without Russia.
- 2026-09-28 — D7 decided. D1 decided: Europe first. Town sources checked; D9 proposed: GeoNames cities5000 (CC BY 4.0).
- 2026-09-28 — D8 decided: the recipe rotates through a fixed list of towns; the user's location is dropped.
- 2026-09-28 — D5 decided (HydroATLAS), D6 decided (Europe supplement in v1), D7 proposed (German names from the curated table only).
- 2026-09-28 — Step 1 done: all 7 sources in BRIEF §14 re-fetched, plus the HydroSHEDS license (TechDoc v1.4), HydroBASINS TechDoc v1.c and Natural Earth's terms and physical downloads page. Facts are recorded below. Two findings block v1 as the brief describes it: **D5** (license terms) and **D6** (Isar isn't in the base Natural Earth river set).
- 2026-09-28 — Repo scaffolded: brief stored (`docs/BRIEF.md`), agent rules (`CLAUDE.md`), empty `pipeline/`, `worker/`, `recipe/`, `fixtures/`.

## Next steps (in order)

1. Fill in `docs/TEXT_REQUIREMENTS.md` (in progress). Still missing: Aurora Watch's map rules, LOCALES pattern and `fixtures/` generator (needs that repo; On the Move may cover the same ground).
2. Views: built (2026-09-30). Next: the author installs the plugin on TRMNL and checks it on a device (OG and X, both orientations, a mashup).

## Deferred (come back after everything else is built)

- 2026-09-29 — **Other continents / a region choice** (author asked what it would take; not planned yet). The rotation already fits: a recipe dropdown (Europe, North America, everything) read by the Polling URL, one folder and town count per region, "everything" as its own shuffled list. The pipeline would need per-region settings where it now assumes Europe: the metric CRS (EPSG:3035 everywhere), the sea grid window (lon −30..55, lat 28..74), the RiverATLAS/BasinATLAS region files (`eu`; North America is `na` plus `ar`), the border filter (D9), and the OSM region list. Also to decide then: the Gulf of Mexico / "Gulf of America" name, miles for US users, and more inland sinks (Great Basin).

- 2026-09-28 — **Rivers through lakes the HydroATLAS path misses** (author: later). Example: Garmisch-Partenkirchen should show Kochelsee (OSM Loisach runs 3.9 km inside it; HydroATLAS passes 2.92 km away). Idea: for each named river on the path, check whether its OSM line crosses a named lake along the matched stretch and insert the lake step there. Fits into `naming.mark_lakes` without touching other stages. Details under D13.

## Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| L | No NC-licensed data without written permission (BRIEF §2) | Decided | 2026-09 (brief) |
| D1 | Coverage for v1: Europe first (towns, per D8) | Decided | 2026-09-28 |
| D2 | Live element (e.g. Open-Meteo "raining here now") | Likely moot: the rotation provides the change (D8) | 2026-09-28 |
| D3 | Show travel time: yes, as a rounded estimate after the distance ("about 3–6 weeks"), flowing water only | Decided | 2026-09-30 |
| D4 | Ask Global River Runner maintainers for permission | Open, not needed for v1 | — |
| D5 | River data from HydroATLAS (CC BY 4.0), not the HydroRIVERS/HydroBASINS downloads (see below) | Decided | 2026-09-28 |
| D6 | Natural Earth Europe supplement is in v1 (see below) | Decided | 2026-09-28 |
| D7 | German names of rivers, lakes, seas: curated table only, `name_de` not used (see below) | Decided | 2026-09-28 |
| D8 | Rotate through a fixed list of towns; drop the user's location (see below) | Decided | 2026-09-28 |
| D9 | Towns: GeoNames cities15000, language-tagged names, geographic Europe without Russia (see below) | Decided | 2026-09-28 |
| D10 | Name streams and rivers from OpenStreetMap (ODbL), publish the name table (see below) | Decided | 2026-09-28 |
| D11 | Pipeline tooling: Python 3.12 + uv, geopandas/pyogrio/shapely, pyosmium (see below) | Decided | 2026-09-28 |
| D12 | Delta arms fold into the main river (Lek → Rhine, Chilia arm → Danube) | Decided | 2026-09-28 |
| D13 | Lakes on the path are steps of their own (natural lakes only, not reservoirs) | Decided | 2026-09-28 |
| D14 | Leave out towns whose start is > 5 km from the town; don't show "Inner Seas" | Decided | 2026-09-29 |
| D15 | Greek and Cyrillic names shown in English: Latin part, else OSM `name:en`, else standard romanization | Decided | 2026-09-29 |
| D16 | Keep prefixes in local names ("La Seine" style, "River Irwell") for now | Decided | 2026-09-29 |
| D17 | Town names straight from GeoNames (as D9 picks them; e.g. "Sëlva", "Solden" in English) | Decided | 2026-09-29 |
| D22 | United States as a second region: contiguous 48 + Alaska; Hawaii left out (no HydroATLAS coverage). New "Region" setting, multi-select (Europe, United States); none ticked = a mix of both. Units default stays metric; "Gulf of Mexico"; German names and phrases for every new endpoint | Decided | 2026-10-01 |
| D21 | Every view is a full-bleed map with the text box overlaid (half views and quadrant too) | Decided | 2026-09-30 |
| D20 | Text order: town (largest), path, "Ends in <endpoint>" (slightly smaller than the town), distance. HydroATLAS and GeoNames credits go to the settings' "about this plugin" text, not on screen (overrides R16's on-screen credit); the map keeps its own OpenStreetMap label | Decided | 2026-09-30 |
| D19 | View design: On the Move's rules as mapped in `docs/DESIGN_PHILOSOPHY.md` part B; every view frames the whole path (integer zoom), no edge pill | Decided | 2026-09-30 |
| D18 | Rotation without a server: the Polling URL picks the town from the clock; static town files on GitHub Pages; Framework 3.4; path as encoded polyline | Decided | 2026-09-29 |

### D5 — River data source: HydroATLAS, CC BY 4.0 (decided 2026-09-28)

**Decision (author, 2026-09-28): use HydroATLAS v1.0 (RiverATLAS for reaches, BasinATLAS for level-12 sub-basins) instead of the HydroRIVERS/HydroBASINS downloads.**

Why: the HydroRIVERS/HydroBASINS downloads fall under the HydroSHEDS v1 License Agreement (excerpts in `docs/sources/HYDROSHEDS_LICENSE.md`). It's a distribution contract that needs a written end-user license (§2.1.2, §1.2) and two years of records of "the identity and address of each End User" (§10.7). A TRMNL recipe can't do either, and the author won't collect or hand over identity or address data. HydroATLAS has the same reaches, routing columns and sub-basins, published under CC BY 4.0 (facts below), which BRIEF §2 allows without permission.

Consequences:
- **Never download the HydroRIVERS or HydroBASINS zips.** Pipeline input is RiverATLAS + BasinATLAS from figshare only. The HydroRIVERS/HydroBASINS TechDocs stay useful as column documentation; the columns are identical (HydroATLAS TechDoc Appendices 1 and 2).
- Attribution follows CC BY 4.0: credit the creators, give the license name and link, say the data was modified. Citations: Linke et al. 2019 (HydroATLAS) and Lehner & Grill 2013 (source data). The Exhibit B statement no longer applies.
- Remaining ambiguity, accepted by the author: TechDoc §4.1 says the collection "as a whole" is CC BY 4.0 and "all attribute columns" are CC BY 4.0 or ODbL. It also says "individual parts … are still governed by their own licenses", without saying which license covers the geometry. figshare lists the whole dataset, data zips included, as CC BY 4.0. Not legal advice. An optional confirmation email to the listed contact needs no personal data; a reply would go in `docs/permissions/`.
- Build cost: RiverATLAS shapefile 2.4 GB and BasinATLAS shapefile 4.3 GB, both global only. P2 drops the ~280 environmental attribute columns we don't need.
- Fallbacks if HydroATLAS ever becomes unusable (none verified): OpenStreetMap waterways (ODbL), USGS NHD/NLDI (US only), EU-Hydro (Europe only).

### D6 — Natural Earth Europe supplement: in v1 (decided 2026-09-28)

`ne_10m_rivers_lake_centerlines` v5.0.0 has Danube and Rhine but **no Isar** (searched all 1,473 features by `name`, zero hits). Isar is only in `ne_10m_rivers_europe` v5.0.0. **Decision (author, 2026-09-28): the Europe supplement is in v1.** This overrides BRIEF §13 for this item. Why the brief had it out of scope: §4.3 said its terms "need checking before use" (it's derived from European Commission research data, and the original CCM data is non-commercial). They're now checked: Natural Earth releases the supplement as public domain (facts below). The North America and Australia supplements stay out until their terms are checked.

### D7 — German names: curated table only (decided 2026-09-28)

Natural Earth's `name_de` isn't reliable German. It appears to come from Wikidata, with another label used when Wikidata has no German one (inferred from the example below; NE's docs weren't checked on this). Example: Rungwa (Q35311383) has no German label on Wikidata, only English "Rungwa River", and NE's `name_de` is "Rungwa River". A partial comparison with live Wikidata (632 of 2,678 named features, in Wikidata ID order, so not a random sample; stopped early by the author as enough evidence):
- 385 match today's German Wikidata label or German Wikipedia title;
- 26 have no German label on Wikidata at all, so the value is English or local ("Lake Kariba", "Pardo River", "Quan River");
- 221 differ from today's German label (e.g. "Vaupés" vs "Río Vaupés").

Proposal: German names on screen come **only** from the curated table (R8). Everything else shows NE's `name` (the local or English form), never `name_de`. Wikidata isn't queried at build or request time. The table only needs the rivers, seas and lakes that realistically appear on paths; the pipeline's build report (P7) should list the named features that do appear, so the table can be checked against them.

### D8 — Rotate through a fixed list of towns (decided 2026-09-28)

**Decision (author, 2026-09-28): the recipe cycles through a fixed list of towns and shows each one's path on a full-screen map, with a text list: the starting town, then every stream and river in order, then the endpoint. The user's own location is dropped.** Reason: a user's watershed never changes, so it isn't interesting to look at twice.

Effect on the brief (BRIEF.md stays verbatim; this overrides it):
- **Gone:** R1's `lat_lon` input; R2 (per-location cache); P5 tiling and the request-time lookup; R19 ("location not set"). The R9 states "start point already in the sea" and "no reach found nearby" become build-time checks: such towns get dropped from the list and don't need screen states.
- **Moved to build time:** R4 to R7 (snap town to nearest reach, follow `NEXT_DOWN`, group names, distance) run once per town in the pipeline. Output: one small result per town (name, path geometry simplified for the map, river chain, distance, endpoint). The Worker (or a static file) serves the next town in the rotation.
- **Unchanged:** R3 (payload), R6, R8 to R18, R20 (as the test list, each checked town can also be in the rotation), R21 to R24.
- **D1** becomes "which towns": US, Europe or world. Size stops being a concern, since the output is a few KB per town.
- **D2** is likely moot: the rotation provides the change.
- BasinATLAS is still useful at build time to snap a town into the right sub-basin (R4), but it never ships.

Open inside D8:
- Town source and selection rule (population threshold, spread across basins so the rotation doesn't show ten Danube towns in a row).
- Rotation order and cadence (per refresh, per hour, per day), depending on how TRMNL refreshes a recipe (not verified).
- **Names for small streams.** Natural Earth names only major rivers (about 1,400 base plus 549 in the Europe supplement), so small tributaries will show as "a stream". Naming nearly every stream needs OpenStreetMap waterways (ODbL; share-alike terms for the name table need checking) or, for the US, USGS NHDPlus (public domain). Not verified.

### D9 — Towns: GeoNames cities15000, Europe without Russia (decided 2026-09-28)

**Decision (author, 2026-09-28):**
- **Source:** GeoNames `cities15000` (population > 15,000 or capitals), CC BY 4.0. Natural Earth populated places isn't used (too few towns; its `NAME_DE` has the D7 problem).
- **Names:** per language from GeoNames `alternateNamesV2` (isolanguage `de` / `en`; preferred name first, skipping colloquial and historic names), falling back to the town's `name`. Don't use `name` alone, since it mixes English and local forms ("Munich", "Köln"). Names are baked into each town's result at build time.
- **Area:** geographic Europe, drawn as a polygon, not selected by country code. **Russia is excluded entirely**, including Kaliningrad.

Count for orientation (2026-09-28): cities15000 has 7,059 towns in GeoNames' `EU` continent countries without Russia (Russia would add 1,108). The polygon will shift this number a little.

Boundary defaults, set by the agent and easy to change: include Iceland, the British Isles, Mediterranean islands, and European Turkey (Thrace, incl. Istanbul: GeoNames lists TR under Asia, 432 towns in all of TR). Exclude the Canary Islands, Azores, Madeira, Svalbard, Cyprus, and the Caucasus countries (GE, AM, AZ) and Kazakhstan. The polygon file goes in the repo (e.g. `pipeline/europe.geojson`) with this list in its header.

**Implemented 2026-09-28** (`pipeline/downstream/europe.py`, rules in its docstring): country allowed (Natural Earth admin-0 v5 `CONTINENT == "Europe"`, 51 countries, minus Russia, plus Turkey) **and** point inside the outline buffered 5 km. Outline = those countries minus the Canaries/Madeira, Azores, Svalbard/Jan Mayen, Ceuta/Melilla and anything outside 25 W–45 E / 34–72 N; Turkey only west of a line through the Bosporus, Sea of Marmara and Dardanelles; plus Crimea. Result: **7,033** of 34,146 cities15000 towns; 0 in Russia; 39 in European Turkey. Checked in `tests/test_europe.py` against 18 towns that must be in and 13 that must be out.

Two corrections from the sweep: (1) Çanakkale (Asian shore of the Dardanelles, where the strait is ~1.3 km wide) first counted as Europe; the line now runs between Kilitbahir and Çanakkale. (2) Natural Earth draws Crimea inside Russia's polygon, so 16 Crimean towns (Sevastopol, Simferopol, Yalta, …) were dropped. **Agent's call, flagged to the author:** Crimea follows GeoNames' country code (UA), which matches UN recognition; Russian towns stay out either way because the country check comes first.

Still open (D8): how to pick the rotation from ~7,000 towns so it spreads across river basins.

### D10 — Stream and river names from OpenStreetMap (decided 2026-09-28)

Natural Earth names only major rivers, so most paths would start with "a stream". OpenStreetMap names nearly every stream. Checked 2026-09-28 (facts below): the license allows it, with conditions we can meet.

How ODbL applies here (sources: ODbL 1.0 text; OSMF Community Guidelines, all board-endorsed; not legal advice):
- The **name table** (HydroATLAS reach ID → OSM name, name:de, name:en) is a substantial extraction of OSM, so it's a **Derivative Database** (ODbL §4.4b). Because the screen shows it, it counts as publicly used (§4.4c). So: license the name table under ODbL, and offer it free in machine-readable form, or the method that made it (§4.6). **Plan: publish the name table as a file under ODbL** (e.g. in the repo or a public R2 path) with the ODbL notice next to it (§4.2).
- **HydroATLAS geometry stays out of share-alike.** Per the Collective Database Guideline (endorsed 2016-06-17), adding a property (the name) to our own primary features, with that property all from OSM or all non-OSM within a regional cut, keeps the datasets "independent". Even if it didn't, HydroATLAS (CC BY 4.0), GeoNames (CC BY 4.0) and Natural Earth (public domain) can all be released under ODbL, so the worst case is publishing more files, not a license conflict.
- Mixing: if our curated table (D7) or Natural Earth names override OSM names for the same property, the table counts as a mixed source. That's fine; they just become part of the published ODbL name table. Nothing in them is restricted.
- **On screen:** the display is a Produced Work (§4.5b; Produced Work Guideline: images are "usually" Produced Works). It needs a notice that makes viewers aware the content comes from OSM under ODbL (§4.3). Attribution Guideline (adopted 2021-06-25): the text must say "OpenStreetMap"; "© OpenStreetMap contributors" is acceptable; place it next to the map or where credits are expected; there must be a way to find the license. Where a link isn't possible, print the URL `openstreetmap.org/copyright` (the rule for printed and non-linkable media). The OSM basemap credit (R16) may already cover this if it's worded to cover the names too. Settle the wording in TEXT_REQUIREMENTS.
- Not a problem: we don't restrict the table (§4.7), and we don't sublicense.

Data quality, one sample only (Munich area, see facts): rivers 225/279 ways named, streams 1,891/3,533, and every tributary on the Starnberg → Würm → Amper → Isar path is named. The unnamed ways are mostly tiny ditches that HydroATLAS doesn't have anyway (it starts at 10 km² catchment). `name:de` coverage outside German-speaking countries isn't checked.

Costs and risks:
- The name join (P3) gets harder: matching thousands of small OSM streams onto 500 m-resolution HydroATLAS reaches, instead of ~2,000 Natural Earth rivers. OSM `type=waterway` relations group a river's ways under one name and may help; not checked.
- Download: Geofabrik's Europe extract is the usual source, but download.geofabrik.de was unreachable from this container on 2026-09-28 (4/4 attempts: connection reset by the proxy). Its size isn't verified. Needs the host allowed in this environment's network settings, or the pipeline running elsewhere (GitHub Actions).
- If D10 is accepted, the Natural Earth Europe supplement (D6) matters less for names, but Natural Earth stays the source for seas and lakes (endpoints).

### D11 — Pipeline tooling (decided 2026-09-28; author asked the agent to choose)

- **Python 3.12**, dependencies managed with **uv** (`pipeline/pyproject.toml` + `uv.lock`). 3.12 because pyproj 3.8 requires ≥ 3.12.
- **pyogrio (GDAL) + geopandas + shapely 2** for reading shapefiles, spatial joins (town → sub-basin → nearest reach; OSM line → reach), and simplifying path geometry. GDAL's `/vsizip/{/vsicurl/URL}` reads single members out of the remote figshare zips, so the pipeline never downloads the full 2.4 GB / 4.3 GB archives.
- **pyosmium** for OSM: streams a PBF and keeps only `waterway=*` ways, so memory and disk stay small. No `osmium-tool` or apt packages needed.
- Routing (`NEXT_DOWN` chains) is plain Python dicts: 938,544 reaches in the `eu` region fit in memory easily.
- **pytest** and **ruff** as dev tools. Test fixtures are clips of real downloaded data (working method #1), never hand-written geometry.
- Intermediate files: GeoParquet in `data/` (git-ignored). Outputs: one JSON per town, the published ODbL name table, the build report.
- Not chosen: DuckDB spatial (another engine for no clear gain at this size; revisit if memory gets tight), PostGIS (needs a server), TypeScript/turf for the pipeline (weak for GB-scale geodata; the Worker stays TypeScript).
- **Where it runs:** this container for development; GitHub Actions `ubuntu-latest` for real builds (repo is public: 4 CPU, 16 GB RAM, 14 GB SSD, free, 6 h per job). Disk is the tight one, so the OSM stage processes one country extract at a time and deletes it.
- Verified in this container 2026-09-28: `uv sync` with the locked versions below, imports OK; GDAL read `RiverATLAS_v10_eu.shp` remotely in 11 s. **Not verified:** pyosmium on a real PBF (Geofabrik unreachable here, D10); a full run on a GitHub runner.

Locked versions (2026-09-28): Python 3.12.3, geopandas 1.2.0 (released that day), shapely 2.1.2, pyogrio 0.13.0 with GDAL 3.12.4, pyproj 3.8.0, osmium 4.3.1, pytest 9.1.1, ruff 0.16.9, uv 0.8.17.

### D12 — Delta arms fold into the main river (decided 2026-09-28)

Author's decision. Implementation (`naming.fold_delta`): in the last river of the path (the `ORD_CLAS` run that reaches the outlet), every name after the first becomes the first. Cologne before: Rhine ×41 reaches, Nederrijn ×11, Lek ×23; after: Rhine ×75. Side effect to watch: a river that genuinely changes name on its last stretch to the sea would also be folded. None seen in the 6 test towns.

### D13 — Lakes are steps of their own (decided 2026-09-28)

Author's decision. A reach that lies at least 50 % and at least 500 m inside a named lake becomes that lake (`naming.mark_lakes`). Lake sources: OSM `natural=water` + `water=lake` (from the `osm-waterways` workflow), then Natural Earth lakes + Europe lakes supplement (`featurecla` Lake or Alkaline Lake). Reservoirs are left out on purpose (agent's default, easy to change): otherwise dams would chop big rivers into "Danube → Iron Gate reservoir → Danube". Starnberg now reads "(stream) → Lake Starnberg → Würm → …"; the lake step is only 0.56 km because HydroATLAS brings the town's stream in at the lake's northern tip, next to the outflow (that reach is 94 % inside the OSM lake, 100 % inside Natural Earth's; both outlines 56.1 km²).

Known limitation, found 2026-09-28: lakes only appear where the HydroATLAS path runs through them. The OSM Loisach runs 3.9 km inside Kochelsee (5.87 km²), but the HydroATLAS path from Garmisch-Partenkirchen passes 2.92 km from the lake, so Garmisch shows no Kochelsee. Possible fix later: check whether the OSM line of the river matched to a stretch crosses a named lake.

OSM lakes for Bavaria (release `osm-waterways-europe-germany-bayern`, 2026-09-28): 745 named `water=lake` areas, 1.56 MB; includes Starnberger See (name:en Lake Starnberg), Ammersee, Chiemsee (Lake Chiemsee), Kochelsee.

## OSM for all of Europe (2026-09-29)

All 122 regions in `pipeline/downstream/osm_regions.txt` extracted by `osm-waterways` (244 files, 1.8 GB locally). `build_names --workers 4` 206 s; `paths --all` 254 s. 6,903 towns in the rotation, 0 errors; payload median 1.9 KB, max 4.9 KB.

Fixes after the first run with all regions, checked by diffing all chains (3,501 changed, 0 endpoints changed):
1. **Bilingual OSM names weren't split**: Munich's Danube ended "Danube → Dunărea - Дунав → … → Dunărea - Дунай" (locked test failed). `name_variants` now splits on `/` (with or without spaces), ` - `, ` – `, `;` and parentheses ("Brațul Borcea (Dunărea)"); hyphens without spaces ("Main-Donau-Kanal") stay.
2. **Rhine delta**: the Rhine splits at Pannerden 172 km from its HydroATLAS mouth, outside the 150 km delta zone, so 664 towns ended "Rhine → Bijlandsch Kanaal → Pannerdensch Kanaal". Delta zone 150 → 200 km; the < 5 % area-growth rule still keeps real confluences.
3. **Curated names** (D7) for the main rivers the report shows under several local names: Elbe/Labe, Vltava (de Moldau), Oder/Odra, Vistula (Weichsel), Tagus (Tajo/Tejo), Seine, Dnieper (Dnepr), Thames (Themse), Scheldt, Meuse (Maas), Rhône, Tisza (Theiß), Loire, Garonne, Moselle, Sava, Dniester (Dnister), Neman (Memel), Douro (Duero), Ebro, Maritsa, Vardar, Pripyat (Prypjat), Tiber. E.g. Toledo "Río Tajo → Río Tajo / Rio Tejo" → "Tagus"; Prague "Vltava → Labe → Elbe" → "Vltava → Elbe"; Bucharest → "Dâmbovița → Argeș → Danube".

Follow-up fixes (2026-09-29, after the author's extra towns), each diffed over all 7,048 towns:
4. **One river, two ways of writing it**: neighbouring steps that share a name part are one step (54 pairs: "Bug / Заходні Буг → Bug", "Río Guadiana → Río Guadiana / Rio Guadiana", "Soča → Isonzo / Soča / Lusinç"); uncurated multi-part names compare on their alphabetically first part, so "Eisack - Isarco" = "Isarco - Eisack". Curated Soča (de Isonzo). 136 chains changed, all merges of one river.
5. **Ditches beside big rivers**: below the Isarco–Adige confluence the sample points split between the two rivers (~400 m away), no river got a majority, and in the next round a `waterway=ditch` 95 m away won. Bolzano, Merano, Bressanone, Eppan and Wolkenstein showed "Fossa di Laives → Fossa Grande". Now ditches and drains don't vote on reaches of ≥ 500 km² upstream area that have an OSM river within 600 m. Tried first and rejected: (a) plurality among rivers — side arms won ("Linker Regnitzarm", "Стара Самара", 271 chains changed); (b) ditches only where nothing else is near — 1,357 reaches lost real names (Berlin's Zingergraben); (c) without the river-near condition — Matera lost "Torrente Gravina di Matera" (tagged `waterway=drain` in OSM). Final: 8 chains changed, all fixes; 14 reaches lost a name, 5 gained one.

Author's decisions 2026-09-29 (D15–D17):
- **D15, Greek and Cyrillic in English** (`pipeline/downstream/latin.py`). A mixed name keeps its Latin parts ("Neris - Вілія" → "Neris"); else OSM `name:en`, most common per name, written by `build_names` to `name_table/name_en.csv` and published with the ODbL name table; else a standard romanization: Ukrainian national 2010, Russian/Belarusian/Macedonian BGN/PCGN without diacritics, Bulgarian official 2009, Serbian Latin alphabet, Greek ELOT 743 without accents. Language from the letters (ў → Belarusian, ї/є/ґ → Ukrainian, ђ/ћ → Serbian, ѓ/ќ/ѕ → Macedonian, ы/э/ё → Russian), else from the town's country. German shows the same form (D7: only curated names get German). Result: 0 of 6,918 chains and endpoints left in Greek or Cyrillic (were 613 chains, 3 endpoints); of 1,256 names converted, 909 from `name:en`, 298 romanized, 49 Latin part. Steps that then read the same merge (Горинь/Гарынь → Horyn). Curated Seversky Donets (de Siwerskyj Donez): Kharkiv showed "Severskiy Donets River → Donets". Some OSM English names end in "River" ("Mukhavets River", "Poltva River"); kept as OSM has them (D16).
- **D16**: prefixes stay for now.
- **D17**: town names as GeoNames gives them.

**Estuaries** (2026-09-29, `pipeline/downstream/estuaries.py`, run by `build_names`, output `data/names/estuaries.csv`). HydroATLAS ends big rivers where the estuary begins and counts the estuary as sea: Lisbon's stream (34 km²) ended in the "North Atlantic Ocean"; the Tagus outlet (70,755 km²) is 30 km upstream. OSM draws "Rio Tejo" on through the estuary, 0.8 km from Lisbon's outlet. Rule: an outlet gets the estuary of river R when an OSM `waterway=river` line within 3 km has R's name, R's HydroATLAS outlet is within 100 km and drains ≥ 10× as much, and the line goes on ≥ 3 km beyond the outlet towards the sea (which way is the sea: the far side of R's outlet from R's last reach). 375 outlets in Europe; 84 town chains changed, 0 endpoints: Tagus (Lisbon and 33 districts/towns), Elbe (21: Pinnau, Krückau, Stör, Este, Schwinge, Wedel, Cuxhaven), Thames (10: Southend, Gravesend, Grays), Scheldt (13 around Antwerp), Mersey (5), Weser (2), Oder (Police), Odiel (Aljaraque), Test (Southampton). The step's km is the distance along the OSM line to the sea.

## Full Europe run and build report (2026-09-29)

**Author's decisions 2026-09-29 (D14):**
- **Towns whose first river segment is more than 5 km from the town point are left out of the rotation** (BRIEF R9 "no reach found nearby"). 130 of 7,033 (Den Helder 30 km, Gibraltar, Kos, Badalona, …); listed in the report; no town file. **6,903 towns in the rotation.**
- **"Inner Seas" is not shown.** First idea was to display it as "Sea of the Hebrides" (Wikidata Q1971856, de "Hebridensee"), but the 53 towns ending there were mostly Glasgow/Clyde (~35) and Northern Ireland/Donegal (14): Natural Earth's area covers the whole North Channel coast. Now it's skipped as an endpoint and the search continues by water: Glasgow, Ayr, Belfast, Larne → Irish Sea; Coleraine, Derry, Letterkenny, Isle of Lewis, Fort William → North Atlantic Ocean.

`uv run python -m downstream.paths --all`: all 7,033 Europe towns (D9), one JSON per town in `data/towns/`, report in `data/report/` (`report.md`, `towns.csv`). Also run and published (release `build-report`) by the `build` workflow.

- **7,033/7,033 computed, 0 errors; 243–260 s** for all towns after two speed-ups (was 1,417 s): the sea grid is drawn once for all of Europe (21 s) instead of once per mouth (0.9 s each, 79 % of the time).
- Payload: median 1.9 KB, max 3.8 KB; 0 over 6 KB (R3).
- Fixes found by the full run, each checked by diffing all 7,033 chains before/after:
  1. **683 towns ended in an unnamed sea** (25 mouths; Seine 288, Scheldt 184, Oder 168): narrow estuaries broke into isolated pockets on the 1 km grid. Water now widened by 2 km → 0 unnamed.
  2. **Endpoints too coarse**: only sea/ocean classes counted, so Le Havre ended in the "North Sea" (312 km) and Boden in the "Baltic Sea" (690 km). Now sea, ocean, gulf, bay, channel, strait, fjord of ≥ 15,000 km² count → English Channel, Gulf of Bothnia, Gulf of Finland, Bay of Biscay, Skagerrak, Golfe du Lion, …
  3. **Lake zigzags**: "Rhine → Bodensee → Rhine → Bodensee → Rhine" and similar (Lake Geneva, Zürichsee, Øyeren): repeated visits to one lake with < 5 km of river between are one step. 85 chains.
  4. **Delta fold (D12) was wrong for 1,022 towns**: "fold into the dominant name" renamed the lower Seine "Marne" (288 towns), Vistula "Bug" (196), Oder "Warta" (167), Rhône "Doubs" (100), Garonne "Tarn" (34). The 14 locked towns didn't cover these basins. New rule: in the last 150 km, a name change where the upstream area grows < 5 % (no tributary) is an arm; checked Rhine → Lek +0.0 %, Danube → Bratul Chillia +0.0 %, Warnow → Unterwarnow +1.8 % (fold) vs Streitgraben → Warnow +103 % (kept). Needs `UPLAND_SKM` (added to the fetched columns).
  5. **Inland endings**: the path's last lake is the endpoint (Ptolemaida → Limni Vegoritis); named-lake radius 25 km → 2 km (Cetinje's karst sink was "Lake Skadar", which drains to the Adriatic).
- Remaining, as data: 18 inland sinks, all karst or closed basins (Salento, Greek plateaus, Nikšić, Trebinje, Resen/Prespa, Fucino); 61 % of towns start with "a stream" and OSM names cover a median 0 % of path km, because OSM is only loaded for DE, AT, SI, HR, HU; Natural Earth errors where OSM is missing (Norway's lower Glomma "Vorma", Galicia's Miño "Mio"); 130 towns start more than 5 km from the town point (max 30 km: Den Helder, Gibraltar, Kos, Badalona, …); "Inner Seas" (NE's name for the sea off western Scotland) for 54 towns; national names on one river (Tajo → Tejo).

## Per-river redesign (2026-09-29, author's go 2026-09-28)

Why: per-town naming repeated the same work for every town (every Danube town re-named the Danube) and gave a segment different names on different paths. Now the network is named once, and a town is a lookup.

- **Stage 1** `reach_names.py`: raw name of every reach, same rules as before, vectorised per 1° tile (OSM read per tile). Checked: identical raw names on the 14 towns' 1,349 reaches (1,349/1,349), 7 s instead of 44 s. Whole `eu` region: 938,544 reaches in 2,749 tiles, **96 s** on 4 workers. Raw names: 117,882 reaches (Natural Earth 80,045; OSM 27,928; lakes 9,306; canals 603).
- **Stage 2** `rivers.py`: a river = chain of same-`ORD_CLAS` reaches (checked on all 938,544 `eu` reaches: no reach has two same-order upstream reaches; order never increases downstream; 24,185 outlets). Clean-up per river; names compare as displayed (curated table); on outlet rivers, names after the last stretch of the dominant name fold into it (D12, was "first name on the path"). **5 s** for the region; 150,610 reaches named.
- **Stage 3** `paths.py` reads `data/names/reach_names.csv`; only display rules (side arms, lakes named like their river) stay per path.
- Correction found on the way: with whole rivers, the old fallback "no long block → most frequent name" guessed a lot (32,000 extra reaches named; Graz's start became Ragnitzbach after a 1:1 tie with Leonhardbach). Now: no long block → leave as is.
- Result on the 14 locked towns: **13/14 identical**. Hamburg: "(stream) → Norderelbe → Elbe" became "**Alster** → Norderelbe → Elbe": the start reach is the last 3.7 km of a river OSM names Alster for 20.6 km upstream. Confirmed by the author 2026-09-29; locked in the test.
- The published ODbL name table is now network-wide (`data/names/name_table/`, written by `build_names`), 150,610 rows, one name per segment.
- Build on GitHub 2026-09-29 (run 36501562990, commit e0c52dc): ~4 min total; fetch 135 s, network naming 72 s, paths 10 s; 19/19 tests passed (none skipped); published name table identical to the local one (150,610 rows).

## Name table and build workflow (2026-09-28)

- `pipeline/downstream/name_table.py` writes `name_table.csv` (hyriv_id, kind, name, source, display_en, display_de) and `NOTICE.md` (ODbL notice, OSM attribution, build commit and time). For the 14 example towns: 1,689 rows over 1,344 segments; 345 segments carry more than one name because clean-up depends on the path (e.g. a lower-Danube segment is "Donau" on Munich's path, "Dunav / Дунав" on Graz's). The NOTICE says the table holds names as used on screen, after clean-up.
- `.github/workflows/build.yml` (manual): fetch all inputs (128 s, 895 MB), compute paths (~2 min), run all tests on the real data, publish the `name-table` release. First run 2026-09-28 (run 36498634719): 15/15 tests passed on GitHub, none skipped; same 14 chains as locally; the published CSV is identical to the local one (1,690 lines incl. header). Release: https://github.com/nikokoren/downstream/releases/tag/name-table
- D10's publishing condition (ODbL 4.4/4.6) is met for the current outputs. Rebuild whenever names or towns change.

## Pipeline test results, round 3: + Slovenia, Croatia, Hungary; tunnel re-extraction (2026-09-28)

- All 17 Austria/Germany regions re-extracted with the `tunnel` tag (18/18 jobs OK); Slovenia, Croatia, Hungary added (3/3 OK). 20 regions in `osm_regions.txt`, 40 files locally.
- Stuttgart: sewer main gone → "(stream) → Neckar → Rhine".
- Graz: "(stream) → Mur → Drava → Danube". OSM uses border and local names on this path ("Mur / Mura", "Mura", "Drava / Dráva", "Dunav / Дунав"): names split on " / " into variants, and the curated table got Mur|Mura → Mur/Mur and Drava|Drau|Dráva → Drava/Drau.
- The other 12 towns unchanged; 6 more chains approved by the author (Hamburg, Berlin, Leipzig, Kiel, Innsbruck, Salzburg) and locked into `tests/test_examples.py` (12 towns). Graz and Stuttgart approved by the author the same day and locked in: the end-to-end test now checks all 14 example towns.
- `fetch osm` skips a region whose release isn't published yet (was: the whole step failed).

## Pipeline test results, round 2: Austria + all of Germany (2026-09-28)

OSM for Austria and the 16 German states (`pipeline/downstream/osm_regions.txt`), one GitHub job and release per region: 16/16 jobs succeeded in ~11 min; 731,383 named waterway ways and 5,495 named lakes, 277 MB. 8 new example towns (Hamburg, Berlin, Leipzig, Kiel, Stuttgart, Innsbruck, Salzburg, Graz). First run: 9/14 plausible; the failures and their fixes, each checked on the real data:

| Town | First result | Cause (measured) | Fix |
|---|---|---|---|
| Kiel | end "unknown" | mouth in Kiel Fjord; nearest named seas in a straight line: Mecklenburger Bucht 51.5 km, North Sea 74.5 km (across Jutland), Baltic 137.1 km | `seas.py`: distance through water on a 1 km grid of the Natural Earth ocean → Baltic Sea (166 km by water) |
| Berlin | Havel → Jungfernsee → … (no Spree) | Spree block = 2 reaches but 17.2 km, absorbed by the 3-reach rule; Natural Earth's "Spree" line runs down the Havel | long = 3 reaches **or** 5 km; lakes marked before clean-up; OSM is authoritative where it has lines within 600 m (Natural Earth only outside OSM coverage) |
| Berlin | Havel → Havel | OSM maps a Havel widening as `water=lake` named "Havel" | a lake named like the adjacent river is that river |
| Nuremberg | … Regnitz → Main-Donau-Kanal → Main | canal line closer than the Regnitz near Bamberg | natural rivers vote first; canal names never form a step inside a river |
| Hamburg | Elbe → Norderelbe → Elbe | side arm | A → B → A also across rivers (never across a lake), shortest B first |
| Leipzig | Weisse Elster → Weiße Elster | two OSM spellings | spelling-insensitive name comparison |
| Stuttgart | Nesenbach-Hauptsammler (a sewer main) | OSM: `waterway=stream` + `tunnel=culvert/yes` | `tunnel` tag now extracted; tunnelled ways skipped (done in round 3) |
| Graz | Mur → Danube (no Drava) | Natural Earth labels 215 km of the lower Drava "Mur" (only 13.5 km "Drau"); Croatia/Hungary had no OSM | OSM for Slovenia, Croatia, Hungary (round 3) |

Side effects, accepted: Munich now starts with "a stream" (its first reach runs 4.8 km through the city; no name covers half: Schwabinger Bach 7/24 points, Isar 3, Eisbach 2; the earlier "Isar" was Natural Earth's guess). Hamburg starts with "a stream" and keeps "Norderelbe → Elbe" (HydroATLAS gives the Norderelbe its own `ORD_CLAS`).

Known data limitation: HydroATLAS ends the Elbe at Hamburg-Finkenwerder (the estuary counts as sea), so totals for Hamburg (11.9 km), Berlin and Leipzig stop there.

## Pipeline test results (2026-09-28)

Table updated after D12/D13. Run: `uv run python -m downstream.paths --waterways ../data/raw/osm_waterways_bayern.fgb --lakes ../data/raw/osm_lakes_bayern.fgb` (inputs from `downstream.fetch` + the OSM release asset). Checked by `tests/test_examples.py` (skipped without the data).

| Town (en / de) | Chain | km | End | Payload |
|---|---|---|---|---|
| Munich / München | Isar → Danube | 2,587.6 | Black Sea | 2,397 B |
| Garmisch-Partenkirchen | Partnach → Loisach → Isar → Danube | 2,685.5 | Black Sea | 2,659 B |
| Starnberg | (stream) → Lake Starnberg → Würm → Amper → Isar → Danube | 2,626.5 | Black Sea | 2,835 B |
| Nuremberg / Nürnberg | Pegnitz → Regnitz → Main → Rhine | 1,003.4 | North Sea | 2,058 B |
| Cologne / Köln | Rhine | 349.2 | North Sea | 2,093 B |
| Vienna / Wien | (stream) → Danube | 2,066.1 | Black Sea | 2,042 B |

How naming works now (`pipeline/downstream/naming.py`): every path reach gets the name of the nearest named line along it (OSM first, 600 m; Natural Earth second, 3 km), where each sample point votes for its closest line and bigger rivers count as closer. Then, per river (a run of equal `ORD_CLAS`): names shorter than 3 reaches are absorbed, and A → B → A becomes A. Each rule came from a failure in this run:
- Every endpoint was "South Pacific Ocean": whole-ocean polygons distort in the Europe projection. Fixed by clipping Natural Earth to a Europe window first.
- The Danube chain fragmented into "(unnamed)" pieces and tributary names (Beli Timok, Ogosta, Lippe, Hammerbach). Natural Earth's generalized Danube lies 2.4–6.0 km from the HydroATLAS Danube in Bulgaria/Romania (Munich path, reaches 466–485), so tributary lines were closer.
- The Regnitz vanished when a whole river got one vote (Pegnitz and Regnitz share an `ORD_CLAS` run).

Other findings:
- R7 total distance: summing `LENGTH_KM` along the path gives 0.5–0.7 % more than `DIST_DN_KM + LENGTH_KM` of the start reach (Munich 2,599.9 vs 2,587.6; Cologne 351.8 vs 349.2). We show the latter (the dataset's own figure).
- Payload was 7.7–8.1 KB with 0.01° simplification; now capped at 120 map points: 2.1–2.7 KB (R3 budget ~6 KB).
- Starnberg's first reach runs mostly through Lake Starnberg, where OSM has no stream line, so it stays "(stream)". Vienna's first stream is outside the Bavaria OSM extract.
- OSM Bavaria (Geofabrik, 2026-09-28): 853,048,441-byte extract, MD5 OK, 180 s to extract on `ubuntu-latest`, 91,971 named waterway ways, 8,073 distinct names, 37.5 MB FlatGeobuf.
- Runtime here for all 6 towns: ~10 s after the data is local. `fetch`: RiverATLAS `eu` 48 s (938,544 reaches), BasinATLAS level 12 in the Europe window 79 s (72,859 sub-basins).

Open questions for the author (both answered 2026-09-28, see D12 and D13):
1. **Delta arms.** HydroATLAS ends the Danube via the Chilia arm and the Rhine via the Lek, and the chain says so ("Bratul Chillia", Natural Earth's spelling; Romanian is "Brațul Chilia"). Show the arm, or fold it into the main river?
2. **Lakes on the path.** Paths through lakes (Lake Starnberg) show no lake. Add lake names from OSM or Natural Earth as their own chain step ("→ Lake Starnberg →")?

## Verified facts about outside systems

### German names of endpoint seas (checked 2026-09-29; re-fetch before relying on this)

en.wikipedia API `prop=langlinks&lllang=de` for the English articles, then de.wikipedia API for each German title (all exist, no redirects): North Sea → Nordsee, Black Sea → Schwarzes Meer, Baltic Sea → Ostsee, North Atlantic → Nordatlantik, Adriatic Sea → Adriatisches Meer, English Channel → Ärmelkanal, Tyrrhenian Sea → Tyrrhenisches Meer, Balearic Sea → Balearen-Meer, Irish Sea → Irische See, Bay of Biscay → Biskaya, Gulf of Lion → Golfe du Lion, Mediterranean Sea → Mittelmeer, Sea of Azov → Asowsches Meer, Aegean Sea → Ägäisches Meer, Bristol Channel → Bristolkanal, Gulf of Finland → Finnischer Meerbusen, Kattegat → Kattegat, Ionian Sea → Ionisches Meer, Gulf of Bothnia → Bottnischer Meerbusen, Sea of Crete → Kretisches Meer, Alboran Sea → Alborán-Meer, Gulf of Riga → Rigaischer Meerbusen, Skagerrak → Skagerrak, Norwegian Sea → Europäisches Nordmeer, Greenland Sea → Grönlandsee, Lake Vegoritida → Vegoritida-See. Lake Paralimni (Greece): no German link. Wikidata and the Wikipedia API answered HTTP 429 from the session container; fetched through WebFetch instead.


All verified 2026-09-28 by fetching the URL. **Re-fetch before relying on any of these.**

### HydroRIVERS (v1.0)

- Page https://www.hydrosheds.org/products/hydrorivers (the brief's `/page/hydrorivers` redirects there). TechDoc: HydroRIVERS_TechDoc_v10.pdf, v1.0, October 2019, 7 pages.
- 8,477,883 reaches, average length 4.23 km, 35.85 million km total (TechDoc §2.1). Streams start where catchment ≥ 10 km² or average discharge ≥ 0.1 m³/s. Brief's figures confirmed.
- Columns (TechDoc §3.2): `HYRIV_ID`, `NEXT_DOWN`, `MAIN_RIV`, `LENGTH_KM`, `DIST_DN_KM`, `DIST_UP_KM`, `CATCH_SKM`, `UPLAND_SKM`, `ENDORHEIC`, `DIS_AV_CMS`, `ORD_STRA`, `ORD_CLAS`, `ORD_FLOW`, `HYBAS_L12`. Brief's field names confirmed.
- `HYRIV_ID` is 8 digits; first digit = region (1 Africa, 2 Europe, 3 Siberia, 4 Asia, 5 Australia, 6 South America, 7 North America, 8 Arctic, 9 Greenland).
- `NEXT_DOWN` = 0 means no downstream connection, "the last river reach draining into the ocean or into an inland sink". `ENDORHEIC`: 0 = not part of an endorheic basin, 1 = part of one.
- **`DIST_DN_KM` is measured from the reach's outlet (most downstream pixel)**, "to the final downstream location … either the pour point into the ocean or an endorheic sink". Consequence for R7: the total from a point on the start reach is `DIST_DN_KM` plus the part of that reach's `LENGTH_KM` below the start point, not `DIST_DN_KM` alone.
- `HYBAS_L12` refers to HydroBASINS level 12 **standard format (without lakes)**. The TechDoc is inconsistent (§2.3 says `HYBAS_ID`, §3.2 says `HYBAS_L12`); the real RiverATLAS file uses `HYBAS_L12` (checked 2026-09-28).
- `ORD_CLAS` = 1 marks main stems (sink to source); may help the name join (P3).
- Quality "significantly inferior" above 60°N (HYDRO1k inserted instead of SRTM). Brief confirmed.
- Downloads (page lists sizes): global shapefile `https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_shp.zip` (544 MB; Content-Length 544,388,154), Europe `HydroRIVERS_v10_eu_shp.zip` (68 MB; 67,648,957). Pattern `HydroRIVERS_v10_{af,ar,as,au,eu,gr,na,sa,si}_shp.zip`; `.gdb.zip` variants also exist. WGS84 lat/lon.
- The Central Asia outlet quirk (BRIEF §4.1) is from a user report the brief doesn't link; not verified here.

### HydroBASINS (v1.c)

- Page https://www.hydrosheds.org/products/hydrobasins. TechDoc HydroBASINS_TechDoc_v1c.pdf, 9 pages.
- Two formats: standard (without lakes) `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_{region}_lev01-12_v1c.zip`, and customized with lakes (`hybas_lake_…`). Use **standard**, to match `HYBAS_L12`.
- Each zip holds all 12 levels: Europe 360,873,795 bytes, Asia 376,386,706 bytes. There's no level-12-only download on the page.
- Columns: `HYBAS_ID` (10 digits: region, level, 6-digit ID, side), `NEXT_DOWN`, `NEXT_SINK`, `MAIN_BAS`, `DIST_SINK`, `DIST_MAIN`, `SUB_AREA`, `UP_AREA`, `PFAF_ID`, `ENDO`, `COAST`, `ORDER` (TechDoc §3.2).
- `ENDO`: 0 = not endorheic, 1 = part of an endorheic basin, 2 = sink of one. `ENDO` = 2 with `NEXT_DOWN` > 0 marks a **virtual connection** (small inland sink linked to a larger basin). `COAST` = 1 marks lumped coastal basins. Both are candidates for the P4 endpoint check and the R9 "start point already at the coast" state.

### HydroATLAS v1.0 (RiverATLAS, BasinATLAS): the river data source (D5)

- Page https://www.hydrosheds.org/products/hydroatlas: "licensed under a Creative Commons Attribution (CC-BY) 4.0 International License". The HydroRIVERS page says "the overarching HydroATLAS database fully contains all river reaches of HydroRIVERS".
- TechDoc: HydroATLAS_TechDoc_v10_1.pdf, v1.0.1, June 2022, 18 pages. §4.1 license text quoted in D5. Appendix 1 lists the HydroBASINS columns carried by BasinATLAS (incl. `HYBAS_ID`, `NEXT_DOWN`, `ENDO`, `COAST`); Appendix 2 lists the HydroRIVERS columns carried by RiverATLAS (`HYRIV_ID`, `NEXT_DOWN`, `MAIN_RIV`, `LENGTH_KM`, `DIST_DN_KM`, `DIST_UP_KM`, `CATCH_SKM`, `UPLAND_SKM`, `ENDORHEIC`, `DIS_AV_CMS`, `ORD_STRA`, `ORD_CLAS`, `ORD_FLOW`, `HYBAS_L12`).
- RiverATLAS catalog (57 pages): each of the ~56 added variables has its own license line. All are CC BY 4.0 in HydroATLAS form, some noting a different original license (e.g. "Original: Free for non-commercial use -- HydroATLAS: Creative Commons CC-BY 4.0"). We need none of the added variables.
- figshare https://doi.org/10.6084/m9.figshare.9890531 (API `https://api.figshare.com/v2/articles/9890531`): "HydroATLAS version 1.0", license CC BY 4.0, published 2019-12-07. Files: `RiverATLAS_Data_v10_shp.zip` 2,418,581,202 bytes; `RiverATLAS_Data_v10.gdb.zip` 2,506,480,742; `BasinATLAS_Data_v10_shp.zip` 4,276,492,333; `BasinATLAS_Data_v10.gdb.zip` 2,695,658,577. Download via `https://ndownloader.figshare.com/files/{id}` (ids 20087486, 20087321, 20087237, 20082137).
- TechDoc §3b: RiverATLAS shapefiles come in regional tiles (split north/south where needed); BasinATLAS as global per-level layers `BasinATLAS_v10_levXX`.
- Citation requested (§4.4): Linke, S., Lehner, B., Ouellet Dallaire, C., Ariwi, J., Grill, G., Anand, M., Beames, P., Burchard-Levine, V., Maxwell, S., Moidu, H., Tan, F., Thieme, M. (2019). Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution. Scientific Data 6: 283. https://doi.org/10.1038/s41597-019-0300-6. Plus the source data (Lehner & Grill 2013) and a link to https://www.hydrosheds.org/hydroatlas "if possible".
- **figshare zips, read 2026-09-28 by HTTP range requests (server answers 206):**
  - `RiverATLAS_Data_v10_shp.zip` (2,418,581,202 bytes) holds regional shapefiles `RiverATLAS_v10_{af,ar,as,au,eu,gr,na,sa_north,sa_south,si}`. Europe: `.dbf` 1,282,060,578 bytes (233 MB compressed), `.shp` 151,566,516 (40 MB), `.shx` 7,508,452. So the Europe part is ~276 MB to download.
  - `BasinATLAS_Data_v10_shp.zip` (4,276,492,333 bytes) holds global layers `BasinATLAS_v10_lev01`…`lev12`. Level 12: `.dbf` 1,437,384,812 bytes (247 MB compressed), `.shp` 1,317,872,444 (674 MB). So level 12 is ~926 MB to download, global only.
  - `RiverATLAS_v10_eu.shp`: **938,544** features, 295 fields. The first 14 are the HydroRIVERS columns, and the sub-basin column really is named **`HYBAS_L12`** (settles the TechDoc inconsistency noted under HydroRIVERS).
- HydroSHEDS v2 (https://www.hydrosheds.org/products/hydrosheds-v2) is also CC BY 4.0, but covers only the Americas so far and has no HydroRIVERS/HydroBASINS equivalent yet ("future releases will include … HydroRIVERS products"). Not usable for v1.

### HydroSHEDS v1 agreement (applies to the HydroRIVERS and HydroBASINS downloads, which we don't use; D5)

- Agreement: HydroSHEDS TechDoc v1.4, Appendix A. Excerpts and the verbatim Exhibit B statement are in `docs/sources/HYDROSHEDS_LICENSE.md`. Open questions are in D5.
- Exhibit B's statement must go in "the documentation or metadata" of the product. The agreement allows no short form (searched pages 24–29 for "short", "abbreviat", "screen": zero relevant hits). So the on-screen credit (R16) is extra, and the full statement goes in the README and store listing. This answers the brief's "confirm the short form satisfies the license agreement".
- (Superseded by D5.) Correction to R17: two citations apply. HydroRIVERS and HydroBASINS ask for Lehner & Grill (2013); Exhibit B gives Lehner, Verdin & Jarvis (2008) for HydroSHEDS. The README carries both.

### OpenStreetMap (names, ODbL)

- License: https://www.openstreetmap.org/copyright: OSM data is under the Open Database License (ODbL) 1.0; credit "OpenStreetMap and its contributors". ODbL text: https://opendatacommons.org/licenses/odbl/1-0/. Clauses used in D10: §4.2 (notices for a conveyed database), §4.3 (notice for a Produced Work; example: "Contains information from DATABASE NAME, which is made available here under the Open Database License (ODbL)"), §4.4 (share-alike; b: extraction of a substantial part into a new database is a Derivative Database; c: a Derivative Database is publicly used if a Produced Work from it is), §4.5 (limits: Collective Databases; Produced Works don't create Derivative Databases), §4.6 (offer the Derivative Database or the method, free of charge online).
- OSMF Community Guidelines index: https://osmfoundation.org/wiki/Licence/Community_Guidelines. Read on 2026-09-28: Collective Database (endorsed 2016-06-17), Horizontal Map Layers (2014-06-06), Produced Work (2014-06-06), Substantial (2014-06-06; "insubstantial" is under 100 features or an area of up to 1,000 inhabitants, one-off; ours is far above that), Attribution Guideline (adopted 2021-06-25).
- Sample, Overpass API, bbox 47.95–48.45 N, 11.2–11.75 E (Munich area), `way[waterway~river|stream|canal]`, OSM base 2026-09-28T19:34:04Z, via the maps.mail.ru mirror (overpass-api.de: connection reset; overpass.kumi.systems: HTTP 504): 4,127 ways; river 225 named / 54 unnamed; stream 1,891 / 1,642; canal 213 / 102; 296 distinct names. Present by name: Würm (54 ways, wikidata Q258243 on some), Amper (67, Q166301), Isar (23), Glonn (19), Maisach (16), Hachinger Bach (58), Moosach (47). `wikidata` tags are only on some ways.
- download.geofabrik.de: unreachable from this container on 2026-09-28 (see D10).

### GeoNames (towns)

- Dump https://download.geonames.org/export/dump/, readme https://download.geonames.org/export/dump/readme.txt: "This work is licensed under a Creative Commons Attribution 4.0 License". The about page (https://www.geonames.org/about.html) also lists upstream sources, e.g. a UK gazetteer under the Open Government Licence v1.0 and Royal Mail data for postal codes; the export itself is CC BY 4.0, and we don't use postal codes.
- Files (listing 2026-09-28, regenerated daily): `cities15000.zip` 3.2 MB ("population > 15000 or capitals"), `cities5000.zip` 5.4 MB ("population > 5000 or PPLA"), `cities1000.zip` 11 MB, `cities500.zip` 13 MB; `alternateNamesV2.zip` 195 MB (785 MB unzipped); `countryInfo.txt` 31 KB (has a continent column).
- Columns (readme): geonameid, name, asciiname, alternatenames (no language tags), latitude, longitude, feature class, feature code, country code, cc2, admin1–4 codes, population, elevation, dem, timezone, modification date. `alternateNamesV2` columns used: geonameId, isolanguage, alternate name, isPreferredName, isShortName, isColloquial, isHistoric.
- Counts (downloaded and read 2026-09-28): cities15000 34,146 world / 8,167 Europe; cities5000 69,750 world / **22,015 Europe** ("Europe" = the 54 countries with continent `EU` in countryInfo, which includes all of Russia: 2,759 towns). Feature codes in Europe (cities5000): PPL 9,825, PPLA3 4,230, PPLA2 3,919, PPLX 1,910, PPLA 1,015, PPLA4 977, …
- `name` is inconsistent: "Munich" and "Vienna" are English, "Köln" is German. Don't use `name` alone for either language.
- German alternate names: 6,523 of the 22,015 European towns have at least one `de` entry, 420 a preferred one. Spot checks: Munich → München (preferred), Köln → Köln, Vienna → Wien, Rome → Rom, Prague → Prag, Bucharest → Bukarest (not marked preferred), Paris → Paris. Germany: 929 of 3,080 towns have a `de` entry; the rest are local names that are already German.
- Spot checks, cities5000: Munich 1,505,005 (geonameid 2867714), Passau 50,560, Garmisch-Partenkirchen 26,022, Bad Tölz 17,434.

### Natural Earth populated places (v5.1.2)

- Page https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/; download via `https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip` (2.8 MB). Public domain (same terms as above).
- 7,342 places worldwide; 1,386 in Europe (same 54-country list); 58 in Germany. All European places carry `NAME_DE` and 1,358 a `WIKIDATAID`. Munich → "München" (POP_MAX 1,275,000); Passau present; Garmisch-Partenkirchen absent. `POP_MAX` uses -99 for unknown.

### Natural Earth (v5.0.0)

- Terms https://www.naturalearthdata.com/about/terms-of-use/: public domain, "No permission is needed … Crediting the authors is unnecessary." Suggested short credit: "Made with Natural Earth."
- Rivers page (the brief's `?p=466` redirects to https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/): base set v5.0.0, plus Europe, North America and **Australia** supplements (the brief mentions only the first two).
- **Europe supplement terms:** "in the public domain and supplementary attribution to the European Commission is optional". Derived, with permission, from the JRC CCM 2.1 database; the original CCM data is non-commercial, but we wouldn't use it. North America and Australia supplement terms: not checked.
- **Download links on naturalearthdata.com returned HTTP 500 on 2026-09-28** (4/4 tried). The NACIS CDN works: `https://naciscdn.org/naturalearth/10m/physical/ne_10m_{layer}.zip`.
- Layers and counts (downloaded and read, v5.0.0):
  - `rivers_lake_centerlines`: 1,473 features; 1,387 named; `featurecla` River 1,201, Lake Centerline 259, River (Intermittent) 11, Canal 2.
  - `rivers_europe` (supplement): 1,325 features; 549 named; 503 with `name_de`.
  - `lakes`: 1,355 features; 745 named.
  - `geography_marine_polys`: 306 features; 295 named; `featurecla` includes sea 71, bay 60, gulf 61, ocean 7, strait 36, and others.
- **All four layers carry `name_de`, `name_en` and `wikidataid`**, but `name_de` isn't reliable German (see D7). `name_de` is filled for every named feature in the base rivers, lakes and marine layers, and differs from `name` in 506/1,387 base rivers, 494/745 lakes, 218/295 marine areas. It's noisy: e.g. river "Rungwa" → name_de "Rungwa River", and marine `name` "SOUTHERN OCEAN" is in capitals. See D7: `name_de` isn't used.
- Spot checks: Danube→Donau, Rhine→Rhein, Black Sea→Schwarzes Meer, North Sea→Nordsee, Caspian Sea→Kaspisches Meer (sea). Isar only in the Europe supplement (D6). "Aral Sea": zero hits by `name` in all four layers.

### Global River Runner (excluded)

- https://ksonda.github.io/global-river-runner/: data is MERIT-Basins under "Creative Commons CC BY-NC-SA". Confirmed excluded.
- API `https://merit.internetofwater.app/processes/river-runner/execution?lat=…&lng=…` answered HTTP 200 for Munich on 2026-09-28 (2.3 s). Response not stored or used.
- The brief's "explicitly unsupported proof of concept": searched the project page for "concept", "unsupported", "experimental", "prototype", zero hits. It may be stated elsewhere (API page, repo README); not checked.

### TRMNL Creator Fund

- https://trmnl.com/blog/creator-fund: 80% of TRMNL+ revenue; 10–15% of other streams (Developer Edition, Clarity Kit). Payout factors: age on live playlists, presence, impressions; threshold 50 connections (installs + forks). Brief confirmed.
- Not in the brief: payouts are split 70% plugin authors, 30% strategic contributors (first payout, November 2025). Since April 1, plugins in the "comics" category aren't monetizable. Weights and thresholds "may change".

### TRMNL platform (checked 2026-09-29; re-fetch before relying on this)

Verbatim excerpts with URLs: `docs/sources/TRMNL_2026-09-29.md`.

- **Webhooks**: 5 KB, 10 KB with TRMNL+ (was 2 KB / 5 KB when the brief was written); 12 posts/hour, 30 with TRMNL+.
- **Polling**: no payload size limit is documented. Searched: help articles "Private Plugins" (9510536), "How refresh rates work", "Dynamic polling URLs", "Plugin not receiving data from polling URL", "Missing data in multiple polling URLs", "TRMNL FAQ", docs.trmnl.com webhooks page and the docs index (`llms.txt`); the help-centre search is client-rendered and returned nothing to curl. R3's ~6 KB stays our own budget (max town payload now 4.9 KB).
- **Polling URL is a Liquid template**: form fields, `{{ trmnl.* }}` globals and filters such as `"now" | date: ...` can build the URL, so a URL can pick the town without server state.
- **Refresh**: on-demand since 2026-05-22 (plugins refresh just before they are shown); the plugin's refresh setting is now a minimum. Account minimum 15 min (5 min with TRMNL+). A recipe author can set the fastest refresh allowed for installs. Unchanged merge variables → no new screen.
- **Saved state** (new): a Serverless transform can write `trmnl_state` (≤ 8,192 bytes, an object), readable in markup and in the next run's Polling URL; per install. Not available with Async Polling.
- **Serverless** (replaced "Transformer" in Aug 2026): run() in Ruby/Node/PHP/Python with network access, 128 MB, 5 s.
- **Recipes**: published private plugins; installs get the author's updates, forks don't. Portrait-mode support is required for recipes published since 2026-01-17. `TRMNL_SKIP_DISPLAY` should not be used in published recipes.
- **Framework**: current is **3.4.0** (2026-09-28); 3.3 docs redirect to 3.4. Plugins are pinned to a Framework version until the author upgrades. Four views: full, half_horizontal, half_vertical, quadrant.
- **Maps (TRMNLMaps, Framework 3.3.0, 2026-08-27)**: bundled in the runtime; MapLibre GL JS 5.24.0 loaded by the plugin from `trmnl.com/js/maplibre-gl/5.24.0/`. Presets streets, minimal, outline, blank. `route()`, `dot()`, `fit()` (integer zoom, no animation), `decodePolyline()` (Google encoded polyline → [lng, lat]). Default tiles: TRMNL's own `maps.trmnl.com` (Shortbread schema), free for the renderer (3.4 docs; the 3.3.0 notes had said OSM's community endpoint). The map adds its own "© OpenStreetMap contributors" label, bottom right; keep it visible. The runtime waits for maps to go idle before capture (`TRMNLMaps.settle()`).
- **Devices** (`/api/models`, 56 models): TRMNL X 1872×1404 at scale 1.8 (1040×780 CSS px; gray-16/gray-4/bw), OG 800×480 (1-bit, 2-bit, and B/W/R/Y).

### CC NonCommercial

- https://wiki.creativecommons.org/wiki/NonCommercial_interpretation: definition quoted in the brief confirmed verbatim; "intent-based and intentionally flexible … there may be gray areas". Unchanged in version 4.0.

## Estimate assumptions (R10)

### Travel time (D3, decided 2026-09-30; code: `pipeline/downstream/paths.py` `travel_days`, `locales.py` `travel_text`)

- **Speed per river segment** from its mean annual flow Q (RiverATLAS `dis_m3_pyr`, m³/s):
  v = 0.238 · Q^0.2 m/s. The exponent comes from Moody & Troutman (2002) hydraulic geometry,
  width = 7.2 Q^0.5 and depth = 0.27 Q^0.3 (quoted in a NOAA paper, fetched 2026-09-30:
  repository.library.noaa.gov/view/noaa/68731), so v = Q / (w·d) = 0.514 Q^0.2.
- **Calibration**: fed with mean rather than bankfull flow, 0.514 Q^0.2 gave Basel → Lobith
  (720 km) 3.7 days. The Rhine's flood wave takes about 5 days there (CHR/IKSR Rhine Alarm Model,
  search result 2026-09-30; re-fetch before relying on it), and water moves at about 0.6× the wave
  speed (kinematic wave, c = 5/3 v), so about 8 days. Coefficient = 0.514 × 3.7 / 8 = 0.238.
  Result: small streams ~0.2 m/s, the lower Danube ~1.3 m/s.
- **Time = Σ length / speed** over the path's segments. Segments with no flow in the data (5 % of
  Europe's) count as 0.01 m³/s.
- **Shown as a range**: estimate ÷ 1.5 to × 1.5, each end rounded to the nearest whole hour, day,
  week, month or year (unit by the upper end), prefixed "about"/"etwa". Munich: 26.5 days →
  "about 3–6 weeks".
- **Lakes and reservoirs** (author, 2026-09-30: "closer to the real number" if the license fits):
  HydroLAKES v1.0 (CC BY 4.0, `docs/sources/HYDROLAKES_2026-09-30.md`) `Res_time` (days = lake
  volume / mean outflow; for a well-mixed lake also the mean time a drop stays). A lake counts when
  its pour point is within 1 km of a path segment (not the start segment: a town at a lake's outlet,
  Geneva, is below it) AND the lake's outflow (`Dis_avg`) is within ×/÷ 2 of that segment's flow,
  so ponds and gravel pits beside big rivers don't add their months to the river. Reservoirs count
  (they hold water the same way; Spain's Tagus and Ukraine's Dnieper chains add months). HydroLAKES
  dates from 2016: it still has the Kakhovka reservoir, drained in 2023.
- **Not included**: the time before rain reaches a stream (soaking in, groundwater: days to
  decades); weirs, canals; seasonal and flood flows.
- **Numbers (2026-09-30 build, with lakes)**: 4,521 of 6,870 towns pass at least one lake or
  reservoir; 1,198 gain over 30 days, 296 over a year. Units shown: hours 1,843 towns, days 2,295,
  weeks 1,594, months 886, years 252. Examples: Munich "about 3–8 weeks" (Danube reservoirs +10 d),
  Konstanz "about 3–7 years" (Lake Constance 1,629 d), Lausanne "about 7–16 years" (Lake Geneva
  3,961 d), Jönköping "about 47–106 years" (Vättern), Geneva "about 6–14 days".

## Corrections log

- 2026-09-29 — GitHub Pages deploys were refused (job failed in 2 s, no log) until the author allowed `main` in Settings → Environments → github-pages; the environment had been created while the old branch was the default.
- 2026-09-29 — The Polling URL can't carry the town count: GitHub's build found 6,920 towns vs 6,918 locally (GeoNames changes daily), and the build's check failed as meant. Now a fixed 7,200 slots; file n holds town n mod count, so ~4 % of towns show twice per cycle; the build fails only if towns exceed 7,200.
- 2026-09-29 — TRMNL webhooks take 5 KB (10 KB with TRMNL+), not 2 KB (5 KB); the brief's R3 note is out of date.
- 2026-09-29 — Framework is at 3.4 (3.3 docs redirect there); the brief's "Framework 3.3" means 3.3 or later. TRMNLMaps has its own `route()`/`fit()`/`dot()`, so R12's "our own GeoJSON source and line layer" is no longer needed.
- 2026-09-29 — Delta zone is 200 km, not 150 km: the Rhine delta starts 172 km from the mouth.
- 2026-09-28 — R7: total distance is `DIST_DN_KM` plus the start reach's remaining length, not `DIST_DN_KM` alone (the column is measured from the reach outlet).
- 2026-09-28 — The RiverATLAS column is `HYBAS_L12`; the TechDoc's `HYBAS_ID` in §2.3 is wrong.
- 2026-09-28 — R17 (after D5): cite Linke et al. 2019 (HydroATLAS) and Lehner & Grill 2013 under CC BY 4.0; the Exhibit B statement and the 2008 citation no longer apply.
- 2026-09-28 — BRIEF §4.2 says HydroBASINS is used for "R5"; the point lookup is R4.
- 2026-09-28 — BRIEF §4.3: the Europe supplement's terms are checked (public domain); an Australia supplement also exists.
