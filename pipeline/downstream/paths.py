"""Compute the path for example towns and write one JSON per town plus a GeoJSON for checking.

Usage: uv run python -m downstream.paths   (after downstream.build_names)
"""

import argparse
import json
import time

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


class Context:
    """Everything a town lookup needs, loaded once."""

    def __init__(self) -> None:
        self.net = Network.load(RAW / "reaches_eu.fgb")
        self.basins = pyogrio.read_dataframe(RAW / "basins_l12_europe.fgb")
        self.btree = STRtree(self.basins.geometry.values)
        # Names come from the network-wide table (downstream.build_names): same name for a
        # reach whichever town's path reaches it.
        names_csv = RAW.parent / "names" / "reach_names.csv"
        self.reach_label = {
            int(r.HYRIV_ID): (
                r.name if isinstance(r.name, str) else None,
                r.source if isinstance(r.source, str) else None,
            )
            for r in pd.read_csv(names_csv, usecols=["HYRIV_ID", "name", "source"]).itertuples()
        }
        self.curated = naming.load_curated()
        self.seas = load_seas(RAW / "ne_ocean.zip", RAW / "ne_marine.zip")
        self.lakes = load_ne(RAW / "ne_lakes.zip")
        self._ends: dict[int, dict] = {}  # outlet reach -> endpoint (many towns share one)

    def end_of(self, last) -> dict:
        rid = int(last["HYRIV_ID"])
        if rid not in self._ends:
            self._ends[rid] = classify(
                last.geometry.coords[-1], bool(last["ENDORHEIC"]), self.seas, self.lakes
            )
        return self._ends[rid]


def compute_town(
    ctx: Context, gid: str, c: dict, alts: dict
) -> tuple[dict, shapely.Geometry, dict]:
    """(result JSON, full path line, stats for the report)."""
    lon, lat = float(c["lon"]), float(c["lat"])
    start, how = start_reach(ctx.net, ctx.basins, ctx.btree, lon, lat)
    ids = ctx.net.downstream(start)
    reaches = ctx.net.reaches.loc[ids]
    names = [ctx.reach_label.get(int(i), (None, None)) for i in ids]
    groups = naming.chain(reaches, names, ctx.curated)
    first, last = reaches.iloc[0], reaches.iloc[-1]
    end = ctx.end_of(last)
    if end["type"] != "sea" and groups[-1]["kind"] == "lake":
        # The path ends in a named lake (Limni Vegoritis, Limni Ioanninon): that's the endpoint.
        lake = groups[-1]["name"] or {}
        end = {
            "type": "lake",
            "name": lake.get("en") or lake.get("local"),
            "featurecla": "Lake",
            "distance_km": 0.0,
        }
    end_disp = naming.lookup_curated(end["name"], ctx.curated) if end["name"] else None
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
        "chain": [{k: g[k] for k in ("kind", "name", "source", "km", "reaches")} for g in groups],
        "end": {**end, "display": end_disp},
        "path": [[round(x, 3), round(y, 3)] for x, y in shapely.get_coordinates(simple)],
    }
    km = reaches["LENGTH_KM"].to_numpy(dtype=float)
    src = [s or "" for _, s in names]
    town_m = gpd.GeoSeries([shapely.Point(lon, lat)], crs="EPSG:4326").to_crs(naming.METRIC_CRS)
    start_m = gpd.GeoSeries([reaches.geometry.iloc[0]], crs="EPSG:4326").to_crs(naming.METRIC_CRS)
    stats = {
        "start_dist_km": round(float(town_m.iloc[0].distance(start_m.iloc[0])) / 1000, 2),
        "named_share": round(float(km[[bool(s) for s in src]].sum() / km.sum()), 3),
        "osm_share": round(
            float(km[[s.startswith(("osm", "lake:osm")) for s in src]].sum() / km.sum()), 3
        ),
        "first_unnamed": groups[0]["name"] is None,
        "steps": len(groups),
        "payload_bytes": len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()
        ),
    }
    return result, line, stats


def chain_text(result: dict) -> str:
    return " → ".join(
        (g["name"] or {}).get("en") or (g["name"] or {}).get("local") or "(stream)"
        for g in result["chain"]
    )


def main_examples() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = Context()
    cities = towns.load_cities(RAW / "geonames_cities15000.zip")
    wanted = {gid: c for gid, c in cities.items() if (c["name"], c["cc"]) in EXAMPLES}
    alts = towns.load_alt_names(RAW / "geonames_alt_de_en.txt", set(wanted))
    features = []
    for gid, c in sorted(wanted.items(), key=lambda kv: -int(kv[1]["pop"])):
        result, line, stats = compute_town(ctx, gid, c, alts)
        slug = result["town"]["en"].lower().replace(" ", "-")
        (OUT / f"{slug}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        features.append(
            {
                "type": "Feature",
                "properties": {"town": slug},
                "geometry": shapely.geometry.mapping(line),
            }
        )
        end = result["end"]
        print(
            f"{result['town']['en']} / {result['town']['de']}: start {result['start']['reach']} "
            f"({result['start']['how']}); {result['reaches']} reaches, {result['total_km']} km; "
            f"end {end['type']} {end['name']} ({end['distance_km']} km); "
            f"{len(result['path'])} map points, {stats['payload_bytes']} bytes compact\n"
            f"   {chain_text(result)}"
        )
    (OUT / "paths.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )


# Towns whose first river segment is further than this from the town point are left out of the
# rotation (author, 2026-09-29; BRIEF R9 "no reach found nearby", D8). 130 of 7,033 towns on the
# first full run, up to 30 km (Den Helder, Gibraltar, Kos, Badalona, ...).
MAX_START_KM = 5.0


def main_all() -> None:
    """Every Europe town (D9): one JSON per town in ../data/towns/, and the build report (P7)."""
    from downstream import report

    out = RAW.parent / "towns"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):  # no stale files for towns that are now excluded
        old.unlink()
    t0 = time.time()
    ctx = Context()
    eu = towns.europe_towns(RAW)
    cities = {r["geonameid"]: r for r in eu.drop(columns="geometry").to_dict("records")}
    alts = towns.load_alt_names(RAW / "geonames_alt_de_en.txt", set(cities))
    print(f"{len(cities)} towns; loaded in {time.time() - t0:.0f}s", flush=True)
    rows = []
    for k, (gid, c) in enumerate(cities.items(), 1):
        row = {"geonameid": gid, "name": c["name"], "cc": c["cc"], "population": int(c["pop"])}
        try:
            result, _, stats = compute_town(ctx, gid, c, alts)
            excluded = stats["start_dist_km"] > MAX_START_KM
            if not excluded:
                (out / f"{gid}.json").write_text(
                    json.dumps(result, ensure_ascii=False, separators=(",", ":"))
                )
            row |= {
                "en": result["town"]["en"],
                "de": result["town"]["de"],
                "total_km": result["total_km"],
                "end_type": result["end"]["type"],
                "end_name": result["end"]["name"],
                "chain": chain_text(result),
                **stats,
                "excluded": "start far from town" if excluded else "",
                "error": "",
            }
        except Exception as e:  # noqa: BLE001 - recorded in the report, not fatal
            row["error"] = f"{type(e).__name__}: {e}"
        rows.append(row)
        if k % 500 == 0:
            print(f"  {k}/{len(cities)} towns, {time.time() - t0:.0f}s", flush=True)
    report.write(pd.DataFrame(rows), RAW.parent / "report", time.time() - t0)


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="every Europe town + build report")
    main_all() if ap.parse_args().all else main_examples()
