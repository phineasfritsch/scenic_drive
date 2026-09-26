---
id: T-0221
title: ops/plan against the served LA graph: Westwood -> Malibu (T-0209's first named pair) - the URL and the per-edge table quoted in the Log, the owner drives it (plan:284's exit)
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/plan, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0182, T-0209, T-0244]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/plan run once against the served LA graph (T-0209's import of T-0208's whole-LA tagged PBF; /info's graph hash quoted) for Westwood -> Malibu at +25: the Apple Maps URL (<= 9 waypoints), the fastest ETA, the returned ETA (<= fastest + 25 min, asserted), the per-edge table and the lambda chosen quoted in the Log; the longest residential/service run on the returned route quoted (m, way ids) against T-0209's ruled threshold"
  - "the same for T-0209's other two pairs (Westwood -> Woodland Hills, Santa Monica -> Topanga) with the three URLs handed to the owner in one FOR THE HUMAN block - the owner's own commute pair is T-0013's (M4), added here only when the owner names it"
---
## Brief

Split out of T-0182 by the 10:13 panel (grounded on plan:284 and T-0209 clause 2): T-0182 ships the CLI, the
meta-tests and the golden over T-0213's real canyon graph; this task is the run against the SERVED LA graph and the
drive the owner takes. Order: T-0208 -> T-0209 -> this.

## Log
- 2026-09-19T17:49:27Z filed by agent/claude-fable-5-1 (10:13 panel, fable-grounded). Not started; after T-0182 and T-0209.
- 2026-09-19T20:26:45Z by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0): the 800 m figure copied from T-0209 clause 3 was an unmeasured predicate; now the measurement against T-0209's ruled threshold.
- 2026-09-19T20:54:38Z by agent/claude-fable-5-1 (orchestrator): the run on the returned route needs T-0209's path-details mode (added as its first clause); the pair coordinates are typed, never prose.
- 2026-09-26T03:11:50Z depends_on gains T-0244 (orchestrator): T-0209 measured a 813.9 m residential run on 7th Street, Santa Monica at lambda 8 and a non-monotone T over LA; the owner's first LA drive waits on the request-model fix.
- 2026-09-26T15:20:43Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0182, T-0209 (PR #131) and T-0244 (PR #134, af36cd3) are merged - the whole-LA graph (services/routing/work/t0209/graph-la, GRAPH_DIGEST eb43090a...18eb) and the request model without the 7th Street rat-run are on main. The graph has no HTTP surface until the VPS (T-0209 R6/R9): the author rules how ops/plan reaches it (a recording of the three pairs through the committed in-process recorder, replayed with ops/plan --recorded, is the expected path).
