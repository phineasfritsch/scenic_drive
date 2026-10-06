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
- 2026-10-06T03:43:10Z **RULED before code** (agent/claude-opus-5, owner). Read T-0256 (R2, R3), T-0267 (R5-R8),
  T-0268 (R5, the full itinerary for `who.tier === "paid"`), T-0269 (P-STORE-02's sixty-one bindings).
  - **R1 token header and format.** The tier is read from ONE client field: header `x-scenic-account-token`
    (asn.ts's ACCOUNT_TOKEN_HEADER, T-0267 R8), lowercased, accepted only in the RFC 4122 shape asn.ts's /entitlement
    already enforces (the same exported regex, never a second copy). Missing or malformed is anon WITHOUT a D1 read
    (not 400, unlike GET /entitlement: the header is optional on /plan, /loop, /trip and an anon caller must keep
    working). The quota bucket (userId) stays the install UUID from `x-scenic-device` (T-0256 R2); the token only
    picks the allowance. x-scenic-tier, a body `tier` field, the token sent as x-scenic-device or as a bearer
    `authorization` all stay anon (T-0256 R3) - tested.
  - **R2 state -> tier.** Exactly readEntitlement's (T-0267 R8) answer for the token at the Worker's now: `active`
    -> paid; `none` (unknown token), `inactive` (EXPIRED/REFUND/REVOKE/GRACE_PERIOD_EXPIRED) -> anon. There is no
    `free` tier yet (no account system), so the two outcomes are paid and anon. One reader, so GET /entitlement and
    the quota can never disagree on a token.
  - **R3 expiry/grace instants.** A row is live iff status active and (active_until null or now < active_until). For
    a SUBSCRIBED/DID_RENEW row active_until is the transaction's expiresDate; for DID_FAIL_TO_RENEW/GRACE_PERIOD it is
    gracePeriodExpiresDate. So active_until == now (exactly-now) -> anon ("expired at the boundary instant") and
    active_until == now + 1 ms -> paid, for both the expiry and the grace row; tested at both instants through
    ROUTES['/plan'], ['/loop'], ['/trip'].
  - **R4 D1 failure -> anon.** Any throw while resolving (prepare, bind, all; a missing DB binding) is caught and the
    caller is anon - fail CLOSED on cost, never paid. Nothing is logged on that path or any other: identify writes no
    console line, and the token is in no answer (answers are compared whole, and console.log/info/warn/error/debug are
    spied and must be uncalled). A D1 outage therefore downgrades paying users to anon for its duration - the safe
    direction for spend; GET /entitlement still answers 503 for the app to explain it.
  - **R5 residual risk (bearer token).** The appAccountToken is a BEARER SECRET until App Attest + a signed JWT
    (plan Auth) exist: anyone who learns a paying user's token (a shared phone, a leaked log on the client, a
    proxy) gets paid allowances on their own install UUID, and a token shared over N installs earns N paid daily
    allowances, because the bucket is the install (R1). Bounded by MAX_MONTHLY_UPSTREAM_CALLS (P-COST-02) and the
    kill switch (P-COST-01), not by anything per-token. Accepted for now; closed only by the Auth milestone.
    The Worker never echoes or logs the token, so it does not leak from our side.
  - **R6 REFUND_REVERSED.** Apple sends it when it reverses a refund it granted; the app must reinstate the content.
    It joins ACTIVATES: status active, active_until = the signed transaction's expiresDate (as SUBSCRIBED). The
    signedDate guard is UNCHANGED (strictly newer wins), so it re-activates the row its REFUND deactivated, an older
    REFUND_REVERSED never overrides a newer REFUND/EXPIRED, and a reversal for a subscription whose expiresDate has
    passed lands active but reads inactive (anon) at R3. It leaves the "every other type" table (asnState.test.ts).
  - **R7 the identify signature.** RouterDeps.identify becomes async (a D1 read); PlanDeps/LoopDeps accept a sync or
    async identify and every handler awaits it (/plan, /loop, /trip, /isochrone), so injected test fakes stay sync.
  - **R8 pins.** touches: is services/api/ - ops/lib/named-tests.json is outside it, so no new P-STORE-02/P-COST-01
    binding is added here (recorded; the new tests are named for a later binding task). The sixty-one P-STORE-02
    and twenty-two P-COST-01 bindings must stay green; killSwitchRoutes is untouched.
  - **R9 population.** services/api/test/mutate/tierMutants.mjs (the vitest-driven form of quotaMutants.mjs, since
    check-mutate-population reads Sources/ and services/etl/etl/ only), literal MIN_MUTATIONS = its length.
