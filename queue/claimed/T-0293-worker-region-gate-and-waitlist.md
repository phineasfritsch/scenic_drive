---
id: T-0293
title: The Worker refuses a plan outside the served region with 422 region_unsupported before any quota or upstream call, the app reads it as PlanError.regionUnsupported, and POST /waitlist counts interest per coarse cell with no personal data
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T03:14:58Z
lease_expires_at: 2026-10-07T17:14:58Z
worktree: .worktrees/T-0293
branch: task/T-0293
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/, Tests/Fixtures/t0251/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/mutate/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05, P-PRIV-06]
reviewer: null
depends_on: [T-0248, T-0251]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: which coordinate(s) each of /plan /loop /trip /isochrone receives today (at most one per action, 2 dp - quote the whitelist), where the served region's bounds come from (services/etl/regions/la/region.json and the CI golden sfbay - one source of truth, compiled into the Worker, never fetched), and whether the gate is a bbox or a polygon; quote the bounds"
  - "Every planning route answers 422 {error: 'region_unsupported'} for a coordinate outside the bounds, BEFORE the quota decrement and with 0 upstream calls (counting fakes), through the shipped worker.fetch; table over every bound per memory range-checks-every-bound (each edge just outside via nextafter at 2 dp granularity, each exact edge accepted with the whole response compared), per route - rows as functions of the route with a meta-test that no row ignores it"
  - "Swift: PlanResponseReader maps 422 region_unsupported to PlanError.regionUnsupported, by full equality in the R6 table test; the doc comment on the enum case is updated by fact, not by prose claim"
  - "POST /waitlist {cell} accepts exactly one H3 resolution-5 cell id (validated), increments a D1 counter row keyed by that cell (migration 0006, columns cell + count + updated_at only - P-PRIV-05 DDL test extended and seen red with a forbidden column), refuses anything else with 400 by full-equality table, is quota-exempt and kill-switch-exempt by ruling (no upstream), and appears in the requestReadSites / route-enumerating tests"
  - "A mutation population entry per gate edge and per waitlist validation branch with a literal floor; three shown MISSED before, CAUGHT by name after"
---
## Brief

Plan, Launch scope: "US-only, Bay Area corpus/graph, REGION_UNSUPPORTED + waitlist". PlanError.regionUnsupported exists
on the client (T-0251) but no Worker response produces it. The owner's region is LA (memory user-lives-in-la); the
plan's Bay Area is the CI golden set. Privacy invariant: the server never receives more than one coordinate per user
action, never more than 2 decimal places; the waitlist stores a coarse cell count, never a person.

## Log
- 2026-10-07T03:11:48Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 region waitlist).
- 2026-10-07T03:14:58Z claimed by agent/claude-opus-5; lease until 2026-10-07T17:14:58Z
- 2026-10-07T03:31:25Z RULINGS (agent/claude-opus-5, before any code). MEASURED on 82e59854:
  - R1 COORDINATES TODAY. Each planning route receives exactly ONE coordinate, 2 dp, by its body whitelist:
    /plan `planRequest.ts` BODY_KEYS ["origin", "destination", "budget_minutes", "departs_at"], ORIGIN_KEYS ["lat", "lon"],
    DESTINATION_KEYS ["place"] (a corpus place id, never a coordinate); /trip `tripRequest.ts` BODY_KEYS ["origin",
    "destination", "days", "extra_budget_pct"], ORIGIN_KEYS ["lat", "lon"], DESTINATION_KEYS ["place"]; /loop
    `loopRequest.ts` and /isochrone `isochroneRequest.ts` BODY_KEYS ["start", "minutes"], START_KEYS ["lat", "lon"].
    Every coordinate component passes `atMostTwoDecimals` (toFixed(ORIGIN_DECIMALS = 2)) or is 400 invalid_request.
  - R2 BOUNDS, ONE SOURCE. The served region is the `bbox` of services/etl/regions/la/region.json (the owner's region)
    UNION services/etl/regions/sfbay/region.json (the plan's launch corpus and the CI golden set). Quoted: la min_lon
    -119.0, min_lat 33.7, max_lon -117.85, max_lat 34.45; sfbay min_lon -123.62, min_lat 36.85, max_lon -121.55, max_lat
    38.92. src/servedRegion.ts IMPORTS both JSON files (resolveJsonModule; wrangler's esbuild bundles them into the
    Worker at build time) - compiled in, never fetched, no second literal. Every bound is already a 2 dp value.
  - R3 BBOX, NOT POLYGON. The region source carries a bbox and nothing else geometric (`counties` are names); the graph
    and corpus are cut by that bbox, so a coordinate inside it is routable. A polygon would be a second source of truth.
    Inclusive on all four edges of each box; the two boxes are disjoint, so a just-outside row of one is outside both.
  - R4 WHAT IS GATED: the one received coordinate (/plan, /trip `origin`; /loop, /isochrone `start`). The destination
    place id is NOT gated: the server receives no destination coordinate, and the corpus it resolves through is cut from
    the same bboxes. Recorded as a scope line, not a claim that an out-of-region place cannot exist in D1.
  - R5 ORDER: KILL (503, before the body) -> POST only -> body whitelist (400 wins: a malformed body is malformed
    anywhere) -> REGION GATE -> deps/bindings (503 planning_unavailable) -> place resolve -> identify -> closures ->
    quota -> upstream. So a refused coordinate costs no D1 read, no quota read or reservation, no router request.
  - R6 ANSWER: 422 {"error":"region_unsupported"} exactly, nothing beside it (the bounds are not echoed).
  - R7 SWIFT: PlanResponseReader maps (422, "region_unsupported") -> PlanError.regionUnsupported; the reply is recorded
    from the Worker into Tests/Fixtures/t0251/422-region-unsupported.json and held there by planWire.test.ts (R7 of
    T-0251); the enum's doc comment moves the case out of "no current Worker response produces".
  - R8 POST /waitlist {cell}: exactly one key `cell`, a string for which h3Res5.ts `isResolution5Cell` holds (the
    validator /telemetry already uses). Else 400 {"error":"invalid_request","detail":...}; non-POST 405; D1 missing or
    failing 503 {"error":"waitlist_unavailable"}; accepted 200 {"waitlisted":true}. No identity is read, no header,
    no quota, no kill switch: D1 only and no upstream call (the /asn ruling of T-0267 R11) - OPERATIONAL in
    killSwitchRoutes, listed in routes.test.ts and requestReadSites.test.ts.
  - R9 MIGRATION 0006_waitlist.sql: waitlist (cell TEXT PRIMARY KEY, count INTEGER >= 1, updated_at TEXT) and nothing
    else. updated_at is the UTC DAY "YYYY-MM-DD", not an instant: a per-increment millisecond stamp would time one
    person's tap. accountDelete.test.ts's TABLES gains waitlist with its reason (no user column).
  - R10 "P-PRIV-05 DDL test": none exists on main (grep `breadcrumb` over services/api/test, ops/lib and Tests: zero
    hits; P-PRIV-05's NOT ASSERTED clause names "the server-column grep"). This task writes it, reading the columns
    from D1 itself after every shipped migration is applied (pragma_table_info), and binds it to P-PRIV-05 by name.
  - R11 P-PRIV-06 does not exist in pins/PINS.yaml on main. This task adds it: "/waitlist stores a coarse H3-5 cell
    count, never a person", binding the waitlist tests by name.
  - R12 MUTATION POPULATION: the Worker's populations live in services/api/test/mutate/*.mjs (thirteen drivers;
    ops/mutate holds the Python/Swift drivers P-PROC-06 reads). This one is services/api/test/mutate/regionMutants.mjs
    with a literal MIN_MUTATIONS; ops/mutate is not touched.
  - R13 TABLE SHAPE: a row is a function route -> body (the route's reference body with only its coordinate field
    replaced); meta-test: per row, the four routes' bodies are pairwise distinct and each differs from its route's
    reference body only in that field. Outside rows: fresh quota, answer compared whole, router requests [] and quota
    state {} (the fake creates an instance on first touch, so a READ shows too). Accepted rows: the device's daily
    record seeded past every tier's limit, answer compared whole to 429 quota_exhausted - the gate passed, the quota
    answered, zero router requests.
- 2026-10-07T04:12:22Z RED FIRST, BY NAME (before src/servedRegion.ts, src/waitlist.ts and the Swift case existed; migration 0006 written
  first so the waitlist file loads). vitest over the eight touched files: Tests 9 failed | 44 passed (53) - FAILED
  by name: regionGate "a coordinate just outside any edge or corner ... is 422 region_unsupported ..."; waitlist's
  five ("a valid cell is 200 waitlisted ...", "every other body is 400 ...", "a method other than POST is 405 ...",
  "no D1 binding is 503 ...", "is kill-switch-exempt and quota-exempt ..."); planWire "422-region-unsupported: ...";
  routes "every route is enumerable ..."; requestReadSites "the request sites under src are exactly ...". Swift
  (swift test --filter ScenicAPIClientTests): Executed 44 tests, with 1 failure - test422RecordedRegionUnsupported
  IsRegionUnsupported: unexpectedResponse(status: 422) is not equal to regionUnsupported. DDL test seen RED: `address
  TEXT` added to migrations/0006_waitlist.sql -> both migrationColumns tests FAILED by name (2 failed); restored,
  2 passed. GREEN after code: the eight files 53/53; Swift 44 tests, 0 failures. requestReadSites approves the two
  region.json import lines of servedRegion.ts (".json" is a request-member spelling in its regex) and waitlist.ts's
  three request lines.
- 2026-10-07T04:12:22Z MUTATION POPULATION services/api/test/mutate/regionMutants.mjs (R12), MIN_MUTATIONS = 40, eight subjects,
  --prove-floor: all four arms REFUSED, real population quiet. First run: RESULT caught=39 missed=1 trap=0 of 40 -
  MISSED db-missing-ignored: without the guard an unbound DB throws inside the write's try and the catch answers
  the same 503, so it moved to EQUIVALENT with that witness; its replacement write-failure-answers-200 was MISSED
  (no row reached the catch), the 503 test gained a D1 whose write throws (renamed "no D1 binding, or a D1 whose
  write throws, is 503 waitlist_unavailable"), then CAUGHT by that name. The other 39 CAUGHT by name, e.g.
  lat-max-strict by "a coordinate on any exact edge or corner ... passes the gate ...", lon-min-dropped by "a
  coordinate just outside any edge or corner ...", keys-superset by "every other body is 400 ...",
  migration-device-column by "the waitlist table is exactly (cell, count, updated_at) ...". MISSED BEFORE: those
  four under --prove-vacuity (no test runs): RESULT caught=0 missed=4 of 4.
- 2026-10-07T06:09:23Z MERGED origin/main (2ce37073, PR #177 /config) as 9306ad26. Conflicts in routes.test.ts and killSwitchRoutes.test.ts
  resolved to carry both /config and /waitlist. configSweep's REQUESTS gains /waitlist (valid: a res-5 cell; invalid:
  the same cell uppercased). configAnswerPath's whole-file digest for src/index.ts moves to cdda2094... in the same
  commit because index.ts gained the /waitlist ROUTES line. R14 (a disagreement found on the merged head):
  tripRequest.test.ts "every exact bound is accepted through the shipped route" sent the whitelist corners (90, 180)
  and (-90, -180) and expected 200. Those corners still PARSE (the parseTripRequest table is unchanged), but they lie
  outside the served region, so through the shipped route those two rows now expect 422 with no router request.
  REGION_REFUSED names them, and an assertion holds those names to rows of ACCEPTED.
- 2026-10-07T06:09:23Z GATES ON THE MERGED HEAD 9306ad26: npx vitest run (services/api): Test Files 68 passed (68), Tests 2095 passed
  (2095), and 68 equals the number of test/*.test.ts files on disk. swift test --scratch-path .build/t0293-swift --filter
  ScenicAPIClientTests: Executed 44 tests, with 0 failures, exit 0. run-named-tests: NAMED P-COST-01 passed=31/31,
  NAMED P-PRIV-05 passed=28/28, NAMED P-PRIV-06 passed=7/7, each exit 0. check-mutate-population.py: "every added
  module is covered or allowlisted; the floor of 67 holds" exit 0. ops/queue-check: QUEUE OK (285 tasks) exit 0.
  NOT COMPLETED HERE: bash ops/lib/check-line-cap had run for over 100 minutes without finishing, and bash
  ops/check-pins --source-only and the region population re-run on the merged head printed nothing in about 30 minutes.
  The box was at 99% CPU from another session's headless-chrome render, and every bash fork crawled. Substitute
  measurement: the same population (git ls-files of Sources/Tests/apps/ios **/*.swift) is 242 files and none is over 300
  lines, measured with python. Touched files: PlanClientResponseTests.swift 215, regionMutants.mjs 191, tripRequest.test.ts
  182, regionGate.test.ts 178, waitlist.test.ts 154. CI is the confirmation for these three.
