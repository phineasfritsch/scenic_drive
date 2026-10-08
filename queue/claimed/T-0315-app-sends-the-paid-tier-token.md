---
id: T-0315
title: The app sends its paid-tier identity (x-scenic-account-token from the StoreKit entitlement, per T-0272) on plan, loop and trip requests, so a subscriber gets the full itinerary and per-day handoff, and a non-subscriber keeps the free preview
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T09:35:56Z
lease_expires_at: 2026-10-08T17:35:56Z
worktree: .worktrees/T-0315
branch: task/T-0315
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-COST-01]
reviewer: null
depends_on: [T-0272, T-0313, T-0310]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: what the Worker's tier seam reads today (T-0272: x-scenic-account-token -> purchase id with a live entitlement; T-0278 R6 IDENTITY_HEADERS migration window) versus the session JWT path (T-0310), which one the app sends and when, where the token comes from (StoreKit 2 originalTransactionID / appAccountToken in the Keychain - plan, Entitlement row), and that it is never logged"
  - "Every request client (PlanClient, TripClient, LoopClient if present) attaches the identity by one shared function; table by full equality over {no purchase, live purchase, expired purchase, session present/absent}; the trip preview vs full itinerary follows the Worker's answer, never a client-side guess"
  - "ios-compile + ios-screenshot pass; digests re-approved; population entries MISSED before and CAUGHT by name after"
---
## Brief

rv1-t0313 recordable 1 / T-0313 owner stillOpen (PR #201): the app sends no x-scenic-account-token, so every trip is the
anon preview and the per-day Apple Maps handoff is unreachable. The plan's paid tier unlocks the full itinerary,
unlimited plans and navigation.

## Log
- 2026-10-08T06:32:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0313's recordable 1.
- 2026-10-08T09:35:56Z claimed by agent/claude-opus-5; lease until 2026-10-08T17:35:56Z
- 2026-10-08T09:40:13Z **MEASURED, then RULED before code** (agent/claude-opus-5, owner). Read at d908849b:
  services/api/src/{accountTier,sessionIdentity,routerDeps,asn,attest}.ts, wrangler.jsonc, Sources/ScenicAPIClient/
  {PlanClient,TripClient,LedgerClient,SessionStore,AttestClient}.swift, PlanAdapter/*, Entitlements/PaywallScreen.swift,
  queue/done/T-0272 (R1-R5), T-0278, T-0310, T-0313, the plan's Entitlement row; origin/task/T-0314's LoopClient.
  - **M1 what the Worker reads.** routerDeps.identify = identifyCaller(authorization, env, now, legacy). Without
    SESSION_JWT_SECRET, or with it but NO Bearer while IDENTITY_HEADERS == "1" (wrangler.jsonc vars: "1" today), the
    tier is `legacy`: accountTier reads `x-scenic-account-token` (asn.ts ACCOUNT_TOKEN_HEADER), lowercased, RFC 4122
    shape, paid iff readEntitlement says active at now; everything else (absent, malformed, unknown, expired, D1
    throw) is anon. With a Bearer that verifies, the bare headers are IGNORED and the tier is the JWT's `act` claim's
    entitlement; `act` is set only when /attest or /assert carried `appAccountToken`.
  - **M2 what the app sends today.** PlanClient and TripClient send exactly {content-type, x-scenic-device}; no
    account token anywhere under Sources/ or apps/ios (grep appAccountToken / x-scenic-account-token: 0 hits outside
    services/api). SessionStore attests with NO appAccountToken, so every session JWT the app holds has no `act`.
    The paywall's SubscriptionStoreView sets no purchase option, so no transaction carries an appAccountToken and
    /asn could never key a row the app could name. Logging: grep print( / Logger / os_log / NSLog over
    Sources/ScenicAPIClient and PlanAdapter: 0 files.
  - **R1 which identity the app sends, and when.** Plan, trip (and loop) requests carry the HEADER identity:
    x-scenic-device (unchanged) plus `x-scenic-account-token` = the purchase's appAccountToken lowercased, whenever
    the device holds one; no header when it holds none. They carry NO Bearer. Disagreement with the acceptance's
    "session present/absent" axis, ruled: a Bearer without `act` reads anon under SESSION_JWT_SECRET (M1), so
    attaching the session today would DOWNGRADE a subscriber; the session therefore is not an input of these
    clients (structurally: PlanClient/TripClient hold no LedgerSessionProvider) and the table's session axis is the
    proof that the request is the same with or without one held - realized as the whole-request equality over the
    token axis with the session-only `authorization` header absent from every row. Moving plan/trip/loop to the
    Bearer needs `appAccountToken` in the attest/assert body first; that is a follow-up (stillOpen), not this PR.
  - **R2 one shared function.** `IdentityHeaders.json(device:account:)` (Sources/ScenicAPIClient) builds the WHOLE
    header set of every plan-family request; PlanClient and TripClient call it and nothing else builds those headers.
    The token comes from an injected `AccountTokenProvider` (async, `UUID?`), a REQUIRED init argument like installID
    (nil must be said). It is read after the body validated, so a device refusal reads nothing and sends nothing.
  - **R3 where the token comes from.** StoreKit 2's own transactions: PlanAdapter `StoreKitAccountToken` walks
    `Transaction.all` (verified, auto-renewable, appAccountToken non-nil) and `AccountTokenCandidate.latest` (Linux-
    tested) picks the most recent purchase's token - LIVE OR EXPIRED OR REVOKED, because the client never guesses the
    tier: an expired token is sent and the Worker answers anon (the free preview). Disagreement with the plan's
    "appAccountToken in iCloud keychain", ruled: the token rides the transaction itself, which StoreKit already
    syncs to every device on the Apple ID and restores with AppStore.sync - one copy, no Keychain item to drift. The
    paywall attaches a fresh `appAccountToken` to each purchase (`inAppPurchaseOptions`); renewals keep it.
  - **R4 never logged.** No client, provider or error carries the token into a description, a Telemetry event or a
    print; PlanError/TripError have no associated string. The value is never printed in this Log or in CI output.
  - **R5 trip preview vs full.** TripClient returns exactly TripReplyReader's reading of the Worker's reply: a token
    with a preview reply is a preview, no token with a full reply is full - the table holds both crossings.
  - **R6 LoopClient.** Not on main (PR #204 open; its LoopClient builds {content-type, x-scenic-device} inline). If
    #204 merges before this PR's final merge, LoopClient adopts IdentityHeaders.json and joins the table in that merge
    commit; otherwise the merge that comes second (T-0314's merge-main round) adopts it - recorded in stillOpen.
  - **R7 population.** New ops/mutate/accounttoken{,_mutations,_run}.py over IdentityHeaders.swift and
    AccountTokenCandidate.swift (+ the two call sites in PlanClient/TripClient); MISSED by --prove-vacuity, CAUGHT by
    name after. DRIVERS and COVERED_FLOOR gain it. Digests re-approved for every Sources/ + apps/ios file touched.
- 2026-10-08T09:50:48Z **RED by name, then GREEN** (agent/claude-opus-5). With IdentityHeaders.json ignoring
  `account` and AccountTokenCandidate.latest returning nil (the API in place, the clients wired), `swift test
  --filter "AccountTokenHeaderTests|AccountTokenCandidateTests"`: RED - "every plan request carries exactly the
  device and the purchase's account token" (2 of 4 cases: live, expired), "every trip request carries exactly the
  device and the account token, and the itinerary is the Worker's" (4 of 8: live and expired x preview and full),
  "the latest purchase's token is the one sent, live or expired, in every StoreKit order" (15 issues); "a request
  refused on the device reads no account token and sends nothing" and the rows-are-functions meta test green (they
  hold by construction). Implemented: `Test run with 5 tests in 2 suites passed`.
  Apple side: PlanAdapter `StoreKitAccountToken` (Transaction.all, verified auto-renewable) handed to PlanClient and
  TripClient by LivePlanner/LiveTripPlanner; PaywallScreen `.inAppPurchaseOptions { _ in [.appAccountToken(UUID())] }`
  placed after `.storeButton(.hidden, for: .cancellation)` because P-STORE-01 freezes the run from
  SubscriptionStoreView through `.safeAreaInset` (first placement refused: "the paywall's modifier chain ... occurs
  0 time(s)"). Re-approved: store_links_pinned FROZEN[PW] e78e2079.. -> 333b33ed..; PINNED_APP_SWIFT rows for
  PaywallScreen, LivePlanner, LiveTripPlanner (changed) and StoreKitAccountToken (added); linked-digests rows for
  PlanClient, TripClient (changed) and AccountTokenCandidate, AccountTokenProvider, IdentityHeaders (added). Bare
  guards: check-safety-disclaimer exit 0, check-map-attribution exit 0, check-store-links exit 0.
- 2026-10-08T10:34:39Z **Population, CI** (agent/claude-opus-5) at 662aa929. `swift test --filter
  ScenicAPIClientTests`: `Test run with 58 tests in 14 suites passed` + XCTest 4+11+26+4+46, 0 failures.
  `python ops/mutate/accounttoken.py`: `caught by the test that names it: 13 of 13 (wrong killer 0, trapped 0,
  compile-only 0, MISSED 0, skipped 0)`, `MUTATE OK caught=13/13 equivalent_caught=0` (E1 MISSED as required).
  CAUGHT by name: 1-4, 12 by "every plan request carries exactly the device and the purchase's account token" and
  "every trip request carries exactly the device and the account token, and the itinerary is the Worker's"; 5 by
  the plan row, 6 by the trip row; 8-11 by "the latest purchase's token is the one sent, live or expired, in every
  StoreKit order"; 13, 14 by "a request refused on the device reads no account token and sends nothing".
  MISSED before: `--prove-vacuity` (both test files emptied): `caught by the test that names it: 0 of 13 ...
  MISSED 13`, `VACUITY PROOF OK: with the 2 test file(s) emptied, caught=0 (need 0) and MISSED=13 of 13`.
  `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control did not`. check-mutate-population first
  refused AccountTokenProvider.swift (a protocol); allowlisted with its reason -> `every added module is covered or
  allowlisted; the floor of 116 holds`. ios-compile run 37760671707 success, ios-screenshot run 37760729288
  success (both at 662aa929). Pins: P-STORE-02 and P-COST-01 unchanged - services/api is untouched; P-STORE-02's
  "NOT ASSERTED HERE: the app's side" stands (the new suites are not bound by name in run-named-tests).
