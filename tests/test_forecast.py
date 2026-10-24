from datetime import datetime, timedelta

import pytest


def forecast_source():
    return [{"timestamp": (datetime(2015, 1, 1) + timedelta(hours=hour)).strftime("%Y-%m-%d %H:%M:%S"),
             "ambient_temp_c": 25, "humidity_pct": 60, "solar_irradiance_wm2": 0}
            for hour in range(24)]


def test_service_composes_one_aligned_run_without_claiming_live_battery_or_storage():
    from energy.forecast import ForecastService

    class RemoteBoundaryFixture:
        model_version = "test-model-7"

        def predict_rows(self, features):
            assert len(features) == 24
            assert all("timestamp" not in row and "target_demand_kw" not in row for row in features)
            return [100.0] * 23 + [200.0]

    result = ForecastService(RemoteBoundaryFixture()).run(
        forecast_source(), "2015-01-01 00:00:00")
    assert result["model_version"] == "test-model-7"
    assert result["feature_version"] == "v1"
    assert result["battery_provenance"] == "SIMULATED"
    assert result["saved"] is False
    assert len(result["hourly"]) == 24
    assert result["hourly"][0]["timestamp"] == "2015-01-01 00:00:00"
    assert result["summary"]["total_energy_kwh"] == 2500
    assert result["summary"]["peak_demand_kw"] == 200
    assert result["summary"]["storage_hours"] == 6
    assert result["summary"]["critical_hours"] == 1
    assert result["summary"]["final_soc_pct"] == pytest.approx(80 - 700 / .95 / 2000 * 100)


def test_bad_inputs_never_reach_remote_prediction():
    from energy.forecast import ForecastService

    class MustNotCall:
        model_version = "fixture"

        def predict_rows(self, _):
            pytest.fail("Invalid inputs reached paid inference")

    with pytest.raises(ValueError):
        ForecastService(MustNotCall()).run(forecast_source()[:23], "2015-01-01 00:00:00")
    with pytest.raises(ValueError):
        ForecastService(MustNotCall()).run(forecast_source(), "2015-01-01 00:00:00",
                                         {"reserve_soc_pct": 90})


@pytest.mark.parametrize("predictions", [[100] * 23, [100] * 23 + [float("nan")]])
def test_service_rejects_misaligned_or_invalid_predictions(predictions):
    from energy.forecast import ForecastService

    class InvalidRemoteFixture:
        model_version = "fixture"

        def predict_rows(self, _):
            return predictions

    with pytest.raises(ValueError):
        ForecastService(InvalidRemoteFixture()).run(forecast_source(), "2015-01-01 00:00:00")
