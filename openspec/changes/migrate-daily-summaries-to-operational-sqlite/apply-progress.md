# Apply Progress: Migrate Daily Summaries to Operational SQLite

## Status

- Mode: Strict TDD
- Artifact store: OpenSpec
- Assigned batch: Delivery Group 3, phases 7-8
- Cumulative completed tasks: 1.1-8.3
- Newly completed tasks: 7.1-8.3
- Next pending task: 9.1
- Delivery boundary: One PR-ready operational persistence, authority, and current-projection work unit
- Authored non-documentation change count: 925 additions plus deletions
- Auto-chain threshold: Not triggered; this work unit remains below the approved 1,000-line limit
- Prior evidence: Delivery Group 2 task, test, and rollback evidence remains unchanged below

## TDD Cycle Evidence

The three tasks in each phase are the named RED, GREEN, and REFACTOR checkpoints
of one shared phase cycle. The command evidence is repeated per task so every
completed checkbox remains independently machine-routable without inventing an
execution that did not occur.

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 4.1 | `tests/test_metric_contracts.py` | Unit | N/A (new files) | Shared phase-4 RED: `python3 -m pytest tests/test_metric_contracts.py -q` failed during collection with `ModuleNotFoundError: src.metric_contracts` | Shared phase-4 GREEN: same command; 24 passed | Valid/invalid totals, all declared units, Decimal parsing, and canonical JSON | Shared phase-4 REFACTOR: same command after shared-unit refactor; 24 passed |
| 4.2 | `tests/test_metric_contracts.py` | Unit | N/A (new files) | Shared phase-4 RED: `python3 -m pytest tests/test_metric_contracts.py -q` failed during collection with `ModuleNotFoundError: src.metric_contracts` | Shared phase-4 GREEN: same command; 24 passed | Energy/distance conversion aliases and incompatible-unit paths forced generalized conversion | Shared phase-4 REFACTOR: same command after shared-unit refactor; 24 passed |
| 4.3 | `tests/test_metric_contracts.py` | Unit | N/A (new files); 24-case phase baseline before refactor | Shared phase-4 RED: `python3 -m pytest tests/test_metric_contracts.py -q` failed during collection with `ModuleNotFoundError: src.metric_contracts` | Shared phase-4 GREEN: same command; 24 passed | Unknown metric, unknown unit, incompatible unit, invalid shape, and invalid numeric paths | Shared phase-4 REFACTOR: same command after shared-unit refactor; 24 passed |
| 5.1 | `tests/test_metric_contracts.py` | Unit | 24 phase-4 cases passing | Shared phase-5 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase5`; 33 failed, 24 deselected because scalar contracts were absent | Shared phase-5 GREEN: same command; 33 passed, 24 deselected | Accepted aliases, boundaries, malformed values, booleans, and non-finite values | Shared phase-5 REFACTOR: full focused file after shared factory refactor; 57 passed |
| 5.2 | `tests/test_metric_contracts.py` | Unit | 24 phase-4 cases passing | Shared phase-5 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase5`; 33 failed, 24 deselected because scalar contracts were absent | Shared phase-5 GREEN: same command; 33 passed, 24 deselected | Multiple source units and canonical outputs covered all 12 indivisible scalar contracts | Shared phase-5 REFACTOR: full focused file after shared factory refactor; 57 passed |
| 5.3 | `tests/test_metric_contracts.py` | Unit | 24 phase-4 cases passing; 33 phase-5 cases green before refactor | Shared phase-5 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase5`; 33 failed, 24 deselected because scalar contracts were absent | Shared phase-5 GREEN: same command; 33 passed, 24 deselected | Oxygen-only fractional rescaling and gait-percentage no-rescaling counterexample | Shared phase-5 REFACTOR: full focused file after shared factory refactor; 57 passed |
| 6.1 | `tests/test_metric_contracts.py` | Unit | 57 phase-4/5 cases passing | Shared phase-6 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase6`; 21 failed, 1 passed, 57 deselected because four contracts were absent | Shared phase-6 GREEN: same command; 22 passed, 57 deselected | Heart extrema, sleep consistency/tolerance, sparse absence, and unit alignment | Shared phase-6 REFACTOR: full focused file after exact-duration and field-selection refactors; 80 passed |
| 6.2 | `tests/test_metric_contracts.py` | Unit | 57 phase-4/5 cases passing | Shared phase-6 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase6`; 21 failed, 1 passed, 57 deselected because four contracts were absent | Shared phase-6 GREEN: same command; 22 passed, 57 deselected | Additional identity-form and optional sleep no-fill RED: focused command produced 2 failed, 78 deselected, then 2 passed | Shared phase-6 REFACTOR: full focused file after exact-duration and field-selection refactors; 80 passed |
| 6.3 | `tests/test_metric_contracts.py` | Unit | 57 phase-4/5 cases passing; 22 phase-6 cases green before refactor | Shared phase-6 RED: `python3 -m pytest tests/test_metric_contracts.py -q -k phase6`; 21 failed, 1 passed, 57 deselected because four contracts were absent | Shared phase-6 GREEN: same command; 22 passed, 57 deselected | All 25 contracts exercised with valid shape, accepted unit, incompatible unit, plus fingerprint context changes | Shared phase-6 REFACTOR: full focused file after exact-duration and field-selection refactors; 80 passed |
| 7.1 | `tests/test_operational_store.py` | Integration | N/A (new files); schema/registry safety net: `.venv/bin/python -m pytest tests/test_storage_schema.py tests/test_metric_contracts.py -q` exited 0 with 97 passed | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q` exited 2 during collection with `ModuleNotFoundError: src.operational_store` | Shared phase-7 GREEN command exited 0 with 9 passed | Owner/hash reuse, separate receipts, both rejected retention paths, five artifact/transaction faults, corrupt target, quarantine, diagnostics, and FULL durability | Shared phase-7 REFACTOR command with `--durations=5` exited 0 with 9 passed in 0.12s |
| 7.2 | `tests/test_operational_store.py` | Integration | N/A (new production module) | Shared phase-7 RED exited 2 because the operational store did not exist | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q` exited 0 with 9 passed | Fault points prove stage cleanup versus published-orphan quarantine and SQLite atomicity | Same focused command after private artifact-verification extraction exited 0 with 9 passed |
| 7.3 | `tests/test_operational_store.py` | Integration | Phase-7 GREEN: 9 passed | Shared phase-7 RED retained as the behavior boundary | Phase-7 behavior remained green: 9 passed | Existing and new target paths, retained and non-retained rejections, and pre/post-publication failures | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q --durations=5` exited 0 with 9 passed in 0.12s; slowest synthetic artifact case was 0.02s |
| 8.1 | `tests/test_operational_store.py` | Integration | Phase-7 refactor safety net: 9 passed | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q` exited 2 during collection because `VersionCandidate` did not exist; explicit-tombstone RED exited 1 with 1 failed, 16 deselected; rejected-version RED exited 1 with 1 failed, 17 deselected and exposed a foreign-key failure before input rejection | Shared phase-8 GREEN first exited 0 with 16 passed; supplemental greens and final focused run exited 0 with 18 passed | Unchanged retry, completeness correction, complete non-regression, rejected/replay/conflict exclusion, three rollback points, one promoted batch tombstone, unpromoted/pending exclusion | Final focused suite after writer/quarantine lock refactor exited 0 with 18 passed in 0.21s |
| 8.2 | `tests/test_operational_store.py` | Integration | Phase-7 refactor safety net: 9 passed | Shared phase-8 RED exited 2 because immutable version input was absent | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q` exited 0 with 16 passed | Four live sequences, no-op retry, rejected/replay/conflict exclusion, rollback, value correction, and batch tombstone paths | Shared selector extraction and lock narrowing retained 18 passing cases |
| 8.3 | `tests/test_operational_store.py`, `tests/test_storage_schema.py` | Integration | Phase-8 GREEN: 16 passed | Shared phase-8 RED plus supplemental tombstone/rejected-version REDs define all refactor behavior | Final focused operational-store command exited 0 with 18 passed | Live and promoted-batch candidates use one selector; current points to one immutable value or tombstone without field mixing | `python -m pytest tests/test_operational_store.py -q` exited 0 with 18 passed; `python -m pytest tests/test_storage_schema.py -q -k query_plans` exited 0 with 1 passed, 14 deselected |

## Delivery Group 2 Test Summary

- **Total tests written**: 80 collected pytest cases in `tests/test_metric_contracts.py`
- **Total tests passing**: 80
- **Layers used**: Unit (80), Integration (0), E2E (0)
- **Approval tests** (refactoring): None — no existing production behavior was refactored; refactor steps changed only the new module under its phase RED/GREEN coverage
- **Pure functions created**: 25 module-level pure functions

## Delivery Group 3 Test Summary

- **Total tests written**: 18 collected pytest cases in `tests/test_operational_store.py`
- **Total tests passing**: 18 focused; 115 across all modified/dependent modules; 168 repository-wide
- **Layers used**: Unit (0), Integration (18), E2E (0)
- **Approval tests** (refactoring): None — the work unit added an unused operational module and refactored it only under its phase RED/GREEN coverage
- **Pure functions created**: 4 validation/selection/encoding helpers
- **Synthetic runtime**: Real temporary SQLite, gzip, staging, fsync, rename, directory sync, writer locks, injected clock, and injected transaction/artifact faults; no private dataset or external service

## Completed Tasks

- [x] 4.1 RED: totals, units, Decimal, canonical JSON, and rejection fixtures
- [x] 4.2 GREEN: immutable total contracts and canonical conversions
- [x] 4.3 REFACTOR: shared validators/converters and unknown-metric rejection
- [x] 5.1 RED: scalar unit, boundary, shape, boolean, and non-finite fixtures
- [x] 5.2 GREEN: 12 indivisible scalar contracts
- [x] 5.3 REFACTOR: dimensionally equivalent helpers; legacy storage unchanged by scope
- [x] 6.1 RED: composite ordering, sleep consistency/tolerance, sparse absence, and units
- [x] 6.2 GREEN: aligned heart-rate/sleep details and sparse observations
- [x] 6.3 REFACTOR: stable error codes, deterministic context fingerprints, and 25-metric proof
- [x] 7.1 RED: owner/hash idempotency, receipt separation, retention, artifact faults, rollback, and quarantine
- [x] 7.2 GREEN: durable content-addressed raw and atomic receipt/error/artifact persistence
- [x] 7.3 REFACTOR: narrow artifact/transaction seams, privacy-safe failures, and synthetic timing
- [x] 8.1 RED: retry, completeness, authority, projection, conflict, batch, tombstone, and rollback failures
- [x] 8.2 GREEN: immutable versions, monotonic authority, and deterministic transactional current selection
- [x] 8.3 REFACTOR: shared live/seal projection selector and indexed current-range plan inspection

## Delivery Group 2 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `python3 -m pytest tests/test_metric_contracts.py -q` exited 0: 80 passed in 0.05s |
| Runtime harness | The same command exercised the required pure synthetic-row harness. No API, storage, filesystem, or external runtime boundary exists in this work unit. |
| Rollback boundary | Delete `src/metric_contracts.py` and `tests/test_metric_contracts.py`; revert only the phase 4-6 checkboxes and sequencing clarification in this change directory. Legacy storage and runtime paths remain untouched. |

## Delivery Group 3 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `source .venv/bin/activate && python -m pytest tests/test_operational_store.py -q` exited 0: 18 passed in 0.21s |
| Full modified-module command and exact result | `source .venv/bin/activate && python -m pytest tests/test_storage_schema.py tests/test_metric_contracts.py tests/test_operational_store.py -q` exited 0: 115 passed |
| Runtime harness | The focused command exercised a faulting `tmp_path` filesystem plus real SQLite/WAL with `synchronous=FULL`, deterministic synthetic payloads, an injected UTC receipt instant, and fault hooks after stage write, stage sync, rename, parent sync, authority, versions, projection, and before commit. It exited 0 with 18 passed. |
| Rollback boundary | Delete unused `src/operational_store.py` and `tests/test_operational_store.py`; revert only task checkboxes 7.1-8.3 and this appended Delivery Group 3 evidence. `HealthStore`, legacy metadata/raw/Parquet, DuckDB, PyArrow, app routes, and selected legacy root remain unchanged. |
| Review budget | 925 authored non-documentation additions plus deletions against `origin/main`, below the approved 1,000-line ceiling. New files were marked intent-to-add before counting. |

## Delivery Group 3 Final Verification

| Command | Exact result |
|---|---|
| `source .venv/bin/activate && python -m pytest tests/test_storage_schema.py tests/test_metric_contracts.py tests/test_operational_store.py -q` | Exit 0: 115 passed |
| `source .venv/bin/activate && python -m pytest` | Exit 0: 168 passed |
| `source .venv/bin/activate && python scripts/check_repository.py` | Exit 0: repository audit OK, 135 tracked files inspected |
| `source .venv/bin/activate && python -m unittest scripts.test_check_repository` | Exit 0: 22 passed; expected synthetic negative-fixture diagnostics were emitted before final `OK` |
| `git diff --check` | Exit 0 with no output |
| Branch convention command | Pending by instruction: commit, title, and parent delivery are not executor-owned |

## Deviations And Constraints

- `src/storage.py` generic conversions were not changed because this delivery group is an unused registry module and the approved scope explicitly preserves the current `HealthStore`, DuckDB, PyArrow, and Parquet paths.
- `duckdb` and `pyarrow` remain dependencies until phases 9-17, cutover, and fallback closure prove no operational path imports them.
- Final readiness still requires a WAL/checkpoint policy, representative Raspberry Pi 5/NVMe measurement, and proven isolated restore after corruption.
- Final delivery gates, review, commit, push, and PR creation remain parent-owned and were not run here.
- Delivery Group 3 adds `src/operational_store.py` as an unused focused storage module; it does not wire `HealthStore` or HTTP routes, which remain phases 9-10.
- Batch staging/sealing remains phases 11-12. This group supplies and verifies the shared promoted-batch/live projection selector but does not implement the batch lifecycle early.
- The first bare `python -m pytest tests/test_storage_schema.py tests/test_metric_contracts.py -q` safety-net attempt exited 127 because `python` was not on the parent shell PATH. The repository-local `.venv` was already present; all recorded TDD and final commands then activated it explicitly without installing or changing dependencies.
- No production-data operation, schema rewrite, ADR 0004 edit, dashboard/deployment change, dual-write, interpolation, zero-fill, or version combination occurred.

## Ordinary-Review Correction `review-9781b9b5de8c74ba`
| Finding | RED | GREEN / REFACTOR |
|---|---|---|
| Replay-first/live-later | `python -m pytest tests/test_operational_store.py -k replay_does_not_suppress_later_live_authority`: 1 failed, 18 deselected | GREEN and no-refactor rerun: 1 passed, 21 deselected |
| Publication `OSError` privacy | `python -m pytest tests/test_operational_store.py -k publication_oserror_is_private_and_preserves_cleanup`: 3 failed, 19 deselected | GREEN and no-refactor rerun: 3 passed, 19 deselected; open/rename left no staging or orphan, post-rename sync left one quarantinable orphan |
Final verification: focused file 22 passed; modified modules 119 passed; full suite 172 passed; repository audit OK (135 files); audit unittests 22 passed; `git diff --check` clean.
Correction budget: 84 additions plus deletions against the frozen candidate; tasks, phases 9+, runtime ledger, and `.atl/` unchanged.
