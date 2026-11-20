"""Discover nearby towns draining to different seas; write candidates for human review.

Use complete town JSONs after a model build. A captured report + GeoNames coordinate cache
also supports an initial search, explicitly without claiming the routes were reviewed.
Nothing here changes the rotation or approves/publishes pairs.
"""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from itertools import product
from pathlib import Path

from pyproj import Geod

from downstream import naming

GEOD = Geod(ellps="WGS84")
# Lower than WGS84's minimum curvature radius: conservative search cells even near the poles.
MIN_RADIUS_KM = 6330.0
DEFAULT_MAX_KM = 80.0

# Editorial receiver groups for strong comparisons, not a formal global basin taxonomy.
# Keep the North, Baltic and Black Seas distinct; collapse nested gulfs and Mediterranean
# sub-seas so a local label boundary cannot by itself qualify a pair. Cards keep real names.
DESTINATION_GROUPS = {
    name: group
    for group, names in {
        "Baltic Sea": ("Baltic Sea", "Gulf of Bothnia", "Gulf of Finland", "Gulf of Riga"),
        "Black Sea": ("Black Sea", "Sea of Azov"),
        "North Sea": ("North Sea", "Skagerrak", "Kattegat"),
        "Mediterranean Sea": (
            "Mediterranean Sea",
            "Adriatic Sea",
            "Tyrrhenian Sea",
            "Balearic Sea",
            "Ligurian Sea",
            "Ionian Sea",
            "Aegean Sea",
            "Gulf of Lion",
            "Sea of Crete",
            "Alboran Sea",
        ),
        "North Atlantic": (
            "North Atlantic Ocean",
            "Bay of Biscay",
            "English Channel",
            "Irish Sea",
            "Bristol Channel",
            "Celtic Sea",
            "Gulf of Saint Lawrence",
            "Gulf of Maine",
            "Bay of Fundy",
            "Labrador Sea",
        ),
        "North Pacific": (
            "North Pacific Ocean",
            "Salish Sea",
            "Hecate Strait",
            "Gulf of California",
            "Bering Sea",
        ),
        "Hudson Bay": ("Hudson Bay", "James Bay"),
        "Gulf of Mexico": ("Gulf of Mexico", "Straits of Florida"),
    }.items()
    for name in names
}


def destination_group(name: str) -> str:
    return DESTINATION_GROUPS.get(name, name)


def report_towns(report: Path, coordinates: Path) -> tuple[list[dict], dict]:
    """Join by GeoNames ID, never by a guessed spelling. Coordinates are a cached city JSON."""
    cities = json.loads(coordinates.read_text(encoding="utf-8"))
    curated = naming.load_curated()
    towns, missing = [], []
    with report.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["excluded"] or r["error"] or r["end_type"] != "sea":
            continue
        gid = r["geonameid"]
        c = cities.get(gid)
        if not c:
            missing.append(gid)
            continue
        if c["countrycode"] != r["cc"]:
            raise ValueError(f"country mismatch for GeoNames {gid}")
        disp = naming.lookup_curated(r["end_name"], curated) or {}
        towns.append(
            {
                "geonameid": gid,
                "name": r["en"],
                "de": r["de"],
                "country": r["cc"],
                "lon": c["longitude"],
                "lat": c["latitude"],
                "population": int(r["population"]),
                "destination": disp.get("en") or r["end_name"],
                "total_km": float(r["total_km"]),
                "start_dist_km": float(r["start_dist_km"]),
                "chain": r["chain"],
                "travel_days": float(r["travel_days"]) if r.get("travel_days") else None,
                "model_file": None,
            }
        )
    return towns, {
        "report_rows": len(rows),
        "matched_sea_towns": len(towns),
        "missing_ids": missing,
    }


def model_towns(folders: list[Path]) -> list[dict]:
    """Read normal-rotation outputs; towns.region_towns owns the shared eligibility policy."""
    towns = []
    for folder in folders:
        for path in sorted(folder.glob("*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            if d["end"]["type"] != "sea":
                continue
            c = d["town"]
            towns.append(
                {
                    "geonameid": str(c["geonameid"]),
                    "name": c["en"],
                    "de": c["de"],
                    "country": c["cc"],
                    "lon": c["lon"],
                    "lat": c["lat"],
                    "population": c["population"],
                    "destination": (d["end"].get("display") or {}).get("en") or d["end"]["name"],
                    "total_km": d["total_km"],
                    "start_dist_km": d["start"].get("distance_km"),
                    "chain": " → ".join(
                        (s["name"] or {}).get("en") or (s["name"] or {}).get("local") or "(stream)"
                        for s in d["chain"]
                    ),
                    "travel_days": d.get("travel_days"),
                    "model_file": str(path),
                }
            )
    return towns


def _xyz(town: dict) -> tuple[float, float, float]:
    lat, lon = math.radians(town["lat"]), math.radians(town["lon"])
    return math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)


def find_pairs(
    towns: list[dict], max_km=DEFAULT_MAX_KM, max_start_km=1.0, min_path_km=100.0
) -> list[dict]:
    """Global spatial grid, then exact WGS84 town-to-town distances. No route is recomputed."""
    if max_km <= 0 or max_start_km < 0 or min_path_km < 0:
        raise ValueError("invalid pair-search thresholds")
    if len({t["geonameid"] for t in towns}) != len(towns):
        raise ValueError("duplicate GeoNames IDs in the search input")
    cells = defaultdict(list)
    size = max_km / MIN_RADIUS_KM
    pairs = []
    for town in sorted(towns, key=lambda t: t["geonameid"]):
        if not (-90 <= town["lat"] <= 90 and -180 <= town["lon"] <= 180):
            raise ValueError(f"invalid coordinate for {town['geonameid']}")
        if town["total_km"] < min_path_km:
            continue
        if town["start_dist_km"] is not None and town["start_dist_km"] > max_start_km:
            continue
        xyz = _xyz(town)
        key = tuple(math.floor(x / size) for x in xyz)
        for offset in product((-1, 0, 1), repeat=3):
            bucket = tuple(k + o for k, o in zip(key, offset, strict=True))
            for other in cells.get(bucket, ()):
                if destination_group(town["destination"]) == destination_group(
                    other["destination"]
                ):
                    continue
                azimuth, _, metres = GEOD.inv(other["lon"], other["lat"], town["lon"], town["lat"])
                if metres > max_km * 1000:
                    continue
                lon, lat, _ = GEOD.fwd(other["lon"], other["lat"], azimuth, metres / 2)
                members = [other, town]
                pairs.append(
                    {
                        "id": "-".join(t["geonameid"] for t in members),
                        "distance_km": round(metres / 1000, 3),
                        "towns": members,
                        "midpoint": [lon, lat],
                        "review": "route, basin, travel-time and screen review required",
                    }
                )
        cells[key].append(town)
    return sorted(pairs, key=lambda p: (p["distance_km"], p["id"]))


def shortlist(pairs: list[dict], limit=30, spacing_km=75.0) -> list[dict]:
    """A small review sample only. Never use this to cap the rotation catalogue."""
    if limit <= 0:
        return []
    selected, used = [], set()
    for pair in pairs:
        if any(t["geonameid"] in used for t in pair["towns"]):
            continue
        lon, lat = pair["midpoint"]
        if any(GEOD.inv(lon, lat, *p["midpoint"])[2] < spacing_km * 1000 for p in selected):
            continue
        selected.append(pair)
        used.update(t["geonameid"] for t in pair["towns"])
        if len(selected) >= limit:
            break
    return selected


def pair_key(pair: dict) -> tuple[str, str]:
    """Swapping left/right is the same comparison, not another unique screen."""
    ids = tuple(sorted(str(t["geonameid"]) for t in pair["towns"]))
    if len(ids) != 2 or ids[0] == ids[1]:
        raise ValueError("a comparison needs two distinct towns")
    return ids


def source(path: Path) -> dict:
    return {"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--towns",
        nargs="+",
        type=Path,
        help="Normal-rotation model folders, selected by towns.region_towns",
    )
    inputs.add_argument("--report", type=Path, help="Captured build-report towns.csv")
    parser.add_argument("--coordinates", type=Path, help="GeoNames cache city JSON keyed by ID")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-km", type=float, default=DEFAULT_MAX_KM)
    parser.add_argument("--max-start-km", type=float, default=1.0)
    parser.add_argument("--min-path-km", type=float, default=100.0)
    parser.add_argument(
        "--review-sample",
        "--shortlist",
        dest="review_sample",
        type=int,
        default=30,
        help="Example count for human review only; never limits the pool",
    )
    args = parser.parse_args()
    if args.report:
        if not args.coordinates:
            parser.error("--report requires --coordinates")
        towns, stats = report_towns(args.report, args.coordinates)
        sources = [source(args.report), source(args.coordinates)]
    else:
        towns = model_towns(args.towns)
        stats = {"model_towns": len(towns)}
        sources = [source(Path(t["model_file"])) for t in towns]
    pairs = find_pairs(towns, args.max_km, args.max_start_km, args.min_path_km)
    chosen = shortlist(pairs, args.review_sample)
    args.out.mkdir(parents=True, exist_ok=True)
    packet = {
        "review_only": True,
        "town_selection": "Existing recipe rotation only; no separate population or suburb policy",
        "sources": sources,
        "coverage": stats,
        "thresholds": {
            "max_km": args.max_km,
            "max_start_km": args.max_start_km,
            "min_path_km": args.min_path_km,
        },
        "candidates": pairs,
        "review_sample_ids": [p["id"] for p in chosen],
        # Compatibility with the first review output; this is not a catalogue limit.
        "shortlist_ids": [p["id"] for p in chosen],
    }
    (args.out / "candidates.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=1) + "\n"
    )
    with (args.out / "candidates.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "distance_km", "town_1", "cc_1", "sea_1", "town_2", "cc_2", "sea_2"])
        for p in pairs:
            a, b = p["towns"]
            w.writerow(
                [
                    p["id"],
                    p["distance_km"],
                    a["name"],
                    a["country"],
                    a["destination"],
                    b["name"],
                    b["country"],
                    b["destination"],
                ]
            )
    lines = [
        "# Nearby towns, different seas: review examples",
        "",
        f"{len(pairs)} candidates retained. The {len(chosen)} examples below do not cap the pool.",
        "",
        "| Town | Destination | Neighbour | Destination | Apart |",
        "|---|---|---|---|---|",
    ]
    for p in chosen:
        a, b = p["towns"]
        lines.append(
            f"| {a['name']} ({a['country']}) | {a['destination']} | {b['name']} ({b['country']}) | {b['destination']} | {p['distance_km']:.1f} km |"
        )
    (args.out / "shortlist.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.out / "review-sample.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "coverage": stats,
                "candidates": len(pairs),
                "review_examples": len(chosen),
                "out": str(args.out),
            }
        )
    )


if __name__ == "__main__":
    main()
