# ADR 0006: gate private dashboard publication on a verified release boundary

- Status: Accepted
- Date: 2026-07-23

## Context

The dashboard/BFF described as deployed context in ADR 0001 was explored in the
unmerged PR #3 prototype and is not present in `main`. ADR 0003 accepts Compose
as the single-host target but does not establish that a Compose stack is deployed.
Those target directions remain useful, but publication needs a
security and evidence boundary that does not inherit the prototype's BFF,
shared-token, routing, or release assumptions.

The private dashboard will expose sensitive health information to a browser on a
local network. A trusted LAN does not by itself provide transport integrity,
reliable client identity, or proof that the tested ARM64 artifact is the one
published.

## Decision

Dashboard publication MUST remain blocked until a release satisfies all of these
conditions:

- one modular FastAPI application serves authenticated reads and same-origin
  static assets; no separate dashboard BFF or browser ingestion token exists;
- private browser traffic outside loopback uses TLS;
- client identity and scheme derive from the socket peer unless the immediate
  proxy is explicitly trusted; forwarded headers from other peers are ignored;
- host firewall, bind addresses, and proxy allowlists limit reachability to the
  intended private network, with negative reachability tests;
- the immutable release identity binds the application and proxy images; effective
  application, proxy, Compose, trusted-proxy, origin, session-security, bind, and
  firewall configuration; and certificate/trust state;
- a private Raspberry Pi 5 smoke test uses synthetic data and the exact ARM64
  release identity; remote CI and emulation are necessary evidence but cannot
  replace this gate;
- backup, rollback, least-privilege, resource-limit, accessibility, and browser
  privacy gates defined by the active dashboard SDD are satisfied.

This decision supersedes only the implications that a dashboard/BFF or Compose
release is currently deployed and that private browser data may be published over
plaintext LAN transport. It preserves the modular-monolith and single-host
Compose directions of ADR 0001 and ADR 0003.

## Consequences

### Positive

- publication evidence is bound to the complete deployed stack;
- proxy spoofing and accidental broad LAN exposure fail closed;
- the historical prototype remains available for reference without becoming a
  delivery baseline;
- rollback can identify exactly which application and proxy configuration was
  tested.

### Costs and limits

- native verification requires access to the private Raspberry Pi;
- certificate and proxy operation add maintenance work;
- no dashboard can be declared published from CI evidence alone.

## Review Criteria

Review this decision if browser access remains loopback-only, the deployment no
longer uses a reverse proxy, or equivalent measured controls provide the same
transport, identity, reachability, and immutable-release guarantees.
