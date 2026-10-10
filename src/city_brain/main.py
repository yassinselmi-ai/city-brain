"""FastAPI application entrypoint.

Preloads the decision model at startup so the first pipeline call
doesn't pay the ~1s .pkl load cost on the critical path (§3.1).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from city_brain.api.routes import router
from city_brain.config import settings
from city_brain.decision.model import get_model

logging.basicConfig(level=settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("City Brain starting — preloading decision model...")
    m = get_model()
    log.info("decision model preloaded ready=%s path=%s", m.ready, m.path)
    yield
    log.info("City Brain stopping")


app = FastAPI(title="City Brain", version="0.1.0", lifespan=lifespan)
app.include_router(router)