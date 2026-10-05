from __future__ import annotations
from fastapi import APIRouter
from city_brain.schemas.guardian import GuardianVerdict
from city_brain.schemas.twin import DispatchCommand

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/verify_reading")
async def verify_reading(verdict: GuardianVerdict) -> dict[str, str]:
    return {"received": verdict.correlation_id}


@router.post("/dispatch")
async def dispatch(command: DispatchCommand) -> dict[str, str]:
    return {"dispatched": command.correlation_id}
