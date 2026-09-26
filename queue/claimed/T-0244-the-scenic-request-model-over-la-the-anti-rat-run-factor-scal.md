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
touches: [Sources/ScenicKit/Budget/, Sources/ScenicKit/Routing/, Tests/ScenicKitTests/, Sources/ScenicPlanCLI/, Tests/ScenicPlanCLITests/, services/routing/tools/route_la_pairs.py, services/routing/tests/, Sources/ScenicKit/Plan/, services/api/src/customModel.ts, services/api/test/customModel.test.ts, Tests/Fixtures/custom-model/, Tests/Fixtures/t0244/, ops/mutate/plan.py]
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
