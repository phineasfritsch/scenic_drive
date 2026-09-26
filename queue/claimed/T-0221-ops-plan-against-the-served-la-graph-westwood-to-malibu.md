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
- 2026-09-26T16:54:13Z STAGE C - THE THREE PLANS (agent/claude-opus-5). At 6ef7ced, per pair:
  `SCENIC_PLAN_SCRATCH=.build/T0221 bash ops/plan <O> <D> 25 --recorded Tests/Fixtures/t0221/<pair>`, exit 0 each,
  stdout to the main checkout's gitignored services/routing/work/t0221/plan-<pair>.txt - the FULL per-edge tables
  live there (sha256 prefixes: westwood-malibu f8f1a5c1e726d668, westwood-woodland-hills 1a6d816d375506b4,
  santa-monica-topanga fe48c0e125717b27). The same command over the FULL recording (rec/<pair>/, all ten lambdas)
  is `cmp`-equal for all three (`SUBSET==FULL <pair>`), so the committed subset is the plan's whole input (R3).
  Graph: GRAPH_DIGEST eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb (R2; there is no /info, R1).
  Table summaries are `python services/routing/work/t0221/runs.py plan-<pair>.txt` (main checkout, gitignored):
  rows are the plan's own table rows, consecutive way runs in route order; R4's run is a maximal sequence of rows
  whose highway is residential, living_street or service. T-0209 V3's threshold: such a run with every edge
  scored < 7 and longer than 800 m is a rat-run.
  (1) WESTWOOD -> MALIBU `bash ops/plan 34.0669,-118.4399 34.0356,-118.6894 25 --recorded Tests/Fixtures/t0221/westwood-malibu`
      ROUTER recorded westwood-malibu
      PLAN origin=34.06690,-118.43990 destination=34.03560,-118.68940 budget=25m00s
      LAMBDA 3.25 evaluations=6 used-budget=false monotonicity-violated=false
      ETA fastest=27m47s returned=31m44s ceiling=52m47s distance=29214.7m
      OVERLAP jaccard=0.505 required<0.600
      TABLE rows=166 columns=way,highway,scenic_score,metres,seconds (seconds apportioned by metres; the scoring terms are not in the graph)
      WAY         HIGHWAY         SCORE  METRES     SECONDS
      909518997   tertiary        5      332.7      21.7            (first of 166 rows)
      1073769540  tertiary        2      374.5      24.4            (last)
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.03560,-118.68940&waypoint=34.05041,-118.48215&waypoint=34.05287,-118.50255&waypoint=34.04804,-118.54339&waypoint=34.04207,-118.56917&waypoint=34.03946,-118.58947&waypoint=34.03721,-118.60854&waypoint=34.03719,-118.63819&waypoint=34.03818,-118.65069&waypoint=34.03942,-118.66089&mode=driving
      ROWS 166 metres=29214.6 seconds=1903.9
      BY_CLASS trunk rows=49 12427.8 m mean_score=0.00; secondary rows=74 12116.1 m mean_score=4.65; tertiary rows=20 3001.7 m mean_score=3.75; primary rows=23 1669.0 m mean_score=3.42
      MEAN_SCORE(metres-weighted) 2.51 ; score>=7 metres=616.1
      LONGEST_MINOR_RUN 0.0 m (none)
  P-SAFE-04: returned 1904.238 s (lambda-3.25.json paths[0].time 1904238) <= fastest 1667.261 s + 1500 s =
  3167.261 s - HOLDS (31m44s <= 52m47s). Lambda 3.25, visited 0, 4 (3578.870 s, over), 2 and 3 (both ARE the
  fastest route), 3.5 (over), 3.25. Longest residential/living_street/service run: NONE - the route has no such
  row (0 m < 800 m; no rat-run).
  (2) WESTWOOD -> WOODLAND HILLS `bash ops/plan 34.0669,-118.4399 34.1684,-118.6058 25 --recorded Tests/Fixtures/t0221/westwood-woodland-hills`
      LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false
      ETA fastest=20m09s returned=38m26s ceiling=45m09s distance=30333.0m
      OVERLAP jaccard=0.006 required<0.600
      TABLE rows=195 ...; first row 909518997 tertiary 5 90.8 6.9; last row 1092910876 primary 1 17.5 1.3
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.16840,-118.60580&waypoint=34.08536,-118.43525&waypoint=34.09972,-118.44349&waypoint=34.10963,-118.44655&waypoint=34.13142,-118.44889&waypoint=34.13770,-118.49706&waypoint=34.16322,-118.53754&waypoint=34.16262,-118.57024&waypoint=34.15881,-118.58836&waypoint=34.15692,-118.60583&mode=driving
      ROWS 195 metres=30332.9 seconds=2305.4
      BY_CLASS secondary rows=90 23431.3 m mean_score=5.85; primary rows=92 5515.6 m mean_score=2.86; tertiary rows=13 1386.0 m mean_score=4.52
      MEAN_SCORE(metres-weighted) 5.25 ; score>=7 metres=5959.3
      LONGEST_MINOR_RUN 0.0 m (none)
  P-SAFE-04: returned 2305.902 s (lambda-7.75.json 2305902) <= 1208.634 + 1500 = 2708.634 s - HOLDS (38m26s <=
  45m09s). Lambda 7.75 (0, 4, 6, 7, 7.5, 7.75, none over; lambda 3.5 onward is one route). Longest minor run:
  NONE (0 m; no rat-run).
  (3) SANTA MONICA -> TOPANGA `bash ops/plan 34.0195,-118.4912 34.0676,-118.5957 25 --recorded Tests/Fixtures/t0221/santa-monica-topanga`
      LAMBDA 7.75 evaluations=6 used-budget=false monotonicity-violated=false
      ETA fastest=20m14s returned=22m26s ceiling=45m14s distance=20358.6m
      OVERLAP jaccard=0.453 required<0.600
      TABLE rows=86 ...; first row 819770629 service 0 6.4 0.4; last row 723963657 service 0 174.9 11.6
      WAYPOINTS 9 of max 9
      URL https://maps.apple.com/directions?source=34.01950,-118.49120&destination=34.06760,-118.59570&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&mode=driving
      ROWS 86 metres=20358.2 seconds=1346.1
      BY_CLASS tertiary rows=26 7189.7 m mean_score=6.08; primary rows=16 6554.9 m mean_score=7.20; trunk rows=38 5961.7 m mean_score=0.00; secondary rows=1 409.2 m mean_score=4.00; service rows=4 223.7 m mean_score=0.00; residential rows=1 19.0 m mean_score=2.00
      MEAN_SCORE(metres-weighted) 4.55 ; score>=7 metres=8821.9
      LONGEST_MINOR_RUN 174.9 m over 1 row(s): service 723963657 score 0 174.9 m
      LONGEST_V3_RUN(score<7) 174.9 m over 1 row(s): service 723963657 score 0 174.9 m
  P-SAFE-04: returned 1346.010 s (lambda-7.75.json 1346010) <= 1213.650 + 1500 = 2713.650 s - HOLDS (22m26s <=
  45m14s). Lambda 7.75 (0, 4, 6, 7, 7.5, 7.75, none over; lambda 0 through 3.5 ARE the fastest route). Longest
  minor run 174.9 m, way 723963657 (highway=service, unnamed, score 0 - `osmium getid` over la-tagged.osm.pbf),
  the route's LAST row, the approach to the destination point; 174.9 < 800 m - NOT a rat-run. The one
  residential row is 19.0 m of way 384819177 (7th Street, score 2 - the way T-0244 left at 19.0 m), its own run.
- 2026-09-26T16:54:13Z STAGE D - THE LINUX TEST, RED THEN GREEN (agent/claude-opus-5).
  Tests/ScenicPlanCLITests/PlanCLILARecordingTests.swift (new, 150 lines, LF): two tests x the three pairs, each
  driving `PlanCommand.run(PlanArguments.parse([O, D, "25", "--recorded", dir]))` - main.swift's call (R6).
  `theReturnedRouteIsInsideTheCeiling`: the printed lines EQUAL "ROUTER recorded <pair>" + report() of the plan
  recomputed with the literal 25 * 60 s; the LAMBDA and ETA lines EQUAL the literals quoted in (1)-(3);
  plan.fastestDuration and plan.outcome.duration EQUAL fastest.json's and the chosen file's raw `paths[0].time`
  / 1000 read by JSONSerialization (not RoutePath's decoder); both durations <= fastest + 1500 s.
  `thePrintedURLIsTheHandoffOfThePlan`: the URL line EQUALS "URL " + AppleMapsDirections(source: O,
  destination: D, waypoints: plan.waypoints).url() with O and D typed as Coordinates in the test, AND EQUALS the
  literal quoted in (1)-(3); waypoints <= 9 and the literal's `&waypoint=` count == plan.waypoints.count.
  GREEN: `swift test --scratch-path .build/T0221 --filter PlanCLILARecordingTests` -> `Test run with 2 tests in
  1 suite passed`. RED - three mutants of SHIPPING code, each applied, run, restored by
  services/routing/work/t0221/mutants.py (main checkout, gitignored; log mutants.log; `git diff --stat` empty
  after):
      MUTANT M1 an over-ceiling candidate is eligible (LambdaSearch) and the planner guard lets it through: exit=1 RED
          (LambdaSearch `if d <= ceiling, best == nil` -> `ceiling * 2`; ScenicPlanner `guard chosen.duration <= ceiling` -> `ceiling * 2`)
          FAILED (plan.outcome.duration → 3578.87) == (returned → 1904.238)
          FAILED (plan.outcome.duration → 3578.87) <= (fastest + Self.budgetSeconds → 3167.261)
          × Test run with 2 tests in 1 suite failed after 0.356 seconds with 5 issues.
      MUTANT M2 PlanCommand drops the last decision point from the URL: exit=1 RED
          × Test run with 2 tests in 1 suite failed after 0.320 seconds with 6 issues.   (lines.last != recomputed and != literal, x3)
      MUTANT M3 PlanWaypoints.maximum 9 -> 8 (printed == recomputed; only the Log literal sees it): exit=1 RED
          FAILED (pair.url.components(separatedBy: "&waypoint=").count - 1 → 9) == (plan.waypoints.count → 8)   (x3)
          × Test run with 2 tests in 1 suite failed after 0.279 seconds with 6 issues.
      ORIGINAL restored: exit=0 GREEN √ Test run with 2 tests in 1 suite passed after 0.308 seconds.
  M1 is red on westwood-malibu ONLY: it is the one recording holding routes over its ceiling (lambda 3.5 and 4,
  3578.870 s); the other two pairs never cross 45 min, so no ceiling mutant can show on them - P-SAFE-04's
  witness here is one pair, and the general ceiling stays LambdaSearchTests'. M3 is the mutant the printed ==
  recomputed half cannot see (both sides share PlanWaypoints); the Log literal is what turns it red.
- 2026-09-26T16:54:13Z FOR THE HUMAN (agent/claude-opus-5). Three drives planned over the whole-LA graph with 25
  extra minutes allowed on each. Open a link on the phone and Apple Maps shows the route with its nine stops in
  order. The times are estimates with no traffic data. Road names are OpenStreetMap's for the ways the route
  uses (`osmium getid` over la-tagged.osm.pbf; stretches under 300 m left out).
  1. Westwood to Malibu
     https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.03560,-118.68940&waypoint=34.05041,-118.48215&waypoint=34.05287,-118.50255&waypoint=34.04804,-118.54339&waypoint=34.04207,-118.56917&waypoint=34.03946,-118.58947&waypoint=34.03721,-118.60854&waypoint=34.03719,-118.63819&waypoint=34.03818,-118.65069&waypoint=34.03942,-118.66089&mode=driving
     Wilshire and San Vicente, then Sunset Boulevard through Brentwood and the Palisades to the coast and 12 km
     of Pacific Coast Highway to Civic Center Way: 31 min 44 s, about 4 minutes more than the fastest way
     (27 min 47 s, San Vicente and Channel Road to PCH).
  2. Westwood to Woodland Hills
     https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.16840,-118.60580&waypoint=34.08536,-118.43525&waypoint=34.09972,-118.44349&waypoint=34.10963,-118.44655&waypoint=34.13142,-118.44889&waypoint=34.13770,-118.49706&waypoint=34.16322,-118.53754&waypoint=34.16262,-118.57024&waypoint=34.15881,-118.58836&waypoint=34.15692,-118.60583&mode=driving
     Hilgard and Sunset to Beverly Glen, up to Mulholland Drive for about 6 km along the ridge, down Calneva and Hayvenhurst into
     Encino, Ventura Boulevard west, then Wells Drive and Dumetz Road to Topanga Canyon Boulevard: 38 min 26 s,
     about 18 minutes more than the fastest way (20 min 9 s on the 405 and the 101).
  3. Santa Monica to Topanga
     https://maps.apple.com/directions?source=34.01950,-118.49120&destination=34.06760,-118.59570&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&mode=driving
     Lincoln, Montana and 4th Street to San Vicente, down Entrada Drive and Channel Road to PCH, then Topanga
     Canyon Boulevard, Fernwood Pacific Drive and Tuna Canyon Road: 22 min 26 s, about 2 minutes more than the
     fastest way (20 min 14 s by the California Incline); from PCH on, the two are the same road.
- 2026-09-26T17:24:37Z FINAL PRE-REVIEW - the acceptance block re-quoted on the merged head (agent/claude-opus-5).
  `git fetch origin && git merge --no-edit origin/main` -> `Already up to date.` (origin/main is 74b5f4f, the
  claim commit, an ancestor of HEAD). Re-run bare at 4831a16:
      swift test --scratch-path .build/T0221 -> exit 0, `Test run with 348 tests in 50 suites passed` (XCTest: `Executed 0 tests`)
      bash ops/plan <O> <D> 25 --recorded Tests/Fixtures/t0221/<pair>, x3 -> exit 0 each, stdout `cmp`-IDENTICAL to stage C's (sha256 f8f1a5c1e726d668 / 1a6d816d375506b4 / fe48c0e125717b27)
      bash ops/lib/check-line-cap -> exit 0, `P-SRC-02: 123 Swift files tracked (Sources=45, Tests=54, apps/ios=24), none over 300 lines`
      bash ops/lib/check-exec-bits -> exit 0, `P-OPS-01: 100 files, 23 required present, all modes correct`
      bash ops/queue-check -> exit 0, `QUEUE OK (237 tasks)`
      bash ops/check-pins --source-only, FIRST run -> exit 1, `PINS ok=14 skipped=16 pending=1 expired=0 failed=1 tier=linux source-only`
          - P-SAFE-05 (its `swift test --filter SolarFixtureTests` into the worktree's DEFAULT .build, cold; output `(none)`)
      swift test --filter SolarFixtureTests (that assertion's command, bare, right after) -> exit 0, `Test run with 6 tests in 1 suite passed`
      bash ops/check-pins --source-only, SECOND run -> exit 0, `PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only`
  This branch touches no solar source, test or fixture. The first run's cause is NOT established (the box was
  running two other pins/mutation jobs at the time); it is recorded here, not explained away.
  Not run, per the orchestrator: `bash ops/test` and the full `bash ops/check-pins` (this task's verify: list);
  CI runs its Linux tier on the PR.
  ACCEPTANCE, re-quoted:
  (A1) "ops/plan run once against the served LA graph (T-0209's import of T-0208's whole-LA tagged PBF; /info's
  graph hash quoted) for Westwood -> Malibu at +25: the Apple Maps URL (<= 9 waypoints), the fastest ETA, the
  returned ETA (<= fastest + 25 min, asserted), the per-edge table and the lambda chosen quoted in the Log; the
  longest residential/service run on the returned route quoted (m, way ids) against T-0209's ruled threshold"
     MET AS RULED (R1, R2): "served" is T-0209's graph reached in-process by the committed recorder and replayed
     by `ops/plan --recorded`; the hash is GRAPH_DIGEST eb43090a...18eb, because no /info exists. STAGE C (1):
     the URL with 9 waypoints; fastest 27m47s; returned 31m44s <= ceiling 52m47s, ASSERTED by
     PlanCLILARecordingTests over the raw 1904.238 <= 1667.261 + 1500 s (seen red by mutant M1); lambda 3.25;
     the table's summary lines quoted, the full 166-row table in plan-westwood-malibu.txt; longest
     residential/living_street/service run NONE (0 m), against T-0209 V3's 800 m / score < 7 threshold.
  (A2) "the same for T-0209's other two pairs (Westwood -> Woodland Hills, Santa Monica -> Topanga) with the three
  URLs handed to the owner in one FOR THE HUMAN block - the owner's own commute pair is T-0013's (M4), added here
  only when the owner names it"
     MET: STAGE C (2) Woodland Hills - 9 waypoints, fastest 20m09s, returned 38m26s <= 45m09s, lambda 7.75,
     longest minor run NONE; (3) Topanga - 9 waypoints, fastest 20m14s, returned 22m26s <= 45m14s, lambda 7.75,
     longest minor run 174.9 m (way 723963657, service, score 0) < 800 m, not a rat-run. Both asserted by the same
     test. The three URLs are in the one FOR THE HUMAN entry (16:54:13Z). The owner has not named a commute pair;
     none is added.
  NOT CLAIMED: nobody has driven these routes yet; the ETAs are GraphHopper's estimates with no traffic data; the
  drive itself (plan:284's exit) is the owner's.
