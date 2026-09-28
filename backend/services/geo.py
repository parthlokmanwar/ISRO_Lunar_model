"""
Geographic mapping for Chandrayaan-2 pushbroom strips.

PDS4 labels give the four ground corners of each strip. That is enough to fit an
affine map between pixel space (sample, line) and selenographic (lon, lat), which
is what we need to answer the only question that matters when pairing images:

    which pixels of A and B look at the same piece of the Moon?

The previous pipeline never asked this. It paired images by a coarse latitude
bucket and then squashed whole 78000-line strips down to 2048 px, which is how
OHRC ended up being "matched" against TMC-2 across 42 degrees of longitude.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

# Mean lunar radius (IAU/IAG 2015), metres.
MOON_RADIUS_M = 1_737_400.0
M_PER_DEG_LAT = 2 * np.pi * MOON_RADIUS_M / 360.0  # ~30.32 km


def m_per_deg_lon(lat_deg: float) -> float:
    """Ground metres per degree of longitude at a given latitude."""
    return M_PER_DEG_LAT * float(np.cos(np.radians(lat_deg)))


@dataclass(frozen=True)
class Footprint:
    """Ground footprint of one strip, plus its pixel dimensions."""

    ul: Tuple[float, float]   # (lon, lat) at pixel (sample=0, line=0)
    ur: Tuple[float, float]   # (lon, lat) at pixel (sample=max, line=0)
    ll: Tuple[float, float]   # (lon, lat) at pixel (sample=0, line=max)
    lr: Tuple[float, float]   # (lon, lat) at pixel (sample=max, line=max)
    lines: int
    samples: int

    # -- bounds ---------------------------------------------------------------
    @property
    def _corners(self) -> Tuple[Tuple[float, float], ...]:
        return (self.ul, self.ur, self.ll, self.lr)

    @property
    def lon_min(self) -> float:
        return min(c[0] for c in self._corners)

    @property
    def lon_max(self) -> float:
        return max(c[0] for c in self._corners)

    @property
    def lat_min(self) -> float:
        return min(c[1] for c in self._corners)

    @property
    def lat_max(self) -> float:
        return max(c[1] for c in self._corners)

    @property
    def lat_center(self) -> float:
        return (self.lat_min + self.lat_max) / 2.0

    @property
    def lon_center(self) -> float:
        return (self.lon_min + self.lon_max) / 2.0

    # -- pixel <-> ground -----------------------------------------------------
    def _forward_matrix(self) -> np.ndarray:
        """
        Least-squares affine [lon, lat] = M @ [sample, line, 1] from the four
        corners. Exact for a parallelogram footprint; these strips are close
        enough that the residual stays well under one pixel.
        """
        s, l = self.samples - 1, self.lines - 1
        src = np.array(
            [[0.0, 0.0, 1.0], [s, 0.0, 1.0], [0.0, l, 1.0], [s, l, 1.0]],
            dtype=np.float64,
        )
        dst = np.array(self._corners, dtype=np.float64)
        M, *_ = np.linalg.lstsq(src, dst, rcond=None)
        return M.T  # 2x3

    def pixel_to_lonlat(self, sample: float, line: float) -> Tuple[float, float]:
        v = self._forward_matrix() @ np.array([sample, line, 1.0])
        return float(v[0]), float(v[1])

    def lonlat_to_pixel(self, lon: float, lat: float) -> Tuple[float, float]:
        """Inverse affine. Returns (sample, line); may fall outside the strip."""
        M = self._forward_matrix()
        A, b = M[:, :2], M[:, 2]
        sol = np.linalg.solve(A, np.array([lon, lat], dtype=np.float64) - b)
        return float(sol[0]), float(sol[1])

    def contains_pixel(self, sample: float, line: float) -> bool:
        return 0 <= sample < self.samples and 0 <= line < self.lines

    def ground_sample_distance_m(self) -> Tuple[float, float]:
        """Metres per pixel along the sample and line axes, derived from corners."""
        mlon = m_per_deg_lon(self.lat_center)
        dx_s = (self.ur[0] - self.ul[0]) * mlon
        dy_s = (self.ur[1] - self.ul[1]) * M_PER_DEG_LAT
        dx_l = (self.ll[0] - self.ul[0]) * mlon
        dy_l = (self.ll[1] - self.ul[1]) * M_PER_DEG_LAT
        return (
            float(np.hypot(dx_s, dy_s) / max(self.samples - 1, 1)),
            float(np.hypot(dx_l, dy_l) / max(self.lines - 1, 1)),
        )


@dataclass(frozen=True)
class GeoWindow:
    """A lon/lat rectangle that two strips have in common."""

    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    @property
    def width_m(self) -> float:
        return (self.lon_max - self.lon_min) * m_per_deg_lon(
            (self.lat_min + self.lat_max) / 2.0
        )

    @property
    def height_m(self) -> float:
        return (self.lat_max - self.lat_min) * M_PER_DEG_LAT

    @property
    def area_km2(self) -> float:
        return self.width_m * self.height_m / 1e6

    def center(self) -> Tuple[float, float]:
        return (
            (self.lon_min + self.lon_max) / 2.0,
            (self.lat_min + self.lat_max) / 2.0,
        )

    def as_dict(self) -> dict:
        lon, lat = self.center()
        return {
            "lon_min": round(self.lon_min, 6),
            "lon_max": round(self.lon_max, 6),
            "lat_min": round(self.lat_min, 6),
            "lat_max": round(self.lat_max, 6),
            "lon_center": round(lon, 6),
            "lat_center": round(lat, 6),
            "width_m": round(self.width_m, 1),
            "height_m": round(self.height_m, 1),
            "area_km2": round(self.area_km2, 3),
        }


def overlap_window(a: Footprint, b: Footprint) -> Optional[GeoWindow]:
    """
    Axis-aligned lon/lat intersection of two footprints, or None if disjoint.

    Conservative by construction: the real footprints are slightly rotated
    quadrilaterals, so their true intersection sits inside this box. Every tile
    cut from it is still verified against both strips before being accepted.
    """
    lon_min = max(a.lon_min, b.lon_min)
    lon_max = min(a.lon_max, b.lon_max)
    lat_min = max(a.lat_min, b.lat_min)
    lat_max = min(a.lat_max, b.lat_max)
    if lon_min >= lon_max or lat_min >= lat_max:
        return None
    return GeoWindow(lon_min, lon_max, lat_min, lat_max)


def _box_area_m2(f: Footprint) -> float:
    return (
        (f.lon_max - f.lon_min) * m_per_deg_lon(f.lat_center)
        * (f.lat_max - f.lat_min) * M_PER_DEG_LAT
    )


def overlap_fraction(a: Footprint, b: Footprint) -> float:
    """Overlap area as a fraction of the smaller of the two footprints."""
    w = overlap_window(a, b)
    if w is None:
        return 0.0
    smaller = min(_box_area_m2(a), _box_area_m2(b))
    if smaller <= 0:
        return 0.0
    return float(min(1.0, (w.width_m * w.height_m) / smaller))


def footprint_from_meta(meta: dict) -> Optional[Footprint]:
    """Build a Footprint from a parsed PDS4 metadata dict, or None if incomplete."""
    need = (
        "upper_left_lon", "upper_left_lat", "upper_right_lon", "upper_right_lat",
        "lower_left_lon", "lower_left_lat", "lower_right_lon", "lower_right_lat",
    )
    if any(meta.get(k) is None for k in need):
        return None
    lines, samples = meta.get("lines"), meta.get("samples")
    if not lines or not samples:
        return None
    return Footprint(
        ul=(meta["upper_left_lon"], meta["upper_left_lat"]),
        ur=(meta["upper_right_lon"], meta["upper_right_lat"]),
        ll=(meta["lower_left_lon"], meta["lower_left_lat"]),
        lr=(meta["lower_right_lon"], meta["lower_right_lat"]),
        lines=int(lines),
        samples=int(samples),
    )
