# Voltide operations

## Verified on 24 October 2026

- Repository: https://github.com/vikky781/Voltide; implementation branch: codex/implementation.
- Initial local baseline used the starter formula. It has now been replaced: the unchanged self-tester passes with 1000 real QuickML predictions in 16.998 seconds. This verifies integration, not accuracy.
- Catalyst connector authentication works and lists the existing Project-Rainfall development project in the India region. It remains untouched.
- The connected Catalyst MCP account belongs to a different organization and cannot administer the browser-provisioned Voltide project. QuickML entitlement is verified by three successful cloud model executions and remote predictions in the dedicated project.
- Catalyst CLI 1.29.0 is installed. CLI authentication now succeeds in the dedicated project's account; project:list verifies Voltide 92462000000018001. The user explicitly approved the official CLI's broad deployment scopes. An earlier automatic approval rejection for those scopes was resolved by that explicit approval. The prediction app keeps its separate narrow OAuth credentials.
- Local tools: Python 3.14.7, stale Python 3.13 registration, Node 24.19.0, npm 11.17.0. Hosted AppSail uses managed Python 3.12; the bundled dependencies and SDK storage have passed deployed integration checks.
- The connected tools lack general project creation, local CSV dataset import, and AppSail source deployment. Use the official Catalyst console and CLI for those steps.
- Console sign-in and OneAuth verification completed by the user. Passwords and refresh tokens must not be pasted into chat.

## Dedicated project provisioned

The user completed console sign-in. The signed-in browser is in organization 60093105197, which differs from the connector's organization. Use the browser-provisioned project details below for Voltide; do not mix them with the connector's unrelated account/project context.

- Voltide project ID: 92462000000018001.
- Organization: 60093105197; India data center; Development environment.
- Console: https://console.catalyst.zoho.in/baas/60093105197/project/92462000000018001/Development#/quickml/home
- QuickML workspace contains the development dataset and Ridge, gradient-boosting, and random-forest pipelines, models, and endpoints described in model-card.md.
- No payment method was added and no paid plan was selected. Cloud training and prediction succeed; remaining quota and the exact production entitlement remain unverified; public Development access is verified.

## Development dataset imported

- Dataset: Voltide_Development_v1; ID 12429000000003002; version V1.
- QuickML confirms 2400 records, 11 columns (10 features plus target), 100% valid values, and no missing values.
- The initial candidate training used only artifacts/quickml/development.csv. The later remote refit used artifacts/quickml/refit.csv after selection was frozen; selection.csv and locked_test.csv were never uploaded as training datasets.
- The dataset preview samples/shuffles rows for display; feature/label alignment is carried in each uploaded row and external chronological partition membership is preserved.
- Prediction pipeline uses target_demand_kw and leaves automatic retraining disabled. Ridge configuration and cloud execution succeeded; see model-card.md.

## Verified endpoint and authorization

Endpoint URL: https://api.catalyst.zoho.in/quickml/v1/project/92462000000018001/endpoints/predict. Required headers: X-QUICKML-ENDPOINT-KEY, Authorization (`Zoho-oauthtoken`), CATALYST-ORG, and Environment (`Development`). Scope: QuickML.deployment.READ. Both single-object and 24-record array data payloads return an aligned result array.

The user approved creation of a Self Client and prediction-only access in the signed-in browser account. Client credentials and refresh token are stored only in ignored .env. A short-lived grant is exchanged using POST form data to https://accounts.zoho.in/oauth/v2/token, without URL query credentials or token output. Inference automatically refreshes expired access tokens; a 401 triggers one refresh/replay. No browser cookie or unrelated connector credential is used.

QuickMLClient uses sequential batches of 24, a 120-second operation deadline, up to two transient retries, and refuses long rate-limit waits. Malformed, missing, negative, nonfinite, nested, or misaligned outputs fail the entire operation. There is no fallback prediction. Captured fixtures omit all headers and tokens.

## Local API development

Use the project environment: .venv/Scripts/python.exe -m pytest and .venv/Scripts/python.exe -m web.app on Windows. The configured application provides /api/health, /api/validate, and /api/forecast using real QuickML. Invalid/missing model configuration fails startup. Isolated create_app() without a service returns forecast 503. Built frontend assets are served from frontend/dist.

## Dashboard and deployment preparation

Build the dashboard with `npm ci`, `npm test`, and `npm run build` in frontend/. The React dashboard supports CSV and manual weather entry, exact 24-hour validation, editable battery assumptions, a lazily loaded demand chart, hourly source/SOC inspection, warnings, private newest-20 history, and predictions/dispatch exports even when a run cannot be saved. Battery efficiency is expressed as percent consistently with the API. Browser CSV upload and 390-pixel responsive acceptance remain pending.

Run `python -m tools.build_appsail --install-dependencies --private-config` from the project virtual environment. This removes only the exact generated artifacts/deploy directory after checking its resolved path, copies allowlisted application files and built assets, and installs Linux x86-64 Python 3.12 wheels. Training datasets, tests, .venv, local .env, and source development files are excluded. Do not run training tools in the hosted app.

The tracked app-config.json is a secret-free template from the CLI, configured for Python 3.12, 512 MiB, and Gunicorn (one process/four threads, 150-second worker timeout). The build helper writes actual secret settings only to ignored artifacts/appsail/app-config.json; catalyst.json selects that source with artifacts/deploy as the build path. SESSION_SECRET is generated privately if missing. Never stage the generated private configuration. The CLI packages and deploys this bundle; public availability is verified separately by health and browser/API checks.

The installed Node 24.19.0 produces a Catalyst CLI security advisory recommending a patched runtime. It has not been disabled or bypassed; resolving the runtime advisory remains an operations follow-up.

## First hosted slice

- URL: https://voltide-50047138433.development.catalystappsail.in (Development environment, reachable without login cookies).
- AppSail ID: 92462000000019001; Python 3.12; 512 MiB; deployed from CLI on 24 October 2026.
- Health: HTTP 200, status=ok, model_configured=true. This is configuration readiness, not a fresh model prediction on each health request.
- Real hosted /api/forecast: 24 aligned predictions from generated, non-private constant weather, model Voltide_Linear_v1:V1, HTTP 200, 0.735 seconds after warm startup. Battery provenance SIMULATED, saved=false. Evidence remains private in artifacts/hosted-forecast-synthetic.json. This does not establish model accuracy or the browser CSV upload flow.
- Browser dashboard renders and calls health successfully. Manual CSV acceptance remains pending because browser upload permission was declined; no alternate browser/upload mechanism was used.

The selected gradient-boosting candidate V1 was the provisional hosted model. After that private configuration switch and successful AppSail redeployment, public health returned HTTP 200 and a real 24-hour generated-weather forecast returned HTTP 200 with `model_version=Voltide_Gradient_v1:V1`, `saved=true`, and 24 hourly results. The browser reopened a Ridge run created before that deployment, confirming history remained usable across the switch. The earlier Ridge endpoint settings remain in ignored local artifacts for rollback. That deployment was not a locked-test or final-model accuracy claim; see model-card.md.

The current deployment uses the final cloud model `Voltide_GB_Final_v1:V1`. After a fresh private bundle and successful official CLI deployment, public health returned HTTP 200 with model/history configured. A real public 24-hour forecast returned the exact final version, 24 hourly results, and `saved=true`; the owner could list/reload it, an unrelated session received 404, and a run saved before this deployment still reloaded. The final endpoint settings are ignored/private; prior candidate settings are retained locally for rollback. None of these integration checks changes the one frozen locked-test result.

The first metadata upload failed because supplied environment names collided with platform-reserved names. Hosted private configuration now prefixes every application variable with VOLTIDE_; runtime readers prefer these over platform-managed names. Local .env names remain compatible. Do not override Catalyst's own reserved environment values.

The first deployed process returned 503 because AppSail executes startup commands directly, without shell expansion. The startup command now explicitly uses `sh -c` and `exec` to expand the platform's port and forward process signals. See the official [startup command requirements](https://docs.catalyst.zoho.com/en/serverless/help/appsail/appsail-configurations/). The subsequent public HTTP 200 verifies the correction. A CLI deployment success or console Live label alone is not application health evidence.

Redeploy after rebuilding with `catalyst deploy --only appsail:Voltide --project 92462000000018001 --org 60093105197 --dc in --non-interactive`. Inspect public health and a real prediction after every deployment. Keep generated deployment settings out of Git.

SDK compatibility: zcatalyst-sdk 1.4.0 constrains typing-extensions to ~=4.12.1. Pydantic 2.13.5 requires >=4.14.1, so these cannot be resolved together. The application now validates the five battery fields with standard Python dataclasses, preserving strict finite numbers, bounds, frozen settings, and structured API errors. Pydantic is no longer a dependency; no vendor constraint was overridden. Project `pip check` passes. The rebuilt Linux bundle with compatible dependencies and SDK storage has been deployed successfully.

## Private run history

Provisioned in the dedicated Development project:

- Data Store table ForecastRuns, ID 92462000000018025. All application columns are mandatory; run_id is unique. App Administrator retains access; App User has no Select/Insert/Update/Delete permissions. The revoked default App User Select permission was verified after reloading the console.
- Encrypted Stratus bucket voltide-runs-92462000000018001, Development URL https://voltide-runs-92462000000018001-development.zohostratus.in. Bucket policy explicitly denies public GetObject/PutObject/DeleteObject and contains no authenticated end-user allow rule. Server SDK administrator access passed a real save/read round trip. No storage object is publicly linked by the API.

| Column | Type / limit |
| --- | --- |
| run_id | varchar 36, unique |
| session_hash | varchar 64 |
| created_at | varchar 40, UTC ISO timestamp |
| first_timestamp / last_timestamp | varchar 64 each, original dataset-local forecast times |
| model_version | varchar 100 |
| feature_version | varchar 20 |
| object_key | varchar 160 |
| peak_demand_kw | double |
| critical_count | int |

Set CATALYST_RUNS_BUCKET and CATALYST_RUNS_TABLE in ignored local settings; the builder maps them to VOLTIDE_* hosted variables. The repository initializes the official SDK from the current Catalyst request with admin scope, rather than caching credentials across requests. Local requests have no Catalyst SDK headers, so local history fails visibly instead of using a local production database.

A signed HTTP-only SameSite=Lax cookie contains a random browser identifier. A server-keyed SHA-256 HMAC scopes the Data Store row and Stratus object key; the raw identifier is never stored in cloud records. Hosted cookies are Secure. All history queries require that scope, and object downloads recheck ownership and the expected object path. A run UUID alone does not authorize access.

Each private runs/{session_hash}/{run_id}.json stores schema version 1, original source_rows, validated_rows with original positions, and the complete result including corrections and battery assumptions. The object is uploaded first; only then is metadata inserted. A failed index write may leave a private orphan object. Failed storage leaves a complete forecast with saved=false and a warning; it never advertises a history record. Logs include only failure stage and exception class, not upstream bodies or credentials.

GET /api/runs lists the newest 20 session summaries. GET /api/runs/{run_id} returns only that session's result. GET /api/runs/{run_id}/export?kind=predictions writes timestamp,target_demand_kw; kind=dispatch includes all dispatch/battery/alert columns. Unknown kinds return 400, missing/other-session runs 404, unavailable history 503. API responses and exports use no-store. Real cloud save, reload after redeployment, authorized history, both exports, cross-session 404, and direct unauthenticated object 403 have been verified with generated non-private input.

The actual local Python 3.13 registration is stale; .venv uses the working Python 3.14 interpreter. Flask 3.1.3 and the pinned requirements were installed into .venv, without training packages. The hosted Python 3.12 runtime has passed public forecast and storage checks.

Project creation evidence is stored locally under ignored artifacts/voltide-project.png; account screenshots are not published to Git.

## Remaining release gates

Source/archive audit on 24 October: `git archive` of the pushed implementation commit contained 85 tracked entries, including `predict.py`, `test_eval.py`, backend and frontend source, requirements, and runbooks. It contained no `.env`, generated `artifacts/`, `.venv/`, `frontend/dist/`, `frontend/node_modules/`, or Python bytecode. The original supplied CSVs remain tracked as project inputs. At this checkpoint, 133 backend tests, 10 frontend tests, the TypeScript/production build, and `pip check` passed. These checks do not replace the pending final-endpoint and browser acceptance gates.

1. Refit import and remote execution are complete: the user uploaded `artifacts/quickml/refit.csv` to QuickML as dataset `Voltide_Refit_v1`, ID 12429000000003055, V1, with 3,200 records and 11 complete columns. Prediction pipeline 12429000000002118 and model 12429000000002121 completed successfully; separate endpoint 12429000000002147 is Published. Real external 1-row and 24-row tests passed exact-column, order, and finite-value checks. Its private endpoint key is under ignored `artifacts/refit-endpoint-private.json`. Browser upload authorization for the agent was declined; the user performed the upload directly. Dataset detail's separate Create Pipeline action also produced an unexecuted Data Transformation pipeline 12429000000002115; it is not connected to this model and performed no fitting.
2. Locked final 800 scored exactly once from the new refit endpoint: 800 aligned real predictions, RMSE 13.2666 kW, MAE 10.1386 kW. The SHA-256 and all subset metrics are frozen in model-card.md and ignored `artifacts/locked-gb-refit-v1-metrics.json`. Do not rerun locked scoring or fit locally.
3. The user imported `artifacts/quickml/final.csv` (all 4,000 labeled rows) as `Voltide_Final_v1` dataset 12429000000002154 V1. Final cloud pipeline/model 12429000000002163/12429000000002166 succeeded with the frozen settings; published endpoint 12429000000002184 passed real 1-, 24-, and 1,000-row contract checks and the unchanged starter evaluator. Its key is in ignored `artifacts/final-endpoint-private.json`. The hosted app is switched and real forecast/storage verified as above. Keep the working Gradient V1 endpoint as rollback. Release source/credential instructions from organizers remain unknown.
4. Human CSV browser acceptance: upload `sample_test_input.csv` through “Choose a telemetry CSV” in the local dashboard. This file is unlabeled sample telemetry; it is not `train_telemetry.csv` or `refit.csv`.
5. The browser viewport override did not change the actual 920-pixel content viewport, so true 390-pixel mobile acceptance remains unverified. Review it on a real narrow viewport. Exact organizer cutoff, judge timeout, dependency installation, and credential handoff remain unknown.

## Information requested from organizers

The exact 28 October cutoff, evaluator invocation mode, timeout, dependency installation procedure, and permitted secret credential handoff are not yet known. These remain release risks; the application and deterministic core can be implemented independently.

## Scope and safety

No local model fitting is permitted, including CPU fitting or learned imputers/scalers. Deterministic parsing/features, remote calls, scoring supplied predictions, application builds, and tests are permitted. Data timestamps are dataset-local wall-clock values; do not infer a timezone from the India account region. Battery values are simulated, with assumptions attached to each run.

Development fixtures can replace remote network boundaries in tests. Production and evaluator paths must never return simulated demand after a QuickML failure. The original CSVs, problem statement, and test_eval.py remain unchanged.
