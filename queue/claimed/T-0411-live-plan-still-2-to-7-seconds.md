---
id: T-0411
title: Live /plan still takes 1.8-7 s after T-0403 (failure paths 4-7 s) against the plan's p95 1.5 s - measure the remaining time per stage and cut it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T17:23:19Z
lease_expires_at: 2026-10-19T17:23:19Z
worktree: .worktrees/T-0411
branch: task/T-0411
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/test/mutate/, ops/lib/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: null
depends_on: [T-0409]
verify: [ops/test]
acceptance: []
---
## Brief

T-0409 deployed T-0403's 5-round schedule (live 839220da) and timed 5 places from Westwood (34.07,-118.44, +25):
- 200 answers: 1.8-4.3 s (Topanga dropped from 4.17 s to 2.41 s).
- Honest-failure 422 answers (no_scenic_alternative, nothing_pretty): still 4-7 s.

The quoted lines are in T-0409's Log. Each warm router call through the tunnel takes 0.25-0.9 s, and GraphHopper's
own work is about 50 ms of that.

This is a MEASUREMENT task first. Use a timed fake router plus Worker-side timing over the recorded fixtures to
attribute the remaining time:
- the rounds on the failure paths (the nothing_pretty offer computes lambda-4 and lambda-8 extras)
- the re-request that confirms the chosen route
- KV and D1 reads
- the plan cache

Rule which lever pays without changing any answer, and keep the ETA ceiling and the <= 2 in-flight cap. Candidate
levers:
- compute the failure-path extras concurrently within the cap
- cache the fastest route per (H3-8 origin, H3-8 destination, hour bucket)
- skip the confirming re-request when the bracket already holds the chosen route

Answer equality must stay byte-exact on the recorded fixtures (T-0403's oracle).

## Log
- 2026-10-18 filed by agent/claude-opus-5 from T-0409's live timings.
- 2026-10-18T17:23:19Z claimed by agent/claude-opus-5; lease until 2026-10-19T17:23:19Z
