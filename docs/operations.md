# Voltide operations

## Verified on 24 October 2026

- Repository: https://github.com/vikky781/Voltide; implementation branch: codex/implementation.
- Local baseline: unchanged starter self-test succeeds on 1,000 rows using its original formula fallback. This is not evidence of QuickML integration or model accuracy.
- Catalyst connector authentication works and lists the existing Project-Rainfall development project in the India region. It remains untouched.
- The QuickML project-list operation returns HTTP 204 (no projects). This does not prove QuickML entitlement or a successful provisioning path.
- Catalyst CLI 1.29.0 is installed. Its config directory requires execution outside the restricted sandbox. CLI authentication is separate from connector authentication and has not been verified.
- Local tools: Python 3.14.7, additional Python 3.13, Node 24.19.0, npm 11.17.0. Hosted target remains the documented Python 3.12 managed runtime; run compatibility checks before deployment.
- The connected tools lack general project creation, local CSV dataset import, and AppSail source deployment. Use the official Catalyst console and CLI for those steps.
- The console browser opens at Zoho Accounts sign-in. The user must complete sign-in; passwords and refresh tokens must not be pasted into chat.

## Dedicated project provisioned

The user completed console sign-in. The signed-in browser is in organization 60093105197, which differs from the connector's organization. Use the browser-provisioned project details below for Voltide; do not mix them with the connector's unrelated account/project context.

- Voltide project ID: 92462000000018001.
- Organization: 60093105197; India data center; Development environment.
- Console: https://console.catalyst.zoho.in/baas/60093105197/project/92462000000018001/Development#/quickml/home
- QuickML workspace opens successfully with no datasets, pipelines, models, or endpoints yet.
- No payment method was added, no paid plan was selected, and no model has been trained. Available training quota and production access still require verification.

## Development dataset imported

- Dataset: Voltide_Development_v1; ID 12429000000003002; version V1.
- QuickML confirms 2400 records, 11 columns (10 features plus target), 100% valid values, and no missing values.
- Only artifacts/quickml/development.csv was uploaded. Selection and locked-test labels remain local.
- The dataset preview samples/shuffles rows for display; feature/label alignment is carried in each uploaded row and external chronological partition membership is preserved.
- Prediction pipeline creation uses target_demand_kw and leaves automatic retraining disabled. Algorithm configuration and execution are still pending.

## Local API development

Use the project environment: .venv/Scripts/python.exe -m pytest and .venv/Scripts/python.exe -m web.app on Windows. The API provides /api/health, /api/validate, and /api/forecast. No real client is wired yet: forecast returns 503 instead of fabricated predictions. A built frontend is not present yet.

The actual local Python 3.13 registration is stale; .venv uses the working Python 3.14 interpreter. Flask 3.1.3 and the pinned requirements were installed into .venv, without training packages. The hosted Python 3.12 target still requires a compatibility check.

Project creation evidence is stored locally under ignored artifacts/voltide-project.png; account screenshots are not published to Git.

## Required external setup

1. Sign in at https://console.catalyst.zoho.in/ and verify the Catalyst account if requested.
2. Provision a dedicated Voltide project, preserving unrelated projects. Confirm QuickML and AppSail availability and the account's budget/quota before cloud jobs.
3. Upload the prepared development feature partition to QuickML. Model training, learned preprocessing, and tuning occur only there; never locally.
4. Publish a regression endpoint and capture its sample request/response, authentication requirements, model version, and actual internal split behavior.
5. Store credentials in private local/hosted environment settings. The browser and Git must never receive endpoint keys, OAuth refresh tokens, or client secrets.
6. Verify hosted SDK permissions, production/public URL access, token renewal, and actual latency before declaring the release ready.

## Information requested from organizers

The exact 28 October cutoff, evaluator invocation mode, timeout, dependency installation procedure, and permitted secret credential handoff are not yet known. These remain release risks; the application and deterministic core can be implemented independently.

## Scope and safety

No local model fitting is permitted, including CPU fitting or learned imputers/scalers. Deterministic parsing/features, remote calls, scoring supplied predictions, application builds, and tests are permitted. Data timestamps are dataset-local wall-clock values; do not infer a timezone from the India account region. Battery values are simulated, with assumptions attached to each run.

Development fixtures can replace remote network boundaries in tests. Production and evaluator paths must never return simulated demand after a QuickML failure. The original CSVs, problem statement, and test_eval.py remain unchanged.
