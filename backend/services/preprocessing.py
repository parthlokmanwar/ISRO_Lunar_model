"""
Illumination and contrast normalisation.

This is the stage that carries the sun-angle-invariance claim, so it runs before
detection and the UI shows its output rather than the raw tile.
"""
from __future__ import annotations

from typing import Dict, Tuple

import cv2
import numpy as np

from config import CLAHE_CLIP_LIMIT, CLAHE_GRID_SIZE, SHADOW_THRESHOLD


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim > 2:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def apply_clahe(img: np.ndarray,
                clip_limit: float = CLAHE_CLIP_LIMIT,
                grid_size: Tuple[int, int] = CLAHE_GRID_SIZE) -> np.ndarray:
    """Contrast-limited adaptive histogram equalisation on a grayscale image."""
    gray = to_gray(img)
    if gray.dtype != np.uint8:
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit),
                            tileGridSize=tuple(int(v) for v in grid_size))
    return clahe.apply(gray)


def shadow_mask(img: np.ndarray, threshold: int = SHADOW_THRESHOLD) -> np.ndarray:
    """Boolean mask, True where the pixel is bright enough to carry information."""
    return to_gray(img) > threshold


def normalize_for_matching(
    img: np.ndarray,
    clip_limit: float = CLAHE_CLIP_LIMIT,
    grid_size: Tuple[int, int] = CLAHE_GRID_SIZE,
    suppress_shadows: bool = True,
    threshold: int = SHADOW_THRESHOLD,
) -> Tuple[np.ndarray, Dict]:
    """
    Normalise a tile before detection, and report what the step did.

    The shadow mask is now computed from the same grayscale image that CLAHE was
    applied to. Previously it came from the original array while being multiplied
    into the grayscale result, which broadcast incorrectly for any 3-channel input
    and only avoided raising because every code path happened to pass grayscale.
    """
    gray = to_gray(img)
    if gray.dtype != np.uint8:
        gray = np.clip(gray, 0, 255).astype(np.uint8)

    enhanced = apply_clahe(gray, clip_limit, grid_size)

    stats: Dict = {
        "clahe_clip_limit": float(clip_limit),
        "clahe_grid": list(grid_size),
        "shadow_suppressed": bool(suppress_shadows),
        "shadow_threshold": int(threshold),
        "mean_before": round(float(gray.mean()), 2),
        "std_before": round(float(gray.std()), 2),
    }

    if suppress_shadows:
        mask = gray > threshold
        stats["shadow_fraction"] = round(float(1.0 - mask.mean()), 4)
        enhanced = np.where(mask, enhanced, 0).astype(np.uint8)
    else:
        stats["shadow_fraction"] = round(float((gray <= threshold).mean()), 4)

    stats["mean_after"] = round(float(enhanced.mean()), 2)
    stats["std_after"] = round(float(enhanced.std()), 2)
    return enhanced, stats
