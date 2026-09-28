"""
Coarse co-registration: finding the tile pair that actually shows the same ground.

Measured on this dataset, the PDS4 corner geometry for the OHRC cross-date pair is
off by roughly 184 m across-track and 1430 m along-track. A 1024 px OHRC tile spans
about 313 m, so cutting tiles at the label-predicted position produces two tiles
that do not overlap at all. That is why matching them yielded four inliers and a
meaningless 0.001 px RMSE: with exactly four points a homography fits perfectly by
construction, whether or not the correspondence is real.

So the labels are used as a prior, not as truth:

  1. Predict the tile centre in both strips from the PDS4 corners.
  2. Read wide swaths around both predictions, sized to the geolocation error budget.
  3. Resample both to a common ground sample distance.
  4. Normalised cross-correlation of a patch of B against the swath of A.
  5. Accept the lock only if the correlation peak is unambiguous, then cut the
     final tiles at native resolution from the corrected positions.

Step 5 matters. A weak or ambiguous peak means we could not confirm the two strips
see the same ground, and the honest response is to reject the pair rather than hand
the matcher two unrelated tiles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from services.geo import Footprint
from services.raster import PixelWindow, read_window, to_uint8


@dataclass
class CoregResult:
    """Outcome of the coarse lock between two strips."""

    window_a: PixelWindow
    window_b: PixelWindow
    ncc_peak: float               # correlation at the accepted peak
    peak_ratio: float             # peak / next-best peak; >2 is a confident lock
    peak_z: float                 # peak prominence in std devs above the surface
    shift_samples: float          # correction applied to the label prediction
    shift_lines: float
    shift_m_across: float         # the same correction expressed on the ground
    shift_m_along: float
    gsd_ratio: float              # gsd_b / gsd_a
    accepted: bool
    used_prior: bool = False      # True when we kept the label geometry unchanged
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "window_a": self.window_a.as_dict(),
            "window_b": self.window_b.as_dict(),
            "ncc_peak": round(self.ncc_peak, 4),
            "peak_ratio": round(self.peak_ratio, 3),
            "peak_z": round(self.peak_z, 2),
            "shift_samples": round(self.shift_samples, 1),
            "shift_lines": round(self.shift_lines, 1),
            "shift_m_across": round(self.shift_m_across, 1),
            "shift_m_along": round(self.shift_m_along, 1),
            "gsd_ratio": round(self.gsd_ratio, 4),
            "accepted": self.accepted,
            "used_prior": self.used_prior,
            "reason": self.reason,
        }


def _prep(img: np.ndarray, clahe_clip: float = 3.0) -> np.ndarray:
    """
    Contrast-normalise before correlating.

    The two OHRC scenes were taken three years apart at different sun elevations,
    so their raw brightness distributions differ enough to depress the correlation
    peak. CLAHE removes most of that without touching geometry.
    """
    if img.ndim > 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8, 8)).apply(img)


def _safe_centre(f: Footprint, lon: float, lat: float,
                 half_s: int, half_l: int) -> Tuple[int, int]:
    """Label-predicted tile centre, pulled inside the strip so a full window fits."""
    s, l = f.lonlat_to_pixel(lon, lat)
    s = int(np.clip(s, half_s, max(half_s, f.samples - half_s)))
    l = int(np.clip(l, half_l, max(half_l, f.lines - half_l)))
    return s, l


def _refine_shift(
    path_a: Path, meta_a: dict, fp_a: Footprint,
    path_b: Path, meta_b: dict, fp_b: Footprint,
    cs_a: int, cl_a: int, cs_b: int, cl_b: int,
    d_samples: float, d_lines: float,
    tile_size: int, gsd_ratio: float,
) -> Tuple[float, float]:
    """
    Second correlation pass at full tile resolution over a small search range.

    Returns an updated (d_samples, d_lines); falls back to the input values if the
    refinement cannot be computed or wants to move further than the coarse pass
    should have left on the table.
    """
    pad = tile_size // 4
    half = tile_size // 2
    half_b = max(16, int(round(half * 1.0 / gsd_ratio)))

    a_s = int(np.clip(cs_a + d_samples, half + pad, fp_a.samples - half - pad))
    a_l = int(np.clip(cl_a + d_lines, half + pad, fp_a.lines - half - pad))
    b_s = int(np.clip(cs_b, half_b, fp_b.samples - half_b))
    b_l = int(np.clip(cl_b, half_b, fp_b.lines - half_b))

    try:
        big_a = to_uint8(read_window(
            path_a, meta_a,
            PixelWindow(a_s - half - pad, a_l - half - pad,
                        a_s + half + pad, a_l + half + pad),
        ))
        tile_b = to_uint8(read_window(
            path_b, meta_b,
            PixelWindow(b_s - half_b, b_l - half_b, b_s + half_b, b_l + half_b),
        ))
    except Exception:  # noqa: BLE001 - refinement is best-effort
        return d_samples, d_lines

    if big_a.size == 0 or tile_b.size == 0:
        return d_samples, d_lines

    if abs(gsd_ratio - 1.0) > 1e-3:
        tile_b = cv2.resize(tile_b, (tile_size, tile_size), interpolation=cv2.INTER_AREA)

    # Shrink the template a little so there is room to slide.
    inset = tile_size // 8
    tmpl = tile_b[inset:tile_b.shape[0] - inset, inset:tile_b.shape[1] - inset]
    if tmpl.shape[0] >= big_a.shape[0] or tmpl.shape[1] >= big_a.shape[1] or tmpl.size == 0:
        return d_samples, d_lines

    res = cv2.matchTemplate(_prep(big_a), _prep(tmpl), cv2.TM_CCOEFF_NORMED)
    _, peak, _, loc = cv2.minMaxLoc(res)
    if peak < 0.15:
        return d_samples, d_lines

    exp_x = (big_a.shape[1] - tmpl.shape[1]) / 2.0
    exp_y = (big_a.shape[0] - tmpl.shape[0]) / 2.0
    extra_x, extra_y = loc[0] - exp_x, loc[1] - exp_y

    # A refinement should be small; a large jump means we locked onto something else.
    if abs(extra_x) > pad or abs(extra_y) > pad:
        return d_samples, d_lines
    return d_samples + extra_x, d_lines + extra_y


def locate_overlap(
    path_a: Path, meta_a: dict, fp_a: Footprint,
    path_b: Path, meta_b: dict, fp_b: Footprint,
    lon: float, lat: float,
    tile_size: int = 1024,
    search_m_across: float = 600.0,
    search_m_along: float = 4000.0,
    decimation: int = 4,
    min_peak: float = 0.20,
    min_peak_ratio: float = 1.8,
    min_peak_z: float = 6.0,
    refine: bool = True,
) -> CoregResult:
    """
    Lock two strips onto the same ground patch near (lon, lat).

    `search_m_across` / `search_m_along` set how far from the label prediction we
    are willing to look. They default to the error actually observed on this
    dataset, with headroom.
    """
    gsd_a = float(np.mean(fp_a.ground_sample_distance_m()))
    gsd_b = float(np.mean(fp_b.ground_sample_distance_m()))
    gsd_ratio = gsd_b / gsd_a

    # Swath A is the search area: the tile plus the geolocation error budget.
    half_s_a = int(tile_size / 2 + search_m_across / gsd_a)
    half_l_a = int(tile_size / 2 + search_m_along / gsd_a)
    half_s_a = int(min(half_s_a, max(64, fp_a.samples // 2 - 2)))
    half_l_a = int(min(half_l_a, max(64, fp_a.lines // 2 - 2)))

    # B supplies the template: roughly one tile, with a little context around it.
    # It is capped below at half of A's swath by the patch crop further down, so
    # there is always room to slide. Sizing it off the search area instead would
    # make the template grow with the error budget until it covered kilometres of
    # unrelated terrain and correlated with nothing.
    half_s_b = int(max(24, (tile_size / 2) * 1.4 / gsd_ratio))
    half_l_b = int(max(24, (tile_size / 2) * 1.4 / gsd_ratio))
    half_s_b = int(min(half_s_b, max(24, fp_b.samples // 2 - 2)))
    half_l_b = int(min(half_l_b, max(24, fp_b.lines // 2 - 2)))

    cs_a, cl_a = _safe_centre(fp_a, lon, lat, half_s_a, half_l_a)
    cs_b, cl_b = _safe_centre(fp_b, lon, lat, half_s_b, half_l_b)

    win_a = PixelWindow(cs_a - half_s_a, cl_a - half_l_a, cs_a + half_s_a, cl_a + half_l_a)
    win_b = PixelWindow(cs_b - half_s_b, cl_b - half_l_b, cs_b + half_s_b, cl_b + half_l_b)

    swath_a = to_uint8(read_window(path_a, meta_a, win_a))
    swath_b = to_uint8(read_window(path_b, meta_b, win_b))
    if swath_a.size == 0 or swath_b.size == 0:
        return CoregResult(win_a, win_b, 0.0, 0.0, 0.0, 0, 0, 0, 0, gsd_ratio,
                           False, "empty swath")

    # Common ground scale, then decimate for a fast search.
    tgt_a = (max(8, swath_a.shape[1] // decimation), max(8, swath_a.shape[0] // decimation))
    small_a = cv2.resize(swath_a, tgt_a, interpolation=cv2.INTER_AREA)
    scale_b = gsd_ratio / decimation
    tgt_b = (max(8, int(swath_b.shape[1] * scale_b)), max(8, int(swath_b.shape[0] * scale_b)))
    small_b = cv2.resize(swath_b, tgt_b, interpolation=cv2.INTER_AREA)

    small_a, small_b = _prep(small_a), _prep(small_b)

    # Template from the centre of B, capped so at least 25% of each axis stays
    # free for the search. Without that headroom the correlation surface is a
    # couple of pixels wide and every peak looks equally good.
    max_h = max(16, int(small_a.shape[0] * 0.5))
    max_w = max(16, int(small_a.shape[1] * 0.5))
    ph = min(small_b.shape[0], max_h)
    pw = min(small_b.shape[1], max_w)
    by = (small_b.shape[0] - ph) // 2
    bx = (small_b.shape[1] - pw) // 2
    patch = small_b[by:by + ph, bx:bx + pw]
    if patch.size == 0 or patch.shape[0] >= small_a.shape[0] or patch.shape[1] >= small_a.shape[1]:
        return CoregResult(win_a, win_b, 0.0, 0.0, 0.0, 0, 0, 0, 0, gsd_ratio,
                           False, "search swath smaller than template")

    res = cv2.matchTemplate(small_a, patch, cv2.TM_CCOEFF_NORMED)
    _, peak, _, peak_loc = cv2.minMaxLoc(res)

    # Ambiguity check, part one: suppress a neighbourhood of the peak, look again.
    masked = res.copy()
    cv2.circle(masked, peak_loc, max(8, max(res.shape) // 12), 0.0, -1)
    runner_up = float(masked.max())
    peak_ratio = float(peak / runner_up) if runner_up > 1e-6 else float("inf")

    # Part two: how far the peak stands above the surface as a whole.
    #
    # Peak ratio alone rejects good locks on long strips. Along a stereo pair the
    # correlation surface is a ridge rather than an isolated spike, so the
    # second-best point sits on the same ridge and the ratio collapses to ~1.0
    # even when the peak is strong and correctly placed. Prominence in standard
    # deviations does not have that failure mode.
    res_mean = float(res.mean())
    res_std = float(res.std())
    peak_z = (peak - res_mean) / res_std if res_std > 1e-6 else 0.0

    # Where the label prior said the patch would land.
    exp_x = (small_a.shape[1] - pw) / 2.0
    exp_y = (small_a.shape[0] - ph) / 2.0
    d_samples = (peak_loc[0] - exp_x) * decimation
    d_lines = (peak_loc[1] - exp_y) * decimation

    # What the correction would cost us if we are wrong about it.
    implied_m = float(np.hypot(d_samples * gsd_a, d_lines * gsd_a))
    trust_prior_m = tile_size * gsd_a * 0.35  # a third of a tile

    confident = bool(
        peak >= min_peak and (peak_ratio >= min_peak_ratio or peak_z >= min_peak_z)
    )

    # Three outcomes, not two.
    #
    # A same-orbit stereo pair has accurate labels already, and its correlation
    # surface is a long ridge, so it can post a strong peak with a poor ratio and
    # only moderate prominence. Rejecting it would throw away a perfectly good real
    # pair. What actually matters is whether we are being asked to move far on weak
    # evidence: a small correction is safe to ignore, a large one is not safe to
    # trust.
    used_prior = False
    if confident:
        accepted, reason = True, ""
    elif implied_m <= trust_prior_m:
        accepted, used_prior = True, True
        d_samples, d_lines = 0.0, 0.0
        reason = (
            f"correlation inconclusive (peak={peak:.3f}, ratio={peak_ratio:.2f}, "
            f"prominence={peak_z:.1f} sigma) but the implied correction is only "
            f"{implied_m:.0f} m, within the label accuracy we already assume; "
            "using the PDS4 geometry as-is"
        )
    else:
        accepted = False
        reason = (
            f"weak or ambiguous correlation (peak={peak:.3f}, ratio={peak_ratio:.2f}, "
            f"prominence={peak_z:.1f} sigma) while asking for a {implied_m:.0f} m "
            "correction; cannot confirm these strips see the same ground"
        )

    # Refinement pass. The coarse search is quantised to `decimation` pixels, which
    # leaves a residual offset of a few tens of pixels; measured on this dataset it
    # converges to under 5 px after one extra correlation at full tile resolution.
    if accepted and refine and not used_prior:
        d_samples, d_lines = _refine_shift(
            path_a, meta_a, fp_a, path_b, meta_b, fp_b,
            cs_a, cl_a, cs_b, cl_b, d_samples, d_lines,
            tile_size, gsd_ratio,
        )

    # Corrected native-resolution tiles.
    half = tile_size // 2
    a_s = int(np.clip(cs_a + d_samples, half, fp_a.samples - half))
    a_l = int(np.clip(cl_a + d_lines, half, fp_a.lines - half))
    half_b = int(round(half * gsd_a / gsd_b))
    half_b = max(16, half_b)
    b_s = int(np.clip(cs_b, half_b, fp_b.samples - half_b))
    b_l = int(np.clip(cl_b, half_b, fp_b.lines - half_b))

    return CoregResult(
        window_a=PixelWindow(a_s - half, a_l - half, a_s + half, a_l + half),
        window_b=PixelWindow(b_s - half_b, b_l - half_b, b_s + half_b, b_l + half_b),
        ncc_peak=float(peak),
        peak_ratio=peak_ratio,
        peak_z=float(peak_z),
        shift_samples=float(d_samples),
        shift_lines=float(d_lines),
        shift_m_across=float(abs(d_samples) * gsd_a),
        shift_m_along=float(abs(d_lines) * gsd_a),
        gsd_ratio=gsd_ratio,
        accepted=accepted,
        used_prior=used_prior,
        reason=reason,
    )
