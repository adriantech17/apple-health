# Apply Progress: Migrate Daily Summaries to Operational SQLite

## Status

- Mode: Strict TDD
- Artifact store: OpenSpec
- Assigned batch: Phase 11, Stage Reconciliation (stacked slice 1 targeting `main`)
- Cumulative completed tasks: 1.1-11.3
- Newly completed tasks: 11.1-11.3
- Next pending task: 12.1
- Delivery boundary: Manifest-bound staging, pending validation, private CLI, and repository policy only; no seal or authority promotion
- Phase 11 review budget after the automatic gatekeeper retry: 997 non-documentation additions plus deletions; 1,115 total additions plus deletions against `387a66f1d2ddd3b249b19f4a8f2de9211760c142`
- Auto-chain decision: Phase 11 is the first of two separately reviewable stacked slices; Phase 12 remains dependent and unimplemented
- Prior evidence: Delivery Groups 2-4 task, test, correction, and rollback evidence remains unchanged below

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

## Phase 11 Result Contract

```yaml
status: success
executive_summary: >-
  Phase 11 tasks 11.1-11.3 added canonical manifest-bound reconciliation
  staging, durable source artifacts, pending-only versions and tombstones,
  exact-hash resume, a private CLI adapter, and tracked-artifact policy guards.
artifacts:
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/tasks.md
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/apply-progress.md
next_recommended: sdd-apply task 12.1 as a dependent stacked slice
risks: Semantic evidence production and atomic sealing remain intentionally absent until phases 12 and 14.
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
| 11.1 | `tests/test_reconciliation.py`, `scripts/test_check_repository.py` | Integration/policy | Existing operational store: 22 passed; policy: 22 passed | Reconciliation RED exited 2 during collection with `ModuleNotFoundError: scripts.reconcile_history`; policy RED exited 1 with missing `PRIVATE_ARTIFACT_PARTS` import | Initial implementation exposed 5 SQL failures and 7 passes, then the corrected focused suite passed 12 tests | Canonical/hash/identity/scope/source branches, sparse omission, explicit absence, pending invisibility, exact resume, Git-root refusal, cleanup, and sanitized output | Shared phase behavior remained green before helper consolidation |
| 11.2 | `tests/test_reconciliation.py` | Integration | Phase RED observed before production code | Shared phase RED above; partial-write assertion failed 1 with 12 deselected; traversal cleanup failed 1 with 12 deselected; expected-evidence binding failed 1 with 13 deselected; existing owner/payload import reuse failed 1 with 14 deselected | Each supplemental RED passed after its bounded fix; final focused suite passed 15 tests | Partial `os.write`, normalized cleanup escape, exact manifest drift, expected counts/evidence, owner/hash import reuse, sparse values, and tombstones forced non-trivial paths | Manifest/source phase helpers and privacy-safe result adapter retained 15 passing tests |
| 11.3 | `tests/test_reconciliation.py`, `scripts/test_check_repository.py` | Integration/policy | Phase 11 GREEN: 15 pytest and 23 policy tests passing | The task's refactor boundary is the shared failing phase RED plus four supplemental REDs, all written before their production changes | No new behavior was introduced during refactor; focused union remained green | All RED-defined manifest, durability, resume, cleanup, privacy, idempotency, and policy branches remained covered | Replaced repeated source-set scans with explicit phase sets; final focused command exited 0 with 15 pytest and 23 policy tests |

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

## Phase 11 Test Summary

- **Total tests written**: 15 pytest reconciliation cases and 1 repository-policy case (23 policy tests total)
- **Total tests passing**: 15 focused reconciliation; 23 policy; 212 repository-wide
- **Layers used**: Integration (15), repository policy (1 new), E2E (0)
- **Approval tests**: None — the new staging module was behavior-driven before refactor
- **Pure functions/helpers created**: 9 manifest, scope, candidate, publication, and resume helpers
- **Synthetic runtime**: Temporary mode-0700 roots, mode-0600 canonical manifest/source files, real SQLite/WAL, durable content-addressed artifacts, pending rows, CLI success/failure output, partial writes, and cleanup boundaries; no real reconciliation, migration, cutover, backup, or restore

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
- [x] 11.1 RED: canonical manifest, source durability, scope/identity, sparse omission, mismatch, pending invisibility, policy, cleanup, privacy, and exact-resume failures
- [x] 11.2 GREEN: durable manifest/source staging, pending receipts/versions/tombstones, resumable state, private CLI, and tracked-artifact audit
- [x] 11.3 REFACTOR: consolidated manifest/source phase helpers and privacy-safe output without changing the RED-defined boundaries

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

## Phase 11 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `.venv/bin/python -m pytest tests/test_reconciliation.py -q && .venv/bin/python -m unittest scripts.test_check_repository` exited 0: 15 pytest passed in 0.22s; 23 unittest tests passed in 0.101s. Expected synthetic negative-fixture diagnostics preceded final `OK`. |
| Runtime harness | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k cli_reports_only_sanitized_counts_and_failures` exited 0: 1 passed, 14 deselected in 0.06s. It invoked the real CLI adapter against isolated temporary synthetic SQLite/source/manifest artifacts and verified sanitized success/failure output. |
| Rollback boundary | Delete `src/reconciliation.py`, `scripts/reconcile_history.py`, and `tests/test_reconciliation.py`; revert only the Phase 11 additions in `scripts/check_repository.py`, `scripts/test_check_repository.py`, `tasks.md`, and this progress artifact. No sealed batch, authority event, current projection, source dataset, or live route is changed. |
| Review budget | 973 authored non-documentation additions plus deletions (972 additions, 1 deletion) and 1,048 total additions plus deletions (1,035 additions, 13 deletions) against merged base `387a66f1d2ddd3b249b19f4a8f2de9211760c142`; the non-documentation slice remains below the approved 1,000-line ceiling. |

## Phase 11 Final Verification

| Command | Exact result |
|---|---|
| `.venv/bin/python -m pytest tests/test_reconciliation.py -q && .venv/bin/python -m unittest scripts.test_check_repository` | Exit 0: 15 pytest passed; 23 unittest tests passed |
| `.venv/bin/python -m pytest` | Exit 0: 212 passed in 4.62s |
| Protected-path-filtered candidate repository audit using `.venv/bin/python` and `scripts.check_repository.main` | Exit 0: repository audit OK, 141 candidate files inspected; `dashboard/` and `.atl/` excluded |
| `.venv/bin/python -m unittest scripts.test_check_repository` | Exit 0: 23 passed; expected synthetic negative-fixture diagnostics preceded final `OK` |
| Protected-path-filtered tracked and untracked `git diff --check` equivalents | Exit 0 with no whitespace errors |
| Branch convention command | Not run by instruction: native ledger, stage, commit, review, issue, push, and PR delivery are parent-owned |

## Deviations And Constraints

- `src/storage.py` generic conversions remain unchanged for the pre-cutover/fallback `HealthStore`; the verified-candidate path bypasses that aggregation and reads only operational SQLite.
- `duckdb` and `pyarrow` remain dependencies until phases 9-17, cutover, and fallback closure prove no operational path imports them.
- Final readiness still requires a WAL/checkpoint policy, representative Raspberry Pi 5/NVMe measurement, and proven isolated restore after corruption.
- Final delivery gates, review, commit, push, and PR creation remain parent-owned and were not run here.
- Delivery Group 4 wires `src/operational_store.py` only when pointer selection resolves a schema-valid `ready` candidate; direct and legacy-pointer roots continue using `HealthStore` without dual-write.
- Batch staging is now implemented by Phase 11; approval, semantic-evidence admission, sealing, authority allocation, and current projection remain Phase 12+ and are absent from this slice.
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

## Phase 11 Automatic Gatekeeper Retry

```yaml
status: success
executive_summary: >-
  Corrected the two Phase 11 contract failures: same-hash retained live artifacts
  now resolve batch and receipt lineage to the durably published batch-source
  representation, and the CLI normalizes lower-level failures without exposing
  paths or hashes.
artifacts:
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/apply-progress.md
next_recommended: sdd-apply task 12.1 as the dependent stacked slice
risks: Phase 12 sealing, authority promotion, cutover, and private execution remain intentionally absent.
skill_resolution: paths-injected
```

### Retry TDD Cycle Evidence

| Contract failure | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|
| Same-hash retained `live_raw` collision | `.venv/bin/python -m pytest tests/test_reconciliation.py -q`: 15 passed | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k same_hash_live_artifact`: 1 failed, 14 deselected; the artifact row remained `live_raw` at the raw path | Same command: 1 passed, 14 deselected after explicit conflict rebinding to the published `batch_source` row | Existing no-collision staging plus retained-live collision cover both insert and conflict paths; both receipt purposes remain linked and the original live file remains present | Full focused file before the second RED: 15 passed; no further production refactor was needed |
| SQLite, writer-lock, and final directory-sync CLI failures | Phase-11 focused file after cycle 1: 15 passed | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k lower_level_failures`: 3 failed, 15 deselected with uncaught `sqlite3.OperationalError`, `RuntimeError`, and `OSError` | Same command: 3 passed, 15 deselected with exact constant privacy-safe output | Three distinct lower-level exception classes carry a synthetic private path and 64-character hash marker; none reaches output | `.venv/bin/python -m pytest tests/test_reconciliation.py -q`: 18 passed after test-only compaction; production behavior unchanged |

### Retry Test Summary

- **Corrective cases**: one retained-live collision case and three parametrized lower-level CLI failure cases.
- **Focused tests**: 18 reconciliation tests and 23 repository-policy tests passed.
- **Synthetic runtime harness**: `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k 'same_hash_live_artifact or cli_reports_only_sanitized_counts_and_failures or cli_sanitizes_lower_level_failures'` exited 0 with 5 passed and 13 deselected.
- **Full suite**: `.venv/bin/python -m pytest` exited 0 with 215 passed in 4.65s.
- **Repository audit**: protected-path-filtered candidate audit exited 0 with 141 files inspected; `.venv/bin/python -m unittest scripts.test_check_repository` exited 0 with 23 passed.
- **Whitespace**: the first wrapper used zsh's read-only `status` name and did not complete; the corrected protected-path-filtered tracked/untracked command used `rc` and exited 0 with no output.
- **Review budget**: 997 non-documentation additions plus deletions (996 additions, 1 deletion), below the hard 1,000-line ceiling.

### Retry Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `.venv/bin/python -m pytest tests/test_reconciliation.py -q && .venv/bin/python -m unittest scripts.test_check_repository` exited 0: 18 pytest passed; 23 unittest tests passed. |
| Runtime harness command and exact result | The five-case CLI and real temporary SQLite/filesystem harness above exited 0: 5 passed, 13 deselected. It performed no real reconciliation, migration, seal, cutover, backup, or restore. |
| Rollback boundary | Revert only the artifact conflict update in `src/reconciliation.py`, the lower-level CLI exception normalization in `scripts/reconcile_history.py`, their corrective assertions in `tests/test_reconciliation.py`, and this retry section. The Phase 11 staging capability and unrelated prior evidence remain intact; no schema, sealed batch, authority, current projection, source dataset, or live route changed. |
| Task status | Unchanged: 33/64 tasks complete; 11.1-11.3 remain complete and 12.1 remains the first pending task. |
| Protected paths | `dashboard/` and `.atl/` were excluded from every repository/diff command and were not read, enumerated, staged, moved, cleaned, deleted, or modified. |

## Ordinary-Review Correction `review-c28497124cb0c91c`

### Correction TDD Cycle Evidence

| Finding | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|
| Equal normalized source occurrences | `.venv/bin/python -m pytest tests/test_reconciliation.py -q`: 18 passed | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k 'equal_identity_occurrences or distinct_same_kind_batches'`: 2 failed, 18 deselected; equal occurrences yielded 0 versions/2 errors | Same command: 2 passed, 18 deselected | Corrective union added differing-value and value/absence controls: 4 passed, 18 deselected | None needed; corrective union remained green after the final pending-status assertion |
| Distinct same-kind batch context | Same 18-pass safety net | Same RED command aborted the second batch with `sqlite3.IntegrityError: duplicate metric context` | Same GREEN command retained one version per batch with distinct fingerprints | The first batch plus a second batch reusing the exact logical import exercised both initial and duplicate-context paths | None needed; minimum trusted batch context was passed to existing normalization |

### Correction Work Unit And Verification Evidence

| Evidence | Exact result |
|---|---|
| Focused corrective regressions | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k 'equal_identity_occurrences or only_differing_or_value_absence_occurrences or distinct_same_kind_batches'` exited 0: 4 passed, 18 deselected |
| Relevant reconciliation suite | `.venv/bin/python -m pytest tests/test_reconciliation.py -q` exited 0: 22 passed |
| Full pytest | `.venv/bin/python -m pytest` exited 0: 219 passed in 5.04s |
| Repository audit | Protected-path-filtered `scripts.check_repository.main(...)` exited 0: 141 versioned files inspected; the unfiltered wrapper was not run because it reads forbidden `dashboard/` and `.atl/` paths |
| Repository-policy unittests | `.venv/bin/python -m unittest scripts.test_check_repository` exited 0: 23 passed in 0.114s; expected synthetic negative-fixture diagnostics preceded final `OK` |
| Whitespace | `git diff --check` limited to the seven frozen review paths exited 0 with no output |
| Runtime harness | The focused tests used real temporary SQLite/WAL, two synthetic source receipts, one reused logical import across two pending batches, and no network or private operation |
| Rollback boundary | Revert only this correction in `src/reconciliation.py`, its regressions in `tests/test_reconciliation.py`, and this appended evidence; Phase 11 staging remains independently intact |
| Correction budget | **151 additions plus deletions** against the frozen candidate; hard limit 200 |
| Privacy and cleanup | Only synthetic `tmp_path` JSON/SQLite artifacts were used outside the worktree. No real reconciliation, seal, cutover, migration, backup, restore, network, staging, or cleanup operation ran; `dashboard/` and `.atl/` remained excluded and untouched. |

Task status remains unchanged: 33/64 tasks complete, with 12.1 still the first pending task.
