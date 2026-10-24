from collections import OrderedDict, deque
import csv
from dataclasses import asdict
import hashlib
import hmac
from io import StringIO
import json
import os
from pathlib import Path
import secrets
from threading import Lock
from time import monotonic
from uuid import uuid4

from flask import Flask, Response, abort, g, jsonify, request, send_from_directory, session
from werkzeug.exceptions import BadRequest, HTTPException

from energy.contracts import BatterySettings, BatterySettingsError, PredictionError, TelemetryError
from energy.forecast import UNSAVED_WARNING
from energy.storage import StorageUnavailable
from energy.validation import (
    forecast_windows, MAX_SOURCE_BYTES, MAX_SOURCE_ROWS, parse_csv,
    parse_telemetry, select_forecast_window,
)


def create_app(*, service=None, repository_factory=None) -> Flask:
    app = Flask(__name__, static_folder=None)
    session_secret = os.environ.get("VOLTIDE_SESSION_SECRET", os.environ.get("SESSION_SECRET"))
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

    def session_scope():
        if 'voltide_session' not in session:
            session['voltide_session'] = secrets.token_urlsafe(32)
        return hmac.new(app.secret_key.encode(), session['voltide_session'].encode(), hashlib.sha256).hexdigest()

    def repository():
        if repository_factory is None:
            raise StorageUnavailable()
        if not hasattr(g, 'run_repository'):
            try:
                g.run_repository = repository_factory(request)
            except Exception as error:
                app.logger.warning('History SDK initialization failed (%s).', type(error).__name__)
                raise StorageUnavailable() from None
        return g.run_repository

    @app.errorhandler(StorageUnavailable)
    def unavailable_history(_error):
        return error_response('Forecast history is unavailable. Please try again later.', 503)

    @app.errorhandler(TelemetryError)
    def invalid_telemetry(error):
        return error_response(str(error), 422, [asdict(issue) for issue in error.issues])

    @app.errorhandler(PredictionError)
    def invalid_predictions(_error):
        return error_response("The model returned invalid predictions. Please retry later.", 502)

    @app.errorhandler(BatterySettingsError)
    def invalid_settings(error):
        issues = [asdict(issue) for issue in error.issues]
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
                       history_configured=repository_factory is not None,
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
        if repository_factory is not None:
            result['warnings'] = [warning for warning in result['warnings'] if warning != UNSAVED_WARNING]
            scope = session_scope()
            try:
                validated_rows = [{'position': row.position, **row.to_record()} for row in validated.rows]
                result['saved'] = repository().save_run(scope, result, records, validated_rows) is True
            except Exception:
                result['saved'] = False
            if not result['saved']:
                result['warnings'].append('The forecast could not be saved. History is unavailable for this run.')
        result["request_id"] = g.request_id
        return jsonify(result)

    @app.get('/api/runs')
    def history():
        scope = session_scope()
        return jsonify(runs=repository().list_runs(scope), request_id=g.request_id)

    def owned_run(run_id):
        result = repository().get_run(session_scope(), run_id)
        if result is None:
            abort(404, description='Forecast run was not found in this browser session.')
        return result

    @app.get('/api/runs/<run_id>')
    def get_run(run_id):
        result = owned_run(run_id)
        return jsonify(**result, request_id=g.request_id)

    @app.get('/api/runs/<run_id>/export')
    def export_run(run_id):
        kind = request.args.get('kind', 'predictions')
        if kind not in {'predictions', 'dispatch'}:
            raise BadRequest('Export kind must be predictions or dispatch.')
        result = owned_run(run_id)
        columns = ['timestamp', 'target_demand_kw']
        if kind == 'dispatch':
            columns += ['requested_mode', 'reasons', 'critical_overload', 'battery_soc_start_pct',
                        'battery_soc_end_pct', 'battery_delivered_kw', 'unserved_kw',
                        'storage_shortfall', 'alerts']
        output = StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in result['hourly']:
            writer.writerow({name: '|'.join(row[name]) if isinstance(row[name], list) else row[name]
                             for name in columns})
        return Response(output.getvalue(), mimetype='text/csv', headers={
            'Content-Disposition': f'attachment; filename="voltide-{run_id}-{kind}.csv"'})

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
    from energy.storage import repository_from_request

    settings = QuickMLSettings.from_env()
    bucket_name = os.environ.get('VOLTIDE_CATALYST_RUNS_BUCKET', os.environ.get('CATALYST_RUNS_BUCKET'))
    table_name = os.environ.get('VOLTIDE_CATALYST_RUNS_TABLE', os.environ.get('CATALYST_RUNS_TABLE', 'ForecastRuns'))
    factory = (lambda incoming: repository_from_request(incoming, bucket_name, table_name)) if bucket_name else None
    return create_app(service=ForecastService(QuickMLClient(settings)), repository_factory=factory)


if __name__ == "__main__":
    create_configured_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
