# Accessible Descriptive Dashboard Specification

## Purpose

Define an accessible, privacy-preserving browser experience that remains
descriptive and educational under ADR 0005.

## Requirements

### Requirement: Provide Accessible Responsive Access To Essential Information

The overview, metric navigation, metric detail, authentication, logout, range
selection, correction notice, coverage, limitations, and request states MUST be
operable by keyboard and usable at mobile and desktop viewport sizes. Focus MUST
remain visible and follow a logical order. Controls MUST have programmatic names,
current selection and status MUST not rely on color alone, and status changes
MUST be exposed to assistive technology without unexpected focus movement.

Every chart containing information essential to understanding a metric MUST have
an accessible textual equivalent that communicates the displayed period, unit,
coverage, current or summary values as applicable, gaps, corrections, and
limitations. Decorative visual detail MAY be omitted from that equivalent;
essential extrema or structured details such as heart-rate minimum/maximum and
sleep stages MUST NOT be discarded.

Acceptance MUST include a 320 CSS-pixel viewport without loss of information or
essential horizontal page scrolling, pointer targets of at least 44 by 44 CSS
pixels, and browser text-only zoom to 200 percent without clipped, overlapping,
or unreachable content. Text, controls, visible focus, and non-text status cues
MUST meet the applicable WCAG contrast criterion. Tests MUST use computed colors
and interaction geometry rather than visual assertion alone.

Modal navigation or metric drawers MUST move focus inside, trap focus, make the
background inert to pointer and assistive-technology interaction, close on
Escape, and restore focus to the control that opened them. Motion that is not
essential MUST be removed when reduced motion is requested. Chart information
MUST also be available as a chronological accessible table. Opening a row's
detail and returning MUST restore focus to that row or its invoking control.

#### Scenario: A chart cannot be perceived

- GIVEN a metric trend is visually rendered
- WHEN a person uses non-visual navigation
- THEN an equivalent identifies its period, unit, coverage, meaningful values, gaps, and limitations.

#### Scenario: A partial state is announced

- GIVEN verified values render while part of the requested range is unavailable
- WHEN the state changes from loading to partial
- THEN the limitation is programmatically exposed without relying only on color.

#### Scenario: The dashboard is used at the quantified mobile boundary

- GIVEN a 320 CSS-pixel viewport with text zoomed to 200 percent
- WHEN authentication, navigation, range selection, and metric detail are used
- THEN content remains operable and understandable without clipping or essential horizontal page scrolling.

#### Scenario: A modal drawer closes

- GIVEN focus entered an open drawer while the background was inert
- WHEN Escape closes it
- THEN focus returns to the invoking control and no hidden drawer control remains reachable.

#### Scenario: A chart detail is explored without a pointer

- GIVEN the chronological accessible table represents the chart
- WHEN a keyboard user opens and closes one row's detail
- THEN all essential details are available and focus returns to that row or its invoking control.

### Requirement: Keep Browser Processing Private

Health values, provenance, corrections, coverage, and session material MUST NOT
be sent to analytics, telemetry, error-reporting, advertising, CDN processing,
or any external service by default. Private data responses MUST prohibit shared
or persistent browser caching. Health data and credentials MUST NOT be persisted
in `localStorage`, `sessionStorage`, IndexedDB, service-worker caches, URLs, or
client logs.

The application MUST request private data only from its same origin. Browser
errors MUST be sanitized and MUST NOT expose health values, credentials, raw
payloads, private paths, hashes, manifests, or internal provenance identifiers.
Static assets MAY be cacheable only when they contain no private state.

Repository, CI, review, screenshots, and release evidence MUST use minimal
synthetic data. Real health values or identifiable browser captures MUST NOT be
used as fixtures or public evidence, including superficially anonymized exports.

#### Scenario: A browser reloads after viewing health data

- GIVEN private values were displayed in an authenticated session
- WHEN the page reloads after authorization is lost
- THEN no browser-persisted health dataset is restored and private reads require a valid session.

#### Scenario: A release screenshot is needed

- GIVEN reviewers need visual evidence
- WHEN the screenshot is produced
- THEN it uses synthetic values and contains no real identifier, secret, path, hash, or health history.

### Requirement: Remain Descriptive And Educational

The dashboard MAY describe what a metric represents, its displayed period,
source, unit, collection method, coverage, provenance class, and known
limitations. It MUST present those explanations as educational context, not as
clinical interpretation.

The dashboard MUST NOT define or present diagnosis, clinical advice,
individualized health guidance, warning signs, risk classification, causal
claims, treatment suggestions, or normal/abnormal judgments. Comparisons MUST
remain descriptive and MUST NOT imply that a personal value is healthy, safe,
expected, or pathological.

Any future interpretive material remains governed by ADR 0005 and requires a
separate approved proposal and current governance evidence. Missing, stale,
conflicting, withdrawn, or uncertain eligibility MUST fail closed to descriptive
data only. This specification MUST NOT be used as authorization for that future
capability.

#### Scenario: A metric lacks interpretive authorization

- GIVEN the dashboard has a value and descriptive limitation but no separately approved interpretive capability
- WHEN explanatory content is rendered
- THEN it remains factual and educational without diagnosis, guidance, warning signs, or normality claims.

#### Scenario: Future governance becomes uncertain

- GIVEN a later interpretive capability loses a required current precondition
- WHEN the dashboard determines eligible content
- THEN associated interpretation is suppressed and only descriptive data remains.
