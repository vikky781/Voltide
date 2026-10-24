"""Fixed HackSphere dispatch rules, independent of battery availability."""

import math
from numbers import Real

from energy.contracts import DispatchDecision
from energy.validation import parse_timestamp


def evaluate_dispatch(timestamp: str, demand_kw: float) -> DispatchDecision:
    if (isinstance(demand_kw, bool) or not isinstance(demand_kw, Real)
            or not math.isfinite(demand_kw) or demand_kw < 0):
        raise ValueError("Demand must be a finite nonnegative number.")
    hour = parse_timestamp(timestamp).hour
    reasons = []
    if demand_kw > 160:
        reasons.append("DEMAND_THRESHOLD")
    if 18 <= hour <= 22:
        reasons.append("PEAK_WINDOW")
    return DispatchDecision(timestamp, float(demand_kw),
        "RENEWABLE_STORAGE" if reasons else "MAIN_GRID",
        reasons or ["NORMAL_LOAD"], demand_kw >= 200)
