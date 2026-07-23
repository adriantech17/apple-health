# Exploration: Evaluate Prudent Health-Pattern Guidance

## Change Frame

- **Mode:** independent product decision exploration
- **Artifact store:** OpenSpec and Engram
- **Product scope:** one person, one private local installation
- **Implementation:** explicitly excluded
- **Deferred scope:** multi-user access, sharing, clinical workflow integration,
  diagnosis, treatment, and automated triage

## Decision To Make

Decide whether the private dashboard may evolve from educational trend display to
carefully bounded guidance about persistent patterns and correlations. Any
permitted capability would describe observations in the person's imported data,
state possible meanings only as hypotheses, and make the underlying evidence,
quality, uncertainty, and limitations visible.

The product MUST NOT diagnose, assert pathology, present a correlation as a
cause, claim clinical certainty, or replace professional judgement. It remains a
private, single-person educational dashboard; multi-user capability is
explicitly deferred.

## Verified Repository Context And Tensions

The repository already requires privacy first, traceability and reversibility,
simple operation for one maintainer, and educational, explainable patterns with
limitations. It also says the product must not be presented as a diagnostic
tool. The architecture documentation further requires every derived pattern to
identify its metrics, period, rule, and limitations.

Those rules support descriptive education, but they are in tension with product
copy that could influence a health decision. A persistent-pattern statement can
be mistaken for a clinical conclusion even if its statistical calculation is
correct. A correlation can be misread as causation. A suggestion to consult a
professional can be interpreted as urgency or triage unless its trigger,
evidence, and limits are carefully governed.

Conservative options, from least to most expanded scope, are:

1. Retain descriptive education only: trends, personal-reference comparisons,
   quality states, and plain-language calculation limits. Do not suggest action
   or mention warning signs.
2. Add a neutral, always-available statement that a person may discuss questions
   about their health data with a qualified professional. It must not be tied to
   a measured pattern or imply urgency.
3. Evaluate pattern-linked, non-urgent consultation prompts only in a separate
   future change after the prerequisites below are met. Phase 1 must not draft,
   select, or approve their wording.
4. Consider symptom-conditioned warning-sign information only in a later,
   separately approved change. Each item requires a recognized clinical source,
   editorial review, source/version traceability, explicit symptom and evidence
   conditions, and a safe no-signal state. No warning-sign content is authorized
   by this exploration.

Options 3 and 4 materially increase safety, evidence, and governance burdens.
They are not a copy-only extension of the current educational scope.

## What Can Remain Educational Now

The following can remain within the existing non-diagnostic scope when backed by
the operational metric contract and transparent presentation:

- Describe a measured trend, persistence rule, or statistical association in
  the person's data without asserting causality or health meaning.
- Show the metric definitions, canonical units, period, inclusion and exclusion
  rules, sample count, missingness, freshness, corrections, and known data
  limitations.
- Contrast a current value or period with a disclosed personal reference period,
  while clearly labelling it as an individual comparison rather than a clinical
  range.
- Explain that consumer-exported observations can be incomplete, inaccurate,
  context-poor, or unsuitable for a conclusion.
- Offer general educational language about discussing questions with a qualified
  professional, if it is not triggered by or framed as an assessment of the
  person's health data.

The dashboard MUST suppress derived statements when data quality, provenance,
metric semantics, or minimum observation requirements are not met. Absence of a
displayed statement MUST NOT imply normality, safety, or absence of concern.

## Prerequisites Before Pattern-Linked Guidance

### Evidence And Clinical Governance

- Define the intended use, target user, excluded uses, and foreseeable misuse in
  writing before selecting a pattern or drafting user-facing language.
- Create a controlled source register for every health-meaning claim: source
  publisher, title, stable link or identifier, version/publication date,
  retrieval date, applicable population/context, exact supported claim, and
  review status. Source text must not be copied into the public repository when
  that would create licensing or privacy concerns.
- Require qualified clinical review and documented editorial approval for each
  hypothesis, professional-consultation prompt, and any warning-sign content.
  The necessary reviewer role and approval process remain decisions for a later
  proposal; this exploration does not assume a credential, jurisdiction, or
  legal standard.
- Separate descriptive data facts from interpretive text. The UI must make clear
  which calculation produced an observation and which cautiously worded
  hypothesis is editorial content.
- Establish evidence criteria before implementation: relevance to the intended
  use, source authority, population fit, strength and limitations of evidence,
  recency, conflict handling, and a maximum next-review or withdrawal date. Weak, indirect, or
  conflicting evidence MUST result in no interpretation.
- Use the NICE Evidence Standards Framework for Digital Health Technologies as a
  planning reference for proportionate evidence and evaluation. NICE states that
  meeting its framework does not mean NICE endorsement or regulatory approval.
  It is not, by itself, a determination of Spanish or EU regulatory status.

### Data And Explainability

- Complete and consume the authoritative operational read contract before
  deriving guidance. It must preserve import provenance, correction/current
  selection, timezone semantics, units, completeness, freshness, sparse absence,
  and tombstones.
- Predefine each pattern algorithm, its metric eligibility, minimum sample and
  persistence requirements, missing-data policy, adjustment/context policy,
  correlation method, and suppression criteria. Do not tune thresholds against a
  person's real history.
- Display calculation version, inputs or input summaries, observation window,
  coverage, confidence/uncertainty representation, and limitations in a form a
  person can inspect. "Confidence" must describe the computation or data quality
  precisely; it must not suggest clinical certainty.
- Retain a reproducible audit record of the algorithm version, editorial-content
  version, source-register entry, and input-data version used to create a shown
  statement. The record must stay private and must not introduce external
  telemetry.

### Safety, Editorial, And Operational Controls

- Define a safety case and risk register before user-facing pattern-linked
  guidance. Include false reassurance, unnecessary anxiety, delayed care,
  inappropriate self-management, misunderstood correlation, and repeated alerts.
- Require adversarial review of wording, layout, color, ordering, and defaults
  for implied diagnosis, urgency, causal language, and unequal comprehension.
- Make each statement reversible: version content and rules, support withdrawal,
  and provide a safe fallback to descriptive data only.
- Define an incident and correction process for inaccurate or outdated content,
  including source review, prompt suppression, auditability, and user-visible
  correction where appropriate.
- Prevent health values, interpreted statements, source queries, and audit
  records from being sent to third parties by default. Preserve the existing
  local/private authentication boundary and keep the ingestion credential out of
  the browser.

## Warning-Sign Boundary

No warning-sign feature should proceed in the first guidance phase. If it is
considered later, every statement MUST derive from a specifically identified,
recognized clinical source and undergo clinical/editorial review. It MUST be
conditioned on the source-supported symptoms and the available evidence being
sufficient for that statement; an isolated dashboard metric is not automatically
sufficient. It MUST distinguish unavailable evidence from negative evidence and
must not claim that absence of a prompt means safety.

This exploration deliberately does not name warning signs, thresholds, diseases,
or emergency actions because no clinical sources for such content have been
selected and reviewed.

## Risk Assessment

| Area | Risk | Required guardrail |
|---|---|---|
| Privacy | Interpreted health information, audit records, or analytics leak beyond the private installation. | Local-only processing by default; no telemetry; authenticated data paths; synthetic test evidence only. |
| Harm | False reassurance, anxiety, delayed consultation, or inappropriate self-management follows an overconfident statement. | Conservative scope, suppression, uncertainty, editorial/clinical review, and a descriptive-only fallback. |
| Bias | Evidence, defaults, or language do not fit the person, device, context, or data capture conditions. | Population/context review, explicit limits, accessibility review, and no inference when applicability is uncertain. |
| Regulation | Product claims or functions may change the applicable regulatory analysis. | Seek appropriate jurisdiction-specific assessment before expanding intended use; do not treat NICE ESF as approval or EU/Spanish advice. |
| Security | Sensitive health in browser state, logs, screenshots, backups, or credentials is exposed. | Preserve private deployment and session boundaries; minimize retention; prohibit real-data fixtures and external services by default. |
| UX | Charts, colors, ranking, or alert-like language imply urgency or diagnosis despite disclaimers. | Test comprehension and misuse, use neutral presentation, disclose limits adjacent to the statement, and avoid alert styling. |
| Correctness | Corrections, timezone boundaries, incomplete days, or incompatible units produce a false pattern. | Reuse authoritative contracts, test synthetic edge cases, version algorithms, and suppress on insufficient quality. |

## Evaluation And Validation Gates

Before any implementation proposal for option 3 or 4, the project needs:

1. An approved intended-use and excluded-use statement that retains the
   single-person private scope.
2. A reviewed source register and editorial governance process for every
   interpretive claim in scope.
3. A documented safety case, risk register, stop/withdrawal criteria, and owner
   for review of incidents and content changes.
4. A testable pattern specification with synthetic fixtures covering missing,
   corrected, sparse, incomplete, boundary-time, and incompatible-unit data.
5. Usability and comprehension validation focused on whether people understand
   uncertainty, non-causality, non-diagnostic status, and the no-signal state.
6. A privacy and security review of local storage, browser rendering, logging,
   backups, authentication, and any future support workflow.
7. An appropriate Spain and European Union assessment, commissioned and recorded
   by the governance owner and performed by an advisor who satisfies predefined
   role, qualification, independence, and conflict-of-interest criteria, before
   a future implementation proposal can advance. The private versioned record
   must identify its completion and valid-through dates, exact scope and intended
   use, outcome, limitations, and reassessment triggers. No law, credential, or
   outcome is assumed by this process gate.

Validation should first evaluate wording and interaction with synthetic examples
and reviewer scenarios, then confirm algorithmic reproducibility and suppression
behavior. It MUST NOT use real health exports in tests, documentation, or public
review artifacts.

## Recommendation And Phases

**Recommendation: no-go for pattern-linked professional-consultation prompts or
warning-sign functionality now.** The present repository direction supports
educational, explainable trend display, but the required clinical governance,
source traceability, evidence criteria, safety evaluation, and validation are not
yet defined or evidenced.

**Phase 0 - continue:** deliver descriptive, data-quality-aware education only,
subject to the existing operational data-contract prerequisites.

**Phase 1 - decision preparation:** define intended use, evidence and source
governance, editorial/clinical review roles, safety case, and evaluation plan.
Do not expose interpretation or action prompts.

**Phase 2 - bounded pilot decision:** only if Phase 1 gates pass, propose one
small, reversible category of non-urgent, hypothesis-framed prompt with strict
suppression and validation. Keep warning signs out of scope.

**Phase 3 - separate decision:** evaluate symptom-conditioned warning-sign
content only with identified recognized clinical sources, completed clinical and
   editorial governance, the mandatory Spain and European Union assessment, and
evidence that the UX does not imply diagnosis or automated triage.

Multi-user support remains deferred throughout all phases. It requires a
separate product, authorization, privacy, and operational decision rather than
an extension of this exploration.

## Confirmed Decisions

1. Fund Phase 1 documentary governance without authorizing product behavior.
2. Require written competency, independence, and conflict-of-interest criteria
   for separate clinical and editorial reviewers.
3. Require a Spain and European Union assessment owned by the governance owner
   with a private, versioned, time-bounded process record before a future
   implementation proposal can advance.
4. Require a separate future proposal for any warning-sign content.

## Evidence Consulted

- `AGENTS.md` and `docs/architecture/README.md` in this worktree: private,
  single-user scope; educational, non-diagnostic, explainable pattern limits;
  privacy, traceability, and operational priorities.
- `openspec/config.yaml`: current implementation state and OpenSpec rules.
- NICE, "Evidence standards framework for digital health technologies":
  https://www.nice.org.uk/about/what-we-do/our-programmes/evidence-standards-framework-for-digital-health-technologies
  (retrieved 2026-07-23). NICE describes the ESF as an evidence framework and
  states that meeting it is neither NICE endorsement nor regulatory approval.
