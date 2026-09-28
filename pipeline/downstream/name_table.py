"""The published name table (D10, ODbL): which name each river segment on a computed path got.

It holds names taken from OpenStreetMap, so it's a Derivative Database under the ODbL and is
published with its notice (ODbL 4.2, 4.6). One row per (segment, name, source); a segment can
carry different names on different paths when context-dependent clean-up differs.
"""

import csv
from pathlib import Path

from downstream.naming import is_lake, lookup_curated

COLUMNS = ["hyriv_id", "kind", "name", "source", "display_en", "display_de"]

NOTICE = """# Downstream name table

`name_table.csv` lists, for each river segment on the paths computed by Downstream, the name the
pipeline gave it.

- `hyriv_id`: river segment ID from HydroATLAS / RiverATLAS v1.0 (CC BY 4.0; Linke et al. 2019,
  https://doi.org/10.1038/s41597-019-0300-6).
- `kind`: `river` or `lake`.
- `name`: the name Downstream used for the segment on a path, as spelled in the source, after
  clean-up (short blips, side arms and delta arms take the surrounding river's name). A segment
  can appear with several names when paths reach it from different rivers.
- `source`: where that name came from: `osm`, `osm:canal`, `naturalearth`, `lake:osm` or
  `lake:naturalearth`.
- `display_en`, `display_de`: Downstream's curated display names, where it has one.

Contains information from OpenStreetMap (https://www.openstreetmap.org/copyright), which is made
available here under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ . © OpenStreetMap contributors.
This table is itself licensed under the ODbL 1.0. Names from Natural Earth are public domain.

Made by `pipeline/downstream/paths.py` in https://github.com/nikokoren/downstream (the method is
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
