"""
Derived products from a completed match: keypoint density, terrain suitability,
and export.

Every number here is computed from the run it names. The previous version accepted
keypoints in the request body and let the client decide the image size, which meant
the "landing readiness" score reflected whatever the frontend chose to send.
"""
from __future__ import annotations

import csv
import io
import json
import re
from typing import Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from config import RESULTS_DIR, STATIC_DIR

router = APIRouter(prefix="/api", tags=["analytics"])

_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


def _load_result(result_id: str) -> Dict:
    """
    Load a stored run.

    The id is validated against a strict pattern before touching the filesystem,
    and the resolved path is confirmed to sit inside the results directory. The
    old export endpoint interpolated the id straight into a path.
    """
    if not _SAFE_ID.match(result_id):
        raise HTTPException(status_code=400, detail="Invalid result id")
    path = (RESULTS_DIR / f"{result_id}.json").resolve()
    if not str(path).startswith(str(RESULTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid result id")
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No stored result '{result_id}'. Run the pipeline first.",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _matched_points(result: Dict, inliers_only: bool = True) -> np.ndarray:
    """Image-A coordinates of the matches, as an (N, 2) array."""
    kps = result.get("keypoints_a") or []
    matches = result.get("inlier_matches" if inliers_only else "matches") or []
    pts = [kps[m["idx_a"]] for m in matches if m["idx_a"] < len(kps)]
    return np.asarray(pts, dtype=np.float32).reshape(-1, 2)


def _density_field(pts: np.ndarray, weights: np.ndarray,
                   w: int, h: int, sigma_frac: float = 0.04) -> np.ndarray:
    """Confidence-weighted keypoint density, normalised to [0, 1]."""
    field = np.zeros((h, w), dtype=np.float32)
    for (x, y), c in zip(pts, weights):
        xi = int(np.clip(x, 0, w - 1))
        yi = int(np.clip(y, 0, h - 1))
        field[yi, xi] += float(c)
    sigma = max(3.0, sigma_frac * max(w, h))
    field = cv2.GaussianBlur(field, (0, 0), sigma)
    peak = float(field.max())
    return field / peak if peak > 0 else field


def _uniformity(pts: np.ndarray, w: int, h: int, grid: int = 4) -> float:
    """
    How evenly the correspondences cover the frame, in [0, 1].

    A homography fitted from points clustered in one corner extrapolates badly
    across the rest of the image, so coverage is a real quality signal and not
    just decoration.
    """
    if len(pts) == 0:
        return 0.0
    cells = np.zeros((grid, grid), dtype=np.float32)
    for x, y in pts:
        ci = min(int(x / max(w, 1) * grid), grid - 1)
        ri = min(int(y / max(h, 1) * grid), grid - 1)
        cells[ri, ci] += 1
    expected = len(pts) / float(grid * grid)
    return float(np.minimum(cells / max(expected, 1e-6), 1.0).mean())


@router.get("/analytics/{result_id}")
async def analytics(result_id: str, grid: int = Query(8, ge=2, le=16)) -> Dict:
    """
    Coverage and terrain-suitability analysis for one completed run.

    The suitability score is deliberately described as what it is: a measure of
    how densely and evenly the terrain produced reliable correspondences. Dense,
    well-distributed matches indicate texture that registers consistently. That
    is a useful proxy for a well-characterised surface, but it is not a slope or
    boulder measurement, and calling it a landing decision would overstate it.
    """
    result = _load_result(result_id)
    w = int(result["image"]["width"])
    h = int(result["image"]["height"])

    pts = _matched_points(result, inliers_only=True)
    if len(pts) == 0:
        raise HTTPException(status_code=422,
                            detail="This run produced no inliers to analyse")
    confs = np.array([m.get("confidence", 0.5)
                      for m in result.get("inlier_matches", [])], dtype=np.float32)
    if len(confs) != len(pts):
        confs = np.full(len(pts), 0.5, dtype=np.float32)

    field = _density_field(pts, confs, w, h)
    uniformity = _uniformity(pts, w, h)

    cell_w, cell_h = max(1, w // grid), max(1, h // grid)
    cells: List[Dict] = []
    for r in range(grid):
        for c in range(grid):
            patch = field[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            score = float(patch.mean()) if patch.size else 0.0
            cells.append({
                "row": r, "col": c,
                "x": c * cell_w, "y": r * cell_h, "w": cell_w, "h": cell_h,
                "density": round(score, 4),
                "class": "high" if score > 0.40 else ("medium" if score > 0.12 else "low"),
            })

    heat = cv2.applyColorMap((field * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    heat_name = f"density_{result_id}.png"
    cv2.imwrite(str(STATIC_DIR / heat_name), heat)

    high = sum(1 for c in cells if c["class"] == "high")
    coverage = high / float(len(cells))

    return {
        "result_id": result_id,
        "grid": grid,
        "cells": cells,
        "density_url": f"/static/{heat_name}",
        "uniformity": round(uniformity, 4),
        "uniformity_label": (
            "Excellent" if uniformity > 0.70 else
            "Good" if uniformity > 0.50 else
            "Fair" if uniformity > 0.30 else "Poor"
        ),
        "coverage": round(coverage, 4),
        "high_cells": high,
        "medium_cells": sum(1 for c in cells if c["class"] == "medium"),
        "low_cells": sum(1 for c in cells if c["class"] == "low"),
        "interpretation": (
            "Density of reliable correspondences per cell. High-density terrain "
            "registers consistently across observations; low-density terrain is "
            "either featureless or unstable between viewing conditions. This is a "
            "registration-quality map, not a slope or boulder hazard assessment."
        ),
    }


@router.get("/export/csv/{result_id}")
async def export_csv(result_id: str):
    """Every correspondence from a run, with its residual, as CSV."""
    result = _load_result(result_id)
    kps_a = result.get("keypoints_a") or []
    kps_b = result.get("keypoints_b") or []
    matches = result.get("matches") or []

    residual_by_key = {}
    for m, r in zip(result.get("inlier_matches", []), result.get("residuals", [])):
        residual_by_key[(m["idx_a"], m["idx_b"])] = r

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["match_index", "x_a", "y_a", "x_b", "y_b",
                     "confidence", "is_inlier", "residual_px"])
    for i, m in enumerate(matches):
        ia, ib = m["idx_a"], m["idx_b"]
        xa, ya = kps_a[ia] if ia < len(kps_a) else (None, None)
        xb, yb = kps_b[ib] if ib < len(kps_b) else (None, None)
        writer.writerow([
            i, xa, ya, xb, yb,
            round(float(m.get("confidence", 0.0)), 4),
            bool(m.get("inlier")),
            residual_by_key.get((ia, ib), ""),
        ])

    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="matches_{result_id}.csv"'},
    )


@router.get("/export/json/{result_id}")
async def export_json(result_id: str):
    """The complete stored run, including the homography and every stage timing."""
    return _load_result(result_id)
