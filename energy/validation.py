"""Validate source inputs without learning values or consulting future readings."""

from collections import defaultdict
from collections.abc import Mapping
import csv
from datetime import datetime, timedelta
from io import StringIO
import math
from numbers import Real
import re

import pandas as pd

from energy.contracts import (
    CellIssue, Correction, INPUT_FIELDS, TelemetryError, TelemetryRow,
    TIMESTAMP_FORMAT, ValidationResult, WEATHER_FIELDS,
)

MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_ROWS = 10_000
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\Z")


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value.strip()):
        raise ValueError("Use YYYY-MM-DD HH:MM:SS in dataset-local time.")
    return datetime.strptime(value.strip(), TIMESTAMP_FORMAT)


def _missing(value) -> bool:
    return (value is None or value is pd.NA or value is pd.NaT
            or isinstance(value, str) and not value.strip()
            or isinstance(value, Real) and math.isnan(float(value)))


def _numeric(value, column: str) -> float | None:
    if _missing(value):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, Real)):
        raise ValueError("Expected a finite numeric value.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Expected a finite numeric value.")
    if column == "humidity_pct" and not 0 <= number <= 100:
        raise ValueError("Humidity must be between 0 and 100 percent.")
    if column == "solar_irradiance_wm2" and number < 0:
        raise ValueError("Solar irradiance cannot be negative.")
    return number


def parse_telemetry(source, *, max_rows: int | None = None) -> ValidationResult:
    records = source.to_dict(orient="records") if isinstance(source, pd.DataFrame) else list(source)
    if not records:
        raise TelemetryError("Telemetry is empty.")
    if max_rows is not None and len(records) > max_rows:
        raise TelemetryError(f"Source exceeds row limit ({max_rows}).")
    result = ValidationResult(source_count=len(records))
    original = []
    times = defaultdict(list)
    extras = set()
    for position, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TelemetryError("Every telemetry row must be an object.")
        cleaned = {}
        for key, value in record.items():
            if not isinstance(key, str):
                raise TelemetryError("Telemetry column names must be strings.")
            name = key.lstrip("\ufeff").strip()
            if name in cleaned:
                raise TelemetryError(f"Duplicate column: {name}.")
            cleaned[name] = value
        missing_columns = set(INPUT_FIELDS) - cleaned.keys()
        if missing_columns:
            raise TelemetryError("Missing columns: " + ", ".join(sorted(missing_columns)))
        extras.update(set(cleaned) - set(INPUT_FIELDS))
        entry = {"position": position, "timestamp": cleaned["timestamp"], "time": None, "values": {}}
        try:
            entry["time"] = parse_timestamp(cleaned["timestamp"])
            times[entry["time"]].append(entry)
        except (ValueError, TypeError):
            result.errors.append(CellIssue(position + 1, "timestamp", "INVALID_TIMESTAMP",
                                           "Use a valid YYYY-MM-DD HH:MM:SS timestamp."))
        for column in WEATHER_FIELDS:
            try:
                entry["values"][column] = _numeric(cleaned[column], column)
            except (ValueError, TypeError, OverflowError) as error:
                entry["values"][column] = None
                result.errors.append(CellIssue(position + 1, column, "INVALID_VALUE", str(error)))
        original.append(entry)
    if extras:
        result.warnings.append("Excluded extra columns: " + ", ".join(sorted(extras)))
    invalid = {(issue.row, issue.column) for issue in result.errors}
    for entry in original:
        position = entry["position"]
        if entry["time"] is None:
            continue
        values = entry["values"].copy()
        for column, value in values.items():
            if value is not None or (position + 1, column) in invalid:
                continue
            previous = times.get(entry["time"] - timedelta(hours=1), [])
            if (len(times[entry["time"]]) == 1 and len(previous) == 1
                    and previous[0]["values"][column] is not None):
                values[column] = previous[0]["values"][column]
                result.corrections.append(Correction(position + 1, column,
                    previous[0]["position"] + 1, values[column]))
            else:
                result.errors.append(CellIssue(position + 1, column, "MISSING_VALUE",
                    "Supply a value; only one missing consecutive hour can be carried forward."))
        if all(value is not None for value in values.values()):
            result.rows.append(TelemetryRow(entry["timestamp"], entry["time"], position, **values))
    return result


def parse_csv(data: bytes, *, max_bytes: int | None = MAX_SOURCE_BYTES,
              max_rows: int | None = MAX_SOURCE_ROWS) -> ValidationResult:
    if max_bytes is not None and len(data) > max_bytes:
        raise TelemetryError("CSV exceeds upload size limit.")
    try:
        reader = csv.DictReader(StringIO(data.decode("utf-8-sig")), strict=True)
        headers = [name.strip() for name in reader.fieldnames or []]
        if len(headers) != len(set(headers)):
            raise TelemetryError("CSV contains duplicate columns.")
        if not set(INPUT_FIELDS).issubset(headers):
            raise TelemetryError("CSV is missing required columns.")
        records = []
        for record in reader:
            if None in record:
                raise TelemetryError("CSV row has more cells than the header.")
            records.append(record)
            if max_rows is not None and len(records) > max_rows:
                raise TelemetryError(f"CSV exceeds row limit ({max_rows}).")
    except (UnicodeDecodeError, csv.Error) as error:
        raise TelemetryError("CSV must be valid UTF-8 with comma-separated fields.") from error
    return parse_telemetry(records)


def _hour_index(result: ValidationResult) -> dict[datetime, list[TelemetryRow]]:
    index = defaultdict(list)
    for row in result.require_valid():
        if row.time.minute == 0 and row.time.second == 0:
            index[row.time].append(row)
    return index


def forecast_windows(result: ValidationResult) -> list[str]:
    index = _hour_index(result)
    return [start.strftime(TIMESTAMP_FORMAT) for start in sorted(index)
            if all(len(index.get(start + timedelta(hours=hour), [])) == 1 for hour in range(24))]


def select_forecast_window(result: ValidationResult, window_start: str) -> list[TelemetryRow]:
    try:
        start = parse_timestamp(window_start)
    except ValueError as error:
        raise TelemetryError("Select a valid hourly window start.") from error
    index = _hour_index(result)
    if start.minute or start.second or any(
        len(index.get(start + timedelta(hours=hour), [])) != 1 for hour in range(24)
    ):
        raise TelemetryError("Window must contain 24 unique consecutive hourly readings.")
    return [index[start + timedelta(hours=hour)][0] for hour in range(24)]
