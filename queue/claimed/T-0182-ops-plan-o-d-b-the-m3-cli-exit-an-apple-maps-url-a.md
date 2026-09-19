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
