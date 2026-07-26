# Design: Reclassify Dashboard Future Specs

## Technical Approach

Move the four recovery specifications, without rewriting bytes, from the recovery
delta tree into this change's `evidence/recover-dashboard-future-specs/` tree.
Add a canonical JSON relocation manifest and a machine-checked Markdown ownership
matrix. Extend the existing repository audit with pure-stdlib validators that
discover either active or archived change roots. This governs documentation only;
it adds no dashboard runtime behavior or dependency.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Canonical JSON manifest | Less readable than Markdown; deterministic parsing | Use schema v1 JSON, sorted entries, two-space indentation, UTF-8/LF, trailing newline |
| Rewrite or copy specs | Easier editing but loses rename/byte identity | Use four Git-recognizable moves and preserve bytes |
| Active-path constants | Simple but breaks after archive | Locate exactly one active-or-`archive/*-{change}` root for each change, then resolve stable suffixes |
| Git commands in validation | Resolves objects but expands subprocess/repository-selection risk | Use `hashlib` to recompute SHA-256 and Git blob IDs against reviewed baseline constants; add no subprocess |

## Data Flow

```text
tracked paths + discovered roots -> manifest/matrix parsers -> identity/count/placement checks -> audit failures
destination bytes ----------------> SHA-256 + Git-blob proof -----------^
```

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/recover-dashboard-documentation/specs/{accessible-descriptive-dashboard,dashboard-operational-data,private-dashboard-access,dashboard-release-baseline}/spec.md` | Move | Remove exactly four mergeable deltas |
| `openspec/changes/reclassify-dashboard-future-specs/evidence/recover-dashboard-future-specs/{same capability}/spec.md` | Create by move | Preserve exact bytes and history |
| `.../evidence/recover-dashboard-future-specs/relocation-manifest.json` | Create | Relocation and protected-narrative identities |
| `.../evidence/recover-dashboard-future-specs/requirement-matrix.md` | Create | 22-row/64-scenario ownership evidence |
| `scripts/check_repository.py` | Modify | Add fail-closed governance audit |
| `scripts/test_check_repository.py` | Modify | Add strict-TDD policy tests |

## Interfaces / Contracts

Manifest schema v1 contains `source_commit` fixed to the recovery-spec commit
`12cf7d316887f206fcdd0041435b8622445de042`, plus
`protected_narrative_commit` fixed to the post-housekeeping baseline
`14dd29f03fe08d35a89b6ec23bbd07fbbb02eb36`; exactly four `entries`, sorted by
`source_path`; and five `protected_narratives`. Each entry has repository-relative
`source_path`, `destination_path`, 40-hex `source_blob_sha1`, 64-hex `sha256`, and
`byte_count`. Narrative records cover `exploration.md`, `proposal.md`, `design.md`,
`tasks.md`, and `verify-report.md` with identities resolved from the protected
narrative commit. Paths
must be normalized POSIX paths without absolute roots or `..`. Current locations
are resolved through the discovered change root; recorded paths remain historical.

The matrix declares `Requirements: 22` and `Scenarios: 64`, then has exactly these
columns: `Source anchor | Requirement | Scenario count | Scenarios | Future owner |
Dependencies`. Anchors are unique change-root-relative evidence paths plus exact
requirement slugs. Requirement/scenario names must equal parsed headings and each
scenario appears once. Each row has exactly one owner from
`dashboard-read-contract`, `browser-authentication-session`,
`frontend-presentation`, or `deployment-release`; dependency notes preserve
SQLite phases 4–10/11–17 where applicable.

Active state may pass before verification. Archived reclassification requires a
valid PASS verification report and all relocation checks. Archived recovery also
requires archived reclassification and no recovered spec in any mergeable delta
path. Unknown, duplicate, missing, malformed, or conflicting state fails closed.

## Testing Strategy

Strict work units are: (1) RED malformed/discovery/archive/path-classification
fixtures, then GREEN root/parser helpers; (2) RED missing, byte/blob/hash,
narrative, and rollback failures, then GREEN manifest validation; (3) RED 22/64
drift, duplicate/missing anchors, scenario-name drift, and owner cardinality, then
GREEN matrix validation; (4) RED CLI integration, then GREEN audit wiring/refactor.
Tests build temporary trees only from deterministic synthetic documentation held
in the repository test module. Unit and CLI integration use `unittest`; E2E is N/A.

## Threat Matrix

| Boundary | Applicability | Safe/failure behavior | Planned RED tests |
|---|---|---|---|
| Documentation-like paths | Applicable: evidence-path classification changes | Accept only contracted non-executable evidence; aliases or executable files fail | `requirements.txt`, `CMakeLists.txt`, executable Markdown/MDX, `README.sh` |
| Git repository selection | N/A: no new Git invocation or selector | Injected root/tracked paths are authoritative | None |
| Commit state | N/A: no index/commit automation | No index semantics | None |
| Push state | N/A: no push automation | No remote resolution | None |
| PR commands | N/A: no PR automation | No command composition | None |

## Migration / Rollout / Rollback

Apply performs RED/GREEN work and the four moves; verification follows. Archive
sequencing remains a later phase: reclassification first, recovery second. Rollback
uses validated manifest entries to restore all four original paths and exact bytes,
then removes policy additions; ambiguity blocks rollback readiness.

## Risks

Archive-layout ambiguity or synchronized tampering could hide drift; exact-one-root
discovery, reviewed baseline identities, and fail-closed parsing mitigate both.

## Open Questions

None.
