# Legacy Evidence Preservation Specification

## Purpose

Preserve the raw, metadata, and Parquet evidence needed to audit and recover the
storage migration without exposing private health data.

## Requirements

### Requirement: Keep Legacy Sources Immutable Through Migration

The legacy raw archives, metadata SQLite database, and Parquet artifacts MUST be
treated as immutable migration inputs. Their source hashes MUST be captured
before candidate construction and MUST remain unchanged through migration,
semantic verification, cutover, and the initial rollback window.

After writers drain, metadata SQLite evidence MUST be captured with the SQLite
online backup API so the frozen copy includes every committed WAL transaction.
The original database and WAL file inventory MUST also be recorded. Hashing or
archiving the live main database file alone MUST NOT qualify as a consistent
source snapshot.

The candidate SQLite database MUST have its own independently verified hashes.
Candidate changes MUST NOT be mistaken for mutations of legacy source evidence.
No migration or rollback step MAY delete, compact, rewrite, superficially
anonymize, or regenerate legacy evidence in place.

#### Scenario: Candidate verification completes

- GIVEN the candidate has its own final database hash
- WHEN source integrity is checked
- THEN each legacy source hash still matches its pre-migration value independently of the candidate hash.

### Requirement: Preserve Known Gaps Without Inventing Provenance

Previously pruned raw payloads, dangling paths, first-occurrence-only event
lineage, and ambiguous Parquet rows MUST remain explicit limitations. Migration
MUST NOT claim those gaps are reconstructable from SQLite or infer occurrence,
completeness, authority, or correction order that the surviving evidence cannot
prove.

The sealed reconciled baseline MAY establish new authoritative current versions,
but MUST NOT rewrite the meaning or provenance of incomplete legacy evidence.

#### Scenario: A legacy raw payload was pruned

- GIVEN SQLite and Parquet retain part of an import whose raw artifact is absent
- WHEN migration records its legacy evidence
- THEN the gap remains explicit and is not presented as a fully reconstructable receipt.

### Requirement: Prevent Automatic Loss Of Required Evidence

Automatic raw-payload pruning MUST be disabled before retained receipts depend on
raw evidence for audit, migration, or rollback. Any future retention policy MUST
be an explicit reversible change that preserves the evidence required to explain
every authoritative current version.

Orphan cleanup MAY remove only artifacts proven never to have belonged to a
committed receipt. It MUST NOT infer orphan status from age, an unreadable
Parquet scan, or a dangling legacy path alone.

#### Scenario: A retained artifact reaches the old age limit

- GIVEN raw evidence belongs to a committed authoritative receipt
- WHEN the previous automatic retention interval elapses
- THEN the artifact remains preserved.

### Requirement: Archive Only After Verified Recovery

Legacy evidence MAY leave operational storage only after the rollback window is
closed and an encrypted archive has a canonical manifest, integrity verification,
documented key custody, and a successful isolated restore. The restore MUST prove
that files, hashes, the WAL-consistent frozen SQLite backup, schema metadata, and
audit relationships are recoverable.

Archive failure or unavailable decryption material MUST block removal from
operational storage. Archival MUST NOT imply that legacy Parquet can be rebuilt
from the new SQLite store when pre-baseline evidence was not migrated.

#### Scenario: An encrypted archive has not been restored

- GIVEN archive creation and hash verification succeeded
- WHEN operational cleanup is considered before an isolated restore
- THEN every legacy artifact remains in operational storage.

### Requirement: Keep Health Evidence Private

Real health payloads, values, filenames, paths, hashes, manifests, comparisons,
backups, and restore reports MUST remain in the private environment. They MUST
NOT enter Git, CI, container images, public logs, screenshots, telemetry, or
external APIs. Public tests and documentation MUST use only minimal synthetic
fixtures and temporary storage.

Diagnostics MUST expose sanitized identifiers and counts only when needed and
MUST NOT include complete credentials or raw health values.

#### Scenario: Migration verification fails

- GIVEN a private semantic comparison finds a mismatched health value
- WHEN diagnostics are emitted
- THEN public output identifies the check without printing the real value, payload, path, or source hash.
