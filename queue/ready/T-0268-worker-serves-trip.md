---
id: T-0268
title: the Worker serves POST /trip - a multi-day road trip planned in at most 12 upstream requests, the RoadTrip day splitter ported to TS with a shared parity fixture, quota first, one coordinate at 2 dp
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/, Tests/Fixtures/t0268/, Tests/ScenicKitTests/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-04]
reviewer: null
depends_on: [T-0249, T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /trip {origin:{lat,lon} at 2 dp, destination:{place}, days, extra_budget_pct?} (whitelisted keys at every level; ranges table-tested at EVERY bound per the repo rule) plans the A->B route with the plan's +40% scenic budget, splits it with a TS port of Sources/ScenicKit/RoadTrip (T-0249) and returns the whole day plan; the per-day legs are ONE /plan-style request each; the whole trip makes at most 12 upstream requests (plan Requests-per-plan: 12 per 5-day trip) - tested by count through ROUTES['/trip'] and refused with zero further calls past the cap"
  - "a shared fixture under Tests/Fixtures/t0268/ gives IDENTICAL day plans from the Swift RoadTrip and the TS port (a vitest test and a Swift test each read it and compare to the same recorded answer by full equality; the T-0252 retrace parity pattern)"
  - "KILL=1 (env and KV) -> 503 before the body; quota reserved before the first call with its own ruled kind (free tier: preview only, per the plan feature table); the killSwitchRoutes test's upstream-route literal gains /trip; the budget ceiling ETA <= fastest + budget holds per day and for the trip; a TS mutation population with a literal floor"
---
## Brief

Plan 'Road trip - A->B over N days, +40% scenic budget, day splitter, 2-4 stops/day, overnight town; 1 request per
day'; Worker list /plan /loop /surprise /trip. T-0249 shipped the Swift splitter; nothing serves a trip. Copy
T-0248/T-0252/T-0262 shapes (handlers, deps, QuotaCounter kinds, killSwitch, mutation drivers with --only).

## Log
- 2026-10-05T23:08:38Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M3/M5 /trip).
