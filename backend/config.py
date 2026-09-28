"""
Configuration for the Lunar Correspondence Engine.

Paths are anchored on PROJECT_ROOT, which is resolved from this file's location
and can be overridden with LCE_PROJECT_ROOT. Keeping the project root explicit
ensures the local API finds the data and generated assets regardless of the
directory from which Uvicorn is started.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---------------------------------------------------------------- #
_here = Path(__file__).resolve().parent          # .../backend
PROJECT_ROOT = Path(os.getenv("LCE_PROJECT_ROOT", _here.parent)).resolve()

BACKEND_DIR = _here
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = PROJECT_ROOT                            # PDS4 bundles sit at the root
SCENES_DIR = BACKEND_DIR / "static" / "scenes"    # generated scenario tiles
CATALOG_PATH = DATA_DIR / "scenarios.json"
STATIC_DIR = BACKEND_DIR / "static"
RESULTS_DIR = STATIC_DIR / "results"              # per-run JSON, for CSV export
EXAMPLES_DIR = PROJECT_ROOT / "examples"          # generated worked examples
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist" # production build, served when present

# --- Tiling --------------------------------------------------------------- #
# Tiles are cut at native sensor resolution from the geographic overlap of two
# strips. This is the setting that decides whether the demo is doing real
# sub-metre registration or matching 60 m/px mush.
TILE_SIZE = 1024
TILE_MIN_USABLE_FRACTION = 0.55   # reject tiles that are mostly fill/saturation
TILE_MIN_TEXTURE = 3.0            # reject featureless tiles

# --- Matching ------------------------------------------------------------- #
MATCH_MAX_DIM = 1024              # matcher works at this size; coords restored after
MAX_KEYPOINTS = 2048
MATCH_CONF_THRESHOLD = 0.10

# --- Geometry ------------------------------------------------------------- #
RANSAC_REPROJ_THRESH = 3.0
RANSAC_MAX_ITERS = 10_000
RANSAC_CONFIDENCE = 0.9999

# --- Preprocessing -------------------------------------------------------- #
CLAHE_CLIP_LIMIT = 3.0
CLAHE_GRID_SIZE = (8, 8)
SHADOW_THRESHOLD = 10

THUMBNAIL_SIZE = (512, 512)

# --- API ------------------------------------------------------------------ #
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "LCE_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    ).split(",")
    if o.strip()
]

# --- AI assistant (optional; the app is fully usable without these) -------- #
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "iWNf11sz1GrUE4ppxTOL")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
