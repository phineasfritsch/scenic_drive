---
id: T-0272
title: the Worker's quota tier comes from the entitlement - an active /asn entitlement for the request's appAccountToken makes the caller paid (plan 200/day, full /trip itinerary), everything else stays anon; REFUND_REVERSED restores access
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T03:31:08Z
lease_expires_at: 2026-10-06T15:31:08Z
worktree: .worktrees/T-0272
branch: task/T-0272
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01, P-STORE-02]
reviewer: agent/rv3-t0272
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
- 2026-10-06T04:18:01Z **RED first, then code, then green** (agent/claude-opus-5). Tests written before any src change:
  test/accountTier.test.ts (new) and test/asnState.test.ts (REFUND_REVERSED leaves OTHERS; describe "REFUND_REVERSED
  re-activates the row its REFUND deactivated (T-0272 R6)"). RED at 1e2ea5d + tests only: `npx vitest run
  test/accountTier.test.ts test/asnState.test.ts` -> `Tests  16 failed | 54 passed (70)`, failing BY NAME: the
  eleven entitlement states that read D1 or expect paid (an unknown token, an inactive (REFUND) row, an active row
  with no end, the active token upper-cased, active until exactly now / now + 1 ms, in grace until exactly now /
  now + 1 ms, one expired and one active transaction), both D1-failure tests (reads 0, expected 3), the three
  REFUND_REVERSED route tests and two of the four REFUND_REVERSED table tests (the older and replay arms were already
  inactive). Code (22fe1f5, a6eb580): src/accountTier.ts (new), routerDeps.ts identify async (deviceIdentity kept
  whole and lifted to paid only on a live entitlement, so quotaMutants' router-tier rows stay observable), RouterEnv
  gains DB, plan/loop/trip/isochrone await identify, asn.ts exports UUID, asnNotification.ts REACTIVATES.
  GREEN: `npx vitest run` -> `Test Files  34 passed (34)`, `Tests  475 passed (475)` (now 476 with the reference test).
  Population services/api/test/mutate/tierMutants.mjs, MIN_MUTATIONS = 18, 1 EQUIVALENT (tier-no-db-check, witness in
  the file): full run at 22fe1f5 `RESULT caught=16 missed=0 trap=2 of 18` - the TRAPs plan/loop-identify-unawaited
  failed beforeAll's reference assertion, which skipped all twenty tests and named none; the assertion moved into
  the named test "the paid states' reference answers are a plan and a loop served 200 to a fresh anon device", and
  `--only` of both: `RESULT caught=2 missed=0 trap=0 of 2`. After the identify rewire (a6eb580) the touched rows
  re-ran: `--only` deps-tier-always-anon, deps-tier-without-db, deps-now-minus-1, deps-now-plus-1,
  deps-bucket-is-token, tier-active-free -> `RESULT caught=6 missed=0 trap=0 of 6`. `--prove-vacuity` ->
  `RESULT caught=0 missed=18 trap=0 of 18`; `--prove-floor` all four arms REFUSED, real population quiet.
  **Found on main and fixed (in touches):** quotaMutants.mjs refused to run - `STALE quota-loop-free-2 / quota-loop-
  anon-2 / quota-loop-paid-201: anchor occurs 2 times in src/quota.ts`, because T-0268's DAILY_TRIP_QUOTA repeats
  DAILY_LOOP_QUOTA's `{ anon: 1, free: 1, paid: DAILY_PLAN_QUOTA.paid }` (quota.ts is unchanged here). The three
  anchors now start at `DAILY_LOOP_QUOTA = `; they and every quota row over a file this task touched re-ran:
  `RESULT caught=12 missed=0 trap=0 of 12` (incl. router-tier-free and router-tier-from-header). Every population's
  anchors counted exactly once (`stale=0` over asn/isochrone/loop/plan/quota/tier/trip).
- 2026-10-06T05:01:24Z **asn rows re-run; merged origin/main (e309799) at 5b113e8; acceptance re-quoted on the merged
  head** (agent/claude-opus-5). asnMutants.mjs `--only` its 29 rows over asn.ts and asnNotification.ts (the two asn
  files this task touched): `baseline green tests=112`, `RESULT caught=29 missed=0 trap=0 of 29`. main's delta since
  the branch point touches no services/api path (T-0270 fallback corpus, T-0273/T-0274 filings).
  On 5b113e8: `npx vitest run` -> `Test Files  34 passed (34)`, `Tests  476 passed (476)` (twice). RECORDED, not hidden:
  under heavy box load (import 273 s) one run printed `Tests  1 failed | 475 passed (476)` and an earlier one
  `Test Files 19 passed (19)`, `Tests 202 passed (202)`; neither named its test in the lines kept, the next two runs
  were 476/476, and accountTier.test.ts' slowest test measures 160 ms against vitest's 5 s timeout - an unidentified
  flake, left for the reviewer to watch in CI. `python ops/lib/run-named-tests.py P-STORE-02` -> `NAMED P-STORE-02
  passed=61/61`; `... P-COST-01` -> `NAMED P-COST-01 passed=22/22`. `python ops/lib/check-mutate-population.py` ->
  `P-PROC-06: every added module is covered or allowlisted; the floor of 67 holds`. `bash ops/queue-check` -> `QUEUE OK
  (265 tasks)`. wc -l: accountTier.ts 19, routerDeps.ts 81, accountTier.test.ts 203, asnState.test.ts 229,
  tierMutants.mjs 159, quotaMutants.mjs 202. `git grep` for console.log/info/warn/error/debug under services/api/src: none.
  1. identify reads x-scenic-account-token and resolves the tier from the entitlements table (active and before
     active_until -> paid; missing, malformed, unknown, inactive, expired at the boundary instant -> anon), never
     from another client field (the token as authorization/x-scenic-account/x-account-token/cookie, plus
     x-scenic-tier: paid, is anon with zero D1 reads); table test "the tier is the entitlement of
     x-scenic-account-token, through the shipped ROUTES (R1-R3)" - fourteen states, each through ROUTES['/plan'],
     ['/loop'], ['/trip'] with the whole answers, the whole quota state, the entitlement read count and every console
     call by one equality; expiry and grace both at active_until == now (anon) and now + 1 ms (paid). MET.
  2. D1 failure -> anon: "an entitlement read that throws at prepare leaves an active token anon", "an entitlement
     read that rejects at all() leaves an active token anon" (whole answers equal the anon expectation, 3 reads);
     never logged or echoed: console spied in every test (logged: [] inside each equality) and "no answer and no
     console line carries the token, paid or failed". The bearer-token residual risk is RULED in R5. MET.
  3. REFUND_REVERSED re-activates a row it deactivated, signedDate guard unchanged - asnState.test.ts "REFUND_REVERSED
     re-activates the row its REFUND deactivated (T-0272 R6)" (four tests: the reactivation until expiresDate with GET
     /entitlement active, the older arm, the replay arm, +1 ms lands) and accountTier.test.ts "REFUND_REVERSED restores
     access through the shipped ROUTES (R6)" (three). killSwitchRoutes untouched and green (P-COST-01 22/22);
     P-STORE-02 61/61. Population tierMutants.mjs, literal MIN_MUTATIONS = 18, caught 18 of 18 across the runs above,
     1 EQUIVALENT with witness. MET.
  NOT DONE (R8): no new name is bound in ops/lib/named-tests.json (outside touches: services/api/). A binding task
  should add the accountTier.test.ts states and the REFUND_REVERSED tests to P-STORE-02 / a P-COST row.
- 2026-10-06T05:40:42Z **pre-review survivor closed** (agent/claude-opus-5, owner). The pre-review mutant pass at
  a9ab981 found ONE survivor (BLOCKING, fail-OPEN): M4 "reversal-of-lapsed-row-open-ended" - in entitlementChange,
  `activeUntil = REACTIVATES.includes(type) && epochMs(expiresDate, ...) <= signedDate ? null : epochMs(...)` stores a
  REFUND_REVERSED whose expiresDate had already passed at signing with active_until NULL (open-ended paid). R6 rules
  that case in prose ("lands active but reads inactive (anon) at R3") and no test drove expiresDate <= signedDate.
  RULED: the CLASS is "an activating notification whose transaction lapsed at or before signing lands open-ended",
  and it covers ACTIVATES (SUBSCRIBED, DID_RENEW, OFFER_REDEEMED) as well as REFUND_REVERSED, at every bound
  expiresDate - signedDate in {-1, 0, +1} ms (all three before now). Closed by:
  - accountTier.test.ts "an activation whose expiresDate had passed when Apple signed it stays anon through the
    shipped ROUTES (R6)" - twelve rows (4 types x 3 offsets), signedDate T - 1000, a REFUND at T - 2000 first for
    REFUND_REVERSED; each drives ROUTES['/plan'], ['/loop'], ['/trip'] and equals expected("anon", 3) whole.
  - asnState.test.ts "an activation whose expiresDate had passed when Apple signed it lands active until that
    expiresDate (R6)" - the same twelve rows; the whole entitlements table equals one active row with active_until =
    signedDate + offset, and GET /entitlement answers {status: inactive, active_until: null}.
  - tierMutants.mjs: four entries (asn-reversal-lapsed-open-ended = the survivor verbatim,
    asn-activation-lapsed-open-ended, asn-lapsed-before-signing-open-ended (`<`, killed only at -1),
    asn-lapsed-1ms-after-signing-open-ended (killed only at +1)); literal MIN_MUTATIONS 18 -> 22.
  GREEN on real code: `npx vitest run test/accountTier.test.ts test/asnState.test.ts -t "expiresDate had passed"` ->
  `Tests  24 passed | 71 skipped (95)`. RED by name (faster verification - only the touched rows):
  `node services/api/test/mutate/tierMutants.mjs --only=asn-reversal-lapsed-open-ended,asn-activation-lapsed-open-ended,
  asn-lapsed-before-signing-open-ended,asn-lapsed-1ms-after-signing-open-ended,asn-reversal-no-expiry` ->
  `baseline green tests=105`; `CAUGHT asn-reversal-no-expiry by "a REFUND_REVERSED whose expiresDate is exactly now
  leaves the caller anon; now + 1 ms is paid"`; `CAUGHT asn-reversal-lapsed-open-ended by "REFUND_REVERSED with
  expiresDate - signedDate = -1 ms, both before now, leaves the caller anon"`; `CAUGHT asn-activation-lapsed-open-ended
  by "SUBSCRIBED with expiresDate - signedDate = -1 ms, ..."`; `CAUGHT asn-lapsed-before-signing-open-ended by
  "SUBSCRIBED with expiresDate - signedDate = -1 ms, ..."`; `CAUGHT asn-lapsed-1ms-after-signing-open-ended by
  "SUBSCRIBED with expiresDate - signedDate = 1 ms, ..."`; `RESULT caught=5 missed=0 trap=0 of 5`, exit 0.
  `--prove-floor`: four arms REFUSED (0, 21 below 22, isochrone unmutated, new subject), real population quiet.
  wc -l: accountTier.test.ts 216, asnState.test.ts 243, tierMutants.mjs 167.
  RECORDED, NOT CHANGED (outside T-0272's acceptance): an ACTIVATES notification for a transaction with NO
  expiresDate (a non-subscription product) lands active_until NULL in shipped T-0267 code, pinned by asnState.test.ts
  "SUBSCRIBED for a transaction without expiresDate is active with no end"; scenic.pro is an auto-renewable
  subscription so Apple always sends expiresDate, but if a non-subscription product is ever sold this is open-ended
  paid. A follow-up should rule whether /asn refuses or ignores a productId outside the subscription allowlist.
- 2026-10-06T05:51:01Z **merged head re-measured** (agent/claude-opus-5, owner). `git fetch origin` and merged
  origin/main (b183c6e; no services/api change) into 8e06817 -> 2f2bc40. On the merged head: `npx vitest run` ->
  `Test Files  34 passed (34)`, `Tests  500 passed (500)` (476 + the 24 lapsed-at-signing rows);
  `python ops/lib/run-named-tests.py P-STORE-02` -> `NAMED P-STORE-02 passed=61/61`;
  `python ops/lib/run-named-tests.py P-COST-01` -> `NAMED P-COST-01 passed=22/22`; `bash ops/queue-check` ->
  `QUEUE OK (266 tasks)`. Acceptance 1 and 2 unchanged from the re-quote above; acceptance 3 now also carries the
  twelve-row lapsed-at-signing tables (accountTier.test.ts through ROUTES, asnState.test.ts by whole-table equality)
  and tierMutants.mjs at literal MIN_MUTATIONS = 22. MET. NOT DONE (R8) unchanged: no named-tests.json binding
  (outside touches).
- 2026-10-06T06:37:59Z **rv1-t0272 FAIL closed** (agent/claude-opus-5, owner; PR #164 at 04e548d). The finding:
  accountTier.ts falling back to `new URL(req.url).searchParams.get("account_token")` left the suite green, because
  the "every other client field" row is a BLACKLIST of five header spellings and always sends the bare path.
  RULED: the class is "the tier read from any carrier but the one header"; closed two ways, neither a list of bad
  spellings. (1) WHITELIST source guard `services/api/test/requestReadSites.test.ts`: every non-comment line under
  `src/**/*.ts` (import.meta.glob, so a new file is seen) that names `req` or `Request` or reads a request member
  (.headers .url .json .text .formData .arrayBuffer .blob .body .cf, URL, searchParams) is collected trimmed and
  compared by full equality, file by file, to the APPROVED sites (55 lines in 14 files); any new site fails naming
  its file and line. A second test pins that accountTier.ts's only request read is the ACCOUNT_TOKEN_HEADER line; a
  third shows the guard red in-test for a query, a body and an alternate-header read. Skipped lines are comment
  lines only (leading `//`, `/*`, `*/`, `* `) - so stripping comments cannot move it. (2) Behaviour table
  `services/api/test/tierCarriers.test.ts` through ROUTES["/plan"], device at the anon plan limit, an active
  entitlement for TOKEN: the token under 13 query names (each, and all at once), a URL fragment, a path suffix
  `/plan/<token>`, a path parameter `;account_token=`, and 42 generated header names (13 stems x {"", "x-",
  "x-scenic-"} plus six more, less the real header and x-scenic-device; each, and all at once), and every carrier at
  once - each answers EXACTLY the no-token drive (answer 429, quota state, entitlement reads 0, console lines) by
  full equality; the real header answers planOk 200 with 1 read. Body fields: /plan's key whitelist refuses an
  unknown key, so the 13 body names each answer the whole `{400, invalid_request, "the body carries \"<name>\",
  which /plan does not accept"}` with the quota untouched and 0 reads.
  rv1's mutant RED by name: against the OLD suite `accountTier.test.ts` alone it is `total=33 failed=0` (the
  finding reproduced); against `tierCarriers.test.ts` `failed=3 ['query ?account_token=', 'every query name at
  once', 'every carrier at once']`; the alt-header mutant `failed=3 ['header x-scenic-account-token-v2', 'every
  header name at once', 'every carrier at once']`. Population: tierMutants.mjs gains tier-query-fallback,
  tier-body-fallback (reads `req.clone().json()` when the body is unused - unreachable on /plan, so only the guard
  can see it), tier-alt-header-fallback; MIN_MUTATIONS 22 -> 25; TESTS += the two new files. Faster verification,
  only the new entries: `--only=tier-query-fallback,tier-body-fallback,tier-alt-header-fallback` ->
  `baseline green tests=184`; `CAUGHT tier-query-fallback by "the request sites under src are exactly the approved
  sites, file by file, line by line"` (same for tier-body-fallback and tier-alt-header-fallback); `RESULT caught=3
  missed=0 trap=0 of 3`. `--prove-vacuity` on the same three: `RESULT caught=0 missed=3`. `--prove-floor`: four arms
  REFUSED, real population quiet. wc -l: requestReadSites.test.ts 132, tierCarriers.test.ts 125.
- 2026-10-06T06:49:32Z **merged head re-measured** (agent/claude-opus-5, owner). `git fetch origin`, merged origin/main into
  e4c749c -> 455ece6 (queue-only change upstream: T-0275 claimed). On the merged head: `npx vitest run` ->
  `Test Files  36 passed (36)`, `Tests  579 passed (579)` (500 + 4 requestReadSites + 75 tierCarriers);
  `bash ops/queue-check` -> `QUEUE OK (266 tasks)`. rv1-t0272 BLOCKING closed; ready for re-review.
- 2026-10-06T07:25:11Z **rv2-t0272 FAIL closed** (agent/claude-opus-5, owner; PR #164 at 5f02dbe). The finding: the guard's
  COMMENT `/^(\/\/|\/\*|\*\/|\* |\*$)/` dropped every line beginning `/*`, `*/`, `* ` or `*` even with code after it,
  so `/* v1 */ { const alt = req.headers.get(ACCOUNT_TOKEN_HEADER.replace("account","purchase")); ... }` in
  accountTier.ts left 112/112 green and granted paid from x-scenic-purchase-token. RULED: fail closed - the guard
  drops ONLY lines that begin with `//` (LINE_COMMENT `/^\/\//`, per memory source-guards-fail-closed / PR #130);
  every other line naming the request is compared whole to APPROVED. That makes seven JSDoc lines under src sites,
  approved by full equality: appleMaps.ts (2), customModel.ts, hazards.ts, retrace.ts, ro.ts, roadTrip.ts (1 each)
  -> APPROVED is now 62 lines in 20 files. Seen-red rows added to the in-test guard: `/* x */ <read>`, `*/ <read>`,
  `* <read>`, `<read> /* fallback */`, and rv2's opening-block-comment line. Guard RED under the old filter (swapped
  back in the worktree, uncommitted): `x the request sites under src are exactly the approved sites` (`expected {
  ...(14) } to deeply equal { ...(20) }`), `x ... the guard seen red` (`expected [] to deeply equal [ Array(1) ]`),
  `Tests  2 failed | 2 passed (4)`; GREEN with LINE_COMMENT: `Tests  4 passed (4)`. Population: tierMutants.mjs gains
  tier-blockcomment-fallback (rv2's line completed to compile: `if (alt) return accountTier(new Request(req.url,
  { headers: { [ACCOUNT_TOKEN_HEADER]: alt } }), db, nowMs); }` inserted as the function's first line);
  MIN_MUTATIONS 25 -> 26. Faster verification, only the new entry: `--only=tier-blockcomment-fallback` ->
  `population mutations=26 (floor 26)`, `baseline green tests=184`, `CAUGHT tier-blockcomment-fallback by "the
  request sites under src are exactly the approved sites, file by file, line by line"`, `RESULT caught=1 missed=0
  trap=0 of 1`. wc -l: requestReadSites.test.ts 155, tierMutants.mjs 177.
- 2026-10-06T07:41:11Z **rv3-t0272 PASS** (agent/rv3-t0272, reviewer round 3, not the owner; PR #164 at 25d15ec).
  History: rv1-t0272 FAIL at 04e548d (a `new URL(req.url).searchParams.get("account_token")` fallback in
  accountTier.ts left the suite green; the other-client-field row was a blacklist of header spellings); rv2-t0272
  FAIL at 5f02dbe (the guard's COMMENT filter dropped any line beginning `/*`, `*/`, `* ` or `*` even with code after
  it; rv2's one-line `/* v1 */ { const alt = req.headers.get(...) ... }` left 112/112 green and granted paid from
  x-scenic-purchase-token). Round 3, touched rows only, review worktree `.worktrees/rv3-t0272` at
  origin/task/T-0272 == 25d15ec, `npm ci`, each mutant inserted after accountTier's signature line, full
  `npx vitest run`, file restored (byte-equal check true):
  - rv2's line, completed to compile (`... if (alt) return accountTier(new Request(req.url, { headers:
    { [ACCOUNT_TOKEN_HEADER]: alt } }), db, nowMs); }`) -> RED: `Tests 3 failed | 576 passed (579)`, by name
    "the request sites under src are exactly the approved sites, file by file, line by line", "the tier module
    reads the request once: the ACCOUNT_TOKEN_HEADER line", "a query, body or alternate-header read in the tier
    module is refused by its line (the guard seen red)".
  - reviewer's own, a `*`-leading continuation line inside a multi-line expression (`const purchased = 1` /
    `* Number(Boolean(req.headers.get(ACCOUNT_TOKEN_HEADER.replace("account", "purchase"))));` /
    `if (purchased) return "paid";`) -> RED: `Tests 3 failed | 576 passed (579)`, the same three names.
  - reviewer's own, a template literal (`` const via = `${req.headers.get(ACCOUNT_TOKEN_HEADER.replace("account",
    "purchase")) ?? ""}`; `` / `if (via) return "paid";`) -> RED: the same three names, 3 failed | 576 passed.
  RECORDED (not blocking): in all three the only catcher is the source-layer whitelist; no behavioral test fails
  (576 green), so a read that names no SITE token on any line (e.g. `arguments[0]["head" + "ers"]`) is outside what
  a lexical guard can see (inferred from SITE, not run). Adversarial obfuscation, recorded, not ruled a fail.
  Green: `npx vitest run test/requestReadSites.test.ts test/accountTier.test.ts test/tierCarriers.test.ts` ->
  `Test Files 3 passed (3)`, `Tests 112 passed (112)`. wc -l: requestReadSites.test.ts 155, tierMutants.mjs 177.
  `bash ops/queue-check` (bare) -> `QUEUE OK (266 tasks)`, exit 0. `gh pr checks 164` -> core pass 4m12s,
  pins-source-only pass 1m47s. Ancestry: `git merge-base --is-ancestor origin/main origin/task/T-0272` -> true
  (origin/main 8bf2709). Verdict PASS; queue/claimed/ -> queue/done/. Not merged by the reviewer.
