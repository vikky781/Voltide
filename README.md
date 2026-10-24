# Voltide

Smart energy demand forecasting and microgrid dispatch for HackSphere 3.0.

## Current status

Implementation is in progress on `codex/implementation`. The [hosted application](https://voltide-50047138433.development.catalystappsail.in) serves CSV/manual weather input, real QuickML forecasts, dispatch decisions, a labeled battery simulation, private session history, and CSV exports. Cloud saves survive redeployment; another session cannot retrieve a run. There are 133 passing backend tests and 10 frontend tests. The unchanged starter evaluator passed against the real endpoint for all 1,000 sample rows in 17.0 seconds.

The first Ridge candidate's chronological selection RMSE is 32.0430 kW, with substantial high-demand underprediction. Model comparison, effective cloud fitting-row evidence, final model freeze, CSV browser-upload acceptance, and mobile acceptance remain open. See the model card and progress log for verified evidence and limits.

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

Secrets belong in a private `.env` or hosted environment settings, never in Git. Copy `.env.example` and supply the India-region endpoint and OAuth values. Local `.env` loads without overriding existing environment variables. One-time authorization uses the approved `QuickML.deployment.READ` scope; `python -m tools.authorize_quickml` prompts for the short-lived code without echoing it. Never paste secrets into chat.

With credentials configured:

    python test_eval.py
    python predict.py --input sample_test_input.csv --output artifacts/predictions.csv
    python -m web.app

The CLI writes `timestamp,target_demand_kw` atomically and fails without replacing output if any remote batch fails. Batches contain at most 24 rows and share a 120-second operation deadline. No formula fallback remains. The local API is at `http://127.0.0.1:5000`. Build the dashboard with `npm ci` and `npm run build` inside frontend/; Flask then serves it from the same origin. `npm test` runs the frontend boundary tests.

## Design and progress

- [Technical design](docs/superpowers/specs/2026-10-24-microgrid-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-24-microgrid-implementation-plan.md)
- [Verified progress and decisions](docs/progress.md)

Forecast timestamps are dataset-local wall-clock values. Battery values are explicitly simulated; no physical power switches are controlled.
