---
id: T-0244
title: the scenic request model over LA - the anti-rat-run factor scales with lambda (7th Street, Santa Monica at lambda 8), T(lambda) monotone (distance_influence), and a lambda ladder that moves the route before lambda 8
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T07:45:04Z
lease_expires_at: 2026-09-26T17:45:04Z
worktree: .worktrees/T-0244
branch: task/T-0244
exclusive: []
touches: [Sources/ScenicKit/Budget/, Sources/ScenicKit/Routing/, Tests/ScenicKitTests/, Sources/ScenicPlanCLI/, Tests/ScenicPlanCLITests/, services/routing/tools/route_la_pairs.py, services/routing/tests/, Sources/ScenicKit/Plan/, services/api/src/customModel.ts, services/api/test/customModel.test.ts, Tests/Fixtures/custom-model/, Tests/Fixtures/t0244/, ops/mutate/plan.py, ops/lib/mutate-population-allowlist.json, services/api/test/customModelMinorClause.test.ts]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0209]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED population (T-0209, PR #131, whole-LA graph services/routing/work/t0209/graph-la, GRAPH_DIGEST eb43090a...18eb, ops/plan --emit-model models): Santa Monica (34.0195,-118.4912) -> Topanga (34.0676,-118.5957) at lambda 8 drives an 813.9 m residential run on 7th Street (ways 121941230 score 4, 384819177 score 2) - T-0207's residential x0.5 is constant while the bands grow as 1/(1+lambda), so at lambda 8 a score-4 residential edge costs 10 against 9 for a low-band arterial. RULED in the Log before code: the factor scales with lambda (or the plan's step-4 rat-run repair re-issues with the run as a zero area), and the same pair at lambda 8 has no residential/living_street/service run over 800 m scored below 7 - a test over a RECORDED route by name, RED first"
  - "T(lambda) non-decreasing over {0,1,2,4,8} on T-0209's three LA pairs: Westwood -> Woodland Hills today gives T(1) 1,201,286 ms < T(0) 1,208,634 ms because the request keeps distance_influence 30 s/km (W0 is monotone, T is not). RULED: distance_influence 0 in the scenic request model, or the plan property restated on W0 with the budget ceiling still enforced on the returned route's real ETA - either way P-SAFE-04 (ETA <= fastest + budget) holds on every returned route, a test by name"
  - "the ladder moves before lambda 8: on 2 of 3 LA pairs lambdas 0-4 return the identical route and lambda 8 doubles Westwood -> Malibu (27.8 -> 55.7 min); RULED from a measured finer ladder (e.g. {0,0.5,1,2,3,4,6,8} or a banded model) so a +20 min budget over LA has a route between the two - durations quoted per pair"
---
## Brief

From T-0209's own measurement (clauses 4 and 5 FAILED honestly, 2026-09-26) and rv1-t0209's B3. The graph is right;
the per-request model is what routes badly. The owner's first LA drives (T-0221, Westwood -> Malibu) wait on this.
A route that cuts through Santa Monica's residential grid is the plan's 'one residential rat-run ends the
relationship' failure.

## Log
- 2026-09-26T03:11:50Z filed by agent/claude-opus-5 (orchestrator) from T-0209's clauses 4-5 and its STILL OPEN 1-3.
- 2026-09-26T07:44:31Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0209 merged (PR #131, a2cf7ef); the whole-LA graph is at services/routing/work/t0209/graph-la in the main checkout and route_la_pairs.py / the route-details mode are on main.
- 2026-09-26T07:45:04Z claimed by agent/claude-opus-5; lease until 2026-09-26T17:45:04Z
- 2026-09-26T08:03:38Z DISAGREEMENTS RULED BEFORE ANY MODEL CODE, and the measurement plan (agent/claude-opus-5).
  (D1) WHERE THE MODEL LIVES. touches: named Sources/ScenicKit/Budget/ and Sources/ScenicKit/Routing/; the
  per-request model is Sources/ScenicKit/Plan/LambdaCustomModel.swift (Routing/ does not exist). And it is a PORT:
  its doc and LambdaCustomModelParityTests hold it BYTE FOR BYTE to services/api/src/customModel.ts's
  buildCustomModel through the node-printed golden Tests/Fixtures/custom-model/ (T-0182). Changing the Swift copy
  alone fails that test by name and - worse - makes ops/plan and the Worker send different models, the drift the
  golden exists to stop. RULED: touches += Sources/ScenicKit/Plan/, services/api/src/customModel.ts,
  services/api/test/customModel.test.ts, Tests/Fixtures/custom-model/ (re-recorded from node on the changed
  Worker source with the command quoted - these files are the Worker's printed bytes, a parity golden, not a
  rendered snapshot reference, and the reviewer re-runs the emitter to check them), Tests/Fixtures/t0244/ (the
  recorded route), ops/mutate/plan.py (LambdaCustomModel is already a subject of that population). No
  profiles/*.json or config.yml edit: the base profile keeps distance_influence 30 for car_fast.
  (D2) THE GRAPH is never opened in place: services/routing/work/t0209/graph-la (78 MB) was copied to the MAIN
  checkout's gitignored services/routing/work/t0244/graph-la; every run below mounts the copy, and each run's
  GRAPH_DIGEST line must equal T-0209's eb43090a...18eb or the run does not count.
  (D3) ops/plan --emit-model on this Windows box prints CRLF; each emitted file is piped through tr -d '\r'. With
  that, the emitted CURRENT model at lambda {0,1,2,4,8} reproduces T-0209's R5 sha256 prefixes exactly (a3ca54ce5d14
  2ea18dc1b15f 3fcf7e6af6f2 8dccac165a8c 38fbbb3f8994), so family `cur` below IS T-0209's model.
  (D4) route_la_pairs.py hard-coded the five lambda files. It now groups every <family>-<lambda>.json in the
  models dir and reports each family as `PAIR <pair>/<family>` (one container run per pair still), takes W0's
  distance_influence from the model file when the model sets one, and records a --fixture route. The T-0209
  call shape (LAMBDAS, report_pair(name, origin, destination, routes)) is kept; its tests pass unchanged.
  MEASUREMENT 1 (run1, models1/, ladder {0,0.5,1,2,3,4,5,6,7,8}), three families before any ruling:
    cur   - T-0209's model as emitted today (bands 1 / (1+0.5l)^-1 / (1+l)^-1, RESIDENTIAL && <7 x0.5, base di 30)
    lin   - candidate: FIRST clause `(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class ==
            SERVICE) && scenic_score < 7` -> 1/(1+2l), then >=7 -> 1, >=4 -> 1/(1+0.5l), else 1/(1+l);
            "distance_influence": 0 in the request model
    score - candidate: the same minor clause and di 0, then one band per integer score s <= 6: 1/(1 + l(7-s)/7)
  (candidate files from the gitignored work/t0244/cands.py; the clause text above is the whole of it).
- 2026-09-26T08:12:37Z MEASUREMENT 1 LANDED, then RULINGS (a) (b) (c) and the predicates (agent/claude-opus-5).
  `python services/routing/tools/route_la_pairs.py --graph work/t0244/graph-la --models work/t0244/models1 --out
  work/t0244/routes1` (image scenic-routing:t0209), exit 0. GRAPH_DIGEST sha256=eb43090a0de52432756d5b6f98a0dad0
  f568838f8272ff339042344e920d18eb (= T-0209's). SUMMARY monotone=8/9. Minutes per lambda over the ladder
  (0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8); T in ms where the order is in question:
    westwood-malibu          car_fast 27.79
      cur    27.79 at 0..6, 55.70 at 7, 8                                        T non-decreasing True
      lin    27.06, then 27.79 at 0.5..4, 55.70 at 5..8                            True
      score  27.06, then 27.79 at 0.5..3, 59.65 at 4, 5, 61.85 at 6..8               True
    westwood-woodland-hills  car_fast 20.14
      cur    20.14, 20.02 at 0.5, 1, 26.49 at 2..8   False: T(0.5) 1,201,286 < T(0) 1,208,634 (T-0209 V1, again)
      lin    20.02 at 0..2, 26.49 at 3..5, 27.75 at 6..8                           True
      score  20.02 at 0, 0.5, 1, 26.49 at 2, 31.27 at 3, 38.43 at 4..8              True
    santa-monica-topanga     car_fast 20.23
      cur    20.23 at 0..5, 21.24 at 6..8                                          True
      lin    20.23 at EVERY lambda (spread +0.00 %)                                True
      score  20.23 at 0..3, 22.43 at 4..8 (spread +10.91 %)                         True
  RUNS: `SUMMARY longest_mixed_minor_run santa-monica-topanga/cur 813.9m model=cur-6.json classes=['residential']
  ways=[121941230,384819177]` - 7th Street appears from lambda 6, not only at 8. lin and score: the longest mixed
  minor run on every route at every lambda is 174.8 m on santa-monica-topanga (service 723963657, score 0, the
  car_fast route's own), 52.3 m on westwood-woodland-hills (service 1087155744,1087155743), 0.0 m on westwood-malibu.
  GraphHopper 11 HONOURS a per-request distance_influence (measured, not read): at lambda 0 lin/score (di 0) return
  27.06 min on westwood-malibu and 20.02 on westwood-woodland-hills where cur-0 / car_fast (di 30) return 27.79 /
  20.14; no refusal, and the route moved.
  (a) ANTI-RAT-RUN FORM - RULED: the minor clause `(road_class == RESIDENTIAL || road_class == LIVING_STREET ||
  road_class == SERVICE) && scenic_score < 7` -> 1/(1+2l) is the FIRST branch of the band chain, so it REPLACES
  the band instead of multiplying it. A minor edge costs 1+2l against 1+l for the dullest (score 0) arterial: the
  ratio is 1 at l=0, 1.5 at 1, 1.89 at 8 and RISES with lambda, where cur's fell from 2 to 1.11 (10 vs 9 at l=8,
  T-0209 V4). Not "x0.5 times the 1/(1+l) band factor on top of the band": that makes a minor edge's 1/p quadratic
  (2(1+0.5l)(1+l) = 90 for a score-4 residential at l=8, a 10x detour incentive) and keeps a lambda-0 halving that
  breaks (b). Not the step-4 zero-area repair: a second request per plan and an area per rat-run, carried on the
  Worker's closure channel for a preference; the model fix removed 7th Street on the measured pair in one
  request. Three classes, not RESIDENTIAL alone: V3's rat-run is residential/living_street/service, and service
  ways all score 0 (T-0207's cap) so the old clause never touched them. `< 7` holds for every such way under
  T-0207's caps (6, 6, 0) and is kept as the plan's own exemption.
  (b) MONOTONE T - RULED: "distance_influence": 0 in the scenic REQUEST model; the base profile keeps 30, so
  car_fast is unchanged and no profiles/*.json is edited. With (a) and (c) EVERY clause multiplies by 1/(1+c l),
  c >= 0 fixed per edge, so at l=0 every priority is 1 and weight(R, l) = T(R) + l S(R) exactly; T-0209 V1's
  exchange argument then gives T non-decreasing and S non-increasing in lambda (not only W0), and T(0) is the least
  T over the gated graph, so T(0) <= T(car_fast): lambda 0 is inside the ceiling at every budget >= 0 - the floor
  LambdaSearch's doc assumes, now true by construction (measured: 27.06 <= 27.79, 20.02 <= 20.14, 20.23 = 20.23).
  P-SAFE-04 stays where it is enforced (ScenicPlanner's guard on the chosen route's own duration); a test by name
  drives the REAL bisection over the measured step table at every whole-minute budget 0..40.
  (c) THE LADDER - RULED: a finer lambda ladder does not help (cur over ten lambdas has two routes on
  westwood-malibu; the bisection already samples continuous lambda to 0.05). A smoother band does: ADOPTED `score`,
  one band per integer score 0..6 with slope (7-s)/7 (score >= 7 unpenalised, score 0 keeps 1/(1+l), minor 2).
  Against lin it moves santa-monica-topanga at l=4 (lin never moves it), gives westwood-woodland-hills four routes
  (20.02, 26.49, 31.27, 38.43) and moves westwood-malibu at 4 instead of 5. The constant is LambdaCustomModel's
  band ladder (the slope per score). No GraphHopper value expression in multiply_by: scenic_score is an integer
  0..10, so one constant clause per score IS the continuous map, with no dependency on that grammar.
  WHAT IT DOES NOT GIVE: westwood-malibu a route between 27.8 and 55.7 min. Over all 30 models the pair returns
  only {27.06, 27.79, 55.70, 59.65, 61.85}. With weight T + l S the returnable routes are the lower convex hull of
  (S, T), and none of three band shapes puts a route inside the gap. The final run adds 3.25/3.5/3.75 across
  score's flip interval; if it finds none, clause 3's "route between" FAILS on that pair and is recorded, never
  re-worded (a between-route is an alternatives question - T-0239's menu - not a penalty-shape one).
  PREDICATES, written after the measurement above:
    P1 (clause 1) - the santa-monica-topanga lambda-8 route routed with the branch's `ops/plan --emit-model 8` has no
       maximal run of residential/living_street/service edges, each scored < 7, over 800 m: LambdaCustomModelRatRunTests
       over Tests/Fixtures/t0244/santa-monica-topanga-lambda-8.{edges.tsv,model.json}, whose model bytes must equal
       LambdaCustomModel.json(for: 8) + "\n" (the recording is bound to the shipping model). RED FIRST on the cur-8
       recording (813.9 m), recorded 08:09 by `route_la_pairs.py --reuse ... --fixture santa-monica-topanga:cur-8.json`.
    P2 (clause 2) - T non-decreasing over the whole ladder on all three pairs in the final run; by name: the emitted
       model sets distance_influence 0 and multiplies by "1" everywhere at l=0; P-SAFE-04 over the real bisection.
    P3 (clause 3) - per pair, some l <= 4 returns a route different from l=0's; durations quoted; westwood-malibu's
       between-route judged from the final run.
  FIXTURE RULED: Tests/Fixtures/t0244/ (route_la_pairs --fixture: route-details edges + probed scenic_score per
  minor edge, 179 rows), not the t0182-recorder: that records GraphHopper HTTP responses, services/routing serves
  none (T-0213 R5), and the rat-run predicate needs road_class and scenic_score per EDGE.
  TEST BINDING: the model tests read LambdaCustomModel.json(for:) - the bytes GraphHopperRouteSource sends and
  --emit-model prints - through a clause-chain evaluator in the test target (GraphHopper's semantics: an
  if/else_if/else chain applies its first matching clause, separate chains multiply), so they compile against
  today's model and go RED by name.
- 2026-09-26T08:27:32Z RED -> CODE -> GREEN, and MEASUREMENT 2 (the branch's own models) LANDED (agent/claude-opus-5).
  RED (commit 63cb33b, `swift test --scratch-path .build/T0244 --filter "LambdaCustomModelRatRunTests|
  PlanCeilingOverLATests"`, exit 1) - every model test red BY NAME against today's bytes:
    x "residential at lambda 8: a minor road below 7 costs 1 + 2 lambda, ..." :25 cost(residential, 4) != 1/0.058824; :34 (ratio -> 1.0), (ratio -> 0.95..)
    x "the request model sets distance_influence 0 and is the identity at lambda 0" :48 distanceInfluence == 0
    x "the band ladder: one band per integer score below 7, ..." :61 (seven.scoreThresholds -> [7, 4]) == [7, 6, 5, 4, 3, 2, 1]
    x "Santa Monica -> Topanga at lambda 8, as routed over the whole-LA graph, has no rat-run over 800 m" :97 (longest -> 813.9249999999998) <= 800
  (the P-SAFE-04 test's own first run failed on MY expectation planned[40] == 3,578.87: 61.85 min fits a +40 budget,
  3,710.979 <= 4,067.261 - corrected before the commit; it is a property that must hold today, not a red.)
  CODE: customModel.ts (HIGH_BAND 7, MINOR_SLOPE 2, MINOR_CONDITION, BAND_LADDER [6..0], bandSlope, bandMultiplier,
  "distance_influence": 0 first in the model, the closure clause now priority[9]) and its Swift port
  (LambdaCustomModel.highBand / minorSlope / minorCondition / ladder / slope / band(slope:lambda:)). The golden
  Tests/Fixtures/custom-model/lambda-{0,1,2.5,7.75,8}.json re-recorded from node v26.3.0 on the changed Worker
  source (PROVENANCE.txt quotes the two-line emitter); LambdaCustomModelParityTests reproduces all five byte for
  byte. customModel.test.ts re-typed BY HAND for the new model (clause shape at lambda 1: minor 0.333333, then 1,
  0.875, 0.777778, 0.7, 0.636364, 0.583333, 0.538462, 0.5): `npx vitest run` Test Files 6 passed (6), Tests 124
  passed (124). GREEN: `swift test --scratch-path .build/T0244` -> "Test run with 343 tests in 49 suites passed".
  MEASUREMENT 2: `ops/plan --emit-model <l> | tr -d '\r'` from THIS branch into work/t0244/models2 (sha256
  prefixes 0:54eb5b269914 1:161a42f5c31a 2:c8932f734c2a 4:b471285b42fe 8:233588b52920; lambda-8 == the golden
  lambda-8.json, cmp), ladder {0, 0.5, 1, 2, 3, 3.25, 3.5, 3.75, 4, 5, 6, 7, 8}, then
  `route_la_pairs.py --graph work/t0244/graph-la --models work/t0244/models2 --out work/t0244/routes2 --fixture
  santa-monica-topanga:lambda-8.json --fixture-dir Tests/Fixtures/t0244`, exit 0. GRAPH_DIGEST
  sha256=eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb. SUMMARY monotone=3/3.
    westwood-malibu          car_fast 27.79  T=[1623696, 1667261, 1667261, 1667261, 1667261, 1904238, 3578870,
      3578870, 3578870, 3578870, 3710979, 3710979, 3710979] - min 27.06 | 27.79 at 0.5..3 | 31.74 at 3.25 |
      59.65 at 3.5..5 | 61.85 at 6..8. T non-decreasing True. BITE +128.55 %.
    westwood-woodland-hills  car_fast 20.14  T=[1201267, 1201267, 1201267, 1589578, 1876472, 1876472, 2305902 x7]
      - 20.02 at 0..1 | 26.49 at 2 | 31.27 at 3, 3.25 | 38.43 at 3.5..8. True. BITE +91.96 %.
    santa-monica-topanga     car_fast 20.23  T=[1213650 x7, 1346010 x6] - 20.23 at 0..3.5 | 22.43 at 3.75..8.
      True. BITE +10.91 %.
  RUNS: longest mixed minor run over every route at every lambda: westwood-malibu 0.0 m; westwood-woodland-hills
  52.3 m (service 1087155744,1087155743, car_fast's); santa-monica-topanga 174.8 m (service 723963657, score 0).
  santa-monica-topanga lambda-8: `residential=19.0m[384819177] ... service=174.8m[723963657] mixed=174.8m
  minor_total=242.6m` - way 121941230 (7th Street, score 4, 15 edges) is GONE; 19.0 m of 384819177 (score 2) is
  all the residential left. FIXTURE santa-monica-topanga-lambda-8 edges=182 time_ms=1346010 distance_m=20358.6
  (its minor rows: service 819770629/819770631/819770628 at score 0 (48.8 m), residential 384819177 score 2
  (19.0 m), service 723963657 score 0 (174.8 m)); LambdaCustomModelRatRunTests' recorded-route test is GREEN on it.
  CLAUSE 3's between-route EXISTS: westwood-malibu at lambda 3.25 is 31.74 min (29,214.7 m, 346 edges), between
  27.8 and 55.7. The sub-ladder found what the integer ladder could not - measurement 1's "not between" held
  only for the lambdas it sampled. PlanCeilingOverLATests now carries that step: a +20 min budget plans the
  1,904.238 s route through the real bisection (evaluations 0, 4, 2, 3, 3.5, 3.25).
- 2026-09-26T08:52:30Z POPULATION, GATES, and THE ACCEPTANCE BLOCK RE-QUOTED (agent/claude-opus-5).
  POPULATION (commit 154ec34): ops/mutate/plan.py - the old mid-band mutant's anchor (the three-band tuple) is
  gone, so it is replaced by six model mutants, one or more per ruling: band-ignores-lambda,
  minor-slope-no-steeper-than-the-dullest-band, minor-clause-residential-only (a); distance-influence-back-to-the-
  base (b); ladder-collapses-to-two-bands, slope-steeper-by-one-step (c). MIN_MUTATIONS 10 -> 24; SUITES and
  TEST_FILES gain LambdaCustomModelRatRunTests, CustomModelChain, PlanCeilingOverLATests. `SCENIC_MUTATE_SCRATCH=
  .build/T0244 python ops/mutate/plan.py` -> "caught 24 of 24   trapped 0   compile-only 0   MISSED 0   skipped 0",
  exit 0. `--prove-floor`: an empty population REFUSED, one mutation REFUSED, a subject nothing mutates REFUSED,
  the shipped table accepted. `python ops/lib/check-mutate-population.py` -> "P-PROC-06: every added module is
  covered or allowlisted; the floor of 36 holds".
  300-LINE CAP: customModel.ts and customModel.test.ts were 295 / 294 on main and 316 / 306 after the change - over
  the cap CLAUDE.md sets for every file although ops/lib/check-line-cap counts .swift only; trimmed to 299 / 299
  (commit ced96bc), goldens re-checked exact with cmp, vitest Tests 123 passed (123) (two band tests merged).
  GATES on ced96bc (`git fetch origin` + `git merge --no-edit origin/main`: "Already up to date", origin/main
  4fc05a4): route tests `pytest tests/test_route_details_runs.py` 7 passed (and test_route_details.py with it,
  exit 0); check-exec-bits "P-OPS-01: 100 files, 23 required present, all modes correct"; check-line-cap "P-SRC-02:
  122 Swift files tracked (Sources=45, Tests=53, apps/ios=24), none over 300 lines"; `bash ops/queue-check` "QUEUE
  OK (237 tasks)". Line counts: LambdaCustomModel.swift 115, CustomModelChain.swift 103,
  LambdaCustomModelRatRunTests.swift 99, PlanCeilingOverLATests.swift 69, LambdaCustomModelParityTests.swift 99,
  route_la_pairs.py 248, ops/mutate/plan.py 257.
  ACCEPTANCE:
    1. MET. Ruled (a) at 08:12:37Z before any model code. Santa Monica -> Topanga at lambda 8 with the branch's
       emitted model (run2): longest mixed residential/living_street/service run 174.8 m (service 723963657, score
       0); residential 19.0 m (384819177, score 2); 7th Street's way 121941230 absent from every route at every
       lambda. "Santa Monica -> Topanga at lambda 8, as routed over the whole-LA graph, has no rat-run over 800 m"
       RED on the cur-8 recording (813.92 m, 63cb33b), GREEN on the branch recording (bda0801), which it binds to
       LambdaCustomModel.json(for: 8) byte for byte.
    2. MET. Ruled (b): "distance_influence": 0 in the request model, every clause 1/(1+c l), so weight = T + l S.
       T over {0, 1, 2, 4, 8} (run2, ms): westwood-malibu 1,623,696 / 1,667,261 / 1,667,261 / 3,578,870 /
       3,710,979; westwood-woodland-hills 1,201,267 / 1,201,267 / 1,589,578 / 2,305,902 / 2,305,902;
       santa-monica-topanga 1,213,650 / 1,213,650 / 1,213,650 / 1,346,010 / 1,346,010 - non-decreasing on 3 of 3,
       and over all 13 ladder lambdas. P-SAFE-04: "every plan's ETA <= fastest + budget at every whole-minute
       budget 0..40 over the LA steps" green; planner/ceiling-* mutants caught.
    3. MET on the measured pairs, with the window recorded. Ruled (c): the smoother band (one per score), not a
       ladder constant. The route moves before lambda 8 on 3 of 3 pairs (westwood-malibu at 3.25, westwood-
       woodland-hills at 2, santa-monica-topanga at 3.75 - under T-0209's model two pairs sat still through 4).
       westwood-malibu has a route between: 31.74 min at lambda 3.25 (27.79 at 3, 59.65 at 3.5), and a +20 min
       budget plans it through the real bisection (PlanCeilingOverLATests: planned[20] == 1,904.238; the six
       default evaluations 0, 4, 2, 3, 3.5, 3.25 are the same for every budget from +4 to +31 min).
  STILL OPEN (recorded, not fixed here):
    - The westwood-malibu between-route lives in a narrow lambda window (in at 3.25; out at 3 and 3.5). The
      bisection lands in it because its fixed sequence visits 3.25; a pair whose window falls between the
      bisection's samples would be skipped. A search that looks for route CHANGES, or T-0239's alternatives
      menu, is the fix - not this model.
    - `npx tsc --noEmit -p services/api` stops locally on "Cannot find type definition file for
      '@cloudflare/workers-types/2023-07-01'" (environment: npm ci's tree on this box); vitest is 123/123. CI is
      the witness for the typecheck.
    - The Worker's served model changes on its next deploy (distance_influence 0, the minor clause, the band
      ladder); ops/plan emits it now. Service ways all score 0 (T-0207), so their cost rose from 1+l to 1+2l -
      a preference, never a gate; a destination on a service road is still reachable.
- 2026-09-26T10:10:43Z agent/claude-opus-5 (owner): PRE-REVIEW MUTANT PASS - three survivors, each BLOCKING, closed (commit
  3af07c2). Rulings before code:
    B1 (the pass's B2): TRUE - scenic(from:to:lambda:) sent json(for:) and no test drove it (the verbatim test built
       its own 7.75 model). RULED: bind to the shipping entry point, not a new helper. GraphHopperRouteSource gains
       an internal transport seam `post` (nil = URLSession, every production run; send() still refuses the safety
       gates FIRST, then hands the body over), and PlanCLIRequestBodyTests
       .theScenicRequestCarriesTheLambdaModelWithDistanceInfluenceZero drives scenic() at every lambda step of 0.1
       in 0..8: parsed distance_influence 0, profile car_scenic, embedded model == LambdaCustomModel.json(for:
       lambda) byte for byte. The allowlist reason for GraphHopperRouteSource.swift ("builds a request body ...
       both of which ops/mutate/plan.py covers") was false by this survivor: the entry leaves
       ops/lib/mutate-population-allowlist.json and the module becomes a plan.py subject.
    B2 (mutant C): TRUE. RULED: all three witnesses. The class set is read from LambdaCustomModel.minorCondition's
       road_class atoms (the static literal is gone; the other three tests in the suite read the derived set too);
       every recorded row's minor-ness must equal "has a numeric scenic_score" (route_la_pairs.py fills it for its
       MINOR_CLASSES only); the measured longest run is pinned, 174.815 m ending on way 723963657.
    B3 (A2-ts): TRUE, and PROVENANCE.txt's "A change on either side fails it by name" was false - the golden is a
       recording and never re-runs node. RULED: services/api/test/customModelMinorClause.test.ts (new, because
       customModel.test.ts is at 299 lines) types out 1/(1+2l) and 1/(1+l) as serialised at every step of 0.1 in
       0..8 and asserts the minor / dullest cost ratio strictly rises; PROVENANCE.txt and LambdaCustomModel's doc
       comment now say the Swift side fails the golden and the TypeScript side fails vitest.
    Touches widened in this header: ops/lib/mutate-population-allowlist.json,
       services/api/test/customModelMinorClause.test.ts.
  RED - each mutant applied to 3af07c2 by .build/t0244/redgreen_b123.py and restored (git status clean after):
    cli/scenic-request-ignores-lambda (json(for: 8)): "scenic(from:to:lambda:) sends distance_influence 0 and
       LambdaCustomModel.json(for: lambda), at every step" recorded an issue at PlanCLIRequestBodyTests.swift:84:13:
       Expectation failed: embedded == (try LambdaCustomModel.json... - exit 1.
    cli/scenic-request-changes-distance-influence (0 -> 30 on the wire): the same test, :81:13 Expectation failed:
       ((model["distance_influence"] as? NSNumber)... and :84:13 - exit 1.
    oracle/rat-run-class-set-drops-service (mutant C, .dropFirst().dropLast()): "Santa Monica -> Topanga at lambda
       8, as routed over the whole-LA graph, has no rat-run over 800 m" failed with 6 issues - :97:13 (minor ->
       false) == ((Int(row[4]) != nil)) x4, :107:9 abs(longest.metres - 174.815) -> 155.769, :108:9 longest.way ->
       "384819177". The 800 m expectation alone stays green on it (19.0 m), as the pass found.
    A2-ts ((9 / 17) * bandMultiplier(bandSlope(0), lambda) for lambda >= 4, in customModel.ts): vitest "Test Files
       1 failed | 6 passed (7)", "Tests 2 failed | 123 passed (125)" - "minor at lambda 4: expected '0.105882' to
       be '0.111111'", "minor / dullest cost at lambda 4.1: expected 1.888888888888889 to be greater than
       1.888895185206173". The 123 pre-existing tests stay green on it, as the pass found.
  GREEN (pristine): "Test run with 13 tests in 3 suites passed" (PlanCLIRequestBodyTests | LambdaCustomModelRatRunTests
    | LambdaCustomModelParityTests); vitest "Test Files 7 passed (7)", "Tests 125 passed (125)".
  POPULATION: ops/mutate/plan.py MIN_MUTATIONS 24 -> 27, SUBJECT_MODULES + Sources/ScenicPlanCLI/
    GraphHopperRouteSource.swift. `--only cli/scenic-request,oracle/rat-run`: "population 27 mutations over 9
    modules", CAUGHT x3, "caught 3 of 3 trapped 0 compile-only 0 MISSED 0 skipped 0". `--only custom-model/` (the
    mutants whose catchers this commit touched): "caught 8 of 8 trapped 0 compile-only 0 MISSED 0 skipped 0". The
    other 16 were not re-run here; their anchors and their catching tests are untouched. --prove-floor: empty /
    one mutation / unmutated subject REFUSED, the shipped table accepted, exit 0. check-mutate-population.py:
    "P-PROC-06: 93 modules, 38 covered by 15 populations, 34 allowlisted, 0 added by this branch ... the floor of
    36 holds", exit 0.
  NOT IN A POPULATION: A2-ts. No mutation harness covers services/api/src (CLAUDE.md's population rule names
    services/etl/etl/ and Sources/); the mutant is recorded here by name with its red and green. A vitest-driven
    population for customModel.ts is STILL OPEN - a harness task, not this model's.
  GATES on 3af07c2: check-line-cap "P-SRC-02: 122 Swift files tracked (Sources=45, Tests=53, apps/ios=24), none
    over 300 lines"; check-exec-bits "P-OPS-01: 100 files, 23 required present, all modes correct"; queue-check
    "QUEUE OK (237 tasks)". Line counts: GraphHopperRouteSource.swift 160, PlanCLIRequestBodyTests.swift 109,
    LambdaCustomModelRatRunTests.swift 110, LambdaCustomModel.swift 117, ops/mutate/plan.py 270,
    customModelMinorClause.test.ts 41, customModel.test.ts 299, customModel.ts 299. Acceptance clauses 1-3 as
    quoted in the previous entry: unchanged by this commit (no model byte, fixture or route moved; the parity
    golden and the recorded route are green above).
