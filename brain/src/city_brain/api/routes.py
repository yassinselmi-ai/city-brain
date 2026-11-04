from __future__ import annotations
from city_brain.observability.live_events import log_live_event

from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi import APIRouter

from city_brain.observability.metrics import METRICS
from city_brain.observability.live_events import get_live_events
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
    """
    # Enregistrer l'événement pour le dashboard AVANT de traiter
    log_live_event("Reading Arrived", f"Sensor: {reading.sensor_id} | Type: {reading.type.value} | Severity: {reading.severity_class.value}", "reading")
    
    # Lancer le pipeline
    result = await _pipeline.process(reading)
    
    # Enregistrer le résultat final
    if result.discarded_reason:
        log_live_event("Incident Discarded", f"Reason: {result.discarded_reason}", "discard")
    elif result.dispatched:
        log_live_event("Action Dispatched", f"Dispatched {len(result.dispatched)} actuator(s)", "dispatch")
        
    return result


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


# --- R3 Requirement: Live Timeline ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    # Try to read the HTML file
    html_path = Path(__file__).parent.parent / "static" / "dashboard.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Dashboard HTML not found</h1>"

@router.get("/api/live-events")
async def api_live_events():
    return get_live_events()