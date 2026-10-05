---
id: T-0248
title: the Worker serves POST /plan - one request from the app becomes a fastest call plus the lambda budget search against the router, returning the scenic route, ETA vs fastest, hazards and the Apple Maps URL; quota first, kill switch honoured, privacy invariant held
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T05:09:51Z
lease_expires_at: 2026-10-05T15:09:51Z
worktree: .worktrees/T-0248
branch: task/T-0248
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-04, P-SAFE-01]
reviewer: agent/rv1-t-0248
depends_on: [T-0244]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, from the plan's Problem A and the product invariants: the request shape (origin/destination, budget minutes, departs-at), and how it holds 'the server never receives more than one coordinate per user action, never more than 2 decimal places' (e.g. origin rounded to 2 dp on the device and the destination as a corpus place id, or a ruled exception argued against the plan) - a Worker test refuses any body carrying a second coordinate or a coordinate with more than 2 decimals"
  - "the handler decrements the quota BEFORE any upstream call and KILL=1 returns 503 with zero upstream calls (P-COST-01, a test with the counting fake for /plan); at most 12 upstream requests per plan (P-COST-04); the custom model sent upstream is buildCustomModel's (the T-0231 seam - a request model touching road_access/surface is never sent, P-SAFE-01)"
  - "the budget search is a port of ScenicKit LambdaSearch with the ceiling enforced on the returned route's real ETA (P-SAFE-04): a recorded-router test (fixtures from Tests/Fixtures/t0221/ or t0182, replayed by the counting fake) returns for Santa Monica -> Topanga +25 the SAME route, ETA and Apple Maps URL that 'ops/plan' prints for that recording - EXACT equality of the URL and ETA, not property checks"
  - "the response carries route geometry, ETA, fastest ETA, the estimate badge flag (no traffic data), hazards and the Apple Maps URL (<= 9 waypoints); vitest count quoted; the mutation population for the new module (ops/mutate/ or a vitest-driven equivalent - rule which) with a literal floor"
---
## Brief

Milestone survey (2026-10-04): the Worker serves only /__health /__version /__ro, so nothing in the app can plan a
live route. This is the first endpoint the app needs (M3 exit). /loop /surprise /trip follow the same shape later.

## Log
- 2026-10-05T05:06:53Z filed by agent/claude-opus-5 (orchestrator) from the milestone survey.
- 2026-10-05T05:09:51Z claimed by agent/claude-opus-5; lease until 2026-10-05T15:09:51Z
- 2026-10-05T05:24:32Z RULINGS before code (agent/claude-opus-5). Read: services/api/src/*, test/*, LambdaSearch.swift,
  Sources/ScenicKit/Plan/*, Sources/ScenicPlanCLI/*, Handoff/AppleMapsDirections.swift, Tests/Fixtures/t0221/,
  plan Problem A (:113-121) and :189 / P-PRIV-05 / P-COST-04 rows.
  R1 REQUEST SHAPE. `POST /plan` JSON body, a WHITELIST of exactly these keys, any other key refused 400:
     `{ "origin": {"lat": n, "lon": n}, "destination": {"place": "<corpus place id>"}, "budget_minutes": n,
        "departs_at"?: "<ISO-8601 UTC, ...Z>" }`. origin has exactly the keys lat/lon; destination exactly `place`
     (a non-empty string <= 128 chars of [A-Za-z0-9:._-]). budget_minutes finite, 0 <= B <= 180 (the CLI takes any
     non-negative number; the server bounds it because B is the user's ceiling and 3 h of extra time is not a drive).
     departs_at is validated and accepted but does not change routing yet: plan step 5 says it shifts the hour-of-week
     ratio and the twilight math, both of which are TrafficProvider / device work, not this endpoint's.
  R2 PRIVACY (plan :189 "server never sees >1 coordinate per action, never >2 decimals"). The ONE coordinate is the
     origin, rounded to 2 dp ON THE DEVICE; the Worker REFUSES (400, zero upstream calls) an origin whose lat or lon
     is not exactly representable at 2 dp (`Number(x.toFixed(2)) !== x`), and refuses any second coordinate by the
     whitelist: `destination` with lat/lon, a `waypoints`/`via` key, a coordinate nested anywhere else is an unknown
     key and is refused. The destination is a corpus PLACE ID (public data, not the user's position) resolved by an
     injected `resolvePlace`; unknown id -> 404 with zero upstream calls. Consequence ruled, not hidden: the Worker
     routes from the 2-dp origin, so the Apple Maps URL's `source` is that 2-dp point (5-dp spelled, e.g.
     34.02000,-118.49000). Dropping `source` so Apple Maps starts from the device's own position is the app's
     handoff decision, not this endpoint's; recorded as open in the PR, not done here.
  R3 THE EQUALITY TARGET. The T-0221 literal (source=34.01950,-118.49120) cannot be what /plan returns: 34.0195 has 4
     dp and R2 refuses it. The test's target is `ops/plan 34.02,-118.49 34.0676,-118.5957 25 --recorded
     Tests/Fixtures/t0221/santa-monica-topanga` - the same recording, the 2-dp origin the device would send, and
     Topanga's coordinate as the test's place resolver answers it. Its printed URL / LAMBDA / ETA lines are quoted
     in this Log when the run lands and typed into the test as literals (not recomputed by the module under test).
     RecordedRouteSource ignores coordinates, so route, lambda and ETA must also equal the T-0221 literal's.
  R4 QUOTA / KILL (P-COST-01). /plan reaches the router ONLY through `guardedPlan` (one door). Order in the handler:
     KILL=1 (env.KILL === "1") -> 503 `planning_paused` before anything else, zero upstream calls, no reservation;
     body validation (400) and place resolution (404) next - neither is an upstream call and neither spends a plan;
     then guardedPlan reserves BEFORE the first router request. quota_exhausted -> 429 with resets_at;
     upstream_paused / invalid_state -> 503. PRODUCTION WIRING: the Worker has no Durable Object counters, no router
     URL and no place table yet, so the shipped ROUTES["/plan"] builds its deps from env and, with any of them
     missing, answers 503 `planning_unavailable` with zero upstream calls (fail closed). Wiring DO counters,
     ROUTER_URL and the corpus place table is follow-up work, named in the PR.
  R5 P-COST-04. Requests per plan = 1 fastest + LambdaSearch's maxEvaluations (6, the Swift default) = 7 <= 12, and
     guardedPlan's PLAN_UPSTREAM_COST cap refuses a 13th before it is made. Calls are sequential (1 in flight <= 2).
     The recorded-router test asserts the exact count (7) and max in-flight 1 with the counting fake.
  R6 THE MODEL (P-SAFE-01). Every scenic request's custom_model is `buildCustomModel(lambda, null)` (closures: null -
     no KV feed exists yet) and passes `rejectCustomModel` immediately before the call; the fastest request carries
     no model. A client body carrying `custom_model` is an unknown key under R1 -> 400, so a request-supplied model is
     never forwarded. Per plan :120 and customModel.ts's own note, the Worker adds `details` naming surface and
     road_access AFTER the gate (the gate reads the model, not the details list) - they feed R8's hazards.
  R7 THE SEARCH (P-SAFE-04). src/lambdaSearch.ts is a line-for-line port of LambdaSearch.search (bracket [0,8],
     tolerance 0.05, maxEvaluations 6, minBudgetUse 0.5, the longer-then-larger-lambda tie rule, only measured
     feasible candidates eligible, pairwise monotonicity flag). The planner keeps every measured route keyed by
     formatMultiplier(lambda) (ScenicPlanner.key) and re-checks the CEILING on the chosen route's own `time`, and
     the Jaccard overlap < 0.6 (RouteDifference) - the same two meta-test guards as ScenicPlanner. Waypoints are a
     port of PlanTable + PlanWaypoints.decisionPoints (haversine, R = 6371008.8 m, <= 9), the URL a port of
     AppleMapsDirections (5 dp by integer arithmetic, source/destination/waypoint.../mode=driving).
  R8 RESPONSE. `{ route: {coordinates [[lon,lat]...], distance_m}, eta_s, fastest_eta_s, ceiling_s, budget_s, lambda,
     evaluations, eta_is_estimate: true, hazards: [...], waypoints: [{lat,lon}...], apple_maps_url }`.
     eta_is_estimate is ALWAYS true from the server: learned speeds never leave the device (plan :189), so the
     >= 5-sample rule can only clear the badge on the device. hazards = the chosen route's `surface` runs whose value
     is not in {asphalt, concrete, paved, missing} and `road_access` runs not in {yes, missing}, each as
     {kind, value, from_index, to_index}; [] when the router did not report those details (the t0221 recordings
     carry only scenic_score/road_class/osm_way_id, so hazards there are []). Failures: no feasible lambda / router
     refusal -> 502 `no_route`; overlap >= 0.6 -> 422 `no_scenic_alternative`; a ceiling breach is never returned
     (500 `ceiling_breached`).
  R9 MUTATION POPULATION. touches: is services/api/ only and check-mutate-population.py scans Sources/ and
     services/etl/etl/ only, so the population is the vitest-driven equivalent: services/api/test/mutate/
     planMutants.mjs (node, outside vitest's *.test.ts include) with a literal MIN_MUTATIONS floor; a mutant is
     CAUGHT only when vitest's JSON report names a failed test, a run with no named failure is a TRAP; it also has
     --prove-vacuity (empty suites -> every mutant MISSED) and --prove-floor.
- 2026-10-05T05:30:08Z R3 target measured (agent/claude-opus-5): `SCENIC_PLAN_SCRATCH=.build/t0248-plan bash ops/plan
  34.02,-118.49 34.0676,-118.5957 25 --recorded Tests/Fixtures/t0221/santa-monica-topanga` exit 0 printed:
    PLAN origin=34.02000,-118.49000 destination=34.06760,-118.59570 budget=25m00s
    LAMBDA 7.75 evaluations=6 used-budget=false monotonicity-violated=false
    ETA fastest=20m14s returned=22m26s ceiling=45m14s distance=20358.6m
    OVERLAP jaccard=0.453 required<0.600
    TABLE rows=86 ... WAYPOINTS 9 of max 9
    URL https://maps.apple.com/directions?source=34.02000,-118.49000&destination=34.06760,-118.59570&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&mode=driving
  The nine waypoints, LAMBDA and ETA lines equal the T-0221 literal (PlanCLILARecordingTests); only `source` differs (R2/R3).
- 2026-10-05T05:38:46Z RED by name (agent/claude-opus-5): `cd services/api && npx vitest run` against stub src/plan.ts, lambdaSearch.ts,
  appleMaps.ts (and ROUTES without /plan): tests 176 passed 127 failed 49, every failure a new named test in
  appleMaps(4) lambdaSearch(9) planCeiling(9 of 10) planCost(10) planPrivacy(14) planRecorded(3). The one new pass,
  planCeiling "asks the router for the surface and road_access details", passed VACUOUSLY over an empty h.sent; it
  now also asserts h.sent has length 7 (red against the stub by construction).
- 2026-10-05T05:59:18Z GREEN (agent/claude-opus-5): src/plan.ts (handler), planRequest.ts, lambdaSearch.ts, scenicPlanner.ts,
  routePath.ts, planWaypoints.ts, appleMaps.ts, hazards.ts, latLon.ts; ROUTES["/plan"] wired fail-closed.
  `cd services/api && npx vitest run`: Test Files 13 passed (13), Tests 176 passed (176) - the 49 red-first tests now
  green, routes.test.ts's ROUTES list now names /plan. planRecorded's URL assertion is EXACT string equality to the
  05:30:08Z ops/plan line. Boundary assertions added for the population (ceiling-inclusive lambda 7.75, zero-budget
  usedBudget at 999 s, a 128-char place id is 404 not 400). `npx tsc --noEmit` in this worktree stops at TS2688
  (cannot find @cloudflare/workers-types/2023-07-01) before reading any file: tsconfig's types path vs the installed
  workers-types, not this task's; vitest is the gate. Population: test/mutate/planMutants.mjs, 43 mutants over 8
  subjects, MIN_MUTATIONS = 43, 2 EQUIVALENT entries with witnesses; --prove-floor refused on all 4 arms
  (empty / 42 / hazards.ts unmutated / a new subject) and stayed quiet on the real table, exit 0.
- 2026-10-05T06:32:38Z POPULATION (agent/claude-opus-5). Run 1, `node services/api/test/mutate/planMutants.mjs` at
  0d50240: "population mutations=43 (floor 43) equivalent=2 subjects=8 tests=6", "baseline green tests=50",
  "RESULT caught=41 missed=2 trap=0 of 43", exit 1 - SURVIVORS pins-closed-run (`index < run.to` -> `<=`) and
  pins-merge-roads (merge ignoring road_class): the t0221 recording's nine longest road changes do not sit on those
  boundaries. Closed by test/planWaypoints.test.ts (three synthetic five-point routes, decisionPoints by exact
  equality), added to the driver's TESTS. Run 2 (the full population again, not only the two rows):
  "population mutations=43 (floor 43) equivalent=2 subjects=8 tests=7", "baseline green tests=53",
  pins-closed-run CAUGHT by "a run names the segment that STARTS at its first point (half-open [from, to))",
  pins-merge-roads CAUGHT by "a change of road class alone, on the same way and score, is a decision point",
  "RESULT caught=43 missed=0 trap=0 of 43", exit 0. `--prove-vacuity` (every test filtered out):
  "RESULT caught=0 missed=43 trap=0 of 43", exit 0 - every mutant loads and nothing but a named failure counts.
  EQUIVALENT (in the driver's table with witnesses, never run): planner-ceiling-guard, search-cap-floor.
  Gates at this head: check-line-cap "P-SRC-02: 134 Swift files ... none over 300 lines" exit 0 (TS: largest new
  file test/planHarness.ts 151 lines, src/routePath.ts 122); check-exec-bits "P-OPS-01: 107 files ... all modes
  correct" exit 0; queue-check "QUEUE OK (242 tasks)" exit 0.
- 2026-10-05T06:32:38Z ACCEPTANCE re-quoted (agent/claude-opus-5), `cd services/api && npx vitest run`: Test Files 14
  passed (14), Tests 179 passed (179).
  (1) RULED R1/R2 above; planPrivacy.test.ts refuses 3-dp/4-dp origins, a coordinate destination, a coordinate beside
      the place id, waypoints/via/extra origin keys - each 400 with h.sent == [] and h.events == [].
  (2) planCost.test.ts: KILL=1 -> 503 planning_paused, sent [] events [] (also before the body is read, and on the
      shipped ROUTES route via SELF); events == ["reserve", then 7 x "fetch"], reserved [12]; 429 quota_exhausted
      with zero calls; 7 requests <= 12, max in flight 1. planRecorded.test.ts: the 6 scenic models toEqual
      [0,4,6,7,7.5,7.75].map(l => buildCustomModel(l, null)), none naming road_access/surface; a client
      custom_model is refused 400 (planPrivacy).
  (3) planRecorded.test.ts "Santa Monica -> Topanga +25 returns ops/plan's Apple Maps URL, ETA and route for the
      recording": apple_maps_url toBe the 05:30:08Z ops/plan URL literal, eta_s toBe 1346.01 (= lambda-7.75.json
      time / 1000, "22m26s"), fastest "20m14s", ceiling "45m14s", lambda 7.75, evaluations 6, route toEqual the
      recorded lambda-7.75.json coordinates + distance. planCeiling.test.ts: 120 seeded curves incl. non-monotone,
      every 200's eta_s <= fastest + budget recomputed in the test.
  (4) response keys exactly apple_maps_url budget_s ceiling_s eta_is_estimate eta_s evaluations fastest_eta_s hazards
      lambda route used_budget waypoints; <= 9 waypoints; vitest 179/179; population 43/43, floor 43 (R9).
- 2026-10-05T07:54:44Z REVIEW PASS (agent/rv1-t-0248, reviewer; owner agent/claude-opus-5) at head 1f27bdb, PR #139.
  Gates, bare, in .worktrees/rv1-T-0248 (detached at origin/task/T-0248): `cd services/api && npx vitest run`
  "Test Files 14 passed (14)", "Tests 179 passed (179)" (= the 06:32:38Z quote); check-mutate-population.py
  "P-PROC-06: 98 modules, 43 covered by 16 populations, 34 allowlisted, 0 added by this branch" exit 0; queue-check
  "QUEUE OK (242 tasks)" exit 0; `gh pr checks 139` core pass, pins-source-only pass. GAP: local
  ops/lib/check-line-cap and `ops/check-pins --source-only` did not finish in 15 min on this host (three other
  worktrees' check-pins runs were hung beside them, the host hang T-0242 recorded); stopped, not quoted. CI's
  pins-source-only on 1f27bdb stands for them; the PR touches no Swift and its largest file is planMutants.mjs, 176 lines.
  `git merge-base --is-ancestor origin/main origin/task/T-0248` exit 1: main moved AFTER the 06:33Z push (PR #138 merged
  07:10Z, then two queue commits for T-0250). The commits after base 677daa9 touch only services/etl, services/tiles,
  ops/etl and queue/ (no ops/lib, no pins). `git merge-tree --write-tree origin/main origin/task/T-0248` exit 0: no conflict.
  Acceptance re-read against the tree: (1) R1/R2 ruled 05:24:32Z before the 2fe8227 red commit; parsePlanRequest
  is a per-level key whitelist, and planPrivacy drives handlePlan. (2) KILL before req.json(); guardedPlan reserves
  before body(call); 7 calls, 13th refused before fetchImpl; the model is buildCustomModel(lambda, null) through
  rejectCustomModel. (3) planRecorded's URL toBe the 05:30:08Z ops/plan literal, eta_s 1346.01. (4) response keys,
  eta_is_estimate true, <= 9 waypoints, population 43 floor 43.
  REVIEWER MUTANTS (my own, none in planMutants.mjs; .build/rv1/mut.mjs applies one exact site, runs vitest, restores):
    rv1-reserve-after-call (upstream.ts: reserve moved after `await body(call)`, the quota decrement after the
      upstream calls): CAUGHT, 4 failed incl. planCost "the quota is reserved once, before the first upstream call".
    rv1-ceiling-from-scenic-lambda0 (lambdaSearch.ts: feasibility `duration <= seen[0].duration + budget`, the
      ceiling measured from the scenic lambda-0 route's own ETA, not the fastest): CAUGHT, 4 failed incl. planCeiling
      "never returns a route whose ETA exceeds fastest + budget, over 120 random curves".
    rv1-ceiling-from-scenic-both (the same in the bisection step too): CAUGHT, the same 4.
    rv1-three-dp-precision (planRequest.ts: `toPrecision(ORIGIN_DECIMALS + 3)`, which accepts 3 dp on a two-digit
      latitude): CAUGHT by planPrivacy "refuses an origin latitude with more than 2 decimals".
    rv1-place-comma (PLACE_ID admits ","): SURVIVED, ruled NOT fail-open. The shipped shape already admits a
      coordinate spelled as a place id ("34.0195:-118.4912"). A probe test, run and then deleted, drove handlePlan:
      that id and "34.01950_-118.49120" both give 404 with h.sent 0 and h.events 0. The comma spelling behaves the
      same way. Nothing goes upstream and no quota is spent, so P-PRIV-05 holds because the resolver is a lookup.
  RECORDABLE, not blocking: (a) the place-id charset admits coordinate spellings. The resolver that ships later
  must stay a lookup and never parse an id into a point. (b) With duplicate JSON keys, a 4-dp value reaches the
  Worker's parser and is dropped: last-wins gives 200 with only [-118.49, 34.02] sent upstream (same probe). (c)
  main must be merged before or at merge time (no conflict today). (d) The author's still-open items stand:
  planDepsFromEnv is null, so /plan answers 503 until DO counters, ROUTER_URL and a place table land; the Apple
  Maps `source` is the 2-dp origin.
