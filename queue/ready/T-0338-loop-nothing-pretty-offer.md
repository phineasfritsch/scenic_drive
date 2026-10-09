---
id: T-0338
title: A dull loop's 422 nothing_pretty carries the Worker's own "try a longer loop" offer, and the app acts on it
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: []
reviewer: null
depends_on: [T-0337]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0337 R2 ruled that the app offers no "try a longer loop" on /loop's 422 {error: nothing_pretty, minutes}: the body
carries only the request's minutes, and an offer of minutes + 40 computed on the device would be a server field
invented on the client. /plan's offer is the Worker's (honestFailure.ts more_time_minutes = budget + 40, nil past 180;
the app acts on it since T-0334). If the owner wants the same for loops, the Worker answers it: loop.ts's
nothing_pretty gains `more_time_minutes` (minutes + 40 when <= MAX_LOOP_MINUTES 180, else null), the client's
LoopNothingPretty reads it fail-closed (present, null or exactly minutes + 40 within 180), and the loop screen offers
"Try a longer loop" that re-plans with those minutes through LoopSheet's gate.

MEASURE FIRST: whether a longer loop from the same start and the same (user, UTC day) seed is any likelier to clear
RouteScore's 0.45 - run the loopHonest harness's dull rows at minutes and minutes + 40 and quote both. If it is not,
the offer is a promise the planner cannot keep, and this task closes with that measurement instead.

## Log
- 2026-10-09T07:34:39Z filed by agent/claude-opus-5 (T-0337 owner) from T-0337 R2.
