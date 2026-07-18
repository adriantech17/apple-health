# Design: Migrate Daily Summaries to Operational SQLite

## Technical Approach

Build a new `operational.sqlite3` inside a private candidate copy and make it the
only operational source after verified cutover. Keep copied legacy
`metadata.sqlite3`, raw archives, and Parquet read-only as migration input and
audit evidence. Raw retained by the source contract, including contract-valid
all-invalid receipts, and reconciliation/backfill sources use content-addressed
private artifacts linked from SQLite.

Normalize Health Auto Export daily summaries through one versioned metric
contract. Commit receipts, valid versions, authority, freshness, and current
selection in SQLite transactions. `metric_current` is explicit; reads never infer
current values from insertion order or scan legacy files.

Use a process-shared maintenance gate to drain ingestion, SQLite online backup
for a consistent snapshot, canonical manifest-backed migration, and an independent
semantic comparator. External lifecycle operations switch an immutable application
artifact and one data-root pointer during a brief stopped-app cutover. Preserve
routine rollback until the first persisted post-cutover live receipt atomically
closes it.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|---|---|---|---|
| Operational database | New `operational.sqlite3` in the candidate | Mutate legacy tables | Keeps evidence and pre-write rollback intact |
| Daily identity | `{user_id, metric, local_date}` in `Europe/Madrid` | Filesystem identity | Matches the daily-summary contract |
| Logical idempotency | `{user_id, payload_sha256}` plus receipts | One row per request | Preserves retries and owner scope |
| Authority | Sequence only for a live operation creating a new authoritative version or a batch seal | Receipt time or filename | Orders trusted corrections without no-op authority |
| Absence | Explicit version tombstone | Zero or omission | Distinguishes reconciled absence from sparse omission |
| Values | Canonical decimal text and details JSON | Generic average or arbitrary `REAL` | Avoids drift and aligns each daily shape |
| Historical import | Pending manifest batch sealed atomically | File-by-file updates | Prevents partial visibility |
| Reconstruction | Preserve live receipts and accepted backfill batches separately | Relabel as replay | Preserves exact-once populations and authority |
| Gate | Durable marker plus advisory shared/exclusive lock | Process-only flag | Drains admitted writes while reads remain available |
| Backup | Encrypted Restic plus isolated restore | Unverified copy or cloud service | Proves private ARM64 recovery |
| Cutover | External lifecycle plus atomic data pointer | Permanent dual-write | One reversible, deployment-neutral switch |

## Module Boundaries

```text
src/app.py                    existing routes and response adapters
src/storage.py                HealthStore facade and operational read/write API
src/storage_schema.py         explicit idempotent SQLite schema migrations
src/metric_contracts.py       daily shapes, validation and canonical conversion
src/maintenance.py            ingestion gate and process/data-root locking
scripts/reconcile_history.py  manifest build, validate, approve and seal
scripts/migrate_storage.py    snapshot, candidate build, compare and cutover
scripts/verify_restore.py     isolated backup/restore and fallback smoke
```

Scripts call storage services directly, never HTTP routes. The application stays
one process and one writer. Schema creation and migration run only through explicit
commands; startup validates schema and state but performs no DDL.

## Private Storage Layout

```text
<source-root>/                         existing HEALTH_DATA_DIR before adoption only
<installation-root>/                   separate sibling on the same filesystem
  current -> datasets/legacy | datasets/candidate
  maintenance/ingestion.gate
  maintenance/ingestion.lock
  maintenance/cutover.json          durable recovery journal
  datasets/legacy/                  unchanged active dataset before cutover
  datasets/candidate/
    operational.sqlite3
    metadata.sqlite3                copied legacy evidence
    raw/                             copied legacy raw evidence
    parquet/                         copied legacy Parquet evidence
    raw-v2/sha256/aa/<digest>.json.gz
    batch-sources/sha256/aa/<digest>.json
    manifests/<batch-id>.json
    migration/<run-id>/report.json
```

Private reports contain hashes, counts, and sanitized identity references. Real
paths, hashes, manifests, values, and reports stay out of Git, CI, images,
telemetry, screenshots, logs, and external APIs.

Private commands set umask `077`, require owned directories mode `0700` and files
mode `0600`, reject symlinked artifact paths, and use no-follow opens. An existing
content-addressed target is reused only when owner, mode, regular-file type,
length, and hash all match.

## Operational Schema

All timestamps are UTC RFC 3339 text; local dates are ISO `YYYY-MM-DD`; booleans
are constrained integers. JSON uses canonical UTF-8 with sorted keys and no
non-finite numbers. Foreign keys are immediate unless a seal transaction needs a
documented deferred constraint.

| Table | Key fields and role |
|---|---|
| `schema_migrations` | Applied version and timestamp |
| `users` | Fixed `user_id`, timezone, contract version, next authority sequence |
| `dataset_state` | Schema state, watermark, cutover phase, first post-cutover live receipt |
| `imports` | Logical import, owner, payload SHA-256, bytes, first seen; unique owner/hash |
| `artifacts` | Content hash, kind, relative path, bytes for durable raw or batch source |
| `receipt_artifacts` | Receipt-to-artifact link and purpose |
| `import_receipts` | Receipt, import, kind, parser/contract, source metadata, result and times |
| `receipt_errors` | Sanitized code, metric and local date when known; no raw values |
| `authority_events` | Owner sequence and exactly one live receipt or sealed batch source |
| `metric_versions` | Receipt/batch, identity, value/absence, source/canonical units, content, completeness, authority source |
| `metric_current` | Identity to selected value or tombstone version |
| `reconciliation_batches` | Kind, canonical manifest hash, scope, status, approval, authority and seal |
| `batch_sources` | Batch-to-artifact link; producing receipts also link artifacts |
| `batch_promotions` | One batch identity to its selected version; all producing receipt versions remain |
| `semantic_evidence` | Manifest/candidate/source hashes, comparator version, outcome and counts |
| `replay_operations` | Replay identity and completed idempotent receipt/evidence audit record |
| `live_freshness` | Latest authenticated, committed and clean receipt; latest complete local date |

`metric_versions` allows one candidate per `{receipt_id, metric, local_date}`.
Identical batch occurrences remain separate receipt versions; validation requires
equal normalized hashes and `batch_promotions` selects one deterministically while
retaining every producing receipt link. Conflicting values or value/absence
disagreement block the batch. Value versions require source/canonical units and
canonical value; tombstones require all value/unit fields null.

Composite keys enforce current-version identity, receipt/import owner, and
version/receipt owner. Each authority event has an XOR live-receipt or batch source
with composite source FKs. Each version has the same XOR: live authority must
reference its own receipt/event; batch authority must reference its batch/event.
Application checks supplement but never replace these relational constraints.

Indexes cover identity, receipt/import joins, receipt status/time, batch status,
and current ranges; none contains details or raw values. Connections enable
`foreign_keys=ON`, WAL, `synchronous=FULL`, and bounded busy timeout. An exclusive
data-root process lock and one in-process writer lock prevent unsupported writers.

## Metric Normalization

`metric_contracts.py` defines immutable entries for every enabled metric:

```text
name, daily shape, timestamp identity forms, accepted source units, canonical unit,
shape validator, converter, detail encoder, limitation
```

Parse JSON numbers as `Decimal`, reject booleans and non-finite values, and emit
canonical decimal strings without display rounding. Convert before persistence.
Initial conversions include `kJ` to `kcal`, metres to kilometres, `hr` to `h`,
`count/min` to `bpm`, and fractional oxygen to percent only for its declared metric.
Unknown metrics, units, or identity forms invalidate the candidate.

Offset-aware timestamps convert to `Europe/Madrid` before deriving the date. A
metric-contract-approved date-only daily identity is interpreted directly as a
Madrid calendar date, never midnight UTC. Other missing or invalid date forms are
invalid. Total/scalar rows persist one `qty`; heart rate keeps aligned
`Avg`/`Min`/`Max`; sleep keeps its primary duration and validated stage/interval
details. Normalization never combines rows for one identity; conflicting rows in
one receipt are ambiguous.

A `context_fingerprint` hashes normalized content, server-assigned kind,
completeness, parser version, contract version, metric contract, and trusted batch
context, excluding receipt ID, time, and authority sequence. It is the
cross-receipt idempotency key for one logical import and daily identity.

## Live Ingestion Flow

1. Authenticate with the existing shared bearer before reading the body.
2. Fast-check the gate, take a nonblocking shared ingestion lock, and recheck the
   marker under it. Gate/busy returns HTTP 503 with `Retry-After`. Hold through commit.
3. Stream within declared and actual limits, then hash admitted bytes. Unauthorized
   or oversized input records nothing. Malformed JSON or invalid source contract
   records a sanitized rejected receipt and logical import but retains no raw.
4. Under current parser/contract rules, validate JSON v2, `Default`, summarized
   daily grouping, source identity form, and Madrid date at one injected instant.
5. Permit today and yesterday. Invalid candidates coexist with valid siblings as
   degraded; a contract-valid all-invalid receipt retains raw and returns HTTP 422.
6. Reuse owner/hash import. Unchanged fingerprints add no version; changed trusted
   context or normalized content adds a receipt-linked version. Revalidate every
   retry: a currently malformed or contract-invalid retry remains an error response,
   reuses its logical import, records a receipt, and retains raw only if currently allowed.
7. For raw-retaining outcomes, gzip to a unique staging path, sync, rename to the
   content-addressed final path, sync the parent, then link it from SQLite.
8. Begin `IMMEDIATE`; insert import, artifact links, receipt, errors, and valid
   versions. Allocate authority only if this live operation created at least one
   new authoritative version; no-op retries allocate none.
9. Apply current selection and outcome-specific freshness. In the first transaction
   persisting any post-cutover live receipt status, also close legacy rollback.
10. Commit SQLite, sync its directory, and release the lock. Pre-commit crashes can
    leave only unreferenced artifacts for quarantine.

Every authenticated bounded request admitted far enough to record a receipt
advances authenticated freshness, including malformed, contract-invalid,
all-invalid, rejected, and retried outcomes. Degraded advances committed but not
clean freshness. Clean accepted or clean no-op duplicate advances committed and
clean freshness. Only successful processing of a complete date advances the fourth
field. Reconciliation, backfill, and replay advance no live freshness.

Today is partial. Yesterday is complete only when validated automation provenance
proves generation after its closing Madrid midnight; otherwise it is unknown.
Exact receipt/source timestamps establish placement but not closure. Reconstructed
receipts use the same rule; invalid new timestamps are invalid, not unknown.

The adapter preserves existing status codes and response fields. `received_points`
counts parsed metric/date candidates; `inserted_points` counts new versions. The
current bearer still authorizes all three `/v1` routes; `/health` remains public
and credential separation is future work.

## Authority And Current Projection

Inside a live commit, increment `users.next_authority_sequence` and add an event
only when at least one new authoritative version is created. A verified batch seal
allocates one sequence shared by all promoted versions/tombstones. Pending batches,
completed replay, and no-op retries have no authority sequence.

For each affected identity:

1. Reject invalid, pending, replay, or unresolved candidates.
2. Keep a complete current version against a later partial or unknown candidate.
3. Otherwise select the eligible greatest authority sequence.
4. Point `metric_current` to that value or explicit tombstone.

A sealed batch replaces lower-sequence identities explicitly covered by its
approved scope; omission does nothing. A later permitted live sequence may replace
it. Projection updates occur in the authority-event transaction; history is
immutable afterward. Rebuild ranks values and tombstones together and never falls
back below a selected tombstone.

## Reconciliation, Backfill, And Replay

Each reconciliation or backfill first durably stores every source artifact and a
canonical manifest containing source hashes, generation context, server kind,
owner, timezone, metric/date scope, explicit identities or coverage rules,
importer version, expected counts, and required semantic evidence. The six annual
files form one baseline reconciliation batch; accepted backfills remain distinct
batches. Discovery order never defines content or precedence.

Validation creates pending receipts, errors, versions, and explicit tombstones
without changing current state. Semantic evidence is persisted and bound to exact
manifest, source, and candidate hashes for reconciliation and backfill. A blocking
error, stale evidence, conflict, hash mismatch, or unexplained population delta
leaves the entire batch unsealed.

Approval re-enters the exact manifest hash. One `IMMEDIATE` seal transaction
rechecks immutable artifacts and evidence, allocates one authority sequence,
activates all pending versions, updates affected current rows, stores approval and
counts, and marks the batch sealed. Failure rolls back the complete seal. Cleanup
removes only proven disposable staging files.

Completed replay records exactly one receipt and mandatory validation/audit
evidence for its existing logical import per replay operation. Repeating the same
payload in that operation is idempotent. Replay has no authority or freshness.
Migration reconstruction is separate: it preserves independently verifiable live
receipt and accepted backfill-batch identities, kinds, times, and authority order,
and rebuilds freshness only where evidence proves it. Unknown occurrences remain
explicit evidence gaps.

## Operational Reads

`/v1/metrics/{metric}?days=N` resolves exactly `N` inclusive Madrid dates ending
today, queries `metric_current` by owner/metric/date, joins one value version,
omits tombstones, and orders by date. It preserves `date`, numeric `value`, `unit`,
`samples`, and optional `details`; `samples` is one selected daily summary.

`/v1/status` preserves existing fields. `imports` counts logical imports,
`points` counts versions from accepted/degraded receipts, `last_import_at` uses
latest committed live receipt, and `last_automation` uses validated metadata.
Reads never open raw, Parquet, batch sources, pending versions, or replay evidence.

## Candidate Migration And Cutover

1. Resolve the existing source root and a distinct sibling installation root;
   require the same filesystem and reject either path as the other's descendant.
   After verifying predecessor, app IDs, capacity, and stop/start, journal and sync
   the `HEALTH_DATA_DIR` transition. With the app stopped, rename source to
   `datasets/legacy`, sync both parents, create/sync `current`, verify old reads,
   and recover or roll back interrupted adoption before candidate work.
2. Atomically create the durable gate outside datasets, acquire the exclusive
   lock, and drain admitted shared holders while GET routes remain live.
3. Use SQLite online backup for a synced frozen legacy copy including committed
   WAL state; after drain, hash it, raw, and Parquet into one private watermark.
4. Copy immutable evidence into the candidate and initialize operational SQLite
   as `building` with pinned owner and timezone.
5. Stage the canonical baseline manifest, run the independent comparator, and
   approve/seal only exact manifest-bound successful evidence.
6. Reconstruct every verifiable authoritative live receipt after baseline through
   watermark exactly once and every accepted backfill batch in scope exactly once
   as distinct populations. Record gaps without invented authority or freshness.
7. Compare owner, identity, validity, completeness, canonical content, provenance,
   logical imports, live-receipt and backfill-batch populations, gaps, current and
   tombstone rows, batch state, and all four freshness dimensions. Block unexplained
   differences or any migrated current identity unsupported by evidence.
8. Still gated/drained, make and sync a SQLite online copy that includes committed
   WAL state as Restic input. Back up it and every referenced artifact, then restore
   in isolation and verify schema, lineage, populations, hashes, and semantic reads.
9. On separate restored copies, run current and fallback startup/read plus synthetic
   accepted, duplicate, degraded, rejected, malformed, oversized, and unauthorized
   write smokes. Test writes never target the cutover candidate.
10. Mark `ready`; durably write an outside-dataset journal with old/new targets,
    immutable application artifact IDs, gate state, and phase `prepared`, using
    temp-file sync, atomic rename, and parent-directory sync.
11. The maintainer externally stops the app and selects the candidate application
    artifact. The CLI records `switching` and atomically replaces/syncs only the
    data pointer. Startup serves nothing unless artifact ID, schema, target, gate,
    journal, and rollback marker agree; POST remains gated during read-only checks.
12. On success, journal `verified` before removing/syncing the gate. Before any live
    receipt, failure restores the verified old application/data pair and old reads
    before reopening POST. Startup idempotently resumes or reverses interrupted
    phases and never invokes deployment tooling.

The durable gate and journal are outside switchable datasets and are fail-closed
startup inputs; advisory locks are coordination, not recovery state. Every phase
verifies recorded inputs and resumes idempotently or refuses mismatch. This design
requires only external lifecycle operations and immutable artifact IDs; it neither
requires nor implements Compose, systemd, GHCR, or release automation. Legacy is
never written and permanent dual-write is not used.

## Backup And Legacy Evidence

Every Restic run gates and drains ingestion, creates a synced SQLite online copy
including committed WAL state, and backs up that copy rather than a live database
file. It includes every SQLite-referenced raw and immutable batch artifact,
canonical manifests/evidence, legacy tree, outside-dataset journal and gate state,
pointer target, application IDs, runtime configuration, and compatible encrypted
secrets. Recovery material remains separate. A pinned hash-verified ARM64 Restic,
repository/capacity/lock preflight, `check --read-data`, offline removable storage,
and native isolated restore are required evidence.

The first persisted post-cutover live receipt of any status closes routine legacy
rollback in its transaction. The verified SQLite-compatible fallback remains until
an encrypted post-cutover backup containing an accepted live receipt is restored
and passes fallback startup/read/write smoke. Legacy evidence may leave operational
storage only after rollback closure and an encrypted isolated restore proves files,
hashes, WAL-consistent SQLite, schema, and audit relationships. Legacy Parquet
remains non-rebuildable evidence where SQLite lacks pre-baseline history.

## Testing Strategy

Strict RED-GREEN-REFACTOR tests use minimal synthetic JSON, temporary directories,
injected clocks, lifecycle harnesses, and fault points.

| Area | Required evidence |
|---|---|
| Schema | Idempotent migration, constraints, indexes, startup state and one writer |
| Identity | Owner FKs, owner/hash import reuse, receipt separation, context fingerprint |
| Metrics | Every shape/unit/date form, Decimal conversion and aligned details |
| Calendar | Today/yesterday, old/future, date-only, midnight and both Madrid DST transitions |
| Acceptance | Auth/size, malformed/contract-invalid retry, all-invalid raw, degraded siblings |
| Authority | No-op sequence, ordering, complete non-regression, later live, tombstones |
| Durability | Artifact/commit fault points, quarantine, restart and freshness atomicity |
| Batches/replay | Canonical evidence, mismatch, sparse omission, exact-once replay, atomic seal |
| Reads | Local-date window, route/status compatibility, auth, empty state, no legacy access |
| Migration | Drain, WAL copy, distinct populations, four freshness fields, journal recovery |
| Recovery | Gated backup, all referenced artifacts, fallback smoke and rollback boundary |

Production checks use private counts and hashes but emit only sanitized pass/fail
evidence. Tests never access the real data root.

## Applicability And Failure Matrix

| Boundary | Applicability | Safe / failure behavior | Planned RED tests |
|---|---|---|---|
| Documentation-like paths | N/A: no executable classification | Fixed Python entry points only | None |
| Git repository selection | N/A: commands never invoke Git | Private output stays outside worktrees | None |
| Commit state | N/A: no commit automation | No index interaction | None |
| Push state | N/A: no push automation | No remote interaction | None |
| PR commands | N/A: no PR automation | No `gh` invocation | None |
| HTTP routing | Applicable | Authenticate first; gate returns 503; failure performs no body/storage work | Unauthorized gate, busy lock, route precedence |
| Restic subprocess | Applicable | Verified absolute binary and argv, no shell, password file; any mismatch blocks readiness | Metacharacter paths, wrong hash/arch, lock/capacity, secret leakage |
| Process lifecycle | Applicable | External stop/start plus immutable artifact ID; mismatch/interruption fails closed | Stop/start failure, spoofed ID, stale journal, restart |
| Artifact/SQLite commit | Applicable | Durable artifact precedes transaction; failure exposes nothing and quarantines orphan | Fault before/after sync, rename, commit |
| Batch seal | Applicable | Whole batch seals or remains pending with current unchanged | Hash/evidence conflict and every transaction fault |
| Candidate/cutover | Applicable | Legacy immutable; pre-boundary journal rollback, post-boundary SQLite fallback | Comparison mismatch, interrupted adoption/switch, stale legacy target |

## File Changes

| Area | Files |
|---|---|
| Storage | `src/storage.py`, `src/storage_schema.py`, `src/metric_contracts.py`, tests |
| Gate | `src/maintenance.py`, app integration and concurrency tests |
| Private operations | Migration, reconciliation, restore scripts and synthetic tests |
| Contracts | Existing app tests for all `/v1` statuses and response fields |
| Documentation | ADR 0004 follow-up, README state, private migration/rollback runbook |

Future dashboard publication work must use SQLite rather than transitional
Parquet/DuckDB operational reads. Task slicing and PR allocation remain for the
next artifact; implementation does not start from this design alone.
