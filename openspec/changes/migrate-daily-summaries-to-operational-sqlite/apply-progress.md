# Apply Progress: Migrate Daily Summaries to Operational SQLite

## Status

- Mode: Strict TDD
- Artifact store: OpenSpec
- Assigned batch: Delivery Group 4, phases 9-10
- Cumulative completed tasks: 1.1-10.3
- Newly completed tasks: 9.1-10.3
- Next pending task: 11.1
- Delivery boundary: One PR-ready operational live-ingestion and indexed-read API work unit based on `aaf8adb`
- Recorded DG4 recovery snapshot budget: 952 non-documentation additions plus deletions; 1,052 total additions plus deletions
- Auto-chain threshold: Not triggered; this work unit remains below the approved 1,000-line limit
- Prior evidence: Delivery Groups 2-3 task, test, correction, and rollback evidence remains unchanged below

## Delivery Group 4 Result Contract

```yaml
status: success
executive_summary: >-
  Delivery Group 4 tasks 9.1-10.3 completed operational live ingestion,
  freshness, verified-candidate routing, and indexed SQLite reads while
  preserving the legacy fallback without dual-write.
artifacts:
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/tasks.md
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/apply-progress.md
next_recommended: sdd-verify
risks: Representative Raspberry Pi 5/NVMe timing remains a later readiness requirement.
skill_resolution: paths-injected
```

Budget evidence for the recovered DG4 snapshot is **952 non-documentation lines**
and **1,052 total lines** against parent `aaf8adb`.

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
| 9.1 | `tests/test_live_ingestion.py`, `tests/test_app.py` | Integration | `.venv` modified/dependent baseline exited 0 with 138 passed | `python -m pytest tests/test_live_ingestion.py -q` exited 2 during collection with `ModuleNotFoundError: src.live_ingestion`; supplemental conflicting-row RED exited 1 with 1 failed, 13 deselected | Shared phase-9 GREEN exited 0 with 13 passed; supplemental GREEN exited 0 with 1 passed, 13 deselected | Auth/body limits, exact source envelope, Madrid today/yesterday and DST, closure, all-invalid/degraded/duplicate/fault/freshness branches | Phase-9 refactor union exited 0 with 49 passed before the supplemental conflict cycle; final DG4 focused union exited 0 with 35 passed |
| 9.2 | `tests/test_live_ingestion.py`, `tests/test_app.py`, `tests/test_maintenance.py` | Integration | Existing app/maintenance/operational tests included in the 138-pass baseline | Shared phase-9 RED failed because no operational runtime or candidate-root route existed | Shared phase-9 GREEN exited 0 with 13 passed | Verified ready candidate versus building candidate, candidate-only persistence, legacy non-dual-write, five success fields and 400/401/413/422 paths | Response adapter and source/clock seams retained 35 passing DG4 focused cases |
| 9.3 | `src/live_ingestion.py`, `src/app.py` tests | Integration | Phase-9 GREEN: 13 passed | Shared phase-9 RED plus conflict supplemental RED define refactor behavior | Phase-9 behavior remained green after injected clock/provenance and adapter extraction | Privacy-safe stable codes, safe metric/date context, three receipt crash outcomes, and source metadata without payload values | `python -m pytest tests/test_live_ingestion.py tests/test_app.py tests/test_operational_store.py -q` exited 0 with 49 passed; final focused union exited 0 with 35 passed |
| 10.1 | `tests/test_operational_reads.py` | Integration | Phase-9 focused suite: 13 passed | `python -m pytest tests/test_operational_reads.py -q` exited 1 with 7 failed because status/current read methods did not exist; one setup date was corrected before GREEN because it was outside the specified live window | Shared phase-10 GREEN exited 0 with 7 passed | Inclusive ranges, both DST offsets, aligned corrections/details, tombstone and empty paths, bearer/identifier behavior, replay exclusion and no legacy engine access | Final phase-10 refactor command exited 0 with 7 passed in 3.24s |
| 10.2 | `tests/test_operational_reads.py`, `tests/test_app.py` | Integration | Phase-9 focused suite: 13 passed | Shared phase-10 RED produced missing-method failures on direct and HTTP reads | Shared phase-10 GREEN exited 0 with 7 passed | SQLite-only `metric_current` join, status meanings, root/schema selection, shared bearer and legacy fallback isolation | Indexed row adapter extraction retained 7 passing cases |
| 10.3 | `tests/test_operational_reads.py` | Integration/performance | Phase-10 GREEN: 7 passed | Shared phase-10 RED proved no operational read path existed; supplemental replay-status RED exited 1 with 1 failed, 6 deselected | Phase-10 GREEN and replay exclusion GREEN each exited 0 | Five years × 25 metrics = 45,650 current rows; plan asserted indexed `SEARCH c` and `SEARCH v` with no `SCAN`; read asserted under 2.0s | `python -m pytest tests/test_operational_reads.py -q --durations=3` exited 0 with 7 passed in 3.24s; slowest complete seed/plan/read case was 2.92s |
| DG4 recovery | `tests/test_operational_reads.py`, `tests/test_storage_schema.py` | Production-path integration | Existing focused files: 23 passed | Production selector failed: 1 failed, 7 deselected; schema identity selector failed: 1 failed, 14 deselected; both rejected `America/New_York` creation | Production selector: 1 passed, 7 deselected; schema selector: 1 passed, 14 deselected | Default Madrid, valid New York, invalid IANA, and persisted/configured mismatch paths | Shared IANA validator required no further refactor; focused files remained green: 23 passed |

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

## Delivery Group 4 Test Summary

- **Total tests written**: 22 collected pytest cases (14 live-ingestion and 8 operational-read cases)
- **Total tests passing**: 22 focused files; 36 DG4 focused with app compatibility; 181 modified/dependent modules; 194 repository-wide
- **Layers used**: Unit (0), Integration (21), Integration/performance (1), E2E (0)
- **Approval tests** (refactoring): One maintenance pointer-layout assertion was intentionally advanced from legacy-only to known legacy/candidate targets under the phase-9 candidate-selection RED
- **Pure functions created**: 5 source/date/completeness/response-row helpers
- **Synthetic runtime**: `TestClient`, bounded ASGI receive chunks, two private-like roots, real temporary SQLite/WAL and gzip artifacts, configured Madrid/New York clocks, injected transaction faults, and a 45,650-row plan/timing harness; no private dataset or external service

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
- [x] 9.1 RED: authentication/body bounds, exact live contract, Madrid closure/DST, degraded/all-invalid/duplicate/freshness/rollback fault cases
- [x] 9.2 GREEN: verified-candidate operational ingestion with preserved legacy route and five-field response
- [x] 9.3 REFACTOR: injected clock/provenance, isolated response adapter, deduplicated safe diagnostics
- [x] 10.1 RED: inclusive SQLite ranges, alignment, tombstones, empty/status/auth/no-legacy and performance cases
- [x] 10.2 GREEN: indexed `metric_current` values and status behind verified candidate selection
- [x] 10.3 REFACTOR: SQLite-only row adapter, replay exclusion, five-year/25-metric plan and timing evidence

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

## Delivery Group 4 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `.venv/bin/python -m pytest tests/test_live_ingestion.py tests/test_operational_reads.py tests/test_app.py -q` exited 0: 36 passed in 3.94s |
| Full modified-module command and exact result | `.venv/bin/python -m pytest tests/test_live_ingestion.py tests/test_operational_reads.py tests/test_app.py tests/test_maintenance.py tests/test_operational_store.py tests/test_storage_schema.py tests/test_metric_contracts.py tests/test_storage.py -q` exited 0: 181 passed in 5.75s |
| Runtime harness | The focused suites used `tmp_path`, synthetic JSON, candidate/legacy roots, `TestClient`, real SQLite/WAL and durable gzip artifacts, and injected clocks. The recovery regression initialized and validated `America/New_York` metadata at `2026-03-29T01:00:00Z`, proving March 27 complete/fresh, March 28 partial, and a one-day March 28 read; Madrid cases remain covered. |
| Rollback boundary | Revert `src/live_ingestion.py` and the DG4 changes in `src/app.py`, `src/maintenance.py`, and `src/operational_store.py`, plus DG4 tests/artifact marks. Before the first post-cutover receipt, reselect the legacy root; legacy `HealthStore`, metadata/raw/Parquet, DuckDB, and PyArrow remain intact and received no dual-write. |
| Review budget | The recovered DG4 snapshot contains 952 authored non-documentation additions plus deletions and 1,052 total additions plus deletions against parent `aaf8adb`, below the approved 1,000-line non-documentation ceiling; `.atl/` is excluded and untouched. |

## Delivery Group 4 Final Verification

| Command | Exact result |
|---|---|
| `.venv/bin/python -m pytest tests/test_live_ingestion.py tests/test_operational_reads.py tests/test_app.py -q` | Exit 0: 36 passed in 3.94s |
| `.venv/bin/python -m pytest tests/test_live_ingestion.py tests/test_operational_reads.py tests/test_app.py tests/test_maintenance.py tests/test_operational_store.py tests/test_storage_schema.py tests/test_metric_contracts.py tests/test_storage.py -q` | Exit 0: 181 passed in 5.75s |
| `.venv/bin/python -m pytest` | Exit 0: 194 passed in 4.37s |
| `.venv/bin/python scripts/check_repository.py` | Exit 0: repository audit OK, 138 tracked files inspected |
| `.venv/bin/python -m unittest scripts.test_check_repository` | Exit 0: 22 passed; expected synthetic negative-fixture diagnostics were emitted before final `OK` |
| `git diff --check` | Exit 0 with no output |
| Branch convention command | Not run by instruction: ledger, review, commit, issue, push, and PR delivery are parent-owned |

## Deviations And Constraints

- `src/storage.py` generic conversions remain unchanged for the pre-cutover/fallback `HealthStore`; the verified-candidate path bypasses that aggregation and reads only operational SQLite.
- `duckdb` and `pyarrow` remain dependencies until phases 9-17, cutover, and fallback closure prove no operational path imports them.
- Final readiness still requires a WAL/checkpoint policy, representative Raspberry Pi 5/NVMe measurement, and proven isolated restore after corruption.
- Final delivery gates, review, commit, push, and PR creation remain parent-owned and were not run here.
- Delivery Group 4 wires `src/operational_store.py` only when pointer selection resolves a schema-valid `ready` candidate; direct and legacy-pointer roots continue using `HealthStore` without dual-write.
- Batch staging/sealing remains phases 11-12. This group supplies and verifies the shared promoted-batch/live projection selector but does not implement the batch lifecycle early.
- The first bare `python -m pytest tests/test_storage_schema.py tests/test_metric_contracts.py -q` safety-net attempt exited 127 because `python` was not on the parent shell PATH. The repository-local `.venv` was already present; all recorded TDD and final commands then activated it explicitly without installing or changing dependencies.
- No production-data operation, schema rewrite, ADR 0004 edit, dashboard/deployment change, dual-write, interpolation, zero-fill, or version combination occurred.
- Yesterday becomes `complete` only when the exact `Default` source also supplies both existing automation and session identifiers; otherwise its accepted completeness remains `unknown`. Receipt time alone never proves closure.
- Rollback closure is persisted for the first live receipt only in `cutover` or `accepted` dataset phases; candidate-build receipts do not claim a post-cutover boundary.

## Native Correction `review-f8433933bd9c72db`

R3-001 RED: `python -m pytest tests/test_operational_reads.py -q -k configured_timezone` exited 1 with 1 failed and 7 deselected at the injected `2026-03-29T01:00:00Z` New York/Madrid date boundary; GREEN and no-refactor rerun exited 0 with 1 passed and 7 deselected.
Final verification: operational reads 8 passed; DG4 focused 36 passed; modified/dependent modules 181 passed; full suite 194 passed; repository audit OK (138 files); audit unittests 22 passed; `git diff --check` clean. Correction budget: **58 additions plus deletions** against the frozen candidate; tasks, phases 11+, `.atl/`, delivery, review, and runtime ledger unchanged.

## Ordinary-Review Correction `review-9781b9b5de8c74ba`
| Finding | RED | GREEN / REFACTOR |
|---|---|---|
| Replay-first/live-later | `python -m pytest tests/test_operational_store.py -k replay_does_not_suppress_later_live_authority`: 1 failed, 18 deselected | GREEN and no-refactor rerun: 1 passed, 21 deselected |
| Publication `OSError` privacy | `python -m pytest tests/test_operational_store.py -k publication_oserror_is_private_and_preserves_cleanup`: 3 failed, 19 deselected | GREEN and no-refactor rerun: 3 passed, 19 deselected; open/rename left no staging or orphan, post-rename sync left one quarantinable orphan |
Final verification: focused file 22 passed; modified modules 119 passed; full suite 172 passed; repository audit OK (135 files); audit unittests 22 passed; `git diff --check` clean.
Correction budget: 84 additions plus deletions against the frozen candidate; tasks, phases 9+, runtime ledger, and `.atl/` unchanged.

## Bounded Correction `review-dg4-timezone-recovery-20260729`

R4R3-001 runtime ordinal 10 RED: `.venv/bin/python -m pytest tests/test_live_ingestion.py -q -k 'madrid_route_converts_utc_instant or rejects_naive_and_invalid_timestamps'` exited 1: 1 failed, 2 passed, 14 deselected. GREEN / no-refactor rerun exited 0: 3 passed, 14 deselected.
Final verification: DG4 focused 39 passed; modified/dependent 184 passed; full suite 197 passed; repository audit OK (138 files); audit unittests 22 passed; `git diff --check` clean.
Correction budget: **47 non-documentation additions plus deletions**; final DG4 snapshot: **979 non-documentation lines** (946 additions, 33 deletions) against `aaf8adb`. Tasks, phases 11+, `.atl/`, review, ledger, delivery, and the Readability WARNING remain unchanged.
