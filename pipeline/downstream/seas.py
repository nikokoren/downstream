"""Which named sea does a river mouth drain into? (P4, R9)

Distance is measured through water, not in a straight line: on a 1 km grid of Natural Earth's
ocean polygon, grow outward from the mouth until a cell of a named sea or ocean is reached.
A straight line fails at Kiel: the nearest sea is the North Sea, 74.5 km away across Jutland
(found 2026-09-28).
"""

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import shapely

from downstream.naming import METRIC_CRS

CELL_M = 1000.0
HALF_WINDOW_M = 700_000.0  # search up to ~700 km of water around the mouth
NAMED_CLASSES = {"sea", "ocean"}


@dataclass
class Seas:
    ocean: shapely.Geometry  # METRIC_CRS
    seas: gpd.GeoDataFrame  # name, geometry (METRIC_CRS), featurecla in NAMED_CLASSES

    def drains_into(self, lon: float, lat: float) -> tuple[str | None, float | None]:
        """(sea name, water distance in km) or (None, None) if nothing named within the window."""
        mouth = gpd.GeoSeries([shapely.Point(lon, lat)], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
        x0, y0 = mouth.x - HALF_WINDOW_M, mouth.y - HALF_WINDOW_M
        n = int(2 * HALF_WINDOW_M / CELL_M)
        xs = x0 + (np.arange(n) + 0.5) * CELL_M
        ys = y0 + (np.arange(n) + 0.5) * CELL_M
        gx, gy = np.meshgrid(xs, ys)
        window = shapely.box(x0, y0, x0 + n * CELL_M, y0 + n * CELL_M)
        water = shapely.contains_xy(self.ocean.intersection(window), gx, gy)
        label = np.full((n, n), -1, dtype=np.int32)
        near = self.seas[self.seas.intersects(window)]
        for k, geom in enumerate(near.geometry):
            label[shapely.contains_xy(geom.intersection(window), gx, gy)] = k
        water |= label >= 0
        # Start from the water cells closest to the mouth (the mouth itself may sit on land).
        ci, cj = n // 2, n // 2
        wi, wj = np.nonzero(water)
        if len(wi) == 0:
            return None, None
        d2 = (wi - ci) ** 2 + (wj - cj) ** 2
        start = d2 <= d2.min() + 4
        reached = np.zeros_like(water)
        reached[wi[start], wj[start]] = True
        frontier = reached.copy()
        steps = int(np.sqrt(d2.min()))
        while frontier.any():
            hit = frontier & (label >= 0)
            if hit.any():
                ks, counts = np.unique(label[hit], return_counts=True)
                return str(near["name"].iloc[int(ks[counts.argmax()])]), round(
                    steps * CELL_M / 1000, 1
                )
            grow = np.zeros_like(frontier)
            grow[1:, :] |= frontier[:-1, :]
            grow[:-1, :] |= frontier[1:, :]
            grow[:, 1:] |= frontier[:, :-1]
            grow[:, :-1] |= frontier[:, 1:]
            frontier = grow & water & ~reached
            reached |= frontier
            steps += 1
        return None, None


def load_seas(ocean_zip, marine_zip, window=(-35.0, 25.0, 60.0, 75.0)) -> Seas:
    box = shapely.box(*window)
    ocean = gpd.read_file(f"zip://{ocean_zip}").clip(box).to_crs(METRIC_CRS).geometry.union_all()
    m = gpd.read_file(f"zip://{marine_zip}").clip(box)
    m.columns = [c.lower() if c != "geometry" else c for c in m.columns]
    m = m[m["featurecla"].str.lower().isin(NAMED_CLASSES) & m["name"].notna()]
    return Seas(ocean, m[["name", "geometry"]].to_crs(METRIC_CRS).reset_index(drop=True))
