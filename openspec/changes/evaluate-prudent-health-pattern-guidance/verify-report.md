# Verification: Evaluate Prudent Health-Pattern Guidance

## Preflight

- Mode: interactive, both.
- Delivery strategy: single PR with the maintainer-approved `size:exception`.
- Review budget: 2,500 lines.
- Scope: six OpenSpec artifacts, ADR 0005, its architecture index entry, and the
  pytest-discovered governance contract test.
- Excluded: product code, Git operations, and unrelated worktree changes, which
  remain independent from this change.
- Current implementation: backend only. This report does not claim that a
  dashboard or any health-pattern guidance behavior exists.

## Result

**Documentary status: pass. Operational readiness: blocked.** All nine
requirements and all twelve scenarios are represented by deterministic
document-control evidence and a focused pytest test. The governance model is
verified as documentation only. It does not make the private record environment,
encrypted backups, restoration, Spain/EU assessment, product behavior, or
clinical content existing, tested, approved, or operational.

The unchecked external-prerequisite tasks in `tasks.md` are intentional
fail-closed blockers. This change cannot authorize a future implementation
proposal until those private controls are evidenced and every applicable
governance record is current.

## Evidence Method

- **Document-control/manual deterministic:** inspect each complete normative
  obligation and Given/When/Then scenario, then inspect the complete scoped
  candidate for contradictory authorization or prohibited content.
- **Focused governance contract:** pytest discovers the test under `tests/`.
  Each method asserts complete normalized normative paragraphs and complete
  scenario blocks rather than isolated words or ambiguous substrings.
- **Runtime regression:** run the repository's existing backend and policy
  suites. Passing confirms no impact on current backend behavior; it does not
  establish future governance operations.
- **Synthetic evidence:** tests read documentary contracts only and introduce no
  real health data, identity, credential, source excerpt, or operational record.

## Requirement Compliance Matrix

| Requirement | Exact evidence | Result |
|---|---|---|
| Record intended use, exclusions, and foreseeable misuse | `spec.md`, `Requirement: Record Intended Use, Exclusions, And Foreseeable Misuse` | Pass: private single-person educational use, owner, maximum review date, clinical exclusions, and misuse are explicit. |
| Prohibit product and interpretive scope in Phase 1 | `spec.md`, `Requirement: Prohibit Product And Interpretive Scope In Phase 1` | Pass: no claim, algorithm, threshold, UI, API, storage, authentication, deployment, or implementation is authorized. |
| Maintain a controlled source register | `spec.md`, `Requirement: Maintain A Controlled Source Register` | Pass: complete provenance, applicability, limitations, currency, conflict, review, withdrawal, and history fields are mandatory; no source or claim is selected. |
| Record independent clinical and editorial review | `spec.md`, `Requirement: Record Independent Clinical And Editorial Review` | Pass: separate versioned records, complete outcomes, and maximum next-review dates are required; neither role substitutes for the other. |
| Apply confirmed governance preconditions | `spec.md`, `Requirement: Apply Confirmed Governance Preconditions`; `design.md`, `Record Locations And Privacy Boundary` | Pass as a documentary gate: private controls are explicitly not claimed as existing; the Spain/EU record has version, dates, exact scope and intended use, advisor criteria, outcome, limitations, and reassessment triggers. |
| Fail closed on currency, conflict, withdrawal, and review deadlines | `spec.md`, `Requirement: Fail Closed On Currency, Conflict, And Withdrawal`; `design.md`, `Fail-Closed Eligibility State Machine` | Pass: every record type requires a maximum review interval and every instance a maximum next-review date; expiry and material triggers suppress without a grace period. |
| Maintain a safety case and operational response | `spec.md`, `Requirement: Maintain A Safety Case And Operational Response` | Pass: hazards, criteria, owner, audit trail, containment, re-approval, and descriptive-only fallback are required without real health data. |
| Evaluate warning-sign governance without content | `spec.md`, `Requirement: Evaluate Warning-Sign Governance Without Content` | Pass: only future gates may be evaluated; signals, diseases, thresholds, symptoms, urgency, actions, wording, and behavior are prohibited. |
| Preserve privacy, locality, and synthetic evidence boundaries | `spec.md`, `Requirement: Preserve Privacy, Locality, And Synthetic Evidence Boundaries` | Pass: records remain private/local, repository evidence is synthetic, external health-data transfer is prohibited, and browser/ingestion credentials remain separated. |

## Scenario Compliance Matrix

| Scenario | Focused pytest method | Result |
|---|---|---|
| A proposed use excludes clinical decision support | `test_excludes_clinical_decision_support` | Pass: complete exclusions, misuse obligations, and scenario are asserted. |
| A proposed pattern-linked prompt is submitted during Phase 1 | `test_rejects_phase_one_product_prompts` | Pass: complete scope prohibition and rejection scenario are asserted. |
| A future claim lacks traceable source metadata | `test_requires_source_provenance` | Pass: every required source field and the blocked scenario are asserted. |
| Editorial review exists without clinical review | `test_requires_independent_dual_review` | Pass: complete dual-review record and no-substitution scenario are asserted. |
| A future proposal lacks an external governance precondition | `test_blocks_missing_external_preconditions` | Pass: private-control and Spain/EU deliverable obligations plus all blocked states are asserted. |
| Current eligibility cannot be established | `test_suppresses_unavailable_eligibility` | Pass: authoritative freshness, suppression, no cache fallback, and complete scenario are asserted. |
| An approved claim reaches its source review date | `test_suppresses_expired_sources` | Pass: complete expiry obligation and source deadline scenario are asserted. |
| A controlled record reaches its maximum next-review date | `test_suppresses_records_at_deadline_or_trigger` | Pass: per-record maximum dates, material triggers, immediate expiry, and no-grace fail-closed behavior are asserted. |
| Sources conflict | `test_suppresses_source_conflicts` | Pass: the complete conflict scenario requires suppression and recorded resolution. |
| A material source error is reported | `test_contains_incidents_with_descriptive_fallback` | Pass: complete incident obligations and containment/fallback scenario are asserted. |
| Warning-sign requirements are evaluated | `test_warning_sign_evaluation_contains_no_content` | Pass: complete content prohibition and gates-only scenario are asserted. |
| Governance evaluation evidence is prepared | `test_preserves_private_synthetic_evidence` | Pass: complete synthetic-only obligation and scenario are asserted, together with explicit non-operational prerequisite statements. |

## Runtime And Repository Checks

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_health_guidance_governance.py` | Pass: 13 focused tests discovered by pytest, including a cross-artifact negative check for prohibited drafted prompts. |
| `.venv/bin/python -m pytest` | Pass: full pytest suite, including the governance contract. |
| `.venv/bin/python scripts/check_repository.py` | Pass: repository audit. |
| `.venv/bin/python -m unittest scripts.test_check_repository` | Pass: repository-audit unit tests. |
| `git diff --check` plus no-index checks for scoped untracked files | Pass: no whitespace errors. |

## Residual Blockers

- The private governance environment, access restrictions, encryption, backup,
  restoration test, category structure, retention, deletion, and credential
  handling have not been operationally verified by this change.
- No Spain/EU assessment has been commissioned or completed. Its required process
  record is defined, but no law, advisor credential, classification, approval, or
  outcome is asserted.
- No health-pattern guidance, dashboard behavior, clinical content, source,
  algorithm, threshold, or released eligibility mechanism exists through this
  documentary change.
