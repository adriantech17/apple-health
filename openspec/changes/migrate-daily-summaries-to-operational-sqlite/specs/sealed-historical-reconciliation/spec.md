# Sealed Historical Reconciliation Specification

## Purpose

Define private, manifest-backed historical reconciliation and backfill that
cannot affect current reads before complete verification and atomic sealing.

## Requirements

### Requirement: Admit Historical Data Only Through A Private Workflow

Reconciliation and backfill MUST run through a private local operator entry point
that assigns the initial owner and import kind server-side. The public ingestion
route MUST NOT invoke or grant this authority. The workflow MUST NOT require
uploading health data, manifests, reports, or hashes to an external service.

#### Scenario: A historical import is requested over HTTP

- GIVEN an authenticated live caller submits an old date range
- WHEN the public endpoint evaluates it
- THEN the request cannot acquire backfill or reconciliation authority.

### Requirement: Bind Every Batch To A Canonical Manifest

Each reconciliation or backfill batch MUST have a canonical manifest containing
immutable source hashes, generation context, server-assigned kind, owner, dataset
timezone, declared temporal scope, selected metrics, explicitly reconciled
identities or coverage rule, importer version, and expected comparison evidence.
The six private reconciled annual JSON files MUST form one explicit baseline
reconciliation batch; file discovery order MUST NOT define its contents or
precedence.

Every accepted source file MUST have a durable private immutable artifact linked
from its batch and receipts. Its content hash, not its original filename or path,
MUST identify it for backup, restore, and audit.

Manifest metadata in repository fixtures MUST be synthetic. Real filenames,
paths, hashes, values, or identifying metadata MUST NOT enter Git, CI, logs,
screenshots, or external services.

#### Scenario: A source file differs from its manifest

- GIVEN one private baseline file no longer matches its declared hash
- WHEN batch validation runs
- THEN the batch remains unsealed and changes no current version.

### Requirement: Keep Pending Batches Invisible

Versions created by reconciliation or backfill MUST remain pending and excluded
from operational reads until the entire declared batch passes parsing, contract,
unit, local-date, scope, population, lineage, and semantic validation and receives
explicit operator approval. Successful semantic evidence MUST be persisted and
bound to the exact manifest, candidate, and source hashes. A blocking error,
stale comparison, or unresolved authority conflict in any required part MUST
leave the complete batch unsealed and MUST modify no current projection.

Sealing MUST atomically assign one trusted authority sequence, record the verified
manifest, comparison, and approval, promote all permitted versions, update every
affected current pointer, and mark the batch sealed. A reader MUST observe either
the state before sealing or the complete state after sealing, never a partial
batch.

#### Scenario: One annual file fails validation

- GIVEN five baseline files validate and one contains a blocking error
- WHEN reconciliation completes
- THEN all six remain invisible to current reads and the batch is unsealed.

#### Scenario: A reader overlaps sealing

- GIVEN a valid batch is ready for promotion
- WHEN a read occurs concurrently with its seal transaction
- THEN the read observes either none or all of the promoted state.

### Requirement: Reconcile Declared Scope Without Inventing Missing Data

Validation MUST compare the batch against its declared owner, metric set, and
local-date scope. A missing expected additive or scalar daily summary MUST remain
missing and MUST NOT become zero. Sparse metrics MUST be validated as dated
observations and MUST NOT be required to populate every date or a fixed
metric-by-date matrix.

The manifest MUST distinguish omission from an explicit authoritative absence.
Only an identity explicitly reconciled as absent MAY produce an absence tombstone
at seal; omission outside that assertion MUST leave lower-authority state intact.

Conflicting candidates MUST follow explicit authority rules. A conflict not
ordered by validated provenance MUST be retained for review and MUST block that
entire batch from sealing; filesystem order and migration time MUST NOT resolve
it.

#### Scenario: A sparse metric has two measurements in one year

- GIVEN the baseline contains only two valid VO2 max dates in its declared scope
- WHEN completeness is validated
- THEN both measurements are accepted without inventing values for other dates.

#### Scenario: A declared identity is authoritatively absent

- GIVEN the manifest explicitly reconciles one metric and date as having no value
- WHEN the approved batch seals
- THEN its absence tombstone removes a lower-authority current value without storing zero.

### Requirement: Keep Replay Non-Authoritative

A completed replay MUST record one receipt and validation evidence for its
existing logical import, but MUST NOT advance the current projection or live
freshness. Repeating the same payload within one replay operation MUST remain
idempotent and MUST NOT duplicate that operation's receipt or evidence. Backfill
or reconciliation authority MUST be explicit at the trusted entry point and MUST
NOT be inferred merely because a payload is old.

#### Scenario: A replay contains a correction

- GIVEN a replayed payload differs from the selected current value
- WHEN replay completes successfully
- THEN its evidence remains traceable but the current value is unchanged.

### Requirement: Preserve Batch Auditability

A sealed batch MUST retain its manifest identity, verification outcome, source
hash references, import receipts, produced versions, promotion time, authority
sequence, and operator approval without copying raw health values into ordinary
logs. A failed or abandoned batch MUST retain its receipts, pending versions,
validation outcome, and lineage. Cleanup MAY remove only disposable staging
artifacts proven not to be the sole copy of source or audit evidence.

#### Scenario: A sealed baseline is inspected

- GIVEN the historical baseline has been promoted
- WHEN its audit record is read
- THEN its scope, hashes, importer version, receipts, counts, and seal outcome can be explained without exposing raw values.
