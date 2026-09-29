"""Per-river clean-up of the reach names (per-river redesign, stage 2, 2026-09-28).

A river is a chain of reaches with the same classical order (ORD_CLAS), from its source down to
where it joins a bigger river: along NEXT_DOWN the order only stays or drops, and no reach has two
upstream reaches of its own order (checked on all 938,544 `eu` reaches, 2026-09-28). So every
reach belongs to exactly one river, identified by the river's last reach ("mouth").

The clean-up rules are the ones from `naming`, applied along each whole river instead of along a
path, so a reach gets the same name whichever town's path reaches it:
- lakes are left alone (D13);
- a name stretch shorter than 3 reaches and 5 km is absorbed; canal names never stand alone;
- A -> B -> A becomes A, shortest B first;
- names compare as displayed (curated table: Donau/Duna/Dunav are one river);
- on a river that reaches the sea or a sink (NEXT_DOWN == 0), a name change on its last 150 km
  where no tributary joins is a delta arm or estuary and keeps the river's name (D12).
"""

import numpy as np
import pandas as pd

from downstream.naming import _absorb_short_blocks, _collapse_interruptions, _key, is_lake


def river_mouths(reaches: pd.DataFrame) -> np.ndarray:
    """For each reach (row order), the HYRIV_ID of the last reach of its river."""
    ids = reaches["HYRIV_ID"].to_numpy()
    pos = pd.Series(np.arange(len(ids)), index=ids)
    nxt = reaches["NEXT_DOWN"].to_numpy()
    order = reaches["ORD_CLAS"].to_numpy()
    nxt_pos = pos.reindex(nxt).to_numpy()
    has = ~np.isnan(nxt_pos)
    nxt_i = np.where(has, nxt_pos, -1).astype(int)
    same = has & (order[np.maximum(nxt_i, 0)] == order)
    ptr = np.where(same, nxt_i, np.arange(len(ids)))
    while True:  # pointer jumping: log2(longest river) rounds
        nptr = ptr[ptr]
        if np.array_equal(nptr, ptr):
            break
        ptr = nptr
    return ids[ptr]


# 200 km, not 150: the Rhine splits at Pannerden 172 km from its HydroATLAS mouth (checked
# 2026-09-29); at 150 km its first Dutch arms ("Bijlandsch Kanaal") were shown to the sea.
DELTA_ZONE_KM = 200.0
ARM_MAX_GROWTH = 0.05


def _fold_outlet(labels: list[tuple], km: list[float], upland: list[float]) -> list[tuple]:
    """Delta arms (D12): on the last DELTA_ZONE_KM of a river that reaches the sea, a name change
    where no tributary joins (upstream area grows < 5 % across the neighbouring reaches) is an
    arm or estuary of the same river and keeps the river's name. Checked 2026-09-29 on the data:
    Rhine -> Lek +0.0 %, Danube -> Bratul Chillia +0.0 %, Warnow -> Unterwarnow +1.8 % (fold);
    Streitgraben -> Warnow +103 % (a real confluence, kept).

    Earlier versions failed: "fold into the dominant name" renamed the lower Rhône "Doubs" and the
    lower Seine "Marne"; "fold the last 150 km" renamed the lower Warnow "Streitgraben".
    """
    n = len(labels)
    from_mouth = np.cumsum(np.asarray(km)[::-1])[::-1] - np.asarray(km)
    out = list(labels)
    current = None
    for i in range(n):
        lab = labels[i]
        if not lab[0] or is_lake(lab):
            continue
        if current is not None and _key(lab) != _key(current) and from_mouth[i] < DELTA_ZONE_KM:
            a, b = upland[max(i - 2, 0)], upland[min(i + 1, n - 1)]
            if a > 0 and (b - a) / a < ARM_MAX_GROWTH:
                out[i] = current
                continue
        current = lab
    return out


def clean(reaches: pd.DataFrame, raw: pd.DataFrame, min_block=3, min_block_km=5.0) -> pd.DataFrame:
    """reaches: HYRIV_ID, NEXT_DOWN, ORD_CLAS, LENGTH_KM, DIST_DN_KM. raw: HYRIV_ID, name, source.
    Returns HYRIV_ID, name, source, mouth (cleaned, one row per reach)."""
    cols = ["HYRIV_ID", "NEXT_DOWN", "ORD_CLAS", "LENGTH_KM", "DIST_DN_KM"]
    has_up = "UPLAND_SKM" in reaches
    df = reaches[cols + (["UPLAND_SKM"] if has_up else [])].copy()
    df["mouth"] = river_mouths(df)
    df = df.merge(raw, on="HYRIV_ID", how="left")
    outlet_mouths = set(df.loc[df["NEXT_DOWN"] == 0, "HYRIV_ID"])
    df = df.sort_values(["mouth", "DIST_DN_KM"], ascending=[True, False]).reset_index(drop=True)
    named = df.groupby("mouth")["name"].count()
    todo = set(named[named > 0].index)
    # pandas 3: plain to_numpy is read-only, and missing values come back as NaN
    names = np.array([x if isinstance(x, str) else None for x in df["name"]], dtype=object)
    sources = np.array([x if isinstance(x, str) else None for x in df["source"]], dtype=object)
    km_all = df["LENGTH_KM"].to_numpy(dtype=float)
    up_all = df["UPLAND_SKM"].to_numpy(dtype=float) if has_up else None
    starts = np.flatnonzero(np.r_[True, df["mouth"].to_numpy()[1:] != df["mouth"].to_numpy()[:-1]])
    ends = np.r_[starts[1:], len(df)]
    mouths = df["mouth"].to_numpy()
    for a, b in zip(starts, ends, strict=True):
        m = mouths[a]
        if m not in todo or b - a < 2 and m not in outlet_mouths:
            continue
        labels = list(zip(names[a:b], sources[a:b], strict=True))
        idx = [i for i, lab in enumerate(labels) if not is_lake(lab)]
        if idx:
            sub = [labels[i] for i in idx]
            km = [km_all[a + i] for i in idx]
            sub = _absorb_short_blocks(sub, min_block, km, min_block_km)
            sub = _collapse_interruptions(sub, km)
            for i, lab in zip(idx, sub, strict=True):
                labels[i] = lab
        if m in outlet_mouths and up_all is not None:
            labels = _fold_outlet(labels, list(km_all[a:b]), list(up_all[a:b]))
        for i, (nm, src) in enumerate(labels):
            names[a + i], sources[a + i] = nm, src
    return pd.DataFrame(
        {"HYRIV_ID": df["HYRIV_ID"], "name": names, "source": sources, "mouth": mouths}
    )
