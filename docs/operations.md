# Voltide operations

## Verified on 24 October 2026

- Repository: https://github.com/vikky781/Voltide; implementation branch: codex/implementation.
- Initial local baseline used the starter formula. It has now been replaced: the unchanged self-tester passes with 1000 real QuickML predictions in 16.998 seconds. This verifies integration, not accuracy.
- Catalyst connector authentication works and lists the existing Project-Rainfall development project in the India region. It remains untouched.
- The QuickML project-list operation returns HTTP 204 (no projects). This does not prove QuickML entitlement or a successful provisioning path.
- Catalyst CLI 1.29.0 is installed. Its config directory requires execution outside the restricted sandbox. CLI authentication is separate from connector authentication and has not been verified.
- Local tools: Python 3.14.7, stale Python 3.13 registration, Node 24.19.0, npm 11.17.0. Hosted target remains the documented Python 3.12 managed runtime; run compatibility checks before deployment.
- The connected tools lack general project creation, local CSV dataset import, and AppSail source deployment. Use the official Catalyst console and CLI for those steps.
- Console sign-in and OneAuth verification completed by the user. Passwords and refresh tokens must not be pasted into chat.

## Dedicated project provisioned

The user completed console sign-in. The signed-in browser is in organization 60093105197, which differs from the connector's organization. Use the browser-provisioned project details below for Voltide; do not mix them with the connector's unrelated account/project context.

- Voltide project ID: 92462000000018001.
- Organization: 60093105197; India data center; Development environment.
- Console: https://console.catalyst.zoho.in/baas/60093105197/project/92462000000018001/Development#/quickml/home
- QuickML workspace contains the development dataset, Ridge pipeline/model V1, and baseline endpoint described in model-card.md.
- No payment method was added and no paid plan was selected. Cloud training and prediction succeed; remaining quota and production/public application access still require verification.

## Development dataset imported

- Dataset: Voltide_Development_v1; ID 12429000000003002; version V1.
- QuickML confirms 2400 records, 11 columns (10 features plus target), 100% valid values, and no missing values.
- Only artifacts/quickml/development.csv was uploaded. Selection and locked-test labels remain local.
- The dataset preview samples/shuffles rows for display; feature/label alignment is carried in each uploaded row and external chronological partition membership is preserved.
- Prediction pipeline uses target_demand_kw and leaves automatic retraining disabled. Ridge configuration and cloud execution succeeded; see model-card.md.

## Verified endpoint and authorization

Endpoint URL: https://api.catalyst.zoho.in/quickml/v1/project/92462000000018001/endpoints/predict. Required headers: X-QUICKML-ENDPOINT-KEY, Authorization (`Zoho-oauthtoken`), CATALYST-ORG, and Environment (`Development`). Scope: QuickML.deployment.READ. Both single-object and 24-record array data payloads return an aligned result array.

The user approved creation of a Self Client and prediction-only access in the signed-in browser account. Client credentials and refresh token are stored only in ignored .env. A short-lived grant is exchanged using POST form data to https://accounts.zoho.in/oauth/v2/token, without URL query credentials or token output. Inference automatically refreshes expired access tokens; a 401 triggers one refresh/replay. No browser cookie or unrelated connector credential is used.

QuickMLClient uses sequential batches of 24, a 120-second operation deadline, up to two transient retries, and refuses long rate-limit waits. Malformed, missing, negative, nonfinite, nested, or misaligned outputs fail the entire operation. There is no fallback prediction. Captured fixtures omit all headers and tokens.

## Local API development

Use the project environment: .venv/Scripts/python.exe -m pytest and .venv/Scripts/python.exe -m web.app on Windows. The configured application provides /api/health, /api/validate, and /api/forecast using real QuickML. Invalid/missing model configuration fails startup. Isolated create_app() without a service returns forecast 503. A built frontend is not present yet.

The actual local Python 3.13 registration is stale; .venv uses the working Python 3.14 interpreter. Flask 3.1.3 and the pinned requirements were installed into .venv, without training packages. The hosted Python 3.12 target still requires a compatibility check.

Project creation evidence is stored locally under ignored artifacts/voltide-project.png; account screenshots are not published to Git.

## Required external setup

1. Verify QuickML internal split/fitted-row usage, remaining quota, and production/public application access.
2. Verify CLI identity for the dedicated Voltide project; connector credentials belong to another organization.
3. Deploy the first real inference path and supply secrets through private hosted environment settings.
4. Verify hosted SDK permissions, durable session-scoped persistence, and public workflow before declaring the release ready.
5. Complete cloud candidate selection and held-out scoring; all fitting remains exclusively in QuickML.

## Information requested from organizers

The exact 28 October cutoff, evaluator invocation mode, timeout, dependency installation procedure, and permitted secret credential handoff are not yet known. These remain release risks; the application and deterministic core can be implemented independently.

## Scope and safety

No local model fitting is permitted, including CPU fitting or learned imputers/scalers. Deterministic parsing/features, remote calls, scoring supplied predictions, application builds, and tests are permitted. Data timestamps are dataset-local wall-clock values; do not infer a timezone from the India account region. Battery values are simulated, with assumptions attached to each run.

Development fixtures can replace remote network boundaries in tests. Production and evaluator paths must never return simulated demand after a QuickML failure. The original CSVs, problem statement, and test_eval.py remain unchanged.
