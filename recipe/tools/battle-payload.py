"""Review packets from captured geography; never supply an invented Nürnberg duration."""

import json
import sys
from pathlib import Path

import shapely

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from downstream.locales import UI  # noqa: E402
from downstream.paths import MAX_MAP_POINTS, encode_polyline, simplify_to  # noqa: E402
from downstream.site import _display  # noqa: E402


def packets(reference):
    munich = json.loads((ROOT / "recipe/preview/munich.json").read_text())
    munich["changes"] = reference["routes"][1]["changes"]
    munich = _display(munich)
    r = reference["routes"][0]
    report = json.loads((ROOT / "fixtures/review/routes.json").read_text())
    row = next(t for t in report["towns"] if t["en"] == "Nuremberg")
    names = [r["changes"][0]["from"], *[c["to"] for c in r["changes"]]]
    assert " → ".join(n["en"] for n in names) == row["chain"]
    nuremberg = _display({
        "town": {"geonameid": row["geonameid"], **r["town"], "cc": row["cc"]},
        "total_km": r["total_km"],
        "travel_days": r.get("travel_days"),
        "chain": [{"kind": "river", "name": n} for n in names],
        "end": {"type": "sea", "name": r["end"]["en"], "display": r["end"]},
        "changes": r["changes"],
        "polyline": r.get("polyline") or encode_polyline(shapely.get_coordinates(simplify_to(
            shapely.LineString(r["coords"]), MAX_MAP_POINTS, keep=[c["at"] for c in r["changes"]]
        ))),
    })
    pair = {"ui": UI, "routes": [{k: v for k, v in town.items() if k != "ui"} for town in [nuremberg, munich]]}
    return {"single": munich, "pair": pair}


if __name__ == "__main__":
    ref = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "fixtures/review/battle-reference.json"
    print(json.dumps(packets(json.loads(ref.read_text())), ensure_ascii=False))
