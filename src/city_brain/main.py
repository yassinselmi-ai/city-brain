from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from city_brain.api.routes import router
from city_brain.config import settings

logging.basicConfig(level=settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("City Brain starting")
    yield
    log.info("City Brain stopping")


app = FastAPI(title="City Brain", version="0.1.0", lifespan=lifespan)
app.include_router(router)
