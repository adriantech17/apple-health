from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT / "openspec/changes/evaluate-prudent-health-pattern-guidance"


def normalized(text: str) -> str:
    return " ".join(text.split())


class HealthGuidanceGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = normalized(
            (CHANGE / "specs/health-pattern-guidance-governance/spec.md").read_text()
        )
        cls.design = normalized((CHANGE / "design.md").read_text())
        cls.exploration = normalized((CHANGE / "exploration.md").read_text())
        cls.proposal = normalized((CHANGE / "proposal.md").read_text())
        cls.tasks = normalized((CHANGE / "tasks.md").read_text())
        cls.adr = normalized(
            (
                ROOT
                / "docs/architecture/decisions/0005-govern-future-health-pattern-guidance.md"
            ).read_text()
        )

    def assert_contract(self, document: str, expected: str) -> None:
        self.assertIn(normalized(expected), document)

    def test_excludes_clinical_decision_support(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Phase 1 governance artifacts MUST record a proposed intended use, intended
            user, private single-person local-installation context, excluded uses, and
            foreseeable misuse before a future health-meaning claim can be considered.
            The record MUST state that the product is educational and non-diagnostic
            and MUST identify the accountable governance owner and its maximum
            next-review date.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Excluded uses MUST expressly include diagnosis, triage, urgency or
            emergency guidance, treatment, clinical claims, and replacement of
            professional judgment. Foreseeable misuse MUST include interpreting a
            data pattern, correlation, absence of a statement, or governance approval
            as a clinical conclusion, safety assessment, causal assertion, or action
            recommendation.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A proposed use excludes clinical decision support
            - GIVEN Phase 1 has a proposed intended-use record
            - WHEN the record is reviewed
            - THEN it identifies its user and local private context, its exclusions
            and foreseeable misuse, its owner, and its maximum next-review date.
            - AND it expressly excludes diagnosis, triage, urgency guidance,
            treatment, and clinical claims.
            """,
        )

    def test_rejects_phase_one_product_prompts(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Phase 1 artifacts MUST NOT select, draft, approve for display, or activate
            any health-meaning claim, warning sign, pattern-linked prompt,
            recommendation, or user-facing guidance. They MUST NOT define algorithms,
            data rules, thresholds, metric eligibility, or triggers for patterns or
            health interpretation.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Phase 1 MUST NOT introduce or authorize UI, dashboard, API, storage,
            authentication, data-processing, deployment, telemetry, third-party
            transfer, or other product changes. A governance artifact MUST NOT be
            represented as an implementation approval; each future product capability
            requires a separately approved change.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A proposed pattern-linked prompt is submitted during Phase 1
            - GIVEN a governance record exists
            - WHEN a submission includes a prompt tied to a person's measured pattern
            or a proposed threshold, algorithm, or trigger
            - THEN the submission is outside Phase 1 and is not selected, drafted,
            approved, activated, or implemented.
            """,
        )

    def test_exploration_contains_no_drafted_pattern_prompt(self) -> None:
        self.assertNotIn(
            "consider discussing this persistent observation",
            self.exploration,
        )
        self.assertIn(
            "Phase 1 must not draft, select, or approve their wording",
            self.exploration,
        )

    def test_requires_source_provenance(self) -> None:
        self.assert_contract(
            self.spec,
            """
            The entry MUST record the source publisher, title, stable link or
            identifier, version or publication date when available, retrieval date,
            applicable population and context, exact supported claim, evidence
            limitations, source status, conflict status, effective date, and maximum
            next-review or withdrawal date.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The register MUST preserve a traceable history of changes to source
            metadata, status, and the supported claim. Phase 1 MUST NOT select clinical
            sources or assert that a source supports any specific health claim. Source
            text MUST NOT be copied to repository artifacts where licensing or privacy
            constraints prohibit it.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A future claim lacks traceable source metadata
            - GIVEN a future health-meaning claim is proposed for review
            - WHEN no controlled source-register entry provides the required
            provenance, applicability, limitations, effective date, and maximum
            next-review date
            - THEN the claim cannot advance to approval or future display consideration.
            """,
        )

    def test_requires_independent_dual_review(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Governance MUST require separate recorded clinical and editorial review
            before a future health-meaning claim may be approved for a later
            implementation proposal. Each review record MUST identify the reviewed
            claim version, corresponding source-register entry or entries, reviewer
            role, review date, outcome, rationale, limitations, conflicts considered,
            and a maximum next-review date.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The governance process MUST define who is authorized to perform each role
            before using the role for approval. Phase 1 MUST NOT assume a credential,
            jurisdiction, legal standard, reviewer identity, or clinical conclusion.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: Editorial review exists without clinical review
            - GIVEN a future claim has a completed editorial review record
            - WHEN its approval status is evaluated
            - THEN the claim remains unapproved until a corresponding recorded
            clinical review satisfies the defined governance process.
            """,
        )

    def test_blocks_missing_external_preconditions(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Phase 1 MUST remain documentary governance only. Funding of Phase 1 MUST
            NOT be represented as authorization for functionality, claims, dashboard
            changes, or regulatory approval.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The private record environment, encryption, access restriction, encrypted
            backup, and verified restoration are prerequisites that Phase 1 MUST NOT
            represent as existing, tested, or operational. Before controlled records
            are used, that environment MUST be provisioned with evidenced access
            restriction and encryption, a written category-based structure, retention,
            and deletion policy, evidenced encrypted backup, and a successful evidenced
            restoration test.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The governance process MUST provide authorized clinical and editorial
            reviewers with only the minimal, versioned review package required through
            a private controlled channel. Reviewers MUST NOT receive direct access to
            the private governance workspace, and their independent returned records
            MUST remain private.
            """,
        )
        self.assert_contract(
            self.spec,
            "Warning-sign content MUST remain outside Phase 1 and require its own future proposal.",
        )
        self.assert_contract(
            self.spec,
            """
            The governance owner MUST commission and retain the deliverable as a
            private, versioned record. It MUST contain a stable identifier and version;
            commissioned, completed, and valid-through dates; exact product scope,
            intended use, users, context, and jurisdictions assessed; advisor role and
            predefined qualification, independence, and conflict-of-interest criteria;
            outcome and rationale; assumptions, limitations, dependencies, and
            conditions; reassessment triggers; and governance-owner acceptance and
            status. The advisor MUST satisfy the recorded criteria, but Phase 1 MUST
            NOT invent or assert a law, credential, classification, approval, or
            favorable outcome.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A future proposal lacks an external governance precondition
            - GIVEN Phase 1 documentary artifacts are complete
            - WHEN a future interpretive proposal lacks the required assessment or the
            assessment is incomplete, expired, scope-mismatched, or due for
            reassessment, or the private record environment lacks evidenced operational
            controls
            - THEN the proposal remains blocked.
            - AND Phase 1 does not imply approval, functionality, or a regulatory outcome.
            """,
        )

    def test_suppresses_unavailable_eligibility(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Missing, stale, unreadable, or unavailable eligibility MUST suppress
            interpretive material and preserve descriptive data only. Cached prior
            eligibility MUST NOT keep interpretive material visible.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: Current eligibility cannot be established
            - GIVEN a future released capability previously displayed eligible material
            - WHEN its current authoritative eligibility is missing, stale, unreadable,
            or unavailable
            - THEN the capability suppresses the interpretive material.
            - AND descriptive data remains available without implying safety or normality.
            """,
        )

    def test_suppresses_expired_sources(self) -> None:
        self.assert_contract(
            self.spec,
            """
            A future claim MUST be suppressed by default when any required source is
            withdrawn, expired, unavailable for review, or in an unresolved conflict
            state, or when either required review is missing, superseded, or past its
            re-review date.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Re-approval MUST require review of current source-register entries,
            recorded resolution of relevant conflicts, and new clinical and editorial
            approval records for the claim version. Prior approval MUST NOT remain
            valid merely because the claim wording or its identifier remains unchanged.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: An approved claim reaches its source review date
            - GIVEN a future claim was previously approved with a source re-review date
            - WHEN that date passes without completed current-source and dual-review records
            - THEN its status becomes suppressed.
            - AND it cannot return to an approvable state without recorded re-approval.
            """,
        )

    def test_suppresses_records_at_deadline_or_trigger(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Governance MUST define a maximum review interval for every controlled record
            type. Each record instance MUST state its effective or completed date and a
            next-review date no later than that maximum. Review MUST become due
            immediately after a material change to intended use, user, product scope,
            jurisdiction, source status or content, prospective claim or wording,
            reviewer-role criteria, safety controls, incident state,
            private-environment controls, or an assessment assumption, limitation,
            outcome, or scope. Reaching the next-review date or any reassessment trigger
            MUST suppress the affected subject without a grace period until a new
            current record is completed.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A controlled record reaches its maximum next-review date
            - GIVEN a future claim depends on a controlled record with a maximum
            next-review date
            - WHEN that date is reached or a material reassessment trigger occurs
            - THEN the affected subject is immediately suppressed without a grace period.
            - AND it remains ineligible until a new current record is completed.
            """,
        )

    def test_suppresses_source_conflicts(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Governance MUST define explicit statuses for source currency, evidence
            conflict, claim approval, and suppression. A future claim MUST be
            suppressed by default when any required source is withdrawn, expired,
            unavailable for review, or in an unresolved conflict state, or when either
            required review is missing, superseded, or past its re-review date.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: Sources conflict
            - GIVEN registered sources for a future claim have an unresolved conflict
            - WHEN the claim status is evaluated
            - THEN the claim is suppressed.
            - AND the record identifies the conflict for resolution rather than treating
            it as support for the claim.
            """,
        )

    def test_contains_incidents_with_descriptive_fallback(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Before a future implementation proposal may consider health-meaning
            content, governance MUST require a versioned safety case and risk register.
            They MUST cover false reassurance, unnecessary anxiety, delayed care,
            inappropriate self-management, misunderstood correlation or causation,
            stale evidence, repeated exposure, privacy exposure, and data-quality or
            applicability limits.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The safety case MUST define acceptance criteria, residual-risk rationale,
            suppression or withdrawal criteria, accountable owner, effective date,
            maximum next-review date, and a safe fallback to descriptive data only.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Governance MUST define an incident and correction process that records report
            intake, assessment, containment, suppression where required, correction
            decision, audit trail, and the conditions for re-approval. Phase 1 MUST NOT
            create an incident workflow that receives real health data.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: A material source error is reported
            - GIVEN a future approved claim has a reported material source error
            - WHEN the incident process assesses the report
            - THEN the assessment, containment decision, and audit record are retained.
            - AND the claim is suppressed when the error meets its withdrawal criteria.
            - AND descriptive data only remains the required safe fallback.
            """,
        )

    def test_warning_sign_evaluation_contains_no_content(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Phase 1 MUST evaluate and record the governance prerequisites that a later,
            separate warning-sign proposal would need, including source traceability,
            applicability, clinical and editorial review, symptom and evidence
            conditions, no-signal limitations, safety case, suppression, incident
            response, and validation.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Phase 1 MUST NOT name, select, rank, draft, paraphrase, display, activate, or
            associate warning signs with diseases, metrics, thresholds, symptoms,
            emergency actions, or urgency instructions. It MUST NOT assert that an
            isolated dashboard metric is sufficient for a warning-sign conclusion, or
            that no signal means safety or absence of concern.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: Warning-sign requirements are evaluated
            - GIVEN the Phase 1 warning-sign governance evaluation is reviewed
            - WHEN its contents are inspected
            - THEN it lists decision gates and evidence requirements only.
            - AND it contains no selected signal, clinical wording, disease association,
            threshold, symptom list, emergency action, or activated behavior.
            """,
        )

    def test_preserves_private_synthetic_evidence(self) -> None:
        self.assert_contract(
            self.spec,
            """
            Phase 1 governance artifacts MUST preserve the private, local-by-default,
            single-person boundary and MUST NOT require third-party services, telemetry,
            or external transfer of health values, interpreted statements, audit
            records, or source queries. They MUST retain the existing separation
            between browser sessions and ingestion credentials.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            Evaluation evidence, examples, reviewer scenarios, and tests for Phase 1
            MUST use minimal synthetic data only. They MUST NOT contain, process,
            publish, or send real health exports, identifiable health information,
            screenshots, or derived records outside the private installation.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            The artifacts MUST state that locality and synthetic evidence do not
            establish clinical validity or regulatory status.
            """,
        )
        self.assert_contract(
            self.spec,
            """
            #### Scenario: Governance evaluation evidence is prepared
            - GIVEN Phase 1 evidence is assembled for review
            - WHEN examples and validation material are checked
            - THEN they contain only synthetic health data and no external health-data
            transmission.
            - AND the material does not claim clinical validity, regulatory approval,
            or a change to the existing private local boundary.
            """,
        )
        self.assert_contract(
            self.design,
            """
            This workspace, its encryption, its access restriction, its encrypted
            backups, and restoration capability are confirmed prerequisites; this
            change does not assert that they exist or have been tested.
            """,
        )
        self.assert_contract(
            self.proposal,
            "These controls are not verified or operational through this change.",
        )
        self.assert_contract(
            self.tasks,
            "[ ] Provision and verify the private environment, encrypted backups, and a successful restoration test outside this repository.",
        )
        self.assert_contract(
            self.adr,
            "A future interpretive capability requires a separate approved proposal.",
        )


if __name__ == "__main__":
    unittest.main()
