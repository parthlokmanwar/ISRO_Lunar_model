"""
Robust homography estimation and the metrics derived from it.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from config import RANSAC_CONFIDENCE, RANSAC_MAX_ITERS, RANSAC_REPROJ_THRESH

RANSAC_METHODS = {
    "MAGSAC": getattr(cv2, "USAC_MAGSAC", cv2.RANSAC),
    "RANSAC": cv2.RANSAC,
    "LMEDS": cv2.LMEDS,
    "RHO": getattr(cv2, "RHO", cv2.RANSAC),
}


def _gather(kpts_a: np.ndarray, kpts_b: np.ndarray,
            matches: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    pts_a = np.float32([kpts_a[m["idx_a"]] for m in matches]).reshape(-1, 1, 2)
    pts_b = np.float32([kpts_b[m["idx_b"]] for m in matches]).reshape(-1, 1, 2)
    return pts_a, pts_b


def ransac_filter(
    kpts_a: np.ndarray,
    kpts_b: np.ndarray,
    matches: List[Dict],
    method: str = "MAGSAC",
    reproj_thresh: float = RANSAC_REPROJ_THRESH,
) -> Tuple[List[Dict], Optional[np.ndarray], Dict]:
    """
    Fit a homography and split the matches into inliers and outliers.

    Returns (inlier_matches, H, diagnostics). The diagnostics carry a
    `degenerate` flag: with four correspondences a homography fits exactly by
    construction, so a "perfect" RMSE at that point means nothing at all. The old
    pipeline reported exactly that number (0.001 px) as a headline result.
    """
    diag: Dict = {
        "method": method,
        "reproj_threshold": reproj_thresh,
        "degenerate": False,
        "warning": "",
    }

    if len(matches) < 4:
        diag["warning"] = f"only {len(matches)} matches; a homography needs at least 4"
        return [], None, diag

    pts_a, pts_b = _gather(kpts_a, kpts_b, matches)
    cv_method = RANSAC_METHODS.get(method, RANSAC_METHODS["MAGSAC"])

    try:
        H, mask = cv2.findHomography(
            pts_a, pts_b, cv_method, reproj_thresh,
            maxIters=RANSAC_MAX_ITERS, confidence=RANSAC_CONFIDENCE,
        )
    except cv2.error as exc:
        diag["warning"] = f"homography estimation failed: {exc}"
        return [], None, diag

    if H is None or mask is None:
        diag["warning"] = "no consensus set found"
        return [], None, diag

    flags = mask.ravel().astype(bool)
    inliers = [dict(m, inlier=True) for m, keep in zip(matches, flags) if keep]

    if len(inliers) <= 4:
        diag["degenerate"] = True
        diag["warning"] = (
            f"{len(inliers)} inliers is at or below the 4-point minimum, so the fit "
            "is exact by construction and its residual carries no information"
        )

    return inliers, H, diag


def reprojection_errors(kpts_a: np.ndarray, kpts_b: np.ndarray,
                        matches: List[Dict], H: Optional[np.ndarray]) -> np.ndarray:
    """Per-match reprojection distance in pixels."""
    if H is None or not matches:
        return np.zeros(0, dtype=np.float32)
    pts_a, pts_b = _gather(kpts_a, kpts_b, matches)
    projected = cv2.perspectiveTransform(pts_a, H.astype(np.float64))
    return np.linalg.norm(projected - pts_b, axis=2).ravel()


def error_stats(errors: np.ndarray) -> Dict[str, float]:
    """
    RMSE plus the numbers that make it interpretable.

    RMSE alone is easy to misread: a handful of bad correspondences pull it up,
    and too few points make it meaninglessly small. Median and the 90th percentile
    say what the typical and worst-case residuals actually are.
    """
    if errors.size == 0:
        return {"rmse": 0.0, "median": 0.0, "p90": 0.0, "max": 0.0, "count": 0}
    return {
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        "median": float(np.median(errors)),
        "p90": float(np.percentile(errors, 90)),
        "max": float(errors.max()),
        "count": int(errors.size),
    }


def warp_image(img: np.ndarray, H: np.ndarray,
               target_shape: Tuple[int, int]) -> np.ndarray:
    """Warp `img` into the frame of the target using H."""
    if H is None:
        return img
    h, w = target_shape[:2]
    return cv2.warpPerspective(img, H.astype(np.float64), (w, h),
                               flags=cv2.INTER_LINEAR)


def decompose_homography(H: Optional[np.ndarray]) -> Optional[Dict[str, float]]:
    """
    Read a homography as physically meaningful quantities.

    Judges and reviewers can interpret "rotated 2.4 degrees, scaled 3 percent,
    shifted 22 px" far more readily than a 3x3 of floats, and an implausible
    decomposition is an immediate red flag that the fit is wrong.
    """
    if H is None:
        return None
    H = np.asarray(H, dtype=np.float64)
    if abs(H[2, 2]) > 1e-12:
        H = H / H[2, 2]
    a, b = H[0, 0], H[0, 1]
    c, d = H[1, 0], H[1, 1]
    scale_x = float(np.hypot(a, c))
    scale_y = float(np.hypot(b, d))
    rotation = float(np.degrees(np.arctan2(c, a)))
    shear = float(np.degrees(np.arctan2(a * b + c * d, a * d - b * c)))
    return {
        "translation_x": float(H[0, 2]),
        "translation_y": float(H[1, 2]),
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_mean": float((scale_x + scale_y) / 2.0),
        "rotation_deg": rotation,
        "shear_deg": shear,
        "perspective_x": float(H[2, 0]),
        "perspective_y": float(H[2, 1]),
    }


def ground_truth_error(H_est: Optional[np.ndarray],
                       H_true: Optional[np.ndarray],
                       shape: Tuple[int, int]) -> Optional[Dict[str, float]]:
    """
    True geometric error against a known transform, where one exists.

    Reprojection RMSE only measures whether the inliers agree with each other. A
    homography fitted confidently to the wrong correspondences, which repeated
    crater terrain invites, can post an excellent RMSE while being badly wrong.
    Corner error against the transform we actually applied cannot be gamed that
    way, which is why the derived scenarios are worth having.
    """
    if H_est is None or H_true is None:
        return None
    h, w = shape[:2]
    corners = np.float32(
        [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]
    ).reshape(-1, 1, 2)
    try:
        est = cv2.perspectiveTransform(corners, np.asarray(H_est, dtype=np.float64))
        true = cv2.perspectiveTransform(corners, np.asarray(H_true, dtype=np.float64))
    except cv2.error:
        return None
    per_corner = np.linalg.norm(est - true, axis=2).ravel()
    return {
        "mean_corner_error_px": float(per_corner.mean()),
        "max_corner_error_px": float(per_corner.max()),
        "per_corner_px": [float(v) for v in per_corner],
    }
