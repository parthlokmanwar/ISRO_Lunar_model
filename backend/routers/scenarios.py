"""Scenario catalogue endpoints."""
from fastapi import APIRouter, HTTPException

from services.scenarios import get_scenario, load_catalog

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
async def list_all():
    catalog = load_catalog()
    if not catalog.get("built"):
        raise HTTPException(
            status_code=503,
            detail="Scenario catalogue not built. Run: python scripts/build_scenarios.py",
        )
    return catalog


@router.get("/{scenario_id}")
async def get_one(scenario_id: str):
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Unknown scenario '{scenario_id}'")
    return scenario
