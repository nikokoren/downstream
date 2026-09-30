# CLAUDE.md — Downstream

TRMNL recipe: rotates through a fixed list of towns and, for each, shows where a raindrop falling there ends up: a full-screen map of the path, plus the town, every stream and river in order, and the endpoint. The user's location is not used (D8 in PROJECT.md overrides BRIEF R1, R2, R4, R19 and P5). Munich → Isar → Danube → Black Sea is acceptance test #1.

## Read first, every session

1. `docs/BRIEF.md` — requirements (R1–R24, P1–P7, decisions D1–D4). Source of truth for *what*.
2. `PROJECT.md` — dated decisions, verified facts about outside systems, and the current status. Source of truth for *where we are*.
3. `docs/TEXT_REQUIREMENTS.md` — must be filled in before any on-screen copy is written (R14).
4. `docs/DESIGN_PHILOSOPHY.md` — how views are built (from On the Move), before touching `recipe/`.

## Working method (adopted 2026-09-27; full text in docs/BRIEF.md)

1. Never verify against invented input. Test payloads are captured from live sources or come from `fixtures/` built from captured data.
2. Sweep the state space (states × languages × views × orientations × devices); report results as numbers.
3. Re-fetch versioned docs; memory is stale. Stamp what was verified and when. The web wins on disagreement.
4. "Not there" needs proof: say what was searched and what came back.
5. Prove fixes: reproduce, show it gone, diff before/after. Device-only proof → "not confirmed on device".
6. Run real data through every new phrase in every state it can appear in.
7. State corrections in one line, then move on.
8. The repo is the memory: every fact about an outside system in `PROJECT.md` carries version, date, and "re-fetch before relying on this".
9. Assume concurrent agents: re-read a file before editing it; don't trust your last-known main.

## Hard rules

- **Licensing:** no NC-licensed data (CC BY-NC, BY-NC-SA, …) unless written permission is stored in `docs/permissions/`. Allowed: public domain, CC0, CC BY, and terms that explicitly allow commercial use. Global River Runner is **excluded** (D4). River data comes from **HydroATLAS (RiverATLAS + BasinATLAS), CC BY 4.0**. Never download or use the HydroRIVERS/HydroBASINS zips: their HydroSHEDS v1 agreement needs a EULA and end-user identity records (D5).
- **Language:** all on-screen words come from the backend LOCALES (en + de); templates contain no literal words (R13). Plain language, no hydrology jargon (R15).
- **Estimates** are labeled as estimates on screen, and the assumption is documented in `PROJECT.md` (R10).
- **Attribution** on every view (R16); CC BY 4.0 credit for HydroATLAS (Linke et al. 2019, plus Lehner & Grill 2013) with license link and a modification note in README and store listing (R17).
- **Payload** under ~6 KB (R3).
- **Maps** (R12): MapLibre via TRMNLMaps; never mutate the preset's style object; use `idle` for measuring; literal stretch axes; loading fallbacks. Design and map rules from On the Move are in `docs/DESIGN_PHILOSOPHY.md` (read it before building views); Aurora Watch's map rules are not copied yet.
- **Endpoint classification** must not trust `NEXT_DOWN == 0 && ENDORHEIC == 0` alone (Central Asia quirk, R9/P4).
- Raw downloaded data never gets committed (`data/` is git-ignored except its README).
- German names only from the curated table; never use Natural Earth's `name_de` (D7).
- Stream and river names come from OpenStreetMap (ODbL, D10): the name table is published under ODbL, and the screen credits OpenStreetMap.
- Pipeline: Python 3.12 + uv in `pipeline/` (D11). Run `uv run pytest` and `uv run ruff check` there before committing pipeline code.

## Layout

| Path | Purpose |
|---|---|
| `docs/BRIEF.md` | Requirements, verbatim |
| `docs/TEXT_REQUIREMENTS.md` | Copy slots and budgets (R14), stub |
| `docs/DESIGN_PHILOSOPHY.md` | View design rules from On the Move, plus the Downstream proposal |
| `docs/sources/` | Verbatim excerpts of outside terms we depend on, dated |
| `docs/permissions/` | Written data-use permissions, if any are ever granted |
| `PROJECT.md` | Decisions log, verified facts, status, estimate assumptions |
| `pipeline/` | Build-time data prep, P1–P7 |
| `worker/` | Cloudflare Worker: not used for now; the rotation is static files on GitHub Pages picked by the Polling URL (D18) |
| `recipe/` | TRMNL markup, four views (Framework 3.4), and the Polling URL |
| `fixtures/` | Captured payloads + generator script (R23) |
| `data/` | Local downloads and build output (git-ignored) |
