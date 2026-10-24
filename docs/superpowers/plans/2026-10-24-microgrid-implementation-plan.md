# Voltide: HackSphere Microgrid Implementation Plan

> For agentic workers: this document is a plan, not permission to execute. After explicit implementation authorization, use the executing-plans workflow task by task. No product code is included here, in accordance with the user's request.

**Goal:** Deliver a publicly accessible Catalyst microgrid dashboard with genuine QuickML forecasts, exact dispatch rules, an honest battery simulation, and an evaluator-compatible prediction script before 28 October 2026.

**Architecture:** One AppSail service serves a compiled React dashboard and a Flask API. A shared Python package is used by the API and root predict.py; all learned fitting and model inference are remote in QuickML. Stratus and Data Store persist results and browser-session history.

**Tech stack:** Python 3.12, Flask, Pydantic, requests, pandas, NumPy, Catalyst Python SDK, hosted Gunicorn; React, TypeScript, Vite, Recharts; pytest and Playwright. Pin verified dependency versions when implementing.

**Spec:** ../specs/2026-10-24-microgrid-design.md. Architectural choices are proposed for user review. All future file names below are planned responsibilities, not files that already exist.

## Global constraints

- DO NOT TRAIN ANY PART OF ANY MODEL LOCALLY, including fitted preprocessing or tuning; QuickML performs all fitting.
- Planning creates Markdown only. No application setup, installs, code, uploads, cloud mutations, training, or deployment during this turn.
- Preserve PROBLEM_STATEMENT.md, train_telemetry.csv, sample_test_input.csv, and test_eval.py.
- Keep predict(input_df), one prediction per row, original row/timestamp order, and the two-column CSV contract.
- Storage: demand >160 kW OR hour 18-22 inclusive. Critical alert: demand >=200 kW. Compare unrounded values.
- Dummy predictions may appear in isolated tests only. Production and evaluation errors must be explicit.
- Browser battery values are labeled SIMULATED; control signals are recommendations, not physical commands.
- No secrets in Git, frontend assets, exports, logs, or screenshots.
- Target completion evening of 27 October in Asia/Kolkata; exact 28 October cutoff is not known.

## Review focus

1. Endpoint credentials expire or actual response differs from the starter: token refresh and strict response parsing must be proven in Task 4.
2. Evaluator sends more than 24 rows or shuffled rows: batching and original ordering must be proven in Tasks 2 and 4.
3. Dataset timestamps are interpreted in the browser's timezone: fixed wall-clock rules and 17/18/22/23 boundaries must be proven in Task 5.
4. Battery reserve is reached while the rule still requests storage: preserve the rule and expose shortfall, proven in Task 5.
5. Stored runs disappear or leak across browser sessions: persistence-failure visibility and session isolation must be proven in Task 6.

## Delivery strategy and budget

The user is the sole builder. Model jobs can run in the cloud while independent application work proceeds; this does not require multiple developers. Finish the first deployed real inference path before visual refinement. Freeze product scope after Day 1 and model selection by midday 27 October.

| Period | Required outcome | Approximate focused effort |
| --- | --- | --- |
| 24 October, remaining time / first work block | Review this plan; resolve account access, project, judging constraints | 1.5 hours |
| 25 October | Verified data/features, first remote model, working CLI, initial public deployment | 8-10 hours |
| 26 October | Exact rules, battery simulation, complete input/result UI, storage/history | 8-10 hours |
| 27 October | Model freeze, full live tests, UI corrections, documentation, release package | 7-9 hours |
| 28 October | Submission buffer and necessary fixes only | No new features |

These are planning estimates, not guarantees. Budget roughly 25-30 focused implementation hours plus 4-6 hours contingency. Cloud job/provisioning duration is unmeasured and may add elapsed time. If fewer hours are available, follow the scope-cut order below instead of removing correctness checks.

Critical dependency: account/access -> stable features -> first cloud endpoint -> minimum shared inference client -> deployed forecast. Complete Task 5's controller and battery while cloud jobs run. Day-1 execution order is Task 1 -> Task 2 -> Task 3, with Task 5 during cloud waits -> Task 4a (real auth/client and 1/24-row behavior) -> Task 6a (health/validate/forecast routes) -> Task 7. Then finish Task 4b (CLI, arbitrary batches, full error cases), Task 6b (durable history), and Tasks 8-10. Do not complete full Tasks 4 and 6 before attempting deployment.

The first slice uses the final ForecastRun contract, including complete controller/battery results; until persistence is connected, it returns saved=false with an explicit history-unavailable warning. No temporary response schema or mock inference endpoint is introduced. This is an intentionally incomplete development milestone, not a submission-ready claim. Full acceptance of Tasks 4 and 6 remains mandatory before release.

## Planned file responsibilities

| Planned file or directory | Responsibility |
| --- | --- |
| AGENTS.md | Preserve the no-local-training rule and project-specific development constraints during implementation. |
| predict.py | Thin evaluator function and CSV CLI using the shared inference core. |
| energy/contracts.py | Validated raw rows, feature records, prediction batches, dispatch hours, battery settings, and forecast runs. |
| energy/validation.py | CSV/row parsing, cleanup provenance, dashboard windows, evaluator ordering. |
| energy/features.py | Feature contract v1 and deterministic training/inference transform. |
| energy/quickml.py | Remote client, refresh-token auth, batching, deadlines, output normalization. |
| energy/controller.py | Pure fixed switching and critical-alert rules. |
| energy/battery.py | Pure one-hour energy simulation and shortfall calculations. |
| energy/forecast.py | Validated inputs -> inference -> controller -> simulation -> response summary. |
| energy/storage.py | Catalyst SDK integration, Stratus run documents, Data Store session index. |
| energy/config.py | Required environment settings, secret validation, regional configuration. |
| web/app.py | Flask setup, API routes, signed sessions, errors, request limits, and SPA serving. |
| frontend/src/App.tsx | Main input/result workflow and UI state transitions. |
| frontend/src/api.ts and types.ts | Typed application API boundary and browser-side contracts. |
| frontend/src/components/ | TelemetryInput, DemandChart, DispatchTable, BatteryPanel, RunHistory. |
| frontend/src/styles.css | Responsive, accessible visual styling and status states. |
| tools/prepare_quickml_data.py | Fixed feature calculations and chronological CSV partition preparation; no fitting. |
| tools/score_predictions.py | RMSE/MAE and subset metrics from supplied labels/predictions; no fitting. |
| tests/ and frontend/tests/ | Core, request-contract, CLI, and browser acceptance checks. |
| docs/model-card.md and docs/operations.md | Evidence of model selection, inference contract, credentials, deployment, and recovery. |
| README.md, requirements.txt, requirements-dev.txt, frontend/package.json | Reproducible setup, pinned dependencies, development and verification commands. |
| catalyst.json, app-config.json, .env.example, .gitignore | Deployment and configuration artifacts generated/verified only after implementation approval. |

Small files may be combined if they stay focused; do not create abstract provider frameworks or separate microservices. Empty package markers and standard frontend build configuration are included in the owning tasks rather than standalone work.

## Task 1: Verify access and freeze the external integration facts

**Estimate:** 1.5 focused hours, excluding external provisioning waits. **Depends on:** implementation authorization.

**Files:** Create docs/operations.md and AGENTS.md; establish project-local Git/configuration only within this folder. Do not use an unrelated ancestor checkout if Git resolves to the user's home directory.

**Interfaces:** Produces an integration record: dedicated project/organization identifiers, data center, environments, supported runtime/CLI versions, credential method, available QuickML algorithms, account limits, judging input/output/credential rules, and ownership of human-only steps.

- [ ] Confirm the exact submission cutoff, whether the evaluator imports predict or invokes the CLI, its timeout, dependency installation method, and how secret credentials may be supplied. Unknown judge rules are recorded as unresolved release risks, not guessed.
- [ ] Confirm account verification, QuickML entitlement, endpoint publishing, production/public app access, and an acceptable account budget. Create the dedicated project only when execution is authorized; leave Project-Rainfall untouched.
- [ ] Confirm dataset upload/pipeline configuration through the console and source deployment through the CLI/console. User handles sign-in, consent, or account/billing actions that tools cannot perform.
- [ ] Record no-local-training in root development instructions. Verify runtime and SDK support against the actual account; preserve only nonsecret identifiers in documentation.npm install -g zcatalyst-cli

**Acceptance:** A project can host the required services and credentials can be supplied to both the hosted app and evaluator. If QuickML or production access is blocked, investigate immediately; do not present a mock as a substitute for the required deliverable. App work and pure tests can still proceed.

## Task 2: Define shared data contracts and deterministic features

**Estimate:** 2 hours. **Depends on:** Task 1's environment decisions.

**Files:** Create energy/contracts.py, validation.py, features.py, config.py, tools/prepare_quickml_data.py, and tests/test_validation.py, test_features.py; add the minimal pinned Python dependencies and .env.example.

**Interfaces:** parse_telemetry produces cleaned rows, original positions/timestamp strings, and correction issues. select_forecast_window produces exactly 24 ordered hourly rows. build_features produces contract-v1 records from those rows without fitting. Prepared cloud partitions retain row identity outside model features.

- [ ] Write tests first for BOM/whitespace, missing columns, wrong numeric types, empty input, humidity/irradiance bounds, leading and repeated missing cells, single-cell carry-forward, shuffled evaluator rows, duplicate evaluator timestamps, invalid dashboard gaps, and ignored target columns.
- [ ] Implement the shared contracts and the exact cleanup policy from the design. Keep dashboard validation separate from evaluator row-count requirements.
- [ ] Test numeric hour, 24-hour sine/cosine, weekday/month/weekend, and cooling-degree features against fixed timestamp/temperature examples; ensure the cloud-upload and inference transforms produce identical features.
- [ ] Prepare separate 2,400-row development, 800-row selection, 800-row locked-test, 3,200-row refit, and 4,000-row final feature CSV artifacts without modifying originals. Keep generated data out of the hosted app bundle.
- [ ] Run the focused validation/feature tests; record exact split timestamps, input hashes, feature names/types/order, and feature version.

**Acceptance:** Both input paths share one policy, all feature calculations are deterministic, and no fitting occurs locally. Generated cloud CSVs contain the expected target only where required; labels never enter inference features.

## Task 3: Train and publish the first usable QuickML model

**Estimate:** 2.5 focused hours plus unmeasured cloud execution. **Depends on:** Tasks 1-2.

**Files:** Create docs/model-card.md and sanitized endpoint input/output fixtures in tests/fixtures/quickml/.

**Interfaces:** Produces a real deployed model endpoint, feature-version binding, auth/header contract, normalized prediction mapping, observed request limits, and sanitized successful/error responses. No guessed predictions response key.

- [ ] Upload only the development partition into QuickML for the first candidate; select target_demand_kw as regression target. Verify target exclusion from input features and record actual internal train/validation behavior.
- [ ] Train a regularized linear candidate remotely, or the available documented linear fallback. If that candidate cannot produce a usable endpoint promptly, train one documented tree regressor remotely and record the change.
- [ ] Publish a versioned endpoint and use its generated sample to record real OAuth, endpoint-key, organization, project, environment, and regional domain requirements.
- [ ] Obtain correct one-row and 24-row responses; compare row count and alignment. Measure a candidate larger batch before choosing a configurable batch size.
- [ ] Capture latency and failures without exposing secrets. Establish the first deployable endpoint before starting additional model experiments.

**Acceptance:** Real endpoint returns one numeric prediction per supplied row with known alignment. All training happened in QuickML. Exact model accuracy remains unclaimed until Task 9.

## Task 4: Complete the shared inference client and evaluator CLI

**Estimate:** 3 hours. **Depends on:** Task 3's verified endpoint contract.

**Files:** Create energy/quickml.py; modify predict.py; create tests/test_quickml.py, test_predict.py, and test_cli.py. Preserve test_eval.py.

**Interfaces:** QuickMLClient.predict_rows consumes feature records and produces a flat ordered vector or a typed error. Root predict consumes a pandas DataFrame and returns a NumPy array. CLI consumes --input/--output and writes timestamp,target_demand_kw on complete success.

**Execution split:** Allocate approximately 1.5 hours to 4a: verified live auth/refresh, response parsing, and 1/24-row prediction tests. This unlocks first deployment. Allocate the remaining 1.5 hours to 4b: arbitrary batching, CLI, 1,000-row verification, and the complete failure matrix after Task 7. The task is not accepted until both are complete.

- [ ] Write tests using sanitized endpoint fixtures for real response shape, token refresh, authentication failure, 429 Retry-After, 5xx, timeout, malformed JSON, wrong result counts, nested/non-numeric outputs, negative/NaN/infinite values, and chunk reassembly.
- [ ] Implement explicit configuration validation, secret-safe regional authentication, bounded retries/deadlines, and sequential batching. One failed chunk fails the overall call; no formula fallback remains on production paths.
- [ ] Implement the evaluator wrapper without dashboard-only restrictions. Verify 1, 24, 25, and 1,000 rows, shuffled input, duplicate valid timestamps, and unchanged input DataFrames.
- [ ] Implement CLI validation and atomic output writing so failure does not leave a partial successful CSV. Logs go to stderr; timestamp strings and row order are preserved.
- [ ] Run focused tests and the unchanged python test_eval.py against the actual remote model. Run the documented CLI with sample_test_input.csv; verify exactly 1,000 output rows and the two required columns. Record total latency and compare with any known judge limit.

**Acceptance:** Import and CLI paths both produce genuine QuickML results; missing credentials and endpoint failures are visible failures. No secret is embedded to make the evaluator pass.

## Task 5: Implement exact control rules and battery simulation

**Estimate:** 2 hours. **Depends on:** Task 2; can proceed while cloud jobs run.

**Files:** Create energy/controller.py, battery.py, and forecast.py; create tests/test_controller.py, test_battery.py, test_forecast.py.

**Interfaces:** evaluate_dispatch produces requested_mode, reasons, and critical_overload for each prediction. simulate_battery consumes chronological dispatch rows and validated BatterySettings, producing start/end SOC, delivered power, and unserved power. ForecastService.run composes these with remote predictions into a ForecastRun without persistence concerns.

- [ ] Write boundary tests for demand 159.99, 160, 160.01, 199.99, 200, and 200.01; hours 17, 18, 22, 23; each independent condition; midnight/date rollover; and different browser/system timezones. Use full precision before display rounding.
- [ ] Implement the exact rules and stable reason codes. Thresholds are fixed by the spec, not dashboard sliders.
- [ ] Test battery defaults, invalid settings, reserve equality, starting at reserve, partial delivery, maximum discharge rate, efficiency loss, and no discharge in MAIN_GRID mode. Assert energy balance, SOC bounds, and chronological state carry-over over 24 hours.
- [ ] Implement no-charge simulation and explicit STORAGE_SHORTFALL without changing requested mode. Compute summaries from the same hourly results, with one-hour kW-to-kWh conversion.
- [ ] Verify the composed service uses supplied prediction results, labels battery provenance, and returns 24 aligned rows with exact summary totals.

**Acceptance:** All specified threshold combinations and energy constraints pass deterministic checks; no real actuation or fabricated generation is implied.

## Task 6: Add the API and Catalyst-backed run persistence

**Estimate:** 2.5 hours. **Depends on:** Tasks 4-5 for full path; can start route contracts earlier.

**Files:** Create web/app.py and energy/storage.py; add tests/test_api.py and test_storage.py; document the ForecastRuns table columns/object layout in docs/operations.md.

**Interfaces:** Routes and response fields are the design's API contract. RunRepository.save_run returns saved status and a run identifier; get_run and list_runs require the current session scope. Forecast calculation remains independent of SDK request initialization.

**Execution split:** Allocate about 0.75 hours to 6a: health, original-source validation, forecast routes, and the final ForecastRun response with saved=false until storage is wired. This unlocks Task 7. Complete 6b's SDK storage, scoped history, exports, and full error checks after the first deployment, within the remaining task estimate.

- [ ] Test validation/forecast routes with deterministic upstream fixtures, row limits, file limits, status/error mapping, correction provenance, HTTP-only signed sessions, and per-process throttling. Include a CSV whose selected window's first missing value is filled from the preceding source hour: preview and final forecast must preserve the same original cell, source position, filled value, and reason after resubmitting the original file.
- [ ] Implement GET health, POST validate/forecast, session-scoped GET runs/run/export, request identifiers, and server-side configuration. Connect only the verified SDK/service credentials.
- [ ] Create private Stratus storage and the ForecastRuns metadata table when authorized. Initialize the SDK per request according to the documented AppSail integration.
- [ ] Save result objects before publishing metadata. Test object-store failure, index-write failure, successful save/reload, anonymous cross-session denial, nonexistent runs, and newest-20 history ordering.
- [ ] Verify a real saved run is retrievable after an application restart and an independent browser cannot read it by run ID. Verify saved=false is visible and computed results remain exportable when storage is unavailable.

**Acceptance:** A complete API round trip uses QuickML and durable cloud storage. No SQLite/local filesystem is treated as production persistence. No public storage credentials or cross-session run access.

## Task 7: Deploy the first complete vertical slice

**Estimate:** 1.5 hours; do as early as feasible on Day 1. **Depends on:** Tasks 3, 4a, 5, and 6a. Full evaluator hardening and durable history follow; neither gates this initial deployment.

**Files:** Create verified catalyst.json/app-config.json, frontend build configuration and a minimal application shell; update requirements and docs/operations.md. Exact platform config keys come from current tooling, not invented examples.

**Interfaces:** Produces a stable public origin serving the UI and /api paths, with required private runtime configuration and the real model endpoint.

- [ ] Build the minimal frontend shell with input submission and a prediction table. Bundle compiled frontend assets with the Python application; do not ship training CSV partitions or .env files.
- [ ] Configure Python 3.12, supported production serving, the platform-supplied listen port, and private runtime secrets. Verify SDK permissions and QuickML network/auth access in the hosted environment.
- [ ] Deploy and open the public URL in a logged-out browser. Upload a 24-hour window and obtain real predictions and control outputs.
- [ ] Record the deployment/version, health result, endpoint model version, and first public workflow evidence. Keep a known-working deployment before further refinement.

**Acceptance:** The deployed UI calls its own API successfully, and that API calls real QuickML. A local-only demonstration or an authenticated console preview does not meet this gate.

## Task 8: Finish the dashboard and input/export experience

**Estimate:** 4 hours. **Depends on:** stable API contracts and Task 7.

**Files:** Implement frontend/src/App.tsx, api.ts, types.ts, styles.css, and the five components listed above; add frontend/tests/forecast.spec.ts for core browser flows.

**Interfaces:** Browser components consume ForecastRun; they do not duplicate controller or battery calculations. UI-created CSV uses the backend field contract and can also export an unsaved successful result.

- [ ] Implement file upload with preview/window selection and the editable 24-row manual table. Preserve the original file/manual source for forecast submission with window_start and battery_settings; do not replace raw source with cleaned preview rows. The sample action uses supplied historical weather and visibly identifies the source.
- [ ] Implement explicit loading, validation, error, previous-result, and successful states. A failed new request keeps the old chart labeled previous; rapid repeated clicks cannot overwrite newer state with an older response.
- [ ] Render the demand chart, fixed threshold lines, selected-hour mode/reasons, critical banners, battery assumptions/SOC/shortfalls, summary cards, detailed hourly table, exports, and session history.
- [ ] Add keyboard access, visible focus, chart alternatives in the data table, readable units, mobile stacking, and text labels for status colors. No fictitious accuracy, savings, renewable-generation, or live-device badges.
- [ ] Run browser checks for CSV -> validation -> real forecast -> saved history -> reload -> export; manual edit -> corrected result; invalid input; upstream failure; shortfall; storage failure; and a narrow mobile viewport.

**Acceptance:** A judge can understand and exercise the required flow without a developer explaining it. Every displayed number can be traced to input, real model output, fixed rules, or visibly stated battery assumptions.

## Task 9: Select the remote model and freeze the production version

**Estimate:** 2 focused hours plus cloud time. **Depends on:** Tasks 2-4. Start additional candidates after Task 7; freeze by midday 27 October.

**Files:** Complete tools/score_predictions.py, its scoring tests, docs/model-card.md, and version/schema metadata consumed by the app.

**Interfaces:** Consumes prepared chronological partitions and saved remote predictions; produces selected feature/model version, reproducible metrics, production endpoint selection, and rollback endpoint/version.

- [ ] Compare the first linear candidate with gradient-boosting and random-forest candidates, all cloud trained on the development partition and evaluated on the same external selection rows. Allow at most one additional bounded improvement experiment before freeze.
- [ ] Verify the local scoring tool with hand-checkable predictions and timestamp alignment; calculate RMSE, MAE, and populated peak/hot subsets. No local fitting or post-hoc calibration.
- [ ] Freeze the candidate, refit remotely on the first 3,200 rows according to verified platform behavior, then score the locked final 800 exactly once. Document the effective training rows and limitations.
- [ ] Publish the final cloud version using the 4,000-row dataset according to verified platform behavior. Preserve the previously working endpoint until the final one passes schema, feature, one-row, 24-row, and 1,000-row regression checks.
- [ ] Record actual metrics and provenance, never a promised hidden-test score. Report poor results honestly. If time/access prevents comparison, ship the best verified remote candidate and document the reduced experiment set.

**Acceptance:** Selected version has documented chronological evaluation, stable production inference, and a recoverable previous version. The unlabeled sample is never used to report accuracy.

## Task 10: Verify the real release and prepare the submission

**Estimate:** 3 focused hours plus contingency. **Depends on:** Tasks 1-9.

**Files:** Complete README.md, docs/operations.md, docs/model-card.md, dependency locks, and release evidence; create a clean source archive if a repository URL is not the chosen submission format.

**Interfaces:** Produces the public URL, reproducible source, working evaluator entry point, secret-delivery instructions, and model/deployment evidence.

- [ ] Run all core/API/CLI tests, TypeScript checks, production build, and browser acceptance checks. Run unchanged test_eval.py and the documented CSV CLI against the final real endpoint. Explicitly count output rows and verify timestamp order and finite values.
- [ ] Check logged-out public access, hard refresh/static routing, mobile layout, saved-run persistence, session isolation, absent/expired credentials, controlled upstream failure, and token refresh. The 24-hour result must come from the same recorded model version shown in the UI.
- [ ] Record measured 24-hour and 1,000-row latency. Set client/server timeouts from those measurements and platform limits; do not invent a judge timeout or a performance guarantee.
- [ ] Document installation, local application development without training, QuickML cloud training steps, environment names, credential refresh, exports, battery assumptions, dataset-local timestamps, deployed URL, rollback, and known limitations. Keep required evaluator dependencies explicit.
- [ ] Verify source/archive contents exclude credentials, generated model/data artifacts, node_modules, caches, and local environment files; include both frontend/backend source and model/deployment instructions. Confirm the chosen Git root is this project.
- [ ] Freeze on the evening of 27 October; preserve the working deployment and source snapshot. Submit before the confirmed 28 October cutoff. Public GitHub publication or final submission is performed only when explicitly authorized.

**Acceptance:** All checklist items below have evidence; remaining limitations are written plainly. No additional scope is started on submission day.

## Release acceptance matrix

| Requirement | Evidence required |
| --- | --- |
| No local training | Training records identify QuickML; local tools perform only deterministic preparation/scoring; no local training commands or model artifacts. |
| Genuine model | Cloud model/endpoint/version and real successful requests; no fallback predictions. |
| Evaluator compatibility | Unchanged self-test succeeds against final endpoint; 1,000-row CSV output has exact columns, count, timestamps, and finite values. |
| 24-hour forecasting | CSV and manual flows each produce 24 consecutive hourly results from supplied weather. |
| Cleanup | Cell-level feedback and correction provenance; invalid/missing leading weather fails clearly. |
| Controller correctness | Strict 160 boundary, inclusive 18/22, and inclusive 200 alert tests pass. |
| Battery honesty | SIMULATED label, visible assumptions, correct energy balance, reserve/power limit, explicit shortfall. |
| Dashboard usability | Demand curve, mode timeline, critical banners, SOC, data table, exports, and mobile flow verified. |
| Durable history | Saved run survives restart; only same browser session can access it; persistence failures are visible. |
| Deployment | Public Catalyst URL works logged out and exercises the real browser -> API -> QuickML -> storage path. |
| Accuracy evidence | Chronological split/model/feature versions and measured RMSE/MAE; no accuracy claim from unlabeled data. |
| Submission readiness | Complete source, README, secure evaluator credential handoff, and stable release URL. |

## Scope cuts and blockers

Cut in order if time slips: playback animation; decorative motion; elaborate chart interactions; extra model tuning beyond the three initial candidates; rich history filters; extra visual styling. Keep the main chart, 24-row manual/CSV inputs, basic newest-20 history, exports, exact controller, labeled battery simulation, genuine QuickML inference, deployment, and submission contract.

If by the end of 25 October no real endpoint/public slice exists, stop polish and resolve account/model/deployment integration first. If the account cannot provide QuickML, there is no compliant local-model workaround. If the model response or auth contract differs from documentation, isolate the change in the shared client and retest both app and evaluator. If storage setup delays the public slice, deploy predictions first and restore required persistence before final acceptance. If cloud fitting is slow, freeze the first usable verified model instead of replacing it with fabricated values.

## Plan self-review

The task mapping covers all five key requirements, the exact rule table, both evaluator interfaces, secure cloud integration, a public deployment, and all submission deliverables. Names and response fields are shared through the design rather than independently invented per task. Each Review Focus item has an owning task and explicit checks. An independent builder review identified raw-input/correction-lineage loss and an overlong first-deployment dependency chain; both were corrected with original-source resubmission and explicit 4a/6a deployment checkpoints. External account/endpoint/judging facts remain discovery gates with defined consequences, not invented capabilities. No implementation or model training is authorized or performed by the existence of these documents.
