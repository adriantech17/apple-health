# Reversible Storage Cutover Specification

## Purpose

Define a candidate-copy migration, semantic verification, and cutover that keeps
the old dataset recoverable until the explicit live-receipt rollback boundary.

## Requirements

### Requirement: Capture A Reproducible Source Watermark

Before migration begins, the system MUST activate a maintenance gate that blocks
new writes through `POST /v1/ingest` while keeping `/health` and authenticated GET
routes available. The migration MUST record a reproducible source watermark
covering the old SQLite metadata, surviving raw payloads, Parquet artifacts, and
every independently verifiable recorded receipt in scope.

After closing admission, the gate MUST drain or abort every previously admitted
write before watermark capture. SQLite MUST be copied through a transactionally
consistent backup including committed WAL state, and raw and Parquet hashes MUST
be captured only after no writer can publish another artifact. The gate MUST
remain active until cutover verification succeeds or rollback to the old
application and dataset is verified. Any source change after the watermark MUST
invalidate the candidate rather than be silently omitted.

#### Scenario: Ingestion arrives during migration

- GIVEN the maintenance gate is active and authentication succeeds
- WHEN a client posts to `/v1/ingest`
- THEN it receives HTTP 503 with retry guidance, no write begins, and read-only routes remain available.

### Requirement: Build A Separate Candidate Without Mutating Sources

Migration MUST read the legacy source without rewriting it and MUST build a
separate writable candidate SQLite database. It MUST import the sealed baseline
and reconstruct every independently verifiable authoritative live receipt after
the baseline cutoff through the captured watermark exactly once. It MUST
reconstruct every accepted backfill batch in scope exactly once as a distinct
population. Reconstruction MUST preserve each original receipt or batch identity,
server-assigned kind, time, and trusted authority order; it MUST NOT create
audit-only `replay` receipts or grant new live authority at migration time.

Unreconstructable receipt occurrences MUST remain explicit gaps and MUST seed no
invented freshness or authority. The baseline scope and surviving evidence MUST
be sufficient to establish every migrated current identity; otherwise cutover
MUST remain blocked.

Migration time, file order, and file modification time MUST NOT determine the
current version. Failure MUST leave the legacy source usable and MUST allow the
candidate to be discarded without data loss.

#### Scenario: Candidate construction fails midway

- GIVEN some candidate records have been written
- WHEN a later migration step fails
- THEN the legacy source remains unchanged and ordinary rollback discards only the candidate.

### Requirement: Compare Accepted Semantics Rather Than Known Defects

Pre-cutover verification MUST compare owner, metric, local date, validity,
completeness, canonical value, unit, details, provenance, reconstructable logical
import, live-receipt and backfill-batch populations, documented evidence gaps,
current selections, tombstones, reconciliation state, and all four live-freshness
dimensions. The comparison MUST use an independent synthetic or reference
implementation of the accepted daily-summary and enabled metric contracts.

Known incorrect legacy behavior, including averaging multiple versions of one
daily identity, arbitrary units or details, rolling UTC windows, and conversion
after aggregation, MUST NOT be the equivalence target. Every intentional
difference MUST be classified and approved; every unexplained difference MUST
block cutover.

Real manifests, hashes, comparison reports, approvals, and restore evidence MUST
remain in private storage. Public diagnostics and tests MUST use only sanitized
counts, stable error codes, and synthetic fixtures; private evidence MUST NOT
enter Git, CI, ordinary logs, screenshots, container images, telemetry, or
external services.

#### Scenario: Corrected daily selection differs from the legacy API

- GIVEN the old reader averaged multiple step versions for one local date
- WHEN candidate equivalence is evaluated
- THEN the one authoritative daily version is checked against the accepted contract and the legacy difference is documented rather than copied.

### Requirement: Verify Backup And Restore Before Switching

Before cutover, ingestion MUST be gated and drained and the candidate MUST be
captured through a transactionally consistent SQLite backup including committed
WAL state. The complete candidate and its referenced artifacts MUST enter an
encrypted backup with a manifest and integrity verification.

That backup MUST be restored into an isolated location and MUST pass schema,
population, lineage, semantic-read, and application-start checks. Every raw
artifact referenced by restored SQLite MUST also be restored and hash-verified.
Every immutable reconciliation or backfill source artifact referenced by a sealed
batch MUST be restored and matched to its manifest hash. A backup that was not
restored successfully MUST NOT authorize cutover.

#### Scenario: Backup integrity succeeds but restore fails

- GIVEN the candidate backup hash matches its manifest
- WHEN isolated restore cannot serve verified reads
- THEN cutover remains blocked.

### Requirement: Switch Application And Dataset As One Unit

Cutover MUST switch the application version and authoritative storage together
while ingestion remains gated. Read-only verification MUST confirm `/health`,
authentication boundaries, `/v1/status`, and `/v1/metrics/{metric}` before new
live writes are admitted. The current release and at least one fallback
SQLite-compatible application artifact MUST both pass startup, read, and
synthetic accepted, duplicate, degraded, rejected, malformed, oversized, and
unauthorized write checks against separate isolated restored candidates. Test
writes MUST never target the cutover dataset.

The maintainer MUST supply immutable current and fallback application artifact
identities and external stop/start operations. Cutover MUST record and verify the
active identity but MUST remain neutral to the private lifecycle mechanism; it
MUST NOT require or implement Compose, systemd, GHCR, or release automation.
Automated tests MUST use a synthetic lifecycle harness.

The maintenance gate and cutover phase MUST be durable outside either switchable
dataset. Startup MUST validate the phase, gate, application identity, selected
dataset, schema, and live-receipt rollback marker before serving traffic. Any
mismatch or interrupted transition MUST fail closed. Every transition MUST be
idempotently resumable or, before the rollback boundary, reversibly return to the
verified old pair. After the boundary, a stale journal MUST NOT authorize the
legacy dataset.

The existing data-route names, parameters, response fields, empty states, and
error shapes MUST remain compatible. Corrected values MAY differ only where the
accepted storage and metric semantics require it.

#### Scenario: A data response shape changes

- GIVEN the candidate returns semantically correct values
- WHEN contract verification detects a removed or renamed existing response field
- THEN cutover fails despite value correctness.

#### Scenario: The process crashes after selecting the candidate

- GIVEN the candidate dataset was selected but read-only verification did not finish
- WHEN the application restarts
- THEN startup keeps ingestion closed and resumes or rolls back the durable cutover phase without serving a mismatched pair.

### Requirement: Enforce The Live-Receipt Rollback Boundary

Before the first post-cutover live receipt is persisted, rollback MUST restore the
old application and complete old dataset together, verify old reads, and only
then reopen ingestion. The first transaction that persists any live receipt,
including accepted, degraded, rejected, or duplicate, MUST durably record that
routine rollback to the stale Parquet-backed dataset is closed in the same SQLite
transaction as its receipt and any versions, freshness, or current-projection
changes applicable to that outcome.

After that boundary, application rollback MUST use a version compatible with the
authoritative SQLite store and MUST preserve all post-cutover receipts and
versions without schema downgrade. The verified fallback artifact MUST remain
available until a post-cutover encrypted backup containing at least one accepted
live receipt has been restored in isolation and has passed the fallback startup,
read, and write smoke tests. Restoring the legacy dataset MUST be treated as
disaster recovery, not ordinary code rollback.

#### Scenario: Verification fails before live writes reopen

- GIVEN cutover read checks fail and no post-cutover live receipt was persisted
- WHEN rollback is requested
- THEN application and storage return to the verified old pair before ingestion reopens.

#### Scenario: A live receipt has crossed the boundary

- GIVEN SQLite persisted a live receipt after cutover
- WHEN an application rollback is needed
- THEN operation remains on SQLite and no stale legacy dataset is mounted as current.
