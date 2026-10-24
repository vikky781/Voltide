from collections import OrderedDict, deque
import csv
from dataclasses import asdict
from io import StringIO
import json
import os
from pathlib import Path
import secrets
from threading import Lock
from time import monotonic
from uuid import uuid4

from flask import Flask, abort, g, jsonify, request, send_from_directory
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, HTTPException

from energy.contracts import BatterySettings, PredictionError, TelemetryError
from energy.validation import (
    forecast_windows, MAX_SOURCE_BYTES, MAX_SOURCE_ROWS, parse_csv,
    parse_telemetry, select_forecast_window,
)


def create_app(*, service=None) -> Flask:
    app = Flask(__name__, static_folder=None)
    session_secret = os.environ.get("SESSION_SECRET")
    hosted = "X_ZOHO_CATALYST_LISTEN_PORT" in os.environ
    if hosted and not session_secret:
        raise RuntimeError("SESSION_SECRET is required in the hosted environment.")
    app.config.update(
        SECRET_KEY=session_secret or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=MAX_SOURCE_BYTES + 65536,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=hosted,
    )
    app.extensions["voltide_service"] = service
    buckets = OrderedDict()
    rate_lock = Lock()
    frontend = Path(__file__).resolve().parents[1] / "frontend" / "dist"

    @app.before_request
    def identify_request():
        g.request_id = str(uuid4())

    @app.after_request
    def response_headers(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def error_response(message, status, errors=None):
        return jsonify(error=message, errors=errors or [], request_id=g.request_id), status

    @app.errorhandler(TelemetryError)
    def invalid_telemetry(error):
        return error_response(str(error), 422, [asdict(issue) for issue in error.issues])

    @app.errorhandler(PredictionError)
    def invalid_predictions(_error):
        return error_response("The model returned invalid predictions. Please retry later.", 502)

    @app.errorhandler(ValidationError)
    def invalid_settings(error):
        issues = [{"row": 0, "column": ".".join(map(str, issue["loc"])),
                   "code": "INVALID_SETTING", "message": issue["msg"]}
                  for issue in error.errors(include_input=False, include_context=False)]
        return error_response("Battery settings are invalid.", 422, issues)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return error_response(error.description, error.code)

    def source_request():
        if "file" in request.files:
            data = request.files["file"].read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                abort(413, description="CSV exceeds the 2 MiB upload size limit.")
            validated = parse_csv(data)
            records = list(csv.DictReader(StringIO(data.decode("utf-8-sig")), strict=True))
            try:
                settings = json.loads(request.form.get("battery_settings", "{}"))
            except json.JSONDecodeError as error:
                raise BadRequest("battery_settings must be valid JSON.") from error
            body = {"window_start": request.form.get("window_start"), "battery_settings": settings}
        else:
            if request.content_length and request.content_length > MAX_SOURCE_BYTES:
                abort(413, description="Source exceeds the 2 MiB request size limit.")
            body = request.get_json(silent=True)
            if not isinstance(body, dict) or not isinstance(body.get("source_rows"), list):
                raise BadRequest("Provide source_rows as a JSON array or upload a CSV file.")
            records = body["source_rows"]
            validated = parse_telemetry(records, max_rows=MAX_SOURCE_ROWS)
        validated.require_valid()
        return body, records, validated

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", model_configured=app.extensions["voltide_service"] is not None,
                       request_id=g.request_id)

    @app.post("/api/validate")
    def validate():
        _, _, result = source_request()
        return jsonify(rows=[row.to_record() for row in result.rows],
            window_starts=forecast_windows(result), warnings=result.warnings,
            corrections=[asdict(item) for item in result.corrections], request_id=g.request_id)

    @app.post("/api/forecast")
    def forecast():
        body, records, validated = source_request()
        start = body.get("window_start")
        if not isinstance(start, str):
            raise BadRequest("Provide the selected window_start timestamp.")
        select_forecast_window(validated, start)
        settings = body.get("battery_settings", {})
        if not isinstance(settings, dict):
            raise BadRequest("battery_settings must be an object.")
        settings = BatterySettings(**settings)
        predictor = app.extensions["voltide_service"]
        if predictor is None:
            abort(503, description="A real QuickML endpoint has not been configured yet.")
        with rate_lock:
            now = monotonic()
            key = request.remote_addr or "unknown"
            bucket = buckets.setdefault(key, deque())
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= 5:
                abort(429, description="Forecast limit reached. Try again in a minute.")
            bucket.append(now)
            buckets.move_to_end(key)
            # Per-process protection; cloud quotas remain the account-wide boundary.
            while len(buckets) > 10000:
                buckets.popitem(last=False)
        result = predictor.run(records, start, settings)
        result["request_id"] = g.request_id
        return jsonify(result)

    @app.get("/")
    @app.get("/<path:path>")
    def frontend_file(path=""):
        if path.startswith("api/"):
            abort(404)
        if not (frontend / "index.html").is_file():
            return jsonify(application="Voltide", frontend_built=False,
                           health_url="/api/health"), 503
        if path and (frontend / path).is_file():
            return send_from_directory(frontend, path)
        return send_from_directory(frontend, "index.html")

    return app


def create_configured_app() -> Flask:
    from energy.config import QuickMLSettings
    from energy.forecast import ForecastService
    from energy.quickml import QuickMLClient

    return create_app(service=ForecastService(QuickMLClient(QuickMLSettings.from_env())))


if __name__ == "__main__":
    create_configured_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
