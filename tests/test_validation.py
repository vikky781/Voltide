from datetime import datetime, timedelta
import math

import pandas as pd
import pytest


def telemetry(count=24, start=datetime(2015, 1, 1)):
    return [
        {"timestamp": (start + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S"),
         "ambient_temp_c": 26.0, "humidity_pct": 60.0, "solar_irradiance_wm2": 100.0}
        for i in range(count)
    ]


def test_csv_cleans_bom_headers_and_reports_excluded_target():
    from energy.validation import parse_csv

    result = parse_csv(b'\xef\xbb\xbftimestamp, ambient_temp_c ,humidity_pct,solar_irradiance_wm2,target_demand_kw\n2015-01-01 00:00:00, 26 ,60,100,999\n')
    assert result.require_valid()[0].to_record() == {
        "timestamp": "2015-01-01 00:00:00", "ambient_temp_c": 26.0,
        "humidity_pct": 60.0, "solar_irradiance_wm2": 100.0,
    }
    assert any("target_demand_kw" in warning for warning in result.warnings)


@pytest.mark.parametrize("field,value", [
    ("humidity_pct", -1), ("humidity_pct", 101), ("solar_irradiance_wm2", -1),
    ("ambient_temp_c", "oops"), ("ambient_temp_c", float("inf")),
    ("ambient_temp_c", True), ("ambient_temp_c", "NaN"),
    ("timestamp", "2015-02-30 00:00:00"), ("timestamp", "2015-01-01T00:00:00Z"),
])
def test_invalid_cells_have_source_row_and_column(field, value):
    from energy.validation import parse_telemetry, TelemetryError

    rows = telemetry(2)
    rows[1][field] = value
    result = parse_telemetry(rows)
    assert any(issue.row == 2 and issue.column == field for issue in result.errors)
    with pytest.raises(TelemetryError):
        result.require_valid()


def test_single_missing_value_uses_previous_original_hour_and_keeps_provenance():
    from energy.validation import parse_telemetry, select_forecast_window

    source = telemetry(25)
    source[0]["ambient_temp_c"] = 28
    source[1]["ambient_temp_c"] = ""
    result = parse_telemetry(source)
    selected = select_forecast_window(result, "2015-01-01 01:00:00")
    assert len(selected) == 24
    assert selected[0].ambient_temp_c == 28.0
    assert result.corrections[0].row == 2
    assert result.corrections[0].column == "ambient_temp_c"
    assert result.corrections[0].previous_row == 1
    assert result.corrections[0].value == 28.0
    assert source[1]["ambient_temp_c"] == ""


@pytest.mark.parametrize("positions", [[0], [1, 2]])
def test_missing_leading_or_consecutive_values_are_not_invented(positions):
    from energy.validation import parse_telemetry

    rows = telemetry(3)
    for position in positions:
        rows[position]["humidity_pct"] = None
    result = parse_telemetry(rows)
    assert result.errors
    assert result.errors[-1].column == "humidity_pct"


def test_missing_value_does_not_cross_gap_or_ambiguous_timestamp():
    from energy.validation import parse_telemetry

    rows = telemetry(3)
    rows[2]["humidity_pct"] = None
    assert parse_telemetry([rows[0], rows[2]]).errors
    assert parse_telemetry([rows[0], rows[1], rows[1].copy(), rows[2]]).errors


def test_pandas_missing_marker_is_cleaned_without_mutating_dataframe():
    from energy.validation import parse_telemetry

    frame = pd.DataFrame(telemetry(2))
    frame.loc[1, "humidity_pct"] = math.nan
    result = parse_telemetry(frame)
    assert result.require_valid()[1].humidity_pct == 60.0
    assert pd.isna(frame.loc[1, "humidity_pct"])


def test_evaluator_rows_keep_order_duplicates_and_timestamp_text():
    from energy.validation import parse_telemetry

    rows = telemetry(25)
    rows = [rows[-1], rows[0], rows[0].copy(), *rows[1:-1]]
    rows[0]["timestamp"] = " 2015-01-02 00:00:00 "
    cleaned = parse_telemetry(rows).require_valid()
    assert len(cleaned) == 26
    assert [row.timestamp for row in cleaned] == [row["timestamp"] for row in rows]


def test_window_choices_are_explicit_and_window_is_chronological():
    from energy.validation import parse_telemetry, forecast_windows, select_forecast_window

    result = parse_telemetry(list(reversed(telemetry(25))))
    assert forecast_windows(result) == ["2015-01-01 00:00:00", "2015-01-01 01:00:00"]
    window = select_forecast_window(result, "2015-01-01 01:00:00")
    assert window[0].timestamp == "2015-01-01 01:00:00"
    assert window[-1].timestamp == "2015-01-02 00:00:00"


@pytest.mark.parametrize("mutation", ["gap", "duplicate", "minute"])
def test_invalid_dashboard_window_is_rejected(mutation):
    from energy.validation import parse_telemetry, select_forecast_window, TelemetryError

    rows = telemetry()
    if mutation == "gap":
        rows.pop(5)
    elif mutation == "duplicate":
        rows.append(rows[4].copy())
    else:
        rows[4]["timestamp"] = "2015-01-01 04:30:00"
    with pytest.raises(TelemetryError):
        select_forecast_window(parse_telemetry(rows), "2015-01-01 00:00:00")


@pytest.mark.parametrize("data", [
    b"", b"timestamp,ambient_temp_c\n2015-01-01 00:00:00,26\n",
    b"timestamp,ambient_temp_c,humidity_pct,humidity_pct,solar_irradiance_wm2\n",
    b"\xff\xfe", b"timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2\n",
])
def test_bad_csv_structure_is_an_explicit_error(data):
    from energy.validation import parse_csv, TelemetryError

    with pytest.raises(TelemetryError):
        parse_csv(data)


def test_upload_limits_are_enforced_before_forecasting():
    from energy.validation import parse_csv, TelemetryError

    with pytest.raises(TelemetryError, match="size"):
        parse_csv(b"x" * (2 * 1024 * 1024 + 1))
    data = b"timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2\n2015-01-01 00:00:00,26,60,0\n2015-01-01 01:00:00,26,60,0\n"
    with pytest.raises(TelemetryError, match="row limit"):
        parse_csv(data, max_rows=1)
