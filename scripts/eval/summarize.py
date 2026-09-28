"""
Summarise a round's CSV into the tables pre-registered in section 0.7.

    python scripts/eval/summarize.py eval/results/round_1.csv

Writes <csv stem>_summary.md next to the CSV and prints it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from common import wilson

FLOAT = ["grid_err_px", "corner_err_px", "heldout_px", "agree_px", "rmse_px",
         "n_inliers", "unif_cells", "t_total_ms", "ncc_before", "ncc_after", "texture"]


def pct(k, n):
    if n == 0:
        return "—"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, CI {100 * lo:.0f}–{100 * hi:.0f})"


def med(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return f"{s.median():.2f}" if len(s) else "—"


def block(df, by=None):
    """Verdict table for one family, optionally broken down by a column."""
    lines = []
    real = df["provenance"].iloc[0] == "REAL"
    err = "heldout_px" if real else "grid_err_px"
    head = ("| arm | " + (f"{by} | " if by else "") + "N | SUCCESS | SUBPIXEL | MARGINAL | "
            f"FAILURE | NO_LOCK | median {err} | median inliers | UNIFORM | median ms |")
    lines += [head, "|" + "---|" * (head.count("|") - 1)]
    groups = df.groupby(["arm"] + ([by] if by else []), sort=True)
    for key, g in groups:
        key = key if isinstance(key, tuple) else (key,)
        ev = g[~g["verdict"].str.startswith("EXCLUDED")]
        n = len(ev)
        c = ev["verdict"].value_counts()
        matched = ev[ev["verdict"] != "NO_LOCK"]
        lines.append(
            f"| {key[0]} | " + (f"{key[1]} | " if by else "") + f"{n} | "
            f"{pct(int(c.get('SUCCESS', 0)), n)} | "
            f"{pct(int((ev['subpixel'] == True).sum()), n)} | "  # noqa: E712
            f"{int(c.get('MARGINAL', 0))} | {int(c.get('FAILURE', 0))} | {int(c.get('NO_LOCK', 0))} | "
            f"{med(matched[err])} | {med(matched['n_inliers'])} | "
            f"{pct(int((matched['uniform'] == True).sum()), len(matched))} | "  # noqa: E712
            f"{med(matched['t_total_ms'])} |")
    return "\n".join(lines)


def main():
    path = Path(sys.argv[1])
    df = pd.read_csv(path)
    for c in ("subpixel", "uniform", "false_confidence", "degenerate"):
        if c in df:
            df[c] = df[c].astype(str).str.lower().eq("true")
    for c in FLOAT:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    out = [f"# Summary — {path.name}", ""]
    for fam, g in df.groupby("family", sort=True):
        out += [f"## {fam} ({g['provenance'].iloc[0]})", ""]
        excl = g[g["verdict"].str.startswith("EXCLUDED")]["id"].nunique()
        if excl:
            out.append(f"Excluded before matching (fill / duplicate): {excl} locations.\n")
        out += ["**All**", "", block(g), ""]
        out += ["**By split**", "", block(g, "split"), ""]
        if g["provenance"].iloc[0] == "REAL":
            out += ["**By terrain (texture tertile)**", "", block(g[g["terrain"].notna()], "terrain"), ""]
        elif g["level_name"].notna().any() and g["level_name"].astype(str).str.len().max() > 0:
            g2 = g.copy()
            g2["lvl"] = g2["level_name"].astype(str) + "=" + g2["level"].astype(str)
            out += ["**By sweep level**", "", block(g2, "lvl"), ""]
        fc = g[g.get("false_confidence", False) == True]  # noqa: E712
        if len(fc):
            out.append(f"FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): "
                       + ", ".join(f"{r.id} [{r.arm}] rmse {r.rmse_px:.2f} / true {r.grid_err_px if pd.notna(r.grid_err_px) else 'none'}"
                                   for r in fc.itertuples()) + "\n")
    text = "\n".join(out)
    dst = path.with_name(path.stem + "_summary.md")
    dst.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
