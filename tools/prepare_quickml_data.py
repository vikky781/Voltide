"""Prepare chronological cloud-upload CSVs without fitting a model or transform."""

import argparse
import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path

from energy.contracts import INPUT_FIELDS
from energy.features import build_features, FEATURE_NAMES, FEATURE_VERSION
from energy.validation import parse_csv, TelemetryError

SPLITS = {"development": (0, 2400), "selection": (2400, 3200),
          "locked_test": (3200, 4000), "refit": (0, 3200), "final": (0, 4000)}


def _write_csv(path: Path, columns, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def prepare_dataset(source: Path, output: Path) -> dict:
    data = source.read_bytes()
    rows = parse_csv(data, max_bytes=None, max_rows=None).require_valid()
    if len(rows) != 4000:
        raise TelemetryError("Expected the supplied 4,000 labeled training rows.")
    if any(previous.time >= current.time for previous, current in zip(rows, rows[1:])):
        raise TelemetryError("Training rows must have unique increasing timestamps.")
    raw = list(csv.DictReader(StringIO(data.decode("utf-8-sig"))))
    try:
        targets = [float(record["target_demand_kw"]) for record in raw]
    except (KeyError, ValueError, TypeError) as error:
        raise TelemetryError("Training rows require numeric target_demand_kw labels.") from error
    if any(not math.isfinite(value) or value < 0 for value in targets):
        raise TelemetryError("Training targets must be finite and nonnegative.")
    features = build_features(rows)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"source_sha256": hashlib.sha256(data).hexdigest(), "feature_version": FEATURE_VERSION,
                "feature_names": list(FEATURE_NAMES), "splits": {}}
    for name, (first, end) in SPLITS.items():
        _write_csv(output / f"{name}.csv", (*FEATURE_NAMES, "target_demand_kw"),
                   [{**features[i], "target_demand_kw": targets[i]} for i in range(first, end)])
        _write_csv(output / f"{name}_inputs.csv", INPUT_FIELDS,
                   [row.to_record() for row in rows[first:end]])
        manifest["splits"][name] = {"rows": end - first, "source_rows": [first + 1, end],
            "first_timestamp": rows[first].timestamp, "last_timestamp": rows[end - 1].timestamp}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("train_telemetry.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/quickml"))
    args = parser.parse_args()
    print(json.dumps(prepare_dataset(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
