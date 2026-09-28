"""
Run one evaluation round over the cached instances.

    python scripts/eval/run_round.py --round 1 [--config default] [--families F1,F3]
                                     [--set key=value ...] [--arms M1_disk_lightglue]

Writes eval/results/round_<N>[_<config>].csv (one row per instance x arm) and a
matching _meta.json (machine, git commit, pipeline config). Earlier result files
are never overwritten: a clash is an error.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time

import cv2
import numpy as np

from common import (
    ARMS, CACHE_DIR, RESULTS_DIR, RUNS_DIR, TILES_DIR, PipelineConfig,
    corner_err_px, heldout_px, machine_info, map_disagreement_px,
    ncc_before_after, run_arm, save_json, uniformity, verdict_gt, verdict_real,
)

COLUMNS = [
    "round", "config", "id", "family", "provenance", "split", "loc_index",
    "level_name", "level", "source", "status", "terrain", "texture", "arm",
    "detector", "n_kp_a", "n_kp_b", "n_matches", "n_inliers", "inlier_ratio",
    "degenerate", "rmse_px", "median_px", "p90_px", "grid_err_px", "corner_err_px",
    "heldout_px", "agree_px", "ncc_before", "ncc_after", "unif_cells", "unif_hull",
    "t_pre_ms", "t_match_ms", "t_fit_ms", "t_total_ms", "verdict", "confirmed_by",
    "subpixel", "uniform", "false_confidence", "gsd_ratio", "tmc_px", "footprint_m",
    "shadow_a", "shadow_b", "coreg_used_prior", "coreg_shift_along_m",
]


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=str(CACHE_DIR.parent.parent), text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def terrain_classes(instances):
    """Texture tertiles per family, over every evaluated location (pre-reg 0.5)."""
    out = {}
    fams = {r["family"] for r in instances}
    for fam in fams:
        tex = [r["texture"] for r in instances if r["family"] == fam and r["status"] == "OK"]
        if len(tex) < 3:
            continue
        q1, q2 = np.quantile(tex, [1 / 3, 2 / 3])
        out[fam] = (float(q1), float(q2))
    return out


def parse_set(pairs):
    cfg = PipelineConfig()
    for kv in pairs or []:
        k, v = kv.split("=", 1)
        cur = getattr(cfg, k)
        if isinstance(cur, bool):
            v = v.lower() in ("1", "true", "yes")
        else:
            v = type(cur)(v)
        setattr(cfg, k, v)
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--config", default="default")
    ap.add_argument("--families", default="")
    ap.add_argument("--ids", default="", help="comma-separated instance ids")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--set", nargs="*", help="PipelineConfig overrides, key=value")
    args = ap.parse_args()

    cfg = parse_set(args.set)
    arms = args.arms.split(",")
    tag = f"round_{args.round}" + ("" if args.config == "default" else f"_{args.config}")
    out_csv = RESULTS_DIR / f"{tag}.csv"
    if out_csv.exists():
        raise SystemExit(f"{out_csv} exists; results are never overwritten")

    instances = json.loads((CACHE_DIR / "instances.json").read_text(encoding="utf-8"))["instances"]
    tertiles = terrain_classes(instances)   # fixed from all instances, before filtering
    if args.families:
        fams = set(args.families.split(","))
        instances = [r for r in instances if r["family"][:2] in fams]
    if args.ids:
        ids = set(args.ids.split(","))
        instances = [r for r in instances if r["id"] in ids]

    run_dir = RUNS_DIR / tag
    run_dir.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    meta = {"round": args.round, "config": args.config, "pipeline": cfg.as_dict(),
            "arms": arms, "git_commit": git_commit(), "machine": machine_info(),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "terrain_tertiles": tertiles, "n_instances": len(instances)}

    rows = []
    t_start = time.perf_counter()
    for n, inst in enumerate(instances, 1):
        base = {
            "round": args.round, "config": args.config, "id": inst["id"],
            "family": inst["family"], "provenance": inst["provenance"],
            "split": inst["split"], "loc_index": inst["loc_index"],
            "level_name": inst.get("level_name", ""), "level": inst.get("level", ""),
            "source": inst.get("source", ""), "status": inst["status"],
            "texture": inst.get("texture"),
            "gsd_ratio": inst.get("gsd_ratio"), "tmc_px": inst.get("tmc_px"),
            "footprint_m": inst.get("footprint_m"),
            "shadow_a": inst.get("shadow_a"), "shadow_b": inst.get("shadow_b"),
            "coreg_used_prior": (inst.get("coreg") or {}).get("used_prior"),
            "coreg_shift_along_m": (inst.get("coreg") or {}).get("shift_m_along"),
        }
        tt = tertiles.get(inst["family"])
        if tt and inst.get("texture") is not None and inst["status"] == "OK":
            t = inst["texture"]
            base["terrain"] = "low" if t < tt[0] else ("mid" if t < tt[1] else "high")

        if inst["status"] != "OK":
            for arm in arms:
                rows.append({**base, "arm": arm,
                             "verdict": "NO_LOCK" if inst["status"] == "NO_LOCK"
                             else f"EXCLUDED_{inst['status']}"})
            continue

        a8 = cv2.imread(str(TILES_DIR / inst["tile_a"]), cv2.IMREAD_GRAYSCALE)
        b8 = cv2.imread(str(TILES_DIR / inst["tile_b"]), cv2.IMREAD_GRAYSCALE)
        H_true = np.array(inst["H_true"]) if inst.get("H_true") else None

        runs = {arm: run_arm(a8, b8, arm, cfg) for arm in arms}
        for arm, r in runs.items():
            np.savez_compressed(run_dir / f"{inst['id']}__{arm}.npz",
                                H=r.H if r.H is not None else np.zeros((0,)),
                                pts_a=r.pts_a, pts_b=r.pts_b, residuals=r.residuals)

        for arm, r in runs.items():
            res = r.residuals
            row = {**base, "arm": arm, "detector": r.detector,
                   "n_kp_a": r.n_kp_a, "n_kp_b": r.n_kp_b, "n_matches": r.n_matches,
                   "n_inliers": r.n_inliers,
                   "inlier_ratio": round(r.n_inliers / r.n_matches, 4) if r.n_matches else 0.0,
                   "degenerate": r.degenerate,
                   "rmse_px": round(float(np.sqrt(np.mean(res ** 2))), 4) if res.size else None,
                   "median_px": round(float(np.median(res)), 4) if res.size else None,
                   "p90_px": round(float(np.percentile(res, 90)), 4) if res.size else None,
                   "t_pre_ms": r.t_ms["pre"], "t_match_ms": r.t_ms["match"],
                   "t_fit_ms": r.t_ms["fit"], "t_total_ms": r.t_ms["total"]}
            row.update(uniformity(r.pts_a, a8.shape))
            row.update({k: (round(v, 4) if v is not None else None)
                        for k, v in ncc_before_after(a8, b8, r.H).items()})
            has_model = r.H is not None

            if H_true is not None:
                g = map_disagreement_px(r.H, H_true, b8.shape)
                row["grid_err_px"] = round(g, 4) if g is not None else None
                c = corner_err_px(r.H, H_true, a8.shape)
                row["corner_err_px"] = round(c, 4) if c is not None else None
                row["verdict"] = verdict_gt(r.n_inliers, r.degenerate, has_model, g)
                row["subpixel"] = row["verdict"] == "SUCCESS" and g is not None and g < 1.0
                row["false_confidence"] = bool(row["rmse_px"] is not None and row["rmse_px"] < 1.5
                                               and (g is None or g > 10.0) and has_model)
            else:
                ho = heldout_px(r.pts_a, r.pts_b, seed=inst["seed"])
                row["heldout_px"] = round(ho, 4) if ho is not None else None
                others = [o for a, o in runs.items() if a != arm]
                other = others[0] if others else None
                other_usable = bool(other and other.H is not None and other.n_inliers >= 8
                                    and not other.degenerate)
                ag = map_disagreement_px(r.H, other.H, b8.shape) if other_usable else None
                row["agree_px"] = round(ag, 4) if ag is not None else None
                v, by = verdict_real(r.n_inliers, has_model, ho, ag, other_usable,
                                     row["ncc_before"], row["ncc_after"])
                row["verdict"], row["confirmed_by"] = v, by
                row["subpixel"] = v == "SUCCESS" and ho is not None and ho < 1.0
            row["uniform"] = row["unif_cells"] >= 0.75
            rows.append(row)

        el = time.perf_counter() - t_start
        summary = " | ".join(f"{a.split('_')[0]} {rows[-len(runs) + i]['verdict'][:4]} "
                             f"{runs[a].n_inliers}in" for i, a in enumerate(runs))
        print(f"[{n}/{len(instances)} {el:.0f}s] {inst['id']}: {summary}", flush=True)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    meta["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta["wall_s"] = round(time.perf_counter() - t_start, 1)
    save_json(RESULTS_DIR / f"{tag}_meta.json", meta)
    print(f"\n{len(rows)} rows -> {out_csv}")


if __name__ == "__main__":
    main()
