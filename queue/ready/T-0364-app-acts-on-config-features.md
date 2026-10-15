---
id: T-0364
title: The app acts on /config's feature_loop, feature_trip and feature_surprise and degrades the Loop, Trip and Surprise entry points before the tap, as T-0357 did for Plan
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0357]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0357 (R1) reads only `min_app_build` and `planning_paused` from GET /config and gates only PlanSheet's Plan
button. The Worker also sends `feature_loop`, `feature_trip`, `feature_surprise` (booleans, services/api/src/config.ts
FIELDS), and under the kill switch /loop and /trip answer 503 planning_paused too (loop.ts, trip.ts) - the app learns
that only after the tap.

MEASURE FIRST: which screens send /loop, /trip and Surprise Me today, what each shows on 503 planning_paused, and
what a `feature_* = false` answer should do per screen (hide, or the typed copy). RULE whether ConfigReader's
whole-answer refusal (T-0357 R2) extends to the three booleans or whether they decode per field (a garbled feature
flag must not throw away a valid pause). Then tests through the shipping ConfigClient and ConfiguredPlanner, the
degrade as a table over every flag, P-SAFE-03 digests, and the config.py population widened to the new logic.

## Log
- 2026-10-15T19:35:43Z filed by agent/claude-opus-5 as T-0357's follow-up (T-0357 R1). Ids checked on origin/main
  and every origin/task/* branch: highest T-0363, so T-0364.
