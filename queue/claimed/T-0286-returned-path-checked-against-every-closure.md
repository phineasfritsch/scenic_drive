---
id: T-0286
title: every returned route is checked against EVERY stored closure (not only the <=50 sent) - a path crossing a dropped closure is re-requested once with that closure swapped in, and if it still crosses, the answer carries a 'crosses closure' hazard instead of a silent route
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T17:35:53Z
lease_expires_at: 2026-10-07T05:35:53Z
worktree: .worktrees/T-0286
branch: task/T-0286
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-COST-04]
reviewer: null
depends_on: [T-0282]
verify: [ops/test, ops/check-pins]
acceptance:
  - "after each driven router response (/plan chosen route, /loop attempt, /trip each leg) the Worker tests the returned path (points_encoded false) against every stored closure polygon with an exact segment-polygon intersection (point-in-polygon for vertices + edge crossings), ruled in the Log; a crossing of a closure that was NOT sent triggers ONE re-request with the crossing closures swapped in for the farthest sent ones (still <= 50), counted inside the existing request caps (P-COST-04: 12/3/12) - a request over the cap is not made"
  - "if the re-requested path still crosses an active closure, or the cap forbids the re-request, the 200 answer carries closures_hazard {state, ..., crosses: [lcs ids]} - never a silent crossing; tests through ROUTES over the T-0276 fixture with a synthetic path crossing a dropped closure, as cross-product tables (empty set / one closure / > 50; crossing at a vertex, along an edge, fully inside) with the no-row-ignores-its-variant meta-test"
  - "P-SAFE-08 binds the new tests by name with an APPENDED dated sentence retiring T-0282's 'nothing re-checks the returned path' limit; a TS mutation population with a literal floor"
---
## Brief

T-0282 stillOpen 1: 'The corridor is the straight segment between a request's two points, not the path GraphHopper
returns. A scenic detour can pass a dropped closure ... nothing re-checks the returned path against the dropped set.'
About 117 closures are dropped per LA request on today's feed. Product invariant: a route never crosses an active
closure (P-SAFE-08), and it is never silent.

## Log
- 2026-10-06T17:30:50Z filed by agent/claude-opus-5 (orchestrator) after PR #172 (T-0282) review PASS.
- 2026-10-06T17:35:53Z claimed by agent/claude-opus-5; lease until 2026-10-07T05:35:53Z
- 2026-10-06T17:48:16Z RULINGS (author rule; before code). Measured on the T-0276 fixture's stored set (expected.json
  cap.geojson): 173 polygons, every one ONE ring of 5 positions (an axis-aligned buffered square), 163 closures.
  C1 geometry. The returned path is the router's points.coordinates ([lon, lat], points_encoded false), n >= 1
  vertices (n = 1 is a degenerate segment p-p; n = 0 crosses nothing). A polygon is its OUTER ring only: inner rings
  (holes; the cron writes none, the reader accepts them) are ignored, so a path inside a hole COUNTS as crossing -
  fail closed. The path crosses the polygon iff (a) some path vertex is inside the ring by the crossing-number rule
  (closuresNearest's `inside`), or (b) some path segment and some ring edge meet as CLOSED segments: orientations
  o1 = orient(c,d,a), o2 = orient(c,d,b), o3 = orient(a,b,c), o4 = orient(a,b,d); proper when o1,o2 and o3,o4 have
  strictly opposite signs; else they meet when some o is exactly 0 and that endpoint lies in the other segment's
  bounding box - this covers touching at a vertex, an endpoint on an edge, collinear overlap, and a degenerate
  (one-point) segment. Touching the boundary counts as crossing (a closure is a closed set; fail closed); collinear
  on the edge's LINE but outside the edge does not. Plane: T-0276 R4's plane is x = 91961 lon, y = 110946 lat, a
  positive diagonal scaling, and orientation signs and bounding-box order are invariant under it, so the predicate
  IS the R4-plane predicate computed on raw degrees, one rounding fewer. Exactness: IEEE doubles, not robust
  predicates; a path vertex equal to a ring position gives an orientation of exactly 0, which is how the tests'
  vertex and edge cases are built (from the ring's own positions).
  C2 which polygons. EVERY polygon of the snapshot's stored set (<= 2000), not the <= 50 sent; a stale snapshot's set
  counts (the last good set is the active set as far as the Worker knows); an unavailable snapshot has no set and
  nothing is checked (its hazard already says unavailable). A loop's retrace squares are not closures and are not
  checked. A closure is N3's group (a run of features sharing a string lcs_index); it is crossed when any of its
  polygons is. Its id in the hazard is its lcs_index, or "#<stored position of its first feature>" without one.
  C3 which responses. Every path the answer RETURNS: /plan the chosen route (the search's other routes are measured,
  never shown); /loop the attempt returned (the clean one); /trip the search's chosen A->B route (returned as
  `route` in both views and split into days) and, in the full view, each day leg. Each gets at most ONE re-request.
  C4 swap rule. C = the crossed closures, sent or not; U = C minus those the request sent. A re-request is made only
  when U is non-empty (swapping cannot help a crossing of a closure the router was already told about). The new
  set: C ranked by N3's (distance, stored position), longest prefix that fits 50 (N4); then the remaining room is
  filled with the longest prefix of the ranked NON-crossed closures - which is exactly "drop the farthest sent ones
  until the crossers fit", since the sent set is itself that ranked prefix. Sent in stored order, always <= 50; the
  re-request's left-out count enters N6's `dropped` max.
  C5 re-request and caps. The re-request is the request that returned the path with only the closures replaced:
  /plan car_scenic at the winning lambda; /loop the same seed with the attempt's own retrace squares merged after
  the swapped set (mergeClosures, R8 unchanged); /trip's search at the winning lambda; a leg at the winning lambda
  on the leg's corridor. It REPLACES the returned path only if it passes the guards the original passed - /plan the
  ceiling (eta <= fastest + budget) and Jaccard < 0.6; /loop the retrace check; /trip's search the day split
  (no over_budget, no too_few_days); a leg its day ceiling - else the original is kept and ITS crossings reported.
  A re-request the router refuses fails the answer as any refused request does (502 no_route). Caps (P-COST-04,
  ceilings): each planner counts its own calls, and a re-request is made only when used + 1 + reserved <= cap,
  reserved = the requests the route must still make: /plan cap 12, reserved 0 (1 + 6 + 1 = 8 always fits);
  /loop cap 3, reserved 0 (only when <= 2 attempts were made); /trip cap 12, the search reserves `days` legs in the
  full view (the most legs a split can make) and 0 in the preview, a leg reserves the legs after it. Otherwise no
  request is made and the crossing is reported - the guarded call is never asked for a 13th / 4th.
  C6 hazard. crosses = the closures still crossed by the paths the answer returns (after their re-request, or
  without one), deduplicated, in stored order. closures_hazard is present when the state is not fresh OR dropped
  > 0 OR crosses is non-empty; `crosses` only when non-empty: {state, version, fetched_at, dropped?, crosses}. A 200,
  never a refusal, never a silent crossing.
  C7 tests. closuresCrossing.test.ts through ROUTES (/plan, /loop, /trip preview): route x set (empty / one closure
  X / over 50 = the T-0276 fixture's 173 polygons, X its single-polygon closure FARTHEST from the route's corridor,
  so dropped) x shape (clear, vertex, edge, inside, through - built from X's own ring) x router (honours: an answer
  to a request whose areas carry X's ring is the clear path; ignores: always the shape), by full equality of every
  request's areas, the request count, the returned coordinates and the hazard, with meta-tests that no row ignores
  its set variant or its shape. Cap rows: a loop whose third attempt crosses (no 4th request), a paid trip whose
  search or leg cannot re-request inside 12, and the ones that can, through handleTrip with paid deps.
  closuresCrossingGeometry.test.ts: the predicate's cases (holes, one-point path, collinear off the edge, ...).
  C8 mutation population: a new runner test/mutate/crossingMutants.mjs (closuresMutants.mjs is at 281 of 300 lines)
  over src/closuresCrossing.ts and the wiring, literal floor; closuresMutants.mjs entries whose anchors this change
  rewrites are re-anchored on the code they name.
  C9 earlier tests: a T-0282 row whose synthetic path lies on a stored closure the request did not send now
  re-requests and/or reports crosses BY THIS RULING; each such row is listed here when the suite shows it.
- 2026-10-06T19:22:39Z RULINGS, ADDENDUM (found while writing the tests; nothing above rewritten). C1's "axis-aligned" is
  wrong: the fixture's squares are buffered along each closure's road and rotated (one ring of 5 positions each, as
  measured); nothing turns on it - the shapes are built from each ring's own positions. C4a futile swap: when every
  crossed closure that fits is already sent (e.g. a 51-way tie at distance 0, all 51 crossed), the swap equals the sent
  set; no request is made and the crossings are named. Equivalently, the re-request is made iff the swap carries a
  feature the request did not send (by C4 only a crosser can be new), which also covers "only sent closures crossed".
  C5a loop: the retrace attempt is always the third of LOOP_UPSTREAM_COST 3, so its re-request is always capped; a loop
  re-request therefore never carries retrace squares - same seed, the swapped set alone.
  C9 earlier tests changed BY RULING (expectations extended, nothing removed): closuresNearest.test.ts - the /loop and
  /trip rows of "over 50, the on-corridor ten stored last", "a 51-way tie at distance 0" and "over 50, stale" (the
  synthetic loop leaves from its corridor and the trip's ROAD IS its corridor, so they cross the on-corridor ten / the
  51 ties - all sent or a futile swap, so no re-request; the hazard now carries crosses) and "the search and legs 3-5
  carry Big Sur..." (ROAD ends inside the big-sur square: crosses ["big-sur"]); closuresNearestRetry.test.ts - the six
  /loop rows over those three variants, and the six /trip "Z beside road vertex k, fifty / over 50" rows (the C squares
  sit ON the road's first edge: crosses c-1..c-49 / c-1..c-50). The /plan rows are unchanged (its synthetic path
  crosses none). Every changed row is still held by full equality.
- 2026-10-06T19:22:39Z RED FIRST by name (new tests over the pre-change src/: `git stash push -- services/api/src`, run, pop;
  closuresCrossing.ts was untracked so the predicate was present): `npx vitest run` over closuresCrossing,
  closuresCrossingTrip, closuresCrossingGeometry, closuresNearest, closuresNearestRetry -> Tests 85 failed | 122 passed
  (207): closuresCrossing.test.ts 43 (every crossing row over X alone and the fixture, e.g. "/loop, the fixture, vertex
  path, router ignores: requests, areas, the returned path and the hazard equal the row's"), closuresCrossingTrip 12,
  closuresCrossingGeometry 11 (every picker/swap test, e.g. "crossing a dropped closure: one re-request carrying it; a
  clear answer replaces the path and names nothing"), closuresNearest 7 and closuresNearestRetry 12 (the C9 rows).
  Green before the change by design: the empty and clear rows, the meta-tests, the predicate cases.
  CODE: src/closuresCrossing.ts (C1, new); closuresNearest.ts rank() extracted unchanged, swappedClosures (C4), picker
  `returned` (C2-C5, C4a) and `crosses()` (C6); closuresStore withClosuresHazard(answer, snapshot, dropped, crosses)
  (C6); scenicPlanner / loopPlanner / tripPlanner take the guard, count their own calls, and re-request inside the caps
  with their own guards (C5, C5a); plan/loop/trip pass picker.returned and picker.crosses(). GREEN: `npx vitest run`
  Test Files 54 passed (54), Tests 1684 passed (1684) (a39956a); after the second batch (futile rule in code, loop
  simplified, re-request body / preview-reserve / first-leg / leg-ceiling rows) the crossing files 15 + 213 passed.
- 2026-10-06T19:22:39Z MUTATION POPULATION: services/api/test/mutate/crossingMutants.mjs (new; closuresMutants.mjs is at 281
  lines), subjects closuresCrossing, closuresNearest, closuresStore, plan, loop, trip, scenicPlanner, loopPlanner,
  tripPlanner. Run once, whole: `node services/api/test/mutate/crossingMutants.mjs` -> baseline green tests=229,
  RESULT caught=54 missed=6 trap=0 of 60. MISSED: cx-o1-off and cx-o2-off (every one-point-on-edge case sat on the
  bottom edge, which the crossing number already calls inside) -> rows "starting on / ending on the top edge's
  interior"; cx-within-x-min-open (masked by the other edge's check) -> "ending at the top-left vertex from the
  north-east"; cx-within-x-only -> "collinear on a vertical edge's line, past its end"; cx-ring-closing-edge (the
  square's closing edge is its left side, inside by crossing number) -> "the ring's CLOSING edge is an edge: a ring
  from the top-right corner"; cx-inside-flip -> EQUIVALENT with its witness (left and right crossing parities agree off
  the boundary; on it segmentsMeet decides). Re-run of the five: `--only=cx-o1-off,cx-o2-off,cx-within-x-min-open,
  cx-within-x-only,cx-ring-closing-edge` -> baseline green tests=234, RESULT caught=5 missed=0 trap=0 of 5. Population
  59, MIN_MUTATIONS 59 (literal); EQUIVALENT 5, each with its witness (cx-inside-flip, cx-o3-alone-off,
  cx-o4-alone-off, plan-cap-ignored, pk-empty-crossers-swapped). --prove-floor: "population 0 is below the floor",
  "population 58 ...", "subject src/trip.ts has no mutation", "subject src/newModule.ts has no mutation" all REFUSED,
  the real population quiet. closuresMutants.mjs: 13 entries re-anchored on the code they name (plan/loop/trip
  -no-closures, -whole-set, -no-hazard, -dropped-unreported; store-dropped-ignored); `--only=<those 13>` -> baseline
  green tests=738, RESULT caught=13 missed=0 trap=0 of 13; every anchor of both files occurs exactly once.
- 2026-10-06T19:22:39Z BOUND (ops/lib/named-tests.json from the vitest JSON report of the three new files): P-SAFE-08
  668 -> 833 (closuresCrossing.test.ts 110, closuresCrossingTrip.test.ts 15, closuresCrossingGeometry.test.ts 40);
  P-COST-04 9 -> 27 (closuresCrossingTrip.test.ts 15 and the loop's 3 cap rows). RED by name, each one-line src mutant
  restored by git checkout: closuresNearest futile test -> `false`: `python ops/lib/run-named-tests.py P-SAFE-08` NAMED
  P-SAFE-08 passed=816/833 (e.g. "crossing only a SENT closure: no re-request, the closure named", "a futile swap (51
  crossers, the 50 nearest already sent) makes no request; all 51 named"); tripPlanner search reserve dropped: `...
  P-COST-04` NAMED P-COST-04 passed=25/27 (the two five-day search rows). PINS.yaml: one dated passage APPENDED to the
  end of P-SAFE-08's and of P-COST-04's why_no_test_catches_it, the earlier text byte-identical; read back through
  ops/lib/pins.py load().
