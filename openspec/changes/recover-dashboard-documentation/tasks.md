# Tasks: Recover Dashboard Documentation

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1,913 final across OpenSpec, ADR 0006, and architecture index |
| Review budget | 2,500 authored changed lines |
| Delivery strategy | `exception-ok`; maintainer-approved `size:exception` |
| Suggested split | One documentation PR; PR #3 follow-up after merge |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

## Suggested Work Units

| Unit | Goal | Focused check | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 1 | Publish baseline and minimal corrections | `git diff --check` | N/A: documentation only | Revert replacement PR |
| 2 | Record PR #3 supersession after Unit 1 merges | Review comment and PR state | N/A: GitHub metadata only | Edit/reopen PR #3 |

## Phase 1: Baseline Evidence

- [x] 1.1 Compare proposal, four specs, and design with `origin/main@ede7d0c`; no dashboard, frontend manifest, Compose release, or browser session is shipped.
- [x] 1.2 Cross-check SDD SQLite/Engram records `#349`, `#351`, and `#353`; Phase 3 is merged and phases 4-17 remain prerequisites.
- [x] 1.3 Record the maintainer-approved `size:exception`, 2,500-line budget, documentation-only scope, and no implementation authorization.

## Phase 2: Documentation Apply

- [x] 2.1 Publish the recovery baseline; mark `modern-health-dashboard`, `publish-health-dashboard-safely`, and PR #3 superseded where conflicting.
- [x] 2.2 Preserve Git/PR history; never copy, cherry-pick, merge, restore, or delete prototype code, manifests, assets, locks, or BFF boundaries.
- [x] 2.3 Retain compatible visual ideas only as reference, preserving responsive, keyboard, focus, non-color, textual-chart, coverage, and limitation requirements.
- [x] 2.4 Correct the architecture current-state table and add ADR 0006 to clarify ADR 0001/0003 prototype and TLS publication implications without rewriting their history.
- [x] 2.5 Inspect the complete scope for secrets, real health values, exports, paths, hashes, manifests, backups, or identifiable screenshots; retain only minimal synthetic examples.

## Phase 3: Recovered Hardening Contracts

- [x] 3.1 Specify bounded login admission, atomic rate state, one-way password verification, unpredictable rotating sessions, and fail-closed capacity without valid-session eviction.
- [x] 3.2 Specify socket-peer authority, explicit immediate-proxy trust, forwarded-header rejection, and HTTPS/private-data denial outside loopback.
- [x] 3.3 Specify synchronous `pagehide` privacy lock, `pageshow` revalidation, atomic abort/clear/generation invalidation, and rejection of late commits.
- [x] 3.4 Specify atomic whole-response validation for metric, snapshot, timezone, dates/range, unit, finiteness, gaps, and structured details with no partial repair.
- [x] 3.5 Specify fail-closed Vite startup, API/health precedence, navigation-only SPA fallback, runtime dependency exclusion, and explicit security/cache headers.
- [x] 3.6 Specify LAN bind/firewall/proxy allowlists, symbolic positive/negative reachability evidence, least privilege, resource bounds, and log rotation.
- [x] 3.7 Specify quantified accessibility at 320 CSS pixels, 44-by-44 targets, 200 percent text zoom, WCAG contrast, focus/inert/Escape/restore, reduced motion, and chronological table focus return.
- [x] 3.8 Specify online-consistent backup with writer drain and candidate isolation, failed-state preservation, and code rollback without old-data restoration.
- [x] 3.9 Bind release evidence to app/proxy image and effective proxy/Compose configuration digests; require a reproducible measured Pi baseline.
- [x] 3.10 Separate SQLite operational prerequisites from the later dashboard read-contract product change; derive the expected 25 metrics from completed registry membership.
- [x] 3.11 Define correction date as selected-version server acceptance time and make `SameSite=Strict` plus same-origin `Origin` enforcement testable.

## Phase 4: Follow-Up Boundary

- [x] 4.1 Require a separate approved product/read-contract follow-up; exclude implementation from this PR.
- [x] 4.2 Gate publication on registry/current reads, the dashboard response contract, reconciliation/readiness, auth, frontend, constrained runtime, full-stack identity, and native ARM64 evidence.
- [x] 4.3 Require fresh implementation from these requirements; prohibit legacy reads, browser ingestion tokens, transplanted code, and parallel metric authority.

## Phase 5: Documentation Verification

- [x] 5.1 Inspect the complete diff from current `origin/main`: recovery OpenSpec artifacts, architecture index, and ADR 0006.
- [x] 5.2 Confirm no product code, private value, runtime artifact, guidance artifact, PR #3 state, or Git history is changed by this recovery commit.
- [x] 5.3 Run pytest, repository audit, audit unittests, and staged diff/whitespace checks; record evidence and residual gates in `verify-report.md`.
- [x] 5.4 Confirm merged PR #20/ADR 0005 is present in the current `origin/main` base.
- Runtime harness: N/A; this change records future acceptance contracts and implements no runtime behavior.

## Phase 6: PR #3 Supersession

- [ ] 6.1 After replacement merge, prepare a PR #3 comment linking the baseline and explaining why no code was copied or cherry-picked.
- [ ] 6.2 Only then, and with maintainer approval, post the comment and close PR #3 as superseded; do not merge or delete its history.
