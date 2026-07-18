# Authoritative Daily Summary Storage Specification

## Purpose

Define SQLite as the transactional source of truth for private daily health
summaries, their provenance, version history, and current selection.

## Requirements

### Requirement: Persist The Complete Operational Record In SQLite

SQLite MUST persist the initial owner, logical imports, concrete import receipts,
normalized daily-summary versions, current-version projection, and historical
reconciliation state. An operational read MUST be reconstructable from SQLite
without reading raw archives, Parquet, or filesystem order.

An accepted write MUST commit its receipt, valid versions, provenance, and current
projection changes in one transaction. A failed transaction MUST expose none of
those changes to readers. Superseded, rejected, and non-current records MUST
remain traceable and MUST NOT be deleted by current-version selection.

#### Scenario: A transaction fails during current selection

- GIVEN a receipt has valid normalized versions but its SQLite transaction fails
- WHEN the current projection is read
- THEN neither the receipt versions nor any partial projection update is visible.

#### Scenario: A version is superseded

- GIVEN two authoritative versions exist for one daily identity
- WHEN the later permitted version becomes current
- THEN the earlier version remains stored with its receipt and import lineage.

### Requirement: Use Owner-Scoped Local-Date Identity

Every daily-summary version MUST use `user_id + metric + local_date` as its
logical identity. The initial owner MUST be assigned from trusted server
configuration and MUST NOT be accepted from payloads, headers, query parameters,
or command arguments intended as untrusted data.

The dataset timezone MUST be persisted as `Europe/Madrid`. Startup with a
conflicting timezone MUST fail before reads or writes unless an explicit,
reversible timezone migration has completed. Local dates and day completeness
MUST NOT depend on the process, browser, or UTC calendar date.

#### Scenario: Runtime timezone conflicts with persisted identity

- GIVEN the database is pinned to `Europe/Madrid`
- WHEN startup requests another dataset timezone
- THEN startup fails before serving health data or accepting ingestion.

### Requirement: Separate Logical Imports From Receipts

A logical import MUST be uniquely identified by owner and SHA-256 of the exact
payload bytes. A later authenticated receipt of those bytes MUST reference the
same logical import. It MUST NOT create another version when trusted kind,
parser/contract version, completeness, and normalized content are unchanged.

Each relevant receipt MUST retain its own server-assigned kind, timestamps,
parser and contract versions, validation result, source metadata, and sanitized
errors. Receipt identity MUST NOT be collapsed into logical payload identity.
Each metric version MUST identify the concrete receipt that produced it. A new
receipt MUST create a version for the same logical import when trusted receipt
kind, parser/contract version, completeness, or normalized content changes;
shared normalized content MAY be deduplicated without changing that receipt
lineage.

#### Scenario: An exact payload is received twice

- GIVEN one owner already has a logical import for a payload hash
- WHEN the same authenticated payload is retried with unchanged trusted context
- THEN one logical import remains and the new receipt creates neither a duplicate version nor an authority sequence.

### Requirement: Select Current Versions By Validated Authority

Only valid versions from an authority-bearing live receipt or sealed batch MUST
be eligible for the current projection. Replay and pending receipts MUST remain
non-authoritative. The store MUST assign one strictly increasing trusted
authority sequence per owner when a live receipt produces at least one new
authoritative version or a verified batch seals. A no-op retry MUST NOT allocate
an authority sequence. A batch shares one sequence and replaces eligible
identities in its declared scope; a later permitted live sequence MAY replace
those versions.

For each identity, the eligible candidate with the greatest authority sequence
MUST become current, except that a `complete` current version MUST NOT regress to
`partial` or `unknown`. Among incomplete candidates, the greatest sequence wins.
Migration reconstruction MUST preserve the original authority identity and order
and MUST NOT assign new live authority merely because it runs later.

An unresolved conflict within one authority operation MUST be recorded for
review and MUST NOT update the identity. Filesystem order, migration time, a
free-form identifier, and arbitrary SQL row order MUST NOT break ties. Invalid
candidates MUST NOT replace the last valid current version.

A sealed batch MAY assert authoritative absence only for an identity explicitly
declared reconciled by its manifest. Sealing that absence MUST store a traceable
tombstone at the batch authority sequence and MUST remove a lower-sequence value
from the current projection. Mere omission MUST NOT create a tombstone. Sparse
metrics MUST use explicit identities and MUST NOT infer absence for every date in
a temporal range.

Projection reconstruction MUST rank value versions and tombstones together by
the same authority rules. A selected tombstone MUST remain the current projection
row while operational reads omit its value; rebuilding MUST NOT fall back to a
lower-sequence value.

#### Scenario: A replay contains a newer value

- GIVEN a replay receipt contains a valid value newer than the current version
- WHEN the current projection is evaluated
- THEN the replay remains traceable but does not become current.

#### Scenario: Authority cannot order a conflict

- GIVEN two valid candidates conflict without a defined authority ordering
- WHEN selection runs
- THEN the existing current value remains and the conflict is marked for review.

#### Scenario: A sealed correction is followed by live data

- GIVEN a sealed batch replaced an identity and a later permitted live receipt has a greater authority sequence
- WHEN current selection runs
- THEN the later live version becomes current unless it would regress complete data to incomplete.

#### Scenario: A sealed batch asserts an identity is absent

- GIVEN a lower-sequence current value exists and the approved manifest explicitly reconciles that identity as missing
- WHEN the batch seals
- THEN a traceable absence tombstone replaces the value without inventing a zero.

#### Scenario: Current projection is rebuilt after an absence

- GIVEN a tombstone has greater authority than an older value for one identity
- WHEN `metric_current` is reconstructed from version history
- THEN the tombstone remains selected and the older value is not resurrected.

### Requirement: Preserve Metric Shape And Unit Semantics

Each selected daily version MUST keep its value, source unit, canonical unit,
structured details, completeness, and provenance aligned to the same receipt.
Every enabled metric MUST declare its accepted source units, canonical unit,
daily-summary shape, required details, and conversion before it can produce a
version. Missing, unknown, non-finite, or dimensionally incompatible units MUST
make the candidate invalid; the system MUST NOT relabel or silently pass through
its numeric value.

At minimum, the persisted contract MUST convert `kJ` to `kcal`, metres to
kilometres, `hr` to `h`, `count/min` to `bpm`, and fractional oxygen values to
percent where the metric declares those source units. A total or scalar `qty`, a
heart-rate `Min`/`Avg`/`Max` composite, and sleep value and stage details MUST
remain distinct daily shapes. One generic average or arbitrary-row operation
MUST NOT combine versions or supply units and details. Missing sparse dates MUST
remain absent rather than becoming interpolated values or zeros.

#### Scenario: A daily total has multiple versions

- GIVEN multiple step totals exist for one local date
- WHEN that date is read
- THEN exactly one selected total, unit, completeness, and provenance are returned without averaging versions.

#### Scenario: A unit is incompatible

- GIVEN a candidate has an undeclared or dimensionally incompatible unit
- WHEN it is normalized
- THEN it cannot become current and the previous valid version remains available.
