# Voltide model card

Status: no model trained or endpoint published yet. No accuracy or performance metric is available. Local preparation below performs no fitting.

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
