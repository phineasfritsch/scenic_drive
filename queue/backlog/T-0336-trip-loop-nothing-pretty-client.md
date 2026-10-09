---
id: T-0336
title: The app reads /trip's and /loop's 422 nothing_pretty as its own failure with calm copy, not as unexpectedResponse(422)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0335]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0335 (R2, R3, R5) made the Worker refuse a dull road trip - 422 {error: nothing_pretty, days, extra_budget_pct} - and
answer a loop whose every clean attempt was dull with 422 {error: nothing_pretty, minutes}. On T-0335's head
Sources/ScenicAPIClient TripReplyReader and LoopReplyReader map both to their `default` arm,
`.unexpectedResponse(status: 422)`, so the driver sees a generic error where the Worker said "nothing pretty within
reach". MEASURE FIRST: the trip and loop error enums and every switch over them (Sources/ and apps/ios), the copy
rows they reach, and whether a loop's refusal should offer "try a longer loop" (minutes + 40 within
MAX_LOOP_MINUTES 180, as /plan's more_time offer) or a re-roll tomorrow (the seed is per user per UTC day). Then the
acceptance: each reader maps (422, nothing_pretty) to its own case over a table with every field at its bounds and
each field missing / mistyped refused, whole-copy equality for the new rows, the digests re-approved.

## Log
- 2026-10-09T05:23:51Z filed by agent/claude-opus-5 (T-0335 owner) from T-0335 R5.
