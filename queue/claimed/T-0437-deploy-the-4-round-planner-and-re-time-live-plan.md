---
id: T-0437
title: Deploy the 4-round planner (T-0411) and re-time live /plan through the tunnel - quote at least 5 plans before and after
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T22:34:36Z
lease_expires_at: 2026-10-19T22:34:36Z
worktree: .worktrees/T-0437
branch: task/T-0437
exclusive: [prod]
touches: [queue/]
pins_affected: []
reviewer: null
depends_on: [T-0411]
verify: [ops/sane]
acceptance: []
---
## Brief

T-0411 (PR #304) is merged. A scenic plan now takes 4 router rounds instead of 5. The speculative midpoint runs in
the idle slot, and the answers are byte-equal on the recorded fixtures.

Production still runs 839220da, deployed by T-0409. Its live timings, from 34.07,-118.44 at +25 with a fresh
x-scenic-device per request:
- 200 answers: 1.8-4.3 s.
- 422 answers: 4-7 s.

Do the same steps as T-0409, using `.artifacts/t0409-time-plans.sh` (its 5 places):
1. Time the 5 live /plan requests BEFORE the deploy. One 2-dp origin per request.
2. Run `bash ops/deploy` from main while holding prod.lock, and quote the DEPLOYED line.
3. Re-time the same 5 requests AFTER the deploy. Quote both sets of timings.
4. Run `ops/sane --prod` and quote the version row.

Record in the Log anything still slow and why. T-0433, an owner decision, covers the remaining nothing_pretty round.

## Log
- 2026-10-18 filed by agent/claude-opus-5 after PR #304 merged.
- 2026-10-18T22:34:36Z claimed by agent/claude-opus-5; lease until 2026-10-19T22:34:36Z
