"""Train the City Brain decision model.

Generates a synthetic dataset of (reading -> action) examples, trains a
RandomForest classifier, saves it to models/city_brain_v1.pkl.

Run once:  python scripts/train_model.py
"""

from __future__ import annotations

import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# ---------------------------------------------------------------------------
# Label space: the actions the model can choose.
# ---------------------------------------------------------------------------
ACTIONS = [
    "dispatch_ambulance_police",   # accidents
    "dispatch_fire_ambulance",     # fires
    "retime_traffic_signal",       # traffic jams
    "open_valve",                  # floods
    "no_action",                   # fallback / nothing detected
]

# ---------------------------------------------------------------------------
# Feature space: what the model sees per reading.
# ---------------------------------------------------------------------------
FEATURES = [
    "is_emergency_call",     # 0/1
    "is_traffic",            # 0/1
    "is_water",              # 0/1
    "is_air",                # 0/1
    "is_power",              # 0/1
    "is_critical",           # 0/1
    "value_normalized",      # 0..1
    "incident_accident",     # 0/1
    "incident_fire",         # 0/1
    "incident_flood",        # 0/1
    "incident_other",        # 0/1
]

SENSOR_TYPES = ["emergency_call", "traffic", "water", "air", "power"]
EMERGENCY_SUBTYPES = ["accident", "fire", "flood", "medical", "other"]


def _random_reading() -> dict:
    """Generate one synthetic reading."""
    stype = random.choices(
        SENSOR_TYPES,
        weights=[0.35, 0.35, 0.15, 0.10, 0.05],
        k=1,
    )[0]
    severity = "critical" if random.random() < 0.35 else "normal"

    reading: dict = {"type": stype, "severity_class": severity, "value": None}

    if stype == "emergency_call":
        reading["incident_type"] = random.choices(
            EMERGENCY_SUBTYPES,
            weights=[0.4, 0.3, 0.15, 0.1, 0.05],
            k=1,
        )[0]
    elif stype in ("traffic", "water", "air", "power"):
        reading["value"] = round(random.uniform(0.0, 1.0), 3)

    return reading


def _label(reading: dict) -> str:
    """Ground-truth action for a reading (rule-based, defines the label)."""
    if reading["type"] == "emergency_call":
        it = reading.get("incident_type", "other")
        if it == "accident":
            return "dispatch_ambulance_police"
        if it == "fire":
            return "dispatch_fire_ambulance"
        if it == "flood":
            return "open_valve"
        return "no_action"

    if reading["type"] == "traffic" and reading["value"] is not None:
        if reading["value"] > 0.8:
            return "retime_traffic_signal"

    if reading["type"] == "water" and reading["value"] is not None:
        if reading["value"] > 0.7:
            return "open_valve"

    return "no_action"


def _features(reading: dict) -> list[float]:
    """Convert a reading into the feature vector the model consumes."""
    stype = reading["type"]
    sev = reading["severity_class"]
    it = reading.get("incident_type", "")
    val = reading.get("value")

    return [
        1.0 if stype == "emergency_call" else 0.0,
        1.0 if stype == "traffic" else 0.0,
        1.0 if stype == "water" else 0.0,
        1.0 if stype == "air" else 0.0,
        1.0 if stype == "power" else 0.0,
        1.0 if sev == "critical" else 0.0,
        float(val) if val is not None else 0.0,
        1.0 if it == "accident" else 0.0,
        1.0 if it == "fire" else 0.0,
        1.0 if it == "flood" else 0.0,
        1.0 if it in ("medical", "other", "") else 0.0,
    ]


def main() -> None:
    random.seed(42)
    np.random.seed(42)

    N = 2000
    print(f"Generating {N} synthetic readings...")
    readings = [_random_reading() for _ in range(N)]
    X = np.array([_features(r) for r in readings])
    y = np.array([_label(r) for r in readings])

    print("Class distribution:")
    for action in ACTIONS:
        count = int((y == action).sum())
        print(f"  {action:32s} {count}")

    print("\nTraining RandomForest...")
    clf = RandomForestClassifier(
        n_estimators=50,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X, y)

    acc = clf.score(X, y)
    print(f"Training accuracy: {acc:.3f}")

    # Feature importances (nice for the report)
    print("\nFeature importances:")
    for name, imp in sorted(
        zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1]
    ):
        print(f"  {name:24s} {imp:.3f}")

    out = Path("models")
    out.mkdir(exist_ok=True)
    out_file = out / "city_brain_v1.pkl"
    joblib.dump({"model": clf, "features": FEATURES, "actions": ACTIONS}, out_file)
    print(f"\nSaved model to {out_file}")


if __name__ == "__main__":
    main()