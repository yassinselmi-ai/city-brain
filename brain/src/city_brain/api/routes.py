from __future__ import annotations
from city_brain.observability.metrics import METRICS
from fastapi import APIRouter
from city_brain.mcp import get_tools
from city_brain.mcp.schemas import MCPTool

from city_brain.audit.db import audit_db
from city_brain.ingestion.stream import RedisStreamConsumer
import redis.asyncio as aioredis
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
    """Direct HTTP ingestion for testing.

    Note: production ingestion goes through the Redis consumer
    (scripts/run_consumer.py). This endpoint is kept for manual tests
    and for the /docs interactive UI.
    """
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
@router.get("/metrics")
async def metrics() -> dict:
    """Operational metrics for observability and evaluation.

    Includes critical-path parallelism gains, near-misses, dispatch/discard
    counts. See ARCHITECTURE.md §3 and §8.
    """
    return METRICS.snapshot()
@router.get("/audit/{correlation_id}")
async def audit_trace(correlation_id: str) -> dict:
    """Full audit trail for one incident, read from PostgreSQL.

    Returns every event (reading_received, decision, verdict, dispatch, ...)
    in chronological order. Proof that the pipeline is fully traceable.
    """
    events = await audit_db.fetch_trace(correlation_id)
    return {
        "correlation_id": correlation_id,
        "count": len(events),
        "events": events,
    }


@router.get("/audit")
async def audit_count() -> dict:
    """Total number of audit events stored."""
    return {"total_events": await audit_db.count()}