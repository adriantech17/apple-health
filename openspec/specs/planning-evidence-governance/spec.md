# Planning Evidence Governance Specification

## Purpose

Preserve future planning evidence without promoting dashboard behavior.

## Requirements

### Requirement: Non-promotable evidence placement

Planning evidence MUST remain outside every active change `specs/` subtree and archive-merge input.

#### Scenario: Evidence is isolated
- GIVEN reclassified evidence
- WHEN placement is checked
- THEN no file is under an active change `specs/` subtree

#### Scenario: Mergeable evidence is rejected
- GIVEN evidence under a mergeable delta path
- WHEN policy runs
- THEN it MUST fail

### Requirement: Recovery artifact preservation

Only the four source spec files MAY relocate. Recovery narrative artifacts MUST remain byte-unchanged and in place.

#### Scenario: Authorized relocation
- GIVEN the recovery change
- WHEN relocation scope is checked
- THEN only its four source specs MAY have moved

#### Scenario: Narrative drift
- GIVEN a changed recovery exploration, proposal, design, tasks, or verification artifact
- WHEN policy runs
- THEN it MUST fail

### Requirement: Byte-preserving relocation manifest

Each relocation manifest entry MUST record original and destination paths, source commit/blob or SHA-256 identities, and exact byte equality.

#### Scenario: Complete identity and equality
- GIVEN a relocated spec
- WHEN its manifest is checked
- THEN paths and identities MUST resolve to byte-identical content

#### Scenario: Missing or altered evidence
- GIVEN a missing, malformed, unresolved, or byte-unequal entry
- WHEN policy runs
- THEN it MUST fail closed

### Requirement: Exact traceability accounting

Traceability MUST declare totals equal to parsed content: exactly 22 requirement rows and 64 scenarios.

#### Scenario: Exact accounting
- GIVEN complete traceability
- WHEN content is parsed
- THEN declared and parsed totals MUST equal 22 rows and 64 scenarios

#### Scenario: Count drift
- GIVEN any declared or parsed count drift
- WHEN policy runs
- THEN it MUST fail

### Requirement: Anchored future ownership

Every requirement row and scenario group MUST have one source anchor and exactly one future implementation owner. Ownership MUST remain documentary and MUST NOT create an implementation skeleton or runtime claim.

#### Scenario: Complete assignment
- GIVEN all rows and scenarios
- WHEN traceability is checked
- THEN each group MUST resolve to one anchor and one owner

#### Scenario: Invalid assignment
- GIVEN a missing or duplicate anchor, or invalid owner count
- WHEN policy runs
- THEN it MUST fail

### Requirement: Fail-closed repository policy

Policy MUST reject malformed manifests, count drift, invalid anchors, mergeable-path evidence, and unmet archive preconditions.

#### Scenario: Valid governance set
- GIVEN all governance checks pass
- WHEN policy runs
- THEN it MUST succeed

#### Scenario: Unknown or incomplete state
- GIVEN any required input cannot be parsed or verified
- WHEN policy runs
- THEN it MUST fail rather than assume compliance

### Requirement: Strict archive precondition

Neither reclassification nor recovery MUST archive until policy and Strict TDD verification permit the applicable step.

#### Scenario: Applicable archive is permitted
- GIVEN relocation and applicable checks pass
- WHEN archive eligibility is evaluated
- THEN that step MAY proceed

#### Scenario: Premature archive
- GIVEN an unmet check or recovery mergeable evidence
- WHEN archive eligibility is evaluated
- THEN archive MUST be blocked

### Requirement: Deterministic restoration

Manifests MUST deterministically restore every relocated file to its original path and bytes.

#### Scenario: Exact rollback
- GIVEN valid manifests and destination evidence
- WHEN restoration is evaluated
- THEN all four original paths and byte sequences MUST be recoverable

#### Scenario: Ambiguous restoration
- GIVEN an absent or conflicting path, identity, or equality proof
- WHEN restoration is evaluated
- THEN rollback readiness MUST fail
