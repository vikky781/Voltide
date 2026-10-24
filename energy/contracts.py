from dataclasses import dataclass, field, fields
from datetime import datetime
import math
from numbers import Real


WEATHER_FIELDS = ("ambient_temp_c", "humidity_pct", "solar_irradiance_wm2")
INPUT_FIELDS = ("timestamp", *WEATHER_FIELDS)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class CellIssue:
    row: int
    column: str
    code: str
    message: str


@dataclass(frozen=True)
class Correction:
    row: int
    column: str
    previous_row: int
    value: float
    reason: str = "PREVIOUS_HOUR"


@dataclass(frozen=True)
class TelemetryRow:
    timestamp: str
    time: datetime
    position: int
    ambient_temp_c: float
    humidity_pct: float
    solar_irradiance_wm2: float

    def to_record(self) -> dict:
        return {name: getattr(self, name) for name in INPUT_FIELDS}


class TelemetryError(ValueError):
    def __init__(self, message: str, issues: list[CellIssue] | None = None):
        super().__init__(message)
        self.issues = issues or []


@dataclass
class ValidationResult:
    rows: list[TelemetryRow] = field(default_factory=list)
    errors: list[CellIssue] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_count: int = 0

    def require_valid(self) -> list[TelemetryRow]:
        if self.errors:
            raise TelemetryError("Telemetry contains invalid cells.", self.errors)
        return self.rows


class BatterySettingsError(ValueError):
    def __init__(self, issues: list[CellIssue]):
        super().__init__('Battery settings are invalid.')
        self.issues = issues


@dataclass(frozen=True, init=False)
class BatterySettings:
    capacity_kwh: float = 2000.0
    initial_soc_pct: float = 80.0
    reserve_soc_pct: float = 20.0
    max_discharge_kw: float = 250.0
    discharge_efficiency_pct: float = 95.0

    def __init__(self, **values):
        defaults = {item.name: item.default for item in fields(self)}
        issues = [CellIssue(0, key, 'INVALID_SETTING', 'Unknown battery setting.')
                  for key in values if key not in defaults]
        positive = {'capacity_kwh', 'max_discharge_kw', 'discharge_efficiency_pct'}
        percentages = {'initial_soc_pct', 'reserve_soc_pct', 'discharge_efficiency_pct'}
        for name, default in defaults.items():
            value = values.get(name, default)
            message = None
            try:
                finite = not isinstance(value, bool) and isinstance(value, Real) and math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                message = 'Enter a finite number.'
            elif value < 0 or (name in positive and value == 0):
                message = 'Value must be greater than zero.' if name in positive else 'Value must be at least zero.'
            elif name in percentages and value > 100:
                message = 'Percentage must not exceed 100.'
            if message:
                issues.append(CellIssue(0, name, 'INVALID_SETTING', message))
            else:
                object.__setattr__(self, name, float(value))
        if not issues and self.reserve_soc_pct > self.initial_soc_pct:
            issues.append(CellIssue(0, 'reserve_soc_pct', 'INVALID_SETTING',
                                    'Initial state of charge must be at or above reserve.'))
        if issues:
            raise BatterySettingsError(issues)


@dataclass(frozen=True)
class DispatchDecision:
    timestamp: str
    target_demand_kw: float
    requested_mode: str
    reasons: list[str]
    critical_overload: bool


@dataclass(frozen=True)
class BatteryHour(DispatchDecision):
    battery_soc_start_pct: float
    battery_soc_end_pct: float
    battery_delivered_kw: float
    unserved_kw: float
    storage_shortfall: bool
    alerts: list[str]


class PredictionError(ValueError):
    """The upstream model did not produce a valid aligned prediction batch."""
