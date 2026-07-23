# Private Dashboard Access Specification

## Purpose

Define a fail-closed, single-person browser session boundary distinct from
machine ingestion authentication.

## Requirements

### Requirement: Separate Browser And Ingestion Credentials

The browser MUST authenticate through a web credential and same-origin session
that are cryptographically and operationally distinct from the ingestion bearer
credential. The ingestion credential MUST remain machine-only and MUST NOT enter
HTML, JavaScript, source maps, cookies, browser storage, request URLs, frontend
build artifacts, or browser-visible logs and errors.

The browser session MUST authorize read access only for the one fixed server-side
owner. The client MUST NOT select or submit a `user_id`, account, role, profile,
or owner scope. This contract MUST NOT be treated as a multiuser identity model.

#### Scenario: A browser authenticates successfully

- GIVEN the single-person web credential is valid
- WHEN the server creates a browser session
- THEN the session is scoped to the fixed owner without revealing or reusing the ingestion credential.

#### Scenario: A client supplies an owner identifier

- GIVEN an otherwise authenticated browser request includes a client-selected owner
- WHEN authorization is evaluated
- THEN the supplied owner grants no scope and cannot change the fixed server-side owner.

### Requirement: Protect Every Health-Data Read

Every route that returns health values, metric status, provenance, corrections,
coverage, or other private operational state MUST require a currently valid web
session. Static assets and the minimum authentication flow MAY be reachable
without a session; they MUST contain no private health state. The minimal public
health check MAY remain public and MUST reveal no data, readiness detail,
credential state, or private topology.

Missing, malformed, expired, revoked, unverifiable, or ambiguously scoped
sessions MUST be denied before private data is read. Authentication dependency
failure MUST deny access rather than preserve an earlier authorization result.

#### Scenario: A private read has no session

- GIVEN a request targets health data without a valid web session
- WHEN it reaches the read boundary
- THEN access is denied before SQLite health data is queried or returned.

#### Scenario: Session validation is unavailable

- GIVEN the server cannot establish that a session is current and authorized
- WHEN a private route is requested
- THEN access fails closed and no cached authorization is assumed.

### Requirement: Bound And Revoke Web Sessions

A web session MUST have a finite server-enforced expiry. Its browser cookie MUST
be same-origin, `HttpOnly`, `SameSite`, and `Secure` whenever used outside
loopback. Browser code MUST NOT be able to read the session secret. Expiry MUST
be evaluated by trusted server time and MUST deny subsequent private reads.

Logout MUST revoke the current session server-side and expire its cookie. A
revoked session MUST remain invalid if the old cookie is replayed. A server
restart, secret rotation, lost revocation state, malformed state, or incompatible
session version MUST fail closed; it MUST NOT silently turn an unverifiable
session into an authenticated one.

The session cookie MUST use `SameSite=Strict` on issuance and matching deletion,
in addition to `HttpOnly`, path, and transport attributes. Every unsafe
cookie-authenticated action MUST validate an allowlisted same-origin `Origin`;
login and logout MUST apply the same rule even where login has no valid session.
Missing, opaque, malformed, cross-origin, or untrusted-forwarded origins MUST be
rejected before authentication work or mutation. `SameSite` MUST be treated as
defense in depth and MUST NOT replace the origin check. Authentication failures
MUST not disclose which secret check failed or include credentials in logs.

#### Scenario: A session expires

- GIVEN a valid session reaches its server-enforced expiry
- WHEN it is used for a private read
- THEN access is denied and the client must authenticate again.

#### Scenario: The person logs out

- GIVEN a valid current session
- WHEN logout completes
- THEN the server revokes it, expires the cookie, and rejects replay of the prior cookie.

#### Scenario: Session state cannot be recovered after restart

- GIVEN a cookie survives but its server-side validity cannot be established
- WHEN it is presented after restart
- THEN the request is unauthenticated rather than reconstructed from browser state.

#### Scenario: SameSite cannot establish origin

- GIVEN an unsafe authentication request has a cookie but no valid same-origin `Origin`
- WHEN the request is evaluated
- THEN it is rejected before state changes, regardless of `SameSite=Strict` behavior.

### Requirement: Bound Login Admission Before Expensive Work

The login contract MUST define finite byte limits for declared body length,
actual streamed body bytes, and password encoding. It MUST reject a declared
oversize before reading the body and stop reading once actual bytes exceed the
limit, including absent or misleading length declarations. Only the accepted
media type, valid JSON, and an exact top-level login object with one string
password field MUST reach password verification. Arrays, scalars, duplicate or
unknown fields, invalid encoding, and passwords outside the configured byte
range MUST be rejected first.

Password verification MUST run through a separately bounded concurrency gate.
Stored credentials MUST use a one-way password verifier designed for password
hashing, and verification MUST avoid secret-dependent early-exit comparison.
Rate-limit state and live session state MUST each have finite capacity and
defined expiry. If any gate, clock, limiter, or session store cannot establish
admission, the attempt MUST fail closed. Capacity pressure MUST reject new login
or session creation; it MUST NOT evict, overwrite, or invalidate an otherwise
valid unexpired session.

Successful authentication MUST issue a new session identifier generated from a
cryptographically secure random source with enough entropy to resist guessing.
The identifier MUST rotate on authentication and any future privilege transition;
an attacker-supplied or pre-authentication identifier MUST NOT be retained.

Rate-limit admission and attempt recording for one authoritative client identity
MUST be atomic across concurrent requests. No two requests may both observe the
same remaining allowance and proceed without recording both attempts. Failure to
serialize or persist that decision MUST reject the attempt before password work.

#### Scenario: Concurrent requests consume the last allowance

- GIVEN one authoritative client has one admitted attempt remaining
- WHEN two login requests arrive concurrently
- THEN at most one reaches password verification and both attempts are accounted
  for by one atomic limiter transition.

#### Scenario: Stream exceeds its declaration or limit

- GIVEN a login body is chunked, has no useful declared length, or sends more bytes than declared
- WHEN actual bytes cross the configured maximum
- THEN reading stops, password verification does not run, and no session is created.

#### Scenario: Expensive work is saturated

- GIVEN the password-verification concurrency bound is occupied
- WHEN another otherwise well-formed login arrives
- THEN it is rejected or deferred within the bounded policy without starting unbounded work.

#### Scenario: Session capacity is full

- GIVEN all session capacity is held by valid unexpired sessions
- WHEN a valid credential requests another session
- THEN creation fails closed and no existing valid session is evicted.

#### Scenario: A login request supplies a session identifier

- GIVEN valid credentials arrive with an attacker-known or pre-authentication identifier
- WHEN authentication succeeds
- THEN the server ignores that identifier and issues a fresh unpredictable session.

### Requirement: Trust Only An Explicit Immediate Proxy

The application MUST derive its initial peer identity from the accepted socket.
Forwarded client address, host, scheme, and origin headers MUST influence trust or
transport decisions only when that immediate peer is in an explicit trusted
proxy allowlist. Such headers from any other peer MUST be ignored or rejected;
trust MUST NOT be inferred from a forwarded private address, hostname, or header
presence.

Loopback MAY use HTTP for local maintenance. Outside loopback, login, session
issuance, and every private response MUST be rejected unless the direct
connection is HTTPS or an explicitly trusted immediate proxy attests HTTPS.
Forwarded HTTP, ambiguous chains, an unavailable peer identity, and private
address syntax without trusted-proxy proof MUST fail closed.

#### Scenario: An untrusted peer forges forwarded HTTPS

- GIVEN a non-loopback socket peer is not in the trusted-proxy allowlist
- WHEN it sends forwarded headers claiming HTTPS and a loopback client
- THEN authentication and private data remain unavailable.

#### Scenario: The trusted proxy reports HTTP

- GIVEN the immediate peer is allowlisted but its accepted forwarded scheme is HTTP
- WHEN a private route is requested
- THEN the request is rejected rather than issuing or accepting a private session.

### Requirement: Lock Browser State Across Authorization Lifecycles

On `pagehide`, the client MUST synchronously lock the private UI, clear private
render/model state, invalidate the active request generation, and prevent later
commits before the page can enter BFCache. On every `pageshow`, including a
persisted BFCache restore, it MUST revalidate the server session before unlocking
or requesting private data.

A `401`, logout, or client-observed expiry MUST execute one atomic transition:
lock, clear all private state, abort every in-flight private request, and advance
the generation. Each response MUST prove that its generation is still current
and authorization remains valid immediately before commit. A late response from
an old generation MUST be discarded and MUST NOT repopulate data or replace the
locked state with an error.

#### Scenario: BFCache restores a private page

- GIVEN a private page was hidden and retained in BFCache
- WHEN `pageshow` restores it
- THEN no prior private state is visible and session revalidation precedes all private reads.

#### Scenario: A read succeeds after logout

- GIVEN logout advanced the generation and aborted an in-flight read
- WHEN that read still resolves successfully
- THEN its result is discarded and the private UI remains locked.
