"""Sea by water distance, on the real Natural Earth files (skipped if not downloaded).
Mouth coordinates are the last points of HydroATLAS paths from the 2026-09-28 run."""

from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
NEEDED = [RAW / "ne_ocean.zip", RAW / "ne_marine.zip"]


@pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="Natural Earth not downloaded")
@pytest.mark.parametrize(
    "mouth, sea",
    [
        ((10.139583, 54.31875), "Baltic Sea"),  # Kiel: straight-line nearest was the North Sea
        ((29.697916, 45.247916), "Black Sea"),  # Danube delta
        ((4.152083, 51.960416), "North Sea"),  # Rhine mouth
        ((9.864583, 53.54375), "North Sea"),  # Elbe at Hamburg
    ],
)
def test_mouth_drains_into_sea(mouth, sea):
    from downstream.seas import load_seas

    assert load_seas(RAW / "ne_ocean.zip", RAW / "ne_marine.zip").drains_into(*mouth)[0] == sea
