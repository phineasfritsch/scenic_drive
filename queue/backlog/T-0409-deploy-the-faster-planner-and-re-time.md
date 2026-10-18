---
id: T-0409
title: Deploy the faster planner (T-0403) and re-time live /plan through the tunnel - quote at least 5 plans before and after
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [prod]
touches: [queue/]
pins_affected: []
reviewer: null
depends_on: [T-0403]
verify: [ops/sane]
acceptance: []
---
## Brief

T-0403 (PR #300) is merged. A full plan now takes 5 router rounds instead of 7, and it sends the same 7 requests and
gets the same answers. Production still runs c6f2da75, deployed by T-0395. The measured live plan took 12.1 s;
cold start was about 5 s and each warm router call took 0.25-0.9 s through the tunnel. The router keep-warm ping is
running.

1. Before deploying, time at least 5 live /plan requests to different seeded places. Respect the privacy rule: one
   2-dp origin per request.
2. Run `bash ops/deploy` from main while holding prod.lock. Quote the DEPLOYED line.
3. Re-time the same 5 requests and quote both sets of timings.
4. Run `ops/sane --prod` and quote the version row. Since T-0402 it compares only the Worker's inputs.

Record in the Log anything that is still slow and why.

## Log
- 2026-10-18 filed by agent/claude-opus-5 after PR #300 merged.
