---
id: T-0387
title: ops/mutate/profilegate.py's 'the request profile read instead' mutant points at the deleted car_scenic_request.json - re-anchor it on the recorded models
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/profilegate.py, services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0190]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0190 deleted services/routing/profiles/car_scenic_request.json. ops/mutate/profilegate.py:88's mutant 'the request profile read instead' still names it, so it is now killed by FileNotFoundError rather than by a gate test (a vacuous kill). Re-anchor the mutant on what a careless edit would really read (a Tests/Fixtures/custom-model/lambda-*.json record), show it CAUGHT by a named test, keep the floor, and add an --prove-vacuity check that no mutant is killed by an exception outside the tests.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0190 stillOpen 2.
