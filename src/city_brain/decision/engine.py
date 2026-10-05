from __future__ import annotations
from dataclasses import dataclass, field
from city_brain.detection.rules import DetectedIncident, IncidentKind
from city_brain.schemas.twin import DispatchCommand


@dataclass
class Decision:
    correlation_id: str
    commands: list[DispatchCommand] = field(default_factory=list)


_RESPONSES: dict[IncidentKind, list[tuple[str, str, dict]]] = {
    IncidentKind.ACCIDENT: [("ambulance@{zone}", "dispatch", {})],
    IncidentKind.FIRE: [("fire_brigade@{zone}", "dispatch", {})],
    IncidentKind.TRAFFIC_JAM: [("traffic_signal@{zone}", "retime", {})],
    IncidentKind.FLOOD: [("valve@{zone}", "adjust", {})],
}


def decide(incident: DetectedIncident, trust_score: float) -> Decision:
    commands = [
        DispatchCommand(
            actuator_id=tmpl.format(zone=incident.zone),
            action=action,
            params=params,
            correlation_id=incident.correlation_id,
            trust_score=trust_score,
        )
        for tmpl, action, params in _RESPONSES.get(incident.kind, [])
    ]
    return Decision(correlation_id=incident.correlation_id, commands=commands)
