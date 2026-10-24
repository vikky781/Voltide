# Voltide model card

Status: first cloud-only Ridge baseline trained and externally callable. Candidate selection, effective fitting-row count, chronological selection/locked-test accuracy, and final-model freeze remain pending. Local preparation below performs no fitting.

## Baseline evidence, 24 October 2026

- Catalyst project 92462000000018001, organization 60093105197, India Development.
- Pipeline Voltide_Linear_v1 (12429000000002023), model 12429000000002026, V1; cloud execution Success / model Ready.
- RidgeRegression: alpha 1, fit intercept true, tolerance 0.0001, positive false, solver Auto, explainer false. Automatic retraining disabled. Input is the 2400-row development partition only.
- QuickML internal reported metrics: RMSE 26.9927 kW, MAE 22.3915 kW, MSE 728.6062, R-squared 0.515, MAPE 15.6678%, RMSLE 0.1822. These are **platform-internal metrics**, not the planned chronological holdout evaluation. Internal split and effective fitted-row count still need verification.
- Endpoint Voltide_Baseline_v1 (12429000000002043), V1. Direct authenticated HTTP 200 verifies external publication even though a console status label appeared stale after publishing.
- Request: `{"data": [feature_record, ...]}`. One object is also accepted. Response: `{"result": [number, ...], "pipeLineType": "prediction", "status": "success"}`. Sanitized actual samples are in tests/fixtures/quickml/.
- Live single-row prediction request: 0.651 seconds; live 24-row request: 0.552 seconds, excluding OAuth refresh. Shared client deliberately caps batches at the verified size 24.
- Unchanged starter evaluator: 1000 real predictions, passed, 16.998 seconds including startup/authentication. Sample rows are unlabeled; this verifies integration, not accuracy. Judge timeout remains unknown.

The configured model version is an explicit deployment label; a future endpoint model change must update configuration and repeat contract/accuracy checks.

## Feature contract v1

The same `energy.features.build_features` transform prepares cloud CSVs and future inference inputs. Raw target demand and raw timestamp strings are excluded from model features.

| Feature | Definition |
| --- | --- |
| ambient_temp_c | Supplied temperature, Celsius. |
| humidity_pct | Supplied humidity, 0-100 percent. |
| solar_irradiance_wm2 | Supplied nonnegative irradiance, W/m2. |
| hour | Dataset-local hour, 0-23. |
| hour_sin / hour_cos | Sine/cosine of 2 pi times hour / 24. |
| weekday | Monday=0 through Sunday=6. |
| month | Calendar month, 1-12. |
| is_weekend | 1 for Saturday/Sunday; otherwise 0. |
| cooling_degree_c | Maximum of zero and ambient temperature minus 24 C. |

Missing weather can be carried forward for a single hour only from the immediately preceding unambiguous, originally valid source reading. Each correction records source row, field, preceding row, and replacement. No averages are learned locally and no future readings are used.

## Chronological evaluation partitions

Source SHA-256: a6bd0c612936c79caa67c07f278731c51be9b2eb83a5951e03fb14b82ee3a122.

| Partition | Source rows | First timestamp | Last timestamp |
| --- | --- | --- | --- |
| Development | 1-2400 | 2014-12-31 23:00:00 | 2015-04-10 22:00:00 |
| Selection | 2401-3200 | 2015-04-10 23:00:00 | 2015-05-14 06:00:00 |
| Locked test | 3201-4000 | 2015-05-14 07:00:00 | 2015-06-16 14:00:00 |

Refit uses rows 1-3200 only after candidate selection. Final cloud fitting can use all 4000 only after the locked-test result is recorded. QuickML's effective internal training split must be recorded; an upload count alone is not proof of fitted-row count.

## Required cloud evidence before completion

- Project, pipeline, model, model version, endpoint, feature version, and actual fitting configuration.
- Sanitized real endpoint request and response, authentication context, batching behavior, and observed latency.
- Chronological selection and locked-test RMSE/MAE with exact prediction alignment and effective fitted-row usage.
- Successful 1-row, 24-row, and 1000-row inference using the final shared client.

The supplied sample_test_input.csv has no labels and cannot establish accuracy. No local model, learned calibration, or fallback formula qualifies as the submitted QuickML model.
