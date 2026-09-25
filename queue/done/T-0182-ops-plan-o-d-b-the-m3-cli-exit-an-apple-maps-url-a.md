---
id: T-0182
title: ops/plan <O> <D> <B> - the M3 CLI exit: an Apple Maps URL and the per-edge term table for an LA origin and destination against the served LA graph
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T17:53:17Z
lease_expires_at: 2026-09-20T01:53:17Z
worktree: .worktrees/T-0182
branch: task/T-0182
exclusive: [root-package]
touches: [ops/plan, ops/lib/, ops/mutate/, Sources/, Package.swift, services/api/src/, Tests/]
pins_affected: []
reviewer: agent/rv1-pr124
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
- 2026-09-19T20:54:04Z THE ACCEPTANCE BLOCK, WHOLE, ON THE MERGED HEAD, by agent/claude-opus-5. `git fetch origin` and
  `git merge --no-edit origin/main` were the LAST steps before the push, and main moved WHILE they ran: the
  first merge took 2fce36b (T-0217's extractadapter work, T-0224 claimed) and conflicted in
  ops/lib/check-mutate-population.py - main added `extractadapter.py` to DRIVERS, this branch added
  `plan.py`, and the resolution is the UNION of the two, alphabetical, with both sides' COVERED_FLOOR
  entries kept (the floor reads 32 now, was 30 on main and 30+plan's 7 here). `git merge-base --is-ancestor`
  then still exited 1, because origin/main had become 6f20c12 (T-0227, T-0228 filed) in the minutes since
  the fetch - the PR #119 lesson, live - so it was fetched and merged again. HEAD's second parent is
  6f20c12 and the block below was measured after that merge, not before.

      $ swift build --scratch-path .build/T0182
      Build complete! (1.83s)                                             exit 0
      (the root package including the new executable target ScenicPlanCLI / product scenic-plan)

      $ swift test --scratch-path .build/T0182
      Test run with 315 tests in 42 suites passed after 0.345 seconds.    exit 0
      (the whole Linux suite; main's own linux-core count at 1303/0 is xcodebuild's, not this one -
      315 here is swift-testing's test count, and it LOSES nothing: 299 on the branch point plus this
      task's 16)

      $ swift test --scratch-path .build/T0182 --filter "ScenicPlannerMetaTests|ScenicPlanGoldenTests|LambdaCustomModelParityTests"
      Suite "Scenic planner meta-tests" passed after 0.003 seconds.
      Suite "Lambda custom model parity" passed after 0.008 seconds.
      Suite "Scenic plan golden" passed after 0.075 seconds.
      Test run with 16 tests in 3 suites passed after 0.076 seconds.      exit 0
      THE META-TESTS BY NAME - "a solver that answers lambda 0 fails actually different", "a solver that
      answers lambda 8 fails the budget ceiling", "a route with no way ids is refused, not waved through as
      different", "a different route inside the ceiling is planned, through the real bisection". Red-first
      for the first three is quoted in the entry above, each guard removed from ScenicPlanner.plan.
      THE GOLDEN BY NAME - Suite "Scenic plan golden": "the recorded canyon pair plans at lambda 7.75
      inside the ceiling", "the report says what the run said", "the table is one row per road under one
      score, over the real path details", "the handoff URL pins nine decision points along the recorded
      route", "the pin cap ScenicKit picks by is the cap Handoff enforces", "T-0213's own pair is refused
      because the canyon has one road", "an unrecorded lambda is refused rather than answered with a
      neighbour".

      $ bash ops/plan
      usage: ops/plan <origin lat,lon> <destination lat,lon> <extra-minutes> (--router <url> | --recorded <dir>) [--max-evaluations N]
      example: ops/plan 34.0392,-118.5836 34.0944,-118.6019 25 --router http://127.0.0.1:8989
                                                                          exit 2

      $ SCENIC_PLAN_SCRATCH=.build/T0182 bash ops/plan 34.0944,-118.6013 34.0365,-118.6870 25 --recorded Tests/Fixtures/t0182/plan-pair
      ROUTER recorded plan-pair
      PLAN origin=34.09440,-118.60130 destination=34.03650,-118.68700 budget=25m00s
      LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false
      ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m
      OVERLAP jaccard=0.112 required<0.600
      TABLE rows=58 columns=way,highway,scenic_score,metres,seconds
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.09440,-118.60130&...&mode=driving   exit 0
      (67 lines of stdout, identical to the 18:30 recording above, re-run here on the merged head: the
      ceiling holds with 5m23s to spare and the returned route shares 11% of its edges with the fastest)

      $ python ops/lib/check-mutate-population.py
      P-PROC-06: every added module is covered or allowlisted; the floor of 32 holds   exit 0

      $ bash ops/check-pins --source-only
      PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only         exit 0
      (the Linux compile gate over Package.swift and P-SRC-01's import ban over Sources/, which now reads
      Sources/ScenicPlanCLI as well; P-PLAT-01's iOS("18.4") grep is among the 15)

      $ bash ops/lib/check-line-cap
      P-SRC-02: 108 Swift files tracked (Sources=42, Tests=45, apps/ios=21), none over 300 lines   exit 0

      $ bash ops/lib/check-exec-bits
      P-OPS-01: 87 files, 23 required present, all modes correct                        exit 0
      (ops/plan is 100755 in the index - `git ls-files -s ops/plan` - and ops/mutate/plan.py is 100644)

      $ bash ops/queue-check
      QUEUE OK (221 tasks)                                                              exit 0

      $ git merge-base --is-ancestor origin/main HEAD ; echo $?
      0

      $ wc -l <every file this branch touches>   (git diff --name-only origin/main HEAD, 40 paths)
          56 Package.swift
          93 Sources/ScenicKit/Plan/LambdaCustomModel.swift
          55 Sources/ScenicKit/Plan/PlanFailure.swift
         130 Sources/ScenicKit/Plan/PlanTable.swift
          39 Sources/ScenicKit/Plan/PlanWaypoints.swift
          55 Sources/ScenicKit/Plan/RecordedRouteSource.swift
          53 Sources/ScenicKit/Plan/RouteDifference.swift
         138 Sources/ScenicKit/Plan/RoutePath.swift
          26 Sources/ScenicKit/Plan/RouteSource.swift
         107 Sources/ScenicKit/Plan/ScenicPlan.swift
         102 Sources/ScenicKit/Plan/ScenicPlanner.swift
         128 Sources/ScenicPlanCLI/GraphHopperRouteSource.swift
         107 Sources/ScenicPlanCLI/PlanArguments.swift
          72 Sources/ScenicPlanCLI/main.swift
          11 Tests/Fixtures/custom-model/PROVENANCE.txt
          20 Tests/Fixtures/custom-model/lambda-0.json
          20 Tests/Fixtures/custom-model/lambda-1.json
          20 Tests/Fixtures/custom-model/lambda-2.5.json
          20 Tests/Fixtures/custom-model/lambda-7.75.json
          20 Tests/Fixtures/custom-model/lambda-8.json
         214 Tests/Fixtures/t0182-recorder/Recorder.java
          32 Tests/Fixtures/t0182/plan-pair/fastest.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-0.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-4.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-6.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.5.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.75.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.json
          32 Tests/Fixtures/t0182/t0213-pair/fastest.json
          32 Tests/Fixtures/t0182/t0213-pair/lambda-0.json
         142 Tests/HandoffTests/ScenicPlanGoldenTests.swift
          91 Tests/ScenicKitTests/LambdaCustomModelParityTests.swift
         156 Tests/ScenicKitTests/ScenicPlannerMetaTests.swift
         300 ops/lib/check-mutate-population.py
          38 ops/lib/mutate-population-allowlist.json
         228 ops/mutate/plan.py
          40 ops/plan
           1 queue/LOCKS/root-package.lock
         295 services/api/src/customModel.ts
             450 queue/claimed/T-0182-ops-plan-o-d-b-the-m3-cli-exit-an-apple-maps-url-a.md (this
      file, as committed with this entry - the one measured file this commit changes, re-measured here)

  ONE THING THE BLOCK SAYS THAT NOBODY SHOULD READ PAST: ops/lib/check-mutate-population.py is now EXACTLY
  300 lines - the cap, not over it: 296 on origin/main, 298 on this branch before the merge, 300 merged,
  because the union keeps both sides' COVERED_FLOOR entries and a DRIVERS tuple that wraps to three lines.
  It is green today and the next line added to that file is a refusal; a RECORDABLE for whoever touches it
  next, not a defect of this branch.

  `git status --short` is empty. Pushing now.
- 2026-09-19T21:35:30Z THE PRE-REVIEW MUTANT PASS, RULED AND CLOSED by agent/claude-opus-5 (owner, as fixer).
  .artifacts/signoffs/t0182-mutant-pass.md over build ed9b5e4 returned one BLOCKING survivor, one recorded
  survivor and two unsupported claims. All four are closed here, in code, each red first; the rulings are
  R8-R11 and they are rulings, not notes, because three of them change what this branch ships.

  R8 - THE BLOCKING ONE (M1b), and what it is really about. `PlanArguments.budget` is
  `budgetMinutes * 60`, and the pass showed `* 3600` shipping with 315/315 green: `ops/plan ... 25` then
  printed `budget=25h00m00s` and `ceiling=25h17m56s` and exited 0. CLAUDE.md's invariant is over the budget
  THE USER STATED - *returned ETA <= fastest + budget. Always* - and this multiplication is the only code in
  the tool that turns what they typed into the seconds the ceiling is computed from. It was covered by no
  test (no test target named ScenicPlanCLI) and excused by an allowlist reason that NAMED the arithmetic
  ("multiplies that count by 60") as the reason no mutant was needed. Two fixes were available and I rule
  for the second: (a) move PlanArguments/GraphHopperRouteSource into a library target so ScenicKitTests can
  see them - rejected, because the symbol under test would then be reachable by a path the executable does
  not take, and moving main.swift also moves two allowlist paths for no property gained; (b) a test target
  ON the executable target, legal since SwiftPM 5.5 and verified here on Swift 6.3.3/Windows - taken. The
  smaller half of the same ruling: main.swift is top-level code, so a run of it is a run of the PROCESS and
  nothing can bind to it, which is WHY this line was unbound. Everything between parsing and printing moves
  to `PlanCommand.run(_:)` (new, Sources/ScenicPlanCLI/PlanCommand.swift, allowlisted with its reason);
  main.swift keeps only what a process can do - printing and the four exit codes - and now reads
  `for line in try PlanCommand.run(arguments) { print(line) }`. One behaviour change, deliberate: the lines
  are built whole and printed together, so a refusal at the URL no longer leaves half a plan on the
  terminal. Exit codes, usage text and the printed lines are otherwise byte-identical (the recorded run is
  re-quoted in the acceptance block below).
  THE TEST BINDS TO THE SHIPPING PATH, both halves in Tests/ScenicPlanCLITests/PlanCLIBudgetTests.swift:
  "25 extra minutes on the command line is 1500 seconds of budget" over `PlanArguments.parse` (the parse
  `ops/plan` performs), and "the ceiling ops/plan prints is the fastest route plus the minutes asked for"
  over `PlanCommand.run` - the same call main.swift makes, over the recorded pair, reading the ceiling off
  the line the terminal prints. A parse-only test would have asserted a number nothing has to use.
  RED FIRST, with the pass's own mutant (`* 60` -> `* 3600`), `swift test --filter PlanCLIBudgetTests`:
      x "25 extra minutes on the command line is 1500 seconds of budget" ... (arguments.budget -> 90000.0) == (1500 -> 1500.0)
      x "the ceiling ops/plan prints is the fastest route plus the minutes asked for" ... (eta -> "ETA fastest=17m56s returned=37m33s ceiling=25h17m56s distance=33068.9m") == "ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m"
      x "the ceiling ops/plan prints is the fastest route plus the minutes asked for" ... (plan -> "PLAN ... budget=25h00m00s").hasSuffix("budget=25m00s")
      x Test run with 2 tests in 1 suite failed after 0.106 seconds with 3 issues.
  THE POPULATION, as CLAUDE.md requires rather than as prose: the allowlist entry for
  Sources/ScenicPlanCLI/PlanArguments.swift is WITHDRAWN, the file is a SUBJECT of ops/mutate/plan.py, the
  mutant is in the table by name as `budget/minutes-are-multiplied-into-hours`, plan.py's SUITES and
  TEST_FILES now include the two CLI suites (without which the mutant would run against a filter that
  cannot see the test that kills it), and check-mutate-population.py's COVERED_FLOOR gains the module -
  32 modules to 33.

  R9 - THE CEILING'S BOUNDARY (M1a), in the planner's own guard. `<=` -> `<` survived 28/28: the mutant is
  stricter, so it can only refuse a drive that was inside the budget, which is why nothing caught it and why
  it is still a defect - a ceiling the user may not REACH is not the ceiling they were promised.
  LambdaSearch's own boundary test does not cover it; the planner's guard is a second net over a different
  value (the chosen route's own duration, re-read from the route). Closed by
  ScenicPlannerMetaTests."a route exactly on the ceiling is planned; one second over is refused", which
  drives `ScenicPlanner.plan` - not LambdaSearch - with a stub solver at both sides of the boundary, one
  second apart. Mutant in ops/mutate/plan.py by name: `planner/ceiling-refuses-a-route-exactly-on-it`.
  RED FIRST with that mutant, `swift test --filter ScenicPlannerMetaTests`:
      x "a route exactly on the ceiling is planned; one second over is refused" ... Caught error: the returned route takes 3300.0 s, over the 3300.0 s ceiling
      x Test run with 5 tests in 1 suite failed after 0.007 seconds with 1 issue.

  R10 - THE WIRE BODY (U1). GraphHopperRouteSource's doc comment claimed "what IS tested here is the request
  BODY"; `body(_:_:profile:model:)` was called by no test, and the safety property was asserted one level
  down over LambdaCustomModel's output - true of the MODEL, unsupported of the REQUEST. Ruled: the body stays
  where it is (it is the transport's, and ScenicKit may not gain an HTTP body builder), and the new CLI test
  target is what binds to it. Tests/ScenicPlanCLITests/PlanCLIRequestBodyTests.swift asserts the assembled
  bytes name neither `road_access` nor `surface` at every tenth from 0 to 8, and that the model the body
  embeds is LambdaCustomModel's bytes exactly (un-indent by the two spaces the body adds, and what is left
  is the model plus the request's closing brace), plus that the fastest request carries no custom model at
  all. RED FIRST twice, each mutant alone:
      details + "surface"          x "the bytes on the wire never name a safety gate, at any lambda" - repeated at every lambda (the run's issue list was read truncated, at six of them)
      the model inserted unindented x "the model the body embeds is LambdaCustomModel's own bytes" ... (embedded -> "{ ...

  R11 - A RUNTIME REFUSAL, NOT ONLY TESTS (U2). The Worker refuses a body that names a safety gate
  (`rejectCustomModel`, FORBIDDEN_ENCODED_VALUES = road_access, surface); this CLI, which is a client of the
  same graph, had no counterpart - the property rested on two tests of the template. It now refuses at the
  request path: `GraphHopperRouteSource.refuseSafetyGates(in:)` is the first statement of `send`, which is
  the single point both `fastest` and `scenic` reach the socket through (the one place that covers every
  request rather than every current caller), and the failure is a new `PlanFailure.modelTouchesSafetyGate`.
  ON CLAUDE.md's WHITELIST RULE, ruled explicitly because a reviewer should: that rule governs a GUARD OVER
  THE SOURCE TREE - every occurrence of an identifier must be at an approved site, never a blacklist of
  spellings of the bad write. This is not that. It is a runtime refusal over one request's bytes, and its
  two names are not a guess at how somebody might spell the defect: they are the Worker's own
  FORBIDDEN_ENCODED_VALUES, the same two encoded values, compared the same way - whole body,
  case-insensitively, substring not word, so `road_access_x` is refused too, exactly as customModel.ts says
  it refuses it. The WHITELIST here is the shipped template itself, which names neither and is asserted not
  to at every lambda (R10).
  RED FIRST by deleting the guard line and running the same test against a port nothing listens on:
      x "a body naming a safety gate is refused before any request is sent" ... expected error "the request body names the safety gate road_access ..." but "the router refused the request: Error Domain=NSURLErrorDomain Code=-1001" was thrown instead
      x (the same, for surface)   x Test run with 3 tests in 1 suite failed after 5.179 seconds with 2 issues.
  The 5.179 s is the point: without the refusal the request WENT OUT and the failure came back from the
  socket. GraphHopperRouteSource stays allowlisted rather than becoming a subject - it computes no number,
  and its reason is amended to name the guard and the suite that asserts it rather than to widen anything.

  RECORDABLES, one line each, not fixed here:
    * `bash ops/lib/check-lock-lifecycle` fails identically on main and on this branch ("review did not
      release the lock"); it is not in this task's acceptance block and this branch does not touch queue.py.
    * P-SAFE-05's assertion runs `swift test` with NO `--scratch-path`, which CLAUDE.md requires of every
      swift build on this shared box; the pin is racy against any other agent building here (it failed OPEN
      once this session for exactly that reason, recorded in the 20:47 entry - the orchestrator has filed it).
    * ops/lib/check-mutate-population.py is at the 300-line cap. This commit adds a COVERED_FLOOR entry
      WITHOUT adding a line, by putting it on the tuple line that held one entry where its neighbours hold
      two or three - the file's own layout, no content removed and nothing reflowed, so it is not the squeeze
      CLAUDE.md forbids. The DEBT stands unchanged: the next line that file gains is a refusal, and the fix
      is moving the allowlist reader or the DEBT table into a sibling under ops/lib, not compressing it.
- 2026-09-19T21:53:56Z THE ACCEPTANCE BLOCK, WHOLE, RE-RUN ON THE MERGED HEAD after the pre-review fix, by
  agent/claude-opus-5. `git fetch origin` and `git merge --no-edit origin/main` were the LAST steps before
  the push. main was 89753a1 ("queue: T-0229 ... filed from T-0182's Log"), eleven commits on from the
  20:54 block's 6f20c12. ONE conflict, and it is a good one to record: queue/LOCKS/root-package.lock,
  add/add, SAME task and SAME owner on both sides with different timestamps - this branch wrote
  `T-0182 agent/claude-opus-5 2026-09-19T20:29:55Z` at 5c1923e, and the orchestrator wrote
  `... 2026-09-19T21:20:08Z` on main at 7585e39 for the same reason (the exclusive was declared before
  ops/claim ever wrote the file). MAIN'S LINE WINS: main holds the lock register, and the PASS that releases
  it releases main's. ops/lib/check-mutate-population.py did NOT conflict this time (main has not touched it
  since the 20:54 merge); both sides' DRIVERS and COVERED_FLOOR entries from that merge are intact and this
  commit adds one more floor entry to them.

      $ swift build --scratch-path .build/T0182
      Build complete! (8.93s)                                              exit 0

      $ swift test --scratch-path .build/T0182
      Test run with 321 tests in 44 suites passed after 0.343 seconds.     exit 0
      (315 at the 20:54 block plus this commit's 6: two in "ops/plan budget", three in "ops/plan request
      body", one in the meta-tests; 44 suites is 42 plus the two new ones)

      $ swift test --scratch-path .build/T0182 --filter "ScenicPlannerMetaTests|ScenicPlanGoldenTests|LambdaCustomModelParityTests|PlanCLIBudgetTests|PlanCLIRequestBodyTests"
      Suite "Scenic planner meta-tests" passed after 0.004 seconds.
      Suite "Lambda custom model parity" passed after 0.007 seconds.
      Suite "ops/plan request body" passed after 0.011 seconds.
      Suite "Scenic plan golden" passed after 0.058 seconds.
      Suite "ops/plan budget" passed after 0.059 seconds.
      Test run with 22 tests in 5 suites passed after 0.060 seconds.       exit 0
      THE FOUR ADDED BY THE FIX, BY NAME - "25 extra minutes on the command line is 1500 seconds of
      budget", "the ceiling ops/plan prints is the fastest route plus the minutes asked for", "the bytes on
      the wire never name a safety gate, at any lambda", "the model the body embeds is LambdaCustomModel's
      own bytes", "a body naming a safety gate is refused before any request is sent", and in the
      meta-tests "a route exactly on the ceiling is planned; one second over is refused". Each was seen
      red, by name, in the 21:35 entry above.

      $ bash ops/plan
      usage: ops/plan <origin lat,lon> <destination lat,lon> <extra-minutes> (--router <url> | --recorded <dir>) [--max-evaluations N]
      example: ops/plan 34.0392,-118.5836 34.0944,-118.6019 25 --router http://127.0.0.1:8989
                                                                           exit 2

      $ SCENIC_PLAN_SCRATCH=.build/T0182 bash ops/plan 34.0944,-118.6013 34.0365,-118.6870 25 --recorded Tests/Fixtures/t0182/plan-pair
      ROUTER recorded plan-pair
      PLAN origin=34.09440,-118.60130 destination=34.03650,-118.68700 budget=25m00s
      LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false
      ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m
      OVERLAP jaccard=0.112 required<0.600
      TABLE rows=58 columns=way,highway,scenic_score,metres,seconds
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.09440,-118.60130&...&mode=driving   exit 0
      67 lines of stdout, the SAME 67 as the 20:54 block - the run now goes through PlanCommand.run and
      prints the same bytes. `ceiling=42m56s` is the line the new budget test reads: 17m56s + the 25
      minutes asked for, and the returned 37m33s is inside it.

      $ SCENIC_MUTATE_SCRATCH=.build/T0182 python ops/mutate/plan.py --only difference/,custom-model/,table/
      population 19 mutations over 8 modules (running 8 selected)
      caught 8 of 8   trapped 0   compile-only 0   MISSED 0   skipped 0    exit 0
      $ SCENIC_MUTATE_SCRATCH=.build/T0182 python ops/mutate/plan.py --only waypoints/,planner/,decode/,report/,budget/
      population 19 mutations over 8 modules (running 11 selected)
      CAUGHT  planner/ceiling-refuses-a-route-exactly-on-it   a named test failed (exit=1)
      CAUGHT  budget/minutes-are-multiplied-into-hours        a named test failed (exit=1)
      caught 11 of 11   trapped 0   compile-only 0   MISSED 0   skipped 0  exit 0
      19 of 19 CAUGHT, each by a named test, no TRAP, no COMPILE-ONLY, no SKIP. In HALVES, as the 20:54
      block ran them and for the same reason: the whole table is one run of minutes on this box and a run
      abandoned halfway reports nothing - and a driver killed mid-mutation leaves the tree mutated, which
      is the one state this repository must never measure from. `git status --short` was empty after each
      half. The two new names are the pass's two survivors.

      $ python ops/mutate/plan.py --prove-floor
      an empty population          REFUSED   0 mutations, expected at least 10
      one mutation                 REFUSED   1 mutations, expected at least 10
      a subject nothing mutates    REFUSED   Sources/ScenicKit/Plan/PlanFailure.swift is declared a subject and mutated by nothing
      the shipped table            accepted                                exit 0
      (the flag is --prove-floor; there is no --prove-vacuity in this driver, and the third arm IS the
      vacuity arm - a module declared into coverage that nothing mutates)

      $ python ops/lib/check-mutate-population.py
      P-PROC-06: 90 modules, 34 covered by 13 populations, 33 allowlisted, 14 added by this branch
      P-PROC-06: every added module is covered or allowlisted; the floor of 33 holds   exit 0
      (32 -> 33: PlanArguments.swift left the allowlist for the population, and PlanCommand.swift entered
      the allowlist with its reason, so the allowlist count is unchanged at 33 and the floor rose by one)

      $ bash ops/check-pins --source-only            (run ALONE - no swift build beside it: that is what
                                                      made P-SAFE-05 fail open once this session)
      PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only          exit 0

      $ bash ops/lib/check-line-cap
      P-SRC-02: 111 Swift files tracked (Sources=43, Tests=47, apps/ios=21), none over 300 lines   exit 0
      (108 -> 111: PlanCommand.swift and the two CLI test files)

      $ bash ops/lib/check-exec-bits
      P-OPS-01: 87 files, 23 required present, all modes correct                         exit 0

      $ bash ops/queue-check
      QUEUE OK (222 tasks)                                                               exit 0

      $ git merge-base --is-ancestor origin/main HEAD ; echo $?
      0

      $ wc -l <every file this branch touches>   (git diff --name-only origin/main HEAD, 42 paths)
          68 Package.swift
          93 Sources/ScenicKit/Plan/LambdaCustomModel.swift
          66 Sources/ScenicKit/Plan/PlanFailure.swift
         130 Sources/ScenicKit/Plan/PlanTable.swift
          39 Sources/ScenicKit/Plan/PlanWaypoints.swift
          55 Sources/ScenicKit/Plan/RecordedRouteSource.swift
          53 Sources/ScenicKit/Plan/RouteDifference.swift
         138 Sources/ScenicKit/Plan/RoutePath.swift
          26 Sources/ScenicKit/Plan/RouteSource.swift
         107 Sources/ScenicKit/Plan/ScenicPlan.swift
         102 Sources/ScenicKit/Plan/ScenicPlanner.swift
         154 Sources/ScenicPlanCLI/GraphHopperRouteSource.swift
         107 Sources/ScenicPlanCLI/PlanArguments.swift
          44 Sources/ScenicPlanCLI/PlanCommand.swift
          58 Sources/ScenicPlanCLI/main.swift
          11 Tests/Fixtures/custom-model/PROVENANCE.txt
          20 Tests/Fixtures/custom-model/lambda-0.json
          20 Tests/Fixtures/custom-model/lambda-1.json
          20 Tests/Fixtures/custom-model/lambda-2.5.json
          20 Tests/Fixtures/custom-model/lambda-7.75.json
          20 Tests/Fixtures/custom-model/lambda-8.json
         214 Tests/Fixtures/t0182-recorder/Recorder.java
          32 Tests/Fixtures/t0182/plan-pair/fastest.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-0.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-4.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-6.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.5.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.75.json
          32 Tests/Fixtures/t0182/plan-pair/lambda-7.json
          32 Tests/Fixtures/t0182/t0213-pair/fastest.json
          32 Tests/Fixtures/t0182/t0213-pair/lambda-0.json
         142 Tests/HandoffTests/ScenicPlanGoldenTests.swift
          91 Tests/ScenicKitTests/LambdaCustomModelParityTests.swift
         181 Tests/ScenicKitTests/ScenicPlannerMetaTests.swift
          54 Tests/ScenicPlanCLITests/PlanCLIBudgetTests.swift
          83 Tests/ScenicPlanCLITests/PlanCLIRequestBodyTests.swift
         300 ops/lib/check-mutate-population.py
          38 ops/lib/mutate-population-allowlist.json
         243 ops/mutate/plan.py
          40 ops/plan
         295 services/api/src/customModel.ts
         695 queue/claimed/T-0182-ops-plan-o-d-b-the-m3-cli-exit-an-apple-maps-url-a.md (this file, as
             committed with this entry - the one measured file this commit changes, re-measured here)
      queue/LOCKS/root-package.lock is no longer in the diff against origin/main: main carries the same
      line now, which is the conflict above, resolved. The files this fix changed are the four Swift
      sources, the two new test files, Package.swift and the three population files; the rest are the
      20:54 block's numbers, unchanged and re-measured rather than copied.

  `git status --short` is empty. The read-only verifier's four findings are closed, each red first.
  Pushing now.
- 2026-09-25T20:30:12Z REVIEW PASS by agent/rv1-pr124 (reviewer; not the owner agent/claude-opus-5, not its fixer).
  Reviewed in a detached sibling worktree at .worktrees/rv1-pr124 on 7de49bf == origin/task/T-0182, base main,
  scratch path .build/rv1-pr124. Every claim below names the command and quotes its output.

  SHAPE. `git diff --stat main...7de49bf`: `42 files changed, 3328 insertions(+), 8 deletions(-)`. NOTHING under
  apps/ios: `git diff --name-only main...HEAD | grep -c '^apps/ios'` -> `0`. No Apple-only import under Sources/:
  `grep -rnE 'import (CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/` -> no match. URLSession's
  Linux home is behind the guard, in the CLI target only: `Sources/ScenicPlanCLI/GraphHopperRouteSource.swift:4:
  #if canImport(FoundationNetworking)` / `:5: import FoundationNetworking` / `:135: URLSession.shared.dataTask`,
  and no other file under Sources/ names URLSession. The platform floor survives the Package.swift edit:
  `grep -n 'iOS("18.4")' pins/PINS.yaml` -> `58:  assertion: "grep -q 'iOS(\"18.4\")' Package.swift"`, and
  `bash ops/check-pins --source-only` runs that assertion green (below). Sizes: no file over the cap -
  `bash ops/lib/check-line-cap` -> `P-SRC-02: 111 Swift files tracked (Sources=43, Tests=47, apps/ios=21), none
  over 300 lines`, exit 0; the largest files this branch adds are `ops/lib/check-mutate-population.py` 300,
  `services/api/src/customModel.ts` 295, `ops/mutate/plan.py` 243 (`wc -l`). Modes:
  `bash ops/lib/check-exec-bits` -> `P-OPS-01: 87 files, 23 required present, all modes correct`, exit 0;
  `git ls-files -s ops/plan` -> `100755`, `ops/mutate/plan.py` -> `100644`, which is what the other twelve
  drivers under ops/mutate/ carry.

  BARE GATES. `swift build --scratch-path .build/rv1-pr124` -> `Build complete! (40.44s)`.
  `swift test --scratch-path .build/rv1-pr124` -> `Test run with 321 tests in 44 suites passed after 1.015
  seconds.` `bash ops/queue-check` -> `QUEUE OK (222 tasks)`, exit 0. `bash ops/check-pins --source-only`, run
  ALONE with no concurrent swift -> `PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only`,
  exit 0. `python ops/lib/check-mutate-population.py` -> `P-PROC-06: 90 modules, 34 covered by 13 populations,
  33 allowlisted, 14 added by this branch` / `every added module is covered or allowlisted; the floor of 33
  holds`, exit 0. `gh pr checks 124` -> `core pass 2m1s` / `pins-source-only pass 2m1s`.

  THE CLI, RUN. `bash ops/plan` with no arguments prints the usage line and exits 2 (`EXIT=2`). The recorded run,
  `bash ops/plan 34.0944,-118.6013 34.0365,-118.687 25 --recorded Tests/Fixtures/t0182/plan-pair`, exits 0 and
  prints `ROUTER recorded plan-pair` / `PLAN origin=34.09440,-118.60130 destination=34.03650,-118.68700
  budget=25m00s` / `LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false` /
  `ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m` /
  `OVERLAP jaccard=0.112 required<0.600` / `TABLE rows=58 columns=way,highway,scenic_score,metres,seconds` /
  58 rows / `WAYPOINTS 9 of max 9` / the maps.apple.com URL with nine waypoints. The ceiling holds on the face of
  it: 17m56s + 25m00s = 42m56s and the returned 37m33s is under it. The second pair refuses rather than
  answering with a neighbour: `bash ops/plan 34.0392,-118.5836 34.0944,-118.6019 25 --recorded
  Tests/Fixtures/t0182/t0213-pair` -> `ops/plan REFUSED: no recorded response at lambda 4.0`, exit 3.

  THE DEVIATION IS DISCLOSED, as R4 ruled and as this review was told to check. Every fixture's own envelope
  carries it: `Tests/Fixtures/t0182/plan-pair/fastest.json` field `recorded.envelope` reads `written by
  Tests/Fixtures/t0182-recorder/Recorder.java, NOT by graphhopper-web: this slice of the router has no HTTP
  surface (T-0209 owns it). Every NUMBER below is GraphHopper 11.0's over the real graph.`, beside
  `image: scenic-routing:t0213`, `image_id: sha256:ff123b2f...ba11`, `jar_sha256: 7931f599...fe43`,
  `graph_properties_sha256: 170bfe37bda146a51821f74fa53d9a42084e1cb3db27e2841205fe432c20b188` and
  `window_pbf_sha256: 06046be0...0090` - the same graph properties sha256 T-0213 recorded. The same field is on
  `t0213-pair/fastest.json`. The Log states it too, in R4 and in the golden's own header comment
  (Tests/HandoffTests/ScenicPlanGoldenTests.swift:13-15).

  THE OWNER'S POPULATION, RE-RUN TWICE BY THE REVIEWER on this tree, cold and then warm:
  `python ops/mutate/plan.py` -> `population 19 mutations over 8 modules` ... `caught 19 of 19   trapped 0
  compile-only 0   MISSED 0   skipped 0`, exit 0, both times, with every line CAUGHT including
  `planner/ceiling-guard-always-passes`, `planner/ceiling-is-twice-the-budget`,
  `planner/ceiling-refuses-a-route-exactly-on-it`, `budget/minutes-are-multiplied-into-hours`,
  `difference/intersection-becomes-union` and `difference/empty-sets-read-as-different`.
  `python ops/mutate/plan.py --prove-floor` -> `an empty population REFUSED 0 mutations, expected at least 10` /
  `one mutation REFUSED 1 mutations, expected at least 10` / `a subject nothing mutates REFUSED
  Sources/ScenicKit/Plan/PlanFailure.swift is declared a subject and mutated by nothing` / `the shipped table
  accepted`, exit 0.

  THREE MUTANTS OF THE REVIEWER'S OWN, none of them in the owner's table, run on .worktrees/rv1-pr124 and
  restored with `git checkout --` (`git status --short` empty after each). ALL THREE CAUGHT; no survivor.

  M1, THE GATE MUTANT - the gate's frame, not the code. In ONE edit to ops/mutate/plan.py:
  `MIN_MUTATIONS = 10` -> `19` (so no count arm can see it) AND
  `"Sources/ScenicKit/Plan/RouteDifference.swift",` deleted from SUBJECT_MODULES. The driver's own
  `--prove-floor` is BLIND to this: it prints `the shipped table accepted` with 19 mutations against a floor of
  19, exit 0 - the narrowing is invisible from inside the driver. The whitelist outside it refuses:
  `python ops/lib/check-mutate-population.py` -> exit 1, `P-PROC-06: POPULATION FLOOR - module(s) that had a
  population and no longer do:` / `  Sources/ScenicKit/Plan/RouteDifference.swift` / `A population is not
  retired by narrowing SUBJECT_MODULES.` That is P-PROC-06's floor arm doing exactly the job its own text
  claims, seen red here by a hand that did not write it.

  M2 - RouteDifference.overlap's DENOMINATOR swapped: `Double(union.count)` -> `Double(a.count)`, which makes a
  scenic route that is a strict SUPERSET of the fastest one read as different (intersection/|A| < 1 whenever A
  is bigger). CAUGHT, by name, over the real recording: `× Test "the report says what the run said" recorded an
  issue at ScenicPlanGoldenTests.swift:63:9: Expectation failed: (lines[3] -> "OVERLAP jaccard=0.207
  required<0.600") == "OVERLAP jaccard=0.112 required<0.600"` / `× Test run with 321 tests in 44 suites failed
  after 0.512 seconds with 1 issue.` The golden binds to the Jaccard NUMBER, not only to the URL.

  M3 - THE GOLDEN EDITED SO THE RETURNED ETA EXCEEDS fastest + budget: in
  Tests/Fixtures/t0182/plan-pair/lambda-7.75.json, `"time": 2253369` -> `"time": 2900000` (48m20s against a
  ceiling of 2575693 ms = 42m56s). The question this mutant was set to answer - does the golden fail, or does it
  only check the URL - is answered twice over. The ENGINE never prints a plan over the ceiling: it re-bisects
  onto a route it measured as feasible, and the golden dies on the numbers:
  `× Test "the report says what the run said" recorded an issue at ScenicPlanGoldenTests.swift:61:9: Expectation
  failed: (lines[1] -> "LAMBDA 7.50 evaluations=6 used-budget=true monotonicity-violated=false") == "LAMBDA 7.75
  ..."` and `× Test "the recorded canyon pair plans at lambda 7.75 inside the ceiling" recorded an issue at
  ScenicPlanGoldenTests.swift:48:9: Expectation failed: (plan.outcome.lambda -> 7.5) == 7.75`, `× Test run with
  321 tests in 44 suites failed after 0.556 seconds with 2 issues.` NO mutant of mine, and none of the owner's
  nineteen, produced a tree that prints a plan over the ceiling or sends a model naming a safety gate with
  everything green. The safety-gate refusal is on the wire path and is a runtime throw, not a comment:
  `Sources/ScenicPlanCLI/GraphHopperRouteSource.swift:54: public static let forbiddenEncodedValues =
  ["road_access", "surface"]` and `:121: throw PlanFailure.modelTouchesSafetyGate(value)`, with
  PlanFailure.modelTouchesSafetyGate a real case (PlanFailure.swift:37).

  RECORDED, NOT BLOCKING - each named with the task that should own it.
  (1) HONEST FAILURE IS UNWIRED, and the Log has it backwards. `grep -rn '0.45' Sources/` finds
  `Sources/ScenicKit/Scoring/RouteScore.swift:92: public static let honestFailureThreshold = 0.45` and NO other
  file under Sources/ reads it; PlanFailure's seven cases (PlanFailure.swift:6-42) contain no honest-failure
  case at all. So a score-8 Topanga corridor that the product should be able to call "not much pretty here" can
  only ever come back as notActuallyDifferent or as a plan. T-0230 owns wiring it; this review does not hold the
  PR for it, but the Log's framing of that refusal as the honest-failure path is wrong today and this entry says
  so on the record.
  (2) JACCARD IS OVER WAY IDS, NOT AN EDGE SET. plan:216 says edge-set; RouteDifference.wayIds reads the
  `osm_way_id` path detail (RouteDifference.swift:41). RULED SOUND, and ruled here rather than left implied:
  GraphHopper edge ids are positions in a built graph and move on every re-import, so an edge-set measure could
  not be compared across two builds of the same window, while way ids survive it; the threshold 0.6 is unchanged
  and the type's own header states the substitution. The empty-set case returns 1.0 - "not different", a refusal
  - which is the non-vacuous direction.
  (3) THE MODEL PARITY IS ONE-DIRECTIONAL. `grep -rln 'custom-model' services/api/` -> no match: the five
  Tests/Fixtures/custom-model/lambda-*.json are read by the Swift side alone
  (Tests/ScenicKitTests/LambdaCustomModelParityTests.swift). A change to
  services/api/src/customModel.ts's buildCustomModel breaks the Swift parity test and nothing on the Worker
  side, and nothing on the Worker side would tell you WHY. T-0231 owns closing that seam. The only Worker edit
  on this branch is the CustomModelError parameter-property rewrite (same field, same `readonly`, same value,
  assigned in the body so node's strip-only mode can run the module) - `gh pr checks 124` has `core pass`.
  (4) ORIGIN/MAIN IS NOT AN ANCESTOR OF THE REVIEWED HEAD. `git merge-base --is-ancestor origin/main 7de49bf`
  exits non-zero: main has moved two commits since this branch's last merge (394f0b6), 969e082 and 5df0b35.
  `git diff --name-only $(git merge-base origin/main 7de49bf)..origin/main` is SEVEN files, all of them queue
  bookkeeping - queue/LOCKS/floors.lock and six task files under queue/backlog/ and queue/ready/ - and nothing
  under ops/, pins/, Sources/, services/ or Tests/. The gate set this sign-off was bought on IS main's current
  gate set, so CLAUDE.md's rule is satisfied in substance; the drift is recorded here because it is real and the
  orchestrator merges, not this reviewer.
  (5) `ops/mutate/plan.py` SILENTLY IGNORES AN UNKNOWN FLAG. `python ops/mutate/plan.py --prove-vacuity` (the
  spelling this review was handed; the driver's flag is `--prove-floor`) does not refuse - argv is scanned for
  known flags only (plan.py:120-128), so it fell through to a full fifteen-minute mutation run that looks like
  a vacuity proof and is not one. It exits 0 with `caught 19 of 19`, which is a true statement about a different
  question. Small, real, and the same shape as the defects this repository keeps filing; worth its own task
  against ops/mutate/*.py as a class rather than this one driver.

  VERDICT: PASS. PR #124 is signed off. state claimed -> done, reviewer agent/rv1-pr124,
  queue/claimed/ -> queue/done/, and queue/LOCKS/root-package.lock is deleted in this same commit - the
  exclusive [root-package] lock this task took in c29b494 is released on the sign-off. The reviewer's worktree
  .worktrees/rv1-pr124 is removed. The merge is the orchestrator's.
