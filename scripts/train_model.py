"""Train the City Brain decision model (v2).

Improvements over v1:
  - 20k examples (up from 2k)
  - Realistic feature distribution (time of day, day of week, zone, trend)
  - Seasonal/hourly incident patterns
  - 3% label noise to avoid overfitting
  - Proper train/test split with accuracy reporting

Run once:  python scripts/train_model.py
Output:    models/city_brain_v1.pkl
"""

from __future__ import annotations

import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

ACTIONS = [
    "dispatch_ambulance_police",
    "dispatch_fire_ambulance",
    "retime_traffic_signal",
    "open_valve",
    "no_action",
]

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
    "hour_of_day",
    "day_of_week",
    "zone_index",
    "value_trend",
    "recent_incidents_zone",
]

SENSOR_TYPES = ["emergency_call", "traffic", "water", "air", "power"]
EMERGENCY_SUBTYPES = ["accident", "fire", "flood", "medical", "other"]
ZONES = ["downtown", "harbor", "north", "south", "airport", "industrial"]


def _seasonal_weights(month: int) -> dict[str, float]:
    if month in (6, 7, 8):
        return {"accident": 0.35, "fire": 0.40, "flood": 0.05, "medical": 0.15, "other": 0.05}
    if month in (10, 11, 12, 1):
        return {"accident": 0.35, "fire": 0.15, "flood": 0.30, "medical": 0.15, "other": 0.05}
    return {"accident": 0.40, "fire": 0.25, "flood": 0.15, "medical": 0.15, "other": 0.05}


def _traffic_weights(hour: int) -> float:
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return 0.50
    if 10 <= hour <= 16:
        return 0.30
    return 0.15


def _random_reading() -> dict:
    hour = random.choices(
        range(24),
        weights=[_traffic_weights(h) for h in range(24)],
        k=1,
    )[0]
    day = random.randint(0, 6)
    month = random.randint(1, 12)
    zone = random.choice(ZONES)

    stype_weights = [0.25, _traffic_weights(hour), 0.10, 0.10, 0.05]
    stype = random.choices(SENSOR_TYPES, weights=stype_weights, k=1)[0]
    severity = "critical" if random.random() < 0.35 else "normal"

    reading: dict = {
        "type": stype,
        "severity_class": severity,
        "hour": hour,
        "day": day,
        "month": month,
        "zone": zone,
        "value": None,
        "trend": 0.0,
        "recent_incidents": random.randint(0, 10),
    }

    if stype == "emergency_call":
        weights = _seasonal_weights(month)
        reading["incident_type"] = random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1,
        )[0]
    elif stype in ("traffic", "water", "air", "power"):
        reading["value"] = round(random.uniform(0.0, 1.0), 3)
        reading["trend"] = round(random.uniform(-0.3, 0.3), 3)

    return reading


def _label(reading: dict) -> str:
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
        if reading["value"] > 0.7 or reading["trend"] > 0.2:
            return "open_valve"

    return "no_action"


def _apply_label_noise(y: list[str], noise: float = 0.03) -> list[str]:
    out = []
    for label in y:
        if random.random() < noise:
            out.append(random.choice(ACTIONS))
        else:
            out.append(label)
    return out


def _zone_index(zone: str) -> float:
    return (hash(zone) % 1000) / 1000.0


def _features(reading: dict) -> list[float]:
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
        reading["hour"] / 23.0,
        reading["day"] / 6.0,
        _zone_index(reading["zone"]),
        reading.get("trend", 0.0),
        min(reading.get("recent_incidents", 0), 10) / 10.0,
    ]


def main() -> None:
    random.seed(42)
    np.random.seed(42)

    N = 20_000
    print(f"Generating {N} synthetic readings (v2)...")
    readings = [_random_reading() for _ in range(N)]
    X = np.array([_features(r) for r in readings])
    y_raw = [_label(r) for r in readings]
    y = _apply_label_noise(y_raw, noise=0.03)

    print("\nClass distribution:")
    for action in ACTIONS:
        count = sum(1 for label in y if label == action)
        print(f"  {action:32s} {count:5d}")

    print("\nSplitting train/test 80/20...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    print("Training RandomForest (100 trees, max_depth=10)...")
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"\nTrain accuracy: {train_acc:.4f}")
    print(f"Test  accuracy: {test_acc:.4f}")

    print("\nClassification report (test set):")
    print(classification_report(y_test, clf.predict(X_test), zero_division=0))

    print("Feature importances:")
    for name, imp in sorted(
        zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1]
    ):
        print(f"  {name:24s} {imp:.4f}")

    out = Path("models")
    out.mkdir(exist_ok=True)
    out_file = out / "city_brain_v1.pkl"
    joblib.dump({"model": clf, "features": FEATURES, "actions": ACTIONS}, out_file)
    print(f"\nSaved model to {out_file}")


if __name__ == "__main__":
    main()