---
id: T-0386
title: Re-measure the routed lambda runs (test_lambda_monotone BITE_FLOOR, test_route_details lambda-8) against the models production now sends
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/routing/tests/, services/routing/measure_runs.py, Tests/Fixtures/custom-model/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0190]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0190 (PR #279) made the shipped Worker builder the only source of the request models: 9 clauses, distance_influence 0, the T-0244 minor clause and new band slopes. The routed numbers recorded before it (test_lambda_monotone's five T(lambda) durations and BITE_FLOOR's measured +43%, test_route_details' lambda-8 2515815 ms) were measured with the old 3-clause template and are stale.

Run the LA GraphHopper container (WSL docker, the committed LA graph build; no VPS, no deploy), route the recorded pairs with Tests/Fixtures/custom-model/lambda-*.json through services/routing/request_models, quote every number in the Log, then rule the new floors from the measured population (never a typed guess). Record the graph hash. If the container cannot run on this box, file the measurement as unverified and stop.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0190 stillOpen 1.
