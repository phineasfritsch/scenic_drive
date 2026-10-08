---
id: T-0319
title: The /plan reroute wire - carry a RerouteRequest (remaining pins + same lambda) without sending more than one 2-dp coordinate (plan token + first remaining pin index); the Worker half of T-0317 R2
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T12:53:20Z
lease_expires_at: 2026-10-08T22:53:20Z
worktree: .worktrees/T-0319
branch: task/T-0319
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/mutate/plansheet_mutations.py, ops/mutate/plansheet_run.py, ops/lib/named-tests.json, ops/lib/check-safety-disclaimer-linked-digests.txt, Tests/Fixtures/t0251/, queue/]
pins_affected: [P-NAV-01, P-PRIV-05]
reviewer: agent/rv2-t0319
depends_on: [T-0317]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED FIRST (Log 2026-10-08T12:59:19Z, R1-R11) and committed before any code: the measurement of what /plan returns, where a token lives, its cost, TTL and the unknown-token fallback"
  - "Wire (R2, P-PRIV-05): /plan's body whitelist gains ONE optional key `reroute` = {token, first_pin}, both required; token matches PLAN_TOKEN (lowercase 8-4-4-4-12 hex), first_pin an integer in [0, MAX_WAYPOINTS=9]. Table-tested at every bound in services/api/test/planReroute.test.ts `every bound of reroute.token and reroute.first_pin` (first_pin -1/0/9/10/1.5/\"1\"/null/absent; token 35/36/37 chars, uppercase, non-hex, a coordinate-shaped value; an extra key inside reroute; a coordinate under any other key) - each refused 400 with zero store reads and zero upstream calls, each accepted one reaching the router"
  - "P-PRIV-05 on the reroute path: `P-PRIV-05: a reroute sends upstream only the one 2-dp origin plus the pins the Worker remembered` - the whole upstream request list equals its recomputation (fastest O->D, then car_scenic through [origin, ...pins.slice(first_pin), destination] at the remembered lambda's buildCustomModel); the test is listed under P-PRIV-05 in ops/lib/named-tests.json"
  - "Fallback (R5), a cross product of variants: unknown token, store unbound, store read throws, a record for another device, another place, first_pin > stored pin count, a malformed record - each answers EXACTLY the fresh plan's answer (whole-answer equality against a plain /plan of the same origin, place and budget) in `an unusable token answers exactly the fresh plan`"
  - "Ceiling (R7): `the budget ceiling holds on a reroute` - a pinned route at fastest + budget is returned (exact bound), one second over falls back to the fresh plan inside the SAME one reservation; every 200 has eta_s <= fastest_eta_s + budget_s"
  - "P-COST-01 (R8): `a reroute reserves one plan before its first upstream call` - events start [reserve, fetch...], one reservation of PLAN_UPSTREAM_COST, the worst case (pinned breach + fresh) <= 12 calls; KILL=1 with a reroute body is 503 with zero store reads, zero reservations, zero calls (`the kill switch covers a reroute`)"
  - "Token (R3/R6): every 200 carries plan_token; `every answer remembers its pins and lambda under plan_token for 43200 s` - the KV put's key, whole value and expirationTtl equal their recomputation; an unbound store or a throwing put answers plan_token null with the plan intact; planRecorded's ruled key list gains plan_token"
  - "Device (R9): Tests/ScenicAPIClientTests/PlanRerouteWireTests.swift - `a reroute leaves as ONE 2-dp origin, the place, the budget and {token, first_pin}, whole` (exact PlanHTTPRequest equality, x-scenic-device header), `the reroute origin is rounded on the device at every bound`, `a reroute is refused on the device with zero requests` (token grammar, first pin -1/10, budget, no install id), `plan_token decodes, and absent or null decodes nil`"
  - "Populations: services/api/test/mutate/planMutants.mjs gains reroute/token entries (subject src/planToken.ts, src/reroutePlanner.ts), each MISSED before the tests and CAUGHT by name after, quoted in the Log; ops/mutate/plansheet_mutations.py gains entries 38+ on PlanRequestBody/PlanClient/PlanResponse with PlanRerouteWireTests in TEST_FILES, run once CAUGHT"
  - "Gates on the merged head: the touched vitest files, swift test --filter ScenicAPIClientTests, bash ops/lib/check-safety-disclaimer (digest rows re-approved), check-mutate-population, check-line-cap, check-pins-yaml, queue-check"
---
## Brief

Filed by agent/claude-opus-5 from T-0317 ruling R2. ScenicKit's DriveSession (T-0317) emits a device-side
RerouteRequest {origin, remainingWaypoints, firstRemainingWaypoint, destination, lambda}. /plan cannot carry it:
services/api/src/planRequest.ts BODY_KEYS are origin, destination, budget_minutes, departs_at, vehicle (measured
2026-10-08), and CLAUDE.md forbids more than one coordinate per user action or more than 2 dp, so sending the pins
as coordinates is not an option. MEASURE FIRST (what /plan returns today that could identify a plan - nothing is a
token yet), then rule an encoding - e.g. a plan token the Worker remembers (with the pins and lambda it chose) plus
`firstRemainingWaypoint` and the one 2-dp origin - whitelist it (P-PRIV-05), and make ScenicAPIClient send it.
Acceptance is written by the claimer after that measurement (CLAUDE.md: a predicate over an unmeasured population is
a measurement task first).

## Log
- 2026-10-08 filed by agent/claude-opus-5 (T-0317 R2) through ops/new-task; the allocator answered T-9902 (a stray
  ref outside origin/main holds T-9901), renumbered to T-0318, the next id after origin/main's T-0317.
- 2026-10-08T12:53:20Z claimed by agent/claude-opus-5; lease until 2026-10-08T22:53:20Z
- 2026-10-08T12:59:19Z MEASURED at 2f6e7579, then RULED (agent/claude-opus-5), before any code:
  * Measured /plan's 200 body: exactly the 12 keys planRecorded.test.ts R8 lists (apple_maps_url, budget_s,
    ceiling_s, eta_is_estimate, eta_s, evaluations, fastest_eta_s, hazards, lambda, route, used_budget, waypoints).
    Nothing identifies a plan. The device holds waypoints and lambda but may not send them (>1 coordinate).
  * Measured storage: no KV plan cache exists for /plan. reachCache.ts (/isochrone) is the Cache API -
    caches.default, PER COLO, so a reroute served by another colo would miss. KV namespaces in Env (CLOSURES,
    CONFIG, KILL_SWITCH) are optional and NOT bound in wrangler.jsonc - the owner creates them. D1 (DB) is bound
    but has no TTL (a migration plus a sweeper).
  * Measured cost: quota.ts MAX_MONTHLY_UPSTREAM_CALLS 250,000 / PLAN_UPSTREAM_COST 12 = at most 20,833 reserved
    plans a month (a reroute reserves as one plan), so at most 20,833 KV writes and 20,833 reads a month (~694 a
    day). Workers Paid includes 1M KV writes and 10M reads a month: $0 marginal. The free tier's 1,000 writes/day is
    above the average; a burst over it fails the put, and R6 keeps the plan. A value is <= ~700 bytes (9 pins).
  * Measured: IdentityHeaders.swift does not exist at 2f6e7579 or on origin/main (git ls-tree | grep -i: empty);
    PlanClient sends x-scenic-device itself.
  * R1 the reroute rides /plan itself - no new route, so ROUTES, the kill-switch sweep, requestReadSites' route
    rows and P-COST-01's route count are unchanged (memory parallel-worker-prs-conflict).
  * R2 the body whitelist gains one optional key `reroute` = {token, first_pin}; token = crypto.randomUUID()'s
    lowercase 8-4-4-4-12 hex grammar (PLAN_TOKEN), first_pin an integer in [0, MAX_WAYPOINTS = 9]. The one
    coordinate stays `origin` at 2 dp; remainingWaypoints, the destination coordinate and lambda never leave the
    device - the Worker remembered them.
  * R3 a new optional KV binding PLANS (Env.PLANS), not bound in wrangler.jsonc. OWNER DEPLOY STEP:
    `wrangler kv namespace create PLANS` and bind it as PLANS. Key `plan:<token>`, value JSON {device, place, pins,
    lambda}, expirationTtl 43,200 s (12 h: the longest drive is a fastest of hours plus a 180-min budget).
    Not the Cache API (per colo), not D1 (no TTL). KV's eventual consistency (up to 60 s across colos) lands in R5.
  * R4 cost as measured above; no new upstream call class.
  * R5 an UNUSABLE token - unknown or expired, store unbound, store read throws, a record whose device is not the
    caller's identity, whose place is not the request's, whose pin count is below first_pin, or a malformed
    record - answers EXACTLY the fresh plan: the one origin to the place with the same budget, plain planScenic.
    Not an error: an off-route driver asking for a scenic way to the same place is what /plan already answers.
  * R6 every 200 carries `plan_token`: a fresh token stored with the waypoints and lambda that answer carries;
    null when PLANS is unbound or the put throws (the plan was paid for and is never lost to the store).
  * R7 with a usable record: fastest car_fast origin->destination; ceiling = fastest + budget_minutes*60; one
    car_scenic request through [origin, ...pins.slice(first_pin), destination] at buildCustomModel(lambda,
    closures), the closures guard with one re-request through the same points. Time <= ceiling -> that answer
    (lambda the remembered one, evaluations 1, used_budget by lambdaSearch's rule, waypoints = decisionPoints of
    the new line so DriveSession.rerouteArrived finds them on it). No Jaccard guard: the drive was ruled different
    when planned, and its own continuation is meant to overlap it. Over the ceiling -> the fresh plan inside the
    SAME reservation: 3 + 8 = 11 <= PLAN_UPSTREAM_COST 12. The ceiling holds on every path.
  * R8 quota: guardedPlan reserves before the first router call on both paths; the store read precedes the
    reservation and is not an upstream call; KILL=1 answers before the body is read, so a reroute is covered.
  * R9 device: PlanClient.reroute(_ RerouteRequest, token:, place:, budgetMinutes:, vehicle:) rounds the origin
    to 2 dp ON THE DEVICE ((v*100).rounded()/100, PlanSheet's rounding), refuses a token outside PLAN_TOKEN
    (.rerouteTokenMalformed) or a firstRemainingWaypoint outside 0...9 (.firstPinOutOfRange) with zero requests,
    and sends plan()'s headers. PlanResponse gains planToken: String? (absent or null -> nil).
  * R10 pins: the reroute privacy test joins P-PRIV-05's named list; P-NAV-01 is the device half (T-0317) and is
    not re-bound here.
  * R11 populations: Worker mutants in planMutants.mjs (it gains `--only` to run the new ids alone); Swift mutants
    in plansheet_mutations.py, which already mutates PlanRequestBody and PlanClient.
- 2026-10-08T13:19:02Z RED FIRST (Worker), with src/planToken.ts present but nothing wired: `npx vitest run
  test/planReroute.test.ts` -> `Tests 8 failed | 1 passed (9)`, the eight by name (every bound of reroute.token and
  reroute.first_pin; P-PRIV-05: a reroute sends upstream only ...; an unusable token answers exactly the fresh plan;
  the first remaining pin may be the stored count ...; the budget ceiling holds on a reroute; a reroute reserves one
  plan before its first upstream call; every answer remembers ... 43200 s; an unbound store or a failed write ...).
  The one green before wiring is `the kill switch covers a reroute`: KILL is read before the body, so it is a
  regression guard, not a new behaviour. GREEN after wiring plan.ts/planRequest.ts/reroutePlanner.ts: 9/9.
  * R12 (ruled while wiring) every 200 now ends `"plan_token":null` with PLANS unbound, so the two recorded wire
    fixtures Tests/Fixtures/t0251/200-plan(.json, -hazards.json) the Swift client decodes gain that one key
    (touches += Tests/Fixtures/t0251/); planWire.test.ts reads them byte for byte. configAnswerPath's approved
    index.ts sha256 is re-approved (5dbcb7fa.. -> 7b50d6d4..: the Env gains PLANS). requestReadSites' approved
    plan.ts line is now `const who = await deps.identify(req);` (the same spelling loop/trip already use).
  * Whole Worker suite after: `Tests 2191 passed` less the 3 above before their fix; after: all green on the four
    touched files (28/28). run-named-tests P-PRIV-05: passed=53/54 - the one red is
    PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail `MISSING - no test of this name ran`, a Swift
    PlaceStore test this branch does not touch.
- 2026-10-08T13:49:33Z RED FIRST (device): PlanClient.reroute first landed as a stub forwarding to plan() with the raw
  fix (what a caller could do before this task) - `swift test --filter PlanRerouteWireTests` -> 4/4 failed by name
  (a reroute leaves as ONE 2-dp origin ... whole; the reroute origin is rounded on the device at every bound; a
  reroute is refused on the device with zero requests; plan_token decodes, and absent or null decodes nil). Real
  sender: 4/4 green, and PlanClient|PlanResponse|PlanVehicle|PlanSheetGate|SavedDraft suites green (45 XCTest + 16
  Swift Testing). Digest rows re-approved for PlanClient, PlanRequestBody, PlanResponse, PlanRefusal;
  `bash ops/lib/check-safety-disclaimer` exit 0.
  * R13 (ruled while running the population): services/api/test/mutate/planMutants.mjs was STALE at 2f6e7579 -
    `planner-other-model` anchored `SCENIC_PROFILE, buildCustomModel(lambda, null)` (0 occurrences at base: the code
    passes `closures`) and the EQUIVALENT `planner-ceiling-guard` anchored `if (!(eta <= ceiling))` (the code says
    `firstEta`), so the population refused to run on main. Both re-anchored on code; the witness is unchanged.
    The runner gains `--only=<ids>` and `--without=<test file>` so the new entries run alone, before and after.
  * WORKER POPULATION (MIN_MUTATIONS 43 -> 60, SUBJECTS += src/planToken.ts, src/reroutePlanner.ts, TESTS +=
    test/planReroute.test.ts): `--only=<the 17 new + planner-other-model> --without=test/planReroute.test.ts` ->
    `RESULT caught=1 missed=17 trap=0 of 18` (the 1 is the re-anchored planner-other-model, by the ceiling sweep);
    with the reroute tests -> `RESULT caught=18 missed=0 trap=0 of 18`, each by name: token-pin-upper/-lower/
    -fraction, token-grammar-case/-long and reroute-other-lambda by `every bound of reroute.token and
    reroute.first_pin`; token-ttl-day and reroute-token-dropped by `every answer remembers its pins and lambda under
    plan_token for 43200 s`; token-failed-write-named by `an unbound store or a failed write ...`;
    token-lambda-range, reroute-foreign-device, reroute-other-place by `an unusable token answers exactly the fresh
    plan`; reroute-pin-count by `the first remaining pin may be the stored count ...`; reroute-pin-skipped and
    reroute-evaluations by `P-PRIV-05: a reroute sends upstream only ...`; reroute-ceiling-plus and
    reroute-used-strict by `the budget ceiling holds on a reroute`.
- 2026-10-08T14:31:46Z SWIFT POPULATION (MIN_MUTATIONS 37 -> 48, MIN_TEST_FILES 4 -> 5): `plansheet.py --only 38..48`
  with FILTER not yet naming PlanRerouteWireTests -> `caught 0 of 11 (MISSED 11)`; FILTER += PlanRerouteWireTests
  (324b5ca9) -> `caught by the test that names it: 11 of 11 (wrong killer 0, trapped 0, compile-only 0, MISSED 0)`.
- 2026-10-08T14:31:46Z MERGED origin/main (1f55e15d) LAST, into 7152aea3. T-0315 landed IdentityHeaders.swift and
  PlanClient's accountToken: the merged `send` builds IdentityHeaders.json(device:account:), so reroute() carries
  the same header set as plan(); PlanRerouteWireTests now builds PlanClient(..., accountToken:) and its whole-request
  case adds a paid row (x-scenic-account-token lowercased). Digest conflict on PlanClient.swift resolved by
  recomputing the four rows this branch owns. services/api is unchanged on main since 2f6e7579.
  ACCEPTANCE RE-RUN ON THE MERGED HEAD:
  1 ruling: 89b0f6b8 (Log R1-R11) precedes the first code commit ac239f38. PASS
  2-7 Worker: `npx vitest run` the ten touched/enumerating files (planReroute, planRecorded, planPrivacy, planCost,
    planCeiling, planWire, requestReadSites, configAnswerPath, killSwitchRoutes, sharedEnvWorker) -> `Test Files 10
    passed (10) / Tests 78 passed (78)`. Whole suite: `Tests 1 failed | 2190 passed (2191)` - the one a 5015 ms
    timeout in configAnswerPath (`loading the shipped worker leaves every global ...`) on the loaded box; alone ->
    `Tests 3 passed (3)`. PASS
  8 device: `swift test --filter ScenicAPIClientTests` -> `Test run with 76 tests in 18 suites passed`, XCTest
    `Executed 46 tests, with 0 failures`. PASS
  9 populations: Worker 18/18 CAUGHT (above), Swift 11/11 CAUGHT on the merged head (re-run after the merge). PASS
  10 gates: bash ops/lib/check-safety-disclaimer exit 0; check-mutate-population `P-PROC-06: every added module is
    covered or allowlisted; the floor of 130 holds`; check-line-cap `P-SRC-02: 460 Swift files ... none over 300
    lines`; check-pins-yaml `PINS-YAML ok pins=46 fields=371`; queue-check `QUEUE OK (315 tasks)`;
    run-named-tests P-PRIV-05 `passed=53/54` - the one red is PlaceStoreTests.UserStorePrivacyTests/
    noColumnNamesAPlaceOrATrail `MISSING - no test of this name ran`, a PlaceStore test this branch does not touch
    (git diff 2f6e7579..HEAD -- Tests/PlaceStoreTests Sources/PlaceStore is empty), the same single red as this
    session's first run of the pin. NOT re-run at 2f6e7579 itself. PASS for every reroute row.
  PR #209 opened; CI on its first run (7152aea3): core pass, pins-source-only pass.
  OWNER DEPLOY STEP (R3): `wrangler kv namespace create PLANS` and bind it as PLANS; until then every answer's
  plan_token is null and every reroute is the fresh plan.
- 2026-10-08T15:23:40Z FIX ROUND 1 RULINGS (rv1-t0319 FAIL, PR #209 at fb7d041f), before any code:
  B1 (reroute re-request over the ceiling returned) and B2 (closures never sent on the reroute's first car_scenic
  request) are one CLASS: the reroute path was outside closuresCrossing's cross product. Closed by making the reroute
  a fourth entry of ROUTE_NAMES ("/plan reroute": handler ROUTES["/plan"], PLANS bound to a KV holding a usable
  token for the request's device and place, BASE 1 car_scenic request before any re-request), so every row the
  other paths have - set x shape x router, the re-request-is-the-request row - is generated for it, and a path added
  to ROUTE_NAMES cannot skip them. The guard rows become a function of the path list: every path whose handler is
  /plan gets "the re-request over the ceiling", "one second over the ceiling" and "exactly at the ceiling (returned,
  the ceiling is inclusive)". RULING on the review's "re-request null": the retry answers null only through its own
  ceiling guard (reroutePlanner has no other null arm), so the over/one-over rows ARE the null rows; a router error
  on the re-request propagates the same way on every path and has no reroute branch. One whole-list row: a reroute
  under X alone sends exactly [car_fast origin->destination, car_scenic origin->pins->destination carrying
  buildCustomModel(lambda, X)] - full equality of every request body.
  Population: planMutants.mjs TESTS += closuresCrossing.test.ts; entries reroute-retry-over-ceiling (B1),
  reroute-first-closures-dropped (B2) and reroute-retry-ceiling-strict (`<= ceiling ? again` -> `< ceiling ? again`),
  each run --only MISSED against fb7d041f's tests, then CAUGHT by name.
  P-PRIV-04 (recordable): a sweep needs PLANS keys a deletion can enumerate (device-prefixed keys, so recall must
  rebuild the key from the caller), list()+delete() on the KV interface, and an edit to src/account.ts, whose whole
  bytes are SHA-pinned by identityVerifierPin.test.ts - well over 40 lines and a second gate re-approval. RULED: the
  12 h TTL (PLAN_TOKEN_TTL_SECONDS) plus the privacy notice is this task's policy; the sweep is filed as T-0326.
- 2026-10-08T15:32:07Z FIX ROUND 1 LANDED. closuresCrossing.test.ts: "/plan reroute" is a fourth ROUTE_NAMES entry (HANDLER maps it
  to ROUTES["/plan"], PLANS bound to a KV remembering TOKEN for DEVICE and la:topanga, BASE 1); the guard ROWS are
  generated over PLAN_PATHS (every path whose handler is /plan): over the ceiling, one second over; a new describe
  holds "exactly at the ceiling" (returned) for each; a whole-list row holds the reroute's upstream requests under
  X alone. Rig state (sent, router, shape) resets in beforeEach. `wc -l test/closuresCrossing.test.ts` -> 300.
  `npx vitest run test/closuresCrossing.test.ts` -> `Tests 150 passed (150)` (fb7d041f had 110 by count: 3 x 30 + 9 + 3 + 4 + 4).
  RED at fb7d041f's tests (planMutants.mjs entries added, closuresCrossing.test.ts in TESTS, test unchanged):
  `--only=reroute-retry-over-ceiling,reroute-retry-ceiling-strict,reroute-first-closures-dropped` ->
  `MISSED` x3, `RESULT caught=0 missed=3 trap=0 of 3`.
  GREEN with the new rows (one transient baseline refusal with no named failure on the loaded box; the nine-file
  TESTS list alone -> `Tests 212 passed (212)`; re-run): `baseline green tests=212`;
  `CAUGHT reroute-retry-over-ceiling by "/plan reroute, the re-request over the ceiling: the crossing path is
  returned, crosses names X, one re-request made"`; `CAUGHT reroute-retry-ceiling-strict by "/plan reroute, the
  re-request exactly at the ceiling: the clear path is returned, one re-request made"`; `CAUGHT
  reroute-first-closures-dropped by "/plan reroute, X alone, clear path, router honours: requests, areas, the
  returned path and the hazard equal the row's"`; `RESULT caught=3 missed=0 trap=0 of 3`. Population 60 -> 63.
  NOT DONE: the new reroute rows are not added to P-SAFE-08's by-name list in named-tests.json (that would change the
  row's bound count in PINS.yaml, outside touches); they are held by the population above.
  P-PRIV-04 follow-up filed: queue/backlog/T-0326-account-deletion-sweeps-plan-tokens.md (T-0325 is the highest id
  on main and every origin/task/* branch).
- 2026-10-08T15:38:07Z MERGED origin/main (8d39f215) LAST into 0dbc8f09 (merge message amended to carry the attribution lines);
  `git merge-base --is-ancestor origin/main HEAD` 0; main changed nothing under services/api. ON THE MERGED HEAD:
  `npx vitest run` closuresCrossing, planReroute, planRecorded, planPrivacy, planCost, planCeiling, planWire,
  requestReadSites, killSwitchRoutes, sharedEnvWorker, configAnswerPath -> `Tests 1 failed | 227 passed (228)`, the
  one the 5021 ms configAnswerPath global-intrinsics timeout on the loaded box; alone -> `Tests 3 passed (3)`.
  bash ops/lib/check-safety-disclaimer exit 0; check-mutate-population `P-PROC-06: every added module is covered or
  allowlisted; the floor of 137 holds`; check-pins-yaml `PINS-YAML ok pins=48 fields=387`; queue-check `QUEUE OK
  (317 tasks)`; run-named-tests P-SAFE-08 `passed=833/833` (the preserved "/plan, the re-request over the ceiling"
  name still binds). Mutants: only the touched rows re-run (faster-verification rule): 3/3 CAUGHT above.
- 2026-10-08T15:48:43Z REVIEW round 2 PASS by agent/rv2-t0319 (not the owner) at origin/task/T-0319 = f1c37f75, in a
  detached worktree .worktrees/rv2-t0319. rv1 mutants re-applied through the population driver:
  `node services/api/test/mutate/planMutants.mjs --only=reroute-retry-over-ceiling,reroute-first-closures-dropped`
  -> `baseline green tests=212`; `CAUGHT reroute-retry-over-ceiling by "/plan reroute, the re-request over the
  ceiling: the crossing path is returned, crosses names X, one re-request made"`; `CAUGHT
  reroute-first-closures-dropped by "/plan reroute, X alone, clear path, router honours: requests, areas, the
  returned path and the hazard equal the row's"`; `RESULT caught=2 missed=0 trap=0 of 2` (B1, B2 closed).
  Own mutant C (outside the population): reroutePlanner.ts re-request `buildCustomModel(lambda, swapped))` ->
  `buildCustomModel(lambda, closures))` -> closuresCrossing + planReroute RED by name, 12 failed, among them
  "/plan reroute, the fixture, through path, router honours: the re-request's whole body is the first request's at
  the answer's lambda, areas swapped" and "/plan reroute, the re-request exactly at the ceiling: the clear path is
  returned, one re-request made"; restored, tree clean. `gh pr checks 209`: core pass 5m12s, pins-source-only pass
  2m4s. check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the floor of 137 holds`
  exit 0; queue-check `QUEUE OK (317 tasks)` exit 0; closuresCrossing.test.ts 300 lines; `git merge-base
  --is-ancestor origin/main origin/task/T-0319` exit 0 (main e158ddbc). Recordable: the new reroute rows are not in
  P-SAFE-08's by-name list (held by the three population entries); P-PRIV-04 PLANS sweep is T-0326 (rows live up
  to 43200 s after deletion); owner must create and bind the PLANS KV namespace.
