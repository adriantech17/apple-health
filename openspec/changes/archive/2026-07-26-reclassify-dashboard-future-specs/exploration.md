## Exploration: Reclassify Dashboard Future Specs

### Current State
`docs/reclassify-dashboard-specs` and `origin/main` both resolve to `14dd29f`,
which includes merged PR #23. `recover-dashboard-documentation` is a completed
documentation/history delivery in intent, but it still owns four OpenSpec delta
specifications containing 22 future runtime requirements and 64 scenarios.
`openspec/specs/` and `openspec/changes/archive/` do not exist. Under the local
archive convention, archiving a change merges every delta below its `specs/`
directory into `openspec/specs/` before moving the change directory to the
immutable archive. That would falsely publish unimplemented dashboard behavior
as current source-of-truth specification.

The current FastAPI repository has no frontend manifest, React source, Compose
configuration, browser session, or dashboard runtime. `strict_tdd: true` applies:
the recovery verification is documentary only and explicitly records no runtime
evidence. It cannot prove the 22 requirements or 64 scenarios as implemented.

### Affected Areas
- `openspec/changes/recover-dashboard-documentation/specs/*/spec.md` — four future behavioral delta specs that must no longer be archive-merge inputs for the documentary change.
- `openspec/changes/recover-dashboard-documentation/{exploration.md,proposal.md,design.md,tasks.md,verify-report.md}` — retain the documentary decision, dependency gates, PR #3 supersession receipt, and verification scope as historical/governance evidence.
- `openspec/changes/reclassify-dashboard-future-specs/` — future reclassification artifacts should preserve exact source anchors and an ownership matrix, but contain no dashboard delta specs under `specs/`.
- `openspec/config.yaml` — Strict TDD remains in force; it cannot be waived by documentary verification.
- `openspec/specs/` and `openspec/changes/archive/` — archive targets that must remain free of the future dashboard contracts until their implementation changes pass runtime verification.

### Approaches
1. **Move all four specs intact into this reclassification change** — Transfer the existing delta files to `reclassify-dashboard-future-specs/specs/` and archive it later.
   - Pros: Preserves wording and scenarios with a simple move.
   - Cons: Archiving this change would repeat the same false promotion into `openspec/specs/`; it leaves incompatible runtime concerns under one non-implementation owner.
   - Effort: Low, but invalid.

2. **Archive the documentary change without its deltas** — Delete the four delta specs and archive `recover-dashboard-documentation` without preserving a traceable record.
   - Pros: Allows a mechanically small closure.
   - Cons: Loses the reviewed contract text from the OpenSpec audit trail and breaks requirement/PR/Engram traceability.
   - Effort: Low, but invalid.

3. **Reclassify as evidence, then split by implementation ownership** — Relocate the four files byte-for-byte from the recovery change's `specs/` tree into a non-delta evidence path owned by this change, add a requirement/scenario source-anchor matrix, and create future executable deltas only in implementation-owned changes.
   - Pros: Lets both documentary changes archive without syncing future behavior; preserves Git rename history, the original PR evidence, and an explicit Engram chain; aligns each executable requirement with the code and Strict-TDD proof that will own it.
   - Cons: Later proposals must intentionally re-specify and verify the contracts rather than treating the evidence copy as an accepted current spec.
   - Effort: Medium.

### Recommendation
Choose approach 3. Do not move the four specs intact into another active change's
`specs/` directory. The smallest truth-preserving transformation is a
documentation-only relocation to an immutable, non-delta evidence path plus a
traceability matrix covering all 22 requirements and 64 scenarios.

The matrix should assign future implementation ownership as follows: dashboard
operational data to a post-phases-4--10 dashboard read-contract change;
private dashboard access to browser authentication/session and private-read
changes; accessible/descriptive dashboard to the frontend/presentation change
after those contracts; and release baseline to the deployment/release change.
Each later change must restate only its executable delta requirements, cite the
evidence anchors, follow RED-GREEN-REFACTOR, and archive only after its runtime
scenarios pass.

`recover-dashboard-documentation` retains its exploration, proposal, design,
tasks, and verification report as the historical record of the approved
SQLite-first target, exclusions, migration gates, documentary verification, and
PR #3 supersession. Its former delta text remains preserved through the Git move,
the reclassification evidence copy, PR links, and Engram artifacts; it is not
deleted or rewritten as runtime truth.

Valid Strict-TDD archive ordering is: (1) apply and documentary-verify this
reclassification with no `specs/` delta directory; (2) archive this
reclassification, preserving its evidence; (3) re-verify that recovery contains
no mergeable dashboard deltas and archive it; (4) after their dependencies are
ready, implement and verify the split product changes; (5) archive each product
change only after its own runtime scenarios pass. No archive may precede the
relocation, and no policy waiver or documentary PASS substitutes for runtime
proof.

One PR remains appropriate: the change is Markdown-only, has zero
non-documentation changed lines against the 1,000-line budget, and has one
auditable outcome. Its review should lead with the move manifest and requirement
matrix; the approximately 884 moved specification lines are documentation but
still require focused traceability review.

Out of scope: runtime implementation; tests of unimplemented behavior; a Strict
TDD or archive-policy waiver; archiving any change in this phase; GitHub/PR
lifecycle actions; and copying, restoring, modifying, or inspecting historical
branch content.

### Risks
- A future delta placed under this reclassification change's `specs/` tree would again be merged as current behavior during archive.
- A textual rewrite during relocation can silently lose a requirement or scenario; the apply phase needs byte-level move validation and a 22/64 source-anchor count.
- Splitting contracts too early without respecting SQLite phases 4-10 and phases 11-17 could create implementation work that cannot truthfully run or publish.

### Ready for Proposal
Yes — propose a documentation-only reclassification with a non-delta evidence relocation, exact 22-requirement/64-scenario traceability matrix, future ownership map, archive-precondition checks, and explicit exclusions. Do not propose runtime behavior, an archive action, or a policy exception.
