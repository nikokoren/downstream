"""The published name table (D10, ODbL): the name of every named river segment in the network.

It holds names taken from OpenStreetMap, so it's a Derivative Database under the ODbL and is
published with its notice (ODbL 4.2, 4.6). Since the per-river redesign (2026-09-29) each
segment has exactly one name, whichever town's path reaches it.
"""

import csv
from pathlib import Path

from downstream.naming import is_lake, lookup_curated

COLUMNS = ["hyriv_id", "kind", "name", "source", "display_en", "display_de"]

NOTICE = """# Downstream name table

`name_table.csv` lists every river segment Downstream has a name for, with that name.

- `hyriv_id`: river segment ID from HydroATLAS / RiverATLAS v1.0 (CC BY 4.0; Linke et al. 2019,
  https://doi.org/10.1038/s41597-019-0300-6).
- `kind`: `river` or `lake`.
- `name`: the segment's name as spelled in the source, after clean-up along its river (short
  blips take the surrounding name; delta arms take the river's main name).
- `source`: where that name came from: `osm`, `osm:canal`, `naturalearth`, `lake:osm` or
  `lake:naturalearth`.
- `display_en`, `display_de`: Downstream's curated display names, where it has one.

Contains information from OpenStreetMap (https://www.openstreetmap.org/copyright), which is made
available here under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ . © OpenStreetMap contributors.
This table is itself licensed under the ODbL 1.0. Names from Natural Earth are public domain.

Made by `pipeline/downstream/build_names.py` in https://github.com/nikokoren/downstream (the method is
public too: ODbL 4.6b). Build: {build}.
"""


class NameTable:
    def __init__(self) -> None:
        self.rows: set[tuple] = set()

    def add(self, reach_ids, labels, curated: dict) -> None:
        for rid, (name, src) in zip(reach_ids, labels, strict=True):
            if not name:
                continue
            disp = lookup_curated(name, curated) or {}
            kind = "lake" if is_lake((name, src)) else "river"
            self.rows.add((int(rid), kind, name, src, disp.get("en", ""), disp.get("de", "")))

    def write(self, out_dir: Path, build: str) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "name_table.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(COLUMNS)
            w.writerows(sorted(self.rows))
        (out_dir / "NOTICE.md").write_text(NOTICE.format(build=build), encoding="utf-8")
        return path
