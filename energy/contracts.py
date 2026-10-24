from dataclasses import dataclass, field
from datetime import datetime


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
