# Globe and UX examples, 2026-11-13

**Current direction:** the globe was accepted. The author did not select the other proposals
below and instead requested river-change labels and a shared-map watershed comparison. See
[River changes and watershed battle](WATERSHED_BATTLE.md) for the current visual prototypes.
This document retains the earlier review examples as history.

Only the Ridgelines globe has been implemented. The fact line and paired journeys below are
proposals for discussion. The route model, durations, rotation, and production copy are unchanged.

Open the generated [interactive walkthrough](../recipe/tools/out/review/walkthrough.html) or its
[image](../recipe/tools/out/review/walkthrough.png). It contains:

1. Globe on/off comparisons on OG and TRMNL X, landscape/portrait, English/German.
2. A fact-line proposal in the actual full-screen template: Munich's lakes and reservoirs add
   about 10 days to the estimate. That is rounded from `lake_days: 9.7` in the committed preview.
   This proposed copy explains an existing number; it does not validate the duration model.
3. A comparison sketch using Munich and Nuremberg: same country, different seas. Routes and
   distances come from the real published build report, captured in `fixtures/review/routes.json`
   with source URL, date and checksum. No second map was fabricated from the report's text.

The proposed comparison is an explanation of the idea, not a ready-to-ship layout. A future
“nearby towns, different seas” feature should select closer pairs from the data, verify both
routes, and then design their maps. The current examples are two verified German cities.

Other suggestions in concrete terms:

- **Journey chapters:** keep the same town across a few refreshes and change the emphasis from
  the full route to an interesting stop to the destination. It is editorial sequencing, not a
  live drop or an arrival prediction. Per-step geometry should be retained before implementing it.
- **Companion atlas:** an optional QR in the full view opens the complete chain, larger map,
  method and sources on a phone. It can remain a static site with no account.
- **Familiar places:** let a user choose an already computed town to recur among discoveries.
  This would deliberately extend D8, without adding arbitrary-address routing or live location.

## Reproducing the visuals

Use real Framework 3.4.0 CSS/JS/fonts and MapLibre 5.24.0 in `data/raw/framework/3.4.0/`, Ruby
with Liquid 5.14.0 on PATH, and the existing npm dependencies. The normal fetch command is
`uv run python -m downstream.fetch framework` in `pipeline/`. During this review, trmnl.com was
blocked by network policy. Assets were instead obtained from the official
`usetrmnl/trmnl-framework` Git repository at `07a0b39e41c9a702e3f21834853d68720f96c170`,
`public/css/3.4.0`, `public/js/3.4.0` and `public/fonts`; MapLibre came from its pinned npm package.
Only the diagnostic basemap was substituted. No network settings were changed.

From the repository root:

```
CHROME=/usr/bin/chromium WORLD_MAP=both UNITS=all OFFLINE_BASEMAP=1 \
  node recipe/tools/render-check.mjs --preview
```

For the fact-line proposal, copy `recipe/src/*.liquid` into an ignored review directory. In that
copy only, append a label span using `review_insight[lang]` in `ds_box`, and pass `review_insight`
from the full view to the partial. Use a copy of the real Munich payload with:

```
"review_insight": {
  "en": "Lakes and reservoirs add about 10 days.",
  "de": "Seen und Stauseen: rund 10 Tage."
}
```

Render it with `--preview`, `WORLD_MAP=1`, `UNITS=all`, `VIEW=full`, `DEVICE=og_1bit`,
`OFFLINE_BASEMAP=1`, `DS_RECIPE_SRC`, `DS_PREVIEW_PAYLOAD` and
`DS_RENDER_OUT=.../recipe/tools/out/review/insight`. The extra line passed the existing render
checks in both languages and units. Then:

```
CHROME=/usr/bin/chromium node recipe/tools/review-concepts.mjs
```

The generator embeds screenshots in a self-contained HTML file and produces a full-page PNG.
Its custom CSS is confined to the surrounding explanation page. The device images use actual
Framework markup. Generated files stay in the ignored `recipe/tools/out/` directory.

These are browser renders with a diagnostic Natural Earth coastline basemap. They validate
layout, route visibility and globe placement, not hosted TRMNL vector tiles or physical displays.
Attribution and source details for the captured comparison are in `fixtures/review/NOTICE.md`.

Validation recorded on 2026-11-13: 192/192 browser cases, 133 Liquid cases, 2,392 real projection
locations/route points. Four globe-off OG full renders have zero changed pixels against the
original templates. An existing narrow portrait half-view German metric clipping case was
reproduced in the original templates and fixed by letting its distance/time label wrap.
