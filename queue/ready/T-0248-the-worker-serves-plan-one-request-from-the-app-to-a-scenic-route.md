---
id: T-0248
title: the Worker serves POST /plan - one request from the app becomes a fastest call plus the lambda budget search against the router, returning the scenic route, ETA vs fastest, hazards and the Apple Maps URL; quota first, kill switch honoured, privacy invariant held
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-04, P-SAFE-01]
reviewer: null
depends_on: [T-0244]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, from the plan's Problem A and the product invariants: the request shape (origin/destination, budget minutes, departs-at), and how it holds 'the server never receives more than one coordinate per user action, never more than 2 decimal places' (e.g. origin rounded to 2 dp on the device and the destination as a corpus place id, or a ruled exception argued against the plan) - a Worker test refuses any body carrying a second coordinate or a coordinate with more than 2 decimals"
  - "the handler decrements the quota BEFORE any upstream call and KILL=1 returns 503 with zero upstream calls (P-COST-01, a test with the counting fake for /plan); at most 12 upstream requests per plan (P-COST-04); the custom model sent upstream is buildCustomModel's (the T-0231 seam - a request model touching road_access/surface is never sent, P-SAFE-01)"
  - "the budget search is a port of ScenicKit LambdaSearch with the ceiling enforced on the returned route's real ETA (P-SAFE-04): a recorded-router test (fixtures from Tests/Fixtures/t0221/ or t0182, replayed by the counting fake) returns for Santa Monica -> Topanga +25 the SAME route, ETA and Apple Maps URL that 'ops/plan' prints for that recording - EXACT equality of the URL and ETA, not property checks"
  - "the response carries route geometry, ETA, fastest ETA, the estimate badge flag (no traffic data), hazards and the Apple Maps URL (<= 9 waypoints); vitest count quoted; the mutation population for the new module (ops/mutate/ or a vitest-driven equivalent - rule which) with a literal floor"
---
## Brief

Milestone survey (2026-10-04): the Worker serves only /__health /__version /__ro, so nothing in the app can plan a
live route. This is the first endpoint the app needs (M3 exit). /loop /surprise /trip follow the same shape later.

## Log
- 2026-10-05T05:06:53Z filed by agent/claude-opus-5 (orchestrator) from the milestone survey.
