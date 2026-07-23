# Design: Prudent Health-Pattern Guidance Governance

## Purpose And Delivery Boundary

This Phase 1 delivery establishes documentary governance for evaluating a
possible future health-pattern guidance capability. It authorizes neither
clinical content nor product behavior. The current backend-only implementation
remains unchanged; descriptive educational dashboard behavior is a future state.

The design creates accountable records and gates so that a later, separately
approved change can determine whether a narrowly defined claim is eligible for
its own implementation proposal. A governance record is evidence of review, not
evidence that a product feature, clinical conclusion, or regulatory status has
been approved.

Phase 1 explicitly excludes claim selection or wording; warning signs; symptoms;
diseases; actions; urgency; algorithms; thresholds; data rules; storage schemas;
APIs; UI; and product implementation.

## Governance Document Set And Ownership

The governance owner maintains the following controlled document set. Before the
process is used, the owner records the authorization criteria for clinical and
editorial reviewers; no credential, jurisdiction, individual, or legal standard
is assumed by this design.

For the confirmed single-maintainer installation, the maintainer holds the
governance-owner role. Future separation of those roles requires a new access and
handoff decision before another person receives controlled-record access.

| Document | Accountable owner | Purpose |
|---|---|---|
| Intended-use record | Governance owner | Defines proposed use, intended user, private local context, exclusions, foreseeable misuse, effective date, and maximum next-review date. |
| Source register | Governance owner | Tracks source provenance, version/currency, applicability, limitations, conflicts, effective date, and maximum next-review date. |
| Clinical review record | Authorized clinical-review role | Records evidence assessment for a prospective claim version. |
| Editorial review record | Authorized editorial-review role | Records whether prospective wording would remain bounded and understandable. |
| Safety case and risk register | Governance owner | Records hazards, controls, residual-risk rationale, stop criteria, owner, effective date, and maximum next-review date. |
| Incident and correction record | Governance owner | Records intake, assessment, containment, correction, and re-approval decisions. |
| Warning-sign readiness evaluation | Governance owner | Records only the future decision gates required before a separate warning-sign proposal. |
| Evaluation evidence pack | Governance owner | Collects synthetic reviewer scenarios, gate results, and privacy-control evidence. |
| Spain/EU assessment record | Governance owner | Records the private, versioned jurisdictional process gate, its exact scope, outcome, validity, limitations, and reassessment triggers. |

The governance owner is responsible for completeness, current status, access
control, version history, and withdrawal. Clinical and editorial reviewers have
independent decisions: neither may silently substitute for the other, and the
governance owner cannot turn incomplete review into approval.

The maintainer has confirmed that review-role authorization must define written
competency, independence, and conflict-of-interest criteria. Identities and
credentials remain private and are not governance artifacts in this repository.

## Record Locations And Privacy Boundary

Versioned OpenSpec artifacts in this repository contain the governance model,
requirements, decision rationale, and sanitized verification results only. They
MUST NOT contain real health exports, values, identifiable context, screenshots,
operational incident narratives, source excerpts, claim wording, clinical
content, reviewer identities, credentials, access details, or private source
queries.

Controlled operational records MUST be kept in a private, access-restricted
governance workspace outside versioned artifacts, images, CI artifacts, logs,
telemetry, and support attachments. This workspace, its encryption, its access
restriction,
its encrypted backups, and restoration capability are confirmed prerequisites;
this change does not assert that they exist or have been tested. Before the
workspace receives records, the maintainer must provision and evidence those
controls and define its category-based structure, retention, and deletion policy
in writing. This Phase 1 design does not prescribe or verify a database, file
format, backup implementation, or restoration procedure.

Authorized clinical and editorial reviewers MUST NOT receive direct access to the
private workspace. The governance owner MUST provide each reviewer only the
minimal,
versioned review package needed through a private controlled channel, then
preserves the returned independent review record in the workspace. The package
and return path must not put health data, identities, credentials, or source text
in versioned artifacts.

Public or versioned references use stable internal record identifiers and
sanitized status summaries only. Links to external sources record a stable
identifier or link and required provenance metadata; they do not copy source text
when licensing, confidentiality, or privacy would make copying inappropriate.
Review material uses minimal synthetic examples with fictional context. A review
must reject any artifact that contains or can reconstruct real health data.

## Controlled Register And Review Flow

A prospective future claim cannot enter review until its intended-use record is
current and its source-register entries are complete. The register preserves
successive versions rather than overwriting provenance, applicability,
limitations, status, conflict assessment, or review dates. A changed source or
claim version is a new review subject; similarity of identifiers or wording does
not preserve approval.

Clinical review assesses source relevance, currency, applicability, limitations,
and conflicts against the intended-use boundary. Editorial review separately
assesses the proposed future material for scope, non-diagnostic framing,
foreseeable misuse, comprehension risks, and alignment with the clinical-review
limitations. Each result records its version, date, outcome, rationale,
limitations, dependencies, and maximum next-review date. The safety case must be
current before both completed reviews can make the subject eligible for a later
implementation proposal.

No Phase 1 record may draft, select, approve for display, or activate content.
Its review outcomes concern eligibility to advance to a future proposal only.

Before this process is used, the governance owner MUST define a maximum review
interval for every controlled record type. Every record instance MUST include an
effective or completed date and a next-review date no later than that maximum;
the owner may set an earlier date but may not extend validity through an
unscheduled or implicit rolling cadence. Clinical reviews, editorial reviews,
the safety case, source entries, intended-use records, evaluation evidence, and
the Spain/EU assessment each have their own recorded maximum next-review date.

Review is due immediately when intended use, user, product scope, jurisdiction,
source status or content, prospective claim or wording version, reviewer-role
criteria, safety controls, incident state, private-environment controls, or an
assessment assumption, limitation, outcome, or scope changes materially. A
triggered, missing, or overdue review makes the affected subject ineligible and
suppressed until a new current record is completed. Reaching the recorded
next-review date is expiry, not a grace-period notification.

## Fail-Closed Eligibility State Machine

The governance owner evaluates the combined source, review, safety, and incident
state whenever a record is created, changed, reaches a review date, receives a
conflict, or receives an incident. The state machine is intentionally
fail-closed:

```text
not-ready --> under-review --> eligible-for-separate-proposal
     |             |                     |
     +-------------+---------------------+
                   |
                suppressed
                   |
            remediation-review
                   |
          under-review or suppressed
```

`not-ready` applies when the intended-use boundary, source register, reviewer
authorization, dual reviews, safety case, or required evaluation evidence is
absent. `under-review` has no approval effect. `eligible-for-separate-proposal`
requires all required records to be current, complete, and mutually consistent;
it does not authorize implementation or display.

Any withdrawn, expired, unavailable, superseded, or materially changed source;
unresolved evidence conflict; missing, superseded, or overdue clinical/editorial
review; unacceptable safety status; relevant incident; or incomplete correction
immediately moves the subject to `suppressed`. Suppression is the default whenever
status cannot be established. It means no future content can advance or remain
eligible, and the only safe product fallback is descriptive data only.

`remediation-review` records investigation and correction without restoring
eligibility. Re-approval requires current source-register review, recorded
resolution or disposition of each relevant conflict and incident, a current
safety case, and new independent clinical and editorial records for the exact
subject version. Historical approval never carries forward automatically.

Before any future released capability can display interpretive material, its
separate proposal must define an authoritative eligibility decision with bounded
freshness. A missing, stale, unreadable, or unavailable eligibility decision must
produce the descriptive-only fallback; cached interpretive material cannot remain
visible merely because the last known decision was eligible.

Eligibility for a future interpretive proposal also requires the appropriate
Spain and European Union assessment. The governance owner MUST retain its
deliverable as a private, versioned record with a stable identifier; commissioned
and completed dates; a valid-through date; exact product scope, intended use,
users, context, and jurisdictions assessed; the advisor role and the predefined
qualification, independence, and conflict-of-interest criteria applied; the
recorded outcome and rationale; assumptions, limitations, dependencies, and
conditions; reassessment triggers; and governance-owner acceptance and status.

The assessment is current only while all required fields are complete, its
outcome permits advancement for the exact proposed scope, its valid-through date
has not been reached, and no reassessment trigger has occurred. A missing field,
scope mismatch, non-permitting or conditional outcome with unmet conditions,
expired validity, changed assumption, or triggered reassessment blocks the future
proposal and moves the subject to `suppressed`. Advisor identity and supporting
qualification evidence remain private. This process gate assumes and declares no
specific law, credential, classification, approval, or favorable outcome.

## Safety Case, Incidents, Corrections, And Fallback

The safety case and risk register cover false reassurance, unnecessary anxiety,
delayed care, inappropriate self-management, implied causation, stale evidence,
repeated exposure, privacy exposure, poor applicability, and data-quality limits.
For every risk, the records identify the accountable owner, expected control,
residual-risk rationale, effective date, maximum next-review date, and condition
requiring suppression or withdrawal.

The incident and correction process is documentary and must not collect real
health data. It records a sanitized report reference, assessment, containment
decision, affected governance-record versions, correction decision, audit trail,
and re-approval requirement. Material uncertainty or a failed containment action
requires suppression pending remediation. The fallback is removal of any future
interpretive material and retention of descriptive data presentation only; it
must not imply normality, safety, or absence of concern.

## Warning-Sign Readiness Gate

Phase 1 evaluates whether a later, separate proposal has a complete governance
path for warning-sign content. The readiness evaluation must require traceable
recognized sources, applicability assessment, symptom and evidence conditions,
independent clinical and editorial review, no-signal limitations, a dedicated
safety case, suppression and incident handling, privacy review, and synthetic
comprehension validation.

The evaluation records only whether these gates exist and are satisfied. It MUST
NOT identify, rank, describe, associate, or activate any warning sign, symptom,
disease, metric, threshold, emergency action, or urgency instruction. It MUST
NOT treat an isolated dashboard metric or the absence of a signal as evidence of
safety.

## Verification Strategy

Verification is a document-control review, not product testing. The evaluation
evidence pack uses synthetic scenarios to demonstrate that:

1. Intended use, exclusions, foreseeable misuse, ownership, effective dates, and
   maximum next-review dates are present before review begins.
2. Missing provenance, stale records, source withdrawal, unresolved conflicts,
   missing independent review, overdue review, incidents, and incomplete
   corrections each result in suppression.
3. Re-approval creates new current-review evidence and does not reuse prior
   approval merely because an identifier remains the same.
4. The safety case contains required hazards, stop criteria, accountable owner,
   and descriptive-only fallback.
5. The warning-sign evaluation contains gates only and no clinical content.
6. Versioned artifacts and evidence packs contain only synthetic, sanitized
   material and no external transfer of health information.
7. Every controlled record has a maximum next-review date, and expiry or a
   material reassessment trigger suppresses eligibility without a grace period.
8. The private Spain/EU assessment record contains every required process field,
   and missing, expired, mismatched, or triggered state blocks advancement.

Reviewers also inspect repository diffs for privacy-boundary violations and
confirm that Phase 1 has introduced no code, API, UI, algorithm, threshold,
claim, clinical content, or operational-record artifact.

## Alternatives Rejected

| Alternative | Rejection rationale |
|---|---|
| Store all governance records in versioned repository files | Would expose sensitive operational context and create an inappropriate public audit trail. |
| Treat a source citation or one reviewer as sufficient | Cannot establish current applicability, independent review, conflict handling, or safety ownership. |
| Leave previously reviewed material eligible until manually withdrawn | Fails open on expired, conflicting, or unavailable evidence. |
| Include warning-sign examples to make the process concrete | Would introduce prohibited clinical content and imply a feature decision before governance is complete. |
| Implement a governance database or workflow now | Expands Phase 1 into schemas, APIs, and product behavior without an approved need. |

## Rollback And Limits

Phase 1 rollback leaves the current backend unchanged and records a new decision
that supersedes this policy. ADR 0005 and the archived change remain as historical
evidence. If a later capability based on this work is withdrawn, its governed
material must be suppressed and its future dashboard must revert to descriptive
data only. Private operational records remain subject to their own retention and
incident obligations; rollback must not erase audit evidence.

This design does not establish clinical validity, regulatory classification,
legal compliance, reviewer qualifications, source selection, a clinical claim,
or authorization for implementation. It does not resolve whether the product
should ever progress beyond descriptive education. A separate approved proposal
is required before any capability, content, data handling, or technical design is
considered.
