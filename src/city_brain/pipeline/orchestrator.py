"""The pipeline: reading -> incident? -> verdict -> decision -> dispatch.

Implements ARCHITECTURE.md §3 and §8.

Critical path (§3.1): decide first, hold, gate on verdict, then dispatch/discard.
Normal path (§3.2):   verify first, then decide, then dispatch.
Invariant: nothing is dispatched without a trusted Guardian verdict.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from city_brain.audit.log import AuditLogger
from city_brain.clients.guardian_client import GuardianClient
from city_brain.clients.twin_client import TwinClient
from city_brain.decision.engine import Decision, decide
from city_brain.decision.state_machine import IncidentState, IncidentStateMachine
from city_brain.detection.rules import detect
from city_brain.dispatch.trust_gate import TrustGate
from city_brain.schemas.guardian import GuardianVerdict
from city_brain.schemas.twin import ActionAck, SensorReading

log = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    correlation_id: str
    state: IncidentState
    incident_kind: str | None = None
    verdict: GuardianVerdict | None = None
    dispatched: list[ActionAck] = field(default_factory=list)
    discarded_reason: str | None = None


class Pipeline:
    def __init__(
        self,
        guardian: GuardianClient | None = None,
        twin: TwinClient | None = None,
        gate: TrustGate | None = None,
        audit: AuditLogger | None = None,
    ) -> None:
        self.guardian = guardian or GuardianClient()
        self.twin = twin or TwinClient()
        self.gate = gate or TrustGate()
        self.audit = audit or AuditLogger()

    async def process(self, reading: SensorReading) -> PipelineResult:
        sm = IncidentStateMachine(reading.correlation_id)
        log.info(
            "ingest sensor=%s type=%s corr=%s",
            reading.sensor_id,
            reading.type,
            reading.correlation_id,
        )
        await self.audit.record(
            "reading_received",
            reading.correlation_id,
            {"sensor_id": reading.sensor_id, "type": reading.type.value},
        )

        # 1. Detect
        incident = detect(reading)
        if incident is None:
            log.info("no incident detected corr=%s", reading.correlation_id)
            return PipelineResult(
                reading.correlation_id,
                sm.state,
                discarded_reason="no_incident",
            )

        # 2. Decide (held until verdict)
        decision: Decision = decide(incident, trust_score=0.0, reading=reading)
        log.info(
            "decision chosen_by=%s confidence=%.3f reason=%s",
            decision.chosen_by,
            decision.confidence,
            decision.reason,
        )
        sm.transition(IncidentState.DECIDED_HELD)
        await self.audit.record(
            "decided_held",
            reading.correlation_id,
            {
                "incident": incident.kind.value,
                "commands": len(decision.commands),
                "chosen_by": decision.chosen_by,
                "confidence": decision.confidence,
            },
        )

        # 3. Verify with Guardian
        verdict = await self.guardian.verify(reading)
        await self.audit.record(
            "guardian_verdict",
            reading.correlation_id,
            {
                "verdict": verdict.verdict.value if verdict else "unreachable",
                "trust_score": verdict.trust_score if verdict else None,
            },
        )

        # 4. Trust gate — fail-safe default: nothing dispatched without "trusted"
        gate_result = self.gate.check(verdict)
        if not gate_result.allowed:
            sm.transition(IncidentState.DISCARDED)
            log.warning(
                "discarded corr=%s reason=%s",
                reading.correlation_id,
                gate_result.reason,
            )
            await self.audit.record(
                "discarded",
                reading.correlation_id,
                {"reason": gate_result.reason},
            )
            return PipelineResult(
                reading.correlation_id,
                sm.state,
                incident_kind=incident.kind.value,
                verdict=verdict,
                discarded_reason=gate_result.reason,
            )

        # 5. Dispatch — re-stamp with real trust_score from Guardian
        assert verdict is not None
        for cmd in decision.commands:
            cmd.trust_score = verdict.trust_score

        acks: list[ActionAck] = []
        for cmd in decision.commands:
            ack = await self.twin.dispatch(cmd)
            if ack is not None:
                acks.append(ack)
            await self.audit.record(
                "dispatched",
                reading.correlation_id,
                {
                    "actuator_id": cmd.actuator_id,
                    "action": cmd.action,
                    "ack": ack.status if ack else "no_ack",
                },
            )

        sm.transition(IncidentState.DISPATCHED)
        log.info("dispatched corr=%s count=%d", reading.correlation_id, len(acks))
        return PipelineResult(
            reading.correlation_id,
            sm.state,
            incident_kind=incident.kind.value,
            verdict=verdict,
            dispatched=acks,
        )