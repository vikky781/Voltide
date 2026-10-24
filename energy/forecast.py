"""Compose validated weather, remote predictions, fixed rules, and simulation."""

from dataclasses import asdict
from datetime import datetime, timezone
import math
from typing import Protocol
from uuid import uuid4

from energy.battery import simulate_battery
from energy.contracts import BatterySettings, PredictionError
from energy.controller import evaluate_dispatch
from energy.features import build_features, FEATURE_VERSION
from energy.validation import parse_telemetry, select_forecast_window, MAX_SOURCE_ROWS


class PredictionClient(Protocol):
    model_version: str

    def predict_rows(self, features: list[dict]) -> list[float]: ...


class ForecastService:
    def __init__(self, client: PredictionClient):
        self.client = client

    def run(self, source_rows, window_start: str,
            battery_settings: dict | BatterySettings | None = None) -> dict:
        settings = (battery_settings if isinstance(battery_settings, BatterySettings)
                    else BatterySettings(**(battery_settings or {})))
        validated = parse_telemetry(source_rows, max_rows=MAX_SOURCE_ROWS)
        rows = select_forecast_window(validated, window_start)
        predictions = self.client.predict_rows(build_features(rows))
        if len(predictions) != len(rows):
            raise PredictionError("QuickML must return one prediction for every selected hour.")
        try:
            dispatch = [evaluate_dispatch(row.timestamp, prediction)
                        for row, prediction in zip(rows, predictions)]
        except (TypeError, ValueError) as error:
            raise PredictionError("QuickML returned an invalid demand prediction.") from error
        hourly = simulate_battery(dispatch, settings)
        return {
            "run_id": str(uuid4()), "model_version": self.client.model_version,
            "feature_version": FEATURE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "saved": False, "warnings": [*validated.warnings,
                "Run is not saved until cloud persistence is connected."],
            "battery_provenance": "SIMULATED", "battery_settings": settings.model_dump(),
            "source_positions": [row.position for row in rows],
            "corrections": [asdict(correction) for correction in validated.corrections],
            "summary": {
                "peak_demand_kw": max(row.target_demand_kw for row in hourly),
                "total_energy_kwh": math.fsum(row.target_demand_kw for row in hourly),
                "storage_hours": sum(row.requested_mode == "RENEWABLE_STORAGE" for row in hourly),
                "critical_hours": sum(row.critical_overload for row in hourly),
                "final_soc_pct": hourly[-1].battery_soc_end_pct,
                "unserved_energy_kwh": math.fsum(row.unserved_kw for row in hourly),
            },
            "hourly": [asdict(row) for row in hourly],
        }
