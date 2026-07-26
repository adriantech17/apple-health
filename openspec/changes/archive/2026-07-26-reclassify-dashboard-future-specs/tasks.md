# Tasks: Reclassify Dashboard Future Specs

## Review Workload Forecast

| Field | Value |
|---|---|
| Non-documentation | 650–850 Python/test lines; 1,000-line session budget |
| Total authored | 1,100–1,350 with planning artifacts, manifest, and matrix |
| Pure renames | Four byte-identical specs (~884 lines), tracked separately |
| Delivery | High risk; maintainer-approved `size:exception`; strategy `size-exception` |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

Policy activation and relocation are coupled. The maintainer approved `size:exception`; apply remains one PR with three reviewable work-unit commits.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Discovery + manifest | Commit 1 | `.venv/bin/python -m unittest scripts.test_check_repository.PlanningEvidenceDiscoveryTests scripts.test_check_repository.RelocationManifestTests` | `.venv/bin/python -m unittest scripts.test_check_repository` | Root/path/manifest helpers and tests |
| 2 | Matrix | Commit 2 | `.venv/bin/python -m unittest scripts.test_check_repository.RequirementMatrixTests` | `.venv/bin/python -m unittest scripts.test_check_repository` | Matrix helpers and tests |
| 3 | Atomic integration | Commit 3 | `.venv/bin/python -m unittest scripts.test_check_repository.RepositoryGovernanceCliTests` | `.venv/bin/python scripts/check_repository.py` | Audit wiring, moves, manifest, matrix |

## Phase 1: Baselines and Discovery

- [x] 1.1 Create `.venv` with `python3 -m venv .venv`, install `.[test]`, and confirm `.venv/bin/python` is ignored and available before RED.
- [x] 1.2 RED `scripts/test_check_repository.py`: pin commits `12cf7d316887f206fcdd0041435b8622445de042` and `14dd29f03fe08d35a89b6ec23bbd07fbbb02eb36`, four specs, five narratives, and 22/64 counts.
- [x] 1.3 RED `scripts/test_check_repository.py`: missing, duplicate, malformed, conflicting active/archive roots and premature archives.
- [x] 1.4 RED `scripts/test_check_repository.py`: reject `requirements.txt`, `CMakeLists.txt`, executable Markdown/MDX, and `README.sh`; accept contracted non-executable evidence.
- [x] 1.5 GREEN/REFACTOR `scripts/check_repository.py`: exact-one active-or-archive root discovery and fail-closed path classification; add no subprocess.

## Phase 2: Manifest Governance

- [x] 2.1 RED `scripts/test_check_repository.py`: malformed/noncanonical JSON, wrong commits, unsafe paths, ordering, non-4 entries, and non-5 narratives.
- [x] 2.2 RED `scripts/test_check_repository.py`: missing/altered bytes, blob/SHA/count or narrative drift, mergeable/conflicting paths, and ambiguous rollback.
- [x] 2.3 GREEN/REFACTOR `scripts/check_repository.py`: validate schema v1, commits, narratives, bytes, SHA-256, Git blobs, placement, archive gates, and restoration.

## Phase 3: Matrix Governance

- [x] 3.1 RED `scripts/test_check_repository.py`: malformed columns or declared/parsed drift from exactly 22 requirements and 64 scenarios.
- [x] 3.2 RED `scripts/test_check_repository.py`: altered names, missing/duplicate anchors/scenarios, invalid owner cardinality/allowlist, or lost SQLite dependencies.
- [x] 3.3 GREEN/REFACTOR `scripts/check_repository.py`: parse `openspec/changes/reclassify-dashboard-future-specs/evidence/recover-dashboard-future-specs/requirement-matrix.md`; enforce exact headings, slugs, scenario names/counts, unique anchors, one owner, and dependencies.

## Phase 4: Atomic Integration and Relocation

- [x] 4.1 RED `scripts/test_check_repository.py`: CLI cases for incomplete state, mergeable evidence, archive order, manifest, matrix, and rollback.
- [x] 4.2 GREEN/REFACTOR `scripts/check_repository.py`: wire governance into `main()` with authoritative root/tracked paths.
- [x] 4.3 `git mv` four `openspec/changes/recover-dashboard-documentation/specs/{accessible-descriptive-dashboard,dashboard-operational-data,private-dashboard-access,dashboard-release-baseline}/spec.md` files into matching `openspec/changes/reclassify-dashboard-future-specs/evidence/recover-dashboard-future-specs/` paths without byte edits.
- [x] 4.4 Create canonical `openspec/changes/reclassify-dashboard-future-specs/evidence/recover-dashboard-future-specs/relocation-manifest.json` and `openspec/changes/reclassify-dashboard-future-specs/evidence/recover-dashboard-future-specs/requirement-matrix.md` with exact 22/64 evidence and owners; make no editorial changes.

## Phase 5: Verification and Rollback

- [x] 5.1 Run focused unittests, then `.venv/bin/python -m unittest scripts.test_check_repository`.
- [x] 5.2 Run `.venv/bin/python -m pytest && .venv/bin/python scripts/check_repository.py && .venv/bin/python -m unittest scripts.test_check_repository && git diff --check`.
- [x] 5.3 Run `.venv/bin/python -m unittest scripts.test_check_repository.PlanningEvidenceRollbackTests`; inspect `git diff --summary` for four-file restoration/rename identity.
- [x] 5.4 Inspect `scripts/check_repository.py`, `scripts/test_check_repository.py`, and evidence diffs: no narrative edits, runtime behavior, historical-branch access, archive, GitHub mutation, or policy waiver.
