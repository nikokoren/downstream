"""Check a model journey against the original CC BY RiverATLAS/BasinATLAS geometry.

The display polyline is deliberately not used to measure the town-to-reach offset.
Missing source evidence is a rejection, not an inferred pass.
"""

import argparse
import csv
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

import pyogrio
import shapely
from pyproj import Transformer
from shapely import STRtree
from shapely.ops import transform

from downstream import naming, regions
from downstream.fetch import basins_file, reaches_file
from downstream.network import Network

CHECK_VERSION = 1


@lru_cache(maxsize=8)
def _projector(metric_crs):
    return Transformer.from_crs("EPSG:4326", metric_crs, always_xy=True).transform


def model_signature(packet):
    fields = (
        "town",
        "start",
        "reaches",
        "total_km",
        "travel_days",
        "lake_days",
        "chain",
        "changes",
        "end",
        "polyline",
    )
    data = {key: packet.get(key) for key in fields}
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def seal_checks(packet):
    packet["pair_checks"]["model_sha256"] = model_signature(packet)
    return packet


def source_checks(packet, net, basins, tree, region, ids=None):
    """Verify point membership, selected reach, complete routing and recorded distance."""
    issues = []
    point = shapely.Point(packet["town"]["lon"], packet["town"]["lat"])
    hits = tree.query(point, predicate="within")
    basin_id = int(basins.iloc[hits[0]]["HYBAS_ID"]) if len(hits) == 1 else None
    if basin_id is None:
        issues.append("town_has_no_unique_source_basin")
    start = packet.get("start", {})
    rid = start.get("reach")
    result = {
        "version": CHECK_VERSION,
        "status": "rejected",
        "issues": issues,
        "basin_id": basin_id,
        "reach_basin_id": None,
        "start_distance_km": None,
        "outlet_reach": None,
    }
    if rid not in net.reaches.index:
        issues.append("source_start_reach_missing")
        return result
    first = net.reaches.loc[rid]
    result["reach_basin_id"] = int(first["HYBAS_L12"])
    if basin_id != result["reach_basin_id"]:
        issues.append("start_reach_outside_town_basin")
    if start.get("how") != f"sub-basin {basin_id}":
        issues.append("start_is_not_selected_inside_source_basin")
    project = _projector(region.metric_crs)
    distance = transform(project, point).distance(transform(project, first.geometry)) / 1000
    result["start_distance_km"] = round(distance, 6)
    if not math.isfinite(distance) or distance > 1:
        issues.append("start_reach_more_than_1km_from_town")
    try:
        ids = ids if ids is not None else net.downstream(rid)
    except (KeyError, ValueError):
        issues.append("source_route_incomplete_or_cyclic")
        return result
    last = net.reaches.loc[ids[-1]]
    result["outlet_reach"] = int(last["HYRIV_ID"])
    if int(last["NEXT_DOWN"]) != 0 or int(first["MAIN_RIV"]) != result["outlet_reach"]:
        issues.append("source_route_does_not_reach_its_outlet")
    if packet.get("reaches") != len(ids):
        issues.append("model_reach_count_differs_from_source")
    km = round(float(first["DIST_DN_KM"] + first["LENGTH_KM"]), 1)
    if not math.isfinite(packet.get("total_km", math.nan)) or abs(packet["total_km"] - km) > 0.051:
        issues.append("model_distance_differs_from_source")
    if not isinstance(packet.get("travel_days"), (int, float)) or not (
        math.isfinite(packet["travel_days"]) and packet["travel_days"] > 0
    ):
        issues.append("travel_estimate_missing")
    if packet.get("end", {}).get("type") != "sea":
        issues.append("journey_does_not_end_in_a_sea")
    if any(s.get("source") == "osm:canal" for s in packet.get("chain", [])):
        issues.append("route_contains_engineered_channel")
    result["status"] = "passed" if not issues else "rejected"
    return result


def checked_for_pairs(packet):
    """Fail closed for published legacy packets or results from another check version."""
    check = packet.get("pair_checks", {})
    offset = check.get("start_distance_km")
    return (
        check.get("version") == CHECK_VERSION
        and check.get("status") == "passed"
        and not check.get("issues")
        and check.get("basin_id") is not None
        and check.get("basin_id") == check.get("reach_basin_id")
        and isinstance(offset, (int, float))
        and math.isfinite(offset)
        and 0 <= offset <= 1
        and bool(check.get("outlet_reach"))
        and packet.get("start", {}).get("distance_km") == offset
        and check.get("model_sha256") == model_signature(packet)
    )


def augment(packet, net, basins, tree, region, labels=None, name_en=None):
    """Keep the published distance/time/chain; regenerate geometry hand-offs from source reaches."""
    from downstream.paths import (
        MAX_MAP_POINTS,
        close_lake_chain,
        encode_polyline,
        map_changes,
        simplify_to,
        to_latin,
    )

    result = dict(packet)
    try:
        ids = net.downstream(packet["start"]["reach"])
    except (KeyError, ValueError):
        ids = None
    check = source_checks(packet, net, basins, tree, region, ids=ids)
    result["pair_checks"] = check
    result["start"] = {**packet["start"], "distance_km": check["start_distance_km"]}
    # The 1 km and canal rules govern comparisons. Ordinary journeys still receive real
    # river-change labels when their complete source route and names can be reproduced.
    fatal = {
        "source_start_reach_missing",
        "source_route_incomplete_or_cyclic",
        "source_route_does_not_reach_its_outlet",
        "model_reach_count_differs_from_source",
        "model_distance_differs_from_source",
    }
    if ids is None or fatal.intersection(check["issues"]):
        return result
    reaches = net.reaches.loc[ids]
    if labels is None:
        check["issues"].append("source_river_names_missing")
        check["status"] = "rejected"
        return result
    groups = naming.chain(
        reaches, [labels.get(i, (None, None)) for i in ids], naming.load_curated()
    )
    groups = to_latin(groups, name_en or {}, packet["town"]["cc"])
    if packet["end"]["type"] != "sea" and groups[-1]["kind"] == "lake":
        groups = close_lake_chain(groups)
    source_chain = [{k: g[k] for k in ("kind", "name")} for g in groups]
    published_chain = [{k: g[k] for k in ("kind", "name")} for g in packet["chain"]]
    # Estuary names can be appended beyond the RiverATLAS terminal reach. They do not locate
    # another river hand-off. All source-network steps must still match exactly.
    if published_chain[: len(source_chain)] != source_chain:
        check["issues"].append("source_names_differ_from_published_chain")
        check["status"] = "rejected"
        return result
    changes = map_changes(groups, reaches)
    line = shapely.line_merge(shapely.MultiLineString(list(reaches.geometry.values)))
    if line.geom_type != "LineString":
        check["issues"].append("source_route_geometry_disconnected")
        check["status"] = "rejected"
        return result
    coords = list(line.coords)
    start_point = shapely.Point(reaches.geometry.iloc[0].coords[0])
    if shapely.Point(coords[-1]).distance(start_point) < shapely.Point(coords[0]).distance(
        start_point
    ):
        line = shapely.reverse(line)
    result["changes"] = changes
    result["polyline"] = encode_polyline(
        shapely.get_coordinates(simplify_to(line, MAX_MAP_POINTS, keep=[c["at"] for c in changes]))
    )
    return seal_checks(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--towns", type=Path, required=True, help="Captured normal-rotation town JSONs"
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--names", type=Path, required=True, help="Released cleaned name_table[_region].csv"
    )
    parser.add_argument("--name-en", type=Path, help="Released name_en.csv")
    args = parser.parse_args()
    region = regions.current()
    net = Network.load(reaches_file(region))
    basins = pyogrio.read_dataframe(basins_file(region))
    tree = STRtree(basins.geometry.values)
    with args.names.open(encoding="utf-8", newline="") as handle:
        labels = {int(r["hyriv_id"]): (r["name"], r["source"]) for r in csv.DictReader(handle)}
    name_en = {}
    if args.name_en:
        with args.name_en.open(encoding="utf-8", newline="") as handle:
            name_en = {r[0]: r[1] for r in list(csv.reader(handle))[1:]}
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, file in enumerate(sorted(args.towns.glob("*.json"))):
        packet = json.loads(file.read_text())
        assert str(packet["town"]["geonameid"]) == file.stem
        result = augment(packet, net, basins, tree, region, labels, name_en)
        (args.out / file.name).write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )
        rows.append({"geonameid": file.stem, "town": packet["town"]["en"], **result["pair_checks"]})
        if (index + 1) % 250 == 0:
            print(f"{region.code}: {index + 1} source checks", flush=True)
    sources = {}
    for path in [reaches_file(region), basins_file(region), args.names]:
        with path.open("rb") as handle:
            sources[str(path)] = hashlib.file_digest(handle, "sha256").hexdigest()
    (args.out.parent / f"{region.code}-pair-validation.json").write_text(
        json.dumps(
            {
                "region": region.code,
                "sources": sources,
                "towns": rows,
                "passed": sum(r["status"] == "passed" for r in rows),
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    print(
        f"{region.code}: {sum(r['status'] == 'passed' for r in rows)}/{len(rows)} passed -> {args.out}"
    )


if __name__ == "__main__":
    main()
