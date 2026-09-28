"""River network: load reaches and follow NEXT_DOWN to the end of the path (BRIEF R5, R7)."""

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pyogrio
from shapely import STRtree
from shapely.geometry import Point


@dataclass
class Network:
    reaches: gpd.GeoDataFrame  # indexed by HYRIV_ID
    tree: STRtree

    @classmethod
    def load(cls, path: Path, bbox=None) -> "Network":
        df = pyogrio.read_dataframe(path, bbox=bbox).set_index("HYRIV_ID", drop=False)
        return cls(df, STRtree(df.geometry.values))

    def nearest(self, lon: float, lat: float) -> int:
        """HYRIV_ID of the reach nearest to the point (planar degrees; fine for picking a reach)."""
        i = self.tree.nearest(Point(lon, lat))
        return int(self.reaches.iloc[i]["HYRIV_ID"])

    def downstream(self, start: int) -> list[int]:
        """Reach IDs from start to the reach with NEXT_DOWN == 0, inclusive."""
        path, seen = [start], {start}
        nxt = int(self.reaches.at[start, "NEXT_DOWN"])
        while nxt:
            if nxt in seen:
                raise ValueError(f"loop in NEXT_DOWN at {nxt}")
            if nxt not in self.reaches.index:
                raise KeyError(f"reach {nxt} missing (outside loaded area?)")
            path.append(nxt)
            seen.add(nxt)
            nxt = int(self.reaches.at[nxt, "NEXT_DOWN"])
        return path
