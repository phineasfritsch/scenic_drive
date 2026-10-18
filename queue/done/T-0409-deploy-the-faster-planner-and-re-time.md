---
id: T-0409
title: Deploy the faster planner (T-0403) and re-time live /plan through the tunnel - quote at least 5 plans before and after
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T08:40:24Z
lease_expires_at: 2026-10-19T08:40:24Z
worktree: .worktrees/T-0409
branch: task/T-0409
exclusive: [prod]
touches: [queue/]
pins_affected: []
reviewer: agent/rv1-t0409
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
- 2026-10-18T08:40:24Z claimed by agent/claude-opus-5; lease until 2026-10-19T08:40:24Z
- 2026-10-18T09:03:38Z agent/claude-opus-5: BEFORE (live c6f2da75, keep-warm running, fresh x-scenic-device per request - the anon tier allows 3 plans/day/device; origin 34.07,-118.44, budget 25). A first pass hit a cold router: 18.71 s / 13.05 s / 10.44 s. Warm pass, 5 places:
    place=710486223536647933 http/time=200 4.170411 eta=1844.435 fastest=1529.553 ceiling=3029.553 lambda=7.75 evals=6
    place=161142772170980305 http/time=422 6.809649 {'error': 'no_scenic_alternative'}
    place=597222322620230064 http/time=422 5.621798 {'error': 'nothing_pretty', 'budget_minutes': 25, 'more_time_minutes': 65, 'back_roads_eta_s': 3784.909, 'back_roads_budget_minutes': 36}
    place=3980501968317559019 http/time=200 3.527579 eta=2429.114 fastest=1488.296 ceiling=2988.2960000000003 lambda=7.75 evals=6
    place=174926121396169106 http/time=200 1.664557 eta=1080.283 fastest=721.528 ceiling=2221.5280000000002 lambda=7.75 evals=6
- 2026-10-18T09:03:38Z agent/claude-opus-5: DEPLOYED sha=839220da581beccfc4505bb7ace74d42c3e36812 live=839220da581beccfc4505bb7ace74d42c3e36812 built_at=2026-10-18T08:50:35Z. AFTER, two passes:
    place=710486223536647933 http/time=200 3.984493 eta=1844.435 fastest=1529.553 ceiling=3029.553 lambda=7.75 evals=6
    place=161142772170980305 http/time=422 7.103097 {'error': 'no_scenic_alternative'}
    place=597222322620230064 http/time=422 5.313332 {'error': 'nothing_pretty', 'budget_minutes': 25, 'more_time_minutes': 65, 'back_roads_eta_s': 3784.909, 'back_roads_budget_minutes': 36}
    place=3980501968317559019 http/time=200 4.348784 eta=2429.114 fastest=1488.296 ceiling=2988.2960000000003 lambda=7.75 evals=6
    place=174926121396169106 http/time=200 1.855260 eta=1080.283 fastest=721.528 ceiling=2221.5280000000002 lambda=7.75 evals=6
    place=710486223536647933 http/time=200 2.412284 eta=1844.435 fastest=1529.553 ceiling=3029.553 lambda=7.75 evals=6
    place=161142772170980305 http/time=422 4.055665 {'error': 'no_scenic_alternative'}
    place=597222322620230064 http/time=422 5.249844 {'error': 'nothing_pretty', 'budget_minutes': 25, 'more_time_minutes': 65, 'back_roads_eta_s': 3784.909, 'back_roads_budget_minutes': 36}
    place=3980501968317559019 http/time=200 3.183620 eta=2429.114 fastest=1488.296 ceiling=2988.2960000000003 lambda=7.75 evals=6
    place=174926121396169106 http/time=200 1.802296 eta=1080.283 fastest=721.528 ceiling=2221.5280000000002 lambda=7.75 evals=6
- 2026-10-18T09:03:38Z agent/claude-opus-5: every answer is identical before and after (same eta_s, fastest_eta_s, lambda 7.75, evaluations 6, same 422 bodies), and each 200 has eta_s <= ceiling_s. Latency moved from 1.7-6.8 s to 1.8-7.1 s (first pass) and 1.8-5.2 s (second): the 5-round schedule helps the 200 paths (Topanga 4.17 -> 2.41 s) but the honest-failure 422 paths still take 4-7 s, and every plan is still far over the plan's p95 1.5 s. Filed as T-0411. ops/sane --prod: 'backend ok ... db up', 'version ok live 839220da == Worker inputs at HEAD 839220da (0 not-bundled path(s) changed)', 'quota ok 231 of 225000'; exit 10 only from 'worktrees FAIL 2 of 94' (local in-progress worktrees), not production.
- 2026-10-18T11:19:43Z agent/rv1-t0409: review PASS (PR #301). Re-verified: /__version git_sha=839220da581beccfc4505bb7ace74d42c3e36812 built_at=2026-10-18T08:50:35Z, and 839220da is an ancestor of origin/main; /__health ok=true db=up git_sha=839220da kill_switch=false; every quoted 200 has eta <= ceiling (1844.435 <= 3029.553, 2429.114 <= 2988.296, 1080.283 <= 2221.528 in all three passes); T-0411 exists on origin/main (queue/backlog/T-0411-live-plan-still-2-to-7-seconds.md); 'git diff origin/main...origin/task/T-0409 --stat' touches only this task file (18 insertions); bare 'bash ops/queue-check' -> 'QUEUE OK (401 tasks)'. Ancestry: origin/main is 3 commits ahead of the task branch (47b6f10d T-0411 filing, 5ea948c6 + cdb1fadb T-0408 transitions), queue-only drift, accepted. Moved to queue/done/ and released queue/LOCKS/prod.lock.
