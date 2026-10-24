# Voltide operations

## Verified on 24 October 2026

- Repository: https://github.com/vikky781/Voltide; implementation branch: codex/implementation.
- Initial local baseline used the starter formula. It has now been replaced: the unchanged self-tester passes with 1000 real QuickML predictions in 16.998 seconds. This verifies integration, not accuracy.
- Catalyst connector authentication works and lists the existing Project-Rainfall development project in the India region. It remains untouched.
- The QuickML project-list operation returns HTTP 204 (no projects). This does not prove QuickML entitlement or a successful provisioning path.
- Catalyst CLI 1.29.0 is installed. Its config directory requires execution outside the restricted sandbox. CLI authentication now succeeds in the dedicated project's account; project:list verifies Voltide 92462000000018001. The user explicitly approved the official CLI's broad deployment scopes. An earlier automatic approval rejection for those scopes was resolved by that explicit approval. The prediction app keeps its separate narrow OAuth credentials.
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

Use the project environment: .venv/Scripts/python.exe -m pytest and .venv/Scripts/python.exe -m web.app on Windows. The configured application provides /api/health, /api/validate, and /api/forecast using real QuickML. Invalid/missing model configuration fails startup. Isolated create_app() without a service returns forecast 503. Built frontend assets are served from frontend/dist.

## Dashboard and deployment preparation

Build the dashboard with `npm ci`, `npm test`, and `npm run build` in frontend/. The initial React slice supports original CSV validation, valid 24-hour selection, editable battery assumptions, demand chart, requested-source timeline, and hourly decisions. Battery efficiency is expressed as percent consistently with the API. Full Task 8 acceptance remains pending.

Run `python -m tools.build_appsail --install-dependencies --private-config` from the project virtual environment. This removes only the exact generated artifacts/deploy directory after checking its resolved path, copies allowlisted application files and built assets, and installs Linux x86-64 Python 3.12 wheels. Training datasets, tests, .venv, local .env, and source development files are excluded. Do not run training tools in the hosted app.

The tracked app-config.json is a secret-free template from the CLI, configured for Python 3.12, 512 MiB, and Gunicorn (one process/four threads, 150-second worker timeout). The build helper writes actual secret settings only to ignored artifacts/appsail/app-config.json; catalyst.json selects that source with artifacts/deploy as the build path. SESSION_SECRET is generated privately if missing. Never stage the generated private configuration. The CLI can package the bundle directly; public availability is not established by preparing it.

The installed Node 24.19.0 produces a Catalyst CLI security advisory recommending a patched runtime. It has not been disabled or bypassed; resolving the runtime advisory remains an operations follow-up.

## First hosted slice

- URL: https://voltide-50047138433.development.catalystappsail.in (Development environment, reachable without login cookies).
- AppSail ID: 92462000000019001; Python 3.12; 512 MiB; deployed from CLI on 24 October 2026.
- Health: HTTP 200, status=ok, model_configured=true. This is configuration readiness, not a fresh model prediction on each health request.
- Real hosted /api/forecast: 24 aligned predictions from generated, non-private constant weather, model Voltide_Linear_v1:V1, HTTP 200, 0.735 seconds after warm startup. Battery provenance SIMULATED, saved=false. Evidence remains private in artifacts/hosted-forecast-synthetic.json. This does not establish model accuracy or the browser CSV upload flow.
- Browser dashboard renders and calls health successfully. Manual CSV acceptance remains pending because browser upload permission was declined; no alternate browser/upload mechanism was used.

The first metadata upload failed because supplied environment names collided with platform-reserved names. Hosted private configuration now prefixes every application variable with VOLTIDE_; runtime readers prefer these over platform-managed names. Local .env names remain compatible. Do not override Catalyst's own reserved environment values.

The first deployed process returned 503 because AppSail executes startup commands directly, without shell expansion. The startup command now explicitly uses `sh -c` and `exec` to expand the platform's port and forward process signals. See the official [startup command requirements](https://docs.catalyst.zoho.com/en/serverless/help/appsail/appsail-configurations/). The subsequent public HTTP 200 verifies the correction. A CLI deployment success or console Live label alone is not application health evidence.

Redeploy after rebuilding with `catalyst deploy --only appsail:Voltide --project 92462000000018001 --org 60093105197 --dc in --non-interactive`. Inspect public health and a real prediction after every deployment. Keep generated deployment settings out of Git.

SDK compatibility: zcatalyst-sdk 1.4.0 constrains typing-extensions to ~=4.12.1. Pydantic 2.13.5 requires >=4.14.1, so these cannot be resolved together. The application now validates the five battery fields with standard Python dataclasses, preserving strict finite numbers, bounds, frozen settings, and structured API errors. Pydantic is no longer a dependency; no vendor constraint was overridden. Project `pip check` passes. Rebuild the Linux bundle before the next deployment so it uses this compatible dependency set.

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
