"""
Scenario catalogue access.

The catalogue is written by scripts/build_scenarios.py and read here. It is cached
in memory and invalidated on file mtime, so rebuilding scenarios while the server
runs picks up without a restart.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import cv2

from config import CATALOG_PATH, SCENES_DIR

THUMB_DIR = SCENES_DIR / "thumbs"
THUMB_MAX = 320   # px on the long side; cards show them at ~120 px, 2x for HiDPI

_cache: Optional[Dict] = None
_cache_mtime: float = 0.0


def load_catalog() -> Dict:
    """Full catalogue, or an empty one if it has not been built yet."""
    global _cache, _cache_mtime
    if not CATALOG_PATH.exists():
        return {"scenarios": [], "generated_utc": None, "built": False}
    mtime = CATALOG_PATH.stat().st_mtime
    if _cache is None or mtime != _cache_mtime:
        _cache = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        _cache["built"] = True
        for sc in _cache.get("scenarios", []):
            for key in ("image_a", "image_b"):
                img = sc.get(key) or {}
                if img.get("url"):
                    img["thumb_url"] = _thumbnail(img["url"])
        _cache_mtime = mtime
    return _cache


def _thumbnail(url: str) -> str:
    """
    Small JPEG for the scenario cards, generated once next to the scene tiles.

    The cards used to load the full scene PNGs - over half a megabyte each, ten
    of them - which is most of the first paint through a tunnel. Falls back to
    the full image if the thumbnail cannot be written.
    """
    src = SCENES_DIR / Path(url).name
    dst = THUMB_DIR / f"{src.stem}.jpg"
    try:
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            img = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return url
            scale = THUMB_MAX / max(img.shape[:2])
            if scale < 1:
                img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            THUMB_DIR.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    except OSError:
        return url
    return f"/static/scenes/thumbs/{dst.name}"


def list_scenarios() -> List[Dict]:
    return load_catalog().get("scenarios", [])


def get_scenario(scenario_id: str) -> Optional[Dict]:
    for s in list_scenarios():
        if s.get("id") == scenario_id:
            return s
    return None
