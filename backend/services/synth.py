"""
Derived-scenario synthesis.

Your dataset contains exactly two genuinely overlapping pairs (the OHRC cross-date
pair and the TMC-2 stereo pair). The cross-sensor, polar-PSR and hyperspectral
scenarios have no real counterpart in it: OHRC sits at 23 E and TMC-2 at 66 E, so
any "match" between them is fitted to noise.

Rather than pretend otherwise, those scenarios are built here by transforming real
Chandrayaan-2 pixels with a transform we choose. That buys something a real
cross-mission pair cannot give: a known ground-truth homography, so registration
error can be reported as true geometric error rather than as a self-consistent
reprojection residual. Every product of this module carries a provenance tag that
the API and the UI surface verbatim.

  DERIVED    real pixels, physically-motivated sensor model, known transform
  SIMULATED  real pixels, synthetic illumination, known transform
"""
from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
# Known transforms                                                             #
# --------------------------------------------------------------------------- #
def similarity_homography(
    shape: Tuple[int, int],
    rotation_deg: float = 0.0,
    scale: float = 1.0,
    tx: float = 0.0,
    ty: float = 0.0,
) -> np.ndarray:
    """
    A 3x3 similarity transform about the image centre.

    Kept deliberately modest (a few degrees, a few percent of scale) so it stands
    for real inter-orbit pointing differences rather than an artificial stunt.
    """
    h, w = shape[:2]
    cx, cy = w / 2.0, h / 2.0
    th = np.radians(rotation_deg)
    cos_t, sin_t = np.cos(th) * scale, np.sin(th) * scale
    return np.array(
        [
            [cos_t, -sin_t, cx - cos_t * cx + sin_t * cy + tx],
            [sin_t, cos_t, cy - sin_t * cx - cos_t * cy + ty],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def perspective_homography(
    shape: Tuple[int, int],
    rotation_deg: float = 0.0,
    scale: float = 1.0,
    tx: float = 0.0,
    ty: float = 0.0,
    tilt: float = 0.0,
) -> np.ndarray:
    """
    Similarity plus a small projective term.

    `tilt` stands for the off-nadir viewing geometry difference between two
    orbits. Values around 1e-5 produce a realistic few-pixel keystone across a
    1024 px tile.
    """
    H = similarity_homography(shape, rotation_deg, scale, tx, ty)
    if tilt:
        H = H.copy()
        H[2, 0] = tilt
        H[2, 1] = tilt * 0.4
    return H


def apply_homography(img: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Warp an image by a known homography, keeping the output size."""
    h, w = img.shape[:2]
    return cv2.warpPerspective(
        img, H, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101
    )


# --------------------------------------------------------------------------- #
# Sensor simulation                                                            #
# --------------------------------------------------------------------------- #
def degrade_to_sensor(
    img: np.ndarray,
    scale_factor: float,
    psf_sigma_px: float = 0.9,
    noise_sigma: float = 2.0,
    seed: int = 0,
) -> np.ndarray:
    """
    Simulate observing the same ground with a coarser sensor.

    Order matters and mirrors a real imaging chain: band-limit with the optical
    PSF first, then sample, then add detector noise. Downsampling before blurring
    would alias, which would make the resulting match problem easier than the real
    one rather than harder.

    `scale_factor` is the ratio of ground sample distances, e.g. 4.46 / 0.26 = 17.2
    for OHRC -> TMC-2.
    """
    rng = np.random.default_rng(seed)
    src = img.astype(np.float32)

    sigma = max(psf_sigma_px, scale_factor / 2.5)
    k = int(max(3, round(sigma * 6)) | 1)
    blurred = cv2.GaussianBlur(src, (k, k), sigma)

    h, w = blurred.shape[:2]
    new_w = max(8, int(round(w / scale_factor)))
    new_h = max(8, int(round(h / scale_factor)))
    small = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)

    if noise_sigma > 0:
        small = small + rng.normal(0.0, noise_sigma, small.shape).astype(np.float32)

    return np.clip(small, 0, 255).astype(np.uint8)


def upsample_to(img: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """Resample to a target (h, w), as a viewer would to display a coarse product."""
    h, w = shape[:2]
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)


# --------------------------------------------------------------------------- #
# Illumination simulation                                                      #
# --------------------------------------------------------------------------- #
def relief_proxy(img: np.ndarray, smooth_sigma: float = 2.5) -> np.ndarray:
    """
    Estimate a relief field from a single shaded image.

    True shape-from-shading is ill-posed, and we are not claiming to solve it. For
    a scene lit at a known low angle the smoothed intensity is monotonically
    related to slope along the illumination direction, which is enough to produce
    a surface whose re-shading looks and behaves like lunar terrain: crater rims
    catch light, floors fall into shadow, and the pattern moves correctly when the
    sun azimuth changes. That behaviour is the thing the PSR scenario needs to
    exercise.
    """
    f = img.astype(np.float32) / 255.0
    f = cv2.GaussianBlur(f, (0, 0), smooth_sigma)
    lo, hi = np.percentile(f, [2, 98])
    if hi <= lo:
        return np.zeros_like(f)
    return np.clip((f - lo) / (hi - lo), 0.0, 1.0)


def _cast_shadow_mask(
    height: np.ndarray, sun_elev_deg: float, sun_az_deg: float, relief_scale: float
) -> np.ndarray:
    """
    Ray-march the height field along the solar azimuth to find occluded pixels.

    At the grazing sun elevations of the lunar poles, cast shadow, not shading, is
    what dominates the image. Skipping it would make the PSR scenario far easier
    than the real thing.
    """
    h, w = height.shape
    elev = np.radians(max(sun_elev_deg, 0.05))
    az = np.radians(sun_az_deg)
    dx, dy = np.sin(az), -np.cos(az)

    z = height * relief_scale
    tan_e = np.tan(elev)
    lit = np.ones((h, w), dtype=np.float32)

    max_steps = int(min(160, max(24, relief_scale / max(tan_e, 1e-3))))
    accum = np.full((h, w), -np.inf, dtype=np.float32)

    for step in range(1, max_steps + 1):
        sx, sy = dx * step, dy * step
        M = np.float32([[1, 0, -sx], [0, 1, -sy]])
        shifted = cv2.warpAffine(
            z, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
        )
        accum = np.maximum(accum, shifted - step * tan_e)

    lit[accum > z + 1e-3] = 0.0
    return cv2.GaussianBlur(lit, (0, 0), 1.2)


def relight(
    img: np.ndarray,
    sun_elev_deg: float,
    sun_az_deg: float,
    relief_scale: float = 26.0,
    ambient: float = 0.05,
    cast_shadows: bool = True,
    noise_sigma: float = 1.5,
    seed: int = 0,
) -> np.ndarray:
    """
    Re-illuminate a tile from a new solar direction.

    Lambertian shading on the relief proxy, plus optional cast shadow and a small
    ambient term standing in for the secondary illumination that bounces off
    crater walls into permanently shadowed regions.
    """
    rng = np.random.default_rng(seed)
    height = relief_proxy(img)

    gy, gx = np.gradient(height * relief_scale)
    norm = np.sqrt(gx ** 2 + gy ** 2 + 1.0)
    nx, ny, nz = -gx / norm, -gy / norm, 1.0 / norm

    elev = np.radians(sun_elev_deg)
    az = np.radians(sun_az_deg)
    sx = np.cos(elev) * np.sin(az)
    sy = -np.cos(elev) * np.cos(az)
    sz = np.sin(elev)

    lambert = np.clip(nx * sx + ny * sy + nz * sz, 0.0, 1.0)

    if cast_shadows:
        lambert = lambert * _cast_shadow_mask(
            height, sun_elev_deg, sun_az_deg, relief_scale
        )

    # Keep the scene's own albedo variation so this stays real imagery, not a render.
    albedo = 0.55 + 0.45 * (img.astype(np.float32) / 255.0)
    out = albedo * (lambert + ambient)

    lo, hi = np.percentile(out, [1, 99])
    if hi > lo:
        out = (out - lo) / (hi - lo)
    out = np.clip(out, 0, 1) * 255.0

    if noise_sigma > 0:
        out = out + rng.normal(0.0, noise_sigma, out.shape)

    return np.clip(out, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- #
# Ground-truth evaluation                                                      #
# --------------------------------------------------------------------------- #
def homography_corner_error(
    H_est: Optional[np.ndarray], H_true: np.ndarray, shape: Tuple[int, int]
) -> Optional[float]:
    """
    Mean corner displacement, in pixels, between an estimated and a true homography.

    This is the honest accuracy number. Reprojection RMSE only says the inliers
    agree with each other, so a confidently wrong homography fitted to repeated
    terrain can post an excellent RMSE. Corner error cannot be gamed that way,
    because it is measured against the transform we actually applied.
    """
    if H_est is None:
        return None
    h, w = shape[:2]
    corners = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).reshape(-1, 1, 2)
    try:
        a = cv2.perspectiveTransform(corners, H_est.astype(np.float64))
        b = cv2.perspectiveTransform(corners, H_true.astype(np.float64))
    except cv2.error:
        return None
    return float(np.linalg.norm(a - b, axis=2).mean())
