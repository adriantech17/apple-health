# Tasks: Evaluate Prudent Health-Pattern Guidance

## Delivery Contract

- Documentation-only Phase 1 governance; no product implementation or clinical content.
- Single cohesive PR under the 2,500-line session budget.
- Maintainer-approved `size:exception` above the default 400-line guard.
- Synthetic, sanitized evidence only; no health data, identities, credentials, private paths, source excerpts, or operational records.

Decision needed before apply: No
Chained PRs recommended: Yes
400-line budget risk: High
Chain strategy: size:exception

## Scope

- `exploration.md`
- `proposal.md`
- `design.md`
- `specs/health-pattern-guidance-governance/spec.md`
- `tasks.md`
- `verify-report.md`
- `tests/test_health_guidance_governance.py`
- `docs/architecture/decisions/0005-govern-future-health-pattern-guidance.md`
- `docs/architecture/README.md`

The maintainer approved Phase 1, ADR 0005, the private-environment prerequisites,
written reviewer competency and independence criteria, a mandatory Spain and
European Union assessment process owned by the governance owner, and a separate
future decision for warning signs. Approval of these prerequisites does not mean
that the environment, backups, restoration, or assessment exists or is operational.

## Suggested Work Unit

| Scope | Focused command | Runtime harness | Rollback boundary |
|---|---|---|---|
| Governance contract | `.venv/bin/python -m pytest tests/test_health_guidance_governance.py` | `.venv/bin/python -m pytest` | Revert test and documentary change together |
| ADR and privacy boundary | `python3 scripts/check_repository.py` | `python3 -m unittest scripts.test_check_repository` | Withdraw ADR and retain backend-only state |

Each unit followed RED (missing policy assertion), GREEN (focused policy test),
and REFACTOR (remove duplication while preserving the passing assertion).

## Tasks

### 1. Establish the governance boundary

- [x] Record intended use, exclusions, foreseeable misuse, ownership, and review points.
- [x] Keep diagnosis, triage, urgency, treatment, claims, warning signs, algorithms, thresholds, UI, API, storage, authentication, deployment, and multi-user access outside Phase 1.
- [x] Record the durable boundary in ADR 0005 and index it.

### 2. Define fail-closed governance

- [x] Require traceable current sources and independent clinical and editorial review.
- [x] Define expiry, conflict, incident, suppression, re-approval, and descriptive-only fallback.
- [x] Require authoritative eligibility with bounded freshness for any future rendering; unavailable or stale eligibility suppresses interpretive material.
- [x] Define maximum next-review dates, reassessment triggers, and immediate fail-closed expiry for every controlled record.
- [x] Define the private, versioned Spain and European Union assessment deliverable and its process-level completeness, validity, scope, advisor-criteria, outcome, limitation, and reassessment gates.
- [ ] Commission and complete a current Spain and European Union assessment before any future implementation proposal advances.

### 3. Preserve the privacy boundary and record prerequisites

- [x] Specify that controlled records require an access-restricted encrypted private environment, encrypted backups, and evidenced restoration before use.
- [ ] Provision and verify the private environment, encrypted backups, and a successful restoration test outside this repository.
- [ ] Define and verify the private category structure, retention, deletion, and credential handling before controlled records receive content.
- [x] Specify that reviewers receive only minimal versioned packages through a private controlled channel and no direct workspace access.
- [x] Keep only non-sensitive identifiers, statuses, hashes, and sanitized evidence in Git.

### 4. Verify the documentary delivery

- [x] Map every requirement and scenario to documentary evidence in `verify-report.md`.
- [x] Run `.venv/bin/python -m pytest`, repository audit, policy unittests, and tracked/untracked whitespace checks.
- [x] Confirm the complete candidate stays below 2,500 lines and contains only the scoped governance files.
- [x] Confirm no governance artifact authorizes product behavior or clinical content.

## Completion Gate

- [x] All documentary governance tasks and maintainer decisions are complete.
- [ ] External operational prerequisites are evidenced and current; until then, future functionality remains blocked.
- [x] Documentary verification passes with the approved `size:exception`; this is not operational readiness or authorization to archive as implemented behavior.
