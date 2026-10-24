# Voltide model card

Status: three cloud-only candidates were compared on the same chronological selection set. Gradient boosting V1 was selected; a separate 3,200-row cloud refit scored RMSE 13.2666 kW on the single locked 800-row test. The earlier selected candidate still provisionally serves the hosted application. The 4,000-row final cloud fit, endpoint verification, and effective fitted-row count remain pending. Local preparation below performs no fitting.

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

## Chronological selection result: baseline V1

The first 2,400-row cloud candidate was evaluated remotely on source rows 2401-3200 (800 rows), with exact timestamp/order alignment. Source hash matches the preparation manifest. Predictions SHA-256: a4c9ac2795bf7811ff31ec692a267a3fdcb8cc9934b50976445112848fb0f830. No fitting or calibration occurred during scoring.

| Subset | Count | RMSE kW | MAE kW | Mean prediction minus actual kW |
| --- | ---: | ---: | ---: | ---: |
| All selection rows | 800 | 32.0430 | 25.5567 | -11.1916 |
| Temperature >=30 C | 95 | 35.8169 | 30.5442 | -30.2639 |
| Actual demand >=200 kW | 206 | 43.8032 | 41.0862 | -41.0862 |

This baseline substantially underpredicts high demand. It remains a rollback integration baseline; verified cloud fitting-row behavior remains open, and the locked final 800 have not been scored.

Reproduce from the repository root with the private endpoint configuration loaded:

```powershell
.venv\Scripts\python.exe predict.py --input artifacts/quickml/selection_inputs.csv --output artifacts/selection-linear-v1.csv
.venv\Scripts\python.exe -m tools.score_predictions --partition selection --predictions artifacts/selection-linear-v1.csv --model-version Voltide_Linear_v1:V1 --output artifacts/selection-linear-v1-metrics.json
```

The scorer requires a new output path and never overwrites an evaluation record. Hot weather is defined in advance as >=30 C; the peak subset uses actual demand >=200 kW. Empty subsets return null metrics with count zero. Locked-test discipline remains an explicit experiment protocol, not a security control enforced by filenames.

## Gradient-boosting selection candidate V1

Cloud pipeline Voltide_Gradient_v1 (12429000000002051), model 12429000000002054, V1, completed successfully on the same development dataset V1. Stage: GB Regression, squared-error loss, learning rate 0.1, 100 estimators, Friedman-MSE criterion, subsample 1, max depth 3, min split 2, min leaf 5, min weight fraction 0, max features None, max leaf nodes unset, min impurity 0, init None, warm start false, tolerance 0.01831563888, explainer false. Automatic retraining is disabled. Internal RMSE 9.0178 kW and MAE 7.2381 kW are supplementary only. Endpoint Voltide_Gradient_v1 (12429000000002073) returned 800 actual selection predictions; its private key is ignored by Git. The hosted app now serves this candidate provisionally.

| Subset | Count | RMSE kW | MAE kW | Mean prediction minus actual kW |
| --- | ---: | ---: | ---: | ---: |
| All selection rows | 800 | 14.1411 | 10.3634 | -4.3748 |
| Temperature >=30 C | 95 | 30.2140 | 27.5676 | -27.5361 |
| Actual demand >=200 kW | 206 | 22.5716 | 18.0408 | -17.2787 |

Predictions SHA-256: df8d14b8bc5433378bba55590d52583790e5f3e171bbceced17317931c58b0ed. The overall improvement did not eliminate hot-weather underprediction. The separate refit and locked result appear below; effective fitting-row evidence and final cloud fitting remain pending.

The [official release notes](https://docs.catalyst.zoho.com/en/release-notes/all/?service=quickml) state that the train/test split field was removed and a default 80/20 split is used. The visible stage configuration and execution statistics do not expose effective fitting-row identities or final refitting behavior. Therefore 2,400 uploaded development rows must not be represented as 2,400 verified fitted rows; 1,920/480 is the expected default split, not yet a runtime-confirmed row count.

## Random-forest selection candidate V1 and selection freeze

Cloud pipeline Voltide_Forest_v1 (12429000000002079), model 12429000000002082, V1, and endpoint Voltide_Forest_v1 (12429000000002103) were trained/published in the same Catalyst Development project on the unchanged 2,400-row development dataset. Stage configuration: squared-error criterion, 150 estimators, max depth 6, minimum split 2, minimum leaf 3, minimum weight fraction 0, max features 1.0, bootstrap true, out-of-bag false, warm-start false, explainer false. No automatic retraining. The exact 800-row chronological selection set was inferred remotely. Predictions SHA-256: dbe1befc08c57e01512e62d329949111329a872f074b225d39d3f082e4005129.

| Candidate | Selection RMSE kW | MAE kW | Hot (>=30 C) RMSE kW | Actual >=200 kW RMSE kW |
| --- | ---: | ---: | ---: | ---: |
| Ridge V1 | 32.0430 | 25.5567 | 35.8169 | 43.8032 |
| Gradient boosting V1 | **14.1411** | **10.3634** | **30.2140** | **22.5716** |
| Random forest V1 | 30.1347 | 25.2132 | 52.5274 | 47.3836 |

Selection decision, frozen before viewing locked-test labels or predictions: choose gradient boosting V1. The forest's full selection bias is -10.8485 kW, hot-weather bias -50.0571 kW, and actual >=200 kW bias -44.6649 kW. Candidate comparison uses the same timestamps, source hash, and feature version. Next action: new cloud model trained from first 3,200 source rows, followed by one score on rows 3,201-4,000. The first 3,200 uploaded rows cannot automatically be equated with fitted rows under QuickML's default internal split; that limitation must be reported.

## Provisional hosted candidate

The selected Gradient V1 endpoint passed real 24-row and 1,000-row CLI inference and the unchanged starter evaluator before its provisional deployment. Public health returned HTTP 200 with `model_configured=true`; a separate public `/api/forecast` request returned HTTP 200, exactly 24 real hourly predictions, `model_version=Voltide_Gradient_v1:V1`, and `saved=true`. A Ridge run created before that redeployment remained in the same browser session's history and reopened with its original 24 hourly decisions. This candidate was replaced by the final endpoint after the locked result was frozen. Its private configuration is retained locally for rollback; no endpoint key is committed.

## Cloud refit execution

The user imported `artifacts/quickml/refit.csv` through the signed-in Catalyst QuickML console as `Voltide_Refit_v1`, dataset ID 12429000000003055, version V1. QuickML reports 3,200 records, 11 columns (the ten feature-contract fields and `target_demand_kw`), 100% valid values, and zero missing values. The separate prediction pipeline `Voltide_GB_Refit_v1` (12429000000002118), model 12429000000002121, uses this dataset V1 and target `target_demand_kw`; automatic retraining is disabled. Its single GB Regression stage uses the frozen candidate's configuration: squared-error loss, learning rate 0.1, 100 estimators, Friedman-MSE, subsample 1, depth 3, minimum split 2, minimum leaf 5, and the other settings listed above. Cloud execution succeeded and model V1 is Ready. Internal QuickML RMSE 8.4407 kW and MAE 6.7329 kW are supplementary platform metrics, not locked chronological accuracy. Endpoint `Voltide_GB_Refit_v1` (12429000000002147) is published; its key is ignored by Git. Actual 1-row and 24-row external calls returned finite predictions with exact timestamp order and columns. The first 3,200 uploaded rows still cannot be equated with a verified effective fitted-row count under QuickML's default internal split. Locked-test labels and predictions were untouched at this checkpoint.

## Single locked chronological test

After the gradient candidate was selected on rows 2401-3200 and the new refit endpoint passed 1/24-row external smoke tests, the first and only locked inference used source rows 3201-4000. The shared CLI produced exactly 800 real remote QuickML predictions. The scorer then required exact timestamp/order alignment against the original immutable source before reading the locked labels. Source SHA-256 remained `a6bd0c612936c79caa67c07f278731c51be9b2eb83a5951e03fb14b82ee3a122`; prediction CSV SHA-256 is `7a8a81b3db245b5c382e151435d1e5e011219a937c188856c576ad4e43e87811`. Model version was `Voltide_GB_Refit_v1:V1`.

| Subset | Count | RMSE kW | MAE kW | Mean prediction minus actual kW |
| --- | ---: | ---: | ---: | ---: |
| All locked rows | 800 | 13.2666 | 10.1386 | -2.0888 |
| Temperature >=30 C | 347 | 15.2119 | 11.9120 | -7.8795 |
| Actual demand >=200 kW | 448 | 14.0727 | 10.8607 | -7.2106 |

This is one held-out estimate for the frozen candidate/refit workflow, not an estimate for a model retrained on all 4,000 source rows. High-load and hot-weather bias remain negative; the battery/controller rules must not treat the forecast as a guaranteed upper bound. QuickML does not expose exact fitted-row identities or count in the inspected execution UI, so the 3,200-row import count is reported separately from verified fitted rows.

## Final cloud model after the locked result

Only after the single locked score was frozen, the user imported `artifacts/quickml/final.csv` as `Voltide_Final_v1`, dataset 12429000000002154 V1. QuickML reports 4,000 records, the ten feature fields plus `target_demand_kw`, 100% valid values, and no missing values. Prediction pipeline `Voltide_GB_Final_v1` (12429000000002163) and model 12429000000002166 V1 use the same frozen GB Regression stage and `target_demand_kw` target; automatic retraining is disabled. Cloud execution succeeded and the model is Ready. Its internal QuickML RMSE 9.0466 kW and MAE 7.2113 kW are platform metrics, **not** a new locked score or evidence of accuracy for the final 4,000-row model. QuickML's visible execution UI still does not expose exact fitted-row identities/count; 4,000 is the imported count, not a verified fitted count.

Endpoint `Voltide_GB_Final_v1` (12429000000002184) is Published with model version `Voltide_GB_Final_v1:V1`. Its key is retained only in ignored `artifacts/final-endpoint-private.json`. The shared CLI made real remote 1-, 24-, and 1,000-row calls; outputs have exactly `timestamp,target_demand_kw`, finite values, and timestamp order matching each input. The unchanged starter `test_eval.py` also passed all 1,000 sample rows with this final endpoint. The sample has no demand labels, so none of these contract tests is an accuracy score. The single locked result above is not rerun against the final model.

After the private AppSail configuration switched to this endpoint and deployment succeeded, public health returned HTTP 200 with the model and history configured. A fresh hosted request returned HTTP 200, 24 hourly final-model predictions, `model_version=Voltide_GB_Final_v1:V1`, and `saved=true`. Its run appears in owner history and reloads; another session receives 404. A previously saved run still reloads after the deployment. This proves hosted integration and persistence, not final-model accuracy on new labels.
