# Drainage-divide search at 80 km — 13 November 2026

**Source checks are now complete:** 1,705 European and 630 US pairs pass, 2,335 total;
Canada's one preliminary pair fails the start-distance rule. The local feed is built.
See [the completed verification report](PAIR_VERIFICATION.md) and
[source-checked CSV](../fixtures/review/source-checked-pairs.csv). The 6,168 figures below
record the broader discovery pass, before original-source verification.

Access to the published model data now works. All **8,348 unique towns in the published
Europe, USA and Canada rotations** were captured successfully, with no failed downloads.
The search uses those town packets and their stored coordinates, river chains, endpoints,
route geometry and travel estimates. It does not add towns from a larger GeoNames list or
change the recipe's town classification.

The full derived [candidate CSV](../fixtures/review/drainage-divide-candidates.csv) contains
**6,168 pairs**. It includes each town's GeoNames ID, intermediate rivers, destination,
distance, estimated travel-time range in both languages, and the outstanding review status.
These are model-based candidates, not an approved or activated catalogue.

| Region | Eligible towns searched | At 50 km | At 80 km | Added |
|---|---:|---:|---:|---:|
| Europe | 5,280 | 424 | **1,720** | **1,296** |
| USA | 2,816 | 2,205 | **4,447** | **2,242** |
| Canada | 252 | 0 | **1** | **1** |
| Mixed | 8,348 | 2,629 | **6,168** | **3,539** |

Every candidate from the 50 km search is retained. Only town-to-town proximity was widened,
at the author's request, for all three regions. The same eligible town packets were reused.
Both the search function and CLI now default to 80 km.

At 15 minutes per screen, the candidate cycles would span **17 days, 22 hours in Europe**,
**46 days, 7 hours, 45 minutes in the USA**, and **64 days, 6 hours mixed**, if all candidates
pass the remaining review. Canada's one comparison occupies one slot in a 72-hour plan,
with 287 normal single-town slots between repetitions.

## What the discovery numbers mean

The geographic rules are now **at most 80 km between town points**, **at least 100 km for
each route**, and **different receiver groups**. Final town distances use the WGS84 ellipsoid.
Nested marine labels are grouped for discovery; cards keep the actual named destination.
No US–Canada cross-border pair meets these rules.

Europe has 2,779 geographic candidates before the start-distance check. The matching European
build-report rows supply that measurement and reduce the pool to **1,720**. All 5,261
sea-ending model towns join by exact GeoNames ID and agree with the report's country,
distance, chain and endpoint. Both starting-reach offsets are known and ≤1 km for every
European candidate. The earlier full-model pass at 50 km had recovered 27 previously missing
coordinates and added seven pairs to the original 417; all 424 remain in the expanded pool.

The published North American packets omit the town-to-start-reach distance. The discovery
search retained **4,447 US leads and one Canadian lead** with that field explicitly unknown.
Subsequent original-source measurements applied the same ≤1 km check; unknown was never
treated as a verified pass. The completed verification report records the resulting subset.
One European candidate, **Weißenburg in Bayern–Pfaffenhofen an der Ilm, 68.0 km**, uses a
`nearest overall` starting-reach fallback and is explicitly flagged for basin review.

Pair count also differs from geographic variety. The European candidates use **563 distinct
towns**, the US candidates use **351**, and Canada contributes two. Of the US candidates,
4,446 contrast the Gulf of Mexico with an Atlantic receiver, including the Great Lakes/St.
Lawrence route. **Butte–Helena** adds a Pacific/Gulf of Mexico comparison. Many are different
town combinations around the same divides. A distance-first sample with no repeated towns
and at least 75 km between pair midpoints gives **30 European, 19 US and one Canadian example**. That is
a review sample, not a catalogue cap or a count of independent watersheds. Rotation should
continue spreading towns, areas and river systems rather than simply sorting by proximity.

## Examples from the actual model packets

These demonstrate the preliminary search results, before route/basin and screen review.
Some examples, including Butte–Helena and Amos–Rouyn-Noranda, were later excluded.

| Town | Model destination | Neighbour | Model destination | Apart |
|---|---|---|---|---:|
| Balingen, Germany | North Sea | Albstadt, Germany | Black Sea | 14.3 km |
| Neuchâtel, Switzerland | North Sea | La Chaux-de-Fonds, Switzerland | Gulf of Lion | 14.4 km |
| Heidenheim, Germany | Black Sea | Aalen, Germany | North Sea | 18.3 km |
| Akron, USA | Gulf of Saint Lawrence | Barberton, USA | Gulf of Mexico | 10.5 km |
| Blacksburg, USA | Gulf of Mexico | Salem, USA | North Atlantic Ocean | 32.6 km |
| Boone, USA | Gulf of Mexico | Lenoir, USA | North Atlantic Ocean | 35.7 km |
| Fort Wayne, USA | Gulf of Saint Lawrence | Huntington, USA | Gulf of Mexico | 41.4 km |
| Altoona, USA | North Atlantic Ocean | Johnstown, USA | Gulf of Mexico | 49.6 km |
| Stuttgart, Germany | North Sea | Ulm, Germany | Black Sea | 73.7 km |
| Linz, Austria | Black Sea | České Budějovice, Czechia | North Sea | 75.6 km |
| Butte, USA | North Pacific Ocean | Helena, USA | Gulf of Mexico | 75.9 km |
| Amos, Canada | James Bay | Rouyn-Noranda, Canada | Gulf of Saint Lawrence | 76.5 km |

The Canadian discovery lead was **Amos–Rouyn-Noranda, 76.5 km** (James Bay/St. Lawrence).
It subsequently failed the 1 km source-distance rule and is absent from the local paired feed.
The next pair is
**Rouyn-Noranda–Val-d'Or, 92.5 km**, which remains outside the active limit. The existing
sparse-region plan uses normal town screens when the comparison pool is too small for the
72-hour repeat interval.

## Discovery checks and subsequent verification

All **8,348 captured packets** passed source-hash verification, finite/in-range town and
decoded route coordinates, complete encoded geometry, nonempty intermediate steps with
positive lengths, positive total distance and travel duration, and English/German place,
destination, travel and metric/imperial distance display fields. All **6,168 retained pairs**
pass those packet checks; one European pair has the starting-reach fallback noted above. These checks
establish that the downloaded model journeys are complete enough for further review.

These discovery checks did not independently establish the hydrology. Subsequent original-source
verification checked town points and routed reaches against BasinATLAS, measured missing start
offsets and excluded explicit canal routes. The local feed build also exports river-change
coordinates, preserves stable pair slots and enforces the payload budget. Full-catalogue card
checks and representative browser scenarios now pass. These remain model checks rather than
a physical survey of drains, diversions or current conditions. See
[the completed verification](PAIR_VERIFICATION.md) and [implementation](PAIR_FEED.md). No code, environment
or recipe was published during this work.

## Sources and local outputs

Source rotations, fetched 13 November 2026:

- https://nikokoren.github.io/downstream/eu/rotation.csv
- https://nikokoren.github.io/downstream/us/rotation.csv
- https://nikokoren.github.io/downstream/ca/rotation.csv

For each unique GeoNames ID, the associated `n` slot supplies the packet at
`https://nikokoren.github.io/downstream/<region>/t/<n>.json`. Each packet's stored ID was
checked against the rotation. The full ignored capture at `data/captured-site/2026-11-13/`
contains the original rotations and packets plus a per-file URL/SHA256 manifest. Generated
candidate JSONs, regional CSVs, review samples and review-only rotation plans are under
`data/pair-candidates/2026-11-13/80km/{eu,us,ca,mix}/`. The previous 50 km outputs are retained
in the parent directory for comparison.

The retained [audit summary](../fixtures/review/pair-audit.json) records rotation hashes,
capture time, thresholds, regional coverage, packet-check results, the full-manifest hash,
the European report hash and the derived CSV hash. The European report source is
https://github.com/nikokoren/downstream/releases/download/build-report/towns.csv .
Attribution and licences are in [the fixture notice](../fixtures/review/NOTICE.md).
