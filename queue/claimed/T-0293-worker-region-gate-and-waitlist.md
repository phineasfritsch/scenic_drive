---
id: T-0293
title: The Worker refuses a plan outside the served region with 422 region_unsupported before any quota or upstream call, the app reads it as PlanError.regionUnsupported, and POST /waitlist counts interest per coarse cell with no personal data
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T03:14:58Z
lease_expires_at: 2026-10-07T17:14:58Z
worktree: .worktrees/T-0293
branch: task/T-0293
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/mutate/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05, P-PRIV-06]
reviewer: null
depends_on: [T-0248, T-0251]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: which coordinate(s) each of /plan /loop /trip /isochrone receives today (at most one per action, 2 dp - quote the whitelist), where the served region's bounds come from (services/etl/regions/la/region.json and the CI golden sfbay - one source of truth, compiled into the Worker, never fetched), and whether the gate is a bbox or a polygon; quote the bounds"
  - "Every planning route answers 422 {error: 'region_unsupported'} for a coordinate outside the bounds, BEFORE the quota decrement and with 0 upstream calls (counting fakes), through the shipped worker.fetch; table over every bound per memory range-checks-every-bound (each edge just outside via nextafter at 2 dp granularity, each exact edge accepted with the whole response compared), per route - rows as functions of the route with a meta-test that no row ignores it"
  - "Swift: PlanResponseReader maps 422 region_unsupported to PlanError.regionUnsupported, by full equality in the R6 table test; the doc comment on the enum case is updated by fact, not by prose claim"
  - "POST /waitlist {cell} accepts exactly one H3 resolution-5 cell id (validated), increments a D1 counter row keyed by that cell (migration 0006, columns cell + count + updated_at only - P-PRIV-05 DDL test extended and seen red with a forbidden column), refuses anything else with 400 by full-equality table, is quota-exempt and kill-switch-exempt by ruling (no upstream), and appears in the requestReadSites / route-enumerating tests"
  - "A mutation population entry per gate edge and per waitlist validation branch with a literal floor; three shown MISSED before, CAUGHT by name after"
---
## Brief

Plan, Launch scope: "US-only, Bay Area corpus/graph, REGION_UNSUPPORTED + waitlist". PlanError.regionUnsupported exists
on the client (T-0251) but no Worker response produces it. The owner's region is LA (memory user-lives-in-la); the
plan's Bay Area is the CI golden set. Privacy invariant: the server never receives more than one coordinate per user
action, never more than 2 decimal places; the waitlist stores a coarse cell count, never a person.

## Log
- 2026-10-07T03:11:48Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 region waitlist).
- 2026-10-07T03:14:58Z claimed by agent/claude-opus-5; lease until 2026-10-07T17:14:58Z
