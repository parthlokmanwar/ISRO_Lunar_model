"""
Figures for a round, written to eval/figures/round_<N>/.

    python scripts/eval/figures.py eval/results/round_1.csv

- sweep_<family>.png : per sweep level, each arm's median primary error (log
  scale, with every instance as a dot) and SUCCESS rate.
- rmse_vs_truth.png  : reprojection RMSE against true error, every GT row.
- pair_<id>.png      : inlier correspondences for chosen instances (--pairs).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import CACHE_DIR, FIGURES_DIR, RUNS_DIR, TILES_DIR  # noqa: E402

ARM_STYLE = {"M1_disk_lightglue": ("#1f6f8b", "DISK + LightGlue"),
             "M2_sift_flann": ("#c8553d", "SIFT + FLANN")}
LEVEL_LABEL = {"footprint_px": "ground footprint (OHRC px; TMC px = /14.5)",
               "delta_azimuth_deg": "sun azimuth difference (deg)",
               "rot": "rotation (deg)", "zoom": "zoom factor"}


def load(path):
    df = pd.read_csv(path)
    for c in ("grid_err_px", "rmse_px", "n_inliers", "level"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def sweep(df, fam, level_name, out):
    g = df[(df.family == fam) & (df.level_name == level_name) & (df.status == "OK")]
    if g.empty:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
    levels = sorted(g.level.unique())
    x = np.arange(len(levels))
    for k, (arm, (col, name)) in enumerate(ARM_STYLE.items()):
        a = g[g.arm == arm]
        err = [a[a.level == lv].grid_err_px.fillna(1e4).clip(upper=1e4) for lv in levels]
        off = (k - 0.5) * 0.18
        for i, e in enumerate(err):
            ax1.scatter(np.full(len(e), x[i] + off), e, s=14, color=col, alpha=0.55)
        ax1.plot(x + off, [np.median(e) for e in err], "-o", color=col, label=name)
        succ = [(a[a.level == lv].verdict == "SUCCESS").mean() * 100 for lv in levels]
        ax2.plot(x, succ, "-o", color=col, label=name)
    ax1.set_yscale("log")
    ax1.axhline(1.0, color="#555", ls=":", lw=1)
    ax1.axhline(2.0, color="#555", ls="--", lw=1)
    ax1.text(x[-1] + 0.3, 1.0, "sub-pixel", va="center", fontsize=8, color="#555")
    ax1.text(x[-1] + 0.3, 2.0, "SUCCESS", va="center", fontsize=8, color="#555")
    ax1.set_ylabel("true registration error (source px)\nno model plotted at 10^4")
    ax2.set_ylabel("SUCCESS rate (%)")
    ax2.set_ylim(-5, 105)
    for ax in (ax1, ax2):
        ax.set_xticks(x, [f"{lv:g}" for lv in levels])
        ax.set_xlabel(LEVEL_LABEL.get(level_name, level_name))
        ax.grid(alpha=0.25)
    ax2.legend(fontsize=8, loc="lower left")
    fig.suptitle(f"{fam} — {len(g) // 2} instances", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / f"sweep_{fam}_{level_name}.png", dpi=140)
    plt.close(fig)


def rmse_vs_truth(df, out):
    g = df[df.grid_err_px.notna() & df.rmse_px.notna()]
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    for arm, (col, name) in ARM_STYLE.items():
        a = g[g.arm == arm]
        ax.scatter(a.rmse_px, a.grid_err_px, s=16, color=col, alpha=0.7, label=name)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axhline(2.0, color="#555", ls="--", lw=1)
    ax.set_xlabel("reprojection RMSE of inliers (px) — what most pipelines report")
    ax.set_ylabel("true registration error (px)")
    ax.set_title("RMSE vs the truth, every instance with a known answer", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "rmse_vs_truth.png", dpi=140)
    plt.close(fig)


def pair(inst_id, tag, out, arms=("M1_disk_lightglue", "M2_sift_flann")):
    a = cv2.imread(str(TILES_DIR / f"{inst_id}_a.png"), 0)
    b = cv2.imread(str(TILES_DIR / f"{inst_id}_b.png"), 0)
    if b.shape != a.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    fig, axes = plt.subplots(1, len(arms), figsize=(6.2 * len(arms), 3.6))
    for ax, arm in zip(np.atleast_1d(axes), arms):
        f = RUNS_DIR / tag / f"{inst_id}__{arm}.npz"
        canvas = np.hstack([a, np.full((a.shape[0], 16), 255, np.uint8), b])
        ax.imshow(canvas, cmap="gray")
        if f.exists():
            d = np.load(f)
            pa, pb = d["pts_a"], d["pts_b"]
            off = a.shape[1] + 16
            for (xa, ya), (xb, yb) in zip(pa, pb):
                ax.plot([xa, xb + off], [ya, yb], "-", color=ARM_STYLE[arm][0], lw=0.5, alpha=0.7)
            ax.set_title(f"{ARM_STYLE[arm][1]}: {len(pa)} inliers", fontsize=9)
        ax.axis("off")
    fig.suptitle(inst_id, fontsize=9)
    fig.tight_layout()
    fig.savefig(out / f"pair_{inst_id}.png", dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--pairs", default="")
    args = ap.parse_args()
    path = Path(args.csv)
    tag = path.stem
    out = FIGURES_DIR / tag
    out.mkdir(parents=True, exist_ok=True)
    df = load(path)
    for fam, lvl in (("F3_scale_footprint", "footprint_px"),
                     ("F4_illum_azimuth", "delta_azimuth_deg"),
                     ("F6_viewpoint", "rot"), ("F6_viewpoint", "zoom")):
        sweep(df, fam, lvl, out)
    rmse_vs_truth(df, out)
    for pid in filter(None, args.pairs.split(",")):
        pair(pid, tag, out)
    print("figures ->", out)


if __name__ == "__main__":
    main()
