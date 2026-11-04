from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class Verdict(StrEnum):
    TRUSTED = "trusted"
    SUSPICIOUS = "suspicious"
    REJECTED = "rejected"


class GuardianVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correlation_id: str
    sensor_id: str
    ts: datetime
    seq: int
    trust_score: float = Field(..., ge=0.0, le=1.0)
    verdict: Verdict
    sig: str
    reason_codes: list[str] = Field(default_factory=list)
