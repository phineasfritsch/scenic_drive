---
id: T-0286
title: every returned route is checked against EVERY stored closure (not only the <=50 sent) - a path crossing a dropped closure is re-requested once with that closure swapped in, and if it still crosses, the answer carries a 'crosses closure' hazard instead of a silent route
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T17:35:53Z
lease_expires_at: 2026-10-07T05:35:53Z
worktree: .worktrees/T-0286
branch: task/T-0286
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-COST-04]
reviewer: null
depends_on: [T-0282]
verify: [ops/test, ops/check-pins]
acceptance:
  - "after each driven router response (/plan chosen route, /loop attempt, /trip each leg) the Worker tests the returned path (points_encoded false) against every stored closure polygon with an exact segment-polygon intersection (point-in-polygon for vertices + edge crossings), ruled in the Log; a crossing of a closure that was NOT sent triggers ONE re-request with the crossing closures swapped in for the farthest sent ones (still <= 50), counted inside the existing request caps (P-COST-04: 12/3/12) - a request over the cap is not made"
  - "if the re-requested path still crosses an active closure, or the cap forbids the re-request, the 200 answer carries closures_hazard {state, ..., crosses: [lcs ids]} - never a silent crossing; tests through ROUTES over the T-0276 fixture with a synthetic path crossing a dropped closure, as cross-product tables (empty set / one closure / > 50; crossing at a vertex, along an edge, fully inside) with the no-row-ignores-its-variant meta-test"
  - "P-SAFE-08 binds the new tests by name with an APPENDED dated sentence retiring T-0282's 'nothing re-checks the returned path' limit; a TS mutation population with a literal floor"
---
## Brief

T-0282 stillOpen 1: 'The corridor is the straight segment between a request's two points, not the path GraphHopper
returns. A scenic detour can pass a dropped closure ... nothing re-checks the returned path against the dropped set.'
About 117 closures are dropped per LA request on today's feed. Product invariant: a route never crosses an active
closure (P-SAFE-08), and it is never silent.

## Log
- 2026-10-06T17:30:50Z filed by agent/claude-opus-5 (orchestrator) after PR #172 (T-0282) review PASS.
- 2026-10-06T17:35:53Z claimed by agent/claude-opus-5; lease until 2026-10-07T05:35:53Z
