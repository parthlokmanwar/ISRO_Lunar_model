"""
The correspondence pipeline.

POST /api/match runs a scenario end to end and returns every stage separately, so
the UI animates real data rather than a scripted sequence. Everything the frontend
draws - keypoints, match lines, the warp, the residual field - comes from here.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import (
    MATCH_CONF_THRESHOLD, MAX_KEYPOINTS, RANSAC_REPROJ_THRESH,
    RESULTS_DIR, SCENES_DIR, STATIC_DIR,
)
from services.feature_matching import match_images
from services.geometric import (
    decompose_homography, error_stats, ground_truth_error,
    ransac_filter, reprojection_errors, warp_image,
)
from services.preprocessing import normalize_for_matching
from services.scenarios import get_scenario, load_catalog

router = APIRouter(prefix="/api", tags=["match"])


class MatchRequest(BaseModel):
    scenario_id: str
    detector: str = Field("auto", pattern="^(auto|disk|sift)$")
    ransac_method: str = Field("MAGSAC", pattern="^(MAGSAC|RANSAC|LMEDS|RHO)$")
    ransac_threshold: float = Field(RANSAC_REPROJ_THRESH, ge=0.5, le=20.0)
    clahe_clip_limit: float = Field(3.0, ge=0.5, le=12.0)
    suppress_shadows: bool = True
    max_keypoints: int = Field(MAX_KEYPOINTS, ge=128, le=8192)
    confidence_threshold: float = Field(MATCH_CONF_THRESHOLD, ge=0.0, le=0.95)


def _scene_path(url: str) -> Path:
    """Map a /static/scenes/<name>.png URL back onto disk."""
    name = Path(url).name
    path = (SCENES_DIR / name).resolve()
    if not str(path).startswith(str(SCENES_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid scene path")
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Scene image '{name}' is missing. Run: python scripts/build_scenarios.py",
        )
    return path


def _load_gray(url: str) -> np.ndarray:
    img = cv2.imread(str(_scene_path(url)), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise HTTPException(status_code=500, detail=f"Could not decode {url}")
    return img


def _save_static(img: np.ndarray, name: str, version: str) -> str:
    """
    Write a per-run image and return its URL, versioned by run.

    The file name is fixed per scenario so the static folder does not grow with
    every run, but the URL carries the run id. Without it the browser and the
    stage's texture cache both kept serving the previous run's image under the
    same URL, so changing CLAHE and re-running showed stale normalisation.
    """
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(STATIC_DIR / name), img)
    return f"/static/{name}?v={version}"


# Runs are persisted for export and analytics. Each one is a few hundred KB of
# JSON plus a density PNG, and nothing removed them, so the static folder grew
# without bound. Keep the most recent runs only.
MAX_STORED_RUNS = 60


def _prune_runs(keep: int = MAX_STORED_RUNS) -> None:
    runs = sorted(RESULTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in runs[keep:]:
        old.unlink(missing_ok=True)
        (STATIC_DIR / f"density_{old.stem}.png").unlink(missing_ok=True)


def _overlay(warped: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    False-colour overlay: warped A in the red channel, B in green and blue.

    Where registration is correct the two coincide and the result reads as
    grey; wherever it is off, the edges fringe red against cyan. That is far
    easier to judge by eye than a 50/50 blend, which hides misalignment in a
    uniform haze.
    """
    h, w = target.shape[:2]
    if warped.shape[:2] != (h, w):
        warped = cv2.resize(warped, (w, h), interpolation=cv2.INTER_LINEAR)
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[:, :, 2] = warped        # red
    out[:, :, 1] = target        # green
    out[:, :, 0] = target        # blue
    return out


@router.post("/match")
async def run_match(req: MatchRequest) -> Dict:
    scenario = get_scenario(req.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Unknown scenario '{req.scenario_id}'")

    stages: List[Dict] = []
    t_start = time.perf_counter()
    result_id = f"{req.scenario_id}_{uuid.uuid4().hex[:8]}"

    # -- Stage 1: acquisition ------------------------------------------------ #
    t0 = time.perf_counter()
    raw_a = _load_gray(scenario["image_a"]["url"])
    raw_b = _load_gray(scenario["image_b"]["url"])
    if raw_b.shape != raw_a.shape:
        raw_b = cv2.resize(raw_b, (raw_a.shape[1], raw_a.shape[0]),
                           interpolation=cv2.INTER_CUBIC)
    stages.append({
        "key": "acquire",
        "label": "Acquisition",
        "detail": (
            f"{scenario['image_a']['sensor']} and {scenario['image_b']['sensor']} "
            f"tiles at {raw_a.shape[1]}x{raw_a.shape[0]} px"
        ),
        "ms": round((time.perf_counter() - t0) * 1000, 1),
        "data": {
            "width": int(raw_a.shape[1]),
            "height": int(raw_a.shape[0]),
            "url_a": scenario["image_a"]["url"],
            "url_b": scenario["image_b"]["url"],
            "coreg": scenario.get("coreg"),
        },
    })

    # -- Stage 2: normalisation --------------------------------------------- #
    t0 = time.perf_counter()
    proc_a, stats_a = normalize_for_matching(
        raw_a, clip_limit=req.clahe_clip_limit, suppress_shadows=req.suppress_shadows)
    proc_b, stats_b = normalize_for_matching(
        raw_b, clip_limit=req.clahe_clip_limit, suppress_shadows=req.suppress_shadows)
    url_pa = _save_static(proc_a, f"proc_{req.scenario_id}_a.png", result_id)
    url_pb = _save_static(proc_b, f"proc_{req.scenario_id}_b.png", result_id)
    stages.append({
        "key": "normalize",
        "label": "Illumination normalisation",
        "detail": (
            f"CLAHE clip {req.clahe_clip_limit:g}; shadow fraction "
            f"{stats_a['shadow_fraction']:.0%} / {stats_b['shadow_fraction']:.0%}"
        ),
        "ms": round((time.perf_counter() - t0) * 1000, 1),
        "data": {"url_a": url_pa, "url_b": url_pb, "stats_a": stats_a, "stats_b": stats_b},
    })

    # -- Stages 3 and 4: detection and matching ------------------------------ #
    t0 = time.perf_counter()
    mr = match_images(
        proc_a, proc_b,
        detector=req.detector,
        max_keypoints=req.max_keypoints,
        conf_threshold=req.confidence_threshold,
    )
    match_ms = (time.perf_counter() - t0) * 1000

    stages.append({
        "key": "detect",
        "label": "Feature detection",
        "detail": f"{mr.detector}: {len(mr.keypoints_a)} and {len(mr.keypoints_b)} keypoints",
        "ms": round(mr.timings_ms.get("detect", match_ms * 0.7), 1),
        "data": {
            "detector": mr.detector,
            "count_a": int(len(mr.keypoints_a)),
            "count_b": int(len(mr.keypoints_b)),
        },
    })
    stages.append({
        "key": "match",
        "label": "Descriptor matching",
        "detail": f"{mr.matcher}: {len(mr.matches)} putative correspondences",
        "ms": round(mr.timings_ms.get("match", match_ms * 0.3), 1),
        "data": {"matcher": mr.matcher, "count": len(mr.matches), "notes": mr.notes},
    })

    if not mr.matches:
        raise HTTPException(
            status_code=422,
            detail=("No correspondences found. These tiles may not overlap, or the "
                    "illumination difference may be beyond what this configuration handles."),
        )

    # -- Stage 5: robust fitting -------------------------------------------- #
    t0 = time.perf_counter()
    inliers, H, diag = ransac_filter(
        mr.keypoints_a, mr.keypoints_b, mr.matches,
        method=req.ransac_method, reproj_thresh=req.ransac_threshold,
    )
    inlier_keys = {(m["idx_a"], m["idx_b"]) for m in inliers}
    all_matches = [
        dict(m, inlier=(m["idx_a"], m["idx_b"]) in inlier_keys) for m in mr.matches
    ]
    stages.append({
        "key": "ransac",
        "label": "Robust model fitting",
        "detail": (f"{req.ransac_method}: {len(mr.matches)} to {len(inliers)} inliers"
                   + (f" - {diag['warning']}" if diag.get("warning") else "")),
        "ms": round((time.perf_counter() - t0) * 1000, 1),
        "data": diag,
    })

    # -- Stage 6: alignment -------------------------------------------------- #
    t0 = time.perf_counter()
    overlay_url = warped_url = None
    if H is not None:
        warped = warp_image(raw_a, H, raw_b.shape[:2])
        overlay_url = _save_static(_overlay(warped, raw_b),
                                   f"overlay_{req.scenario_id}.png", result_id)
        warped_url = _save_static(warped, f"warped_{req.scenario_id}.png", result_id)
    stages.append({
        "key": "align",
        "label": "Alignment",
        "detail": ("Homography applied" if H is not None
                   else "No homography could be estimated"),
        "ms": round((time.perf_counter() - t0) * 1000, 1),
        "data": {"overlay_url": overlay_url, "warped_url": warped_url},
    })

    # -- Metrics ------------------------------------------------------------- #
    errors = reprojection_errors(mr.keypoints_a, mr.keypoints_b, inliers, H)
    stats = error_stats(errors)
    gsd = scenario["image_a"].get("gsd_m") or 0.0

    gt = scenario.get("ground_truth_homography")
    gt_error = ground_truth_error(H, np.array(gt) if gt else None, raw_a.shape) if gt else None

    metrics = {
        "num_keypoints_a": int(len(mr.keypoints_a)),
        "num_keypoints_b": int(len(mr.keypoints_b)),
        "num_matches": len(mr.matches),
        "num_inliers": len(inliers),
        "inlier_ratio": round(len(inliers) / max(len(mr.matches), 1), 4),
        "rmse_px": round(stats["rmse"], 4),
        "median_error_px": round(stats["median"], 4),
        "p90_error_px": round(stats["p90"], 4),
        "max_error_px": round(stats["max"], 4),
        "rmse_m": round(stats["rmse"] * gsd, 4) if gsd else None,
        "gsd_m": gsd,
        "degenerate": bool(diag.get("degenerate")),
        "warning": diag.get("warning", ""),
        "total_ms": round((time.perf_counter() - t_start) * 1000, 1),
    }

    payload = {
        "result_id": result_id,
        "scenario_id": req.scenario_id,
        "scenario": {
            "title": scenario["title"],
            "provenance": scenario["provenance"],
            "challenge": scenario.get("challenge", ""),
            "notes": scenario.get("notes", ""),
        },
        "settings": req.model_dump(),
        "image": {
            "width": int(raw_a.shape[1]),
            "height": int(raw_a.shape[0]),
            "raw_url_a": scenario["image_a"]["url"],
            "raw_url_b": scenario["image_b"]["url"],
            "proc_url_a": url_pa,
            "proc_url_b": url_pb,
            "overlay_url": overlay_url,
            "warped_url": warped_url,
        },
        "sun_angle_a": {
            "elevation": scenario["image_a"].get("sun_elevation"),
            "azimuth": scenario["image_a"].get("sun_azimuth"),
        },
        "sun_angle_b": {
            "elevation": scenario["image_b"].get("sun_elevation"),
            "azimuth": scenario["image_b"].get("sun_azimuth"),
        },
        "keypoints_a": mr.keypoints_a.round(2).tolist(),
        "keypoints_b": mr.keypoints_b.round(2).tolist(),
        "matches": all_matches,
        "inlier_matches": inliers,
        "residuals": [round(float(e), 4) for e in errors],
        "homography": H.tolist() if H is not None else None,
        "homography_decomposed": decompose_homography(H),
        "ground_truth_homography": gt,
        "ground_truth_error": gt_error,
        "metrics": metrics,
        "stages": stages,
    }

    # Persist so the CSV export has something real to read. The previous export
    # endpoint read a results file that nothing ever wrote, so it always 404'd.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"{result_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    _prune_runs()

    return payload
