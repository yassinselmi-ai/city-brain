from __future__ import annotations
import logging
from typing import Any

log = logging.getLogger(__name__)


class AuditLogger:
    async def record(self, event_type: str, correlation_id: str, payload: dict[str, Any]) -> None:
        log.info("AUDIT %s correlation_id=%s payload=%s", event_type, correlation_id, payload)
