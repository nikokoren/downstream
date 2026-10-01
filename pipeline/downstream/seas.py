"""Which named sea does a river mouth drain into? (P4, R9)

Distance is measured through water, not in a straight line: on a 1 km grid of Natural Earth's
ocean polygon, grow outward from the mouth until a cell of a named sea is reached. A straight
line fails at Kiel: the nearest sea is the North Sea, 74.5 km away across Jutland (2026-09-28).

The grid is drawn once for the whole window (2026-09-29: drawing it per mouth was 79 % of a
7,033-town run); each mouth then searches a 50 km window first and widens only if needed.

Named endpoints: Natural Earth marine areas of class sea, ocean, gulf, bay, channel, strait or
fjord with at least 15,000 km² (English Channel, Bay of Biscay, Gulf of Bothnia, Gulf of Finland,
Skagerrak, ... but not Mecklenburger Bucht, Øresund, Waddenzee or Stettiner Haff). With only
sea/ocean, Le Havre ended in the "North Sea" 312 km away and Boden in the "Baltic Sea" 690 km away.
"""

import geopandas as gpd
import numpy as np
import shapely

from downstream import regions
from downstream.naming import METRIC_CRS

CELL_M = 1000.0
WINDOW = regions.current().sea_window  # lon/lat; every mouth in the region plus open sea
NAMED_CLASSES = {"sea", "ocean", "gulf", "bay", "channel", "strait", "fjord"}
MIN_AREA_KM2 = 15_000
# Natural Earth's "Inner Seas" (IHO: Inner Seas off the West Coast of Scotland) also covers the
# Firth of Clyde and the Northern Irish coast: Glasgow, Belfast and Derry ended there (2026-09-29).
# Not shown as an endpoint; the search continues to the next named sea by water.
# "Saint Lawrence River" (class channel) is the river's estuary: 300 US towns "ended" in a river
# (2026-10-01); the search continues to the Gulf of Saint Lawrence.
SKIP_NAMES = {"Inner Seas", "Saint Lawrence River"}
GROW_CELLS = 2  # narrow estuaries (Seine, Scheldt, Szczecin Lagoon) break into pockets at 1 km
SEARCH_HALF_M = (50_000.0, 200_000.0, 800_000.0)


def _grow(mask: np.ndarray) -> np.ndarray:
    g = mask.copy()
    g[1:, :] |= mask[:-1, :]
    g[:-1, :] |= mask[1:, :]
    g[:, 1:] |= mask[:, :-1]
    g[:, :-1] |= mask[:, 1:]
    return g


class Seas:
    def __init__(self, ocean: shapely.Geometry, seas: gpd.GeoDataFrame) -> None:
        """ocean, seas in METRIC_CRS; seas: name, geometry, smallest first (small ones win)."""
        self.names = list(seas["name"])
        box = gpd.GeoSeries([shapely.box(*WINDOW)], crs="EPSG:4326").to_crs(METRIC_CRS)
        x0, y0, x1, y1 = box.total_bounds
        self.x0, self.y0 = x0, y0
        nx, ny = int((x1 - x0) // CELL_M), int((y1 - y0) // CELL_M)
        xs = x0 + (np.arange(nx) + 0.5) * CELL_M
        ys = y0 + (np.arange(ny) + 0.5) * CELL_M
        self.label = np.full((ny, nx), -1, dtype=np.int16)
        water = np.zeros((ny, nx), dtype=bool)
        for geom in [ocean, *seas.geometry]:
            shapely.prepare(geom)
        water |= self._raster(ocean, xs, ys)
        for k, geom in reversed(list(enumerate(seas.geometry))):  # smaller seas drawn last win
            m = self._raster(geom, xs, ys)
            self.label[m] = k
            water |= m
        for _ in range(GROW_CELLS):
            water = _grow(water)
        self.water = water

    @staticmethod
    def _raster(geom, xs, ys) -> np.ndarray:
        """Cells whose centre lies in geom, testing only rows/columns inside its bounds."""
        out = np.zeros((len(ys), len(xs)), dtype=bool)
        gx0, gy0, gx1, gy1 = geom.bounds
        ci = np.flatnonzero((xs >= gx0) & (xs <= gx1))
        ri = np.flatnonzero((ys >= gy0) & (ys <= gy1))
        if len(ci) == 0 or len(ri) == 0:
            return out
        gx, gy = np.meshgrid(xs[ci], ys[ri])
        out[np.ix_(ri, ci)] = shapely.contains_xy(geom, gx, gy)
        return out

    def drains_into(self, lon: float, lat: float) -> tuple[str | None, float | None]:
        """(sea name, water distance in km) or (None, None) if nothing named within ~800 km."""
        p = gpd.GeoSeries([shapely.Point(lon, lat)], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
        ci, cj = int((p.y - self.y0) // CELL_M), int((p.x - self.x0) // CELL_M)
        for half in SEARCH_HALF_M:
            h = int(half // CELL_M)
            r0, r1 = max(ci - h, 0), min(ci + h + 1, self.water.shape[0])
            c0, c1 = max(cj - h, 0), min(cj + h + 1, self.water.shape[1])
            found = self._search(
                self.water[r0:r1, c0:c1], self.label[r0:r1, c0:c1], ci - r0, cj - c0
            )
            if found:
                return found
        return None, None

    def _search(self, water, label, ci, cj):
        wi, wj = np.nonzero(water)
        if len(wi) == 0:
            return None
        d2 = (wi - ci) ** 2 + (wj - cj) ** 2
        start = d2 <= d2.min() + 4  # the mouth itself may sit on land
        reached = np.zeros_like(water)
        reached[wi[start], wj[start]] = True
        frontier = reached.copy()
        steps = int(np.sqrt(d2.min()))
        while frontier.any():
            hit = frontier & (label >= 0)
            if hit.any():
                ks, counts = np.unique(label[hit], return_counts=True)
                return self.names[int(ks[counts.argmax()])], round(steps * CELL_M / 1000, 1)
            frontier = _grow(frontier) & water & ~reached
            reached |= frontier
            steps += 1
        return None


def load_seas(ocean_zip, marine_zip) -> Seas:
    box = shapely.box(*WINDOW)
    ocean = gpd.read_file(f"zip://{ocean_zip}").clip(box).to_crs(METRIC_CRS)
    ocean = ocean.geometry.make_valid().union_all()
    m = gpd.read_file(f"zip://{marine_zip}").clip(box)
    m.columns = [c.lower() if c != "geometry" else c for c in m.columns]
    m = m[m["featurecla"].str.lower().isin(NAMED_CLASSES) & m["name"].notna()].to_crs(METRIC_CRS)
    m["geometry"] = m.geometry.make_valid()
    m = m[(m.area / 1e6 >= MIN_AREA_KM2) & ~m["name"].isin(SKIP_NAMES)].copy()
    m["km2"] = m.area / 1e6
    m = m.sort_values("km2").reset_index(drop=True)
    return Seas(ocean, m[["name", "geometry"]])
