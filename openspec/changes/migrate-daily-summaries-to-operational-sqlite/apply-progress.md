# Apply Progress: Migrate Daily Summaries to Operational SQLite

## Status

- Mode: Strict TDD
- Artifact store: OpenSpec
- Assigned batch: Delivery Group 6, Phase 13 Candidate Builder and Phase 14 Semantic Comparator
- Cumulative completed tasks: 1.1-14.3
- Newly completed tasks: 13.1-14.3
- Next pending task: 15.1
- Delivery boundary: Immutable synthetic candidate construction, exact population reconstruction, resumable source-bound phases, and independent manifest-bound semantic evidence only; no backup, restore, cutover, readiness, or maintainer-only private operation
- Delivery Group 6 review budget: 1,000 non-documentation additions plus deletions, at the approved ceiling; 1,113 total additions plus deletions against `c3e03dc89e7d4f061a5f810c972cbe52f7f3ae24`
- Auto-chain decision: Delivery Group 6 is one autonomous stacked-to-`main` slice containing only phases 13-14; Phase 15 remains unimplemented
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

## Phase 12 Result Contract

```yaml
status: success
executive_summary: >-
  Phase 12 tasks 12.1-12.3 added deterministic manifest/source/population/lineage
  validation, manifest-bound semantic-evidence admission, one atomic batch authority
  transition, explicit tombstone promotion, shared current selection, and idempotent
  retry after complete transactional rollback.
artifacts:
  - src/reconciliation.py
  - src/operational_store.py
  - scripts/reconcile_history.py
  - tests/test_reconciliation.py
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/tasks.md
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/apply-progress.md
next_recommended: sdd-verify Phase 12 stacked slice
risks: Phase 14 remains the required independent semantic-evidence producer before any private seal execution.
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
| 12.1 | `tests/test_reconciliation.py` | Integration | Existing reconciliation/operational/app safety net: 58 passed | Validation RED: `-k 'seal_'` exited 2 during collection because `reconciliation_evidence_binding` did not exist | Validation GREEN: 7 passed, 22 deselected | Approval, retained-source, blocking-error, missing-lineage/identity, missing evidence, and stale snapshot paths | Shared phase refactor retained the final 44-case reconciliation suite |
| 12.2 | `tests/test_reconciliation.py` | Integration | Phase-12 validation cluster: 7 passed | Atomic-seal RED: 10 failed, 1 passed, 29 deselected because `sealed_at` and the authority transition were absent; CLI RED: 2 failed, 40 deselected | Atomic GREEN: 11 passed, 29 deselected; CLI GREEN: 2 passed, 40 deselected | Equal occurrences, tombstone, later live, replay, concurrent reader, five transaction faults, exact retry, and conflict cases | Extracted shared `apply_projection`; reconciliation and operational-store suites remained 64/64 green immediately after refactor |
| 12.3 | `tests/test_reconciliation.py`, `tests/test_operational_store.py` | Integration/fault | Phase-12 GREEN: 64 passed across reconciliation and operational store | Resume re-hash RED: 1 failed, 42 deselected; sealed-lineage RED: 1 failed, 43 deselected | Supplemental GREEN commands each passed 1 focused case; final reconciliation suite passed 44 | Five rollback points preserve pending receipts/versions/evidence; retries reuse sequence 1; sealed retries re-hash artifacts and reject incomplete promotions | Shared authority/current helper plus final focused/relevant/full suites: 44, 125, and 241 passed |

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

## Phase 12 Test Summary

- **Total tests written**: 22 Phase 12 reconciliation cases, including parametrized mismatch and five transaction-fault paths; `tests/test_reconciliation.py` now collects 44 cases
- **Total tests passing**: 44 focused reconciliation; 125 relevant reconciliation/storage/API; 241 repository-wide
- **Layers used**: Integration/fault (22 new), E2E (0)
- **Approval tests**: None — new seal behavior was defined by failing tests before implementation
- **Shared helper refactor**: Live and batch authority now call one `apply_projection` function
- **Synthetic runtime**: Temporary mode-0700 roots, mode-0600 manifest/source artifacts, real SQLite/WAL readers and writer transactions, five injected seal faults, CLI approval, tombstones, live corrections, and replay; no private or production operation

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
- [x] 12.1 RED: approval/source/population/conflict/evidence, reader, fault, later-live, absence, replay, and idempotence failures
- [x] 12.2 GREEN: one manifest-bound atomic seal, authority sequence, activation, promotion, projection, and complete lineage
- [x] 12.3 REFACTOR: shared live/seal projection, deterministic retry, transactional rollback, and retained-evidence verification

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

## Phase 12 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `.venv/bin/python -m pytest tests/test_reconciliation.py -q` exited 0: 44 passed in 0.70s. The final combined focused/policy rerun below also passed 23 repository-policy unittests. |
| Runtime harness command and exact result | `.venv/bin/python -m pytest tests/test_reconciliation.py -q -k 'cli_seals_only or reader_overlapping or interrupted_seal'` exited 0: 7 passed, 37 deselected in 0.19s. It exercised the real private CLI adapter, WAL reader overlap, and five transaction fault points against synthetic `tmp_path` artifacts only. |
| Rollback boundary | Revert Phase 12 additions in `src/reconciliation.py`, `scripts/reconcile_history.py`, and `tests/test_reconciliation.py`; restore the private projection method in `src/operational_store.py`; revert only checkboxes 12.1-12.3 and Phase 12 progress evidence. Phase 11 pending batches remain intact and invisible with no authority event or projection. |
| Runtime rollback/cleanup | Every injected fault rolls the `IMMEDIATE` transaction back to pending receipts and versions, sequence 1, zero promotions, and unchanged imports/sources/evidence; exact retry then seals once. Seal performs no filesystem cleanup or historical deletion. Existing cleanup remains restricted to proven `batch-sources/.<id>.staging` files. |
| Privacy and authority boundary | Only synthetic temporary JSON/SQLite artifacts were used. CLI output contains sanitized counts/codes, the public app imports no seal entry point, and live ingestion cannot supply reconciliation/backfill authority. No real reconciliation, migration, cutover, backup, restore, deployment, network, or destructive cleanup ran. |
| Review budget | 965 non-documentation additions plus deletions (912 additions, 53 deletions), below the approved 1,000-line ceiling; complete diff is 1,047 lines (983 additions, 64 deletions), including OpenSpec evidence. |
| Task status | 36/64 tasks complete; 12.1-12.3 are checked and 13.1 remains the first pending task. |

## Phase 12 Final Verification

| Command | Exact result |
|---|---|
| `.venv/bin/python -m pytest tests/test_reconciliation.py -q` | Exit 0: 44 passed in 0.70s |
| `.venv/bin/python -m pytest tests/test_reconciliation.py tests/test_operational_store.py tests/test_storage_schema.py tests/test_operational_reads.py tests/test_live_ingestion.py tests/test_app.py tests/test_storage.py -q` | Exit 0: 125 passed in 5.39s |
| `.venv/bin/python -m pytest` | Exit 0: 241 passed in 5.39s |
| Protected-path-filtered `scripts.check_repository.main(...)` using Git pathspec exclusions | Exit 0: repository audit OK, 141 versioned files inspected; `dashboard/` and `.atl/` were excluded |
| `.venv/bin/python -m unittest scripts.test_check_repository` | Exit 0: 23 passed; expected synthetic negative-fixture diagnostics preceded final `OK` |
| `git diff --check` | Exit 0 with no output |
| Branch convention command | Not run by instruction: branch, ledger, stage, commit, review, issue, push, and PR mutations are parent-owned |

## Deviations And Constraints

- `src/storage.py` generic conversions remain unchanged for the pre-cutover/fallback `HealthStore`; the verified-candidate path bypasses that aggregation and reads only operational SQLite.
- `duckdb` and `pyarrow` remain dependencies until phases 9-17, cutover, and fallback closure prove no operational path imports them.
- Final readiness still requires a WAL/checkpoint policy, representative Raspberry Pi 5/NVMe measurement, and proven isolated restore after corruption.
- Final delivery gates, review, commit, push, and PR creation remain parent-owned and were not run here.
- Delivery Group 4 wires `src/operational_store.py` only when pointer selection resolves a schema-valid `ready` candidate; direct and legacy-pointer roots continue using `HealthStore` without dual-write.
- Batch staging and sealing are implemented through Phase 12; Phase 14's independent semantic comparator remains required to produce admissible evidence before private execution.
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

## Delivery Group 6 Result Contract

```yaml
status: success
executive_summary: >-
  Delivery Group 6 tasks 13.1-14.3 added a source-immutable, gate-drained,
  WAL-consistent and resumable candidate builder plus an independent reference
  semantic comparator that persists sanitized manifest/candidate/source-bound evidence.
artifacts:
  - scripts/migrate_storage.py
  - tests/test_storage_migration.py
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/tasks.md
  - openspec/changes/migrate-daily-summaries-to-operational-sqlite/apply-progress.md
next_recommended: sdd-apply Delivery Group 7, tasks 15.1-17.3
risks: Representative Raspberry Pi 5/NVMe measurements and isolated restore remain Phase 15+ readiness requirements.
skill_resolution: paths-injected
```

## Delivery Group 6 TDD Cycle Evidence

The three numbered tasks in each phase are the RED, GREEN, and REFACTOR checkpoints
of one shared phase cycle. Evidence is repeated per task so each completed checkbox
has a complete machine-routable cycle without claiming an execution that did not occur.

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 13.1 | `tests/test_storage_migration.py` | Integration/fault | Existing maintenance/schema/reconciliation/store suites: 102 passed | `.venv/bin/python -m pytest tests/test_storage_migration.py -q` exited 2 during collection with `ModuleNotFoundError: scripts.migrate_storage`; partial state-write supplemental RED exited 1 because resume read truncated JSON | Shared Phase 13 GREEN exited 0 with 3 passed; partial-write GREEN passed 1 focused case | WAL-backed metadata, six baseline sources, live/backfill populations, two gap classes, interruption/resume, source drift, partial writes, and wrong selected layout | Shared durable helpers and a complete-write loop retained 6 final focused cases |
| 13.2 | `tests/test_storage_migration.py` | Integration/fault | 102 dependent cases passed before production creation | Shared RED failed because the candidate service/adapter did not exist | Candidate builder GREEN exited 0 with 3 passed | First build and exact resume use different paths; drift and interrupted transaction prove fail-closed behavior | Consolidated one cumulative phase-state mapping; focused suite remained 3 passed |
| 13.3 | `tests/test_storage_migration.py` | Integration/fault | Phase 13 GREEN: 3 passed | Shared Phase 13 RED defined source-integrity and discard behavior before refactor | No new behavior was introduced during refactor | Existing success, interruption, resume, drift, and selected-layout branches remained covered | Existing reconciliation durability helpers and one phase transition mapping retained 3 passing cases |
| 14.1 | `tests/test_storage_migration.py` | Integration/reference | Phase 13 focused suite: 3 passed | Comparator cluster exited 1 with 2 failed, 3 deselected because `compare_candidate` did not exist; integral-zero supplemental RED exited 1 with `2 != 20`; independent authority-selection RED exited 1 with one failed, five deselected | Comparator GREEN passed 5 cases; Decimal and authority-selection GREEN commands each passed 1 focused case | Passed evidence, overlapping live/backfill authority, mutated-version mismatch, stale candidate hash, tombstone, source/manifest binding, populations, gaps, freshness, and multi-digit Decimal paths | Independent reference/query snapshots retained the final 6-case suite |
| 14.2 | `tests/test_storage_migration.py` | Integration/reference | Candidate construction: 3 passed | Shared comparator RED referenced the absent independent service | Shared comparator GREEN persisted passed/failed evidence and sanitized reports; 5 passed | One valid candidate and one non-current post-evidence mutation produced different candidate hashes and one stable privacy-safe difference category | Reference conversion/detail helpers remain separate from `apply_projection`; final focused suite passed 6 |
| 14.3 | `tests/test_storage_migration.py` | Integration/performance | Phase 14 GREEN: 5 passed | Shared comparator RED plus Decimal and authority-selection supplemental REDs define all refactor behavior | Final focused command exited 0 with 6 passed in 0.21s | Deterministic six-source canonical manifest, overlapping authorities, explicit absence, exact reuse, stale reuse, and value mutation cover non-trivial paths | Synthetic comparison passed in 0.004416s at 46,710,784-byte process max RSS; checks were not weakened |

## Delivery Group 6 Test Summary

- **Total tests written**: 6 collected integration/reference cases in `tests/test_storage_migration.py`.
- **Total tests passing**: 6 focused; 108 relevant dependent cases; 247 repository-wide.
- **Layers used**: Integration/fault (3), Integration/reference (2), Unit/reference (1), E2E (0).
- **Approval tests**: None — both new services were behavior-driven before implementation.
- **Independent functions/helpers**: Reference Decimal conversion, reference JSON/details normalization, semantic snapshot construction, and direct SQL observation do not call operational current-selection logic.
- **Synthetic runtime**: Temporary mode-0700 roots, mode-0600 files, live SQLite/WAL, advisory gate/drain locks, six synthetic baseline sources, preserved live/backfill authority, explicit gaps/tombstone, subprocess CLI build/resume/compare, and no private dataset or external service.

## Delivery Group 6 Completed Tasks

- [x] 13.1 RED: gate/drain, WAL snapshot, immutable hashes, adopted layout, six-source baseline, preserved populations/gaps, resume/mismatch, candidate hash, and legacy stability
- [x] 13.2 GREEN: source-bound candidate phases, exact live/backfill reconstruction, sanitized durable state, and idempotent resume
- [x] 13.3 REFACTOR: shared durable publication helpers and consolidated phase transitions without behavior changes
- [x] 14.1 RED: independent identity/content/provenance/current/population/gap/batch/freshness/manifest/staleness comparisons
- [x] 14.2 GREEN: independent reference normalization, structured sanitized report, expected-correction classification, and fail-closed evidence
- [x] 14.3 REFACTOR: independent query/reference paths, deterministic synthetic manifest, and comparison time/memory evidence

## Delivery Group 6 Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `.venv/bin/python -m pytest tests/test_storage_migration.py -q` exited 0: 6 passed in 0.21s. |
| Relevant dependent command and exact result | `.venv/bin/python -m pytest tests/test_storage_migration.py tests/test_reconciliation.py tests/test_operational_store.py tests/test_storage_schema.py tests/test_maintenance.py -q` exited 0: 108 passed in 1.38s. |
| Runtime harness command/scenario and exact result | A temporary-directory Python harness invoked `.venv/bin/python -m scripts.migrate_storage` through the real module/CLI boundary. First build: `phase=complete source_files=4 evidence_gaps=2 resumed=no`; exact resume: same counts with `resumed=yes`; compare: `outcome=passed differences=0`; report mode `0600`; temporary root absent after cleanup. |
| Process and cleanup evidence | Only harness subprocesses for the repository CLI were launched and awaited. No network, HTTP, deployment, process-control, backup, restore, cutover, seal, or real migration ran. `TemporaryDirectory` cleanup reported `cleanup True`; the durable gate and all candidate artifacts existed only below that synthetic root. |
| Source and rollback boundary | Revert/delete only `scripts/migrate_storage.py`, `tests/test_storage_migration.py`, task checkboxes 13.1-14.3, and this appended DG6 evidence. Discarding a synthetic/private candidate removes all new state; legacy metadata/raw/Parquet remain selected and byte-stable, while the comparator changes neither source evidence nor current selection. |
| Privacy boundary | Tests and harnesses used minimal synthetic values in temporary roots. Ordinary CLI output and comparison reports expose only phase/outcome/count/check codes; no paths, hashes, payloads, credentials, or health values are printed. Protected `dashboard/` and `.atl/` paths were excluded from repository/diff commands and never read or enumerated. |
| Review budget | 1,000 authored non-documentation additions plus deletions: 660 in `scripts/migrate_storage.py` and 340 in `tests/test_storage_migration.py`. Complete review total: 1,113 lines (1,100 additions, 13 deletions) against `c3e03dc89e7d4f061a5f810c972cbe52f7f3ae24`. The pre-existing untracked `exploration.md` is unchanged and excluded. |
| Task status | 42/64 tasks complete; 13.1-14.3 are checked and 15.1 is the first pending task. |

## Delivery Group 6 Final Verification

| Command | Exact result |
|---|---|
| `.venv/bin/python -m pytest tests/test_storage_migration.py -q` | Exit 0: 6 passed in 0.21s |
| `.venv/bin/python -m pytest tests/test_storage_migration.py tests/test_reconciliation.py tests/test_operational_store.py tests/test_storage_schema.py tests/test_maintenance.py -q` | Exit 0: 108 passed in 1.38s |
| `.venv/bin/python -m pytest` | Exit 0: 247 passed in 5.30s; configured `testpaths = ["tests"]` kept discovery outside protected paths |
| Protected-path-filtered `scripts.check_repository.main(...)` with the two untracked DG6 files included | Exit 0: repository audit OK, 143 candidate files inspected; `dashboard/` and `.atl/` excluded |
| `.venv/bin/python -m unittest scripts.test_check_repository` | Exit 0: 23 passed in 0.137s; expected synthetic negative-fixture diagnostics preceded final `OK` |
| Protected-path-filtered tracked `git diff --check` plus `git diff --no-index --check` for both new files | Exit 0 with no whitespace errors |
| Synthetic CLI build/resume/compare harness | Exit 0: build and resume completed, comparison passed with zero differences, report mode `0600`, cleanup true |
| Synthetic comparator measurement | Passed in 0.004416 seconds; process maximum RSS 46,710,784 bytes |
| Unfiltered `python scripts/check_repository.py` | Not run because it would enumerate explicitly forbidden `dashboard/` and `.atl/`; the same audit entry point passed with protected path exclusions and all DG6 files explicitly included |
| Branch convention command | Not run by instruction: stage, commit, title, push, issue, review, and PR delivery remain orchestrator-owned |

## Delivery Group 6 Deviations And Constraints

- No design deviation: candidate construction requires the predecessor adopted layout with legacy still selected; actual private adoption and process stop/start remain maintainer-only M.1 work.
- The independent comparator shares no operational projection or selection function. Candidate construction may call `apply_projection`; the comparator instead constructs a reference snapshot and reads persisted state directly.
- Comparison evidence is persisted only in `semantic_evidence`; source/current rows are never modified by comparison. Failed evidence remains non-admissible to Phase 12 sealing.
- Backup, isolated restore, candidate readiness, cutover journal/pointer switching, process lifecycle, POST reopening, and the irreversible first-live-receipt boundary remain entirely Phase 15+ or maintainer-only scope.
- The candidate builder accepts only a canonical, private reconstruction description of independently verifiable populations. It records pruned/collapsed evidence gaps and never synthesizes replay, freshness, or authority for a gap.

## Native Correction `review-d02425cb6ca036a5`

- Evidence revision: `sha256:f193969312b9f54953e8aebd8d69eab6041103e0e13743192b33c0ffc89911d3` over the frozen-to-corrected script and test patches.
- Strict-TDD RED/GREEN: the four named selectors each failed 1 before production changes (5/6/7/8 deselected respectively), then passed 1 and passed again after no-behavior-change refactor; corrective union passed 4 with 5 deselected.
- Verification: migration 9 passed; relevant dependencies 111 passed; full suite 250 passed. Repository audit, policy unittest, and whitespace results are recorded in the correction return.
- Runtime: synthetic CLI build/resume/compare exited 0 with `resumed=no`, `resumed=yes`, and `outcome=passed differences=0`; report mode `0600`, cleanup true, no private operation.
- Budget/rollback/status: 159 lines (script 84, tests 67, evidence 8); revert only those correction hunks. Tasks remain 42/64 and next routing remains Delivery Group 7, tasks 15.1-17.3.
