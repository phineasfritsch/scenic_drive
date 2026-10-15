---
id: T-0365
title: Loop and Trip sheets offer "Count this area" on regionUnsupported through the same WaitlistClient, once per cell per install
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0360]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0360 (PR #245) R1 gave the plan sheet's regionUnsupported failure the `.joinWaitlist` action ("Count this area"),
backed by ScenicAPIClient's WaitlistClient (one res-5 cell from the start rounded to 2 dp, once per cell per
install, six answers each with its line). Loop and Trip were ruled out of scope there: LoopFailure and TripFailure
still offer no waitlist on their regionUnsupported failures (rv1-t0360 recordable 2).

MEASURE FIRST: how regionUnsupported reaches LoopFailure / TripFailure today and what start each carries. RULE the
action and copy (reuse PlanFailureAction.joinWaitlist and WaitlistAnswer lines; the same WaitlistMemory so a cell
joined from any sheet is joined once). Tests: the failure-copy tables for Loop and Trip gain the row (whole-line
equality); a cross-sheet row that a cell joined from Plan answers alreadyJoined from Loop with zero requests. Every
apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-15T22:30:00Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0360 recordable 2 / T-0360 R1.
