---
id: T-0319
title: The /plan reroute wire - carry a RerouteRequest (remaining pins + same lambda) without sending more than one 2-dp coordinate (plan token + first remaining pin index); the Worker half of T-0317 R2
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T12:53:20Z
lease_expires_at: 2026-10-08T22:53:20Z
worktree: .worktrees/T-0319
branch: task/T-0319
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/mutate/plansheet_mutations.py, ops/lib/named-tests.json, ops/lib/check-safety-disclaimer-linked-digests.txt, Tests/Fixtures/t0251/, queue/]
pins_affected: [P-NAV-01, P-PRIV-05]
reviewer: null
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
