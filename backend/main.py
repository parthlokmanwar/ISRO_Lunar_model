"""
FastAPI application entry point.
Lunar Correspondence Engine — SIH26166
"""
import json
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    ALLOWED_ORIGINS, CATALOG_PATH, ELEVENLABS_API_KEY, EXAMPLES_DIR,
    FRONTEND_DIST, OPENROUTER_API_KEY, RESULTS_DIR, SCENES_DIR, STATIC_DIR,
)
from routers import analytics, examples, health, match, scenarios, vyom


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: verify catalog exists and static dir is ready."""
    for d in (STATIC_DIR, SCENES_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    if not CATALOG_PATH.exists():
        print("[WARN] No scenario catalogue. Run: python scripts/build_scenarios.py")
    else:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        scenarios = catalog.get("scenarios", [])
        print(f"[OK] {len(scenarios)} scenario(s) loaded:")
        for s in scenarios:
            gt = " + ground truth" if s.get("ground_truth_homography") else ""
            print(f"     {s['id']:26s} {s['provenance']}{gt}")

    n_ex = len(list(EXAMPLES_DIR.glob("*/result.json"))) if EXAMPLES_DIR.exists() else 0
    if n_ex:
        print(f"[OK] {n_ex} worked example(s) available")
    else:
        print("[INFO] No worked examples. Run: python scripts/build_examples.py")

    if OPENROUTER_API_KEY:
        print("[OK] Vyom AI: OpenRouter key configured")
    else:
        print("[WARN] Vyom AI: No OpenRouter key. Using rule-based fallback.")

    if ELEVENLABS_API_KEY:
        print("[OK] Vyom TTS: ElevenLabs key configured")
    else:
        print("[INFO] Vyom TTS: Using browser native speech synthesis")
    yield


app = FastAPI(
    title="Lunar Correspondence Engine",
    description="SIH26166 — Chandrayaan-2 multi-sensor image correspondence API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scene tiles live under static/scenes, so one mount covers everything the UI needs.
SCENES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# The worked-example figures are served straight from the folder they are
# generated into, so what the UI shows and what is committed cannot drift.
if EXAMPLES_DIR.exists():
    app.mount("/examples", StaticFiles(directory=str(EXAMPLES_DIR)), name="examples")

# Routers
app.include_router(health.router)
app.include_router(scenarios.router)
app.include_router(match.router)
app.include_router(vyom.router)
app.include_router(analytics.router)
app.include_router(examples.router)

# --------------------------------------------------------------------------- #
# Frontend                                                                      #
# --------------------------------------------------------------------------- #
# When a production build exists, serve it from the same origin as the API. That
# removes the dev proxy from the picture entirely, which matters when the app is
# reached through a tunnel: one origin, no CORS, no host allow-listing.
#
#   cd frontend && npm run build
#
# In development this block is simply skipped and Vite serves the app instead.
if FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse

    _assets = FRONTEND_DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/", include_in_schema=False)
    async def _index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def _spa(path: str):
        """
        Serve a built file if it exists, otherwise the app shell.

        Registered last so it never shadows /api, /static or /examples: FastAPI
        matches routes in declaration order.
        """
        candidate = (FRONTEND_DIST / path).resolve()
        if (
            str(candidate).startswith(str(FRONTEND_DIST.resolve()))
            and candidate.is_file()
        ):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
