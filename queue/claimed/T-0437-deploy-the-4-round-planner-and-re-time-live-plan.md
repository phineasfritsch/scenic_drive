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
- 2026-10-18T22:48:49Z agent/claude-opus-5: BEFORE (live /__version git_sha=839220da581beccfc4505bb7ace74d42c3e36812 built_at=2026-10-18T08:50:35Z schema_version=4; main HEAD 2edb7e60; .artifacts/t0409-time-plans.sh, fresh x-scenic-device per request, origin 34.07,-118.44, budget 25). Pass 1 at 2026-10-18T22:41:01Z, its first request hit a cold router:
    place=710486223536647933 http/time=200 12.729441 eta=1844.435 fastest=1529.553 ceiling=3029.553 lambda=7.75 evals=6
    place=161142772170980305 http/time=422 5.802517 {'error': 'no_scenic_alternative'}
    place=597222322620230064 http/time=422 3.471276 {'error': 'nothing_pretty', 'budget_minutes': 25, 'more_time_minutes': 65, 'back_roads_eta_s': 3784.909, 'back_roads_budget_minutes': 36}
    place=3980501968317559019 http/time=200 2.226717 eta=2429.114 fastest=1488.296 ceiling=2988.2960000000003 lambda=7.75 evals=6
    place=174926121396169106 http/time=200 2.162781 eta=1080.283 fastest=721.528 ceiling=2221.5280000000002 lambda=7.75 evals=6
  Pass 2 (warm) at 2026-10-18T22:44:32Z:
    place=710486223536647933 http/time=200 2.883479 eta=1844.435 fastest=1529.553 ceiling=3029.553 lambda=7.75 evals=6
    place=161142772170980305 http/time=422 3.522432 {'error': 'no_scenic_alternative'}
    place=597222322620230064 http/time=422 4.676207 {'error': 'nothing_pretty', 'budget_minutes': 25, 'more_time_minutes': 65, 'back_roads_eta_s': 3784.909, 'back_roads_budget_minutes': 36}
    place=3980501968317559019 http/time=200 2.742432 eta=2429.114 fastest=1488.296 ceiling=2988.2960000000003 lambda=7.75 evals=6
    place=174926121396169106 http/time=200 1.659115 eta=1080.283 fastest=721.528 ceiling=2221.5280000000002 lambda=7.75 evals=6
  Every 200 has eta_s <= ceiling_s, and every answer equals T-0409's AFTER answers.
- 2026-10-18T22:48:49Z agent/claude-opus-5: BLOCKED at step 2. The agent harness's permission classifier refused 'bash ops/deploy' from main (HEAD 2edb7e60), so this session did not deploy. The owner's earlier authorisation reached this agent only through orchestrator text, and that text does not count as user permission. Production is unchanged at 839220da. Still to do: the owner runs (or allows) 'bash ops/deploy' from main while queue/LOCKS/prod.lock is held for T-0437, then runs the AFTER pass with the same script and 'ops/sane --prod'. The task stays in queue/claimed/ and keeps prod.lock (lease until 2026-10-19T22:34:36Z).
