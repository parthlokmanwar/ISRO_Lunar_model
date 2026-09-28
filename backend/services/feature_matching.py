"""
Feature detection and matching.

Primary:  kornia DISK + LightGlue  (learned detector and matcher, pretrained)
Fallback: OpenCV SIFT + FLANN      (CPU, no weights, always available)

Two things differ from the previous version, both of which were producing wrong
output rather than merely slow output:

1. Keypoints are returned in the coordinate frame of the image that was passed
   in. The matcher works on a downscaled copy for speed, but the scale factor is
   undone before anything leaves this module. Previously coordinates were handed
   back in the internal 1024 px frame while the rest of the pipeline treated them
   as 2048 px coordinates, so every overlay and every drawn match line was off by
   a factor of two.

2. Detection and matching are separate steps. `LocalFeatureMatcher` only returns
   keypoints that survived matching, which forced the old code to fake match
   indices as i <-> i and made it impossible to show detected-but-unmatched
   keypoints. Running DISK and LightGlue separately gives real indices into the
   full keypoint sets, which the UI needs to show detection and matching as
   distinct stages.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch

from config import MATCH_CONF_THRESHOLD, MATCH_MAX_DIM, MAX_KEYPOINTS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_disk = None
_lg_matcher = None
_backend_error: Optional[str] = None


def _lazy_init() -> bool:
    """Load DISK + LightGlue on first use. Returns True if the learned path is up."""
    global _disk, _lg_matcher, _backend_error
    if _disk is not None and _lg_matcher is not None:
        return True
    if _backend_error is not None:
        return False
    try:
        import kornia.feature as KF

        _disk = KF.DISK.from_pretrained("depth").eval().to(device)
        _lg_matcher = KF.LightGlueMatcher("disk").eval().to(device)
        print(f"[matching] DISK + LightGlue ready on {device}")
        return True
    except Exception as exc:  # noqa: BLE001 - any failure must fall back cleanly
        _backend_error = f"{type(exc).__name__}: {exc}"
        print(f"[matching] DISK+LightGlue unavailable ({_backend_error}); using SIFT+FLANN")
        return False


@dataclass
class MatchResult:
    """Everything the pipeline stages need, in input-image coordinates."""

    keypoints_a: np.ndarray                  # (N, 2) all detected, image A frame
    keypoints_b: np.ndarray                  # (M, 2) all detected, image B frame
    matches: List[Dict]                      # {idx_a, idx_b, confidence}
    detector: str
    matcher: str
    scale_a: float = 1.0                     # internal frame -> input frame
    scale_b: float = 1.0
    timings_ms: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _downscale(img: np.ndarray, max_dim: int) -> Tuple[np.ndarray, float]:
    """
    Shrink so the long side is at most `max_dim`.

    Returns the image and the factor that maps the shrunken frame back to the
    input frame, so callers can restore coordinates.
    """
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return img, 1.0
    scale = max_dim / float(longest)
    resized = cv2.resize(
        img, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, 1.0 / scale


def _to_tensor(img: np.ndarray) -> torch.Tensor:
    """uint8 HxW (or HxWx3) -> float32 1x3xHxW in [0,1]. DISK wants 3 channels."""
    if img.ndim == 2:
        arr = np.stack([img] * 3, axis=0).astype(np.float32) / 255.0
    else:
        arr = img.transpose(2, 0, 1).astype(np.float32) / 255.0
    return torch.from_numpy(np.ascontiguousarray(arr)).unsqueeze(0).to(device)


def _pad_to_multiple(t: torch.Tensor, multiple: int = 16) -> torch.Tensor:
    """DISK's U-Net needs dimensions divisible by 16."""
    _, _, h, w = t.shape
    ph, pw = (-h) % multiple, (-w) % multiple
    if ph or pw:
        t = torch.nn.functional.pad(t, (0, pw, 0, ph), mode="reflect")
    return t


# --------------------------------------------------------------------------- #
# DISK + LightGlue                                                             #
# --------------------------------------------------------------------------- #
def _detect_disk(img: np.ndarray, max_kp: int):
    import kornia.feature as KF  # noqa: F401 - imported for side-effect parity

    t = _pad_to_multiple(_to_tensor(img))
    with torch.inference_mode():
        feats = _disk(t, n=max_kp, window_size=5, score_threshold=0.0, pad_if_not_divisible=True)[0]
    kp = feats.keypoints.detach().cpu().numpy().astype(np.float32)
    desc = feats.descriptors.detach()

    # Drop keypoints that DISK found in the reflect padding. They sit on mirrored
    # copies of real content, so they are not real features, and their
    # coordinates lie outside the image. LightGlue normalises by the true image
    # size and rejects any keypoint outside [-1, 1]. On the 248 px wide IIRS tile
    # that raised on every run, and the pipeline quietly fell back to SIFT while
    # the detector comparison still labelled the row DISK + LightGlue.
    h, w = img.shape[:2]
    inside = (kp[:, 0] < w) & (kp[:, 1] < h)
    if not inside.all():
        keep = torch.from_numpy(inside).to(desc.device)
        kp, desc = kp[inside], desc[keep]
    return kp, desc


def _match_disk_lightglue(
    img_a: np.ndarray, img_b: np.ndarray, max_kp: int, conf_threshold: float
):
    import kornia.feature as KF

    timings: Dict[str, float] = {}

    t0 = time.perf_counter()
    kp_a, desc_a = _detect_disk(img_a, max_kp)
    kp_b, desc_b = _detect_disk(img_b, max_kp)
    timings["detect"] = (time.perf_counter() - t0) * 1000.0

    if len(kp_a) < 2 or len(kp_b) < 2:
        return kp_a, kp_b, [], timings

    hw_a = torch.tensor(img_a.shape[:2], device=device)
    hw_b = torch.tensor(img_b.shape[:2], device=device)

    laf_a = KF.laf_from_center_scale_ori(
        torch.from_numpy(kp_a).to(device)[None],
        torch.ones(1, len(kp_a), 1, 1, device=device),
    )
    laf_b = KF.laf_from_center_scale_ori(
        torch.from_numpy(kp_b).to(device)[None],
        torch.ones(1, len(kp_b), 1, 1, device=device),
    )

    t0 = time.perf_counter()
    with torch.inference_mode():
        dists, idxs = _lg_matcher(desc_a, desc_b, laf_a, laf_b, hw1=hw_a, hw2=hw_b)
    timings["match"] = (time.perf_counter() - t0) * 1000.0

    idxs_np = idxs.detach().cpu().numpy()
    scores_np = dists.detach().cpu().numpy().reshape(-1)

    matches: List[Dict] = []
    for (ia, ib), s in zip(idxs_np, scores_np):
        # kornia's LightGlueMatcher names its first output a "distance", but it
        # returns LightGlue's matching score: higher is more confident. This
        # used to compute 1 - score, which inverted every confidence and made
        # the 0.1 floor keep only matches scoring <= 0.9 - on real OHRC tiles,
        # 25 of LightGlue's 1223 matches, and the 25 it trusted least
        # (EXPERIMENT_LOG Round 1, observation R1-O1).
        conf = float(np.clip(s, 0.0, 1.0))
        if conf >= conf_threshold:
            matches.append({"idx_a": int(ia), "idx_b": int(ib), "confidence": conf})

    return kp_a, kp_b, matches, timings


# --------------------------------------------------------------------------- #
# SIFT + FLANN fallback                                                        #
# --------------------------------------------------------------------------- #
def _match_sift(img_a: np.ndarray, img_b: np.ndarray, max_kp: int, conf_threshold: float):
    timings: Dict[str, float] = {}
    sift = cv2.SIFT_create(nfeatures=max_kp)

    t0 = time.perf_counter()
    kp_a, ds_a = sift.detectAndCompute(img_a, None)
    kp_b, ds_b = sift.detectAndCompute(img_b, None)
    timings["detect"] = (time.perf_counter() - t0) * 1000.0

    arr_a = (np.array([k.pt for k in kp_a], dtype=np.float32)
             if kp_a else np.empty((0, 2), dtype=np.float32))
    arr_b = (np.array([k.pt for k in kp_b], dtype=np.float32)
             if kp_b else np.empty((0, 2), dtype=np.float32))

    if ds_a is None or ds_b is None or len(ds_a) < 2 or len(ds_b) < 2:
        return arr_a, arr_b, [], timings

    flann = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 64})
    t0 = time.perf_counter()
    raw = flann.knnMatch(ds_a, ds_b, k=2)
    timings["match"] = (time.perf_counter() - t0) * 1000.0

    matches: List[Dict] = []
    for pair in raw:
        if len(pair) < 2:
            continue
        m, n = pair
        if n.distance <= 0:
            continue
        ratio = m.distance / n.distance
        if ratio < 0.8:  # Lowe's ratio test
            conf = float(np.clip(1.0 - ratio, 0.0, 1.0))
            if conf >= conf_threshold:
                matches.append({
                    "idx_a": int(m.queryIdx),
                    "idx_b": int(m.trainIdx),
                    "confidence": conf,
                })
    return arr_a, arr_b, matches, timings


# --------------------------------------------------------------------------- #
# Public entry point                                                           #
# --------------------------------------------------------------------------- #
def match_images(
    img_a: np.ndarray,
    img_b: np.ndarray,
    detector: str = "auto",
    max_dim: int = MATCH_MAX_DIM,
    max_keypoints: int = MAX_KEYPOINTS,
    conf_threshold: float = MATCH_CONF_THRESHOLD,
) -> MatchResult:
    """
    Detect and match features between two uint8 grayscale images.

    Coordinates in the returned MatchResult are in the frame of `img_a` / `img_b`
    as passed in, regardless of any internal downscaling.
    """
    small_a, scale_a = _downscale(img_a, max_dim)
    small_b, scale_b = _downscale(img_b, max_dim)

    use_learned = detector != "sift" and _lazy_init()
    notes: List[str] = []

    if use_learned:
        try:
            kp_a, kp_b, matches, timings = _match_disk_lightglue(
                small_a, small_b, max_keypoints, conf_threshold
            )
            det_name, mat_name = "DISK", "LightGlue"
        except Exception as exc:  # noqa: BLE001
            notes.append(f"LightGlue failed ({type(exc).__name__}: {exc}); fell back to SIFT")
            kp_a, kp_b, matches, timings = _match_sift(
                small_a, small_b, max_keypoints, conf_threshold
            )
            det_name, mat_name = "SIFT", "FLANN"
    else:
        if detector != "sift" and _backend_error:
            notes.append(f"DISK/LightGlue unavailable: {_backend_error}")
        kp_a, kp_b, matches, timings = _match_sift(
            small_a, small_b, max_keypoints, conf_threshold
        )
        det_name, mat_name = "SIFT", "FLANN"

    # Restore input-image coordinates. This is the step that was missing before.
    if len(kp_a):
        kp_a = kp_a * scale_a
    if len(kp_b):
        kp_b = kp_b * scale_b

    return MatchResult(
        keypoints_a=np.asarray(kp_a, dtype=np.float32).reshape(-1, 2),
        keypoints_b=np.asarray(kp_b, dtype=np.float32).reshape(-1, 2),
        matches=matches,
        detector=det_name,
        matcher=mat_name,
        scale_a=scale_a,
        scale_b=scale_b,
        timings_ms={k: round(v, 2) for k, v in timings.items()},
        notes=notes,
    )
