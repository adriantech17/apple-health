# Tasks: Migrate Daily Summaries to Operational SQLite

## Delivery Contract

| Field | Value |
|---|---|
| Estimated authored changes | 4,400-5,630 remaining lines across code, tests, scripts, and docs |
| Review budget | 1,000 authored non-documentation lines per PR; approved size exception |
| 400-line budget risk | High; superseded for this change by the approved 1,000-line exception |
| Chained PRs | Required; 15 remaining phases delivered as 7 cohesive PRs |
| Delivery strategy | `auto-chain`, stacked to `main` |
| Test discipline | Strict RED-GREEN-REFACTOR in every implementation PR |
| Production data | Maintainer-only private operation after all implementation PRs merge |
| Permanent dual-write | Prohibited |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
Approved size exception: 1,000 authored non-documentation lines per PR

Implementation MUST NOT start from the approval of design alone. Phases 1 and 2
already merged as the no-pruning and maintenance/layout predecessors. Delivery
group 1 starts from a clean, updated `main`, not the current dashboard feature
branch; every later PR branches only after its predecessor merges. Split before
opening any PR forecast above 1,000 authored non-documentation additions plus
deletions. Documentation-only `*.md` files do not count toward this limit, but
remain part of complete diff, privacy, correctness, and rollback review. Comments,
docstrings, embedded strings, tests, scripts, configuration, and generated source
code are not documentation for budget purposes. Generated evidence,
databases, JSON, compressed payloads, Parquet, backups, manifests with real
hashes, and private paths MUST NOT enter Git, CI, PR comments, or agent context.

Task approval authorizes synthetic implementation phases only. It does not
authorize maintainer-only private migration execution.

## Required Checks

Run the focused command listed for each PR first, then before review run:

```bash
python -m pytest
python scripts/check_repository.py
python -m unittest scripts.test_check_repository
git diff --check
```

Run configured frontend tests, lint, and build only when those scripts exist on
the merged `main` base. Before each PR, run `scripts/check_conventions.py` with
its actual branch, base, head, and proposed Conventional Commit title.

Before every commit, inspect the complete diff manually for credentials, real
health data, generated artifacts, unrelated changes, and rollback compatibility.
Use synthetic fixtures and `tmp_path` only. A failed check remains visible in the
PR with its residual risk; it is never skipped silently.

RED MUST be committed or otherwise observed failing for the intended reason
before GREEN begins. GREEN adds only enough behavior to pass that RED. REFACTOR
MUST add no behavior or new test case; every discovered case starts another
RED-GREEN cycle before refactoring resumes.

For every delivery group, forecast tests, production code, scripts, and docs per
file in the PR description. After RED, ensure every new file is tracked or marked
`intent-to-add`, inspect `git diff --numstat origin/main`, and manually total
authored additions plus deletions for every file except documentation-only `*.md`
files. Before review, repeat against `origin/main...HEAD` from a clean worktree.
Also report the complete diff including documentation. Use adjacent `a`/`b` PRs
only when a cohesive group cannot remain below the 1,000-line non-documentation
guard.

## Delivery Groups And Phase Chain

Phases retain their numbered RED-GREEN-REFACTOR checkpoints, but adjacent phases
that produce one independently reversible capability share a PR. Each phase must
still complete its focused RED before its GREEN begins, and commits should retain
those review boundaries inside the grouped PR.

| Group | Phases | Cohesive outcome | Non-documentation forecast | Rollback boundary |
|---:|---:|---|---:|---|
| Merged | 1 | Preserve raw evidence | Merged | No rollback; retained raw is required |
| Merged | 2 | Maintenance gate and pointer-ready layout | Merged as PRs #15 and #16 | Gate off; direct legacy root |
| 1 | 3 | Constrained operational SQLite schema | 320-390 | Delete unused candidate DB |
| 2 | 4-6 | Complete immutable metric contract registry | 750-1,000 | Revert unused registry module |
| 3 | 7-8 | Operational persistence, authority, and current projection | 650-780 | Legacy remains selected; projection unused |
| 4 | 9-10 | Operational live ingestion and read API | 590-750 | Select legacy root before first post-cutover live receipt |
| 5 | 11-12 | Reconciliation staging and atomic seal lifecycle | 630-770 | Discard pending batch or leave it unsealed |
| 6 | 13-14 | Candidate construction and independent semantic verification | 610-770 | Discard candidate; comparator mutates no state |
| 7 | 15-17 | Verified recovery, crash-safe cutover, and readiness runbook | 810-1,000 | Discard isolated restore; journal rollback before first post-cutover live receipt |

Run these focused checks after each phase RED-GREEN cycle inside its delivery
group; the final group review still runs their union and all required checks:

| Group | Focused checks | Synthetic harness |
|---:|---|---|
| 1 | `python -m pytest tests/test_storage_schema.py` | Temporary SQLite |
| 2 | `python -m pytest tests/test_metric_contracts.py` | Pure synthetic rows |
| 3 | `python -m pytest tests/test_operational_store.py` | Faulting temporary filesystem and SQLite |
| 4 | `python -m pytest tests/test_live_ingestion.py tests/test_operational_reads.py tests/test_app.py` | `TestClient` and two roots |
| 5 | `python -m pytest tests/test_reconciliation.py && python -m unittest scripts.test_check_repository` | Temporary private-like root and concurrent reads |
| 6 | `python -m pytest tests/test_storage_migration.py` | Independent synthetic legacy and candidate stores |
| 7 | `python -m pytest tests/test_storage_migration.py tests/test_restore.py tests/test_cutover.py tests/test_app.py && python -m unittest scripts.test_check_repository` | Fake Restic/lifecycle and end-to-end synthetic root |

## Phase 1: Preserve Raw Evidence (Merged Prerequisite)

- [x] 1.1 **RED:** Change retention tests to fail unless automatic ingestion-time
  pruning is disabled by default, committed raw survives the old 30-day boundary,
  and an explicit unsupported retention request fails safely.
- [x] 1.2 **GREEN:** Remove the automatic `prune_raw()` call from the route and
  make the no-pruning release the oldest supported migration rollback target;
  preserve the manual function only if an existing testable operator need remains.
- [x] 1.3 **REFACTOR:** Remove dead retention configuration, document increased
  storage responsibility, and run PR 1 checks. Deployment remains a later
  maintainer-only prerequisite in M.1.

## Phase 2: Maintenance And Private Layout (Merged Predecessor)

- [x] 2.1 **RED:** Add synthetic concurrency and restart failures for gate marker
  precheck, nonblocking shared lock, second check under lock, HTTP 503 with
  `Retry-After`, writer drain, GET availability, restrictive permissions, and
  mismatched data/application state. Prove missing/invalid bearer remains 401 and
  performs no gate, lock, body, or storage work.
- [x] 2.2 **GREEN:** Implement `src/maintenance.py`, umask/mode/no-follow checks,
  advisory locking, durable marker helpers, and opt-in pointer resolution while
  preserving the direct legacy root before the private layout-adoption step.
- [x] 2.3 **REFACTOR:** Centralize durable file operations and injected lock/clock
  seams; verify no async-loop blocking and record exact rollback to the direct
  legacy path.

## Phase 3: Operational Schema (Delivery Group 1)

- [ ] 3.1 **RED:** Add schema tests for idempotent explicit migration, schema
  state, fixed owner/timezone, all CHECK constraints, composite owner/identity
  foreign keys, indexes, one-writer lock, and rejection of mismatched current
  pointers or authority sources. Startup with a timezone other than the persisted
  `Europe/Madrid` MUST fail before reads or writes, while the legacy database
  remains readable and unchanged when the standalone candidate is created.
- [ ] 3.2 **GREEN:** Add `src/storage_schema.py` and candidate-only schema creation
  for users, state, imports, artifacts, receipts/errors, authority, versions,
  current, batches/sources, and freshness with WAL and `synchronous=FULL`.
- [ ] 3.3 **REFACTOR:** Keep startup validation read-only, isolate connection
  policy, inspect query plans for identity/range joins, and remove duplication
  without extending behavior.

## Phase 4: Registry Core And Totals (Delivery Group 2)

- [ ] 4.1 **RED:** Add synthetic valid/invalid fixtures for registry admission,
  Decimal parsing, finite-number rejection, canonical JSON, and the nine approved
  daily-total metrics with every accepted source unit and incompatible units.
- [ ] 4.2 **GREEN:** Add immutable `src/metric_contracts.py` entries and canonical
  conversion for totals, including energy and distance, without period aggregation
  or display rounding.
- [ ] 4.3 **REFACTOR:** Share validators/converters, keep metric-specific unit
  declarations explicit, and verify unknown metrics cannot produce versions.

## Phase 5: Scalar Contracts (Delivery Group 2)

- [ ] 5.1 **RED:** Add accepted-unit, boundary, malformed, boolean, non-finite,
  fractional oxygen, gait percentage, and no-rescaling counterexamples for all 12
  approved scalar daily summaries.
- [ ] 5.2 **GREEN:** Implement scalar contracts and canonical values while
  preserving each daily summary as one indivisible version.
- [ ] 5.3 **REFACTOR:** Remove generic conversion branches from legacy storage
  where safe, deduplicate only dimensionally equivalent validators, and run the
  complete registry suite.

## Phase 6: Composite, Sleep, And Sparse Contracts (Delivery Group 2)

- [ ] 6.1 **RED:** Fail heart-rate ordering/extrema, sleep duration/stage/interval
  consistency, one-minute tolerance, sparse absence, and unit-alignment cases for
  `heart_rate`, `sleep_analysis`, `vo2_max`, and `cardio_recovery`.
- [ ] 6.2 **GREEN:** Implement the four contracts with canonical value/details
  from one source row and no interpolation, zero fill, or cross-version fallback.
- [ ] 6.3 **REFACTOR:** Stabilize error codes and context fingerprints and prove
  all 25 enabled metrics have valid-shape, accepted-unit, and invalid examples.

## Phase 7: Imports, Receipts, And Durable Artifacts (Delivery Group 3)

- [ ] 7.1 **RED:** Add fault-injection failures for owner/hash idempotency,
  receipt separation, rejected-body retention rules, stage/sync/rename/parent
  sync, existing-target verification, SQLite rollback, and orphan quarantine.
- [ ] 7.2 **GREEN:** Add operational-store import/receipt/error/artifact methods
  with content-addressed raw, composite FKs, sanitized diagnostics, and atomic
  receipt transactions over already durable artifacts.
- [ ] 7.3 **REFACTOR:** Keep filesystem and transaction seams narrow, ensure no
  raw value/path/hash reaches public logs, and benchmark synthetic artifact work
  without weakening `FULL` durability.

## Phase 8: Versions, Authority, And Current (Delivery Group 3)

- [ ] 8.1 **RED:** Fail tests for context-idempotent retry, changed completeness,
  monotonic owner sequence, complete non-regression, later live correction,
  replay/pending exclusion, unresolved conflicts, batch uniqueness, and explicit
  absence tombstones, including transaction rollback at every projection boundary.
- [ ] 8.2 **GREEN:** Persist immutable metric versions and authority events and
  update `metric_current` transactionally through one deterministic selection
  function enforced by composite identity constraints.
- [ ] 8.3 **REFACTOR:** Consolidate projection updates for live and seal flows,
  remove duplication without changing behavior, and inspect current-range plans.

## Phase 9: Live Ingestion And Freshness (Delivery Group 4)

- [ ] 9.1 **RED:** Add API/store failures for auth-before-body, actual byte bound,
  declared-length rejection, bounded streaming that stops at the actual limit,
  exact `Default` JSON v2 contract, today/yesterday Madrid dates, proven/unknown
  closure, DST, all-invalid 422, degraded siblings, duplicate context, four
  freshness dimensions, first-persisted-receipt rollback closure, and crash
  behavior for rejected, duplicate, and degraded receipts.
- [ ] 9.2 **GREEN:** Route live normalization and operational transactions through
  the new store when a verified candidate root is selected; preserve bearer,
  statuses, five success fields, and legacy behavior on the legacy root without
  dual-writing.
- [ ] 9.3 **REFACTOR:** Inject receipt time and automation provenance, isolate the
  response adapter, remove duplication, and retain privacy-safe errors.

## Phase 10: Operational Reads (Delivery Group 4)

- [ ] 10.1 **RED:** Fail exact inclusive Madrid date ranges, DST boundaries,
  tombstone omission, one-version value/unit/details alignment, `samples=1`,
  empty result, identifier validation, status meanings, and shared-bearer route
  compatibility.
- [ ] 10.2 **GREEN:** Implement indexed SQLite current reads and status projection
  behind root/schema-state selection; operational reads MUST NOT open raw,
  Parquet, DuckDB, pending batches, or replay versions.
- [ ] 10.3 **REFACTOR:** Remove generic operational aggregation from the SQLite
  path, capture five-year/25-metric query plans and timings, and retain the legacy
  path only for the pre-cutover root and fallback window.

## Phase 11: Stage Reconciliation (Delivery Group 5)

- [ ] 11.1 **RED:** Add private-CLI service failures for synthetic canonical
  manifests, source durability, owner/timezone/scope, explicit identity coverage,
  sparse omission, hash mismatch, duplicate sources, pending invisibility, and
  sanitized output. Add repository-policy failures for tracked private artifact
  directories, command output attempted inside any Git worktree, and cleanup that
  would touch anything beyond proven disposable staging. Require idempotent resume
  only when the exact manifest hash matches.
- [ ] 11.2 **GREEN:** Implement batch/source staging and pending receipt/version/
  tombstone validation in reusable Python services plus the non-networked
  `scripts/reconcile_history.py` adapter. Extend the tracked-file audit before
  any private-layout command exists, refuse private output beneath Git roots, and
  persist manifest-bound resumable phase state.
- [ ] 11.3 **REFACTOR:** Consolidate manifest phase helpers, prohibit real
  paths/hashes in ordinary output, and remove duplication without changing the
  RED-defined resume or cleanup boundaries.

## Phase 12: Seal Reconciliation (Delivery Group 5)

- [ ] 12.1 **RED:** Fail approval-hash mismatch, changed source, population error,
  unordered conflict, duplicate batch identity, concurrent reader, transaction
  fault, later live, explicit absence, non-authoritative replay, and missing or
  stale persisted semantic-verification evidence.
- [ ] 12.2 **GREEN:** Recheck and atomically seal one approved batch, allocate one
  authority sequence, activate candidates, update current/tombstones, and retain
  complete audit lineage only when a manifest-bound successful comparison record
  exists. Phase 14 supplies the independent producer before private execution.
- [ ] 12.3 **REFACTOR:** Share authority/current code with live ingestion, keep the
  public route incapable of batch authority, and run the full reconciliation and
  operational-store suites.

## Phase 13: Candidate Builder (Delivery Group 6)

- [ ] 13.1 **RED:** Add synthetic tests for durable gate/drain, SQLite online WAL
  snapshot, immutable source hashes, layout adoption, candidate state, six-source
  baseline, original receipt reconstruction, every accepted backfill batch exactly
  once with preserved identity/kind/time/authority order, collapsed/pruned evidence
  gaps, interrupted resume, mismatched-source refusal, final candidate SQLite hash,
  and legacy hash stability through every completed phase.
- [ ] 13.2 **GREEN:** Implement candidate phases in `scripts/migrate_storage.py`
  through service functions; never mutate source, invent receipts/freshness, or
  create audit replay in place of preserved live or backfill authority. Persist
  sanitized phase evidence/input hashes and implement idempotent resume or mismatch
  refusal for the separate live-receipt and backfill-batch populations.
- [ ] 13.3 **REFACTOR:** Consolidate phase transitions and remove duplication
  without changing RED-defined resume, source-integrity, or discard behavior.

## Phase 14: Semantic Comparator (Delivery Group 6)

- [ ] 14.1 **RED:** Fail independently calculated owner/metric/date, validity,
  completeness, Decimal value, unit, details, provenance, current/tombstone,
  reconstructable live-receipt and backfill-batch populations, evidence-gap,
  batch identity/order, four freshness comparisons, manifest binding, and stale
  comparison reuse.
- [ ] 14.2 **GREEN:** Implement a reference normalizer and structured private
  comparison record/report that classifies expected legacy corrections, binds to
  manifest/candidate/source hashes, and blocks every unexplained difference
  without printing real values.
- [ ] 14.3 **REFACTOR:** Keep the reference path independent from operational
  selection code, add deterministic synthetic golden manifests, and measure
  comparison time/memory without weakening checks.

## Phase 15: Backup And Restore (Delivery Group 7)

- [ ] 15.1 **RED:** Add fake-executor and temporary-repository tests for gated
  online SQLite copy, complete artifact set, pointer/journal/release/config/secret
  inventory, pinned ARM64 Restic hash, disk identity/capacity/lock, restore hash
  mismatch, `check --read-data`, password-file-only secrets, restored schema,
  population, lineage, semantic reads, and both current/fallback failures for
  accepted, duplicate, degraded, rejected, malformed, oversized, and unauthorized
  requests on separate copies. Candidate readiness MUST fail until the complete
  restore contract succeeds.
- [ ] 15.2 **GREEN:** Implement `scripts/verify_restore.py` orchestration with
  explicit command arguments, redacted diagnostics, isolated restore roots, and
  no network or cloud requirement. Mock command construction in CI; expose one
  documented opt-in real-Restic integration command using the pinned official
  ARM64 checksum and password file, and gate readiness on the successful result.
- [ ] 15.3 **REFACTOR:** Separate command construction from execution, document
  native Pi `restic check --read-data` and offline removable-disk operation, and
  remove duplication without changing the RED-defined readiness gate.

## Phase 16: Crash-Recoverable Cutover (Delivery Group 7)

- [ ] 16.1 **RED:** Fault every journal, file sync, application-identity/data-pointer, stop/start,
  startup handshake, read-only verification, gate removal, pre-receipt rollback,
  first persisted receipt, stale journal, reboot, legacy hash recheck, and
  legacy-target refusal step using a fake deployment-neutral lifecycle harness.
- [ ] 16.2 **GREEN:** Implement the durable cutover state machine and CLI around
  atomic data-pointer replacement and externally supplied application artifact
  identity. The operator controls stop/start through the existing private process
  mechanism; startup serves no traffic for a mismatched identity/state and the
  CLI never implements Compose, GHCR, systemd, or release automation.
- [ ] 16.3 **REFACTOR:** Make recovery decisions explicit and idempotent, preserve
  the verified SQLite fallback identity, and remove duplication without adding
  behavior; all route and cutover cases already belong to RED.

## Phase 17: Runbook And Readiness (Delivery Group 7)

- [ ] 17.1 **RED:** Add repository-policy assertions for ignored private artifact
  patterns already blocked in PR 11 and a runbook checklist/link failure covering
  prerequisites, backup, compare, approval, cutover, rollback, archive, and abort.
- [ ] 17.2 **GREEN:** Update ADR/README/operations docs, revise
  the documented future dashboard dependency to require operational SQLite, and
  complete one end-to-end synthetic rehearsal using current and fallback artifacts.
- [ ] 17.3 **REFACTOR:** Record synthetic timings and storage headroom, verify all
  commands from a clean private-like environment, run every required check, and
  leave real migration execution as an explicit maintainer approval gate.

## Maintainer-Only Private Migration Gate

These steps occur only after every remaining delivery-group PR merges, the
maintainer separately authorizes private execution, and deployed artifacts are
verified. They MUST NOT run in CI or against the real dataset by an agent.

- [ ] M.1 Confirm private installation paths, owner, `Europe/Madrid`, six source
  files and expected hashes, Restic repository, removable-disk capacity, recovery
  material, current/fallback artifact IDs, existing private process-control steps,
  and no-pruning predecessor deployment. During a stopped-app window, adopt and
  fsync the `datasets/legacy` plus `current` pointer layout, restart the old
  artifact, and complete its pointer rollback drill before continuing.
- [ ] M.2 Activate the durable gate, drain ingestion, capture the source watermark,
  build the candidate, durably stage the six-file baseline, and produce its
  manifest-bound semantic verification without sealing or reconstructing live.
- [ ] M.3 Review baseline semantic/population differences and evidence gaps;
  approve the exact manifest/comparison hashes and seal only when every
  unexplained difference is closed. Then reconstruct independently verifiable
  live evidence through the watermark and every accepted backfill batch in scope
  exactly once as distinct populations, preserving batch identity, kind, time,
  and authority order. Run the final comparator, including freshness and
  candidate/source hashes.
- [ ] M.4 Complete encrypted backup, native `restic check --read-data`, isolated
  restore, both application artifacts on separate restored copies with every
  ingestion outcome, and pre-receipt rollback drill before changing the pointer.
- [ ] M.5 Execute cutover, verify read-only routes/authentication, and explicitly
  choose rollback or POST reopening. Record that the first persisted receipt of
  any status permanently closes legacy rollback.
- [ ] M.6 After at least one accepted post-cutover live receipt, create and restore
  a new encrypted backup with the fallback artifact. Recheck final candidate and
  legacy hashes. Archive legacy evidence only after the documented rollback
  window and restore criteria close.

## Completion Gate

- [ ] The task plan received explicit maintainer approval before remaining
  implementation; the merged predecessors and every remaining delivery-group PR
  and required adjacent split merged sequentially with focused and full checks.
- [ ] No PR exceeds 1,000 authored non-documentation additions plus deletions;
  documentation-only `*.md` changes remain fully reviewed, and no unrelated
  frontend or deployment infrastructure enters the chain.
- [ ] Synthetic tests cover every accepted metric, unit, DST boundary, correction,
  missingness, failure boundary, backup, restore, and rollback state.
- [ ] Current HTTP route, bearer, status, response fields, and empty/error shapes
  remain compatible.
- [ ] SQLite alone reconstructs operational reads and every current value or
  tombstone has owner-consistent receipt, artifact, authority, and batch lineage.
- [ ] Legacy source hashes remain unchanged through the rollback window, the
  candidate has independently verified hashes, and no migration step deletes
  history.
- [ ] Real-data evidence remains private and the maintainer explicitly approves
  manifest seal, cutover, POST reopening, and later archival.
