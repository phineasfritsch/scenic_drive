---
id: T-0322
title: The app's session carries the purchase - /attest and /assert send the appAccountToken so the session JWT has `act`, and plan, trip and loop move to the Bearer before IDENTITY_HEADERS closes, so no subscriber is downgraded to anon on that day
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T15:57:13Z
lease_expires_at: 2026-10-09T01:57:13Z
worktree: .worktrees/T-0322
branch: task/T-0322
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, services/api/src/, services/api/test/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-PRIV-05]
reviewer: null
depends_on: [T-0315]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: what /attest and /assert accept today for `act` (T-0278/T-0310), what SessionStore/AttestClient send, how the tier is read when a Bearer verifies (identifyCaller), and the order of the switch-over (session carries act -> clients send Bearer -> IDENTITY_HEADERS may close); a subscriber's tier is never lower during any step"
  - "Full-equality request tables for attest/assert over {no purchase, live, expired} and for plan/trip/loop over {session with act, session without act, no session}; the Worker's answer decides the tier, never the client"
  - "Digests re-approved; ios-compile + ios-screenshot pass; population entries MISSED before and CAUGHT by name after"
---
## Brief

rv1-t0315 recordable R3 / T-0315 owner stillOpen 1 (PR #206): today the paid tier reaches the Worker only through the
bare x-scenic-account-token header, which the Worker honours only while IDENTITY_HEADERS is "1". The session JWT has
no `act` because the app attests without one.

## Log
- 2026-10-08T12:24:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0315's recordable R3.
- 2026-10-08T15:57:13Z claimed by agent/claude-opus-5; lease until 2026-10-09T01:57:13Z
- 2026-10-08T16:03:18Z MEASURE then RULE (agent/claude-opus-5, before any code), on 487cae1f.
  MEASURED:
  - M1 the Worker already issues `act` (T-0278 R5, T-0280): services/api/src/attest.ts handleAttest (lines 89-95, 118)
    and handleAttestAssert (133-138, 162) admit one optional body key `appAccountToken` beside the fixed keys, lowercase
    it, refuse a non-UUID as 400, and sign it as `act` with NO entitlement read - a live, an expired and an unknown
    token all become `act`. No Worker source change is needed for the session to carry the purchase.
  - M2 identifyCaller (sessionIdentity.ts 39-47), the tier of /plan, /trip, /loop (routerDeps.ts 83-85): no
    SESSION_JWT_SECRET -> legacy (the bare headers), whatever Bearer is sent; secret set and the Bearer verifies -> sub
    is the bucket and the tier is act's live entitlement, the x-scenic-account-token header IGNORED; a Bearer that does
    not verify -> the unidentified bucket, anon; no Bearer -> legacy only while IDENTITY_HEADERS is "1".
  - M3 the app today: AttestClient's bodies are {attestation, challenge, device, keyId} and {assertion, challenge,
    keyId} - no appAccountToken, so every session issued has no act; SessionStore's one consumer is LedgerClient
    (LiveSurpriseLedger.swift:19 builds the launch's one store); IdentityHeaders sends content-type, x-scenic-device and
    x-scenic-account-token and never `authorization` (T-0315 R1). The paid tier reaches the Worker only via the header.
  - M4 the consequence of M2 that orders the switch-over: a Bearer whose act is not the device's current purchase (a
    session issued before the purchase, or one without act) reads ANON even with the live header beside it. "Send the
    Bearer once you hold one" would downgrade every subscriber whose session predates the purchase - flag on or off.
  - M5 logging: no print/os_log/NSLog/Logger in Sources/ScenicAPIClient or PlanAdapter, no console.* in attest.ts,
    sessionIdentity.ts, sessionJwt.ts (grep, 0 lines each).
  RULED:
  - R1 POST /attest and /attest/assert carry `appAccountToken` = the AccountTokenProvider's token, lowercased, exactly
    when the device holds one - live or expired alike (the client never decides a tier; the Worker reads the
    entitlement on every request); no token -> no key (never null, never ""). Sorted keys, so it is the body's first.
  - R2 the Keychain record remembers the act it was issued for: SessionRecord gains `act` (wire key "act", omitted when
    nil). Every record written before this change reads back byte-identical as act nil - no forced re-attest.
  - R3 a session is used only when it is live AND its act equals the device's current token (nil == nil). Otherwise it
    is renewed by assertion carrying the current token (R1). A PURCHASE AFTER ISSUE: the first request after StoreKit's
    token changes finds act != token and renews with the new act; T-0310 R3's one-acquisition-per-launch budget becomes
    one acquisition per token value per launch, so a purchase mid-launch gets its own one try and nothing can loop (the
    value changes only on a purchase). A spent budget for the current value means no session for that value.
  - R4 /plan, /trip, /loop send `authorization: Bearer <jwt>` exactly when R3 yields a session for the token the same
    request names in its header; otherwise no Bearer (never a stale one, so M4 cannot fire). The x-scenic-account-token
    header STAYS beside the Bearer for the whole migration window: with SESSION_JWT_SECRET unset the Worker reads only
    the header (M2), so dropping it would lower the tier in that step. Removing it is post-closure follow-up work.
  - R5 the switch-over order (tier of a live subscriber; "hdr" = x-scenic-account-token, "B(act)" = Bearer whose act
    is the device's token):
    | step | Worker | app sends | Worker reads | tier |
    | 0 before this PR | any | hdr | hdr (legacy) | paid while flag "1" |
    | 1 this PR, secret unset | flag any | hdr + B(act) | hdr (legacy) | paid |
    | 2 this PR, secret set, flag "1" | | hdr + B(act) | B(act) | paid |
    | 2' acquisition failed (offline, no App Attest, rate limit, spent) | flag "1" | hdr, no Bearer | hdr | paid |
    | 2'' purchase newer than the session, renewal pending | flag "1" | renew first (R3), then hdr + B(act) | B(act) | paid |
    | 3 IDENTITY_HEADERS closes (owner, NOT this PR) | flag unset | as 2 / 2' | B(act) / nothing | paid / 2' anon |
    | any, subscription lapsed | any | as above | entitlement read | anon - the Worker decides |
    No step this PR ships lowers a subscriber's tier. Step 3 lowers row 2' by design; its precondition (measure the
    share of plan-family requests that arrive without a Bearer) is owner work outside this task, recorded here.
  - R6 the Worker decides: Swift tables assert request BYTES only (full equality, every row a function of its
    {session, purchase, attest server} variant); the Worker table drives /attest and /attest/assert over {no purchase,
    live, expired} (claims and token by full equality to an independently minted JWT) and then /plan, /trip, /loop with
    those sessions x {flag "1", unset}, each answer and quota state EQUAL to the paid or anon reference of its route.
  - R7 act is never logged: no logging is added (M5); the Worker table records every console call and expects none.
  - R8 one SessionStore per launch serves the ledger AND the three planners (new PlanAdapter `LiveSession`), so the
    acquisition budget is one store's; the store holds the launch's StoreKitAccountToken so a ledger-driven
    acquisition carries act too. New protocol PlanSessionProvider (allowlisted: a signature, no code).
  - R9 populations: ops/mutate/session_mutations.py gains the R1-R4 entries (MISSED under --prove-vacuity, CAUGHT by
    name after); accounttoken_mutations.py's call-site anchor moves with the code. P-STORE-02 binds the new Worker
    test by name; P-PRIV-05 is unaffected (the attest bodies and the Bearer carry no coordinate) - recorded, not edited.
- 2026-10-08T17:19:37Z RED, GREEN, POPULATIONS (agent/claude-opus-5).
  - RED FIRST BY NAME: the API skeleton (new parameters accepted and ignored: AttestClient account, SessionRecord act
    off the wire, SessionStep act, SessionStore.planSession -> nil, IdentityHeaders bearer, the clients' session) with
    SessionAccountTests + PlanBearerTests: `Test run with 10 tests in 2 suites failed` - FAILED by name: "attest and
    assert carry exactly the purchase's token, live or expired, or none" (6 cases), "the session record keeps its act
    on the wire, and an empty or null act is malformed" (3), "a live session is used only while its act is the
    device's purchase" (9), "a session issued before the purchase renews once to carry it, then is used with no
    request" (2), "the ledger's acquisition carries the store's purchase, and the plan family then uses that session"
    (3), "a failed renewal for the purchase is that token's one try: ...", "every plan-family request names the
    purchase and carries the Bearer exactly when its act is that purchase" (54). Green on the skeleton, by design:
    the meta-test, "a session issued before the purchase is never sent" and "a request refused on the device acquires
    no session" (guards against a regression the skeleton cannot make; each seen red below, entries 63/76 and 75).
  - GREEN: `swift test --filter ScenicAPIClientTests` -> `Test run with 87 tests in 20 suites passed` (after the
    eleventh test, "a purchase made after the launch's first acquisition gets its own one try", was added for entry 64).
  - WORKER (no src change, M1): services/api/test/sessionCarriesAct.test.ts `Tests 36 passed (36)`; with tierCarriers,
    sessionIdentity, attestAssert, attestAccept, identityVerifierPin, requestReadSites, reflectionSites, asnState:
    `Test Files 9 passed (9)`, `Tests 287 passed (287)`. run-named-tests.py P-STORE-02 -> `NAMED P-STORE-02
    passed=97/97` (61 + 36). Seen RED by name (one-off mutants of src/, each restored byte-for-byte, git status clean):
    W1 assert drops act CAUGHT (8 FAILED: the act-live rows of /plan /trip /loop x flag, and the live/expired
    attest-assert rows); W2 attest drops act CAUGHT (2: attest-assert live, expired); W3 a Bearer without act falls back
    to the header CAUGHT (6: every "no act" row); W4 any act is paid CAUGHT (6: every "act expired" row); W5 the header
    beside a verified Bearer is read CAUGHT (12: every "act expired" and "no act" row).
  - SWIFT POPULATION (ops/mutate/session.py, entries 57-76, E3): CAUGHT AFTER, by name - `--only 57..76` caught 19/20
    on 754da4e2 with 75 a WRONG KILLER (red only through the 54-row table: the refusal row held a session for no
    purchase, so `planSession(account: nil)` made no request). Fixed in 17391247 (the refusal row asks an empty store
    that any ask makes attest); `--only 75` -> `MUTATE OK caught=1/1`. MISSED BEFORE: session.py's machinery with ONLY
    the two new test files emptied (every pre-T-0322 suite in the filter intact; driver .build/t322msg/before.py) ->
    `VACUITY PROOF OK: with the 2 test file(s) emptied, caught=0 (need 0) and MISSED=20 of 20`. accounttoken.py
    entries whose anchors moved: `--only 5,6,7,13` caught 5, 6, 13; 7 reported compile-only because I emptied test
    files in this worktree while it built (my interference, not the mutant); `--only 7` rerun -> `MUTATE OK caught=1/1`.
  - R10 (ruled while measuring): accounttoken entry 13's anchor `guard let installID ...` has occurred TWICE in
    PlanClient since T-0319's reroute(), so on main it reports SKIP; the anchor now carries plan()'s next line
    (PLAN_BODY) and is caught again. R11: session.py's full `--prove-vacuity` cannot build on main today -
    Tests/ScenicKitTests/Surprise/SurpriseCardHistoryTests.swift and SurpriseShownDayTests.swift reference
    SurpriseShowingTests, which the vacuity mode empties (`error: cannot find 'SurpriseShowingTests' in scope`). Not
    this task's file set; filed as stillOpen for the orchestrator (my touches do not include queue/backlog/).
  - DIGESTS: [PINNED_ROOT_SOURCES] rows re-approved in place for AttestClient, IdentityHeaders, LoopClient, PlanClient,
    SessionRecord, SessionStep, SessionStore, TripClient; PlanSessionProvider added after PlanResponseReader (9 rows).
  - iOS CI on 754da4e2: ios-compile 37809049629 `completed success` (3m48s); ios-screenshot 37809056825 `completed
    success` (18m45s).
