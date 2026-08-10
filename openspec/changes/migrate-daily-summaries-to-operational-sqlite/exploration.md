## Exploration: Consolidate remaining operational SQLite delivery work

### Current State

`main` is clean at `c3e03dc`; phases 1–12 are merged (36/64 tasks). The operational schema, maintenance gate, candidate-root routing, reconciliation staging, and atomic sealing already exist. No candidate-construction, independent semantic-comparison, restore, cutover, or readiness implementation exists yet.

The remaining implementation is already arranged as two dependency-closed delivery groups:

| Dependency chain | Existing capability | Remaining result |
|---|---|---|
| 13 → 14 | Gate/drain, pointer layout, operational schema, reconciliation staging/seal, `semantic_evidence` schema | Build an immutable candidate and produce the independent manifest-bound evidence that Phase 12 requires before any private seal. |
| 14 → 15 → 16 → 17 | Candidate plus successful semantic evidence | Prove recoverability, perform crash-safe cutover logic, then document and rehearse readiness. |

Phase 13 depends on the existing gate (`src/maintenance.py`), candidate schema (`src/storage_schema.py`), operational/reconciliation persistence (`src/operational_store.py`, `src/reconciliation.py`), and seal evidence binding. Phase 14 must consume the Phase-13 candidate and must stay independent of operational selection; its successful record is the producer for the `semantic_evidence` admission already enforced by Phase 12. Phase 15 requires the verified candidate/comparison result. Phase 16 must not make a candidate selectable until Phase 15 has passed its isolated restore contract. Phase 17 depends on the implemented recovery and cutover commands so that its rehearsal and runbook describe executable behavior.

### Affected Areas

- `scripts/migrate_storage.py` — new Phase-13 candidate builder and Phase-14 comparator; later the Phase-16 cutover CLI/state-machine boundary.
- `tests/test_storage_migration.py` — synthetic source/candidate construction, population/evidence-gap comparison, and migration-resume tests for phases 13–14.
- `src/maintenance.py`, `src/storage_schema.py`, `src/operational_store.py`, `src/reconciliation.py` — existing gate, dataset-state, immutable artifact, lineage, and semantic-evidence seams that migration code must use rather than duplicate.
- `scripts/verify_restore.py`, `tests/test_restore.py` — new Phase-15 backup/isolated-restore orchestration and fake-Restic tests.
- `tests/test_cutover.py`, `tests/test_app.py` — Phase-16 synthetic lifecycle, restart, pointer, gate, and API-compatibility checks.
- `README.md`, `docs/architecture/decisions/0004-separate-operational-and-analytical-storage.md`, and a new operations runbook path — Phase-17 readiness/rollback documentation; no existing operations-runbook file is present on `main`.

### Approaches

1. **Keep the two existing delivery groups: 13–14, then 15–17** — run two sequential future `sdd-apply` invocations, each producing work-unit commits and one stacked-to-`main` PR.
   - Pros: Preserves the hard dependency that recovery/cutover starts only from a merged, independently reviewed candidate/comparator; stays within the recorded 1,000 non-documentation-line ceiling; gives two clean rollback boundaries; minimizes executor count without combining unrelated failure domains.
   - Cons: Requires one merge between executor invocations and two reviews.
   - Effort: Medium.

2. **One executor invocation for phases 13–17, sliced into two PRs** — have one executor author both groups sequentially but deliver separate work-unit commits/stacked slices.
   - Pros: Removes one executor startup/context cost.
   - Cons: Conflicts with the approved stacked-to-`main` rule that later work begins only after its predecessor merges; Phase 15–17 would be authored against unmerged migration/comparator behavior, increasing rework and review-coupling risk. It also weakens the independent rollback/review checkpoint between candidate correctness and production-lifecycle logic.
   - Effort: Medium, with higher delivery risk.

3. **One PR for phases 13–17** — combine the entire remaining implementation and its tests/docs.
   - Pros: One review and merge.
   - Cons: The recorded forecasts total 1,420–1,770 non-documentation changed lines, exceeding the 1,000-line ceiling by 420–770 lines; it mixes candidate correctness, backup recovery, irreversible rollback-boundary logic, and documentation in one rollback unit. This is not compatible with the cached `auto-chain` strategy.
   - Effort: High risk.

### Recommendation

Use **two future `sdd-apply` invocations and two stacked-to-`main` PRs**. This is the minimum practical delivery count:

| Apply block | Tasks and work-unit commits | Forecast | Focused verification | Rollback boundary | Native review risk |
|---|---|---:|---|---|---|
| A | Phase 13 candidate builder; Phase 14 independent comparator/evidence producer | 610–770 non-documentation lines | `python -m pytest tests/test_storage_migration.py` | Discard the candidate only; legacy sources remain untouched and the comparator mutates no source state. | Likely 4 lenses, driven by source immutability, receipt/backfill reconstruction, semantic independence, and private evidence handling; selection remains native-review-owned. |
| B | Phase 15 backup/restore; Phase 16 cutover state machine; Phase 17 runbook/readiness rehearsal | 810–1,000 non-documentation lines | `python -m pytest tests/test_storage_migration.py tests/test_restore.py tests/test_cutover.py tests/test_app.py && python -m unittest scripts.test_check_repository` | Discard isolated restores; before a post-cutover live receipt, journal rollback restores the verified legacy application/data pair. | Likely 4 lenses, driven by encrypted recovery, journal/pointer crash safety, authentication/API continuity, and the irreversible first-live-receipt boundary; selection remains native-review-owned. |

Within each block, preserve strict RED → GREEN → REFACTOR per numbered phase and commit by behavior, not file type. Block A may use two work-unit commits in one PR; Block B may use three. Tests and the relevant documentation stay with their behavior commit. The required full verification remains the configured suite and repository checks before each review.

All phases 13–17 **must not be one PR**. They can be authored mechanically in one invocation only by pre-authoring a later stacked slice, but that is not a safe delivery consolidation under the recorded merged-predecessor/`auto-chain` contract. Therefore, they should be treated as **two apply invocations**, not one.

After both implementation PRs merge, run final `sdd-verify` separately. Archive only after final implementation acceptance and the maintainer-only private gate are complete; neither verification/archive nor M.1–M.6 belongs in either implementation apply block. M.1–M.6 remain explicit maintainer-operated private production work and must not be bundled with code, CI, synthetic tests, commits, or PRs.

### Risks

- The 810–1,000-line Block-B forecast has little headroom; its executor must recount non-documentation additions plus deletions after RED and split only if the recorded ceiling would be exceeded.
- A comparator that reuses operational selection logic would invalidate the required independent semantic check; Phase 14 must remain separate in design even when delivered in Block A.
- Production migration, manifest approval/sealing, backup credentials, lifecycle control, cutover, POST reopening, and legacy archival remain private maintainer decisions, not executable agent work.

### Ready for Proposal

Yes. No task-plan rewrite is needed: retain delivery groups 6 and 7 as the two implementation units, use one PR per group, then keep final verification/archive and M.1–M.6 outside implementation delivery.
