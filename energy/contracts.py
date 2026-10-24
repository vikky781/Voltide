from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class BatterySettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, frozen=True)

    capacity_kwh: float = Field(default=2000.0, gt=0)
    initial_soc_pct: float = Field(default=80.0, ge=0, le=100)
    reserve_soc_pct: float = Field(default=20.0, ge=0, le=100)
    max_discharge_kw: float = Field(default=250.0, gt=0)
    discharge_efficiency_pct: float = Field(default=95.0, gt=0, le=100)

    @model_validator(mode="after")
    def check_reserve(self):
        if self.reserve_soc_pct > self.initial_soc_pct:
            raise ValueError("Initial state of charge must be at or above reserve.")
        return self


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
