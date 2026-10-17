---
id: T-0389
title: lambda=0 routes faster than car_fast on 4 of 28 LA grid pairs - the request models send distance_influence 0 while car_scenic_base.json carries 30; align them or restate the property
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/customModel.ts, services/api/test/, Tests/Fixtures/custom-model/, services/routing/tests/, Sources/ScenicKit/, Tests/ScenicKitTests/]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0190, T-0386]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0386 (PR #282) re-measured the routed lambda runs and found that on 4 of 28 pairs of T-0209's LA canyon grid
(and 2 more in a 0.25/0.5/0.75 grid) the lambda-0 route is FASTER than car_fast, for example
34.0875,-118.8758 -> 34.0875,-118.6044: 2474921 vs 2504511 ms. The cause: since T-0190 the request models carry
distance_influence 0, while car_scenic_base.json (and so car_fast's fastest search) carries 30. The plan's
property "lambda=0 is the fastest route" (Problem A step 2) now holds only on the Vermont pair, and T_fast (the
ceiling's anchor, P-SAFE-04: ETA <= T_fast + B) is measured on a route that is not the fastest the models can
find.

MEASURE the effect on the ceiling with the recorded LA grid (no deploy). RULE one of these: the models carry the base's
distance_influence (bound by identifier to car_scenic_base.json, never a typed 30), or T_fast is defined as
min(car_fast, lambda-0), or the property is restated. Bind it through the shipped Worker builder and the recorded
fixtures (customModelGolden re-emit). Add a routed test that lambda-0 >= car_fast (or the restated property) on
every measured grid pair where a graph is present.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0386 stillOpen 1.
