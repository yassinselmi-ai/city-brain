"""Wrapper around the trained decision model.

Loads the RandomForest .pkl at import time, exposes a predict() that
takes a SensorReading and returns (action_name, confidence).

Falls back to None on any error, so callers can decide what to do.
"""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

from city_brain.config import settings
from city_brain.schemas.twin import SensorReading, SensorType

log = logging.getLogger(__name__)


# Must match the FEATURES list in scripts/train_model.py
FEATURES = [
    "is_emergency_call",
    "is_traffic",
    "is_water",
    "is_air",
    "is_power",
    "is_critical",
    "value_normalized",
    "incident_accident",
    "incident_fire",
    "incident_flood",
    "incident_other",
]


class DecisionModel:
    """Trained classifier + feature extractor."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.model_path)
        self._model = None
        self._actions: list[str] = []
        self._load()

    def _load(self) -> None:
        try:
            bundle = joblib.load(self.path)
            self._model = bundle["model"]
            self._actions = bundle["actions"]
            log.info("decision model loaded path=%s actions=%d", self.path, len(self._actions))
        except Exception as e:
            log.error("failed to load decision model from %s: %s", self.path, e)
            self._model = None

    @property
    def ready(self) -> bool:
        return self._model is not None

    def _extract_features(self, reading: SensorReading) -> list[float]:
        stype = reading.type
        sev = reading.severity_class
        it = (reading.emergency.incident_type.lower() if reading.emergency else "")
        val = reading.value if isinstance(reading.value, (int, float)) else None

        return [
            1.0 if stype == SensorType.EMERGENCY_CALL else 0.0,
            1.0 if stype == SensorType.TRAFFIC else 0.0,
            1.0 if stype == SensorType.WATER else 0.0,
            1.0 if stype == SensorType.AIR else 0.0,
            1.0 if stype == SensorType.POWER else 0.0,
            1.0 if sev.value == "critical" else 0.0,
            float(val) if val is not None else 0.0,
            1.0 if it == "accident" else 0.0,
            1.0 if it == "fire" else 0.0,
            1.0 if it == "flood" else 0.0,
            1.0 if it in ("medical", "other", "") else 0.0,
        ]

    def predict(self, reading: SensorReading) -> tuple[str, float] | None:
        """Return (action_name, confidence) or None if the model can't decide."""
        if not self.ready:
            return None
        try:
            x = np.array([self._extract_features(reading)])
            pred = self._model.predict(x)[0]
            proba = float(self._model.predict_proba(x).max())
            return str(pred), proba
        except Exception as e:
            log.warning("model.predict failed: %s", e)
            return None


# Module-level singleton so the .pkl is loaded once
_model_singleton: DecisionModel | None = None


def get_model() -> DecisionModel:
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = DecisionModel()
    return _model_singleton