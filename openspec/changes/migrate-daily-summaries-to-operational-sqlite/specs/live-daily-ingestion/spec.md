# Live Daily Ingestion Specification

## Purpose

Define the validated daily automation contract, partial-acceptance boundary, and
live freshness semantics for `/v1/ingest`.

## Requirements

### Requirement: Accept Only The Trusted Live Contract

`POST /v1/ingest` MUST continue to require the existing configured bearer
credential and MUST accept live data only when it validates as the configured
Health Auto Export `Default` automation using JSON v2, summarized data, daily
grouping, the pinned owner, and `Europe/Madrid` date semantics.

The server MUST derive authority and owner from its trusted entry point and
configuration. A payload, header, filename, or query parameter MUST NOT grant a
receipt reconciliation, backfill, or replay authority. A validly authenticated
but mismatching source contract MUST be rejected before producing versions.

#### Scenario: A caller claims reconciliation authority

- GIVEN an authenticated live request includes a header naming reconciliation
- WHEN the request is classified
- THEN it remains a live request and the untrusted classification is ignored.

#### Scenario: The automation contract does not match

- GIVEN an authenticated payload is not JSON v2 summarized by day for `Default`
- WHEN it reaches the live endpoint
- THEN the receipt is rejected and creates no metric version.

### Requirement: Assign Import Kinds Only At Trusted Entry Points

Live, reconciliation, backfill, and replay classifications MUST be assigned only
by trusted server entry points; replay MUST remain non-authoritative. The live
HTTP route MUST NOT expose a mode that grants another classification. Private
operator workflows MUST use separate trusted entry points not reachable by
ordinary ingestion requests.

#### Scenario: An ordinary ingestion request is valid

- GIVEN a request satisfies the live automation contract
- WHEN the server records its receipt
- THEN the server assigns `live` without accepting a caller-selected kind.

### Requirement: Bound Rejection And Partial Acceptance

Authentication MUST complete before body consumption. The endpoint MUST enforce
declared and actual byte limits while streaming and MUST stop reading at the
limit. Unauthenticated or oversized bodies MUST create neither receipt nor raw
evidence.

After authentication and bounded body admission, invalid JSON, envelope, or
source contract MUST create only a sanitized rejected receipt containing the
payload hash, byte count, and reason; rejected raw content MUST NOT be retained.
After envelope validation, each metric/date candidate MUST be validated
independently for shape, finite values, unit, local date, and permitted live
window.

A receipt with at least one valid candidate and at least one metric-level error
MUST atomically commit its valid candidates and retained raw evidence as
`degraded`. Invalid candidates MUST NOT update current versions. Sanitized error
metadata MUST identify affected metrics and dates without logging raw values,
credentials, or payload content.

An envelope- and source-contract-valid receipt with no valid candidate MUST
atomically retain its raw evidence and sanitized validation outcome as
`rejected`, MUST create no version, and MUST return HTTP 422. It MUST advance
authenticated freshness only; it MUST NOT advance committed, clean, or
complete-date freshness.

#### Scenario: One metric in a receipt is invalid

- GIVEN a live receipt contains one valid step summary and one invalid heart-rate summary
- WHEN candidate validation completes
- THEN the valid step version commits, heart rate remains unchanged, and the receipt is degraded.

#### Scenario: The envelope is invalid

- GIVEN a body cannot establish the required JSON v2 daily envelope
- WHEN ingestion evaluates it
- THEN no candidate from that body is normalized or committed.

### Requirement: Enforce The Live Date Window And Completeness

A live receipt MAY produce versions only for the current and immediately previous
`Europe/Madrid` local dates at the trusted server receipt instant. A future date
or a date older than yesterday MUST be an invalid metric/date candidate. Valid
siblings MUST commit as a degraded receipt; a receipt with no candidate in the
permitted window MUST be rejected without modifying current versions.
Historical data MUST use the private backfill workflow.

Each source row MUST contain either an offset-aware timestamp or a date-only token
explicitly permitted by its metric contract for an already grouped daily
summary. An instant MUST be converted to `Europe/Madrid` before deriving
`local_date`; its declared offset MUST disambiguate an autumn fold. A permitted
date-only token MUST be interpreted directly as a Madrid calendar date and MUST
NOT be treated as midnight UTC. Any other missing, nonexistent, or invalid
timestamp/date MUST invalidate that candidate.

The current local date MUST be stored as `partial`. Yesterday MUST be stored as
`complete` only when validated automation provenance proves the summary was
generated after its closing Madrid midnight; otherwise it MUST be `unknown` and
MUST NOT replace a complete version. Exact receipt or source timestamps establish
date placement but MUST NOT alone prove closure. Elapsed wall-clock time MUST NOT
promote a persisted version.

#### Scenario: Today is ingested before midnight

- GIVEN a valid live summary belongs to the current configured local date
- WHEN it commits
- THEN its completeness is partial until a newer authoritative version replaces it.

#### Scenario: Midnight behavior is ambiguous

- GIVEN the installed automation does not prove whether a boundary summary is closed
- WHEN that candidate is stored
- THEN its completeness is unknown rather than inferred from UTC or process time.

#### Scenario: A historical date reaches the live route

- GIVEN an otherwise valid candidate is older than yesterday in `Europe/Madrid`
- WHEN it is the only candidate in the live receipt
- THEN the receipt is rejected and the candidate can enter only through private backfill.

#### Scenario: A daily sleep summary uses a date-only token

- GIVEN the sleep metric contract permits date-only daily identity `2026-02-10`
- WHEN the summary is normalized
- THEN its local date remains `2026-02-10` in Madrid without conversion from UTC.

### Requirement: Commit Raw Evidence And SQLite State Safely

Before any receipt that retains raw evidence commits operational state, that
evidence MUST be durably staged, hashed, and published to a unique verified path.
SQLite MUST reference only that durable artifact. A failure before the SQLite
commit MUST leave no visible receipt or version; orphan cleanup MUST NOT treat
staged or unreferenced files as accepted health history.

#### Scenario: Power fails after raw publication

- GIVEN raw evidence is durable but the SQLite transaction did not commit
- WHEN the application restarts
- THEN the artifact contributes no metric value and can be identified safely as orphaned evidence.

### Requirement: Report Live Freshness Without Conflation

The operational store MUST distinguish the latest authenticated live receipt,
latest committed live receipt, latest clean live receipt, and latest complete
local date processed. Every authenticated, bounded request admitted far enough to
record a receipt MUST advance authenticated freshness, including malformed,
contract-invalid, all-invalid, and retried rejected requests. Every degraded live
receipt MUST also advance committed freshness but MUST NOT advance clean
freshness. A clean committed live receipt MUST advance all three receipt
freshness fields and MUST advance the complete-date field only when it
successfully processes a complete local date.

Reconciliation, backfill, replay, metric coverage, and sparse-metric recency MUST
NOT advance live automation freshness. An exact payload retry MUST update the
freshness fields applicable to its outcome without duplicating its logical
import. It MUST create no new version or authority sequence when trusted context
is unchanged, and MUST create a receipt-linked version when the same payload now
proves different completeness. A successfully committed duplicate receipt MUST
update committed freshness and, when clean, clean freshness.

#### Scenario: A reconciliation finishes after live ingestion

- GIVEN the latest live receipt predates a successful reconciliation
- WHEN freshness is read
- THEN every live freshness field remains based only on live receipts.

#### Scenario: An exact live retry is received

- GIVEN a valid payload already belongs to one logical import
- WHEN the authenticated automation retries it with unchanged trusted context
- THEN receipt freshness advances while version count and authority sequence remain unchanged.

### Requirement: Preserve The Existing Ingestion HTTP Contract

The route, shared bearer authentication scheme, and existing response fields MUST
remain compatible. The same configured bearer MUST continue to authorize
`POST /v1/ingest`, `GET /v1/status`, and `GET /v1/metrics/{metric}`; missing or
incorrect credentials MUST remain unauthorized, and `/health` MUST remain
public. Credential separation MUST NOT occur in this storage migration.

A receipt whose current validation result is accepted or degraded, including an
exact payload reuse, MUST return HTTP 200 with
`import_id`, `duplicate_request`, `received_points`, `inserted_points`, and
`payload_sha256`. Missing authentication MUST remain HTTP 401, oversized content
HTTP 413, invalid JSON HTTP 400, and an invalid envelope or source contract HTTP
422. Degraded success MUST retain the existing success fields and MAY add only
backward-compatible integrity metadata.

Current validation MUST determine every retry outcome regardless of an earlier
receipt status. A currently rejected exact retry MUST reference the same logical
import, record a new sanitized rejected receipt, advance authenticated freshness,
and return its HTTP 400 or 422 class and raw-retention outcome. It MUST NOT return
the HTTP 200 duplicate shape or create a version.

#### Scenario: A still-valid exact request is retried

- GIVEN a client repeats an accepted payload that remains valid in the current contract and date window
- WHEN the endpoint returns its duplicate result
- THEN the HTTP status and existing five success fields remain compatible.

#### Scenario: A rejected request is retried

- GIVEN an authenticated payload was previously rejected as invalid JSON
- WHEN the same bytes are submitted again
- THEN the logical import is reused, a rejected receipt is recorded, and HTTP 400 is returned without raw retention or a version.

#### Scenario: The shared bearer reads status

- GIVEN the configured bearer currently authorizes ingestion and protected reads
- WHEN it requests `/v1/status` after migration
- THEN the request remains authorized while a missing or incorrect bearer remains rejected.
