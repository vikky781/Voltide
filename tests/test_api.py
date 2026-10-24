from datetime import datetime, timedelta
from io import BytesIO
import json

import pytest


def source(count=24):
    return [{"timestamp": (datetime(2015, 1, 1) + timedelta(hours=hour)).strftime("%Y-%m-%d %H:%M:%S"),
             "ambient_temp_c": 26, "humidity_pct": 60, "solar_irradiance_wm2": 100}
            for hour in range(count)]


def app_client(remote=None):
    from web.app import create_app
    from energy.forecast import ForecastService

    app = create_app(service=ForecastService(remote) if remote else None)
    app.config.update(TESTING=True)
    return app.test_client()


class RemoteFixture:
    model_version = "test-model"

    def predict_rows(self, records):
        return [125.0] * len(records)


def test_health_does_not_claim_unconfigured_model_is_ready():
    result = app_client().get("/api/health")
    assert result.status_code == 200
    assert result.json["status"] == "ok"
    assert result.json["model_configured"] is False
    assert result.json["request_id"]


def test_validate_json_has_windows_and_excludes_target():
    rows = source(25)
    rows[0]["target_demand_kw"] = 999
    result = app_client().post("/api/validate", json={"source_rows": rows})
    assert result.status_code == 200
    assert len(result.json["rows"]) == 25
    assert len(result.json["window_starts"]) == 2
    assert "target_demand_kw" not in result.json["rows"][0]
    assert result.json["warnings"]


def test_forecast_requires_real_service_and_never_returns_fallback():
    result = app_client().post("/api/forecast", json={
        "source_rows": source(), "window_start": "2015-01-01 00:00:00"})
    assert result.status_code == 503
    assert "hourly" not in result.json


def test_original_csv_correction_context_survives_preview_and_forecast():
    client = app_client(RemoteFixture())
    rows = source(25)
    rows[1]["ambient_temp_c"] = ""
    text = "timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2\n"
    text += "\n".join(",".join(str(row[key]) for key in [
        "timestamp", "ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]) for row in rows)
    preview = client.post("/api/validate", data={"file": (BytesIO(text.encode()), "weather.csv")})
    assert preview.status_code == 200
    forecast = client.post("/api/forecast", data={
        "file": (BytesIO(text.encode()), "weather.csv"),
        "window_start": "2015-01-01 01:00:00", "battery_settings": json.dumps({})})
    assert forecast.status_code == 200
    assert forecast.json["corrections"] == preview.json["corrections"]
    assert forecast.json["corrections"][0]["previous_row"] == 1
    assert forecast.json["hourly"][0]["timestamp"] == "2015-01-01 01:00:00"
    assert forecast.json["saved"] is False
    assert forecast.json["battery_provenance"] == "SIMULATED"


def test_invalid_cell_response_has_actionable_row_details():
    rows = source()
    rows[3]["humidity_pct"] = 101
    result = app_client(RemoteFixture()).post("/api/forecast", json={
        "source_rows": rows, "window_start": "2015-01-01 00:00:00"})
    assert result.status_code == 422
    assert result.json["errors"][0]["row"] == 4
    assert result.json["errors"][0]["column"] == "humidity_pct"


@pytest.mark.parametrize("payload", [None, [], {"source_rows": "oops"}, {"source_rows": []}])
def test_malformed_request_is_rejected(payload):
    result = app_client().post("/api/validate", json=payload)
    assert result.status_code in [400, 422]


def test_upload_body_limit_is_enforced():
    result = app_client().post("/api/validate", data={
        "file": (BytesIO(b"x" * (2 * 1024 * 1024 + 1)), "large.csv")})
    assert result.status_code == 413


def test_invalid_battery_json_is_a_client_error():
    result = app_client(RemoteFixture()).post("/api/forecast", data={
        "file": (BytesIO(b"timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2\n2015-01-01 00:00:00,26,60,100\n"), "weather.csv"),
        "battery_settings": "not-json", "window_start": "2015-01-01 00:00:00"})
    assert result.status_code == 400


def test_upstream_bad_predictions_are_not_reported_as_input_errors():
    class BadRemote:
        model_version = "fixture"

        def predict_rows(self, _):
            return []

    result = app_client(BadRemote()).post("/api/forecast", json={
        "source_rows": source(), "window_start": "2015-01-01 00:00:00"})
    assert result.status_code == 502


def test_public_forecast_route_has_bounded_request_rate():
    client = app_client(RemoteFixture())
    body = {"source_rows": source(), "window_start": "2015-01-01 00:00:00"}
    statuses = [client.post("/api/forecast", json=body).status_code for _ in range(6)]
    assert statuses == [200, 200, 200, 200, 200, 429]
