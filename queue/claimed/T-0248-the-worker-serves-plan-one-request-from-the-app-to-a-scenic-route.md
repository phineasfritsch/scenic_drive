---
id: T-0248
title: the Worker serves POST /plan - one request from the app becomes a fastest call plus the lambda budget search against the router, returning the scenic route, ETA vs fastest, hazards and the Apple Maps URL; quota first, kill switch honoured, privacy invariant held
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T05:09:51Z
lease_expires_at: 2026-10-05T15:09:51Z
worktree: .worktrees/T-0248
branch: task/T-0248
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-04, P-SAFE-01]
reviewer: null
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
