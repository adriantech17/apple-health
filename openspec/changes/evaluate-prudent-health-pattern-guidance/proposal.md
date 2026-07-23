# Proposal: Evaluate Prudent Health-Pattern Guidance

## Problem

The dashboard's educational trend presentation could be mistaken for clinical
interpretation if it later describes persistent patterns or correlations. The
project has not yet defined the evidence, clinical/editorial governance, safety
controls, or withdrawal process required before any pattern-linked guidance can
be considered safely.

## Objective

Deliver Phase 1 decision-preparation artifacts that define governance gates for
any future health-pattern guidance while preserving the private, single-person,
local-installation scope. This change delivers no user-facing capability.

## Maintainer Confirmations

- Phase 1 documentary governance preparation is funded. This confirmation does
  not authorize functionality, claims, or dashboard changes.
- Controlled governance records remain private, separate from versioned
  artifacts, with maintainer-only access. The required private environment is a
  confirmed prerequisite, not an existing or verified capability. Before those
  records receive content, its access restriction, encryption, category-based
  structure, retention, deletion, encrypted backup, and restoration test must be
  implemented, documented, and evidenced outside this repository.
- Clinical and editorial review roles require written competency, independence,
  and conflict-of-interest criteria. Reviewer identities and credentials remain
  private.
- Any future interpretive functionality requires an appropriate assessment for
  Spain and the European Union before its separate implementation proposal can
  advance. This is a gate, not a statement of approval.
- Warning-sign content requires a separate future proposal.
- The governance boundary is durable project policy and requires an ADR.

## Scope

- Define the intended-use, excluded-use, and foreseeable-misuse boundaries for
  a possible future guidance capability.
- Define a controlled, traceable source-register requirement for every future
  health-meaning claim, including source currency, applicability, approval
  status, effective date, and maximum next-review or withdrawal date.
- Define recorded clinical and editorial review gates for every future claim.
- Define evidence conflict, expiry, and withdrawal handling: content MUST be
  suppressed by default when its source is withdrawn, expired, or conflicting
  until it is approved again.
- Define the required safety case, risk register, incident/correction process,
  and safe fallback to descriptive data only.
- Evaluate governance requirements for possible future warning-sign content
  without selecting signals, drafting content, or enabling any feature.

## Non-Objectives

- Diagnosis, triage, urgency guidance, treatment, or clinical claims.
- Selection, wording, display, or activation of warning-sign content.
- Pattern-linked prompts, recommendations, algorithms, thresholds, or data
  interpretation.
- UI, dashboard, API, storage, authentication, data-processing, or deployment
  changes.
- Multi-user access, sharing, third-party calls, telemetry, or external health
  data transfer.

## Dependencies

- Any future dashboard deployment must be private and authenticated, and must
  keep ingestion credentials unavailable to the browser.
- Any future pattern work depends on the authoritative operational read
  contract and reproducible handling of provenance, corrections, units,
  timezone, completeness, freshness, and sparse absence.
- Any future claim requires a current, traceable source and recorded clinical
  and editorial approval. This proposal does not select clinical, regulatory,
  legal, or other external sources.
- The governance owner is accountable for commissioning and recording the Spain
  and European Union assessment performed by an advisor who satisfies written
  role, qualification, independence, and conflict-of-interest criteria. The
  private, versioned assessment record must state its completion and valid-through
  dates, exact scope and intended use, outcome, limitations, and reassessment
  triggers. This process requirement assumes no law, credential, or outcome.

## Risks And Controls

- Health-related wording can cause false reassurance, anxiety, delayed care, or
  inappropriate self-management. Future content remains blocked behind the
  defined safety and review gates.
- Stale or conflicting evidence can make previously approved content unsafe.
  Default suppression and explicit reapproval prevent continued display.
- Governance artifacts could be misread as authorization to implement. This
  proposal creates gates only; a separate approved change is required for any
  functionality or claim.
- Governance records may contain sensitive context. They MUST remain private,
  local by default, and free of real health exports in repository artifacts.

## Privacy, Data, And Authentication Impact

Phase 1 introduces no product data collection, processing, persistence, or
external transmission, and does not alter authentication. Any future proposal
must preserve local-only processing by default, authenticated data routes, and
the existing separation between browser sessions and ingestion credentials.

## Success Criteria

- The Phase 1 framework states intended and excluded uses, governance owners,
  approval records, maximum next-review dates, event-driven review triggers,
  source currency rules, conflict handling, and stop/withdrawal criteria.
- It requires a current traceable source plus recorded clinical and editorial
  review before any future health-meaning claim is shown.
- It defines a descriptive-only fallback and incident/correction process.
- It evaluates warning-sign governance requirements without identifying,
  drafting, or enabling warning-sign content.
- No clinical claim, functional behavior, UI change, or third-party integration
  is introduced.

## Rollback

Phase 1 is governance preparation only. Its rollback leaves the current backend
unchanged and records a new decision that supersedes this policy; ADR 0005 and
the archived change remain as historical evidence. If a later approved capability
is withdrawn, it MUST suppress all associated content and revert its future
dashboard to descriptive data only.

## Future Decisions Required

A new decision is required before implementing any pattern-linked prompt,
interpretation, algorithm, threshold, source selection, clinical or editorial
claim, UI change, warning-sign content, jurisdiction-specific assessment,
multi-user capability, third-party call, or change to data, authentication, or
storage behavior.

## External Blockers

Phase 1 documentation is complete only as a governance boundary. Controlled
records cannot be used until the maintainer provisions and evidences the private
environment's access restriction, encryption, category-based structure,
retention, deletion, encrypted backup, and successful restoration test. These
controls are not verified or operational through this change. Any future
interpretive functionality remains blocked pending its separate approved
proposal and a current, complete Spain/European Union assessment record.

## Delivery

This independent change follows the single-PR default strategy. The requested
review budget is 2,500 lines; this proposal is intentionally far below that
limit and contains no implementation work.
