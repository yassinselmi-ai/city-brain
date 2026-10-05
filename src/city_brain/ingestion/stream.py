from __future__ import annotations
import abc
import logging
from collections.abc import AsyncIterator
from city_brain.schemas.twin import SensorReading

log = logging.getLogger(__name__)


class SensorStreamConsumer(abc.ABC):
    @abc.abstractmethod
    async def start(self) -> None: ...
    @abc.abstractmethod
    async def stop(self) -> None: ...
    @abc.abstractmethod
    def readings(self) -> AsyncIterator[SensorReading]: ...


class RedisStreamConsumer(SensorStreamConsumer):
    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        # TODO: connect redis.asyncio, XGROUP CREATE MKSTREAM
        self._running = True
        log.info("RedisStreamConsumer started")

    async def stop(self) -> None:
        self._running = False

    async def readings(self) -> AsyncIterator[SensorReading]:
        # TODO: XREADGROUP loop
        if False:  # pragma: no cover
            yield SensorReading.model_validate({})
        return
