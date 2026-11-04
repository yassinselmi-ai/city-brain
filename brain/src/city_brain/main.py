"""FastAPI application entrypoint.

Preloads the decision model and connects to PostgreSQL at startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from city_brain.api.routes import router
from city_brain.audit.db import audit_db
from city_brain.config import settings
from city_brain.decision.model import get_model

logging.basicConfig(level=settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("City Brain starting...")

    # Preload decision model
    m = get_model()
    log.info("decision model preloaded ready=%s path=%s", m.ready, m.path)

    # Connect to PostgreSQL (creates audit_log table if missing)
    try:
        await audit_db.connect()
        log.info("audit db ready events=%d", await audit_db.count())
    except Exception as e:
        log.error("audit db unavailable, running in memory-only mode: %s", e)

    yield

    # Shutdown
    await audit_db.close()
    log.info("City Brain stopping")


app = FastAPI(title="City Brain", version="0.1.0", lifespan=lifespan)
app.include_router(router)