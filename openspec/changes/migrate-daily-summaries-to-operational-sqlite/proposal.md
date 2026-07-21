# Proposal: Migrate Daily Summaries to Operational SQLite

## Intent

Make SQLite the authoritative operational store for the private single-user
phase before publishing the dashboard.

Persist logical imports, concrete receipts, normalized daily-summary versions,
the current-version projection, and sealed historical reconciliations in one
transactional store. Preserve the current HTTP route and response shapes while
replacing filesystem-dependent correction selection and generic Parquet
aggregation with explicit, tested metric authority.

Perform the migration against a verified candidate copy, not directly against
the active production dataset. Keep the current raw, SQLite metadata, and
Parquet files intact until equivalence, cutover, rollback, backup, and archival
conditions have been verified.

## Current State

The implemented store currently:

- keeps import metadata and a unique event index in SQLite;
- stores import-level `received_at` in SQLite, but normalized metric values,
  units, details, and per-event receipt timestamps only in Parquet;
- identifies exact request duplicates by SHA-256 of the request body;
- globally deduplicates normalized events by a content-derived event identifier;
- retains only the first import relationship for a repeated event;
- writes raw, SQLite, and Parquet through separate durability boundaries;
- retains new raw payloads without automatic pruning, while earlier pruning left
  dangling SQLite paths and historical evidence gaps;
- reads every matching Parquet file without reconciling it against SQLite;
- selects one row per exact timestamp using `received_at` without a stable
  tie-breaker;
- averages every metric and selects units and details from arbitrary rows;
- converts some units only after aggregation;
- derives daily ranges from a rolling UTC cutoff and mutable process
  configuration.

SQLite alone cannot currently reconstruct the served metric values. Parquet is
therefore an operational dependency rather than a derived analytical layer.

## Scope

### In Scope

- Make SQLite authoritative for accepted imports, ingestion receipts,
  normalized daily-summary versions, and the selected current version.
- Assign all existing and new records to one explicit initial `user_id` without
  implementing user management or accepting user identity from request input.
- Persist the dataset timezone as `Europe/Madrid` and treat local date as part of
  the daily-summary identity.
- Preserve logical payload idempotency within the owner using the payload
  SHA-256 while recording relevant receipts separately.
- Persist receipt provenance, parser and contract version, server-assigned
  import kind, validation result, automation metadata, and degradation errors.
- Accept the daily REST automation only as a validated live `Default` export
  using JSON v2, summarized data, and daily grouping.
- Route reconciliations and historical backfills through private, local import
  workflows whose authority is assigned by the server, never by a free-form
  request header.
- Preserve valid metric versions from a partially degraded live receipt while
  rejecting invalid metric/date candidates and retaining the previous valid
  current value.
- Represent daily-summary completeness as `partial`, `complete`, or `unknown`
  without inferring ambiguous midnight cases.
- Persist live-ingestion freshness independently from reconciliation, backfill,
  replay, metric coverage, and sparse-metric recency.
- Import the six private reconciled JSON files as one manifest-backed historical
  baseline with explicit hashes, scope, validation, and atomic promotion.
- Replay and validate authoritative live receipts after the baseline watermark,
  including overlapping corrections.
- Apply accepted private backfill batches as a distinct authority population
  without relabeling them as live receipts.
- Migrate every independently verifiable accepted import and correction in the
  selected baseline, live, and backfill populations.
- Migrate and verify a candidate dataset while authenticated GET routes remain
  read-only against the old dataset and ingestion remains stopped.
- Preserve the route and response shapes of `/v1/status` and
  `/v1/metrics/{metric}` during the storage migration.
- Preserve all existing raw, SQLite, and Parquet artifacts throughout migration,
  verification, cutover, and the initial rollback window.
- Record the operational boundary at which the first persisted post-cutover live
  receipt closes routine rollback to the old Parquet-backed dataset.
- Retain the legacy raw and Parquet dataset as encrypted audit evidence until
  backup, restore, rollback, and archival requirements permit removing it from
  operational storage.

### Out of Scope

- Dashboard UI, browser authentication, session redesign, accessible navigation,
  charts, request-state handling, or visual work.
- Caddy, Docker Compose, GHCR, ARM64 release automation, or Raspberry Pi
  deployment infrastructure.
- Separating ingestion and direct-read credentials.
- Changing the public route names or JSON response shapes of the existing API.
- Implementing multiple users, account management, authorization roles, user
  selection, or client-supplied `user_id`.
- Introducing PostgreSQL, multiple writers, Uvicorn workers, replicas, network
  services, queues, or distributed session state.
- Rebuilding or publishing a new analytical Parquet layer.
- Deleting current Parquet, raw archives, SQLite metadata, corrections, or
  historical evidence.
- Migrating an obsolete or ambiguous physical Parquet row whose accepted
  authority cannot be proved; retain it as legacy evidence instead.
- Treating legacy Parquet as rebuildable from SQLite when it contains
  pre-baseline evidence not migrated into the operational store.
- New dashboard snapshot, overview, detail, freshness, or provenance response
  contracts.
- Performance optimization beyond indexes and query behavior required for
  correctness of the existing API.
- `tasks.md` or implementation work in this phase.

## Capabilities

### New Capabilities

- `authoritative-daily-summary-storage`: SQLite owns logical payloads, concrete
  receipts, normalized daily versions, owner/date identity, and the current
  projection.
- `live-daily-ingestion`: The REST endpoint validates the daily automation
  contract, commits valid metric versions atomically, records degraded
  processing, and maintains live freshness.
- `sealed-historical-reconciliation`: Private manifest-backed reconciliations
  and backfills remain invisible to current reads until their declared scope is
  verified and promoted atomically.
- `reversible-storage-cutover`: Migration uses a candidate copy, reproducible
  source watermark, semantic equivalence checks, an ingestion gate, a brief
  cutover, and an explicit rollback boundary.
- `legacy-evidence-preservation`: Existing raw, SQLite metadata, and Parquet
  remain immutable audit evidence through migration and can be archived only
  after verified encrypted recovery.

### Modified Capabilities

None in `openspec/specs/`, which is currently empty.

Future dashboard publication work depends on this change and must treat SQLite,
not transitional Parquet/DuckDB reads, as its authoritative operational source.

## Behavioral Contract

### Daily Identity

The private daily-summary identity is:

```text
user_id + metric + local_date
```

The dataset contract, JSON version, grouping, timezone, automation, parser, and
source metadata are validated provenance. A mismatching contract does not create
a parallel metric series.

### Authority

- A valid live receipt may affect only the metric dates permitted by its
  validated `Default` daily window.
- The current date is partial.
- A valid complete previous-day version may replace its earlier partial version.
- Ambiguous midnight cases remain `unknown` until resolved by a later live
  receipt or sealed reconciliation.
- A payload outside the live window is rejected or quarantined by the live
  endpoint.
- An exact payload duplicate remains one logical import for the owner.
- A reconciliation or backfill has no authority until its complete batch is
  verified and sealed.
- A replay retained only for audit does not advance the current projection.
- A conflict that cannot be ordered from validated source authority is recorded
  for review instead of being resolved by filesystem order or a free-form
  identifier.
- Within multiple valid complete live versions belonging to the same allowed
  authority class, server receipt order is the practical deterministic order.

### Partial Acceptance

- Invalid size, JSON, envelope, authentication, or source contract rejects the
  receipt before it can produce versions.
- A receipt containing metric-level validation errors may commit its valid
  metric versions and becomes `degraded`.
- Invalid metric/date candidates do not replace the current valid version.
- The previous valid value remains available but is explicitly associated with
  a newer degraded receipt.
- A reconciliation containing blocking errors remains unsealed and modifies no
  current version.
- Invalid and rejected evidence remains traceable without copying real values
  into public logs or test artifacts.

### Freshness

Freshness is derived only from live receipts and distinguishes:

- latest authenticated live receipt;
- latest committed live receipt;
- latest clean live receipt;
- latest complete local date processed.

Reconciliation, backfill, and replay do not refresh daily automation freshness.
Metric coverage and sparse-metric recency remain separate concepts.

## Migration Approach

Stopping ingestion means activating a maintenance gate over `POST /v1/ingest`
that prevents new writes while keeping the public health check and authenticated
GET routes available. The gate mechanism belongs to the design and is not
selected by this proposal.

Capture a reproducible source watermark, then create a verified private
candidate copy containing the current SQLite metadata, surviving raw payloads,
and legacy Parquet evidence.

Build the authoritative baseline from the six private reconciled JSON files using
one canonical manifest that records hashes, generation context, temporal scope,
selected metrics, importer version, and comparison result.

Reconstruct authoritative live receipts after the baseline cutoff through the
captured source watermark. Reconstruct accepted backfill batches separately.
Preserve each original server-assigned kind and authority order rather than
relabeling data or ordering it by migration time.

Compare the candidate semantically by owner, metric, local date, validity,
completeness, canonical value, unit, details, provenance, import populations,
and status counts. The current incorrect `AVG`, `ANY_VALUE`, rolling-UTC, or
post-aggregation conversion behavior is not the equivalence target.

Keep the existing application reading only the old dataset during preparation.
After candidate verification, switch application and storage during a brief
ingestion outage and run read-only verification before admitting any new live
write.

The first persisted post-cutover live receipt marks the end of routine rollback
to the old Parquet-backed dataset. Subsequent code rollback must remain
compatible with the current SQLite store.

## Affected Areas

| Area | Impact |
|---|---|
| `src/storage.py` and focused storage modules | Replace Parquet-backed operational reads with SQLite imports, receipts, versions, and current projection |
| `src/app.py` | Validate daily live source contract while preserving route and response shapes |
| `tests/test_storage.py` | Add authority, idempotency, partial acceptance, completeness, user scope, and SQLite read tests |
| `tests/test_app.py` | Preserve API compatibility and verify rejected/degraded ingestion behavior |
| New migration and reconciliation commands | Candidate-copy migration, private manifest import, semantic comparison, cutover, and rollback verification |
| SQLite schema management | Introduce explicit versioned and idempotent schema migration |
| Existing raw/Parquet dataset | Preserve as immutable migration input and legacy audit evidence |
| README, ADR, and operations documentation | Replace weekly cadence, document daily automation, SQLite authority, migration boundary, archive policy, and residual risks |
| Future dashboard publication work | Depend on this migration and avoid transitional operational Parquet reads |

## Impacts

- **Privacy:** The six real reconciled JSON files, real dataset, manifests,
  backups, migration reports, and semantic comparisons remain private and never
  enter Git, CI, public logs, container images, screenshots, or external
  services. Repository tests use only minimal synthetic fixtures and temporary
  directories.
- **Data:** SQLite becomes authoritative for the verified baseline and every
  later operational version. Existing raw and Parquet artifacts remain preserved
  as legacy evidence. No migration step deletes or rewrites the source dataset.
- **Authentication:** Existing API authentication and route scopes remain
  unchanged for this storage migration. The fixed initial owner is derived
  server-side and cannot be selected by request input.
- **API:** Existing route names and response shapes remain stable. Corrected
  authority, local-date, unit, and aggregation semantics may intentionally change
  values that were produced incorrectly by the old reader.
- **Operations:** The maintenance gate prevents new `POST /v1/ingest` writes
  during source-watermark capture, candidate migration, final cutover, and
  rollback verification. Authenticated GET routes remain available during
  candidate preparation.
- **Architecture:** This completes the private SQLite operational-store direction
  accepted in ADR 0004. Current Parquet stops being an operational source; future
  Parquet may be regenerated separately as a derived analytical layer.

## Risks

| Risk | Level | Mitigation |
|---|---|---|
| Baseline files do not represent the intended current history | High | Immutable manifest, declared scope, private comparison, and explicit operator approval before sealing |
| Live receipts after baseline are omitted or reordered | High | Reproducible source watermark, deterministic replay, overlap tests, and final population comparison |
| Current incorrect API output is mistaken for expected equivalence | High | Compare against the accepted daily metric contract and an independent synthetic/reference implementation |
| A partial reconciliation becomes visible | High | Keep versions pending and promote the complete verified batch atomically |
| Invalid metric data hides or overwrites a valid value | High | Preserve current valid pointer, record degraded receipt, and expose integrity state |
| Midnight or DST behavior misclassifies completeness | High | `Europe/Madrid` boundary tests, `unknown` state, and synthetic capture of the installed automation behavior |
| Candidate migration mutates the source dataset | High | Read-only source, separate writable candidate, hashes before/after, and no in-place transformation |
| Raw archive and SQLite commit diverge | High | Durable staged raw write and verified reference before transactional operational commit |
| `user_id` is assigned inconsistently | High | Persist one initial owner and derive identity only from trusted server configuration |
| API compatibility breaks existing readers | High | Contract tests for current paths, query parameters, response fields, empty states, and errors |
| Rollback loses post-cutover evidence | High | Keep ingestion closed until cutover acceptance; close legacy rollback in the first transaction that persists any live receipt |
| Legacy archive is removed too early | High | Require encrypted archive, manifest, integrity check, isolated restore, and closed rollback window |
| Metric absence is interpreted as disabled configuration | Medium | Report only observable receipt/data state; keep expected automation configuration as an external versioned contract |
| SQLite write contention appears | Medium | Preserve one writer/worker boundary and measure before adding concurrency or another database |
| Migration exceeds the approved 1,000-line non-documentation review budget | Medium | Group cohesive phases, report complete and non-documentation diff totals separately, and split before opening an oversized review |

## Rollback Plan

Before the first post-cutover live receipt is persisted:

- retain the old application image and complete old dataset;
- keep ingestion stopped through the maintenance gate;
- revert the application and storage mount together if candidate verification
  fails;
- verify the old API and dataset before reopening ingestion.

After the first post-cutover live receipt is persisted:

- do not switch routine operation back to the stale Parquet-backed dataset;
- roll back only to SQLite-compatible application versions;
- preserve new imports and versions in the current SQLite store;
- treat restoration of the old dataset as disaster recovery, not ordinary code
  rollback.

A backup is restored only for actual corruption or failed recovery after
preserving current failure evidence. Source and legacy artifacts are never
deleted as part of code rollback.

## Dependencies

- Accepted ADR 0004 operational/analytical storage direction.
- One fixed initial owner and pinned `Europe/Madrid` timezone.
- Private access to the six reconciled annual JSON files and their expected
  hashes. Publicly versioned migration code may read them only during private
  local execution; public or external tooling never receives their contents.
- Sufficient private storage for the immutable source, writable candidate,
  encrypted backup, isolated restore, and retained legacy archive.
- A period with the `POST /v1/ingest` maintenance gate active for source-watermark
  capture and final cutover, while GET routes remain available.
- Synthetic fixtures representing all metric classes, invalid units, partial
  days, DST boundaries, duplicates, corrections, sparse metrics, degraded
  receipts, and failed reconciliations.
- The merged no-pruning application version as the oldest permissible rollback
  target once migration evidence begins to depend on retained raw payloads.

## Success Criteria

- [ ] SQLite contains the initial owner, logical imports, relevant receipts,
  normalized metric versions, current projection, and reconciliation state.
- [ ] A repeated payload for the same owner remains one logical import while
  receipt provenance remains accurate.
- [ ] Latest authenticated, committed, and clean live receipt and latest complete
  local date advance independently; reconciliation, backfill, and replay advance
  none of those live-freshness fields.
- [ ] Live, reconciliation, backfill, and replay classifications are assigned
  only by trusted server entry points; replay remains non-authoritative.
- [ ] Contract-invalid receipts create no metric versions; metric-level errors
  commit valid siblings as degraded without replacing the last valid value.
- [ ] Partial, complete, and unknown days are selected and aggregated according
  to the pinned `Europe/Madrid` contract, including both DST transitions.
- [ ] Sparse metrics and legitimate missing days do not require a complete
  metric-by-date Cartesian product during reconciliation.
- [ ] The six-file baseline cannot affect current reads before its manifest,
  hashes, scope, counts, and semantic comparison are verified and sealed.
- [ ] Every independently verifiable authoritative live receipt through the
  reproducible source watermark is included exactly once and preserves accepted
  corrections; evidence gaps remain explicit.
- [ ] Every accepted backfill batch in scope is reconstructed exactly once with
  its original non-live kind and authority order.
- [ ] `/v1/status` and `/v1/metrics/{metric}` retain their current route,
  parameter, and response shapes.
- [ ] Corrected SQLite reads match the accepted metric semantics and documented
  limitations rather than reproducing known incorrect Parquet aggregation.
- [ ] Hashes recorded for the legacy source raw archives, metadata SQLite, and
  Parquet artifacts remain unchanged throughout candidate migration and
  verification; the candidate SQLite has its own independently verified hashes.
- [ ] The candidate copy passes semantic equivalence, backup, isolated restore,
  cutover, and pre-write rollback checks.
- [ ] The first persisted post-cutover live receipt is recorded as the boundary
  after which routine rollback to the legacy dataset is prohibited.
- [ ] Legacy raw, metadata SQLite, and Parquet evidence remains operational or is
  moved only after its encrypted archive passes an isolated verified restore.
- [ ] All automated tests and public evidence use only synthetic data and
  temporary storage.
