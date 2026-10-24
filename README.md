# Voltide

Smart energy demand forecasting and microgrid dispatch for HackSphere 3.0.

## Current status

Implementation is in progress on `codex/implementation`. CSV validation, shared deterministic features, cloud data preparation, exact dispatch rules, battery simulation, and the initial Flask API are implemented. The suite has 73 passing tests. Voltide's Catalyst project, QuickML workspace, and 2400-row development dataset exist. A real model endpoint, hosted app, and dashboard are not available yet. The original `predict.py` still contains its starter fallback; do not treat it as a completed model integration. The new web API returns an explicit 503 until a real model client is wired.

## Local development

Target deployment: Catalyst managed Python 3.12. Development checks currently run on Python 3.14; cross-runtime compatibility must be verified before release.

Create a project virtual environment, install `requirements-dev.txt`, then run:

    python -m pytest
    python -m tools.prepare_quickml_data --input train_telemetry.csv --output artifacts/quickml

**Never train a model locally, including on CPU.** These commands only test application logic and calculate fixed features/CSV partitions. All model training, learned preprocessing, and tuning must happen in Zoho Catalyst QuickML.

## Cloud data preparation

The preparation command preserves the original dataset and writes ignored files under `artifacts/quickml/`:

| File | Use |
| --- | --- |
| `development.csv` | First 2,400 labeled rows; first cloud model training input. |
| `selection.csv` | Next 800 labeled rows; compare remote predictions, not candidate training input. |
| `locked_test.csv` | Final 800 labeled rows; keep untouched until model selection is frozen. |
| `refit.csv` | First 3,200 rows; remote refit after selection. |
| `final.csv` | All 4,000 rows; final cloud fitting after locked evaluation. |
| `*_inputs.csv` | Corresponding original timestamp/weather inputs without demand labels. |
| `manifest.json` | Source hash, feature version, columns, row ranges, and timestamps. |

Upload **only development.csv** for the first cloud model, with `target_demand_kw` as the target. Do not upload `selection.csv` or `locked_test.csv` as training data during model selection. See [model card](docs/model-card.md) for feature details and [operations](docs/operations.md) for remaining account setup.

Secrets belong in a private `.env` or hosted environment settings, never in Git. `.env.example` lists the intended names; actual endpoint authentication will be verified before the inference client is completed.

## Design and progress

- [Technical design](docs/superpowers/specs/2026-10-24-microgrid-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-24-microgrid-implementation-plan.md)
- [Verified progress and decisions](docs/progress.md)

Forecast timestamps are dataset-local wall-clock values. Battery values will be explicitly simulated; no physical power switches are controlled.
