# Voltide implementation progress

Plan: superpowers/plans/2026-10-24-microgrid-implementation-plan.md

## 24 October 2026

- Implementation authorized. Branch codex/implementation created from 6eab8e3.
- Task 1 discovery milestone: connector access, local tools, repository scope, and original self-test verified; details in operations.md. Task 1 remains incomplete pending console login, dedicated project/QuickML provisioning, and evaluator rules.
- Task 2: complete. Validation, correction provenance, explicit 24-hour windows, feature contract v1, and deterministic cloud data preparation are implemented. RED: 29 tests failed because the modules were absent. GREEN: all 29 tests pass; real preparation produced the five exact partitions and original hashes are unchanged. Verification: python -m pytest -q; python -m tools.prepare_quickml_data --output artifacts/quickml.
- Task 3 baseline milestone: cloud Ridge model V1 is Ready, endpoint published and directly verified using prediction-only OAuth. Actual one/24-row request and response fixtures captured. Internal cloud metrics recorded in model-card.md; effective internal fitted-row usage is still unresolved.
- Task 4: shared client, regional config, OAuth refresh, bounded transient retries, strict response checks, sequential 24-row chunks, evaluator wrapper, and atomic CSV CLI implemented. Formula fallback removed. RED: 30 new tests failed for missing behavior; GREEN: all 103 tests pass. Unchanged starter evaluator passed with 1000 actual remote predictions in 16.998 seconds. Full deployment and candidate scoring remain separate gates.
- Task 5: complete. Exact demand/time rules, independent critical flags, validated battery assumptions, energy limits/reserve/efficiency, explicit shortfalls, and shared forecast composition are implemented. RED: 31 new tests failed for absent behavior. GREEN: all 60 tests pass. Network boundaries are fixtures in composition tests; no actual model result is claimed.
- Task 6a: complete as an offline API milestone. Health, source validation, original-source forecast submission, error mapping, upload limits, and per-process throttling pass 13 new tests (73 total). Unconfigured prediction returns 503; network results in API tests are isolated fixtures. Task 6b persistence and real-client wiring remain pending.
- Task 6a follow-up: create_configured_app wires the shared real client; explicit unconfigured create_app remains available for isolated API tests. No production fixture or alternate demand calculation is introduced.
- Live follow-up verification: CLI wrote exactly 1000 aligned timestamp/demand rows in 15.583 seconds; real Flask /api/forecast returned 24 aligned results in 1.426 seconds, with SIMULATED battery provenance and saved=false. These are local application/remote inference checks, not a public deployment claim.
- Tasks 7-10: pending.

## Pre-flight decisions

- Tasks 2 -> 3/4: feature contract v1 is the shared authority for prepared cloud data and inference inputs; no local fitted transform.
- Tasks 2 -> 5/6/8: original source and correction provenance survive validation; only a selected valid 24-hour window reaches web inference. Evaluator inference preserves arbitrary input count/order.
- Tasks 3 -> 4/9: live endpoint samples and effective cloud fitting configuration are required evidence, not placeholders.
- Tasks 5 -> 6/8: use one set of controller/battery results; the frontend never recomputes switching rules.
- Tasks 6 -> 7/8: the initial deployed response uses the final schema with saved=false until storage is verified.
- Ruling: work in the user's chosen checkout on codex/implementation rather than moving files to a new worktree. This preserves the app's current writable workspace and keeps main unchanged; the cost is one active checkout rather than simultaneous branch directories.
- Ruling: use Windows PowerShell equivalents for plan bookkeeping when appropriate; the Bash task scripts are available through Git Bash. The tracked progress file supplements the scratch ledger so verification and blocked status survive a push.
- Task 2 ruling: credential-specific runtime configuration is deferred to Task 4's verified endpoint contract; .env.example records intended names now. Cost if wrong: credentials still require validation before any real inference; Task 4 remains an explicit gate.
- The user has no organizer guide beyond PROBLEM_STATEMENT.md. Exact cutoff, judge timeout, and credential handoff stay unknown rather than generating additional repeated requests.
- Task 5 interface clarification: hourly results include storage_shortfall and alerts (CRITICAL_OVERLOAD / STORAGE_SHORTFALL), alongside the specified controller and battery fields. These directly expose the required alerts; no switching threshold or requested mode changes.
- A project-local .venv is installed with application/test dependencies. The registered Python 3.13 launcher points to a missing executable, so the verified local environment is Python 3.14. Hosted Python 3.12 compatibility remains a release check; no machine-wide Python installation was changed.
