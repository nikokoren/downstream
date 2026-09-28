# PROJECT.md — Downstream

Working memory for the project. Every fact about an outside system carries **what, version, date verified, and "re-fetch before relying on this"**. Newest entries at the top of each section.

## Status

- 2026-09-28 — D5 decided (HydroATLAS), D6 decided (Europe supplement in v1), D7 proposed (German names from the curated table only).
- 2026-09-28 — Step 1 done: all 7 sources in BRIEF §14 re-fetched, plus the HydroSHEDS license (TechDoc v1.4), HydroBASINS TechDoc v1.c and Natural Earth's terms and physical downloads page. Facts are recorded below. Two findings block v1 as the brief describes it: **D5** (license terms) and **D6** (Isar isn't in the base Natural Earth river set).
- 2026-09-28 — Repo scaffolded: brief stored (`docs/BRIEF.md`), agent rules (`CLAUDE.md`), empty `pipeline/`, `worker/`, `recipe/`, `fixtures/`.

## Next steps (in order)

1. Author confirms D7 (German names).
2. Copy the map rules from Aurora Watch's CLAUDE.md into `docs/MAP_RULES.md`; copy the LOCALES pattern and `fixtures/` generator approach.
3. Choose pipeline tooling (language, geo libraries, tile format) and record the choice as a decision.
4. Pipeline on a small region first (R21), clipped from RiverATLAS/BasinATLAS (D5) to the Danube and Rhine basins, plus the Natural Earth Europe supplement (D6), so Munich (R20 #1) can pass early. On first download, confirm the real column names (see the HYBAS_L12 note below).
5. Fill in `docs/TEXT_REQUIREMENTS.md` before writing any copy (R14).
6. Not yet verified, needed later: Cloudflare R2 and KV free allowances (D1), TRMNL polling size limit (R3), USGS NLDI, Open-Meteo terms (D2), TRMNL Framework 3.3 and TRMNLMaps docs.

## Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| L | No NC-licensed data without written permission (BRIEF §2) | Decided | 2026-09 (brief) |
| D1 | Coverage for v1: global vs. regions | Open — recommended global if it fits R2 free tier; measure after first build | — |
| D2 | Live element (e.g. Open-Meteo "raining here now") | Open | — |
| D3 | Show travel time at all | Open | — |
| D4 | Ask Global River Runner maintainers for permission | Open, not needed for v1 | — |
| D5 | River data from HydroATLAS (CC BY 4.0), not the HydroRIVERS/HydroBASINS downloads (see below) | Decided | 2026-09-28 |
| D6 | Natural Earth Europe supplement is in v1 (see below) | Decided | 2026-09-28 |
| D7 | German names: curated table only, `name_de` not used (see below) | Proposed | 2026-09-28 |

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

### D7 — German names: curated table only (proposed 2026-09-28)

Natural Earth's `name_de` isn't reliable German. It appears to come from Wikidata, with another label used when Wikidata has no German one (inferred from the example below; NE's docs weren't checked on this). Example: Rungwa (Q35311383) has no German label on Wikidata, only English "Rungwa River", and NE's `name_de` is "Rungwa River". A partial comparison with live Wikidata (632 of 2,678 named features, in Wikidata ID order, so not a random sample; stopped early by the author as enough evidence):
- 385 match today's German Wikidata label or German Wikipedia title;
- 26 have no German label on Wikidata at all, so the value is English or local ("Lake Kariba", "Pardo River", "Quan River");
- 221 differ from today's German label (e.g. "Vaupés" vs "Río Vaupés").

Proposal: German names on screen come **only** from the curated table (R8). Everything else shows NE's `name` (the local or English form), never `name_de`. Wikidata isn't queried at build or request time. The table only needs the rivers, seas and lakes that realistically appear on paths; the pipeline's build report (P7) should list the named features that do appear, so the table can be checked against them.

## Verified facts about outside systems

All verified 2026-09-28 by fetching the URL. **Re-fetch before relying on any of these.**

### HydroRIVERS (v1.0)

- Page https://www.hydrosheds.org/products/hydrorivers (the brief's `/page/hydrorivers` redirects there). TechDoc: HydroRIVERS_TechDoc_v10.pdf, v1.0, October 2019, 7 pages.
- 8,477,883 reaches, average length 4.23 km, 35.85 million km total (TechDoc §2.1). Streams start where catchment ≥ 10 km² or average discharge ≥ 0.1 m³/s. Brief's figures confirmed.
- Columns (TechDoc §3.2): `HYRIV_ID`, `NEXT_DOWN`, `MAIN_RIV`, `LENGTH_KM`, `DIST_DN_KM`, `DIST_UP_KM`, `CATCH_SKM`, `UPLAND_SKM`, `ENDORHEIC`, `DIS_AV_CMS`, `ORD_STRA`, `ORD_CLAS`, `ORD_FLOW`, `HYBAS_L12`. Brief's field names confirmed.
- `HYRIV_ID` is 8 digits; first digit = region (1 Africa, 2 Europe, 3 Siberia, 4 Asia, 5 Australia, 6 South America, 7 North America, 8 Arctic, 9 Greenland).
- `NEXT_DOWN` = 0 means no downstream connection, "the last river reach draining into the ocean or into an inland sink". `ENDORHEIC`: 0 = not part of an endorheic basin, 1 = part of one.
- **`DIST_DN_KM` is measured from the reach's outlet (most downstream pixel)**, "to the final downstream location … either the pour point into the ocean or an endorheic sink". Consequence for R7: the total from a point on the start reach is `DIST_DN_KM` plus the part of that reach's `LENGTH_KM` below the start point, not `DIST_DN_KM` alone.
- `HYBAS_L12` refers to HydroBASINS level 12 **standard format (without lakes)**. The TechDoc is inconsistent: §2.3 calls the column `HYBAS_ID`, §3.2 calls it `HYBAS_L12`. Check the real file on first download.
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
- HydroSHEDS v2 (https://www.hydrosheds.org/products/hydrosheds-v2) is also CC BY 4.0, but covers only the Americas so far and has no HydroRIVERS/HydroBASINS equivalent yet ("future releases will include … HydroRIVERS products"). Not usable for v1.

### HydroSHEDS v1 agreement (applies to the HydroRIVERS and HydroBASINS downloads, which we don't use; D5)

- Agreement: HydroSHEDS TechDoc v1.4, Appendix A. Excerpts and the verbatim Exhibit B statement are in `docs/sources/HYDROSHEDS_LICENSE.md`. Open questions are in D5.
- Exhibit B's statement must go in "the documentation or metadata" of the product. The agreement allows no short form (searched pages 24–29 for "short", "abbreviat", "screen": zero relevant hits). So the on-screen credit (R16) is extra, and the full statement goes in the README and store listing. This answers the brief's "confirm the short form satisfies the license agreement".
- (Superseded by D5.) Correction to R17: two citations apply. HydroRIVERS and HydroBASINS ask for Lehner & Grill (2013); Exhibit B gives Lehner, Verdin & Jarvis (2008) for HydroSHEDS. The README carries both.

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

### TRMNL webhook limits

- https://docs.trmnl.com/go/private-plugins/webhooks: 2 KB, 5 KB for TRMNL+. Brief confirmed.
- Conflict: the Creator Fund blog lists TRMNL+ as "10kb webhook payloads (current: 5kb)". Irrelevant while we use polling (R1).

### CC NonCommercial

- https://wiki.creativecommons.org/wiki/NonCommercial_interpretation: definition quoted in the brief confirmed verbatim; "intent-based and intentionally flexible … there may be gray areas". Unchanged in version 4.0.

## Estimate assumptions (R10)

_None yet. Any travel-time or "reaches the sea in N days" figure must document its flow-speed assumption here before it ships._

## Corrections log

- 2026-09-28 — R7: total distance is `DIST_DN_KM` plus the start reach's remaining length, not `DIST_DN_KM` alone (the column is measured from the reach outlet).
- 2026-09-28 — R17 (after D5): cite Linke et al. 2019 (HydroATLAS) and Lehner & Grill 2013 under CC BY 4.0; the Exhibit B statement and the 2008 citation no longer apply.
- 2026-09-28 — BRIEF §4.2 says HydroBASINS is used for "R5"; the point lookup is R4.
- 2026-09-28 — BRIEF §4.3: the Europe supplement's terms are checked (public domain); an Australia supplement also exists.
