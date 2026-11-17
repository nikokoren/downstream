# Map label placement — 14 November 2026

Callouts now give both journeys room. Label rectangles avoid complete river strokes, casings,
start/end markers, cards, the globe, attribution, other labels and existing connectors. Both
town labels are planned together before river changes, so one cannot consume the other's only
clear position. Full views reserve space around the route bounds for annotations.

Connectors prefer clear paths and can approach a different side of a label near a river bend.
Every connector is clipped around river strokes and markers. A rare town connection can cross
a river loop with a clear gap at the river, preserving the river's ink. A nearby town label can
omit its connector at tightly clustered starts. River-change callouts yield when crowded; their
steps remain in the cards. Native background city names that conflict are hidden after the
Framework places them. Other background names remain.

The paths retain their actual coordinates. This declutters annotations; geographic paths can
still look close together at whole-route scale. Map labels remain optional and on by default.
Comparison cards, Full-only comparison mode and the existing town-selection rules remain.

The Canadian ordinary fallback also exposed clipped Half vertical portrait river text in both
languages. That field now permits three wrapped lines with the existing font and shortening rule.

## Town labels follow the cards (17 November 2026)

Full's comparison now puts the card of the path lying further west bottom left (`site.order_west_to_east`).
The two town labels prefer the same order: the left card's town label left of the other's. It is a
preference (a 60 px penalty in the joint town search), not a rule, so a crowded start can still
swap them rather than lose a label. Replaying all 2,335 live pairs (feed captured 2026-11-17,
routes reordered) × en/de through `check-map-labels.mjs`: labels against card order went from
1,666 to 17 on OG portrait and from 1,577 to 0 on OG landscape, with 0 town labels omitted in
both. The checker now reports this count (`town_labels_against_card_order`); `DS_LABEL_FRAMES=og_land`
replays the landscape frame.

## Verification

All inputs are actual generated packets from the captured source-checked feed. Framework
**3.4.0** and MapLibre **5.24.0** were used; re-fetch before relying on future runtime versions.

- The original US portrait overlap reproduced in **4/4** language/unit variants. The updated
  actual SVG geometry and screenshot checks pass **4/4** for the same packet.
- **4,670 catalogue placement cases pass**: all **2,335 accepted pairs**, both languages,
  OG portrait, with **zero missing town labels**. An additional **960 cases** cover 120 pairs,
  both languages and all four distinct Full shapes. These replays use actual Liquid cards,
  Framework fonts and a blank MapLibre projection, independently of hosted tiles.
- **36/36 hosted-map browser scenarios pass**, covering six screen types, both languages and
  unit systems, US comparisons, clustered Jičín/Jablonec starts, dense Löbau/Żary, Canadian
  ordinary mashups, the globe and labels off. The checks sample actual visible SVG connector
  strokes after clipping and verify route pixels, label/route/marker clearance, cards and credit.
- **768 native Ruby Liquid cases pass** for independent settings, defaults, Full-only
  comparison, fallback journeys, languages and units. JS syntax, bundle and whitespace checks pass.

The catalogue replay checks town-label retention. Hosted-map scenarios separately check visible
geometry and pixels; this does not claim a screenshot of every pair on every frame. Crowded
river-change omissions are permitted and recorded. Physical-device output is not confirmed.

`recipe/tools/out/label-clearance/validation-summary.json` records the checks and source hashes;
regional scenario folders contain PNGs and full results. `river-labels-us.png` and
`river-labels-europe.png` are lightweight review images. Both were visually inspected.

No feed rebuild, deployment, push or publication was performed for this change.
