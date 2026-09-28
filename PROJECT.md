# PROJECT.md — Downstream

Working memory for the project. Every fact about an outside system carries **what, version, date verified, and "re-fetch before relying on this"**. Newest entries at the top of each section.

## Status

- 2026-09-28 — Step 1 done: all 7 sources in BRIEF §14 re-fetched, plus the HydroSHEDS license (TechDoc v1.4), HydroBASINS TechDoc v1.c and Natural Earth's terms and physical downloads page. Facts are recorded below. Two findings block v1 as the brief describes it: **D5** (license terms) and **D6** (Isar isn't in the base Natural Earth river set).
- 2026-09-28 — Repo scaffolded: brief stored (`docs/BRIEF.md`), agent rules (`CLAUDE.md`), empty `pipeline/`, `worker/`, `recipe/`, `fixtures/`.

## Next steps (in order)

1. Author decides D5 and D6 (below).
2. Copy the map rules from Aurora Watch's CLAUDE.md into `docs/MAP_RULES.md`; copy the LOCALES pattern and `fixtures/` generator approach.
3. Choose pipeline tooling (language, geo libraries, tile format) and record the choice as a decision.
4. Pipeline on a small region first (R21): HydroRIVERS `eu` + HydroBASINS `eu`, so Munich (R20 #1) can pass early. On first download, confirm the real column names (see the HYBAS_L12 note below).
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
| D5 | HydroSHEDS license fit (see below) | **Open, blocking** | 2026-09-28 |
| D6 | Use Natural Earth's Europe supplement in v1 (see below) | **Open, blocking acceptance test #1** | 2026-09-28 |

### D5 — HydroSHEDS license fit (raised 2026-09-28)

The product pages say "free for … commercial use", but the actual agreement (verbatim in `docs/sources/HYDROSHEDS_LICENSE.md`) is written as a distribution contract. Clauses that are awkward for a free TRMNL recipe:

- §2.1.2: distribution to End Users must be under an end user license "at least as protective" as the agreement; §1.2 defines End Users as parties with a *written* license agreement. A TRMNL recipe has no EULA.
- §10.7: keep records of "the identity and address of each End User" for two years.
- §2.1.2: never distribute the data "as a stand-alone product". Implication regardless of outcome: the R2 tiles must stay private (Worker-only), never a public bucket, and derived data never goes into this repo.
- §8.1: no use of WWF's name, trademarks or logos without written consent. The brief's on-screen credit "River data: HydroSHEDS © WWF" uses the name; Exhibit B itself names "© World Wildlife Fund, Inc.", so a copyright line is probably what they expect, but no logo.
- §7.1: WWF can terminate "in sole discretion".

Options: (a) proceed on the plain-language "free for commercial use" reading and the Exhibit B attribution; (b) **recommended:** email the HydroSHEDS team (Bernhard Lehner, contact on the TechDocs) describing the recipe, ask whether it's fine without a EULA or end-user records, and ask which on-screen credit they'd like. Store the reply in `docs/permissions/`. Not legal advice.

### D6 — Isar needs the Natural Earth Europe supplement (raised 2026-09-28)

`ne_10m_rivers_lake_centerlines` v5.0.0 has Danube/Donau and Rhine/Rhein but **no Isar** (searched all 1,473 features by `name`, zero hits). Isar is in `ne_10m_rivers_europe` v5.0.0 (the "Europe supplement"). BRIEF §13 puts the supplement out of scope for v1, and §4.3 says its terms need checking. The terms are now checked: public domain (see facts below). Recommended: bring the Europe supplement into v1; without it, Munich would read "streams → Danube → Black Sea" and acceptance test #1 fails. The North America and Australia supplements' terms are not checked yet.

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

### HydroSHEDS license (applies to HydroRIVERS and HydroBASINS)

- Agreement: HydroSHEDS TechDoc v1.4, Appendix A. Excerpts and the verbatim Exhibit B statement are in `docs/sources/HYDROSHEDS_LICENSE.md`. Open questions are in D5.
- Exhibit B's statement must go in "the documentation or metadata" of the product. The agreement allows no short form (searched pages 24–29 for "short", "abbreviat", "screen": zero relevant hits). So the on-screen credit (R16) is extra, and the full statement goes in the README and store listing. This answers the brief's "confirm the short form satisfies the license agreement".
- Correction to R17: two citations apply. HydroRIVERS and HydroBASINS ask for Lehner & Grill (2013); Exhibit B gives Lehner, Verdin & Jarvis (2008) for HydroSHEDS. The README carries both.

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
- **All four layers carry `name_de`, `name_en` and `wikidataid`**; the brief assumed English names only. `name_de` is filled for every named feature in the base rivers, lakes and marine layers, and differs from `name` in 506/1,387 base rivers, 494/745 lakes, 218/295 marine areas. It's noisy: e.g. river "Rungwa" → name_de "Rungwa River", and marine `name` "SOUTHERN OCEAN" is in capitals. So the R8 curated table stays, as overrides on top of `name_de`.
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
- 2026-09-28 — R17: cite Lehner, Verdin & Jarvis 2008 (Exhibit B) as well as Lehner & Grill 2013.
- 2026-09-28 — BRIEF §4.2 says HydroBASINS is used for "R5"; the point lookup is R4.
- 2026-09-28 — BRIEF §4.3: the Europe supplement's terms are checked (public domain); an Australia supplement also exists.
