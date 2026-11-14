"""Capture a small real source-network regression fixture after the regional source fetch.

Run with pipeline/.venv/bin/python from the repository root. No coordinates are invented.
"""

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import pyogrio
import shapely
from shapely import STRtree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))


def main():
    from downstream.fetch import basins_file, reaches_file
    from downstream.network import Network
    from downstream.regions import EUROPE

    CAPTURE = ROOT / "data/captured-site/2026-11-13"
    names = {"Stuttgart", "Ulm", "Mountsorrel", "Weißenburg in Bayern", "Pfaffenhofen an der Ilm"}
    packets = []
    for file in sorted((CAPTURE / "eu/t").glob("*.json")):
        packet = json.loads(file.read_text())
        if packet["town"]["en"] in names:
            packets.append(
                {
                    k: v
                    for k, v in packet.items()
                    if k not in {"ui", "place", "distance", "travel", "end_text", "slot"}
                }
            )
    assert len(packets) == len(names)
    net = Network.load(reaches_file(EUROPE))
    basins = pyogrio.read_dataframe(basins_file(EUROPE))
    tree = STRtree(basins.geometry.values)
    reach_ids, basin_ids = set(), set()
    for packet in packets:
        ids = net.downstream(packet["start"]["reach"])
        reach_ids.update(ids)
        basin_ids.add(int(net.reaches.at[ids[0], "HYBAS_L12"]))
        point = shapely.Point(packet["town"]["lon"], packet["town"]["lat"])
        basin_ids.update(
            int(basins.iloc[i]["HYBAS_ID"]) for i in tree.query(point, predicate="within")
        )
    reaches = net.reaches.loc[sorted(reach_ids)]
    basins = basins[basins["HYBAS_ID"].isin(basin_ids)]
    with (ROOT / "data/raw/pair-validation/name_table.csv").open() as handle:
        labels = {
            r["hyriv_id"]: [r["name"], r["source"]]
            for r in csv.DictReader(handle)
            if int(r["hyriv_id"]) in reach_ids
        }
    raw_names = {label[0] for label in labels.values()}
    with (ROOT / "data/raw/pair-validation/name_en.csv").open() as handle:
        name_en = {r[0]: r[1] for r in list(csv.reader(handle))[1:] if r[0] in raw_names}
    manifest = json.loads((CAPTURE / "manifest.json").read_text())
    gids = {str(p["town"]["geonameid"]) for p in packets}
    report = json.loads((ROOT / "data/towns/eu-pair-validation.json").read_text())
    fixture = {
        "captured_on": "2026-11-13",
        "source_urls": {
            "RiverATLAS": "https://ndownloader.figshare.com/files/20087486",
            "BasinATLAS": "https://ndownloader.figshare.com/files/20087237",
        },
        "derived_from_sha256": report["sources"],
        "model_sources": [f for f in manifest["files"] if f["geonameid"] in gids],
        "modifications": "Only complete source routes and containing/starting basins for five captured towns; unused network features omitted.",
        "towns": packets,
        "reaches": json.loads(reaches.to_json(drop_id=True)),
        "basins": json.loads(basins.to_json(drop_id=True)),
        "labels": labels,
        "name_en": name_en,
    }
    out = ROOT / "fixtures/review/source-network.json.gz"
    out.write_bytes(
        gzip.compress(
            json.dumps(fixture, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(),
            mtime=0,
        )
    )
    print(f"{len(reaches)} real reaches, {len(basins)} real basins, {out.stat().st_size} bytes")
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
