# Drainage-divide feed: source checks completed

**2,335 pairs pass the source checks and are included in the local feed.** All 8,348 towns
from the captured published rotations were checked. Their eligibility rules and IDs are
unchanged; no smaller-town or neighbourhood pool was added.

| Region | Towns checked | Geographic candidates at 80 km | Source-checked pairs |
|---|---:|---:|---:|
| Europe | 5,280 | 1,720 | **1,705** |
| USA | 2,816 | 4,447 | **630** |
| Canada | 252 | 1 | **0** |
| Total | **8,348** | **6,168** | **2,335** |

The [complete source-checked CSV](../fixtures/review/source-checked-pairs.csv) includes both
town IDs, destinations, intermediate rivers, route lengths, bilingual travel ranges,
measured start-reach offsets, containing basin IDs, outlet reach IDs and river-change counts.
The [verification record](../fixtures/review/pair-verification.json) retains source URLs,
file hashes, exclusion counts, feed capacities and payload checks.

## What was checked

The original RiverATLAS and BasinATLAS v1.0 geometry is now captured locally. Each comparison
requires a unique basin containing the town point, the selected reach in that same basin,
a start-reach distance ≤1 km, complete acyclic routing to its source outlet, matching model
distance/reach count, a positive travel estimate and a sea endpoint. Explicitly canal-sourced
routes are excluded. Both paths must be ≥100 km, the towns ≤80 km apart, receiver groups
different, and their source basins and outlet reaches distinct.

This removes **3,833 preliminary pairs**. Most failed the 1 km start-distance rule; 510
removed pairs include an explicitly canal-sourced route, overlapping other reasons.
Pfaffenhofen an der Ilm demonstrates why proximity alone is insufficient: its selected
reach is only 0.29 km away but belongs to a different source basin.

Canada's Amos–Rouyn-Noranda lead fails because Rouyn-Noranda is **3.315759 km** from its
selected reach. Butte–Helena fails because Butte's offset is **1.123898 km**. Those illustrative
preliminary comparisons are not included in the source-checked feed. The 80 km proximity
limit and 1 km source-distance rule have not been relaxed.

These checks establish consistency with the recipe's source model. They do not independently
survey urban drains, diversions, dams, current river conditions or lake residence times.
The existing model and rough-travel-time caveats remain applicable.

## Local build and rotation

All seven region selections have generated ordinary and comparison feeds. The build contains
**45,918 numeric JSON files**. Every original town ID is preserved, internal verification
metadata is removed from the polling payloads, and every payload is within the **6,144-byte**
budget. The largest is **5,490 bytes**.

The comparison cycles are **21 days for Europe**, **9 days for the USA** and **30 days for
mixed Europe/USA or all regions** at 15 minutes per slot. Spare slots show ordinary journeys.
Canada currently shows ordinary journeys throughout its three-day comparison-feed cycle.
Each accepted pair occupies one stable slot per cycle; assignments survive subsequent
builds, and retired IDs retain their positions if later restored. No pair repeats within
72 hours. These initial capacities were chosen after source validation, before the first
publication; no existing published comparison plan was changed.

River-change metadata has also been generated for **all 8,348 ordinary journeys**. A town
can fail the stricter comparison rules and still retain its normal journey and source-backed
river labels. Vertices come from the original reaches and remain protected during map
simplification. Named river changes, starting towns and total estimated travel times remain
in the accepted layouts; there are no letter badges or sea callouts.

## Validation and review

- **149 pipeline tests pass**, with nine data/site-dependent tests skipped.
- A compressed regression fixture contains **1,027 real reaches and six real basin polygons**
  for five published towns. It verifies correct basins, the 1 km boundary, a nearby reach in
  the wrong basin, incomplete source coverage and ordinary labels for rejected comparisons.
- **37,360 actual-card cases pass**, spanning every accepted pair, both languages, both
  unit systems and four distinct Full frames. There are no truncated town/country, river,
  destination or travel lines in that check, including the formerly permitted long-town cases.
- **1,920 native Ruby Liquid layout/setting cases and 80 polling-URL cases pass**, covering
  opt-in values, regional selections, Full-only comparisons, independent labels and
  ordinary-journey fallbacks.
- **72 browser scenarios pass**, using the actual generated Stuttgart/Ulm and Radford/Roanoke
  packets plus Canada's ordinary Rouyn-Noranda fallback, against the real Framework and
  hosted maps. Six frames, both languages and both unit systems are covered for each packet.
  In eight Canadian portrait scenarios, the existing collision policy omits one crowded
  river-change callout; starting-town labels, complete cards, routes and attribution pass.
  Final EU landscape and US portrait screenshots were also visually reviewed.

Long unbroken place names exposed portrait clipping during the full-catalogue check. Paired
cards now select smaller existing Framework title sizes when needed; short titles retain
their original size. Normal-view title selection is unchanged. All previously accepted
layout/settings choices remain.

The feed is built under `data/site/`; nothing has been pushed, deployed or published. Publish
the data feed before activating the new polling URL on an installed recipe. Physical-device
review remains separate from the automated browser checks. See [implementation details](PAIR_FEED.md).
