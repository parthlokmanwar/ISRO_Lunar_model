"""
Worked examples.

The examples folder is generated offline by scripts/build_examples.py and holds a
complete run of every scenario with its figures. Serving it here means the demo
can show verified results instantly, and lets anyone compare what the interface
reports against what was recorded when the examples were built. If the two
disagree, something has regressed.
"""
import json

from fastapi import APIRouter, HTTPException

from config import EXAMPLES_DIR

router = APIRouter(prefix="/api/examples", tags=["examples"])


def _load() -> dict:
    index = EXAMPLES_DIR / "index.json"
    if not index.exists():
        raise HTTPException(
            status_code=503,
            detail="No worked examples yet. Run: python scripts/build_examples.py",
        )
    return json.loads(index.read_text(encoding="utf-8"))


@router.get("")
async def list_examples():
    data = _load()
    # Rewrite repo-relative figure paths to URLs the browser can fetch.
    for ex in data.get("examples", []):
        ex["figures"] = {
            name: "/" + path.replace("\\", "/")
            for name, path in (ex.get("figures") or {}).items()
        }
    return data


@router.get("/{example_id}")
async def get_example(example_id: str):
    for ex in _load().get("examples", []):
        if ex["id"] == example_id:
            ex["figures"] = {
                name: "/" + path.replace("\\", "/")
                for name, path in (ex.get("figures") or {}).items()
            }
            return ex
    raise HTTPException(status_code=404, detail=f"No example '{example_id}'")
