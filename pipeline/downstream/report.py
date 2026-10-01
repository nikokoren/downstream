"""Build report (BRIEF P7): one row per town (towns.csv) and a readable summary (report.md)."""

from pathlib import Path

import pandas as pd

from downstream import regions


def _pct(x: float) -> str:
    return f"{100 * x:.0f} %"


def write(df: pd.DataFrame, out: Path, seconds: float) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "towns.csv", index=False)
    if "excluded" not in df:
        df["excluded"] = ""
    df["excluded"] = df["excluded"].fillna("")
    bad = df[df["error"] != ""]
    computed = df[df["error"] == ""]
    ok = computed[computed["excluded"] == ""]  # towns in the rotation
    excl = computed[computed["excluded"] != ""]
    lines = [
        "# Downstream build report",
        "",
        (
            f"- Towns: {len(df)} (region {regions.current().code}, D9, D22); in the rotation: {len(ok)}; "
            f"excluded (start > 5 km from the town): {len(excl)}; errors: {len(bad)}; "
            f"time: {seconds:.0f} s. Figures below cover the towns in the rotation."
        ),
        (
            f"- Payload (compact JSON): median {ok['payload_bytes'].median():.0f} B, "
            f"max {ok['payload_bytes'].max():.0f} B; "
            f"over 6 KB (R3): {(ok['payload_bytes'] > 6000).sum()}."
        ),
        f"- Start distance from the town point: max {ok['start_dist_km'].max():.1f} km.",
        f'- First step unnamed ("a stream"): {ok["first_unnamed"].sum()} ({_pct(ok["first_unnamed"].mean())}).',
        (
            f"- Path km named: median {_pct(ok['named_share'].median())}; "
            f"from OSM: median {_pct(ok['osm_share'].median())}."
        ),
        "",
        "## Endpoints",
        "",
        "| Type | Name | Towns |",
        "|---|---|---|",
    ]
    ends = (
        ok.groupby(["end_type", ok["end_name"].fillna("(none)")])
        .size()
        .sort_values(ascending=False)
    )
    lines += [f"| {t} | {n} | {c} |" for (t, n), c in ends.items()]
    lines += [
        "",
        "## By country",
        "",
        "| Country | Towns | First step unnamed | Path km named (median) | From OSM (median) | Max payload |",
        "|---|---|---|---|---|---|",
    ]
    for cc, g in ok.groupby("cc"):
        lines.append(
            f"| {cc} | {len(g)} | {_pct(g['first_unnamed'].mean())} | {_pct(g['named_share'].median())} "
            f"| {_pct(g['osm_share'].median())} | {g['payload_bytes'].max():.0f} B |"
        )
    if len(bad):
        lines += ["", "## Errors", "", "| Town | Country | Error |", "|---|---|---|"]
        lines += [f"| {r['name']} | {r['cc']} | {r['error']} |" for _, r in bad.iterrows()]
    far = excl.sort_values("start_dist_km", ascending=False)
    if len(far):
        lines += [
            "",
            f"## Excluded: start more than 5 km from the town ({len(far)})",
            "",
            "| Town | Country | km |",
            "|---|---|---|",
        ]
        lines += [f"| {r['name']} | {r['cc']} | {r['start_dist_km']} |" for _, r in far.iterrows()]
    path = out / "report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
