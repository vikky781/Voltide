from pathlib import Path
import csv
import json

import pytest


def test_features_are_fixed_calculations_and_exclude_target_and_raw_timestamp():
    from energy.features import build_features
    from energy.validation import parse_telemetry

    rows = parse_telemetry([{"timestamp": "2015-01-03 06:00:00", "ambient_temp_c": 28,
                             "humidity_pct": 60, "solar_irradiance_wm2": 100,
                             "target_demand_kw": 999}]).require_valid()
    record = build_features(rows)[0]
    assert record == pytest.approx({
        "ambient_temp_c": 28, "humidity_pct": 60, "solar_irradiance_wm2": 100,
        "hour": 6, "hour_sin": 1, "hour_cos": 0, "weekday": 5,
        "month": 1, "is_weekend": 1, "cooling_degree_c": 4,
    }, abs=1e-12)


def test_feature_version_mismatch_is_rejected():
    from energy.features import build_features

    with pytest.raises(ValueError, match="version"):
        build_features([], version="unknown")


def test_preparation_preserves_partitions_labels_and_shared_inference_features(tmp_path):
    from tools.prepare_quickml_data import prepare_dataset
    from energy.features import build_features
    from energy.validation import parse_csv

    source = Path(__file__).resolve().parents[1] / "train_telemetry.csv"
    original = source.read_bytes()
    manifest = prepare_dataset(source, tmp_path)
    assert source.read_bytes() == original
    assert manifest["source_sha256"] == "a6bd0c612936c79caa67c07f278731c51be9b2eb83a5951e03fb14b82ee3a122"
    assert {name: part["rows"] for name, part in manifest["splits"].items()} == {
        "development": 2400, "selection": 800, "locked_test": 800, "refit": 3200, "final": 4000,
    }
    assert json.loads((tmp_path / "manifest.json").read_text())["feature_version"] == "v1"
    with (tmp_path / "development.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == 2400
    assert float(records[0]["target_demand_kw"]) == 103.68
    assert "timestamp" not in records[0]
    with (tmp_path / "selection.csv").open(newline="") as handle:
        selection = list(csv.DictReader(handle))
    inference_rows = parse_csv((tmp_path / "selection_inputs.csv").read_bytes()).require_valid()
    inference_features = build_features(inference_rows)
    assert len(inference_features) == len(selection) == 800
    assert {key: float(selection[0][key]) for key in inference_features[0]} == pytest.approx(inference_features[0])
    assert manifest["splits"]["development"]["last_timestamp"] < manifest["splits"]["selection"]["first_timestamp"]
    assert manifest["splits"]["selection"]["last_timestamp"] < manifest["splits"]["locked_test"]["first_timestamp"]
