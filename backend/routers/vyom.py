"""
Vyom AI Assistant router — powered by OpenRouter LLM.
Provides conversational interface for ISRO scientists to query
the Lunar Correspondence Engine using natural language.
"""
import io
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from config import (
    OPENROUTER_API_KEY, OPENROUTER_MODEL,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID
)

router = APIRouter(prefix="/api", tags=["vyom-ai"])

SYSTEM_PROMPT = """You are Vyom, the analysis assistant inside the Lunar Correspondence
Engine, a Chandrayaan-2 image registration prototype (SIH26166).

What the system does:
- Cuts native-resolution tiles from the geographic overlap of two PDS4 products,
  using the label corners as a prior and correcting them by normalised
  cross-correlation. On this dataset the OHRC labels are off by roughly 2 km
  along-track, which is larger than a tile, so this step is load-bearing.
- Normalises illumination (CLAHE, optional shadow suppression).
- Detects keypoints with DISK and matches them with LightGlue; SIFT + FLANN is
  the fallback.
- Fits a homography with MAGSAC++ and reports reprojection RMSE plus, where a
  scenario has a known transform, true corner error against it.

Sensors: OHRC ~0.25-0.3 m/px panchromatic; TMC-2 ~4.5 m/px stereo (16-bit);
IIRS 256 bands, 0.8-5.0 um, ~78 m/px.

Scenario provenance is REAL (two genuine overlapping observations), DERIVED (real
pixels through a sensor or band model) or SIMULATED (real pixels, modelled
illumination). DERIVED and SIMULATED carry a known ground-truth transform.

How to answer:
- Use the numbers in the supplied run context. Never invent metrics, and if no
  run has happened yet, say so and offer to run one.
- Be precise and brief. Prefer two or three sentences over a list unless the
  question genuinely has parts.
- Be straight about limits. Reprojection RMSE only shows the inliers agree with
  each other; a confident fit to wrong correspondences can post a good RMSE.
  Ground-truth corner error is the number that settles it. Fewer than about five
  inliers means the fit is degenerate and its residual is not evidence.
- The coverage map reflects where correspondences were reliable. It is not a
  slope or boulder hazard assessment, so do not present it as a landing
  decision."""


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    # The current run, so answers are about what is on screen rather than about
    # figures baked into the system prompt. The old prompt asserted a fixed
    # "RMSE = 0.196 px" regardless of what had been computed.
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None


@router.post("/tts")
async def generate_speech(req: TTSRequest):
    """
    Generate speech using ElevenLabs API.
    Streams audio/mpeg back to frontend with fallback.
    """
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=400, detail="ElevenLabs API key not configured")

    voice = req.voice_id or ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    # Clean markdown formatting from text for cleaner voice output
    clean_text = (
        req.text.replace("**", "")
        .replace("*", "")
        .replace("`", "")
        .replace("#", "")
        .replace("✅", "")
        .replace("⚠️", "")
        .replace("📊", "")
        .replace("🤖", "")
    )
    payload = {
        "text": clean_text[:800],
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"ElevenLabs error: {resp.text}")
            return StreamingResponse(io.BytesIO(resp.content), media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_with_vyom(request: ChatRequest):
    """
    Send a message to Vyom (the ISRO Lunar AI Assistant).
    Uses OpenRouter to access fast LLM inference.
    """
    if not OPENROUTER_API_KEY:
        return _offline_response(
            request.messages[-1].content if request.messages else "", request.context
        )

    system = SYSTEM_PROMPT
    if request.context:
        system += ("\n\nCurrent run on screen (JSON):\n"
                   + json.dumps(request.context, indent=2))
    else:
        system += "\n\nNo pipeline run has been executed yet in this session."

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            *[{"role": m.role, "content": m.content} for m in request.messages],
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://sih26166.isro.gov.in",
                    "X-Title": "Lunar Correspondence Engine",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {e.response.text}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM API timeout")

    reply = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    model_used = data.get("model", OPENROUTER_MODEL)

    return ChatResponse(reply=reply, model=model_used, tokens_used=tokens)


def _offline_response(user_msg: str, context: Optional[dict]) -> ChatResponse:
    """
    Answer without an LLM, from the run context alone.

    The previous offline path returned invented figures - a fixed 0.196 px RMSE,
    "1,643 keypoints", "27 inliers" - phrased as though they described the current
    run. Anything stated here now comes from the run that is actually loaded, and
    when there is no run the honest answer is that there is nothing to report yet.
    """
    msg = (user_msg or "").lower()

    if not context or not context.get("metrics"):
        return ChatResponse(
            reply=("No pipeline run has been executed yet, so there are no metrics to "
                   "report. Pick a scenario on the left and run the pipeline, then ask "
                   "again.\n\n*(The language model is not configured, so this is the "
                   "built-in offline response.)*"),
            model="offline",
            tokens_used=0,
        )

    m = context["metrics"]
    gt = context.get("ground_truth_error")
    name = context.get("scenario", "the current scenario")
    lines: List[str] = []

    if any(w in msg for w in ("rmse", "accurate", "accuracy", "error", "precision")):
        lines.append(
            f"**{name}** fitted at **{m['rmse_px']:.3f} px** reprojection RMSE"
            + (f" ({m['rmse_m']:.3f} m at {m['gsd_m']} m/px)" if m.get("rmse_m") else "")
            + f", median {m['median_error_px']:.2f} px."
        )
        if gt:
            lines.append(
                f"True corner error against the known transform is "
                f"**{gt['mean_corner_error_px']:.2f} px**, which is the number worth "
                "quoting: RMSE only shows the inliers agree with each other."
            )
        if m.get("degenerate"):
            lines.append("Note the fit is degenerate - too few inliers for the residual to mean anything.")
    elif any(w in msg for w in ("inlier", "match", "keypoint", "feature", "consensus")):
        lines.append(
            f"{m['num_keypoints_a']:,} and {m['num_keypoints_b']:,} keypoints detected; "
            f"{m['num_matches']} putative correspondences, of which **{m['num_inliers']} "
            f"survived** ({m['inlier_ratio'] * 100:.1f}%)."
        )
    elif any(w in msg for w in ("provenance", "real", "synthetic", "derived", "simulated")):
        lines.append(
            f"This scenario is **{context.get('provenance', 'unknown')}**. REAL means two "
            "genuine overlapping observations; DERIVED and SIMULATED transform real pixels "
            "by a known transform, which is what makes ground-truth error available."
        )
    else:
        lines.append(
            f"**{name}** - {m['num_inliers']} inliers of {m['num_matches']} "
            f"({m['inlier_ratio'] * 100:.1f}%), RMSE {m['rmse_px']:.3f} px"
            + (f", true error {gt['mean_corner_error_px']:.2f} px" if gt else "")
            + f", {m['total_ms']:.0f} ms."
        )

    lines.append("\n*(Language model not configured; this is the built-in offline response.)*")
    return ChatResponse(reply="\n\n".join(lines), model="offline", tokens_used=0)
