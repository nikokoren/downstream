# CLAUDE.md — Downstream

TRMNL recipe: from the user's location, show where a raindrop ends up (river chain, total distance, endpoint). Munich → Isar → Danube → Black Sea is acceptance test #1.

## Read first, every session

1. `docs/BRIEF.md` — requirements (R1–R24, P1–P7, decisions D1–D4). Source of truth for *what*.
2. `PROJECT.md` — dated decisions, verified facts about outside systems, and the current status. Source of truth for *where we are*.
3. `docs/TEXT_REQUIREMENTS.md` — must be filled in before any on-screen copy is written (R14).

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

- **Licensing:** no NC-licensed data (CC BY-NC, BY-NC-SA, …) unless written permission is stored in `docs/permissions/`. Allowed: public domain, CC0, CC BY, and terms that explicitly allow commercial use. Global River Runner is **excluded** (D4). The HydroSHEDS v1 License Agreement (HydroRIVERS/HydroBASINS downloads) is not acceptable (needs a EULA and end-user records); proposed replacement is HydroATLAS, CC BY 4.0 (D5 in PROJECT.md).
- **Language:** all on-screen words come from the backend LOCALES (en + de); templates contain no literal words (R13). Plain language, no hydrology jargon (R15).
- **Estimates** are labeled as estimates on screen, and the assumption is documented in `PROJECT.md` (R10).
- **Attribution** on every view (R16); full HydroSHEDS Exhibit B statement + Lehner & Grill 2013 and Lehner, Verdin & Jarvis 2008 citations in README and store listing (R17).
- **Payload** under ~6 KB (R3).
- **Maps** (R12): MapLibre via TRMNLMaps; never mutate the preset's style object; use `idle` for measuring; literal stretch axes; loading fallbacks. The full map rules live in Aurora Watch's CLAUDE.md — copy them into `docs/MAP_RULES.md` before building views (not yet done; Aurora Watch is not in this repo).
- **Endpoint classification** must not trust `NEXT_DOWN == 0 && ENDORHEIC == 0` alone (Central Asia quirk, R9/P4).
- Raw downloaded data never gets committed (`data/` is git-ignored except its README).
- HydroSHEDS data (raw or derived tiles) is never publicly downloadable: the R2 bucket is private, reachable only through the Worker (license §2.1.2, no stand-alone distribution; see `docs/sources/HYDROSHEDS_LICENSE.md`).

## Layout

| Path | Purpose |
|---|---|
| `docs/BRIEF.md` | Requirements, verbatim |
| `docs/TEXT_REQUIREMENTS.md` | Copy slots and budgets (R14), stub |
| `docs/sources/` | Verbatim excerpts of outside terms we depend on, dated |
| `docs/permissions/` | Written data-use permissions, if any are ever granted |
| `PROJECT.md` | Decisions log, verified facts, status, estimate assumptions |
| `pipeline/` | Build-time data prep, P1–P7 |
| `worker/` | Cloudflare Worker, R1–R10 |
| `recipe/` | TRMNL markup, four views (Framework 3.3) |
| `fixtures/` | Captured payloads + generator script (R23) |
| `data/` | Local downloads and build output (git-ignored) |
