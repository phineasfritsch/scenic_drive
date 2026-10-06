---
id: T-0272
title: the Worker's quota tier comes from the entitlement - an active /asn entitlement for the request's appAccountToken makes the caller paid (plan 200/day, full /trip itinerary), everything else stays anon; REFUND_REVERSED restores access
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T03:31:08Z
lease_expires_at: 2026-10-06T15:31:08Z
worktree: .worktrees/T-0272
branch: task/T-0272
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01, P-STORE-02]
reviewer: null
depends_on: [T-0267, T-0268]
verify: [ops/test, ops/check-pins]
acceptance:
  - "routerDeps' identify reads x-scenic-account-token (T-0267 R8's header) and resolves the tier from the entitlements table: active and not past expires/grace -> paid; anything else (missing, malformed, unknown, inactive, expired at the boundary instant) -> anon; the tier is NEVER read from any other client field (T-0256 R3); a table test through ROUTES['/plan'], ['/loop'], ['/trip'] per state (whole answer + quota state by equality), the expiry/grace instants tested at exactly-now and now+1 ms"
  - "a D1 failure while resolving the tier fails CLOSED to anon (never paid); the token is never logged or echoed; RULE in the Log the residual risk that an appAccountToken is a bearer secret until App Attest + JWT (plan Auth) exist"
  - "REFUND_REVERSED re-activates a row it previously deactivated (signedDate guard unchanged) - tests by name; the killSwitchRoutes and P-STORE-02 bindings stay green; a TS mutation population entry set with a literal floor"
---
## Brief

T-0267 stillOpen (b)/(e) and T-0268 stillOpen 3: /asn stores entitlements and /trip has a paid itinerary, but every
caller is anon (T-0256 R3), so nothing paid is reachable through ROUTES. Plan: quotas anon 3 / free 10 / paid 200.

## Log
- 2026-10-06T03:25:02Z filed by agent/claude-opus-5 (orchestrator) from T-0267/T-0268's stillOpen.
- 2026-10-06T03:29:33Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0267 (#158) and T-0268 (#159) merged.
- 2026-10-06T03:31:08Z claimed by agent/claude-opus-5; lease until 2026-10-06T15:31:08Z
