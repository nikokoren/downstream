# Fixture sources

- `osm_starnberg.osm`: OpenStreetMap data, © OpenStreetMap contributors, available under the Open Database License (ODbL) 1.0, https://www.openstreetmap.org/copyright. Captured 2026-09-28 (OSM base 2026-09-28T20:16:58Z) from the Overpass API mirror at maps.mail.ru with the query `way["waterway"](47.98,11.30,48.02,11.36); (._;>;); out;` (Starnberg/Würm area). No user metadata.
- `osm_starnberg_lakes.osm`: same license and source. Captured 2026-09-28 (OSM base 2026-09-28T20:32:21Z) with `relation/way["natural"="water"]["water"="lake"](47.98,11.30,48.02,11.36); way["natural"="water"]["water"="reservoir"](47.90,11.20,48.10,11.45); (._;>;); out;`. Contains Starnberger See (relation 168892) and two unnamed reservoirs. No user metadata.
