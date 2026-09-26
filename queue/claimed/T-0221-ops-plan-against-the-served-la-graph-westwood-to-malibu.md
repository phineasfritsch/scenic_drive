---
id: T-0221
title: ops/plan against the served LA graph: Westwood -> Malibu (T-0209's first named pair) - the URL and the per-edge table quoted in the Log, the owner drives it (plan:284's exit)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T15:21:08Z
lease_expires_at: 2026-09-27T01:21:08Z
worktree: .worktrees/T-0221
branch: task/T-0221
exclusive: []
touches: [ops/plan, ops/lib/, Tests/Fixtures/t0221/, Tests/ScenicPlanCLITests/]
pins_affected: []
reviewer: null
depends_on: [T-0182, T-0209, T-0244]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/plan run once against the served LA graph (T-0209's import of T-0208's whole-LA tagged PBF; /info's graph hash quoted) for Westwood -> Malibu at +25: the Apple Maps URL (<= 9 waypoints), the fastest ETA, the returned ETA (<= fastest + 25 min, asserted), the per-edge table and the lambda chosen quoted in the Log; the longest residential/service run on the returned route quoted (m, way ids) against T-0209's ruled threshold"
  - "the same for T-0209's other two pairs (Westwood -> Woodland Hills, Santa Monica -> Topanga) with the three URLs handed to the owner in one FOR THE HUMAN block - the owner's own commute pair is T-0013's (M4), added here only when the owner names it"
---
## Brief

Split out of T-0182 by the 10:13 panel (grounded on plan:284 and T-0209 clause 2): T-0182 ships the CLI, the
meta-tests and the golden over T-0213's real canyon graph; this task is the run against the SERVED LA graph and the
drive the owner takes. Order: T-0208 -> T-0209 -> this.

## Log
- 2026-09-19T17:49:27Z filed by agent/claude-fable-5-1 (10:13 panel, fable-grounded). Not started; after T-0182 and T-0209.
- 2026-09-19T20:26:45Z by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0): the 800 m figure copied from T-0209 clause 3 was an unmeasured predicate; now the measurement against T-0209's ruled threshold.
- 2026-09-19T20:54:38Z by agent/claude-fable-5-1 (orchestrator): the run on the returned route needs T-0209's path-details mode (added as its first clause); the pair coordinates are typed, never prose.
- 2026-09-26T03:11:50Z depends_on gains T-0244 (orchestrator): T-0209 measured a 813.9 m residential run on 7th Street, Santa Monica at lambda 8 and a non-monotone T over LA; the owner's first LA drive waits on the request-model fix.
- 2026-09-26T15:20:43Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0182, T-0209 (PR #131) and T-0244 (PR #134, af36cd3) are merged - the whole-LA graph (services/routing/work/t0209/graph-la, GRAPH_DIGEST eb43090a...18eb) and the request model without the 7th Street rat-run are on main. The graph has no HTTP surface until the VPS (T-0209 R6/R9): the author rules how ops/plan reaches it (a recording of the three pairs through the committed in-process recorder, replayed with ops/plan --recorded, is the expected path).
- 2026-09-26T15:21:08Z claimed by agent/claude-opus-5; lease until 2026-09-27T01:21:08Z
- 2026-09-26T15:25:58Z RULINGS BEFORE ANY RECORDING OR CODE (agent/claude-opus-5). Every disagreement between the
  acceptance, the Brief, the code and the box, ruled here first.
  (R1) "THE SERVED LA GRAPH". The graph has no HTTP surface until the VPS: T-0209 R6 (no /info, no server in
  services/routing) and R9 (`env | grep -c SCENIC_ROUTING_` = 0 again today). RULED: "served" means T-0209's
  whole-LA graph - the bytes the VPS will serve, identified by GRAPH_DIGEST - reached IN-PROCESS by the committed
  recorder (Tests/Fixtures/t0182-recorder/Recorder.java, unchanged) compiled against the shipped jar extracted
  from scenic-routing:t0209 (image sha256:349ad6f5...85dc), routing with that image's own /app/config.yml and
  /app/profiles, over a COPY of the graph at the MAIN checkout's gitignored services/routing/work/t0221/graph-la
  (the original services/routing/work/t0209/graph-la is never opened or moved), with the per-request models THIS
  branch's `ops/plan --emit-model <lambda> | tr -d '\r'` prints (T-0244's model, which is on main). The plan is
  then `bash ops/plan <O> <D> 25 --recorded Tests/Fixtures/t0221/<pair>` - the same ScenicPlanner, table and
  AppleMapsDirections an HTTP run would use; only the RouteSource differs. NOT claimed: an HTTP /route, a VPS, a
  served response. The JSON envelope is the recorder's (each file says so in `recorded.envelope`); every number
  in it is GraphHopper 11.0's over the whole-LA graph.
  (R2) THE GRAPH HASH. There is no /info to quote. RULED: the hash quoted is GRAPH_DIGEST (sha256 of the
  `<sha256>  <name>` manifest of every file in the graph dir, sorted by name - route_la_pairs.graph_digest's
  definition) computed over the COPY before the recording; it must equal T-0209's
  eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb or the recording does not count. The jar's
  sha256 and the image id go into every fixture's `recorded` header through --provenance.
  (R3) WHICH LAMBDAS ARE RECORDED. RecordedRouteSource REFUSES an unrecorded lambda (it never interpolates), so a
  fixture must hold every lambda the bisection visits, and the visit order depends on the recorded durations.
  Predicted from T-0244 run2 (same graph, same model): westwood-malibu 0, 4, 2, 3, 3.5, 3.25 (lambda 4 = 59.65
  min breaks the 52.79 min ceiling); westwood-woodland-hills and santa-monica-topanga 0, 4, 6, 7, 7.5, 7.75.
  RULED: the recorder routes the UNION {0, 2, 3, 3.25, 3.5, 4, 6, 7, 7.5, 7.75} for every pair into the gitignored
  work/t0221/rec/<pair>/; the committed fixture keeps fastest.json plus the lambdas the replay needs, and the
  replay over the kept subset must print byte-identical stdout to the replay over the full recording (a missing
  lambda refuses by name, so the subset proves itself).
  (R4) THE RUN AND ITS THRESHOLD. The longest residential/living_street/service run is computed from the plan's
  own TABLE (rows are consecutive way runs in route order): a maximal sequence of rows whose highway is one of
  the three, metres summed, way ids listed. It is quoted against T-0209 V3's ruled threshold: a rat-run is such a
  run with every edge scored < 7 and longer than 800 m.
  (R5) TOUCHES WIDENED: + Tests/Fixtures/t0221/ (the three recordings) and Tests/ScenicPlanCLITests/ (the Linux
  test). ops/plan and ops/lib/ stay listed and are not expected to change. The recorder is NOT in touches and is
  not changed: it already records fastest + every model in a dir, which is all this needs.
  (R6) THE TEST binds to the shipping entry point: PlanCommand.run(PlanArguments.parse([O, D, "25", "--recorded",
  dir])) - the call main.swift makes for `ops/plan`. Per pair: P-SAFE-04 as the plan's returned duration <= the
  fastest + 1500 s, where BOTH sides are read from the fixture's raw `paths[0].time` by JSONSerialization,
  independent of RoutePath's decoder, and the returned duration EQUALS the chosen lambda file's time / 1000
  exactly; the printed URL line EQUALS "URL " + AppleMapsDirections(source: O, destination: D, waypoints: the
  plan's decision points).url() AND the literal quoted in this Log; waypoints <= 9. Seen RED by a mutant before
  it is called green.
