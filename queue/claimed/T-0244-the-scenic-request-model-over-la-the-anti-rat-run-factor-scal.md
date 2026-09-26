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
