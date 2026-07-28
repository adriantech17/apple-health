# Apply Progress: Migrate Daily Summaries to Operational SQLite

## Status

- Mode: Strict TDD
- Artifact store: OpenSpec
- Assigned batch: Delivery Group 2, phases 4-6
- Cumulative completed tasks: 1.1-6.3
- Newly completed tasks: 4.1-6.3
- Next pending task: 7.1
- Delivery boundary: One PR-ready immutable metric-contract registry work unit
- Authored non-documentation change count: 875 additions plus deletions
- Auto-chain threshold: Not triggered; the approved phases 4-5 / phase 6 split remains unused

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

## Test Summary

- **Total tests written**: 80 collected pytest cases in `tests/test_metric_contracts.py`
- **Total tests passing**: 80
- **Layers used**: Unit (80), Integration (0), E2E (0)
- **Approval tests** (refactoring): None — no existing production behavior was refactored; refactor steps changed only the new module under its phase RED/GREEN coverage
- **Pure functions created**: 25 module-level pure functions

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

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `python3 -m pytest tests/test_metric_contracts.py -q` exited 0: 80 passed in 0.05s |
| Runtime harness | The same command exercised the required pure synthetic-row harness. No API, storage, filesystem, or external runtime boundary exists in this work unit. |
| Rollback boundary | Delete `src/metric_contracts.py` and `tests/test_metric_contracts.py`; revert only the phase 4-6 checkboxes and sequencing clarification in this change directory. Legacy storage and runtime paths remain untouched. |

## Deviations And Constraints

- `src/storage.py` generic conversions were not changed because this delivery group is an unused registry module and the approved scope explicitly preserves the current `HealthStore`, DuckDB, PyArrow, and Parquet paths.
- `duckdb` and `pyarrow` remain dependencies until phases 9-17, cutover, and fallback closure prove no operational path imports them.
- Final readiness still requires a WAL/checkpoint policy, representative Raspberry Pi 5/NVMe measurement, and proven isolated restore after corruption.
- Final delivery gates, review, commit, push, and PR creation remain parent-owned and were not run here.
