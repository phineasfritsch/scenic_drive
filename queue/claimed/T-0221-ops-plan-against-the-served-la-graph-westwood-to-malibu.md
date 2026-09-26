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
- 2026-09-26T15:41:41Z STAGE A LANDED - the graph copy, its digest, the jar, the recorder, the models (agent/claude-opus-5).
  `wsl -e bash services/routing/work/t0221/stage-a.sh` (main checkout, gitignored; exit 0):
      IMAGE scenic-routing:t0209 sha256:349ad6f584a19718d7c44900b13da5aced8650b53330776bc054f41da3b885dc
      9358b40710ff04bf6e287c08795af9e0fc4e7e6f68cb9fb0266debf716b092ae  edgekv_keys
      678fdf7f4e194d8b0387012aff2ebd8b8d3cce6f2d0b14227bded36883709766  edgekv_vals
      0d17354d11436e32479d92d84e7037aa7dbe5924ebbe754f4ae36b49e2d60b66  edges
      9e6c1e3872b75c0a6bc710485dd80727bb87e80e78b1f005bdac42e671ec92cb  geometry
      747b818a0ff193e8fb1ed1c6369643fbd734c99d545d6b10cc97a951583637a0  location_index
      04bacbc54e155cac2ec119fdce485ac585534735321b98e558f78d3b62c963d1  nodes
      fb29845262227854ee5a08c99e7a20bdb550240773b9d13c726262eba91e5839  properties
      786867b0a998feefdf942193ef4d9619c499790481fb5050dd4bc80d3c5d53bb  properties.txt
      GRAPH_DIGEST sha256=eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb
      ab2c7eea902c8244fc9945a6b0134c1c66b188a0339a0c78b247b5cf7c9c0848  scenic-router.jar
      d158304021aa56f2d178dd902958ee0f03a0d96a49746e041c24830fb983483c  Tests/Fixtures/t0182-recorder/Recorder.java
      -rwxrwxrwx 12974 Recorder.class
      STAGE A DONE
  GRAPH_DIGEST over the COPY (services/routing/work/t0221/graph-la) = T-0209's eb43090a...18eb to the byte, the
  per-file manifest line for line (R2 met). The jar is `docker run --rm --entrypoint cat scenic-routing:t0209
  /app/scenic-router.jar`; the recorder compiled with `javac -cp scenic-router.jar` in
  maven:3.9-eclipse-temurin-21@sha256:c2a2c585...a7d74 (services/routing/Dockerfile's own builder pin).
  MODELS: `SCENIC_PLAN_SCRATCH=.build/T0221 bash ops/plan --emit-model <l> | tr -d '\r'` for the ten lambdas of
  R3 (sha256 prefixes 0:54eb5b269914 2:c8932f734c2a 3:aaa34ea8dde2 3.25:be14e120d2b3 3.5:0941838ac56a
  4:b471285b42fe 6:b6cbb7e1971a 7:5962f42b13a6 7.5:63390aa52faa 7.75:7585c320d15b); lambdas 0, 2, 3, 3.25, 3.5,
  4, 6 and 7 `cmp`-equal T-0244's run2 files (work/t0244/models2), and 7.75 `cmp`-equals the node-printed golden
  Tests/Fixtures/custom-model/lambda-7.75.json - the model ops/plan sends IS the Worker's.
- 2026-09-26T16:33:41Z STAGE B LANDED - the three recordings (agent/claude-opus-5). The recorder run finished at
  15:45Z (stage-b.log's mtime); the session that ran it restarted before this entry, so the count lines are
  quoted now from the gitignored main-checkout services/routing/work/t0221/stage-b.log, unedited.
  `wsl -e bash services/routing/work/t0221/stage-b.sh` - the committed recorder over the graph COPY, image
  scenic-routing:t0209 as the JVM, /app/config.yml, `--models models/` (the ten ops/plan --emit-model files of
  stage A) plus car_fast; exit 0 (`stage-b exit 0`):
      PROVENANCE image_id=sha256:349ad6f584a19718d7c44900b13da5aced8650b53330776bc054f41da3b885dc jar_sha256=ab2c7eea902c8244fc9945a6b0134c1c66b188a0339a0c78b247b5cf7c9c0848 graph_digest=eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb
      graph car|RAM_STORE ... edges: 1,194,924(47MB), nodes: 951,816(11MB), bounds: -119.0609263,-117.7641001,33.6832753,34.4920674
      PAIR westwood-malibu 34.0669,-118.4399 -> 34.0356,-118.6894
      ROUTE profile=car_fast model=- time_ms=1667261 distance_m=26776.4 points=511 way_runs=144
      ROUTE profile=car_scenic model=lambda-0.json time_ms=1623696 distance_m=31140.2 points=558 way_runs=181
      ROUTE profile=car_scenic model=lambda-2.json time_ms=1667261 distance_m=26776.4 points=511 way_runs=144
      ROUTE profile=car_scenic model=lambda-3.25.json time_ms=1904238 distance_m=29214.7 points=690 way_runs=166
      ROUTE profile=car_scenic model=lambda-3.5.json time_ms=3578870 distance_m=54739.8 points=1855 way_runs=184
      ROUTE profile=car_scenic model=lambda-3.json time_ms=1667261 distance_m=26776.4 points=511 way_runs=144
      ROUTE profile=car_scenic model=lambda-4.json time_ms=3578870 distance_m=54739.8 points=1855 way_runs=184
      ROUTE profile=car_scenic model=lambda-6.json time_ms=3710979 distance_m=56683.2 points=2000 way_runs=233
      ROUTE profile=car_scenic model=lambda-7.5.json time_ms=3710979 distance_m=56683.2 points=2000 way_runs=233
      ROUTE profile=car_scenic model=lambda-7.75.json time_ms=3710979 distance_m=56683.2 points=2000 way_runs=233
      ROUTE profile=car_scenic model=lambda-7.json time_ms=3710979 distance_m=56683.2 points=2000 way_runs=233
      PAIR westwood-woodland-hills 34.0669,-118.4399 -> 34.1684,-118.6058
      ROUTE profile=car_fast model=- time_ms=1208634 distance_m=28057.6 points=380 way_runs=131
      ROUTE profile=car_scenic model=lambda-0.json time_ms=1201267 distance_m=28482.8 points=380 way_runs=127
      ROUTE profile=car_scenic model=lambda-2.json time_ms=1589578 distance_m=28003.8 points=507 way_runs=166
      ROUTE profile=car_scenic model=lambda-3.25.json time_ms=1876472 distance_m=29922.0 points=658 way_runs=166
      ROUTE profile=car_scenic model=lambda-3.5.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      ROUTE profile=car_scenic model=lambda-3.json time_ms=1876472 distance_m=29922.0 points=658 way_runs=166
      ROUTE profile=car_scenic model=lambda-4.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      ROUTE profile=car_scenic model=lambda-6.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      ROUTE profile=car_scenic model=lambda-7.5.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      ROUTE profile=car_scenic model=lambda-7.75.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      ROUTE profile=car_scenic model=lambda-7.json time_ms=2305902 distance_m=30333.0 points=752 way_runs=195
      PAIR santa-monica-topanga 34.0195,-118.4912 -> 34.0676,-118.5957
      ROUTE profile=car_fast model=- time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-0.json time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-2.json time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-3.25.json time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-3.5.json time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-3.json time_ms=1213650 distance_m=19299.9 points=652 way_runs=100
      ROUTE profile=car_scenic model=lambda-4.json time_ms=1346010 distance_m=20358.6 points=674 way_runs=86
      ROUTE profile=car_scenic model=lambda-6.json time_ms=1346010 distance_m=20358.6 points=674 way_runs=86
      ROUTE profile=car_scenic model=lambda-7.5.json time_ms=1346010 distance_m=20358.6 points=674 way_runs=86
      ROUTE profile=car_scenic model=lambda-7.75.json time_ms=1346010 distance_m=20358.6 points=674 way_runs=86
      ROUTE profile=car_scenic model=lambda-7.json time_ms=1346010 distance_m=20358.6 points=674 way_runs=86
      STAGE B DONE
  (each ROUTE line is followed in the log by its `WROTE <file> <bytes>` line, 33 in all, 14,306 to 61,037 bytes.)
  Against R3's prediction: westwood-malibu's lambda-4 (59.65 min) is over its 52.79 min ceiling as T-0244 run2
  said, so the bisection is 0, 4, 2, 3, 3.5, 3.25; the other two never break the ceiling, 0, 4, 6, 7, 7.5, 7.75.
  THE COMMITTED FIXTURES (Tests/Fixtures/t0221/<pair>/) keep fastest.json plus exactly those six lambdas per pair
  - westwood-malibu 0 2 3 3.25 3.5 4; westwood-woodland-hills and santa-monica-topanga 0 4 6 7 7.5 7.75 - each
  file `cmp`-equal to its rec/<pair>/ original (a loop of `cmp -s` printed no DIFF). Every file's `recorded`
  header carries image_id, jar_sha256 and graph_digest eb43090a...18eb (R2).
  Two facts these numbers state that the plan below inherits: on westwood-malibu lambda 2 and 3 ARE the fastest
  route (26776.4 m, 1667261 ms, the same 144 way runs), and lambda 0 on car_scenic is 43.6 s FASTER than
  car_fast (1623696 < 1667261 ms; the same shape T-0209 measured on Woodland Hills, 1201267 < 1208634 ms here).
