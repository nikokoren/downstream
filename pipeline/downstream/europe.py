"""The Europe border for the town list (D9, author 2026-09-28; boundary defaults accepted).

A town is in Europe when (1) its country is allowed and (2) its point lies inside the Europe
outline, buffered 5 km so coastal towns aren't lost to Natural Earth's generalized coast.
Checking the country first keeps the buffer from pulling in towns across a border (e.g. Sovetsk,
Russia, on the Lithuanian border).

Countries: Natural Earth admin-0 v5 `CONTINENT == "Europe"` (51 countries), minus Russia
(all of it, including Kaliningrad), plus European Turkey. Natural Earth already lists Cyprus,
Georgia, Armenia, Azerbaijan and Kazakhstan under Asia and Greenland under North America.

Outline: those countries' polygon parts, minus parts that aren't geographically European:
- the Canary Islands and Madeira (part centroid south of 34 N),
- the Azores (west of 24.9 W),
- Svalbard (north of 74 N) and Jan Mayen (north of 70 N and west of 5 W),
- Ceuta, Melilla and nearby Spanish islets in Africa (south of 36 N, between 6 W and 2 W),
- anything outside 25 W-45 E / 34-72 N (French overseas departments etc.);
plus Turkey only west of the Bosporus, Sea of Marmara and Dardanelles (THRACE below);
plus Crimea. Natural Earth draws Crimea inside Russia's polygon; GeoNames lists its towns as
Ukraine (UA), which matches UN recognition, so the outline includes the peninsula and the
country check decides (UA towns in, RU towns out). Found 2026-09-28: without this, 16 Crimean
towns (Sevastopol, Simferopol, Yalta, ...) were dropped.
"""

import geopandas as gpd
import shapely

from downstream.naming import METRIC_CRS

WINDOW = (-25.0, 34.0, 45.0, 72.0)
BUFFER_M = 5000.0

# West/north of a line down the middle of the Bosporus, across the Sea of Marmara and down the
# Dardanelles (lon, lat). Everything in Turkey inside this polygon is European Turkey.
CRIMEA_BOX = shapely.box(32.4, 44.3, 36.66, 46.25)

THRACE = shapely.Polygon(
    [
        (25.5, 42.3),
        (29.4, 41.6),
        (29.12, 41.23),
        (29.07, 41.13),
        (29.035, 41.06),
        (29.005, 41.02),
        (28.99, 40.97),
        (26.68, 40.375),  # Dardanelles between Gelibolu (Europe) and Lapseki (Asia)
        (26.39, 40.15),  # between Kilitbahir (Europe) and Çanakkale (Asia), ~1.3 km wide
        (26.20, 40.03),
        (25.5, 40.0),
    ]
)


def _keep_part(part) -> bool:
    c = part.centroid
    x, y = c.x, c.y
    if not (WINDOW[0] <= x <= WINDOW[2] and WINDOW[1] <= y <= WINDOW[3]):
        return False
    if y > 74 or (y > 70 and x < -5):  # Svalbard, Jan Mayen
        return False
    if x < -24.9:  # Azores
        return False
    # Ceuta, Melilla, Alboran and nearby islets
    return not (y < 36.0 and -6.0 < x < -2.0)


class Europe:
    def __init__(self, admin0_zip) -> None:
        g = gpd.read_file(f"zip://{admin0_zip}")
        eu = g[(g["CONTINENT"] == "Europe") & (g["ISO_A2_EH"] != "RU")]
        self.countries = set(eu["ISO_A2_EH"]) | {"TR"}
        parts = [p for geom in eu.geometry for p in getattr(geom, "geoms", [geom]) if _keep_part(p)]
        turkey = g[g["ISO_A2_EH"] == "TR"].geometry.union_all().intersection(THRACE)
        crimea = g[g["ISO_A2_EH"] == "RU"].geometry.union_all().intersection(CRIMEA_BOX)
        outline = shapely.union_all([*parts, turkey, crimea])
        self.outline = outline  # EPSG:4326, for inspection
        m = gpd.GeoSeries([outline], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
        self._metric = m.buffer(BUFFER_M)
        shapely.prepare(self._metric)

    def contains(self, towns: gpd.GeoDataFrame) -> "gpd.pd.Series":
        """towns: columns cc, geometry (EPSG:4326). European Turkey uses THRACE without buffer."""
        cc_ok = towns["cc"].isin(self.countries)
        pts = towns.to_crs(METRIC_CRS).geometry.values
        inside = shapely.contains(self._metric, pts)
        tr = towns["cc"] == "TR"
        thrace = shapely.contains(THRACE, towns.geometry.values)
        return cc_ok & ((~tr & inside) | (tr & thrace))
