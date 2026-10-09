---
id: T-0334
title: The plan sheet acts on a nothing_pretty answer's offers - "+40" re-plans at budget + 40 and "all back roads" plans the lambda-8 route with its real ETA - instead of only showing the honest-failure line
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04, P-COST-04]
reviewer: null
depends_on: [T-0332]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0332 R7 (owner ruling): the Worker answers 422 `nothing_pretty` with `budget_minutes`, `more_time_minutes`
(budget + 40, or null past 180) and `back_roads_eta_s` (the MAX_LAMBDA route's real ETA when it scores >= 0.45, else
null), and the client reads them into `PlanError.nothingPretty(NothingPrettyOffer)`. The sheet shows only the
payload-free line ("Not much pretty within reach of this drive. More time might find some.") with
`.chooseAnotherPlace`: neither offer is actionable yet.

MEASURE FIRST, then write the acceptance: how PlanSheetState / PlanOutcome carry a failure today (payload-free
PlanSheetFailure), where the sheet's budget control lives, and what a back-roads plan must send - a request field the
Worker whitelists (planRequest.ts BODY_KEYS, P-PRIV-05) that plans at lambda 8 and answers that route with its real
ETA. Rule against P-SAFE-04 before code: the back-roads ETA may exceed fastest + budget, so either the request names
a budget that covers it (the driver chose more time) or the invariant's wording is ruled with the owner - never a
silent over-ceiling 200. Each offer is one more plan (P-COST-04, quota). Copy names the minutes ("within 25 minutes")
once the failure carries them to the sheet. Apple files change: ios-compile and ios-screenshot green, shots looked at.

## Log
- 2026-10-08T21:58:00Z filed by agent/claude-opus-5 (T-0332 owner) from T-0332 R7.
