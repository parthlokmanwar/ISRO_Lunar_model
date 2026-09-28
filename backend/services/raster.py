"""
Windowed readers for Chandrayaan-2 raw products.

The point of this module is that we never load a whole strip. An OHRC product is
895 MB and a TMC-2 product is 1.4 GB; the old pipeline read them end to end and
then resized the entire thing to 2048 px, which destroyed the resolution the
mission exists to provide. Here we memory-map the file and slice only the window
that two images actually share, at native resolution.

Formats, taken from the PDS4 labels rather than assumed:
  OHRC  .img   UnsignedByte  (uint8)   lines x samples
  TMC-2 .img   UnsignedLSB2  (uint16)  lines x samples
  IIRS  .qub   UnsignedLSB2  (uint16)  bands x lines x samples (BSQ order)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

# PDS4 data_type -> numpy dtype. Extend here if new products appear.
PDS4_DTYPES = {
    "UnsignedByte": np.dtype("u1"),
    "SignedByte": np.dtype("i1"),
    "UnsignedLSB2": np.dtype("<u2"),
    "SignedLSB2": np.dtype("<i2"),
    "UnsignedMSB2": np.dtype(">u2"),
    "SignedMSB2": np.dtype(">i2"),
    "UnsignedLSB4": np.dtype("<u4"),
    "SignedLSB4": np.dtype("<i4"),
    "IEEE754LSBSingle": np.dtype("<f4"),
}


@dataclass(frozen=True)
class PixelWindow:
    """A rectangle in pixel space. Half-open: [sample0, sample1) x [line0, line1)."""

    sample0: int
    line0: int
    sample1: int
    line1: int

    @property
    def width(self) -> int:
        return self.sample1 - self.sample0

    @property
    def height(self) -> int:
        return self.line1 - self.line0

    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0

    def clip(self, samples: int, lines: int) -> "PixelWindow":
        return PixelWindow(
            max(0, self.sample0),
            max(0, self.line0),
            min(samples, self.sample1),
            min(lines, self.line1),
        )

    def as_dict(self) -> dict:
        return {
            "sample0": self.sample0, "line0": self.line0,
            "sample1": self.sample1, "line1": self.line1,
            "width": self.width, "height": self.height,
        }


def _resolve_dtype(meta: dict) -> np.dtype:
    name = meta.get("data_type") or "UnsignedByte"
    if name not in PDS4_DTYPES:
        raise ValueError(f"Unsupported PDS4 data_type: {name!r}")
    return PDS4_DTYPES[name]


def to_uint8(arr: np.ndarray, lo_pct: float = 1.0, hi_pct: float = 99.0) -> np.ndarray:
    """
    Percentile stretch to 8-bit.

    A plain min/max stretch is wrecked by the saturated pixels and dropped scan
    lines that these products contain, so we clip to percentiles instead. This
    matters most for the 16-bit TMC-2 and IIRS data, where the useful signal
    occupies a narrow part of the range.
    """
    a = arr.astype(np.float32)
    finite = a[np.isfinite(a)]
    if finite.size == 0:
        return np.zeros(a.shape, dtype=np.uint8)
    lo, hi = np.percentile(finite, [lo_pct, hi_pct])
    if hi <= lo:
        lo, hi = float(finite.min()), float(finite.max())
    if hi <= lo:
        return np.zeros(a.shape, dtype=np.uint8)
    return np.clip((a - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def read_window(path: Path, meta: dict, window: PixelWindow) -> np.ndarray:
    """
    Read one rectangular window from a 2D .img product at native resolution.

    Uses a memmap so only the requested rows are touched by the OS.
    """
    lines, samples = int(meta["lines"]), int(meta["samples"])
    dtype = _resolve_dtype(meta)
    w = window.clip(samples, lines)
    if not w.is_valid():
        raise ValueError(f"Empty window after clipping: {window}")

    mm = np.memmap(path, dtype=dtype, mode="r", shape=(lines, samples))
    try:
        tile = np.array(mm[w.line0:w.line1, w.sample0:w.sample1])
    finally:
        del mm
    return tile


def read_qub_window(
    path: Path,
    meta: dict,
    window: PixelWindow,
    band_lo: int,
    band_hi: int,
) -> np.ndarray:
    """
    Read a band-averaged window from an IIRS spectral cube.

    Averaging a contiguous run of bands rather than taking a single band gives a
    usable signal-to-noise ratio; a lone IIRS band is very noisy.
    """
    bands = int(meta.get("bands") or 256)
    lines, samples = int(meta["lines"]), int(meta["samples"])
    dtype = _resolve_dtype(meta)
    w = window.clip(samples, lines)
    if not w.is_valid():
        raise ValueError(f"Empty window after clipping: {window}")

    band_lo = max(0, min(bands - 1, band_lo))
    band_hi = max(band_lo + 1, min(bands, band_hi))

    mm = np.memmap(path, dtype=dtype, mode="r", shape=(bands, lines, samples))
    try:
        chunk = np.array(
            mm[band_lo:band_hi, w.line0:w.line1, w.sample0:w.sample1],
            dtype=np.float32,
        )
    finally:
        del mm
    return chunk.mean(axis=0)


def centred_window(
    sample_c: float, line_c: float, width: int, height: int
) -> PixelWindow:
    """A window of the given pixel size centred on a pixel coordinate."""
    s0 = int(round(sample_c - width / 2.0))
    l0 = int(round(line_c - height / 2.0))
    return PixelWindow(s0, l0, s0 + width, l0 + height)


def usable_fraction(tile: np.ndarray, dark_threshold: int = 4) -> float:
    """
    Fraction of the tile that is neither dead-black nor saturated.

    OHRC strips contain long stretches of near-zero fill, especially at the strip
    edges. Cutting a tile that is 90% fill produces a match result that looks
    plausible and means nothing, so the scenario builder screens tiles with this.
    """
    if tile.size == 0:
        return 0.0
    t = tile if tile.dtype == np.uint8 else to_uint8(tile)
    good = np.count_nonzero((t > dark_threshold) & (t < 252))
    return float(good) / float(t.size)


def texture_score(tile: np.ndarray) -> float:
    """
    Local-gradient energy, as a proxy for how much structure a tile carries.

    Featureless mare produces very few keypoints regardless of the detector, so
    we prefer tiles with real relief when choosing a demo scene.
    """
    if tile.size == 0:
        return 0.0
    t = (tile if tile.dtype == np.uint8 else to_uint8(tile)).astype(np.float32)
    gy, gx = np.gradient(t)
    return float(np.sqrt(gx ** 2 + gy ** 2).mean())
