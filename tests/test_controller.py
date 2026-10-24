import pytest


@pytest.mark.parametrize("hour,demand,mode,critical,reasons", [
    (17, 159.99, "MAIN_GRID", False, ["NORMAL_LOAD"]),
    (17, 160, "MAIN_GRID", False, ["NORMAL_LOAD"]),
    (17, 160.00001, "RENEWABLE_STORAGE", False, ["DEMAND_THRESHOLD"]),
    (18, 80, "RENEWABLE_STORAGE", False, ["PEAK_WINDOW"]),
    (22, 160, "RENEWABLE_STORAGE", False, ["PEAK_WINDOW"]),
    (23, 160, "MAIN_GRID", False, ["NORMAL_LOAD"]),
    (0, 199.99, "RENEWABLE_STORAGE", False, ["DEMAND_THRESHOLD"]),
    (0, 200, "RENEWABLE_STORAGE", True, ["DEMAND_THRESHOLD"]),
    (18, 200.01, "RENEWABLE_STORAGE", True, ["DEMAND_THRESHOLD", "PEAK_WINDOW"]),
])
def test_exact_dispatch_boundaries(hour, demand, mode, critical, reasons):
    from energy.controller import evaluate_dispatch

    result = evaluate_dispatch(f"2015-01-01 {hour:02d}:00:00", demand)
    assert result.requested_mode == mode
    assert result.critical_overload is critical
    assert result.reasons == reasons
    assert result.target_demand_kw == demand


@pytest.mark.parametrize("demand", [-1, float("nan"), float("inf"), True])
def test_invalid_demand_cannot_generate_a_control_signal(demand):
    from energy.controller import evaluate_dispatch

    with pytest.raises(ValueError):
        evaluate_dispatch("2015-01-01 18:00:00", demand)


def test_dataset_clock_is_used_without_utc_or_browser_conversion():
    from energy.controller import evaluate_dispatch

    assert evaluate_dispatch("2015-01-01 22:59:59", 100).requested_mode == "RENEWABLE_STORAGE"
    assert evaluate_dispatch("2015-01-01 23:00:00", 100).requested_mode == "MAIN_GRID"
    assert evaluate_dispatch("2015-01-02 00:00:00", 100).requested_mode == "MAIN_GRID"
