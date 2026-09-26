---
id: T-0244
title: the scenic request model over LA - the anti-rat-run factor scales with lambda (7th Street, Santa Monica at lambda 8), T(lambda) monotone (distance_influence), and a lambda ladder that moves the route before lambda 8
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Budget/, Sources/ScenicKit/Routing/, Tests/ScenicKitTests/, Sources/ScenicPlanCLI/, Tests/ScenicPlanCLITests/, services/routing/tools/route_la_pairs.py, services/routing/tests/]
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
