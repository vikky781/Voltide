"""One-hour storage simulation. Initial energy is assumed; charging is not modeled."""

from dataclasses import asdict
from datetime import timedelta

from energy.contracts import BatteryHour, BatterySettings, DispatchDecision
from energy.validation import parse_timestamp


def simulate_battery(dispatch: list[DispatchDecision], settings: BatterySettings) -> list[BatteryHour]:
    times = [parse_timestamp(row.timestamp) for row in dispatch]
    if not times or any(time.minute or time.second for time in times) or any(
        current - previous != timedelta(hours=1) for previous, current in zip(times, times[1:])
    ):
        raise ValueError("Battery simulation requires consecutive chronological hourly readings.")
    energy = settings.capacity_kwh * settings.initial_soc_pct / 100
    reserve = settings.capacity_kwh * settings.reserve_soc_pct / 100
    efficiency = settings.discharge_efficiency_pct / 100
    result = []
    for row in dispatch:
        start = energy
        delivered = unserved = 0.0
        if row.requested_mode == "RENEWABLE_STORAGE":
            available_kw = max(0.0, energy - reserve) * efficiency
            delivered = min(row.target_demand_kw, settings.max_discharge_kw, available_kw)
            energy = max(reserve, energy - delivered / efficiency)
            unserved = max(0.0, row.target_demand_kw - delivered)
        # Ignore sub-nanowatt subtraction noise when emitting an alert.
        shortfall = unserved > 1e-9
        alerts = (["CRITICAL_OVERLOAD"] if row.critical_overload else [])
        if shortfall:
            alerts.append("STORAGE_SHORTFALL")
        result.append(BatteryHour(**asdict(row),
            battery_soc_start_pct=start / settings.capacity_kwh * 100,
            battery_soc_end_pct=energy / settings.capacity_kwh * 100,
            battery_delivered_kw=delivered, unserved_kw=unserved,
            storage_shortfall=shortfall, alerts=alerts))
    return result
