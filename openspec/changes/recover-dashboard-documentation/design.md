# Design: Recover Dashboard Documentation

## Context And Boundary

This is a documentation design, not an implementation design approval. The
current branch truth remains backend-only: FastAPI/Uvicorn provides ingestion
and reads through the existing bearer boundary; metadata is in SQLite, metric
values are in Parquet, and operational reads use DuckDB. Phase 3 has introduced
the future operational SQLite schema, but the metric contracts, persistence,
current reads, reconciliation, cutover, and readiness work remain incomplete.
There is no shipped React application, browser session, Compose manifest, or
Raspberry Pi dashboard release in `main`.

The accepted ADRs describe a target. This design consolidates that target for a
single person and fixed server-side owner without claiming it exists, changing
the SQLite migration, or authorizing implementation. It is bounded by the four
specifications in this change and ADRs 0001-0006.

## Dependency Gates

Dashboard documentation may proceed independently, but implementation and use
have two hard gates:

| Gate | SQLite phases | Required outcome |
|---|---:|---|
| Operational prerequisites | 4-10 | Registry contracts, canonical shapes and units, immutable versions, deterministic current selection, ingestion lineage, and indexed owner/date reads are authoritative in operational SQLite |
| Dashboard read contract | Separate product change | Defines and implements the atomic dashboard response, including freshness, provenance, correction acceptance time, completeness, gaps, and integrity fields |
| Publication and routine migrated-history use | 11-17 | Reconciliation, semantic equivalence, verified backup/restore, reversible cutover, recovery boundary, and readiness rehearsal are complete |

A failed, missing, stale, timezone-mismatched, or contract-mismatched readiness
state blocks dashboard reads. Completing migration phases does not imply that a
dashboard API or its freshness/provenance fields exist. The release catalog is
derived from completed registry entries; “25” is an expected gate assertion, not
a parallel source of identifiers. There is no temporary fallback to raw archives,
legacy Parquet, DuckDB, pending batches, or replay evidence. This design does not
duplicate or revise the migration's schema, authority, or cutover decisions.

## Target Architecture

The target is one modular FastAPI application deployable with explicit
in-process responsibilities:

```text
browser
  -> TLS reverse proxy (publication target)
  -> FastAPI application
       - browser authentication and server-side session validation
       - private dashboard read orchestration
       - operational query adapter
       - ingestion boundary with a distinct credential
       - static React asset serving
  -> authoritative operational SQLite
```

Authentication, ingestion, private reads, query adaptation, and static serving
are modules with separately testable boundaries, but not network services. The
SPA calls only its origin. No BFF, internal HTTP request, dashboard application
service, second application container, or browser-visible ingestion credential
is introduced. The operational storage layer remains the sole owner of metric
authority and the single write transaction boundary.

The read module translates the completed operational contract into a bounded
dashboard representation. It may format or omit private internals, but it may
not select versions, reaggregate daily values, convert canonical meaning,
reconstruct provenance, infer missingness, or open analytical or raw storage.
Exact routes and response schemas belong to the required dashboard read-contract
product change.

## Decisions

### Operational Read Contract

Every status, overview metric, detail, and quality indicator displayed together
is derived from one named coherent SQLite read snapshot for the fixed owner and
requested `Europe/Madrid` local-date range. Values and structured
details, canonical units, completeness, freshness, current-version identity,
correction state, bounded provenance, coverage, tombstones, and known integrity
state all refer to that snapshot. Results from separate snapshots or versions
must not be combined as one observation or overview.

The server-owned Madrid calendar determines daily identity and range boundaries.
Browser locale may alter display formatting only. It cannot shift a day, change
unit semantics, choose a version, or revise completeness. Canonical units and
metric shapes come from the completed operational registry; display labels and
precision come from a separate presentation catalog and never become data
authority.

The normal view exposes the selected current value. If that version supersedes
an earlier accepted version for the same owner, metric, and Madrid local date,
the view identifies a correction. Its correction date is the authoritative
server acceptance timestamp of the selected correcting version, not the metric
date, source time, filename time, browser time, filesystem time, or display date.
That timestamp and a bounded import-origin label come from the same snapshot. The
view does not expose raw payloads, private paths, hashes,
manifests, or complete version history by default. A current tombstone is
absence, not zero, and an older value is not resurrected.

Every data-bearing view distinguishes loading, verified success, partial,
empty, and error states. Useful verified values may remain in a partial result
only with the snapshot's affected coverage and integrity limitation. Errors are
not converted to empty results; stale values are not presented as current after
a failed refresh. Gaps remain gaps: no interpolation, zero filling, connected
discontinuity, or invented cause. Known legitimate absence, sparse collection,
and ingestion or processing failure are distinguished only when the operational
contract does so; otherwise the UI states uncertainty.

Coverage uses every eligible Madrid local date in the requested range, including
missing leading and trailing dates, rather than clipping to observed edges.
Sparse dates use elapsed calendar-time geometry instead of equal categorical
spacing.

### Product And Presentation Scope

The first release has overview, metric navigation, and metric-detail journeys
for exactly the 25 identifiers admitted by the completed operational registry.
The presentation catalog has one entry per admitted identifier and may contain
labels, grouping, descriptive education, display precision, accessibility text,
provenance labels, limitations, and display rules. It cannot add a metric or
override operational shapes, units, sparse semantics, completeness, or current
selection.

The default range prioritizes the latest 12 months. This is a reversible query
and presentation choice, not retention: older history, versions, corrections,
and raw evidence remain governed by the storage migration and remain preserved.

React, Vite, Recharts, conventional CSS, npm, and one committed npm lockfile are
the implementation target from ADR 0002. TypeScript may be adopted incrementally.
No package versions, manifest, lockfile, generated bundle, or source structure
are created by this change. Prototype colors, typography, grouping, and
interaction concepts may be selectively reimplemented only when they remain
truthful for partial and sparse data, responsive, accessible, and compatible
with this architecture. Historical code is not a source artifact.

Essential information is available without perceiving a chart. Each chart has
a textual equivalent covering period, unit, coverage, meaningful values, gaps,
corrections, and limitations, including structured details such as heart-rate
extrema and sleep stages. Authentication, logout, navigation, range selection,
status, and data views remain keyboard operable at mobile and desktop sizes,
with visible logical focus, programmatic names, non-color status cues, and
assistive-technology announcements that do not move focus unexpectedly.

### Educational Boundary

Content may factually explain a metric, source, collection method, period, unit,
coverage, provenance class, and limitations. It must not diagnose, advise,
classify risk, suggest treatment, identify warning signs, make causal claims, or
label values normal or abnormal. Descriptive comparisons cannot imply healthy,
safe, expected, or pathological status.

ADR 0005 governs any future interpretation. Such work requires a separate
approved proposal and current governance evidence; this design grants no
authorization. Missing, stale, conflicting, withdrawn, or uncertain eligibility
fails closed by suppressing interpretation and retaining descriptive data only.

### Browser Privacy And Sessions

The web credential and server-validated browser session are cryptographically
and operationally distinct from the machine ingestion credential. Authorization
always resolves the fixed owner on the server; the browser cannot select an
owner, account, profile, or role. Every response containing health values,
status, provenance, corrections, coverage, or other private operational state
requires a currently valid session before SQLite is queried. Static assets, the
minimum authentication flow, and the minimal public health check contain no
private state or readiness topology.

The session has finite server-enforced expiry. Its same-origin cookie is
`HttpOnly` and `SameSite=Strict`, and is `Secure` outside loopback. Logout revokes the
server-side session and expires the cookie; replay remains invalid. Expiry,
revocation, restart, secret rotation, lost validity state, malformed state, and
incompatible session versions fail closed. State-changing authentication flows
enforce same-origin and CSRF protections appropriate to their cookie semantics.
The login boundary admits only a bounded body: actual bytes and declared length
must both fit the limit, the media type and decoded JSON must be accepted, the
top-level shape must be exactly the login object, and the password must satisfy
an explicit byte-length bound before password verification begins. Malformed,
oversized, chunked-over-limit, duplicate/unknown-field, and non-string inputs are
rejected without expensive secret work. Password verification, concurrent login
attempts, per-source rate state, and live sessions each have independently
bounded capacity. Saturation or unavailable limiter/session state rejects new
work; it never bypasses a check or evicts an otherwise valid unexpired session.
Credentials use a one-way verifier designed for password hashing, and comparison
avoids secret-dependent early exit. Successful authentication creates a fresh
cryptographically unpredictable session identifier; supplied or pre-authentication
identifiers are never retained, and future privilege changes rotate the identifier.

The cookie contract verifies `SameSite=Strict` on every
issuance and deletion path. `SameSite` is defense in depth, not the CSRF control:
every unsafe cookie-authenticated action, including login and logout where
applicable, validates an allowlisted same-origin `Origin` and rejects missing,
opaque, malformed, cross-origin, or forwarded-forged origins before mutation.
Safe private reads remain non-mutating. Exact limits and durations are chosen by
the later implementation change, but their bounded and fail-closed behavior is
not deferred.

The transport decision starts from the socket peer. Forwarded client, host,
scheme, and origin information is accepted only when the immediate socket peer
matches an explicit trusted-proxy allowlist; headers from every other peer are
ignored or rejected. Trust is not inferred from a forwarded client address,
private address syntax, hostname, or header presence. Outside loopback, any
request that would authenticate, set a session, or return private state is
rejected unless the trusted transport context proves HTTPS.

Health data, provenance, correction details, or session material are not stored
in browser storage, service-worker caches, URLs, or client logs and are not sent
to telemetry, analytics, error reporting, advertising, CDNs, or other external
processors by default. Private responses prohibit shared or persistent caching;
static assets may be cached only when they contain no private state. Browser and
server errors are sanitized and disclose neither credentials nor private health
or provenance evidence.

Client authorization state is an atomic privacy boundary. `pagehide` performs a
synchronous in-memory private lock before the page can enter the back-forward
cache: clear rendered/private model state, invalidate the active request
generation, and prevent commits. `pageshow`, including a persisted BFCache
restore, revalidates the session before unlocking or issuing private reads. A
`401`, logout, or local expiry performs one atomic transition that locks the UI,
clears all private state, aborts every in-flight private request, and advances
the generation. A response may commit only if its request generation is still
current and authorization remains valid; late success or error responses from a
prior generation are discarded.

Changing metric, range, area, or snapshot selection also aborts superseded work
or advances the generation. A valid response for an old selection cannot commit
after the active selection changes.

The client validates the complete response boundary before committing any of it:
metric identity, snapshot/current-version coherence, timezone, local dates,
requested range, canonical unit, finite numeric values, gap and completeness
semantics, and metric-specific structured details. Unknown, missing,
out-of-range, non-finite, duplicate, internally inconsistent, or shape-invalid
content rejects the entire response. The client does not drop bad points, infer
details, coerce units, clip dates, or otherwise partially repair a response.

### Deployment And Release Target

ADR 0006 defines the durable publication boundary and clarifies the historical
prototype context in ADR 0001 and ADR 0003 without rewriting those records.
Docker Compose on the single Raspberry Pi host is a future deployment target,
not current state. The target topology contains one application replica with one
Uvicorn worker because operational SQLite assumes one process owning writes. A
dedicated Caddy reverse-proxy container may terminate TLS, but it is not a BFF
and does not create another application deployable. More workers or replicas are
excluded until measured need and a storage/session model supporting their
concurrency are approved.

Authenticated use outside loopback is blocked until Caddy TLS, origin handling,
secure cookies, private-route denial, authentication, expiry, logout, and restart
behavior pass the release gate. Compose, Caddy configuration, certificates,
secrets, image definitions, and volumes are future implementation artifacts and
are not created or implied to exist here.

The future build produces static SPA assets and includes them in the same
immutable application image as FastAPI. Dependency installation uses npm and the
committed lockfile. CI must verify repository checks, frontend tests, production
build reproducibility, synthetic integration behavior, image construction, and
security/privacy invariants. CI is necessary but cannot establish target-host
compatibility or authorize publication.

Before LAN publication, the maintainer runs a private native smoke on the target
Raspberry Pi ARM64 host using the exact immutable release-stack identity. That
identity binds the application and proxy image digests; effective application,
proxy, Compose, trusted-proxy, origin, session-security, bind, and firewall
configuration digests; and certificate/trust-state identity. Changing any bound
component invalidates prior evidence. The smoke uses the exact stack intended to
be released and minimal synthetic data only. It covers startup, minimal health,
authentication denial and success, expiry and logout, private reads, static
serving, empty/partial/error presentation, TLS, and restart. Emulation, another
architecture, a mutable tag, a stale result, or CI cannot substitute for this
gate. Failure or digest mismatch blocks publication. No real data, identifiable
screenshot, secret, path, hash, manifest, or backup is release evidence.

Startup validates the Vite manifest and every referenced entry, import, CSS, and
asset path before becoming ready. Missing, malformed, escaping, non-regular, or
unreadable manifest/assets fail startup; development serving and filesystem
guessing are forbidden. API routes and `/health` take precedence over static
routing. SPA fallback serves the entry document only for navigation `GET` or
`HEAD`; API prefixes, asset prefixes, unsupported methods, malformed paths,
encoded or decoded traversal, and missing assets never fall back to the SPA.
The production runtime excludes Node, package managers, source trees, test tools,
and development dependencies.

The proxy and application define explicit Content Security Policy, `nosniff`,
anti-framing, referrer, permissions, and cache policies with no conflicting
duplicate ownership. Authentication and private responses are non-store and
static cache policy follows immutable naming. The minimal public `/health`
response remains non-sensitive and is never shadowed by the SPA.

LAN exposure uses an explicit bind address, host firewall rule, proxy upstream
allowlist, and trusted-proxy allowlist. Release tests prove intended reachability
and negative reachability from disallowed interfaces/peers without recording a
private IP address or hostname. The application runs as a non-root identity with
read-only runtime filesystems except named writable data/temporary locations,
least-capability mounts and secrets, bounded CPU/memory/process/file resources,
and bounded rotating logs that exclude private content.

Backup is online-consistent, not a filesystem copy of a live database. The
runbook enters maintenance, blocks new writers, drains or terminates active
writers, creates and verifies the backup through the database-supported method,
and restores only into an isolated candidate location. Promotion occurs only
after integrity and synthetic checks. A failed upgrade/restore preserves the
failed database and logs for private diagnosis and leaves the last verified data
untouched. A code-only rollback changes immutable stack artifacts but never
restores an older data backup or discards writes accepted by the current schema.
Release evidence binds the backup to the current operational watermark and a
complete restore set: supported SQLite backup/journal output, every referenced
raw or batch artifact, required configuration, recovery-material references, and
integrity metadata. The isolated restore must reach the same watermark and
resolve every reference.

The native Pi baseline records sanitized, reproducible evidence: full immutable
stack identity, hardware model and memory class, test time and server timezone,
synthetic fixture identity, request mix and concurrency, sample count and
warm-up, latency distribution, CPU/memory/disk observations, and compressed/
uncompressed asset sizes. Release thresholds are compared with that measured
baseline rather than asserted from CI or an unspecified device.

Quantified accessibility gates cover a 320 CSS-pixel viewport without essential
horizontal scrolling, 44-by-44 CSS-pixel pointer targets, browser text-only zoom
to 200 percent without loss or overlap, and WCAG contrast for text, controls,
focus, and non-text status indicators. Modal drawers trap focus, make background
content inert, close on Escape, and restore focus to the invoker. Reduced-motion
preferences remove nonessential animation. The accessible chronological table
preserves all essential chart details, and opening/closing a detail returns focus
to the invoking row or control.

## Alternatives Rejected

| Alternative | Reason rejected |
|---|---|
| Restore or cherry-pick the historical dashboard | It predates operational SQLite and carries obsolete BFF, credential, storage, package, and deployment assumptions |
| Separate BFF or dashboard service | Adds network, secret, deployment, and failure boundaries without isolation or measured scaling benefit |
| Browser use of the ingestion API token | Breaks credential separation and exposes a machine write credential to browser surfaces |
| Temporary Parquet/DuckDB dashboard reads | Creates a second operational authority and bypasses migration readiness and rollback guarantees |
| Frontend-owned corrections, units, timezone, or gap inference | Can combine versions, shift Madrid dates, or invent semantics not supported by evidence |
| SSR, global state, or another package workflow by default | No confirmed requirement offsets additional complexity; ADR 0002 retains the smaller SPA target |
| Multiple workers or replicas in the private SQLite phase | Violates the current single-writer/process assumptions without measured need |
| Treat CI as publication approval | It cannot prove native behavior for the exact ARM64 artifact on the target host |

## Risks And Controls

| Risk | Control |
|---|---|
| Target documentation is mistaken for shipped behavior | Keep backend-only current truth prominent and label all dashboard/deployment artifacts as future work |
| UI starts before its dependencies exist | Block on phases 4-10 plus a separate dashboard read contract, and block routine migrated-history use on phases 11-17 |
| A mixed snapshot misstates a correction or provenance | Require one SQLite snapshot and one operationally selected current identity per result |
| Browser timezone or display conversion changes meaning | Preserve Madrid date identity and canonical unit semantics from the server contract |
| Sparse, degraded, or failed data appears normal or complete | Separate states, expose coverage and limitations, and forbid imputation and invented causes |
| Private material leaks through browser or evidence | Same-origin processing, no external telemetry/persistence, sanitized errors, synthetic public evidence only |
| Educational copy becomes clinical guidance | Enforce ADR 0005 and fail closed to factual descriptive content |
| A 12-month default becomes deletion policy | Verify older retained history and evidence are unchanged and remain addressable |
| Release cannot be recovered | Require compatible artifact/data pairs, verified backups, restore evidence, triggers, and post-rollback checks before publication |

## Verification Strategy

Documentation review first verifies traceability from every decision to the
proposal, four specifications, ADRs, and SQLite migration without introducing an
endpoint, table, source claim, or private operation. Later implementation must
provide layered synthetic evidence:

- contract tests for fixed-owner authorization, coherent current snapshots,
  corrections, tombstones, canonical units, Madrid boundaries including DST,
  completeness, freshness, gaps, sparse metrics, and degraded receipts;
- session tests for denial-before-read, expiry, revocation, replay, restart,
  rotation, CSRF, sanitized failures, and ingestion-credential exclusion;
- frontend tests for all 25 catalog mappings, 12-month default without
  retention effects, loading/partial/empty/error states, no invented values,
  keyboard operation, focus, names, announcements, and textual chart equivalents;
- privacy checks for browser persistence, caching, external requests, logs,
  source maps, bundles, fixtures, screenshots, and release evidence;
- build and integration checks for npm lockfile reproducibility, same-origin
  static/private behavior, one application deployable, and immutable image identity;
- private target-host checks for Compose/Caddy/TLS, full release-stack identity,
  native ARM64 smoke and baseline, restart, backup restore, and fallback compatibility.

All repository and CI fixtures are minimal and synthetic. Tests never access the
real data root. Private operational verification emits only sanitized pass/fail
evidence suitable for its intended private location; real values and private
identifiers never become Git or CI evidence.

## Rollout And Rollback

This documentation rolls out as one reviewable PR from current `origin/main`.
Approval establishes a planning baseline only. Implementation is split into
later reviewed work after phases 4-10 and a separate dashboard read-contract
product change; publication remains disabled until phases 11-17 and the full
release-stack native gate pass.

Before any future release, the runbook identifies the current and fallback image
digests, compatible operational SQLite states, configuration and secret
prerequisites, verified backup/restore evidence, rollback triggers, operator
steps, and post-rollback checks. Before the first post-cutover live receipt, the
application and dataset roll back together under the reversible storage-cutover
contract. After that boundary, fallback remains SQLite-compatible and never
remounts stale legacy Parquet as current. Every path preserves raw evidence,
versions, corrections, provenance, and older history.

Documentation rollback is a normal revert of this planning PR. It performs no
database, credential, deployment, or PR operation and does not revive a legacy
dashboard plan as approved architecture.

## File And Artifact Migration

`recover-dashboard-documentation` becomes the forward planning baseline. On
approval, architecture and project-state documentation may be updated in the
same documentation-only delivery to distinguish backend-only current truth from
the target, and legacy dashboard plans may be marked superseded where their
requirements conflict. The active SQLite migration remains authoritative and is
referenced rather than copied or edited by this design.

`modern-health-dashboard`, `publish-health-dashboard-safely`, the historical
branch, and PR #3 remain intact as historical evidence. No commit, source file,
manifest, lockfile, generated asset, deployment file, or private artifact is
cherry-picked, merged, copied, restored, or deleted. PR #3 is not modified,
closed, or merged; that requires a separate maintainer decision. Reusable visual
concepts are reimplemented later from current requirements, never transplanted
with obsolete boundaries.

This documentation delivery creates the `recover-dashboard-documentation`
OpenSpec artifacts, corrects the architecture current-state index, and adds ADR
0006. It changes no runtime files, dependencies, storage artifacts, other
OpenSpec changes, or private operational evidence.
