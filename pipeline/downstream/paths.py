"""Compute the path for example towns and write one JSON per town plus a GeoJSON for checking.

Usage: uv run python -m downstream.paths   (after downstream.build_names)
"""

import json

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely
from shapely import STRtree

from downstream import naming, towns
from downstream.endpoints import classify, load_ne
from downstream.fetch import RAW
from downstream.network import Network
from downstream.seas import load_seas

OUT = RAW.parent / "paths"

# Acceptance and example towns (R20, D9): (name, country code) looked up in cities15000.
EXAMPLES = [
    ("Munich", "DE"),
    ("Starnberg", "DE"),
    ("Garmisch-Partenkirchen", "DE"),
    ("Nuremberg", "DE"),
    ("Köln", "DE"),
    ("Vienna", "AT"),
    # Added 2026-09-28 with the Austria + Germany OSM extracts: Elbe, Baltic, Inn, Mur, Neckar.
    ("Hamburg", "DE"),
    ("Berlin", "DE"),
    ("Leipzig", "DE"),
    ("Kiel", "DE"),
    ("Stuttgart", "DE"),
    ("Innsbruck", "AT"),
    ("Salzburg", "AT"),
    ("Graz", "AT"),
]


def start_reach(
    net: Network, basins: gpd.GeoDataFrame, btree: STRtree, lon, lat
) -> tuple[int, str]:
    """R4: nearest reach inside the level-12 sub-basin containing the point, else nearest overall."""
    pt = shapely.Point(lon, lat)
    hit = btree.query(pt, predicate="within")
    if len(hit):
        basin_id = int(basins.iloc[hit[0]]["HYBAS_ID"])
        inside = net.reaches[net.reaches["HYBAS_L12"] == basin_id]
        if len(inside):
            m = inside.to_crs(naming.METRIC_CRS)
            p = gpd.GeoSeries([pt], crs="EPSG:4326").to_crs(naming.METRIC_CRS).iloc[0]
            i = m.geometry.distance(p).idxmin()
            return int(i), f"sub-basin {basin_id}"
    return net.nearest(lon, lat), "nearest overall"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    net = Network.load(RAW / "reaches_eu.fgb")
    basins = pyogrio.read_dataframe(RAW / "basins_l12_europe.fgb")
    btree = STRtree(basins.geometry.values)

    # Names come from the network-wide table (downstream.build_names): same name for a reach
    # whichever town's path reaches it.
    names_csv = RAW.parent / "names" / "reach_names.csv"
    reach_label = {
        int(r.HYRIV_ID): (
            r.name if isinstance(r.name, str) else None,
            r.source if isinstance(r.source, str) else None,
        )
        for r in pd.read_csv(names_csv, usecols=["HYRIV_ID", "name", "source"]).itertuples()
    }
    curated = naming.load_curated()
    seas = load_seas(RAW / "ne_ocean.zip", RAW / "ne_marine.zip")
    lakes = load_ne(RAW / "ne_lakes.zip")

    cities = towns.load_cities(RAW / "geonames_cities15000.zip")
    wanted = {gid: c for gid, c in cities.items() if (c["name"], c["cc"]) in EXAMPLES}
    alts = towns.load_alt_names(RAW / "geonames_alt_de_en.txt", set(wanted))

    features = []
    for gid, c in sorted(wanted.items(), key=lambda kv: -int(kv[1]["pop"])):
        lon, lat = float(c["lon"]), float(c["lat"])
        start, how = start_reach(net, basins, btree, lon, lat)
        ids = net.downstream(start)
        reaches = net.reaches.loc[ids]
        names = [reach_label.get(int(i), (None, None)) for i in ids]
        groups = naming.chain(reaches, names, curated)
        first, last = reaches.iloc[0], reaches.iloc[-1]
        end = classify(last.geometry.coords[-1], bool(last["ENDORHEIC"]), seas, lakes)
        end_disp = curated.get(end["name"]) if end["name"] else None
        line = shapely.line_merge(shapely.MultiLineString(list(reaches.geometry.values)))
        simple = simplify_to(line, MAX_MAP_POINTS)
        result = {
            "town": {
                "geonameid": gid,
                "en": towns.pick_name(c, alts.get(gid, {}), "en"),
                "de": towns.pick_name(c, alts.get(gid, {}), "de"),
                "lon": lon,
                "lat": lat,
                "population": int(c["pop"]),
            },
            "start": {"reach": start, "how": how},
            "reaches": len(ids),
            "total_km": round(float(first["DIST_DN_KM"] + first["LENGTH_KM"]), 1),
            "chain": [
                {k: g[k] for k in ("kind", "name", "source", "km", "reaches")} for g in groups
            ],
            "end": {**end, "display": end_disp},
            "path": [[round(x, 3), round(y, 3)] for x, y in shapely.get_coordinates(simple)],
        }
        slug = result["town"]["en"].lower().replace(" ", "-")
        (OUT / f"{slug}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        size = len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode())
        features.append(
            {
                "type": "Feature",
                "properties": {"town": slug},
                "geometry": shapely.geometry.mapping(line),
            }
        )
        chain_txt = " → ".join(
            (g["name"] or {}).get("en") or (g["name"] or {}).get("local") or "(unnamed)"
            for g in groups
        )
        print(
            f"{result['town']['en']} / {result['town']['de']}: start {start} ({how}); "
            f"{len(ids)} reaches, {result['total_km']} km; end {end['type']} "
            f"{end['name']} ({end['distance_km']} km); {len(result['path'])} map points, "
            f"{size} bytes compact\n   {chain_txt}"
        )
    (OUT / "paths.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )


MAX_MAP_POINTS = 120  # keeps the payload under R3's ~6 KB; revisit with the TRMNL design


def simplify_to(line, max_points: int):
    tol = 0.002
    simple = line.simplify(tol, preserve_topology=False)
    while len(shapely.get_coordinates(simple)) > max_points:
        tol *= 1.5
        simple = line.simplify(tol, preserve_topology=False)
    return simple


def pd_concat(frames):
    import pandas as pd

    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)


if __name__ == "__main__":
    main()
