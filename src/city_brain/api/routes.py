from __future__ import annotations

from fastapi import APIRouter
from city_brain.mcp import get_tools
from city_brain.mcp.schemas import MCPTool

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
@router.get("/mcp/tools", response_model=list[MCPTool])
async def mcp_tools() -> list[MCPTool]:
    """MCP-style tool discovery endpoint.

    Returns the list of callable tools exposed by City Brain, with
    JSON schemas for their inputs and outputs. Mirrors the MCP
    (Model Context Protocol) tool listing convention.
    """
    return get_tools()