# ADR 0005: govern future health-pattern guidance through fail-closed review

- Status: Accepted
- Date: 2026-07-23

## Context

Apple Health remains a private dashboard for one person. Its current product
scope is descriptive education and does not extend to interpretive functionality.
Any future expansion can affect how people understand health-related information
and therefore requires durable governance before product work is considered.

## Decision

The project adopts the following policy for any future health-pattern guidance:

- The current private, single-person, descriptive educational scope remains in
  force.
- A future interpretive capability requires a separate approved proposal. This
  policy does not authorize functionality, dashboard changes, or claims.
- All required governance preconditions must be current and complete before a
  future proposal may advance. When status is missing, stale, conflicting, or
  uncertain, progression is denied.
- A later released capability MUST suppress its associated interpretive material
  and revert to descriptive data only when a required precondition becomes
  missing, stale, conflicting, withdrawn, or uncertain, or when a relevant
  incident requires containment. It may return only after current records and
  independent reviews re-establish eligibility.
- Clinical and editorial review are separate required controls. Each role is
  governed by written competency, independence, and conflict-of-interest
  criteria.
- Any future interpretive functionality requires an appropriate assessment for
  Spain and the European Union before it advances. This requirement does not
  assert any approval or outcome.
- Governance records remain private and separate from versioned artifacts.
  Versioned material may contain only non-sensitive identifiers, statuses, and
  hashes. Credentials remain separate from those records.
- Warning-sign content is outside this policy's authorized delivery and requires
  a separate future proposal.

## Consequences

### Positive

- Future proposals begin from an explicit, conservative boundary.
- Independent review and fail-closed progression reduce accidental expansion of
  the product scope.
- Versioned documentation does not become a repository for sensitive governance
  records.

### Costs and limits

- A future capability cannot proceed solely because Phase 1 governance exists.
- Required preconditions introduce review work before any future proposal.
- This decision establishes policy only; it does not establish content,
  implementation, or an external assessment outcome.

## Review Criteria

Review this decision only when the confirmed product scope, applicable
jurisdiction, or governance boundary changes. Any revision requires a new ADR
and a separately approved change for product impact.
