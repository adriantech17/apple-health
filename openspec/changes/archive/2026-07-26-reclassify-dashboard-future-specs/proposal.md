# Proposal: Reclassify Dashboard Future Specs

## Intent

Prevent unimplemented dashboard contracts from being promoted to OpenSpec source-of-truth during archive. Establish a testable repository-governance capability for preserving planning evidence and assigning future implementation ownership. It authorizes no dashboard runtime behavior; privacy, data, and authentication behavior remain unchanged.

## Scope

### In Scope
- Relocate exactly four recovery delta files byte-for-byte to `evidence/recover-dashboard-future-specs/`, outside every delta `specs/` tree, with relocation manifests.
- Create a 22-row requirement matrix that accounts for all 64 scenarios, preserves exact source traceability, and assigns future implementation ownership.
- Add repository-policy validation and tests in `scripts/check_repository.py` and `scripts/test_check_repository.py` for evidence placement, manifests, accounting, and archive-sync exclusion/preconditions.
- Keep Strict TDD and archive policy unchanged; archive is a later phase after merge and verification.

### Out of Scope
- Dashboard runtime/product code, implementation, runtime tests, requirements, or behavior; future implementation changes or skeletons.
- Historical branch content, GitHub lifecycle actions, Strict TDD waivers, and archive actions.
- Editing retained recovery exploration, proposal, design, tasks, or verification evidence.

## Capabilities

This capability governs repository planning evidence, not dashboard behavior. Evidence MUST remain non-promotable and outside delta `specs/` trees.

### New Capabilities
- `planning-evidence-governance`: Governs non-promotable evidence placement, byte-preserving relocation manifests, exact requirement/scenario accounting, future ownership, and archive-sync exclusion/preconditions.

### Modified Capabilities
None.

## Approach

Use Git-preserving moves without editorial changes. A policy checker validates manifests, 22/64 traceability, ownership, and absence of future dashboard evidence from mergeable delta trees. Later implementation-owned changes must restate executable requirements, cite evidence, follow RED-GREEN-REFACTOR, and prove runtime scenarios before their own archive.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `openspec/changes/recover-dashboard-documentation/specs/*/spec.md` | Relocated | Four future contracts leave archive-merge inputs. |
| `openspec/changes/reclassify-dashboard-future-specs/evidence/` | New | Evidence, manifests, and ownership matrix. |
| `scripts/{check_repository,test_check_repository}.py` | Modified | Automated governance validation and tests. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Future behavior is promoted as current spec | Low | Policy rejects mergeable delta placement and unmet archive preconditions. |
| Text or traceability is lost | Med | Prove byte equality and 22-row/64-scenario accounting. |

## Rollback Plan

Revert the policy and test additions, then restore the four relocated files to their original paths from the byte-preserving manifests. No runtime, data, credential, GitHub, or archive operation occurs.

## Dependencies

- Recovery exploration, proposal, design, tasks, and verification evidence.
- SQLite phases 4–10 for later read work; phases 11–17 for later publication.

## Success Criteria

- [ ] Repository-policy tests pass.
- [ ] Exactly four files are byte-preserved, proven by per-file SHA-256 equality and `git diff --no-index`.
- [ ] Manifests and matrix prove 22 requirement rows and 64 scenarios, each source-traceable and assigned a future owner.
- [ ] Policy proves no future dashboard evidence is under a mergeable delta tree; no runtime behavior, waiver, or archive action is introduced.
