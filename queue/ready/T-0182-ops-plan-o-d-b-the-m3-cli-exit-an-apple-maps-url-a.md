---
id: T-0182
title: ops/plan <O> <D> <B> - the M3 CLI exit: an Apple Maps URL and the per-edge term table for an LA origin and destination against the served LA graph
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/plan, ops/lib/, Sources/ScenicKit/, services/api/src/, Tests/]
pins_affected: []
reviewer: null
depends_on: [T-0116, T-0158]
verify: [ops/test, ops/check-pins]
acceptance:
  - "`ops/plan <origin> <destination> <extra-minutes>` prints an Apple Maps URL with <= 9 pinned waypoints, the fastest ETA, the returned ETA (<= fastest + budget: the ceiling, asserted), and a per-edge table (way id, highway, scenic_score, the terms, the lambda chosen); RED by name: the budget-ceiling assertion red on a stub that returns lambda 8, the actually-different assertion red on a stub that returns lambda 0 (the plan's meta-tests)"
  - "Linux tests: the URL builder and the table over a recorded GraphHopper response (a golden), count line quoted"
---
## Brief

From the 2026-09-19 19:13 panel (STRATEGY, grounded). plan:22's success criterion - "the developer drives a route
this app made" - has a phone-free instance in plan:284's M3 exit: `ops/plan <O> <D> <B>` prints an Apple Maps
URL plus the per-edge term table, and "you drive engine output from the CLI". That path needs no TestFlight
(T-0009, human) and retires the criterion for the owner in LOS ANGELES once T-0168 clips regions/la, T-0031
serves it, and the Worker's custom model (T-0158, merged) supplies the lambda. No task named `ops/plan` existed
in ready/ or claimed/ (only T-0013 mentions it). The origin is Westwood (regions/la); the destination is the one
the owner names - nothing in the plan or any Log records it (FOR THE HUMAN).

## Log
- 2026-09-19T02:11:14Z filed by agent/claude-fable-5-1 from the 19:13 panel's grounded synthesis. Not started; behind T-0031's second half.
- 2026-09-19T02:58:56Z PROMOTED to ready/ by agent/claude-fable-5-1 (20:13 panel, grounded): T-0116 and T-0158 are merged and T-0031's first slice is PR #105; the terminal task of the LA CLI path was the only link still in backlog/.
- 2026-09-19T10:46:00Z depends_on: T-0031 -> T-0209 by agent/claude-fable-5-1 (03:13 panel, grounded): T-0031 is in done/ as a Vermont slice, so the queue read this task as unblocked while nothing builds the LA graph it needs; T-0209 is that graph.
- 2026-09-19T17:49:27Z SPLIT by agent/claude-fable-5-1 (10:13 panel, fable-grounded): plan:284's M3 exit names the CLI plus MV->SF; the commute answer is M4/T-0013's input, not this task's - the freeze on 'the destination the owner names' was self-imposed (asked of the human seven panels running). Clauses 1 and 3 need no graph; clause 3's recorded GraphHopper response comes from T-0213's REAL canyon-window GraphHopper 11.0 graph (#117: window-tagged-1.osm.pbf sha256 06046be0...0090; the graph-cache preserved at services/routing/work/t0213/ in the main checkout - verify it is there before recording, else record from a fresh import of that PBF), not a stub. The served-graph run moves to T-0221 (depends_on [T-0182, T-0209]). NOTE: touches ops/lib/ overlaps T-0217's by directory only.
