# Voltide

Smart energy demand forecasting and microgrid dispatch for HackSphere 3.0.

## Current status

Implementation is in progress on `codex/implementation`. The [hosted application](https://voltide-50047138433.development.catalystappsail.in) serves CSV/manual weather input, real QuickML forecasts, dispatch decisions, a labeled battery simulation, private session history, and CSV exports. Cloud saves survive redeployment; another session cannot retrieve a run. There are 133 passing backend tests and 10 frontend tests. The unchanged starter evaluator passed against the real endpoint for all 1,000 sample rows in 17.0 seconds.

Three cloud-trained candidates were compared on the same 800-row chronological selection set. Gradient boosting won with RMSE 14.1411 kW; Ridge scored 32.0430 kW and random forest 30.1347 kW. A cloud gradient refit on the first 3,200 uploaded rows scored RMSE 13.2666 kW and MAE 10.1386 kW on the single locked 800-row test. The final cloud GB model on the 4,000-row uploaded dataset is Ready and deployed through its published endpoint. Real 1/24/1,000-row inference and the unchanged starter evaluator passed. The public app returned a real 24-hour final-model forecast with saved history and cross-session isolation. Effective cloud fitting-row evidence, CSV browser-upload acceptance, and mobile acceptance remain open. See the model card and progress log for verified evidence and limits.

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

The development, refit, and final datasets are in QuickML, and the single locked evaluation is recorded. The final cloud model uses the all-4,000-row uploaded dataset with `target_demand_kw` as the target. The selection and locked partitions were kept out of candidate/refit fitting before that locked result was frozen. See [model card](docs/model-card.md) for feature details and [operations](docs/operations.md) for the current handoff.

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
