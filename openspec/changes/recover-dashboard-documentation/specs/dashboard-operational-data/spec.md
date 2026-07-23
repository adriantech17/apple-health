# Dashboard Operational Data Specification

## Purpose

Define the SQLite readiness dependency and truthful data contract for the first
private dashboard without duplicating operational storage semantics.

## Requirements

### Requirement: Gate Dashboard Reads On Operational SQLite Readiness

Dashboard implementation MUST NOT begin until phases 4-10 of
`migrate-daily-summaries-to-operational-sqlite` have completed the metric
registry, version/current selection, ingestion, and indexed operational reads.
Routine use against migrated history MUST NOT begin until phases 11-17 have
completed reconciliation, verified cutover, recovery, and readiness.

Those migration phases establish operational prerequisites; they MUST NOT be
claimed to deliver a dashboard endpoint or dashboard-specific freshness,
provenance, correction-notice, completeness, gap, or response fields. A separate
approved dashboard read-contract product change MUST define and implement those
fields after the prerequisites exist. Dashboard reads MUST use only that
contract backed by operational SQLite.
They MUST NOT open raw evidence, legacy Parquet, DuckDB, pending batches, or
replay evidence, and MUST NOT recreate storage schemas, current selection,
correction ordering, provenance, completeness, unit conversion, or timezone
rules. A missing, stale, mismatched, or not-ready operational state MUST fail
closed without falling back to a legacy source.

#### Scenario: Registry and current reads are incomplete

- GIVEN any required phase from 4 through 10 is incomplete
- WHEN dashboard implementation readiness is evaluated
- THEN implementation remains blocked and no temporary legacy read path is authorized.

#### Scenario: Migrated history is not ready for routine use

- GIVEN operational reads exist but reconciliation, cutover, or readiness is incomplete
- WHEN private publication is evaluated
- THEN publication against migrated history remains blocked.

#### Scenario: SQLite reports a mismatched state

- GIVEN the application artifact expects a different operational contract or timezone
- WHEN a dashboard read is requested
- THEN the request fails closed without reading another store.

#### Scenario: Storage migration completes without a dashboard contract

- GIVEN phases 4 through 10 are complete but no dashboard read-contract product change is implemented
- WHEN dashboard implementation readiness is evaluated
- THEN dashboard reads remain blocked and no response fields are inferred from migration phase names.

### Requirement: Consume A Consistent Current Snapshot

Every status, overview metric, detail, freshness indicator, and coverage value
displayed together MUST represent one named, internally consistent SQLite read
snapshot for the fixed owner and requested Madrid local-date range. Values,
details, units, completeness, current-version identity, provenance, correction
status, coverage, freshness, and known integrity state MUST refer to that same
snapshot. The dashboard MUST NOT combine fields from different versions or
requests or independent snapshot identities as one overview.

#### Scenario: Overview requests complete at different times

- GIVEN independently executed reads do not share one authoritative snapshot identity
- WHEN the overview would combine their results
- THEN the overview rejects the mixed state instead of presenting it as coherent.

The operational contract MUST remain authoritative for the fixed owner,
`Europe/Madrid` day identity, selected current value or tombstone, canonical
unit, source lineage, correction status, and import origin. Browser locale MAY
format a value or date for display but MUST NOT change its day identity, unit
semantics, selection, or completeness.

When a current value supersedes an earlier accepted version for the same owner,
metric, and Madrid local date, the presentation MUST identify it as a correction.
Its “correction date” MUST be the authoritative server timestamp at which that
selected correcting version was accepted. It MUST NOT use the metric local date,
source sample time, import filename timestamp, browser receipt time, filesystem
time, or display locale as the correction date. The value, correction acceptance
timestamp, and bounded import-origin label MUST come from the selected version
in the same snapshot. Raw payloads, private paths, hashes, manifests, and complete
version history MUST remain hidden by default.

#### Scenario: A corrected value is selected

- GIVEN SQLite selects a correction as current and supplies its date and import origin
- WHEN the metric is presented
- THEN the current value, canonical unit, correction notice, date, and origin come from the same snapshot.

#### Scenario: The browser uses another timezone

- GIVEN a daily value belongs to a Madrid local date
- WHEN a browser in another timezone renders it
- THEN its operational local-date identity remains unchanged.

#### Scenario: A selected version is an absence tombstone

- GIVEN the current projection selects an authoritative absence
- WHEN the dashboard reads that identity
- THEN it presents no numeric value and does not resurrect an older version or display zero.

### Requirement: Derive The Launch Catalog From The Completed Registry

The completed operational registry MUST be the only authority for launch metric
membership. At the release gate, its admitted entries are expected to total 25;
the presentation catalog MUST contain exactly one entry for each admitted entry
and no others. The following identifiers are a review expectation, not a second
registry or permission to present an incomplete contract:

```text
step_count
active_energy
walking_running_distance
apple_exercise_time
apple_stand_hour
apple_stand_time
flights_climbed
resting_heart_rate
heart_rate_variability
vo2_max
cardio_recovery
walking_heart_rate_average
heart_rate
respiratory_rate
blood_oxygen_saturation
sleep_analysis
walking_speed
walking_step_length
walking_asymmetry_percentage
walking_double_support_percentage
stair_speed_up
stair_speed_down
time_in_daylight
physical_effort
basal_energy_burned
```

The presentation catalog MAY define labels, grouping, descriptive education,
display precision, accessibility text, provenance labels, and limitations. It
MUST NOT redefine accepted source units, canonical units, metric shape,
completeness, sparse semantics, or current selection. An identifier not admitted
by the completed operational registry MUST NOT be presented as available.

The default overview and metric-detail range MUST prioritize the latest 12
months. That default MUST be a reversible query and presentation choice: older
retained history and raw evidence MUST NOT be deleted, pruned, or declared
unavailable because it falls outside the default range.

#### Scenario: The completed registry admits all launch metrics

- GIVEN all 25 listed identifiers have completed operational contracts
- WHEN the presentation catalog is validated
- THEN every identifier has one presentation entry and no extra metric is implied to be supported.

#### Scenario: The registry count or membership differs

- GIVEN the completed registry does not admit exactly the expected 25 identifiers
- WHEN release catalog validation runs
- THEN release is blocked rather than filling from or overriding the documentary list.

#### Scenario: The default view opens

- GIVEN more than 12 months of retained history exists
- WHEN the dashboard opens its default range
- THEN it prioritizes the latest 12 months without deleting or rewriting older history.

### Requirement: Present Coverage And Gaps Without Inventing Data

The dashboard MUST make range, units, coverage, completeness, freshness, gaps,
and known limitations available wherever they affect understanding. It MUST NOT
impute, interpolate, zero-fill, connect a discontinuity, or label an observed or
missing value as normal or abnormal.

Coverage MUST use every eligible Madrid local date in the complete requested
range as its denominator, including missing leading dates before the first
observation and trailing dates after the last observation. It MUST NOT clip the
denominator to observed edges. Sparse observations MUST be positioned by actual
elapsed calendar time, not equally spaced categorical slots.

When the operational contract identifies the cause, the dashboard MUST
distinguish legitimate absence or an inherently sparse metric from an ingestion
or processing error. When the cause is unknown, it MUST state that uncertainty
and MUST NOT infer device use, user behavior, or ingestion failure.

Every data-bearing view MUST have distinct loading, partial, error, and empty
states. A partial state MUST preserve useful verified values while identifying
the unavailable or degraded portion. An error MUST NOT be rendered as an empty
dataset, and an empty dataset MUST NOT be described as evidence of health or
normality. Previously verified values associated with a newer degraded receipt
MAY remain visible only with the integrity limitation supplied by the
operational contract.

#### Scenario: A sparse metric has isolated observations

- GIVEN a sparse metric contains two verified observations in the selected range
- WHEN its trend is rendered
- THEN only those observations appear, the gap remains visible, and no line or value is invented between them.
- AND their horizontal distance represents the actual elapsed calendar time.

#### Scenario: Observations do not cover the requested edges

- GIVEN the requested range starts before the first observation and ends after the last
- WHEN coverage is calculated
- THEN every eligible requested date remains in the denominator and both edge gaps remain visible.

#### Scenario: A known ingestion error affects part of a range

- GIVEN the operational contract identifies a processing error for some dates
- WHEN other verified dates remain useful
- THEN the view is partial, preserves the verified values, and identifies the affected coverage as an error rather than legitimate absence.

#### Scenario: No observations exist for the selected range

- GIVEN the operational snapshot returns no current values and no known error
- WHEN the view renders
- THEN it shows a truthful empty state without zeroes, normality claims, or an invented cause.

#### Scenario: The read fails

- GIVEN the private read cannot produce a valid operational snapshot
- WHEN the request completes
- THEN the view shows an error state and does not reuse stale values as if they were current.

### Requirement: Validate And Commit A Complete Response Atomically

Before rendering any newly received private data, the client MUST validate the
entire response boundary: requested and returned metric identity, snapshot and
current-version coherence, exact `Europe/Madrid` timezone contract, valid local
calendar dates, requested range and ordering, canonical unit, finite numeric
values, explicit gap/completeness semantics, and every required metric-specific
detail. Heart-rate extrema, sleep stages, and other structured shapes MUST be
validated as complete coherent units rather than independent optional fragments.

Any unknown metric/unit/detail shape; missing required field; non-finite number;
duplicate, unordered, impossible, or out-of-range date; range escape; timezone
mismatch; snapshot mismatch; or contradictory gap/detail MUST reject the whole
response. Validation and state replacement MUST be atomic. The client MUST NOT
drop an invalid point, retain a valid subset, substitute a unit, clip a date,
infer a gap/detail, combine with prior state, or otherwise repair a partial
response.

Each metric, range, area, or snapshot selection change MUST abort superseded work
or advance a request generation. A response may commit only when its initiating
selection and generation are still active at commit time, even if its payload and
session remain otherwise valid.

#### Scenario: A valid response arrives for an old range

- GIVEN the person changes range after a valid request starts
- WHEN the earlier response arrives after the active generation changed
- THEN it is discarded without replacing data for the current selection.

#### Scenario: One point contains a non-finite value

- GIVEN every other point is valid but one value is non-finite
- WHEN the response boundary is validated
- THEN no part of that response commits and the prior generation is not presented as refreshed.

#### Scenario: Structured details disagree with the snapshot

- GIVEN a response has valid top-level values but missing or mismatched required details
- WHEN atomic validation runs
- THEN the complete response is rejected without preserving only the top-level values.
