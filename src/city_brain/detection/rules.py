from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from city_brain.schemas.twin import SensorReading

log = logging.getLogger(__name__)


class IncidentKind(StrEnum):
    ACCIDENT = "accident"
    FIRE = "fire"
    TRAFFIC_JAM = "traffic_jam"
    FLOOD = "flood"


@dataclass
class DetectedIncident:
    kind: IncidentKind
    correlation_id: str
    sensor_id: str
    zone: str
    severity_class: str
    evidence: dict = field(default_factory=dict)


def detect(reading: SensorReading) -> DetectedIncident | None:
    # TODO §5.1 emergency_call accident -> ACCIDENT
    # TODO §5.2 emergency_call fire    -> FIRE
    # TODO §5.3 sustained traffic      -> TRAFFIC_JAM
    # TODO §5.4 water level + rate     -> FLOOD
    return None
