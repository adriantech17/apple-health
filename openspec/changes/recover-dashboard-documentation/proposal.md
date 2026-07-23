# Proposal: Recover Dashboard Documentation

## Intent

Establish one current, SQLite-first planning baseline for the private dashboard
without restoring or implementing the historical dashboard branch.

This documentation-only change consolidates the approved first-release product
boundary, identifies reusable requirements from the prototype, and retires
obsolete BFF, credential, storage, package-management, and retention assumptions.
It conceptually supersedes `modern-health-dashboard`,
`publish-health-dashboard-safely`, and PR #3. It does not modify or close PR #3.

## Current State

`origin/main` is `ede7d0c`. The published application currently has:

- a FastAPI ingestion and read API protected by one bearer token;
- SQLite metadata plus Parquet metric values and DuckDB operational reads;
- retained compressed raw payloads with automatic pruning disabled;
- the operational SQLite schema from Phase 3 of
  `migrate-daily-summaries-to-operational-sqlite`;
- no dashboard, frontend manifest, browser session, Compose manifest, or
  published Raspberry Pi dashboard deployment.

Operational SQLite metric contracts, persistence, current-version reads,
reconciliation, cutover, and readiness are not complete. Accepted ADRs describe
the target architecture, not implemented behavior. The historical dashboard
branch predates this migration and is not a mergeable implementation baseline.

## Scope

This change documents a future first private dashboard release for exactly one
person and one fixed server-side owner. Multiuser behavior is not part of the
product scope.

The documented release boundary includes:

- a same-origin React SPA served by the modular FastAPI application, with no
  separate BFF or dashboard application service;
- overview and metric-detail experiences covering all 25 metrics admitted by
  the completed operational registry;
- a default experience focused on the latest 12 months while retaining and
  preserving all older history;
- a presentation catalog separate from the operational metric registry, limited
  to names, descriptive education, units, provenance labels, limitations,
  accessibility text, and display rules;
- responsive and accessible navigation, textual equivalents for essential chart
  information, visible units, coverage, and limitations;
- selective reuse of the prototype's visual language only where it remains
  compatible with truthful data states, accessibility, and the current ADRs;
- browser authentication using credentials distinct from ingestion and a
  same-origin `HttpOnly`, `SameSite` session;
- local-network TLS before the browser session is used outside loopback;
- ADR 0006 as the durable publication boundary for trusted proxy identity,
  private reachability, complete release identity, and native verification;
- npm and a committed npm lockfile as the frontend package workflow;
- reproducible rollback and private release evidence for the exact application
  artifact, proxy, Compose configuration, and data state;
- bounded login admission, trusted-proxy and transport enforcement, synchronous
  browser privacy locking, atomic response validation, and fail-closed static
  asset startup and routing;
- quantified accessibility, least-privilege operation, online-consistent backup,
  negative LAN reachability tests, and a measured Raspberry Pi baseline.

### Corrections

The normal dashboard view shows the operationally selected current value. When
that value supersedes an earlier accepted version for the same metric owner and
Madrid local date, it also shows a concise notice. “Correction date” means the
authoritative server timestamp at which that correcting version was accepted,
not the metric day, source sample time, import filename time, browser time, or
display-formatting date. The timestamp and bounded import origin must be supplied
with the selected version by the future dashboard read contract.

Raw payloads and the complete version history are not shown by default. The
dashboard does not select corrections, reconstruct provenance, or create a
parallel version authority.

### Incomplete And Sparse Data

The dashboard preserves a visualization whenever useful information remains,
while making gaps, coverage, completeness, freshness, and known limitations
visible. It does not impute values, connect discontinuities, replace absence
with zero, or imply that missing or observed values are normal.

When the operational contract can determine the distinction, the presentation
separates legitimate absence, an inherently sporadic metric, and an ingestion
or processing failure. Otherwise it states the uncertainty rather than
inventing a cause.

### Descriptive Education

The release may explain what a metric represents, how it was sourced, what
period is displayed, and what limitations affect the presentation. Health
interpretation, individualized guidance, diagnosis, clinical advice, warning
signs, and claims of normality remain outside this change and are governed by
ADR 0005. This proposal does not authorize interpretive functionality.

## Non-Goals

- Implementing React, API contracts, authentication, storage, deployment,
  Compose, tests, migration, reconciliation, or cutover.
- Supporting multiple people, accounts, profiles, roles, or client-selected
  `user_id` values.
- Restoring a separate BFF, internal HTTP boundary, dashboard container, or
  browser access to the ingestion token.
- Reading dashboard data from raw archives, legacy Parquet, or DuckDB, or making
  either analytical store authoritative.
- Creating alternate metric metadata, current-value selection, provenance,
  completeness, freshness, absence, or ingestion-status authority.
- Defining health-pattern interpretation outside ADR 0005 governance.
- Adopting pnpm, generating a pnpm lockfile, or maintaining two frontend package
  workflows.
- Pruning raw payloads, corrections, versions, or older history.
- Transplanting historical branch code or modifying, closing, or merging PR #3.

## Operational SQLite Dependencies

Documentation may proceed now. The applicable phases of
`migrate-daily-summaries-to-operational-sqlite` establish operational
prerequisites, but they do not themselves deliver a dashboard API, dashboard
freshness/provenance fields, or a browser response contract:

| Required outcome | SQLite phases | Dashboard dependency |
|---|---:|---|
| Complete registry | 4-6 | Completed registry entries, rather than a parallel list, determine the launch catalog and its cardinality |
| Versions and current selection | 7-8 | Immutable versions, deterministic current values, corrections, tombstones, and source lineage become operational prerequisites |
| Ingestion and operational reads | 9-10 | Indexed owner/date reads and integrity state become operational prerequisites; no dashboard field is implied |
| Reconciliation and cutover | 11-16 | Historical populations are verified, promoted, backed up, restored, and cut over without invented authority or lost evidence |
| Readiness | 17 | The private runbook, rollback boundary, and synthetic rehearsal are complete |

After the operational prerequisites complete, a separate approved dashboard
read-contract product change MUST define and implement the atomic response,
including freshness, bounded provenance, correction acceptance time,
completeness, gaps, and integrity fields. Dashboard implementation must consume
that contract without duplicating its semantics or introducing a temporary
Parquet/DuckDB path. Routine use against migrated history cannot begin before
that product change plus reconciliation, verified cutover, and readiness are
complete. The “25 metrics” scope is a count derived from completed registry
entries at the release gate, never an independently maintained authority.

## Impacts

### Privacy

- Only synthetic fixtures and screenshots may be used in Git, CI, review, and
  release evidence.
- Real health values, raw payloads, paths, hashes, manifests, backups, secrets,
  and identifiable traces remain private and are not sent to external services
  or telemetry.
- The latest-12-month default is a presentation window, not retention or
  deletion policy.

### Authentication And Network

- The ingestion credential remains machine-only and never reaches browser code,
  HTML, storage, logs, or frontend build artifacts.
- Browser sessions use a separate credential boundary and same-origin secure
  cookies. The implementation contract must make login admission, capacity,
  expiry, revocation, `SameSite` mode, CSRF enforcement, browser lifecycle, and
  recovery mechanically verifiable and fail closed.
- The immediate socket peer is authoritative unless it is explicitly trusted as
  a proxy; forwarded origin, host, scheme, and client-address headers from any
  other peer are ignored or rejected.
- LAN publication is blocked until TLS, origin, cookie, and private-access
  behavior plus positive and negative network reachability pass the release gate.

### Data

- SQLite is the sole future operational authority for dashboard reads.
- The dashboard may format authoritative fields but may not infer missing
  values, reaggregate daily contracts, choose versions, or rewrite provenance.
- Raw evidence, every accepted version, and history older than 12 months remain
  preserved under the operational migration and rollback contracts.

## Risks

| Risk | Mitigation |
|---|---|
| Documentation is mistaken for shipped behavior | Keep verified current state prominent and require later design, specifications, tasks, and implementation review |
| UI work races ahead of SQLite authority | Block implementation on phases 4-10 and publication on phases 11-17 |
| Missing data is visually normalized or concealed | Require explicit gaps, coverage, limitations, no imputation, and no connected discontinuities |
| Correction notices leak raw evidence or become a second audit UI | Expose only current value plus bounded date/origin notice from the operational contract |
| Prototype reuse restores obsolete boundaries | Reuse only accessible interaction and visual language; prohibit BFF, shared token, legacy reads, and duplicate metadata |
| CI gives false confidence for Raspberry Pi publication | Require a private native ARM64 smoke on the exact image digest; CI cannot waive or replace it |
| A valid session is evicted under login pressure | Bound expensive work, concurrency, rate state, and session capacity; reject new work without evicting valid sessions |
| A proxy header or SPA fallback bypasses a boundary | Trust only an allowlisted immediate proxy and fail closed for API, asset, method, traversal, manifest, and transport errors |
| Browser history or a late request restores private state | Lock synchronously on `pagehide`; revalidate on `pageshow`; abort and invalidate a generation atomically on loss of authorization |
| A partially repaired response combines incompatible data | Validate the complete metric response and commit it atomically or reject it entirely |
| Rollback or backup loses accepted writes | Drain writers, take an online-consistent backup into isolation, preserve failed state, and never restore old data for code-only rollback |
| Descriptive education drifts into health interpretation | Enforce ADR 0005 and fail closed to descriptive data |
| A 12-month focus becomes destructive retention | Test it as a default query/display choice and preserve complete history and raw evidence |

## Success Criteria

- [x] Repository documentation states that no dashboard or Compose deployment is
  currently published in `main`.
- [x] One approved planning baseline replaces the conflicting dashboard drafts
  without copying their obsolete implementation assumptions.
- [x] The release is explicitly single-person and covers the operational
  registry's 25 metrics.
- [x] The latest 12 months are prioritized without deleting or hiding access to
  older retained history.
- [x] Correction, missingness, sparse-data, completeness, coverage, and degraded
  states follow the operational contract and the presentation rules above.
- [x] Accessibility, separated authentication, LAN TLS, npm, rollback, and the
  compatible prototype visual language are retained as future requirements.
- [x] BFF separation, browser ingestion credentials, alternate metadata
  authority, pnpm, raw pruning, and authoritative Parquet/DuckDB reads are
  explicitly rejected.
- [x] Dashboard implementation and publication gates reference the required
  SQLite phases as prerequisites and require a separate dashboard read-contract
  product change rather than attributing dashboard fields to those phases.
- [x] Login, proxy trust, browser lifecycle, response validation, static routing,
  security headers, network allowlisting, accessibility, runtime confinement,
  backup/rollback, immutable stack identity, and measured Pi evidence are stated
  as testable fail-closed requirements.
- [x] Health interpretation remains excluded and subject to ADR 0005.
- [x] PR #3 remains untouched until the maintainer separately decides to close
  it as superseded.

## Rollback

This proposal changes documentation only. Rollback is a normal revert of the
documentation PR; it performs no database, raw-data, credential, deployment, or
runtime operation.

Reverting the documentation must not revive the historical branch as an
approved baseline, delete its history, alter PR #3, weaken the SQLite migration,
or authorize raw pruning. Any future implementation rollback must be specified
against the SQLite cutover boundary and exact deployed artifact before that
implementation begins.

## Delivery

- Preflight: `interactive`, OpenSpec and Engram, `single-pr-default`, 2,500
  authored-line review budget.
- Deliver one documentation-only PR from current `origin/main`, which includes
  ADR 0005 from merged PR #20.
- Do not include dashboard code, dependencies, generated assets, deployment
  manifests, private evidence, or changes to the health-guidance change.
- Keep the active SQLite migration artifacts authoritative and unchanged except
  for later, separately reviewed documentation links if required.
- Subsequent product implementation and private release execution require
  separate approval; this PR contains the approved planning artifacts only.
- LAN publication remains blocked until a maintainer-run private smoke test with
  synthetic data passes on the Raspberry Pi using the exact ARM64 image digest
  intended for release. CI is necessary evidence but cannot replace this gate.
