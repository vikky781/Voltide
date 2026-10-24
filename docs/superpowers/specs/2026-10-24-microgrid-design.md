# Voltide: HackSphere Microgrid Design

Status: proposed design for user review; implementation is not authorized by this document.

Date: 24 October 2026. Submission date: 28 October 2026; exact cutoff is unknown. Internal completion target: evening of 27 October, Asia/Kolkata. Team: one person.

## Intent and success

Build the application in PROBLEM_STATEMENT.md: accept hourly weather inputs, obtain demand predictions from a regression model trained and published in Zoho Catalyst QuickML, apply the prescribed switching rules, and show a usable dashboard at a public Catalyst URL. Preserve the evaluator's predict(input_df) interface and implement its documented CSV command-line interface.

Success requires real remote inference, correct control signals, usable input and output flows, a public deployment, and a reproducible submission. A starter self-test passing on dummy predictions is insufficient. Scoring priorities are model accuracy 35%, deployment/functionality 35%, controller 20%, and UI/UX 10%.

## Hard constraints

- DO NOT TRAIN ANY PART OF ANY MODEL LOCALLY. This includes CPU training, fitting imputers/scalers/encoders, hyperparameter searches, and automatic retraining. All learned fitting happens inside QuickML.
- Local parsing, fixed mathematical feature calculations, API calls, scoring already-produced predictions, application builds, and tests are permitted. No local ML training dependencies or model weight artifacts are needed.
- Planning work creates only these Markdown documents. No product code, scaffolding, dependency installs, cloud resources, dataset uploads, training, or deployment occurs during planning.
- Keep the provided datasets, problem statement, and test_eval.py unchanged.
- Keep credentials outside source control and browser bundles. Never silently substitute dummy predictions for a failed QuickML call.
- No numerical accuracy, cloud cost, latency, or delivery guarantee is asserted before measurement.

## Evidence and unknowns

The repository contains exactly five starter files. predict.py has an unset endpoint, a generic request template, and a formula fallback; it lacks CSV CLI arguments/export. There is no existing application or deployment configuration. The provided self-test passed previously, using the fallback.

Training contains 4,000 labeled hourly rows; the sample contains 1,000 later unlabeled rows. There were no missing numeric values or duplicate timestamps in the initial inspection. Average temperature shifts from 18.50 C in training to 29.22 C in the sample. The sample cannot support RMSE calculation because labels are absent.

The connected Catalyst account is reachable. A project named Project-Rainfall exists; it is not assumed to belong to this work. The user reports no project/model for this task. Plan a dedicated project and preserve that existing project. Account entitlement to QuickML, production deployment, quotas, billing limits, endpoint availability, and provisioning time still require verification.

The connector exposes project/model discovery and endpoint metadata, but its discovered tools do not include general local CSV dataset import or AppSail source deployment. Use the Catalyst console for dataset upload/pipeline configuration and the documented CLI/console for deployment when implementing. Do not assume every action is automatable through this connector. The onboarding site linked in the brief could not be read by the web tool; official documentation was used instead.

## Architecture decision and alternatives

Recommended, not yet selected by the user: one AppSail deployment serves a built React dashboard and a Flask API on the same origin. A shared Python package supplies validation, features, remote inference, control, and battery calculations to both the API and root predict.py. QuickML owns training and inference; Stratus stores run documents; Data Store indexes run history.

| Approach | Benefit | Cost and decision |
| --- | --- | --- |
| React plus Python API in one AppSail service | One public origin, one deployment, shared Python logic, simpler debugging | Frontend and backend deploy together. Recommended for the solo deadline. |
| Slate frontend plus AppSail API | Independent frontend deployment; follows the brief's recommended example | Two deployments and cross-origin/routing setup. Valid alternative if independent hosting becomes necessary. |
| Slate plus multiple Functions | Small independently deployable handlers | More packaging, invocation, and shared-core wiring. No clear benefit for this small app. |

AppSail's documented managed runtimes include Python 3.12, and its Flask guide and Python SDK integration are documented. The brief explicitly permits Slate / AppSail hosting. See [runtime support](https://docs.catalyst.zoho.com/en/serverless/help/appsail/catalyst-managed-runtimes/key-concepts/), [Flask deployment](https://docs.catalyst.zoho.com/en/serverless/help/appsail/help-guides/python/flask/), and [SDK integration](https://docs.catalyst.zoho.com/en/serverless/help/appsail/implement-catalyst-sdk/).

Proposed stack: React, TypeScript, Vite, Recharts; Python 3.12, Flask, Pydantic, requests, pandas, NumPy, Catalyst Python SDK, Gunicorn on hosted Linux; pytest and Playwright. Use a supported Node LTS for the frontend build. Pin actual compatible dependency versions during implementation, not from guesses in this plan.

## Product flow and scope

1. Open the public app and see service status, input options, and explicit data provenance.
2. Upload CSV or edit a 24-row hourly input table. A sample action loads 24 consecutive supplied sample rows, visibly labeled historical sample inputs.
3. Preview validation issues and any missing-value corrections before requesting a forecast. The browser retains the original uploaded file or unmodified manual source, not just the cleaned preview.
4. Request a 24-hour forecast by submitting that original source and selected window start. The backend reruns cleanup against the source, preserves correction provenance and preceding-hour context, selects 24 rows, constructs features, calls QuickML, validates outputs, applies rules, simulates battery delivery, and saves the completed run.
5. Inspect the load curve, requested mode timeline, critical alerts, simulated battery charge, per-hour explanation table, and session history. Export the two-column evaluator CSV or the detailed dispatch CSV.

The dashboard has one main page rather than multiple product sections. At desktop widths, put input/controls beside the results; stack them on mobile. The chart uses kW and visible 160/200 kW reference lines. Every status uses text as well as color. Empty, validating, requesting, successful, failed, and saved-but-stale states must be distinct.

Summary values: peak demand, total forecast energy in kWh, count of storage-request hours, critical-hour count, and final simulated state of charge. A selected-hour cursor controls the mode badge and battery value. Optional play/pause advances through stored results; it does not claim live telemetry or issue repeated API calls. Initially select the first forecast hour, not the computer's current hour.

Included: upload/manual inputs, 24-hour forecasts, exact rules, labeled battery simulation, bounded session history, exports, real deployment, and submission documentation. Excluded: hardware actuation, live weather feeds, autonomous schedules/retraining, user-management screens, optimization-based dispatch, savings/carbon claims, invented confidence intervals, and a chatbot.

## Input, time, and cleanup contracts

Public raw fields are timestamp, ambient_temp_c, humidity_pct, solar_irradiance_wm2. Timestamp format is YYYY-MM-DD HH:MM:SS. The dataset has no timezone metadata: treat timestamps as dataset-local wall-clock values and do not convert them using browser timezone or assume they are Indian time. User-facing schedule dates use Asia/Kolkata.

The 24-hour API requires exactly 24 unique, consecutive hourly timestamps, ordered oldest first, with minute/second zero. For larger uploaded CSVs, validate and let the user choose a valid 24-hour window; do not silently take the first window. Duplicate/gapped windows receive row-specific errors. Manual entry creates the 24 timestamps from a selected starting hour and requires weather values for each.

The evaluator predict function and CSV CLI accept any nonempty row count, including 1 and 1,000; they do not impose the dashboard's 24-row restriction. Preserve original row order and timestamp strings. Duplicate valid timestamps can be scored independently by the evaluator path. The web API ignores an accidentally supplied target column with an explicit warning; target values never reach the feature payload.

Cleanup trims headers/cells, handles UTF-8 BOM, and parses numeric cells. Empty/null cells, including pandas missing-value markers in the imported evaluator DataFrame, are treated as missing; literal nonnumeric text such as NaN in a raw CSV cell is invalid. Reject malformed numeric text, infinity, humidity outside 0-100, negative irradiance, or unparseable timestamps. Missing weather cells may be forward-filled only from the immediately preceding consecutive hourly reading with an originally valid value for that same field; a second consecutive missing value or a leading missing value is rejected. Each filled cell is recorded. Do not use later rows, training-target values, or silently invented averages. API preview and forecast use the same cleanup policy. Evaluator cleanup restores original order after chronological inspection and never forwards through ambiguous duplicate timestamps. Empty files are errors; extra unrelated columns are excluded with warnings.

The upload limit is a proposed application limit of 2 MiB and 10,000 rows, not a claimed Catalyst quota. Validate bytes and row count before paid inference. CLI inference is chunked and is not restricted by the dashboard upload cap.

## Modeling and honest validation

Use supervised per-row regression because hidden evaluation supplies timestamp and weather rows, not historical target demand. Avoid target lags, target rolling averages, or an autoregressive interface requiring unavailable labels.

Preserve the original files. The first 2,400 labeled rows are model-development training data; rows 2,401-3,200 are chronological selection validation; rows 3,201-4,000 remain a locked chronological test until the feature/model choice is frozen. All splits follow timestamp order. If data quality inspection finds a timestamp discontinuity, document it before fixing split boundaries.

First establish an end-to-end model using weather plus hour features. Feature contract v1 contains the three weather values, numeric hour, hour sine/cosine with period 24, weekday number Monday=0, month number, weekend flag, and fixed cooling degrees above 24 C. These are fixed calculations, with no locally learned parameters. A shared transform generates the cloud training-upload features and the inference features. Raw timestamps remain identifiers and rule inputs; do not pass their raw strings as numeric regression features. Reject unexpected feature versions.

Compare a regularized linear regression, gradient-boosting regression, and random-forest regression in QuickML on the same feature contract and held-out validation rows. The exact regularized linear option is chosen from those available in the account; ordinary linear regression is the documented fallback. QuickML documents regression families in its [algorithm reference](https://docs.catalyst.zoho.com/en/quickml/help/ml-algorithms/regression-algorithms/). Start with platform defaults; permit at most one bounded feature/hyperparameter improvement experiment on the leading candidate before the scheduled model freeze. No exhaustive search or locally fitted ensemble.

For each cloud candidate, obtain predictions on the external 800-row selection set and compute RMSE and MAE locally without fitting. Also inspect hot-weather and >=200 kW subsets when populated, to expose peak underprediction. QuickML internal metrics are supplementary: [its release notes](https://docs.catalyst.zoho.com/en/release-notes/all/?service=quickml) describe a default internal 80/20 split, so do not assume uploading a partition means all those rows were used in fitting. Capture the actual configuration and effective row usage.

Freeze the candidate; train a new cloud version using only the first 3,200 rows; score the untouched final 800 once. Report that result with its exact split and version. Then create a final cloud version using the 4,000 labeled rows according to verified platform training behavior. Do not mislabel a full-data fit's internal score as untouched test performance. Keep the previous tested endpoint until the final version passes inference regression checks. If the final evaluation disappoints, report it honestly; reopening selection consumes the lock and requires a newly described validation protocol.

Record pipeline/model/endpoint versions, input schema, feature version, split boundaries, metrics, and actual train-row behavior in docs/model-card.md. A numerical RMSE target cannot responsibly be fixed before the first cloud result. The 1,000-row sample is for shape, latency, and integration testing only.

## QuickML integration boundary

The real endpoint contract must be retrieved from its published sample and confirmed with a one-row and 24-row request before client completion. The starter's predictions response key is not established evidence of the real format.

The [endpoint documentation](https://docs.catalyst.zoho.com/en/quickml/help/pipeline-endpoints/) specifies external OAuth and endpoint-key authentication, with organization/environment context and QuickML.deployment.READ scope. The connector's inference schema additionally exposes project context. Copy required headers and payload shape from the actual endpoint; do not assume connector-supplied authentication is available to deployed Python or evaluator execution.

Use server-side regional endpoint/accounts domains from actual project metadata. Support refresh-token credentials through secret environment variables and cache short-lived access tokens until shortly before expiry. Keep endpoint keys, refresh tokens, client secrets, and raw authorization headers out of logs. Refresh once on an expired-token response; do not retry permission errors indefinitely.

Choose and record batch size from measured supported behavior. Verify single-row, 24-row, and 1,000-row runs. Sequential chunks preserve input position. Require exactly one finite, nonnegative numeric prediction per row; reject malformed, partial, or ambiguous responses. Preserve full precision until presentation. Retry rate-limit/transient failures at most twice, respecting Retry-After and a configurable total deadline; do not retry validation failures. Never produce a successful partial CSV. Mock responses are test fixtures only, never a production inference mode.

## Exact controller contract

For every row, requested_mode is RENEWABLE_STORAGE if demand is strictly greater than 160 kW OR the timestamp hour is 18, 19, 20, 21, or 22. Otherwise requested_mode is MAIN_GRID. critical_overload is true at demand >=200 kW independently of the mode calculation. Evaluate unrounded demand.

Return reasons as a list containing DEMAND_THRESHOLD and/or PEAK_WINDOW, or NORMAL_LOAD when neither applies. Thresholds and the time window are fixed submission rules, not user-editable settings. The controller is a pure calculation used by the web app; export the resulting signals. No physical switch is actuated.

## Battery simulation contract

The dataset contains no battery telemetry or renewable generation measurements. Label all battery values SIMULATED. Initial defaults, chosen for this demonstration rather than inferred from data: capacity 2,000 kWh; starting SOC 80%; reserve SOC 20%; discharge limit 250 kW; discharge efficiency 95%; one-hour steps. Show assumptions next to the chart, permit validated changes, and snapshot them per run. Require positive capacity/limit, 0 < efficiency <=100%, and 0 <= reserve <= initial SOC <=100%.

At MAIN_GRID hours, demand is assigned to main grid and battery energy is unchanged. At RENEWABLE_STORAGE hours, battery output is limited by requested demand, the 250 kW limit, and available energy above reserve after discharge efficiency. Energy removed equals delivered kW times one hour divided by efficiency. Never cross reserve or exceed capacity. Report delivered battery kW and remaining unserved kW separately.

No charging is simulated because panel area, conversion efficiency, generation, and charging telemetry are unknown. Initial stored energy is an explicit assumption. Do not convert irradiance directly into charging power. If battery cannot meet demand, preserve the required requested mode and show STORAGE_SHORTFALL; do not invent an override, silently assign backup power, or claim demand was met.

## Persistence, API, and failure behavior

Use a signed, secure, HTTP-only browser session cookie to scope history to that browser. Store only a hash of the session identifier with each run. Run IDs alone do not grant access to another session's run. A public demo page does not need account registration.

Stratus privately stores raw input, validated rows with correction provenance, and a completed result document under a server-generated run UUID. Data Store ForecastRuns indexes run_id, session_hash, created_at, first/last forecast timestamp, model/feature versions, peak demand, critical count, and result object key. List newest 20 runs for that session. Creation times are UTC; forecast times retain dataset-local semantics. Server routes proxy authorized results/exports rather than expose storage credentials or public bucket listings. Stratus supports the Python SDK; see its [introduction](https://docs.catalyst.zoho.com/en/cloud-scale/help/stratus/introduction/).

Save objects first, then publish the Data Store index entry. A persistence error returns the computed result marked saved=false with a visible warning; CSV export from that in-memory result remains available in the browser, but no history record is advertised. History only lists completed indexed runs. Temporary orphan objects may remain after a failed index write; accept this limited cleanup debt for the hackathon rather than invent transactional guarantees.

API contracts: GET /api/health returns process status without secrets and performs no paid prediction. POST /api/validate accepts original source_rows or a multipart CSV file and returns cleaned preview rows, candidate window starts, warnings, and cell errors. POST /api/forecast accepts the same original source plus window_start and battery_settings; JSON carries source_rows, while multipart requests carry the file and those two fields. It revalidates/recleans the original source, retains source positions and correction lineage, selects exactly 24 rows, and returns a ForecastRun. Manual entry uses source_rows and its starting timestamp. Never accept a cleaned preview as proof of valid raw input. GET /api/runs lists session summaries; GET /api/runs/{run_id} returns an authorized result; GET /api/runs/{run_id}/export supports predictions or dispatch CSV. Responses include a request_id. The frontend uses returned cell errors instead of showing generic failure toasts.

A ForecastRun contains run_id, model_version, feature_version, generated_at, saved, warnings, battery_settings, summary, and 24 hourly results. Each hourly result contains timestamp, target_demand_kw, requested_mode, reasons, critical_overload, battery_soc_start_pct, battery_soc_end_pct, battery_delivered_kw, and unserved_kw. The dispatch CSV uses these hourly names; the evaluator CSV contains only timestamp and target_demand_kw.

Use 400 for malformed requests, 413 for upload size, 422 for row/window errors, 429 for the application request limit, 502 for invalid upstream responses, and 503 for unavailable/misconfigured upstream service. A failed forecast never replaces the last successful chart; keep it explicitly marked as a previous result. Bound the original source by the upload limits and send exactly 24 selected rows to paid inference, with configurable request deadlines and per-process request throttling of 5 forecasts per minute per IP. That throttle is best-effort across multiple instances, not an account-wide spend guarantee; verify cloud quotas separately.

## Release and remaining decisions

Deploy an initial real prediction flow on Day 1. Keep secrets in hosted environment settings, serve the built frontend on the API origin, bind to the documented AppSail port, and use its Linux production server rather than Flask's development server. Verify access in a logged-out browser and test model authentication after token expiry. Record how model credentials will be supplied to the evaluator; do not publish an unauthenticated QuickML proxy merely to hide missing credential handoff.

Open external facts: exact submission cutoff and judge timeout/dependency/credential rules; dedicated project provisioning; QuickML availability and costs; actual endpoint schema/response/batch behavior; cloud fit behavior and initial accuracy; deployment limits; public production URL accessibility. Resolve these in the first implementation milestone. None prevents writing a complete proposed design, but unresolved access or endpoint facts prevent claiming a working product.

User decisions already supplied: solo execution, deadline on 28 October, no existing task model/project, choose the battery approach on project merit. Proposed choices still reviewable: one AppSail deployment, the stack, fixed input cleanup policy, battery defaults, and scope. No implementation begins until the user requests it after reviewing the plan.
