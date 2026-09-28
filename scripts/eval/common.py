"""
Shared pieces of the evaluation harness.

The pipeline here is the production one - the same service functions, in the
same order, with the same defaults as POST /api/match - so a number measured
here is a number about the app, not about a lookalike. Metric definitions
follow the pre-registration in docs/EXPERIMENT_LOG.md section 0.
"""
from __future__ import annotations

import json
import platform
import sys
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from config import (  # noqa: E402
    CLAHE_CLIP_LIMIT, MATCH_CONF_THRESHOLD, MAX_KEYPOINTS, RANSAC_REPROJ_THRESH,
)
from services.feature_matching import match_images  # noqa: E402
from services.geometric import error_stats, ransac_filter, reprojection_errors  # noqa: E402
from services.preprocessing import normalize_for_matching  # noqa: E402

EVAL_DIR = ROOT / "eval"
CACHE_DIR = EVAL_DIR / "cache"
TILES_DIR = CACHE_DIR / "tiles"
RUNS_DIR = CACHE_DIR / "runs"
RESULTS_DIR = EVAL_DIR / "results"
FIGURES_DIR = EVAL_DIR / "figures"

ARMS = {
    # arm id -> (detector argument, expected detector name)
    "M1_disk_lightglue": ("disk", "DISK"),
    "M2_sift_flann": ("sift", "SIFT"),
}


def seed_for(key: str) -> int:
    """Stable per-instance seed, independent of Python's hash randomisation."""
    return zlib.crc32(key.encode("utf-8")) & 0x7FFFFFFF


def machine_info() -> Dict:
    import torch
    import kornia
    return {
        "cpu": platform.processor(),
        "logical_cpus": __import__("os").cpu_count(),
        "torch_threads": torch.get_num_threads(),
        "cuda": bool(torch.cuda.is_available()),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "kornia": kornia.__version__,
        "opencv": cv2.__version__,
        "numpy": np.__version__,
    }


# --------------------------------------------------------------------------- #
# Pipeline                                                                      #
# --------------------------------------------------------------------------- #
@dataclass
class PipelineConfig:
    """The knobs of the production pipeline. Defaults = production defaults."""

    clahe_clip: float = CLAHE_CLIP_LIMIT
    suppress_shadows: bool = True
    max_keypoints: int = MAX_KEYPOINTS
    conf_threshold: float = MATCH_CONF_THRESHOLD
    ransac_method: str = "MAGSAC"
    ransac_threshold: float = RANSAC_REPROJ_THRESH
    preprocess: str = "clahe"

    def as_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class ArmRun:
    arm: str
    detector: str
    H: Optional[np.ndarray]
    pts_a: np.ndarray            # inlier points in A
    pts_b: np.ndarray            # inlier points in B
    n_kp_a: int
    n_kp_b: int
    n_matches: int
    n_inliers: int
    degenerate: bool
    residuals: np.ndarray
    t_ms: Dict[str, float] = field(default_factory=dict)


def run_arm(a8: np.ndarray, b8: np.ndarray, arm: str, cfg: PipelineConfig) -> ArmRun:
    """One pipeline run, mirroring routers/match.py stage for stage."""
    det_arg, det_expected = ARMS[arm]
    t_all = time.perf_counter()

    if b8.shape != a8.shape:  # the API resizes B onto A's grid
        b8 = cv2.resize(b8, (a8.shape[1], a8.shape[0]), interpolation=cv2.INTER_CUBIC)

    t0 = time.perf_counter()
    pa = preprocess_image(a8, cfg)
    pb = preprocess_image(b8, cfg)
    t_pre = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    mr = match_images(pa, pb, detector=det_arg, max_keypoints=cfg.max_keypoints,
                      conf_threshold=cfg.conf_threshold)
    t_match = (time.perf_counter() - t0) * 1000
    if mr.detector != det_expected:
        raise RuntimeError(f"{arm}: expected {det_expected}, pipeline ran {mr.detector} "
                           f"({'; '.join(mr.notes)})")

    t0 = time.perf_counter()
    inliers, H, diag = ransac_filter(mr.keypoints_a, mr.keypoints_b, mr.matches,
                                     method=cfg.ransac_method,
                                     reproj_thresh=cfg.ransac_threshold)
    t_fit = (time.perf_counter() - t0) * 1000

    idx_a = np.array([m["idx_a"] for m in inliers], dtype=int)
    idx_b = np.array([m["idx_b"] for m in inliers], dtype=int)
    pts_a = mr.keypoints_a[idx_a] if len(idx_a) else np.zeros((0, 2), np.float32)
    pts_b = mr.keypoints_b[idx_b] if len(idx_b) else np.zeros((0, 2), np.float32)

    return ArmRun(
        arm=arm, detector=f"{mr.detector}+{mr.matcher}", H=H,
        pts_a=pts_a, pts_b=pts_b,
        n_kp_a=len(mr.keypoints_a), n_kp_b=len(mr.keypoints_b),
        n_matches=len(mr.matches), n_inliers=len(inliers),
        degenerate=bool(diag.get("degenerate")) or H is None,
        residuals=reprojection_errors(mr.keypoints_a, mr.keypoints_b, inliers, H),
        t_ms={"pre": round(t_pre, 1), "match": round(t_match, 1),
              "fit": round(t_fit, 1),
              "total": round((time.perf_counter() - t_all) * 1000, 1)},
    )


def preprocess_image(img: np.ndarray, cfg: PipelineConfig) -> np.ndarray:
    """Apply one evaluation-only alternative to the production normalizer.

    ``shadow_norm`` divides by a broad Gaussian illumination field before
    CLAHE. It is deliberately simple: the Round A question is whether a
    stronger radiometric correction moves the observed 45-90 degree boundary,
    not whether a new matcher or learned model can be tuned around it.
    """
    if cfg.preprocess != "shadow_norm":
        out, _ = normalize_for_matching(img, clip_limit=cfg.clahe_clip,
                                         suppress_shadows=cfg.suppress_shadows)
        return out
    gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = np.clip(gray, 0, 255).astype(np.uint8)
    field = cv2.GaussianBlur(gray, (0, 0), sigmaX=21, sigmaY=21).astype(np.float32)
    corrected = gray.astype(np.float32) / np.maximum(field, 1.0) * 128.0
    corrected = np.clip(corrected, 0, 255).astype(np.uint8)
    out, _ = normalize_for_matching(corrected, clip_limit=cfg.clahe_clip,
                                    suppress_shadows=False)
    return out


# --------------------------------------------------------------------------- #
# Metrics (pre-registration section 0.3)                                        #
# --------------------------------------------------------------------------- #
def _grid(shape, n: int = 16) -> np.ndarray:
    h, w = shape[:2]
    xs = np.linspace(0, w - 1, n)
    ys = np.linspace(0, h - 1, n)
    g = np.array([[x, y] for y in ys for x in xs], dtype=np.float64)
    return g.reshape(-1, 1, 2)


def _inv_map(H: np.ndarray, q: np.ndarray) -> np.ndarray:
    return cv2.perspectiveTransform(q, np.linalg.inv(np.asarray(H, np.float64)))


def map_disagreement_px(H1, H2, shape_b) -> Optional[float]:
    """
    Mean over a 16x16 grid of reference points q of |H1^-1 q - H2^-1 q|, in
    source pixels. With H2 = H_true this is `grid_err_px`; with H1, H2 from the
    two arms it is `agree_px`.
    """
    if H1 is None or H2 is None:
        return None
    try:
        q = _grid(shape_b)
        d = np.linalg.norm(_inv_map(H1, q) - _inv_map(H2, q), axis=2).ravel()
    except (np.linalg.LinAlgError, cv2.error):
        return None
    if not np.all(np.isfinite(d)):
        return None
    return float(d.mean())


def corner_err_px(H_est, H_true, shape) -> Optional[float]:
    if H_est is None or H_true is None:
        return None
    h, w = shape[:2]
    c = np.float64([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).reshape(-1, 1, 2)
    try:
        e = cv2.perspectiveTransform(c, np.asarray(H_est, np.float64))
        t = cv2.perspectiveTransform(c, np.asarray(H_true, np.float64))
    except cv2.error:
        return None
    return float(np.linalg.norm(e - t, axis=2).mean())


def heldout_px(pts_a: np.ndarray, pts_b: np.ndarray, seed: int,
               splits: int = 20, frac: float = 0.7) -> Optional[float]:
    """Median over splits of the held-out RMSE of a least-squares homography."""
    n = len(pts_a)
    if n < 10:
        return None
    rng = np.random.default_rng(seed)
    k = max(4, int(round(n * frac)))
    if n - k < 2:
        return None
    out = []
    for _ in range(splits):
        perm = rng.permutation(n)
        tr, te = perm[:k], perm[k:]
        H, _ = cv2.findHomography(pts_a[tr].reshape(-1, 1, 2).astype(np.float64),
                                  pts_b[tr].reshape(-1, 1, 2).astype(np.float64), 0)
        if H is None:
            continue
        proj = cv2.perspectiveTransform(pts_a[te].reshape(-1, 1, 2).astype(np.float64), H)
        err = np.linalg.norm(proj.reshape(-1, 2) - pts_b[te], axis=1)
        out.append(float(np.sqrt(np.mean(err ** 2))))
    return float(np.median(out)) if out else None


def ncc_masked(x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> Optional[float]:
    m = mask.astype(bool)
    if m.sum() < 1000:
        return None
    a = x[m].astype(np.float64)
    b = y[m].astype(np.float64)
    a -= a.mean()
    b -= b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else None


def ncc_before_after(a8: np.ndarray, b8: np.ndarray, H) -> Dict:
    if b8.shape != a8.shape:
        b8 = cv2.resize(b8, (a8.shape[1], a8.shape[0]), interpolation=cv2.INTER_CUBIC)
    full = np.ones_like(a8, dtype=np.uint8)
    before = ncc_masked(a8, b8, full)
    after = None
    if H is not None:
        h, w = b8.shape[:2]
        warped = cv2.warpPerspective(a8, np.asarray(H, np.float64), (w, h))
        valid = cv2.warpPerspective(full, np.asarray(H, np.float64), (w, h),
                                    flags=cv2.INTER_NEAREST)
        after = ncc_masked(warped, b8, valid)
    return {"ncc_before": before, "ncc_after": after}


def uniformity(pts_a: np.ndarray, shape_a) -> Dict:
    h, w = shape_a[:2]
    if len(pts_a) == 0:
        return {"unif_cells": 0.0, "unif_hull": 0.0}
    cx = np.clip((pts_a[:, 0] / w * 4).astype(int), 0, 3)
    cy = np.clip((pts_a[:, 1] / h * 4).astype(int), 0, 3)
    cells = len(set(zip(cx.tolist(), cy.tolist()))) / 16.0
    hull = 0.0
    if len(pts_a) >= 3:
        hull = float(cv2.contourArea(cv2.convexHull(pts_a.astype(np.float32)))) / (w * h)
    return {"unif_cells": round(cells, 4), "unif_hull": round(hull, 4)}


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# --------------------------------------------------------------------------- #
# Verdicts (pre-registration section 0.4)                                       #
# --------------------------------------------------------------------------- #
def verdict_gt(n_inliers: int, degenerate: bool, has_model: bool,
               grid_err: Optional[float]) -> str:
    if has_model and not degenerate and n_inliers >= 15 and grid_err is not None \
            and grid_err <= 2.0:
        return "SUCCESS"
    if has_model and n_inliers >= 8 and grid_err is not None and grid_err <= 10.0:
        return "MARGINAL"
    return "FAILURE"


def verdict_real(n_inliers: int, has_model: bool, heldout: Optional[float],
                 agree: Optional[float], other_usable: bool,
                 ncc_before: Optional[float], ncc_after: Optional[float]) -> tuple:
    confirmed_by = ""
    if agree is not None and other_usable and agree <= 3.0:
        confirmed_by = "agreement"
    elif not other_usable and ncc_before is not None and ncc_after is not None \
            and ncc_after - ncc_before >= 0.05:
        confirmed_by = "ncc"
    if has_model and n_inliers >= 15 and heldout is not None and heldout <= 2.0 \
            and confirmed_by:
        return "SUCCESS", confirmed_by
    if has_model and n_inliers >= 8 and heldout is not None and heldout <= 5.0:
        return "MARGINAL", confirmed_by
    return "FAILURE", confirmed_by


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")
