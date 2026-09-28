# PROJECT.md — Downstream

Working memory for the project. Every fact about an outside system carries **what, version, date verified, and "re-fetch before relying on this"**. Newest entries at the top of each section.

## Status

- 2026-09-28 — Repo scaffolded: brief stored (`docs/BRIEF.md`), agent rules (`CLAUDE.md`), empty `pipeline/`, `worker/`, `recipe/`, `fixtures/`. **No investigation done yet**: no source has been fetched or verified in this repo.

## Next steps (in order)

1. Re-fetch every source in BRIEF §14 and record verified facts below (license text, HydroSHEDS attribution statement and whether a short form is allowed, field names from the HydroRIVERS tech doc, download URLs and file sizes, Natural Earth layer names).
2. Copy the map rules from Aurora Watch's CLAUDE.md into `docs/MAP_RULES.md`; copy the LOCALES pattern and `fixtures/` generator approach.
3. Choose pipeline tooling (language, geo libraries, tile format) and record the choice as a decision.
4. Pipeline on a small region first (R21): Bavaria/Danube basin, so Munich (R20 #1) can pass early.
5. Fill in `docs/TEXT_REQUIREMENTS.md` before writing any copy (R14).

## Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| L | No NC-licensed data without written permission (BRIEF §2) | Decided | 2026-09 (brief) |
| D1 | Coverage for v1: global vs. regions | Open — recommended global if it fits R2 free tier; measure after first build | — |
| D2 | Live element (e.g. Open-Meteo "raining here now") | Open | — |
| D3 | Show travel time at all | Open | — |
| D4 | Ask Global River Runner maintainers for permission | Open, not needed for v1 | — |

## Verified facts about outside systems

_None verified in this repo yet._ The brief's facts were checked by the author in September 2026 but must be re-fetched before use. Template:

```
- <fact>. Source: <unversioned URL>. Version: <x>. Verified: YYYY-MM-DD. Re-fetch before relying on this.
```

## Estimate assumptions (R10)

_None yet. Any travel-time or "reaches the sea in N days" figure must document its flow-speed assumption here before it ships._

## Corrections log

_One line each._
