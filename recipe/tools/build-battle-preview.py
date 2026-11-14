"""Build review-only geographic fixtures from captured, attributed source geometry.

The production Pages host may be unavailable in the review environment. In that case Nürnberg
uses a reference route along real OSM / Natural Earth river lines, not a claimed reconstruction
of the HydroATLAS model. Munich keeps the committed model polyline. Nothing is published.
Run with pipeline/.venv/bin/python from the repository root.
"""

import hashlib
import heapq
import json
import math
from itertools import pairwise
from pathlib import Path

import pyogrio
import shapely
from pyproj import Geod
from shapely.geometry import LineString, Point, shape
from shapely.ops import nearest_points

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/review"
OUT = ROOT / "recipe/tools/out/battle"
GEOD = Geod(ellps="WGS84")


def metres(a, b):
    return GEOD.inv(a[0], a[1], b[0], b[1])[2]


def parts(geom):
    return list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]


def reference_path(lines, start, end):
    """Shortest connected section of the named source river, preserving its sampled geometry."""
    graph = {}
    xy = {}

    def node(c):
        k = (round(c[0], 6), round(c[1], 6))
        xy[k] = list(c[:2])
        graph.setdefault(k, {})
        return k

    def edge(a, b):
        if a == b:
            return
        cost = metres(xy[a], xy[b])
        graph[a][b] = cost
        graph[b][a] = cost

    segments = []
    for line in lines:
        cs = list(line.coords)
        for a, b in pairwise(cs):
            ka, kb = node(a), node(b)
            edge(ka, kb)
            segments.append((ka, kb))
    # Attach at a point on a source segment, rather than jumping to a coarse nearby vertex.
    seg_geoms = [LineString([xy[a], xy[b]]) for a, b in segments]
    tree = shapely.STRtree(seg_geoms)

    def attach(c):
        i = int(tree.nearest(Point(c)))
        p = nearest_points(Point(c), seg_geoms[i])[1]
        k = node(p.coords[0])
        a, b = segments[i]
        edge(k, a)
        edge(k, b)
        return k

    a, b = attach(start), attach(end)
    # Natural Earth splits a river into cartographic parts. Join only short end-point gaps,
    # and record them in the fixture so this cannot be mistaken for model-exact geometry.
    endpoints = [k for k, links in graph.items() if len(links) == 1]
    joins = []
    for i, p in enumerate(endpoints):
        for q in endpoints[i + 1:]:
            d = metres(xy[p], xy[q])
            if d <= 500:
                edge(p, q)
                joins.append(round(d, 1))
    queue = [(0.0, a)]
    costs, previous = {a: 0.0}, {}
    while queue:
        cost, here = heapq.heappop(queue)
        if cost != costs[here]:
            continue
        if here == b:
            break
        for there, length in graph[here].items():
            nc = cost + length
            if nc < costs.get(there, math.inf):
                costs[there] = nc
                previous[there] = here
                heapq.heappush(queue, (nc, there))
    if b not in costs:
        raise ValueError("named reference river is disconnected; do not invent a route")
    route = [b]
    while route[-1] != a:
        route.append(previous[route[-1]])
    return [xy[k] for k in reversed(route)], joins


def main():
    osm_file = ROOT / "data/raw/osm/waterways-europe-germany-bayern.fgb"
    osm = pyogrio.read_dataframe(osm_file, where="name IN ('Pegnitz','Regnitz','Main','Isar','Donau')")
    osm_lines = {n: list(osm[osm["name"] == n].geometry) for n in ("Pegnitz", "Regnitz", "Main", "Isar", "Donau")}
    regnitz_arms = pyogrio.read_dataframe(osm_file, where="name IN ('Linker Regnitzarm','Rechter Regnitzarm')")

    def junction(a, b):
        av = {tuple(c[:2]) for g in osm_lines[a] for c in g.coords}
        bv = {tuple(c[:2]) for g in osm_lines[b] for c in g.coords}
        common = sorted(av & bv)
        if len(common) != 1:
            raise ValueError(f"ambiguous real confluence: {a} / {b}: {len(common)} points")
        return list(common[0])

    pegnitz_regnitz = junction("Pegnitz", "Regnitz")
    regnitz_main = junction("Regnitz", "Main")
    isar_danube = junction("Isar", "Donau")
    ne_file = RAW / "ne_10m_rivers_lake_centerlines.geojson"
    rivers = json.loads(ne_file.read_text())["features"]
    ne_lines = {n: [part for f in rivers if f["properties"].get("name") == n for part in parts(shape(f["geometry"]))] for n in ("Main", "Rhine", "Nederrijn", "Lek")}
    main_rhine = list(nearest_points(shapely.union_all(ne_lines["Main"]), shapely.union_all(ne_lines["Rhine"]))[0].coords[0])
    rhine_nederrijn = list(nearest_points(shapely.union_all(ne_lines["Rhine"]), shapely.union_all(ne_lines["Nederrijn"]))[0].coords[0])
    nederrijn_lek = list(nearest_points(shapely.union_all(ne_lines["Nederrijn"]), shapely.union_all(ne_lines["Lek"]))[0].coords[0])
    sea = min((list(c[:2]) for g in ne_lines["Lek"] for c in g.coords), key=lambda c: c[0])
    places_file = RAW / "ne_10m_populated_places_simple.geojson"
    city = next(f for f in json.loads(places_file.read_text())["features"] if f["properties"].get("name") == "Nürnberg")
    origin = city["geometry"]["coordinates"][:2]
    chunks, gaps = [], []
    for name, lines, a, b in [
        ("Pegnitz", osm_lines["Pegnitz"], origin, pegnitz_regnitz),
        ("Regnitz", osm_lines["Regnitz"] + list(regnitz_arms.geometry), pegnitz_regnitz, regnitz_main),
        ("Main", ne_lines["Main"], regnitz_main, main_rhine),
        ("Rhine", ne_lines["Rhine"], main_rhine, rhine_nederrijn),
        ("Nederrijn", ne_lines["Nederrijn"], rhine_nederrijn, nederrijn_lek),
        ("Lek", ne_lines["Lek"], nederrijn_lek, sea),
    ]:
        try:
            cs, joins = reference_path(lines, a, b)
        except ValueError as exc:
            raise ValueError(f"{name}: {exc}") from exc
        # Simplification for a screen-sized review, separately per river to retain joins.
        cs = [list(c) for c in LineString(cs).simplify(0.001).coords]
        chunks.append(cs)
        gaps.append({"river": name, "short_part_joins_m": joins, "points": len(cs)})
    transfers = [round(metres(a[-1], b[0]), 1) for a, b in pairwise(chunks)]
    if any(d > 3000 for d in transfers):
        raise ValueError(f"reference datasets disagree too much at joins: {transfers}")
    report = json.loads((ROOT / "fixtures/review/routes.json").read_text())
    munich = json.loads((ROOT / "recipe/preview/munich.json").read_text())
    row = next(r for r in report["towns"] if r["en"] == "Nuremberg")
    nuremberg = {
        "id": "a", "town": {"en": row["en"], "de": row["de"]},
        "coords": [c for chunk in chunks for c in chunk], "end": {"en": "North Sea", "de": "Nordsee"},
        "total_km": float(row["total_km"]), "geometry_kind": "reference",
        "changes": [
            {"at": pegnitz_regnitz, "from": {"en": "Pegnitz", "de": "Pegnitz"}, "to": {"en": "Regnitz", "de": "Regnitz"}},
            {"at": regnitz_main, "from": {"en": "Regnitz", "de": "Regnitz"}, "to": {"en": "Main", "de": "Main"}},
            {"at": main_rhine, "from": {"en": "Main", "de": "Main"}, "to": {"en": "Rhine", "de": "Rhein"}},
        ],
    }
    m = {"id": "b", "town": {k: munich["town"][k] for k in ("en", "de")}, "polyline": munich["polyline"],
         "end": munich["end"]["display"], "total_km": munich["total_km"], "geometry_kind": "model",
         "changes": [{"at": isar_danube, "from": {"en": "Isar", "de": "Isar"}, "to": {"en": "Danube", "de": "Donau"}}]}
    sources = []
    for p in [osm_file, ne_file, places_file, RAW / "ne_10m_coastline.geojson", RAW / "ne_10m_admin_0_boundary_lines_land.geojson"]:
        url = (
            "https://github.com/nikokoren/downstream/releases/download/"
            "osm-waterways-europe-germany-bayern/waterways-europe-germany-bayern.fgb"
            if p == osm_file else
            "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/" + p.name
        )
        sources.append({"file": str(p.relative_to(ROOT)), "url": url,
                        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    result = {"review_only": True, "captured": "2026-11-13", "routes": [nuremberg, m], "sources": sources,
              "reference_notes": {"parts": gaps, "between_sources_m": transfers,
                  "description": "Nürnberg reference follows actual Pegnitz, Regnitz, Main, Rhine, Nederrijn and Lek linework. Delta arms fold into Rhine, as D12. It is not the unavailable published HydroATLAS polyline. Distances come from the captured model report."}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "routes.json").write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    # Fine, real coastline/border geometry for an explicitly offline review basemap.
    window = shapely.box(-6, 39, 34, 58)
    features = []
    for filename, kind in [("ne_10m_coastline.geojson", "coast"), ("ne_10m_admin_0_boundary_lines_land.geojson", "border")]:
        for f in json.loads((RAW / filename).read_text())["features"]:
            geom = shape(f["geometry"])
            if geom.intersects(window):
                features.append({"type": "Feature", "properties": {"kind": kind}, "geometry": shapely.geometry.mapping(geom.intersection(window).simplify(0.003))})
    (OUT / "basemap.json").write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")))
    print(json.dumps({"routes": len(result["routes"]), "nuremberg_points": len(nuremberg["coords"]), "changes": [r["at"] for r in nuremberg["changes"]], "source_gaps_m": transfers, "parts": gaps}, ensure_ascii=False))


if __name__ == "__main__":
    main()
