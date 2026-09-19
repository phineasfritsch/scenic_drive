---
id: T-0182
title: ops/plan <O> <D> <B> - the M3 CLI exit: an Apple Maps URL and the per-edge term table for an LA origin and destination against the served LA graph
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T17:53:17Z
lease_expires_at: 2026-09-20T01:53:17Z
worktree: .worktrees/T-0182
branch: task/T-0182
exclusive: [root-package]
touches: [ops/plan, ops/lib/, ops/mutate/, Sources/, Package.swift, services/api/src/, Tests/]
pins_affected: []
reviewer: null
depends_on: [T-0116, T-0158]
verify: [ops/test, ops/check-pins]
acceptance:
  - "`ops/plan <origin> <destination> <extra-minutes>` prints an Apple Maps URL with <= 9 pinned waypoints, the fastest ETA, the returned ETA (<= fastest + budget: the ceiling, asserted), and a per-edge table (way id, highway, scenic_score, the terms, the lambda chosen); RED by name: the budget-ceiling assertion red on a stub that returns lambda 8, the actually-different assertion red on a stub that returns lambda 0 (the plan's meta-tests)"
  - "Linux tests: the URL builder and the table over a recorded GraphHopper response (a golden), count line quoted"
---
## Brief

From the 2026-09-19 19:13 panel (STRATEGY, grounded). plan:22's success criterion - "the developer drives a route
this app made" - has a phone-free instance in plan:284's M3 exit: `ops/plan <O> <D> <B>` prints an Apple Maps
URL plus the per-edge term table, and "you drive engine output from the CLI". That path needs no TestFlight
(T-0009, human) and retires the criterion for the owner in LOS ANGELES once T-0168 clips regions/la, T-0031
serves it, and the Worker's custom model (T-0158, merged) supplies the lambda. No task named `ops/plan` existed
in ready/ or claimed/ (only T-0013 mentions it). The origin is Westwood (regions/la); the destination is the one
the owner names - nothing in the plan or any Log records it (FOR THE HUMAN).

## Log
- 2026-09-19T02:11:14Z filed by agent/claude-fable-5-1 from the 19:13 panel's grounded synthesis. Not started; behind T-0031's second half.
- 2026-09-19T02:58:56Z PROMOTED to ready/ by agent/claude-fable-5-1 (20:13 panel, grounded): T-0116 and T-0158 are merged and T-0031's first slice is PR #105; the terminal task of the LA CLI path was the only link still in backlog/.
- 2026-09-19T10:46:00Z depends_on: T-0031 -> T-0209 by agent/claude-fable-5-1 (03:13 panel, grounded): T-0031 is in done/ as a Vermont slice, so the queue read this task as unblocked while nothing builds the LA graph it needs; T-0209 is that graph.
- 2026-09-19T17:49:27Z SPLIT by agent/claude-fable-5-1 (10:13 panel, fable-grounded): plan:284's M3 exit names the CLI plus MV->SF; the commute answer is M4/T-0013's input, not this task's - the freeze on 'the destination the owner names' was self-imposed (asked of the human seven panels running). Clauses 1 and 3 need no graph; clause 3's recorded GraphHopper response comes from T-0213's REAL canyon-window GraphHopper 11.0 graph (#117: window-tagged-1.osm.pbf sha256 06046be0...0090; the graph-cache preserved at services/routing/work/t0213/ in the main checkout - verify it is there before recording, else record from a fresh import of that PBF), not a stub. The served-graph run moves to T-0221 (depends_on [T-0182, T-0209]). NOTE: touches ops/lib/ overlaps T-0217's by directory only.
- 2026-09-19T17:53:17Z claimed by agent/claude-opus-5; lease until 2026-09-20T01:53:17Z
- 2026-09-19T17:53:17Z at claim by agent/claude-fable-5-1 (orchestrator): T-0213's canyon-window GraphHopper 11.0 graph-cache is preserved at services/routing/work/t0213/graph-la-window/ in the MAIN checkout (edges, geometry, location_index, edgekv_*) with its custom models under models-la/; the served image is scenic-routing:t0213 in WSL docker (T-0213's Log names the digest-pinned build). Record clause 3's golden from THAT graph (a real /route response over the window: PCH at Topanga -> Topanga near Old Topanga, the pair T-0213 routed), never a stub. Swift 6.3.3 is native on this box - swift test runs locally with --scratch-path .build/T0182.
- 2026-09-19T18:00:39Z RULINGS BEFORE CODE by agent/claude-opus-5 (the author rule). Seven, R1-R7, and the
  header amendments they authorise.

  HEADER, ruled and done in this commit BEFORE any edit to a serial file: `exclusive: [root-package]` and
  `Package.swift` added to `touches:` (R1 needs an executable target declared in the root package);
  `Sources/ScenicKit/` widened to `Sources/` (the CLI target is a new directory under Sources/); `ops/mutate/`
  added (R7's population). Nobody holds the root package: `ls queue/LOCKS/` is `floors.lock scenic-index.lock`,
  and no claimed task names Package.swift in its `touches:` (`grep -n '^touches:' queue/claimed/*.md`:
  T-0043 and T-0058 are ops/lib/check-line-cap, T-0087 is ops/lib/queue.py; the three only mention the path
  in prose).

  (R1) THE SHAPE: (a). One implementation of the bisection and the scoring - ScenicKit's LambdaSearch, which
  T-0116 already shipped with the measured-feasible-only discipline - driven by a thin CLI: a Swift executable
  target `ScenicPlanCLI` (product `scenic-plan`) in the ROOT Package.swift, Foundation + ScenicKit + Handoff,
  and `ops/plan` a bash wrapper around `swift run --scratch-path .build/plan scenic-plan "$@"`. (b), a python
  ops/plan that re-implements the bisection, is REJECTED: two bisections drift, and the one that would drift
  is the one holding the ceiling invariant. The CLI target imports no Apple-only module (P-SRC-01's grep runs
  over the whole of Sources/); URLSession's Linux home, FoundationNetworking, is behind `#if canImport` in the
  CLI target only, never in ScenicKit.

  (R2) THE REQUEST PATH. The Worker is not deployed and the VPS is not up, so the CLI speaks to GraphHopper
  directly. The custom model is buildCustomModel's, ported ONCE to Swift (`LambdaCustomModel`) rather than
  shelled to node: a routing binary that needs a node toolchain on the box to ask for a route is a second
  runtime on the hot path, and the CLI has to run where GraphHopper runs. The port is held to the TS by a
  GOLDEN - the bytes `node --experimental-transform-types` prints from services/api/src/customModel.ts,
  committed under Tests/ScenicKitTests/Fixtures/custom-model/ with the node version and the command in a
  header - and a test asserting byte equality at several lambdas. The safety gates stay server-side in
  car_scenic_base.json: the emitted model names neither `road_access` nor `surface`, asserted over the
  serialised text (the same property rejectCustomModel enforces on the Worker).

  (R3) THE META-TESTS, red by name: `ScenicPlannerMetaTests` - "a solver that answers lambda 0 fails actually
  different" (Jaccard(edge-set, fastest) < 0.6 -> PlanFailure.notActuallyDifferent) and "a solver that answers
  lambda 8 over the ceiling fails the budget ceiling" (returned ETA > fastest + B*60 ->
  PlanFailure.budgetCeilingBreached). Red-first is demonstrated by removing each guard from the SHIPPING
  symbol (ScenicPlanner.plan, the entry point ops/plan runs) and quoting the named failure, not by asserting
  over a helper.

  (R4) THE GOLDEN, and the disagreement this task's instructions carry. T-0213's image HAS NO HTTP SURFACE:
  config.yml carries no Dropwizard `server:` block (its own header says the section arrives with the HTTP
  surface), the shaded jar depends on graphhopper-core alone (plugins/scenic-score-parser/pom.xml), and
  ScenicRouterMain has modes import|probe|route and no server - T-0213's ruling R5 recorded exactly this
  ("/info is therefore not reachable"). The serving half is T-0209, which is not done, and services/routing/
  plus config.yml (a serial file held by nobody here) are not in this task's touches. So "a recorded /route
  response" cannot be recorded from a server today without doing T-0209's work inside T-0182. RULED: the
  golden is recorded from the REAL preserved graph by the REAL shipped jar - extracted from
  scenic-routing:t0213 and sha256'd - compiled against a ~100-line recorder in the pinned maven builder image,
  with services/routing/work/t0213/graph-la-window mounted read-only. GraphHopper 11.0 computes every number
  in it (time, distance, points, the path details); the recorder writes them into the documented
  points_encoded=false /route shape. THE ENVELOPE IS THE RECORDER'S, NOT graphhopper-web's - that is the
  deviation, and the fixture's header field says so beside the image tag, the jar sha256, the graph
  properties sha256 (170bfe37bda146a51821f74fa53d9a42084e1cb3db27e2841205fe432c20b188), the window PBF sha256
  (06046be0...0090) and the recorder's run line. No stub, and no claim that this is a served response.
  SECOND: T-0213 named its pair in prose only - the input coordinates were never recorded - so the recorder's
  own from/to are quoted here with the SNAPPED waypoints GraphHopper returned, and the corroboration that it
  is the same pair is T-0213's own numbers (distance 8121.6 m, time 507242 ms at lambda 0). If they disagree
  the Log says so rather than claiming the pair.
  THIRD: with no server there is no end-to-end HTTP smoke. `ops/plan` is smoked against the recorded
  directory (real responses from the real graph, refusing any lambda it has not got); the HTTP transport is
  T-0221's to exercise against the served graph. Stated plainly rather than implied.

  (R5) THE TABLE. Columns the graph can answer TODAY: way id (osm_way_id), highway (road_class), scenic_score,
  metres, seconds - T-0213 encoded scenic_score and osm_way_id and config.yml adds road_class/surface/
  road_access, and NOTHING in that graph carries the scoring TERMS (E/M/GATE of SegmentTerms). The per-term
  breakdown the acceptance line names arrives when the terms reach the graph as path details; until then the
  table prints the columns that exist and the header says which. The header line carries the lambda chosen,
  the fastest ETA, the returned ETA, the ceiling, the evaluation count and the Jaccard distance from the
  fastest edge set. A returned ETA over the ceiling is a hard error (PlanFailure.budgetCeilingBreached,
  thrown in ScenicPlanner.plan) and is never printed as a plan.

  (R6) COORDINATES. This path is CLI -> GraphHopper on the owner's own box and never touches OUR server, so
  P-PRIV-05's two-decimal rule (what the SERVER may receive) does not govern it: full precision goes to the
  router, and the Apple Maps URL keeps AppleMapsDirections' own five decimals, which is that type's
  documented, deliberate choice. When this same plan is issued through the Worker - T-0221, and the app - the
  two-decimal rule applies at that boundary; this CLI does not launder anything through it and claims no
  exemption for it.

  (R7) THE POPULATION. ops/mutate/plan.py, with a literal floor, covers the numeric modules this task adds:
  RouteDifference.swift (Jaccard), LambdaCustomModel.swift (the band multipliers and their formatting),
  PlanTable.swift (the detail-run intersection and the row arithmetic), PlanWaypoints.swift (the spacing) and
  ScenicPlanner.swift (the ceiling and difference guards). The rest are allowlisted in
  ops/lib/mutate-population-allowlist.json with a reason each - a decoder, a protocol, an error enum, the CLI
  entry point and the HTTP transport - and the driver is added to check-mutate-population.py's DRIVERS
  whitelist and its subjects to COVERED_FLOOR.
- 2026-09-19T18:30:00Z THE CONTAINER STAGES, quoted as they landed (CLAUDE.md: a session restart keeps the
  worktree and loses stdout), and the R4 amendment the first of them forced.

  STAGE 1, the jar and the graph, in WSL. `docker image inspect scenic-routing:t0213` ->
  sha256:ff123b2f85b337c66e99286a0af40f5dcd1029c79206f28dfffb72f1fa2eba11. The shipped jar extracted from
  that image (`docker run --rm --entrypoint cat scenic-routing:t0213 /app/scenic-router.jar`):

      7931f599a14bd00844793ef441ce6228e475e5d5482be5702a75e506f076fe43  scenic-router.jar
      170bfe37bda146a51821f74fa53d9a42084e1cb3db27e2841205fe432c20b188  graph/properties

  The graph sha256 is T-0213's own, to the byte: the preserved cache IS the canyon-window graph #117 built.
  It was copied out of the main checkout before use so the preserved original is never opened read-write.

  STAGE 2, the recorder compiled against that jar in the pinned maven builder image
  (maven:3.9-eclipse-temurin-21@sha256:c2a2c585...a7d74), with services/routing/config.yml and
  services/routing/profiles mounted, the graph copy at /rec/graph, and the models emitted by the SWIFT CLI
  itself (`ops/plan --emit-model <lambda>`, which is the Worker's model byte for byte):

      GraphHopper - version 11.0|2025-10-14T14:28:00Z
      graph car|RAM_STORE|2D|no_turn_cost|nodes:9,edges:24,... edges: 24,057(1MB), nodes: 21,137(1MB),
        bounds: -118.9663074,-118.5138948,34.0026669,34.172355
      ROUTE profile=car_fast   model=-               time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-0.json   time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-4.json   time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-6.json   time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-7.json   time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-7.5.json time_ms=509258 distance_m=8114.6 points=293 way_runs=26
      ROUTE profile=car_scenic model=lambda-7.75.json time_ms=509258 distance_m=8114.6 points=293 way_runs=26

  That is T-0213's pair (PCH at Topanga -> Topanga near Old Topanga, 34.0392,-118.5836 -> 34.0944,-118.6019;
  T-0213 recorded its pair in prose only, so these are MY coordinates and they land on the same corridor:
  8114.6 m / 509258 ms against T-0213's 8121.6 m / 507242 ms, a different snap of the same drive).

  R4 AMENDMENT, ruled here rather than worked around: on that pair the route is IDENTICAL at every lambda
  the bisection visits - one road, Topanga Canyon Boulevard, scored 8 and therefore in the never-penalised
  high band at every lambda. A plan over it is REFUSED by the actually-different guard, which is the honest
  answer for a corridor with one road and is the plan's own "not much pretty within 25 minutes" state. So
  the golden is recorded for TWO pairs off the same graph, the same image and the same jar:
    * `Tests/Fixtures/t0182/t0213-pair/` - T-0213's pair, fastest + lambda 0, kept as the REAL-DATA witness
      that the guard fires (a test plans over it and expects `notActuallyDifferent`);
    * `Tests/Fixtures/t0182/plan-pair/` - Topanga village -> PCH at Malibu Canyon (34.0944,-118.6013 ->
      34.0365,-118.6870), a pair INSIDE THE SAME WINDOW that has a real alternative, measured before it was
      chosen (four candidate pairs were probed; this is the one that bites):

      PAIR 34.0944,-118.6013 -> 34.0365,-118.6870
      ROUTE profile=car_fast   model=-               time_ms=1075693 distance_m=18224.3 points=478  way_runs=61
      ROUTE profile=car_scenic model=lambda-0.json   time_ms=1075693 distance_m=18224.3 points=478  way_runs=61
      ROUTE profile=car_scenic model=lambda-4.json   time_ms=1075693 distance_m=18224.3 points=478  way_runs=61
      ROUTE profile=car_scenic model=lambda-6.json   time_ms=2253369 distance_m=33068.9 points=1393 way_runs=58
      ROUTE profile=car_scenic model=lambda-7.json   time_ms=2253369 distance_m=33068.9 points=1393 way_runs=58
      ROUTE profile=car_scenic model=lambda-7.5.json time_ms=2253369 distance_m=33068.9 points=1393 way_runs=58
      ROUTE profile=car_scenic model=lambda-7.75.json time_ms=2253369 distance_m=33068.9 points=1393 way_runs=58

      PAIR 34.0392,-118.5836 -> 34.1150,-118.6450    all seven identical, 739632 ms / 11989.1 m
      PAIR 34.0392,-118.5836 -> 34.0365,-118.6870    all seven identical, 565177 ms / 10160.3 m

  NO claim is made here about T(lambda)'s shape over this window - T-0213's ruling holds, the scores are
  T-0207's and T-0208's to move. What is claimed is exactly what was measured: on this pair, at lambda >= 6,
  this graph returns a different, longer route, and the bisection therefore has something to find.

  STAGE 3, the recording (`--out`, 9 files, every byte GraphHopper's):

      == PLAN PAIR ==   fastest.json 15503 · lambda-0 15517 · lambda-4 15517 · lambda-6 39725
                        lambda-7 39725 · lambda-7.5 39727 · lambda-7.75 39728 bytes
      == T-0213 PAIR == fastest.json 9792 · lambda-0.json 9806 bytes

  STAGE 4, `ops/plan` END TO END over that recording, the smoke this task owes (T-0221 is the served-graph
  run; this is the CLI working, not a drive):

      $ SCENIC_PLAN_SCRATCH=.build/T0182 bash ops/plan 34.0944,-118.6013 34.0365,-118.6870 25 \
          --recorded Tests/Fixtures/t0182/plan-pair
      ROUTER recorded plan-pair
      PLAN origin=34.09440,-118.60130 destination=34.03650,-118.68700 budget=25m00s
      LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false
      ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m
      OVERLAP jaccard=0.112 required<0.600
      TABLE rows=58 columns=way,highway,scenic_score,metres,seconds (seconds apportioned by metres; the
        scoring terms are not in the graph)
      WAY         HIGHWAY         SCORE  METRES     SECONDS
      13388359    residential     5      151.9      10.4
      667514947   primary         6      98.9       6.7
      ... 54 rows ...
      13346012    tertiary        7      9164.0     624.4
      42775099    primary         7      3470.2     236.5
      1296483244  service         2      21.8       1.5
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.09440,-118.60130&destination=34.03650,-118.68700&
          waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&waypoint=34.06814,-118.61111&
          waypoint=34.07507,-118.62613&waypoint=34.08375,-118.63666&waypoint=34.08111,-118.64574&
          waypoint=34.07001,-118.65343&waypoint=34.08025,-118.70367&waypoint=34.06937,-118.70790&
          mode=driving

  (the URL is one line in the terminal; it is wrapped here only to fit the Log. The full 58-row table is
  the run's stdout and is reproduced by re-running the line above.)
- 2026-09-19T20:47:43Z RESUMED by agent/claude-opus-5 after the previous session died on a usage limit (the worktree was
  kept: c29b494 rulings, 3524cf1 the CLI and the recording, 3f340dd the population). This entry closes the
  four things that were still in flight, answers the 11:13 panel's CHECK ZERO in its own words, and records
  two things this branch did not cause and is not fixing.

  CHECK ZERO - THE GOLDEN'S PROVENANCE, stated plainly rather than by reference. The panel asks the Log to
  show how the server was stood up over services/routing/work/t0213/graph-la-window and to quote the real
  /route request, the /info line and the response. IT WAS NOT STOOD UP, BECAUSE IT CANNOT BE TODAY, and R4
  above rules exactly that: scenic-routing:t0213 has no HTTP surface. T-0213's own Log (:344) says it, its
  ruling R5 says `/info is therefore not reachable`, services/routing/config.yml carries no Dropwizard
  `server:` block, and ScenicRouterMain has modes import|probe|route and nothing else. There is therefore no
  local config to quote in full: a config that would stand a server up does not exist, and writing one is
  T-0209's work on a SERIAL file (config.yml) outside this task's touches:. What was done instead, and what
  the fixtures say about themselves:
    * every number in Tests/Fixtures/t0182/*.json was computed by GraphHopper 11.0 from the REAL preserved
      canyon-window graph - the same image (sha256:ff123b2f...2eba11), the same shipped jar
      (7931f599...fe43) and the same graph/properties (170bfe37...c20b188) T-0213 built, quoted with their
      digests in the 18:30 entry above as each stage landed;
    * the `/info` line's content - GraphHopper's version, the graph's node/edge counts and its bounds - is
      quoted there from the recorder's own banner (`GraphHopper - version 11.0|2025-10-14T14:28:00Z`,
      `edges: 24,057, nodes: 21,137, bounds: -118.9663074,-118.5138948,34.0026669,34.172355`), because that
      is where those numbers live when no /info endpoint exists;
    * the request is the recorder's `ROUTE profile=... model=lambda-N.json` line, the same profile and the
      same custom-model bytes an HTTP /route body would carry - emitted by the SWIFT CLI itself
      (`ops/plan --emit-model`), which the parity golden holds byte-for-byte to the Worker's buildCustomModel;
    * the response is the GeoJSON path, the path details and the times GraphHopper returned, written into
      the documented points_encoded=false /route shape, and EVERY fixture carries the deviation in its own
      envelope field rather than in prose: the envelope is the recorder's, not graphhopper-web's.
  Nothing here is a stub, nothing here is hand-written geometry, and no claim is made that a server answered.
  The served-graph run against a real HTTP surface is T-0221, behind T-0209, and this task's transport
  (Sources/ScenicPlanCLI/GraphHopperRouteSource.swift) is deliberately untested against one - R4 THIRD.

  THE THREE PRE-PUSH CHECKS the panel named, each run rather than assumed:
    * the executable's sources live under Sources/ - Sources/ScenicPlanCLI/{main.swift,PlanArguments.swift,
      GraphHopperRouteSource.swift}, so P-SRC-01's import ban (`grep -rEn ... Sources/`) reads them; the
      three import Foundation, Dispatch, ScenicKit, Handoff and FoundationNetworking and nothing banned.
      `bash ops/check-pins --source-only` is the measurement, quoted in the acceptance block.
    * URLSession's Linux home is behind `#if canImport(FoundationNetworking)` (GraphHopperRouteSource.swift
      lines 4-6), in the CLI target only - ScenicKit never imports it, so linux-core's ScenicKit build is
      unchanged.
    * P-PLAT-01's `grep -q 'iOS("18.4")' Package.swift` survives the serial edit: the platforms line is
      untouched at Package.swift:10, and the pin is green in the ok=15 run below. The serial edit added a
      product and a target and moved no existing line.

  RED-FIRST, BY NAME, ON THE SHIPPING SYMBOL. R3 promised the guards would be removed from ScenicPlanner.plan
  - the entry point ops/plan runs - rather than asserted over a helper. Both were, one at a time, with the
  file restored after each (`swift test --scratch-path .build/T0182 --filter ScenicPlannerMetaTests`):

      guard chosen.duration <= ceiling else {   ->   guard true else {      exit=1
        X Test "a solver that answers lambda 8 fails the budget ceiling" recorded an issue at
          ScenicPlannerMetaTests.swift:106:9: Expectation failed: an error was expected but none was thrown
          and "ScenicPlan(... outcome: BudgetOutcome(lambda: 8.0, duration: 3360.0, ceiling: 3300.0 ...))"
          was returned
        X Test run with 4 tests in 1 suite failed after 0.005 seconds with 1 issue.

      guard overlap < RouteDifference.maximumOverlap else {   ->   guard true else {      exit=1
        X Test "a solver that answers lambda 0 fails actually different" recorded an issue at
          ScenicPlannerMetaTests.swift:91:9: Expectation failed: an error was expected but none was thrown
          and "ScenicPlan(... overlapWithFastest: 1.0)" was returned
        X Test "a route with no way ids is refused, not waved through as different" recorded an issue at
          ScenicPlannerMetaTests.swift:127:9: ... "ScenicPlan(... table: rows: [Row(wayId: nil ...)],
          overlapWithFastest: 1.0)" was returned
        X Test run with 4 tests in 1 suite failed after 0.003 seconds with 2 issues.

  The second removal takes TWO named tests down, which is the point of the fourth meta-test 3f340dd added:
  the no-way-id route is refused by the same guard, so the empty-set rule cannot become a vacuous green.
  `git status --short` after the run lists neither source file: both were restored.

  THE POPULATION, RUN, not merely shipped. ops/mutate/plan.py's `--only` now takes a comma-separated list of
  name fragments (the uncommitted change this session inherited, committed here) because the whole table is
  one run of minutes on this box and a run abandoned halfway reports nothing at all. Both halves, warm
  scratch .build/T0182:

      --only difference/,custom-model/,table/      caught 8 of 8   trapped 0 compile-only 0 MISSED 0 skipped 0   (3m43s)
      --only waypoints/,planner/,decode/,report/   caught 9 of 9   trapped 0 compile-only 0 MISSED 0 skipped 0   (2m14s)

  17 of 17 CAUGHT, each by a named test failing; no TRAP, no COMPILE-ONLY, no SKIP, so no anchor in the table
  is stale. `--prove-floor` refuses all three ways and accepts the shipped table:

      an empty population          REFUSED   0 mutations, expected at least 10
      one mutation                 REFUSED   1 mutations, expected at least 10
      a subject nothing mutates    REFUSED   Sources/ScenicKit/Plan/PlanFailure.swift is declared a subject and mutated by nothing
      the shipped table            accepted

  (the third arm's subject was RoutePath.swift, which the table DOES mutate, so the arm was passing for the
  wrong reason - it now uses PlanFailure.swift, which is allowlisted rather than populated and is exactly the
  defect shape the arm refuses: a module declared into coverage. That is the other uncommitted change.)

  THE LOCK THE HEADER CLAIMED AND THE TREE DID NOT HAVE. c29b494 added `exclusive: [root-package]` to the
  header and reasoned about it at length; nobody wrote queue/LOCKS/root-package.lock, because this task was
  claimed BEFORE the exclusive: line existed and nothing re-ran the claim. `bash ops/queue-check` found it -
  "declares exclusive [root-package] but queue/LOCKS/root-package.lock is not held" - which is the gate
  doing its job against its own owner. The lock is written here in queue.py's format
  (`T-0182 agent/claude-opus-5 2026-09-19T20:29:55Z`) and queue-check is OK (215 tasks). It is released when
  this task moves out of claimed/, by the same `queue.py review` that moves it.

  TWO THINGS THIS BRANCH DID NOT CAUSE, recorded rather than quietly worked around:
    * `bash ops/lib/check-lock-lifecycle` exits FAIL on this branch AND on a clean main checkout at a03c965,
      identically - "FAIL: review did not release the lock" and "FAIL: review refused a task that holds no
      locks". It is not in this task's acceptance block, this branch does not touch queue.py's review path,
      and it fails the same before and after the only queue file this branch adds. RECORDABLE, not fixed
      here.
    * P-SAFE-05 was seen FAILING ONCE in this session's first `ops/check-pins --source-only`, and the cause
      was mine, not the pin's data: I ran that gate and a `swift test --scratch-path .build/T0182` as two
      parallel calls against the SAME package, and SwiftPM cannot have two builds in one package at once.
      Each of the pin's three conjuncts was then checked alone - 'Naval Observatory' present in
      Tests/Fixtures/solar/oracle.json, 35 SolarFixture(name: entries (>= 20), and
      `swift test --filter SolarFixtureTests` "Test run with 6 tests in 1 suite passed" - and the gate,
      re-run serially, is ok=15 failed=0. A P-SAFE-* pin that failed OPEN buys a review round under
      CLAUDE.md, so it is stated here in full rather than as a re-run. The underlying wart is real and is a
      RECORDABLE: P-SAFE-05's assertion runs `swift test` with NO `--scratch-path`, which CLAUDE.md requires
      of every swift build on this shared box, so the pin is racy against any other agent building here.
