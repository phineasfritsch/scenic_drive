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
- 2026-10-08T17:45:00Z FINAL, on the merged head (agent/claude-opus-5). `git fetch origin` + merge of origin/main
  9e910336 (queue-only: T-0327 filed/claimed; no gate file moved) as 8a47cf6f, message amended with the attribution.
  The bare disclaimer guard then refused LiveSession.swift ("Found 78 *.swift entr(ies) under apps/ios; approved 77"):
  the -pinned app table is re-approved in the same diff (LiveLoopPlanner, LivePlanner, LiveSurpriseLedger,
  LiveTripPlanner re-hashed; LiveSession added after LivePlanner). App Swift is byte-identical to 754da4e2, where both
  iOS workflows passed; the merge and this commit touch no app source.
  ACCEPTANCE, re-quoted:
  1. "MEASURE then RULE FIRST ... a subscriber's tier is never lower during any step" - M1-M5 and R1-R9 in the
     16:03:18Z entry, committed (628e1774) before any code; the switch-over table is R5.
  2. "Full-equality request tables for attest/assert over {no purchase, live, expired} and for plan/trip/loop over
     {session with act, session without act, no session}; the Worker's answer decides the tier, never the client" -
     Swift: SessionAccountTests (attest/assert bodies x 3 purchases, whole request) and PlanBearerTests (3 routes x
     {with act, without act, no session} x 3 purchases x {server answers, down}, 54 whole requests + the store's attest
     requests, meta-test per dimension): `Test run with 87 tests in 20 suites passed`. Worker: sessionCarriesAct.test.ts
     (tokens equal to minted JWTs; every route x 5 held sessions x flag equal to the paid or anon reference):
     `Tests 216 passed (216)` with tierCarriers, sessionIdentity, attestAssert, attestAccept, identityVerifierPin.
  3. "Digests re-approved; ios-compile + ios-screenshot pass; population entries MISSED before and CAUGHT by name
     after" - digests: 9 [PINNED_ROOT_SOURCES] rows + 5 -pinned app rows; `bash ops/lib/check-safety-disclaimer`
     exit 0; CI above; population 57-76 MISSED=20 of 20 before, caught by name after (19 + 75 rerun).
  GATES (bare, merged head + this commit's tables): check-safety-disclaimer exit 0; check-store-links.py exit 0;
  check-mutate-population.py exit 0 ("the floor of 137 holds"); check-line-cap exit 0 ("489 Swift files ... none over
  300 lines"); check-pins-yaml.py exit 0 (pins=48); ops/queue-check exit 0 ("QUEUE OK (318 tasks)").
  STILL OPEN (for the orchestrator to file; my touches exclude queue/backlog/): (a) session.py --prove-vacuity does not
  build on main (R11); (b) before IDENTITY_HEADERS closes (R5 step 3), measure the share of plan-family requests that
  arrive with no Bearer; after it closes, drop x-scenic-account-token from IdentityHeaders.
- 2026-10-08T18:43:08Z agent/claude-opus-5: PRE-REVIEW M3 (BLOCKING) closed by CLASS. The survivor: attest.ts line
  95 / 138 with `UUID.test(act.slice(0, 36))` passed the whole Worker suite (2267/2267) - a 37-character
  appAccountToken minted a session on both /attest and /attest/assert. RULED: the hole is not one bound but the
  whole ruled shape at both call sites - the only rows were a 35-character token missing its FIRST char, "not-a-uuid",
  null and upper case. CLASS = every bound of asn.ts's UUID after lowercasing: length 35/37 at either end (and 72),
  each hyphen moved or replaced, one past each end of 0-9, a-f, A-F, trailing space/newline, empty, number, object.
  FIX: services/api/test/accountTokenShapes.ts `malformedTokens(token)` - 20 rows, each a function of the one valid
  token - run whole as defects in attestVerify.test.ts (POST /attest via postAttest, 400 invalid_attestation, tables
  unchanged) and attestAssert.test.ts (shipped route, 400 invalid_assertion, all four tables unchanged);
  `ADMITTED_TOKENS` (0-9/a-f and 0-9/A-F at both bounds) in sessionCarriesAct.test.ts: both routes' answers EQUAL a
  JWT minted with act = the lower-case token. No src change - the routes were right; the tests did not pin them.
  POPULATION: 9 entries per route, one per class member (tail, head, short-padded, hyphens-unplaced, before-0, past-9,
  before-a, past-f, multiline `$`): attestMutants.mjs attest-act-* (floor 60 -> 84 = the population),
  assertMutants.mjs assert-act-* (floor 40 -> 58). Both `--prove-floor` quiet on the real population.
  BEFORE (the three test files stashed to branch head 22c9656d, --only the 18 ids): attest `RESULT caught=0 missed=9
  trap=0 of 9`, assert `RESULT caught=0 missed=9 trap=0 of 9`. AFTER: attest `RESULT caught=9 missed=0 trap=0 of 9`
  (tail by "appAccountToken of 37 characters: a hex digit appended", head by "... a hex digit prepended", short by
  "... 35 characters: the last dropped", hyphens by "... first hyphen moved one place right", '/', ':', '`', 'g' by
  their rows, multiline by "... a newline appended"); assert `RESULT caught=9 missed=0 trap=0 of 9`, the same rows
  under "body: ". Touched files: `Tests 221 passed (221)` (attestVerify, attestAssert, sessionCarriesAct,
  attestAccept; 179 + 42). No Sources/ or apps/ios change, so no digest row moves and no iOS re-trigger is owed.

### 2026-10-08T19:17:23Z - review round 1 (rv1-t0322 FAIL, B1): rulings before code
- B1 stands. At 91d67b28 `identifyCaller` answered `{unidentified, anon}` for a present Bearer that fails verification
  BEFORE it read IDENTITY_HEADERS, so under flag "1" a live subscriber whose Bearer is expired, signed by a rotated
  secret or of another SESSION_TTL_S read anon where the header alone reads paid (reviewer's witness: headerOnly 200,
  withStale 429). R5 ("no step lowers a subscriber tier") was false for it.
- RULING (a), orchestrator, REQUIRED: while IDENTITY_HEADERS is "1", a Bearer that fails verification falls back to
  the header path (`legacy`) exactly as if no Bearer were sent; with the flag off it stays `{unidentified, anon}`. Not
  a fail-open: a forged Bearer plus the header yields only what the header alone yields. Shape: no Bearer and an
  unverifiable Bearer share ONE line - `claims` is null for both, and the flag decides once. R5 is restated: under
  flag "1" an unverifiable Bearer reads exactly as no Bearer; under flag off it is anon, as no Bearer is.
- Table (sessionCarriesAct): routes x {valid act live, valid act expired, valid no act, expired, wrong secret, wrong
  TTL, malformed, absent} x {flag "1", off} x {header live, expired, absent}; each whole answer (status, json, quota
  state, console) EQUALS the reference picked by a pure `ruled()` from the rule (valid: act live -> paid, else the
  device bucket anon; otherwise flag "1" -> the header's tier in the device bucket, flag off -> unidentified anon);
  a meta-test proves for every dimension and every value that some row's reference changes when that value alone
  changes. The ruling's "valid-with-act" is split into act live / act expired (a superset).
- Ripple, ruled: sessionIdentity.test.ts's INVALID rows ran only under flag "1" expecting unidentified; they now run
  under both flags (flag "1": today's header identity of LEGACY_HEADERS; off: unidentified). waitlistDedupe's
  `bucket()` treated a malformed Bearer as unidentified in legacy mode; it now follows the rule (the header's bucket
  in legacy, unidentified without), and its step name says so. ledger.ts / account.ts read BEARER themselves and do
  not call identifyCaller: unchanged.
- Population (attestMutants.mjs): `ident-fallthrough` becomes the inverse (fallback also with flag off; must be
  CAUGHT) and `ident-early-anon` restores the 91d67b28 line ahead of the shared one (MISSED at 91d67b28 by
  construction - it IS that code and its tests asserted it - CAUGHT by name now). MIN_MUTATIONS 84 -> 85.
- RULING (b), client, in scope (<= ~40 source lines): SessionStore.keep stores the session's expiry on the DEVICE's
  clock - receipt time plus the token's own lifetime `exp - iat` read from its payload (SessionRecord.lifetime) - and
  falls back to the server's expires_at only when the payload is not {iat, exp} integers with exp > iat. A device
  clock any amount slow or fast then uses the session for exactly lifetime - margin seconds after receipt, so it
  never rides a session the Worker considers expired (up to request latency, which the 60 s margin covers). Table at
  the bounds (SessionSkewTests): device offsets {-7200, -3600, -61, -60, 0, +60, +61, +3600} x elapsed {3539, 3540,
  3541} -> used iff elapsed < 3540, every write compared whole. Mutants 77-79 in session_mutations.py.
- NOT in scope, recorded: after IDENTITY_HEADERS closes (step 3), a Bearer the Worker cannot verify (secret
  rotation) still reads anon with no recovery inside the launch, because the plan family has no 401 path (the Worker
  answers 200/429 as anon). Follow-up: the Worker would need to signal an unverifiable Bearer on the plan family
  before step 3; filed as a note for the step-3 task, not built here.

### 2026-10-08T19:55:51Z - review round 1 fixes landed (B1 a + b)
- (a) Worker 25ef1f31: `identifyCaller` computes `claims` null for no Bearer AND for one that fails verification,
  and one line decides: `if (claims === null) return env.IDENTITY_HEADERS === "1" ? legacy() : {unidentified, anon}`.
  sessionCarriesAct: 153 tests (3 sign + ADMITTED rows + 1 meta + 3 references + 144 cross-product rows) green.
  Seen RED by name (.build/t0322_red.py, src restored byte-equal): restoring the 91d67b28 early-anon line ahead of
  the shared one failed 12/153 (every route x {expired, wrong secret, wrong TTL, malformed} x flag 1 x header live -
  the reviewer's witness, now a row); the inverse (fallback also with the flag off) failed 15/153 (those Bearers and
  no Bearer, flag unset, header live). attestMutants.mjs --only on the touched entries: `RESULT caught=4 missed=0
  trap=0 of 4` (ident-fallthrough and ident-early-anon by "now = exp (bound)", ident-flag-ignored likewise,
  ident-flag-any-value by "... IDENTITY_HEADERS unset or 0 ..."); --prove-floor quiet on the real population (85).
  At 91d67b28 the early-anon line WAS the code and its tests asserted it (reviewer: 336/336 green) - MISSED there.
- (b) client 092e8321: SessionRecord.lifetime + SessionStore.keep (+22/-1 source lines). SessionSkewTests: offsets
  {-7200,-3600,-61,-60,0,60,61,3600} x elapsed {3539,3540,3541}, the lifetime table at every bound, the fallback
  rows. `swift test --filter` the 6 session suites: `Test run with 27 tests in 6 suites passed`.
  `python ops/mutate/session.py --only 77,78,79,80,81`: `MUTATE OK caught=5/5`, each by the test it names.
- Digests re-approved for SessionRecord.swift and SessionStore.swift (gate seen red on both, then exit 0).
- P-STORE-02: sessionCarriesAct's 36 bound names replaced by 151 (ADMITTED rows stay unbound, as before);
  check-named-table approval 103 -> 218, digest 2e457a58...; PINS.yaml text records the round.
- Still open, recorded not built: after IDENTITY_HEADERS closes, a Bearer the Worker cannot verify (secret
  rotation) reads anon with no in-launch recovery - the plan family has no 401 path. B1(b) removes the clock-skew
  source; rotation remains for the step-3 task.
