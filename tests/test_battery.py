import pytest


def test_energy_balance_and_reserve_shortfall_preserve_requested_mode():
    from energy.battery import simulate_battery
    from energy.contracts import BatterySettings
    from energy.controller import evaluate_dispatch

    settings = BatterySettings(capacity_kwh=1000, initial_soc_pct=80, reserve_soc_pct=20,
                               max_discharge_kw=250, discharge_efficiency_pct=100)
    dispatch = [evaluate_dispatch(f"2015-01-01 {hour:02d}:00:00", 250) for hour in [18, 19, 20, 21]]
    result = simulate_battery(dispatch, settings)
    assert [row.battery_delivered_kw for row in result] == pytest.approx([250, 250, 100, 0])
    assert [row.unserved_kw for row in result] == pytest.approx([0, 0, 150, 250])
    assert [row.battery_soc_end_pct for row in result] == pytest.approx([55, 30, 20, 20])
    assert all(row.requested_mode == "RENEWABLE_STORAGE" for row in result)
    assert result[-1].storage_shortfall is True
    assert result[-1].critical_overload is True


def test_grid_hours_do_not_discharge_or_charge_and_efficiency_is_applied():
    from energy.battery import simulate_battery
    from energy.contracts import BatterySettings
    from energy.controller import evaluate_dispatch

    settings = BatterySettings(capacity_kwh=1000, initial_soc_pct=80, reserve_soc_pct=20,
                               max_discharge_kw=250, discharge_efficiency_pct=50)
    dispatch = [evaluate_dispatch("2015-01-01 17:00:00", 100),
                evaluate_dispatch("2015-01-01 18:00:00", 200)]
    result = simulate_battery(dispatch, settings)
    assert result[0].battery_soc_start_pct == result[0].battery_soc_end_pct == 80
    assert result[0].battery_delivered_kw == result[0].unserved_kw == 0
    assert result[1].battery_soc_end_pct == pytest.approx(40)
    assert result[1].battery_delivered_kw == 200


def test_discharge_power_limit_and_starting_at_reserve():
    from energy.battery import simulate_battery
    from energy.contracts import BatterySettings
    from energy.controller import evaluate_dispatch

    demand = [evaluate_dispatch("2015-01-01 18:00:00", 300)]
    limited = simulate_battery(demand, BatterySettings())[0]
    assert limited.battery_delivered_kw == 250
    assert limited.unserved_kw == 50
    empty = simulate_battery(demand, BatterySettings(initial_soc_pct=20))[0]
    assert empty.battery_soc_end_pct == 20
    assert empty.battery_delivered_kw == 0
    assert empty.unserved_kw == 300


@pytest.mark.parametrize("settings", [
    {"capacity_kwh": 0}, {"capacity_kwh": float("inf")}, {"max_discharge_kw": -1},
    {"initial_soc_pct": 101}, {"initial_soc_pct": 10, "reserve_soc_pct": 20},
    {"reserve_soc_pct": -1}, {"discharge_efficiency_pct": 0},
    {"discharge_efficiency_pct": 101}, {"capacity_kwh": True},
])
def test_invalid_battery_assumptions_are_rejected(settings):
    from energy.contracts import BatterySettings

    with pytest.raises(ValueError):
        BatterySettings(**settings)


def test_simulation_requires_consecutive_chronological_hours():
    from energy.battery import simulate_battery
    from energy.contracts import BatterySettings
    from energy.controller import evaluate_dispatch

    rows = [evaluate_dispatch("2015-01-01 19:00:00", 180),
            evaluate_dispatch("2015-01-01 18:00:00", 180)]
    with pytest.raises(ValueError):
        simulate_battery(rows, BatterySettings())
