from __future__ import annotations

from fastapi import APIRouter

from city_brain.pipeline.orchestrator import Pipeline, PipelineResult
from city_brain.schemas.guardian import GuardianVerdict
from city_brain.schemas.twin import DispatchCommand, SensorReading

router = APIRouter()
_pipeline = Pipeline()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ingest", response_model=PipelineResult)
async def ingest(reading: SensorReading) -> PipelineResult:
    """Feed a reading through the full pipeline: detect -> decide -> gate -> dispatch."""
    return await _pipeline.process(reading)


@router.post("/verify_reading")
async def verify_reading(verdict: GuardianVerdict) -> dict[str, str]:
    return {"received": verdict.correlation_id}


@router.post("/dispatch")
async def dispatch(command: DispatchCommand) -> dict[str, str]:
    return {"dispatched": command.correlation_id}