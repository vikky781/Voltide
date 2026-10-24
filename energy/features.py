"""Fixed feature calculations shared by cloud-data preparation and inference."""

import math

from energy.contracts import TelemetryRow, WEATHER_FIELDS

FEATURE_VERSION = "v1"
FEATURE_NAMES = (*WEATHER_FIELDS, "hour", "hour_sin", "hour_cos", "weekday",
                 "month", "is_weekend", "cooling_degree_c")


def build_features(rows: list[TelemetryRow], *, version: str = FEATURE_VERSION) -> list[dict]:
    if version != FEATURE_VERSION:
        raise ValueError(f"Unsupported feature version: {version}.")
    features = []
    for row in rows:
        hour = row.time.hour
        features.append({
            **{name: getattr(row, name) for name in WEATHER_FIELDS},
            "hour": hour, "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "weekday": row.time.weekday(), "month": row.time.month,
            "is_weekend": int(row.time.weekday() >= 5),
            "cooling_degree_c": max(0.0, row.ambient_temp_c - 24.0),
        })
    return features
