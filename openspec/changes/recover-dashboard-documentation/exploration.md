# Exploration: Recover Dashboard Documentation

## Change Frame

- **Mode:** interactive
- **Artifact store:** OpenSpec and Engram
- **Delivery:** one documentation-only PR from `origin/main`
- **Review budget:** 2,500 authored lines
- **Implementation:** explicitly excluded

## Problem

The accepted dashboard direction is documented as a same-origin React SPA in a
modular FastAPI monolith, but the current architecture documents still describe
the historical two-process dashboard/BFF deployment as if it existed. The
historical dashboard branch diverged before the operational SQLite migration,
deleted the migration OpenSpec artifacts, and reads the ingestion API through a
separate BFF authenticated with the ingestion token. It is therefore not a
mergeable implementation baseline.

Without consolidation, a later dashboard proposal could accidentally recover an
obsolete storage, credential, or deployment boundary instead of the accepted
SQLite-first architecture.

## Verified Current Context

- `origin/main` is `ede7d0c`; Phase 3 of
  `migrate-daily-summaries-to-operational-sqlite` is merged.
- The operational SQLite schema exists, but metric contracts (phases 4-6),
  operational persistence/reads (phases 7-10), and cutover remain incomplete.
- The existing migration proposal explicitly makes SQLite the future dashboard
  operational source and excludes dashboard UI, browser sessions, deployment,
  and new dashboard response contracts.
- ADR 0001 requires one deployable, same-origin browser access through an
  `HttpOnly` session, and credentials distinct from ingestion.
- ADR 0002 retains React, Vite, Recharts, a separate metric catalog, accessible
  textual alternatives, and educational, non-diagnostic explanations.
- ADR 0004 makes Parquet/DuckDB derived analytical storage; the dashboard
  normally reads the operational store.

## Rescuable Requirements

- A private, responsive SPA for one local-network user on the Raspberry Pi.
- Metric navigation and a presentation catalog that supplies names, units,
  explanatory context, provenance, limitations, and display rules separately
  from UI components.
- Visual trends accompanied by textual summaries, coverage, units, and an
  accessible equivalent for information essential to interpretation.
- Explicit treatment of sparse metrics, incomplete current days, missing data,
  corrections, and detailed values such as heart-rate extrema and sleep stages.
- Personal-reference comparisons that disclose their period, sample threshold,
  and limitations, and never present a diagnosis or clinical advice.
- Browser authentication through a same-origin `HttpOnly`, `SameSite` session;
  the ingestion token never reaches the browser.
- Private operation: no health values, screenshots, manifests, hashes, secrets,
  or identifiable traces in Git, CI, documentation examples, or external
  services.

## Non-Goals

- No React, API, authentication, storage, deployment, Compose, or test
  implementation.
- No restoration of a standalone BFF, inter-service HTTP call, shared ingestion
  token, in-memory dashboard session store, or separate dashboard container.
- No dashboard read path from raw archives, legacy Parquet, or DuckDB.
- No duplicate dashboard metadata, metric authority, correction selection, or
  raw-data retention/pruning policy.
- No implementation decision on exact screen composition, trend algorithms,
  numeric limits, password recovery, or concrete deployment values. The proposal
  establishes the approved session, accessibility, and topology boundaries.
- No modification, archival, or re-planning of the active SQLite migration
  artifacts in this exploration.

## SQLite Dependencies

The dashboard proposal depends on phases 4-10 for metric authority, canonical
units/shapes, versions/current selection, source lineage, and indexed SQLite
reads. Those phases do not themselves deliver dashboard completeness, freshness,
coverage, or integrity-response fields. A separate product change MUST define and
implement that read contract from operational authority before dashboard work.

Phases 11-17 are not a prerequisite for documenting the dashboard, but private
publication and any routine use against migrated history remain subject to the
reconciliation, recovery, cutover, and readiness gates defined there.

## Confirmed Product Boundaries

1. One private person, an overview and metric detail for registry-admitted metrics,
   with the latest 12 months as a non-destructive default.
2. Explicit coverage, gap, partial, empty, error, correction, and uncertainty states.
3. Separate browser and ingestion credentials with fail-closed session lifecycle.
4. Quantified accessibility, same-origin modular delivery, TLS outside loopback,
   and native exact-stack ARM64 publication evidence.
5. Comparison algorithms, concrete numeric limits, and password recovery remain
   separate implementation decisions.

## Risks

| Area | Risk | Required documentary guardrail |
|---|---|---|
| Privacy | A browser, BFF, log, fixture, or screenshot exposes the ingestion token or health data. | Separate session and ingestion credentials; synthetic evidence only; no external telemetry. |
| Correctness | UI calculations average totals, hide corrections/completeness, or use browser-local time. | UI consumes canonical operational fields and labels limitations; server-owned `Europe/Madrid` semantics remain authoritative. |
| Correctness | The historical metric catalog is mistaken for an accepted contract. | Map every presented metric/detail to phases 4-6 before implementation. |
| Operation | A second process/container and shared secret increase recovery and deployment cost. | Preserve the single-deployable, same-origin ADR boundary. |
| Migration | Dashboard publication is interpreted as permission to read legacy or partially migrated data. | State phases 4-10 as operational-read prerequisites and retain phases 11-17 gates. |
| Review | A documentation cleanup silently becomes a product rewrite. | Keep this PR to consolidation; defer product choices to an interactive proposal. |

## Consolidation Strategy

1. Create this new OpenSpec change as the audit trail for recovering dashboard
   planning without editing accepted migration artifacts during exploration.
2. In the later documentation-only PR, correct the current-state language in
   the architecture overview and ADRs so historical deployment facts are not
   described as implemented state.
3. Preserve ADR 0001, 0002, and 0004 decisions while explicitly retiring the
   historical BFF/Parquet dashboard assumptions from forward-looking guidance.
4. Add a compact dashboard planning document or OpenSpec proposal only after the
   product questions above are answered; it must reference, rather than copy,
   SQLite metric and authority contracts.
5. Leave the obsolete historical branch and PR unmerged as historical context;
   do not transplant its code or delete its history in this change.

## Estimate

- This exploration: 136 Markdown lines, one new file.
- Final documentation consolidation: 1,913 changed lines across the architecture
  overview, ADR 0006, and dashboard planning artifacts; within the 2,500-line
  review budget.
- Product implementation: intentionally unestimated until the proposal answers
  the outstanding product and operational questions.

## Evidence Consulted

- `origin/main` at `ede7d0c` and the active SQLite migration proposal/tasks.
- ADRs 0001-0004 in `docs/architecture/decisions/`.
- Historical `codex/feat-health-dashboard` commits and diff from `origin/main`.
