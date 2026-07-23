# Dashboard Release Baseline Specification

## Purpose

Define the single-deployable delivery, native release gate, rollback, and
supersession boundary for future dashboard work.

## Requirements

### Requirement: Preserve The Modular Monolith Boundary

The React SPA MUST be built as static assets and served from the modular FastAPI
application in one application deployable. Ingestion, browser authentication,
operational reads, and static serving MUST remain explicit in-process modules.
They MUST NOT communicate through an internal HTTP BFF or require a separate
dashboard application service, network hop, container, or copy of the ingestion
credential.

Frontend dependencies MUST use npm and one committed npm lockfile. The release
MUST NOT add pnpm, a pnpm lockfile, or parallel package-manager workflows.
Package versions and generated assets remain implementation concerns and MUST NOT
be added by this documentation change.

#### Scenario: A dashboard read is designed

- GIVEN the SPA needs private operational data
- WHEN the module boundary is selected
- THEN it uses the same-origin modular application rather than a BFF or inter-service HTTP request.

#### Scenario: Frontend dependencies are installed

- GIVEN a later implementation introduces the frontend manifest
- WHEN dependency installation is made reproducible
- THEN npm uses the committed npm lockfile and no second package-manager lockfile is created.

### Requirement: Gate LAN Publication On Reproducible Native Evidence

The target single-host release MUST use Docker Compose when the accepted Compose
deployment is implemented. Compose MAY include a dedicated TLS reverse proxy,
but MUST contain only one application deployable for API and dashboard behavior.
Use of the authenticated browser session outside loopback MUST be blocked until
TLS, origin, secure-cookie, private-route, and logout behavior pass verification.

Before LAN publication, the maintainer MUST run a private smoke test natively on
the target Raspberry Pi ARM64 host using the exact immutable release-stack
identity intended for release. That identity MUST bind the application and proxy
image digests; effective application, proxy, Compose, trusted-proxy, origin,
session-security, bind, and firewall configuration digests; and the effective
certificate/trust-state identity. The smoke MUST use only synthetic data and MUST
verify startup, health, authentication denial and success, session expiry/logout,
private reads, static serving, empty/partial/error presentation, TLS behavior,
and restart behavior without exposing secrets or real health evidence.

CI MUST pass and is necessary release evidence, but CI, emulation, mutable tags,
or a smoke on another architecture MUST NOT replace the native exact-digest gate.
A failed, incomplete, stale, or digest-mismatched native smoke MUST block LAN
publication.

#### Scenario: CI passes without a native smoke

- GIVEN all repository checks pass in CI
- WHEN no successful smoke exists for the exact ARM64 release-stack identity on the target Pi
- THEN LAN publication remains blocked.

#### Scenario: The smoke uses a mutable tag

- GIVEN a native Pi smoke passes against an image tag
- WHEN the immutable digest cannot be matched to the release candidate
- THEN the evidence is insufficient and publication remains blocked.

#### Scenario: A bound release component changes

- GIVEN native evidence passed for one full release-stack identity
- WHEN any bound image, configuration, allowlist, bind/firewall rule, session
  security setting, or certificate/trust state changes
- THEN that evidence no longer authorizes publication even if the application digest is unchanged.

#### Scenario: TLS is absent on the LAN URL

- GIVEN the browser session would be used outside loopback
- WHEN TLS and secure-cookie behavior have not passed verification
- THEN authenticated LAN access remains disabled.

### Requirement: Define Release Rollback Before Publication

Each future dashboard release MUST identify the exact current and fallback
application artifacts, compatible operational SQLite state, configuration and
secret prerequisites, backup/restore evidence, rollback trigger, operator steps,
and post-rollback verification before publication.

Rollback MUST preserve raw evidence, every accepted version, corrections,
provenance, and history. Before the first post-cutover live receipt, storage
rollback MUST follow the reversible-cutover contract and switch the verified
application/dataset pair together. After that receipt boundary, application
rollback MUST remain SQLite-compatible and MUST NOT remount stale legacy
Parquet-backed data as current.

Documentation rollback MAY revert this planning change but MUST NOT mutate a
database, deployment, credential, raw artifact, historical branch, or pull
request.

#### Scenario: The dashboard release fails before the receipt boundary

- GIVEN cutover verification fails before any post-cutover live receipt is persisted
- WHEN rollback runs
- THEN the verified old application and dataset pair is restored under the storage cutover contract.

#### Scenario: The receipt boundary has been crossed

- GIVEN SQLite persisted a post-cutover live receipt
- WHEN application rollback is required
- THEN the fallback remains compatible with SQLite and preserves all post-cutover evidence.

### Requirement: Fail Closed At Static Startup And Routing

Application startup MUST parse and validate the production Vite manifest and all
transitively referenced entry, import, CSS, and asset paths before readiness.
Missing, malformed, duplicate-ambiguous, escaping, non-regular, or unreadable
manifest/assets MUST fail startup. Production MUST NOT guess filenames, serve a
development server, or search outside the immutable asset root.

API routes and `/health` MUST take precedence over static routing. The SPA entry
MAY be returned only for navigation `GET` and `HEAD` requests outside reserved
API and asset namespaces. Missing API routes, missing assets, unsupported
methods, malformed paths, and encoded or decoded traversal attempts MUST return
their fail-closed response and MUST NOT fall through to the SPA. `HEAD` MUST use
the corresponding `GET` metadata without returning a body.

The runtime image MUST omit Node, package managers, development dependencies,
test tools, frontend sources, and caches. Responses MUST carry explicit CSP,
`X-Content-Type-Options: nosniff`, anti-frame, referrer, permissions, and cache
policies. Authentication and private responses MUST be non-store; immutable
public assets MAY use long-lived caching. Header ownership MUST be defined so the
proxy and application cannot silently weaken or duplicate conflicting policies.

#### Scenario: A referenced asset is absent

- GIVEN the manifest names an asset that is missing or unreadable
- WHEN the application starts
- THEN readiness fails instead of serving a partial dashboard.

#### Scenario: A path resembles SPA navigation

- GIVEN a request is an unknown API path, missing asset, unsupported method, or traversal attempt
- WHEN static routing evaluates it
- THEN it never returns the SPA entry document.

#### Scenario: Health and SPA routes overlap

- GIVEN the SPA fallback could match `/health`
- WHEN `/health` is requested
- THEN the minimal API health response wins and exposes no private readiness topology.

### Requirement: Constrain LAN Reachability And Runtime Privilege

The release MUST declare the intended bind interface, host firewall allowlist,
proxy upstream allowlist, and application trusted-proxy allowlist. Tests MUST
prove allowed reachability and denied reachability from disallowed interfaces,
source classes, direct application ports, and untrusted proxy peers. Public
evidence MUST use symbolic test roles and MUST NOT embed a private IP address,
hostname, certificate name, or network map.

Application and proxy processes MUST run as non-root with no unnecessary Linux
capabilities. Runtime filesystems MUST be read-only except explicit data and
temporary locations; mounts and secrets MUST be least privilege. Compose MUST
bound CPU, memory, process count, and open-file resources and MUST configure
bounded log rotation. Logs MUST remain sanitized and MUST NOT contain health
values, credentials, cookies, private addresses, or raw request bodies.

#### Scenario: The application port bypasses the proxy

- GIVEN a LAN peer can reach the host but is not the local proxy
- WHEN it connects directly to the application port
- THEN the firewall/bind boundary denies reachability and no forwarded-header trust is available.

#### Scenario: A resource limit is exhausted

- GIVEN the application reaches a declared process, file, memory, or logging bound
- WHEN more work arrives
- THEN it fails within the bounded policy without disabling authentication or expanding privilege.

### Requirement: Back Up And Roll Back Without Losing Accepted Data

A backup MUST use the database-supported online-consistent mechanism. Before it
begins, maintenance mode MUST reject new writers and the operator MUST drain or
terminate active writers within a bounded procedure. A live SQLite file copy is
not acceptable evidence. Verification and restore MUST target an isolated
candidate path; the current database MUST remain untouched until integrity,
schema compatibility, and synthetic application checks pass.

Release-qualified backup evidence MUST identify the current operational data
watermark and the complete restore set for that watermark: SQLite database and
journals captured by the supported mechanism, every SQLite-referenced raw or
batch artifact, required configuration, encryption/recovery material references,
and integrity metadata. Missing, older, or mismatched components MUST block the
release. Restore verification MUST prove the isolated candidate reaches the same
watermark and resolves every referenced artifact before it can qualify.

#### Scenario: Backup evidence predates the release data

- GIVEN the current operational watermark includes accepted writes or referenced
  artifacts newer than the backup evidence
- WHEN release recoverability is evaluated
- THEN publication remains blocked until a complete current restore set passes
  isolated restoration.

Failed migration, restore, or verification state MUST be preserved in a private
isolated location for diagnosis without replacing the last verified state. A
code-only rollback MUST switch to a compatible immutable release stack and MUST
NOT restore an older database, overwrite current data, or discard writes accepted
after the backup. Data restoration requires its own explicit loss/recovery
decision and evidence.

#### Scenario: A backup starts with an active writer

- GIVEN maintenance has not blocked and drained active writes
- WHEN backup is requested
- THEN the procedure stops before producing a release-qualified backup.

#### Scenario: New code fails after accepting writes

- GIVEN the current schema accepted post-release writes
- WHEN application rollback is required
- THEN compatible old code is selected without restoring old data and the failed state is preserved.

### Requirement: Measure A Reproducible Raspberry Pi Baseline

The private native baseline MUST record the full immutable release-stack
identity, hardware model and memory class, server timezone and measurement time,
synthetic fixture identity, request routes/mix/concurrency, sample count and
warm-up, latency distribution, CPU/memory/disk observations, and compressed and
uncompressed asset sizes. It MUST state thresholds and measurement method before
the release comparison. Mutable tags, unspecified fixtures, single unqualified
latency values, or measurements on different hardware MUST NOT qualify the
candidate.

#### Scenario: A performance claim lacks context

- GIVEN a candidate reports latency without fixture, request mix, resources, or stack identity
- WHEN the Pi release gate reviews it
- THEN the claim is non-reproducible and publication remains blocked.

### Requirement: Supersede Legacy Dashboard Plans Without Transplanting Code

`recover-dashboard-documentation` MUST be the forward planning baseline for the
private dashboard. It supersedes the requirements and delivery assumptions in
`modern-health-dashboard`, `publish-health-dashboard-safely`, and PR #3 where
they conflict with this change, the operational SQLite migration, or ADRs
0001-0006.

Supersession MUST NOT cherry-pick, merge, copy, or restore historical dashboard
code, BFF boundaries, shared credentials, Parquet/DuckDB operational reads,
retention behavior, package-manager choices, deployment manifests, or generated
assets. Historical Git and PR evidence MUST remain intact. This change MUST NOT
close, modify, merge, or delete PR #3; any such action requires a separate
maintainer decision.

Reusable visual or interaction ideas MAY be reconsidered only through later
implementation derived from this baseline and verified against current data,
accessibility, privacy, and architecture contracts.

#### Scenario: A legacy implementation appears reusable

- GIVEN historical dashboard code implements a desired interaction
- WHEN future work is planned
- THEN the requirement is reimplemented from the current baseline rather than cherry-picked with obsolete boundaries.

#### Scenario: This documentation change is accepted

- GIVEN PR #3 remains open as historical context
- WHEN the recovery documentation is approved
- THEN PR #3 remains untouched and is not treated as the implementation base.
