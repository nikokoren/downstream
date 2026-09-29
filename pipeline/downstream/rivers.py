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
- on a river that reaches the sea or a sink (NEXT_DOWN == 0), names after the last stretch of
  its dominant name (most km) fold into it: delta arms (D12). Upstream names stay (e.g. a
  source stream with its own name).
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


def _fold_outlet(labels: list[tuple], km: list[float]) -> list[tuple]:
    river = [i for i, lab in enumerate(labels) if lab[0] and not is_lake(lab)]
    if not river:
        return labels
    total: dict = {}
    for i in river:
        total[_key(labels[i])] = total.get(_key(labels[i]), 0.0) + km[i]
    main = max(total, key=total.get)
    last = max(i for i in river if _key(labels[i]) == main)
    main_label = labels[last]
    out = list(labels)
    for i in range(last + 1, len(labels)):
        if not is_lake(labels[i]):
            out[i] = main_label
    return out


def clean(reaches: pd.DataFrame, raw: pd.DataFrame, min_block=3, min_block_km=5.0) -> pd.DataFrame:
    """reaches: HYRIV_ID, NEXT_DOWN, ORD_CLAS, LENGTH_KM, DIST_DN_KM. raw: HYRIV_ID, name, source.
    Returns HYRIV_ID, name, source, mouth (cleaned, one row per reach)."""
    df = reaches[["HYRIV_ID", "NEXT_DOWN", "ORD_CLAS", "LENGTH_KM", "DIST_DN_KM"]].copy()
    df["mouth"] = river_mouths(df)
    df = df.merge(raw, on="HYRIV_ID", how="left")
    df["name"] = df["name"].where(df["name"].notna(), None)
    df["source"] = df["source"].where(df["source"].notna(), None)
    outlet_mouths = set(df.loc[df["NEXT_DOWN"] == 0, "HYRIV_ID"])
    df = df.sort_values(["mouth", "DIST_DN_KM"], ascending=[True, False]).reset_index(drop=True)
    named = df.groupby("mouth")["name"].count()
    todo = set(named[named > 0].index)
    names = df["name"].to_numpy(dtype=object)
    sources = df["source"].to_numpy(dtype=object)
    km_all = df["LENGTH_KM"].to_numpy(dtype=float)
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
        if m in outlet_mouths:
            labels = _fold_outlet(labels, list(km_all[a:b]))
        for i, (nm, src) in enumerate(labels):
            names[a + i], sources[a + i] = nm, src
    return pd.DataFrame(
        {"HYRIV_ID": df["HYRIV_ID"], "name": names, "source": sources, "mouth": mouths}
    )
