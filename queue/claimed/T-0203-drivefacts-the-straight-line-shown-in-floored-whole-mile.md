---
id: T-0203
title: DriveFacts - the straight line shown in floored whole miles for a US driver, test-pinned exactly like the kilometre figure, and the label says 'as the crow flies' not 'through the pins'
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T13:05:20Z
lease_expires_at: 2026-09-19T21:05:20Z
worktree: .worktrees/T-0202
branch: task/T-0202
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: []
reviewer: null
depends_on: [T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "StraightLineDistance gains wholeMiles(through:) (floored, from the same metres) with a typed literal pinned in Tests/HandoffTests beside the kilometre one (RED first: the literal wrong by one, then green); DriveFacts renders miles for the US build and its label reads as a driver reads it - both LA drivers on the 00:13 panel read '112 km ... through the pins' as an engineer's number (DRIVER TWO guessed 90 minutes from it); the timing line stays"
  - "swift test --scratch-path <own> --filter HandoffTests count line; ios-compile dispatch green with the run id quoted; bash ops/lib/check-line-cap and bash ops/queue-check bare"
---
## Brief

From the 00:13 panel's DRIVER TWO (grounded): 'km, and I think in miles; through the pins means nothing to me; I read
112 and guessed 90 minutes, which the app never said'. The plan's launch scope is US-only. The honest number in the
unit the driver thinks in.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from the 00:13 panel's grounded synthesis (DRIVER TWO-3). Not started; after #110 merges.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): its dependencies (T-0170 via #110, T-0178 via #115) are in done/. ONE BRANCH with its three siblings (T-0202, T-0203, T-0210, T-0212 all edit DriveFacts / DriveCopy / HandoffFailureCard / StraightLineDistance): claim all four together, one PR, one ios-compile. T-0211 (the freeway middle leg) stays in backlog pending the owner's return-leg choice.
- 2026-09-19T13:05:20Z claimed by agent/claude-opus-5; lease until 2026-09-19T21:05:20Z
- 2026-09-19T13:13:49Z RULINGS for all four tasks on this branch are ONE dated entry on T-0202's task file (R0 no Swift toolchain on this box, R1 payload, R2 MILES - this task, R3 timing, R4 chip, R5 P-SAFE-03). R2 is the one that binds here.
- 2026-09-19T13:06:31Z branch: task/T-0203 -> task/T-0202 by agent/claude-fable-5-1 (orchestrator): built on the shared branch with T-0202 (one PR, one ios-compile); no branch task/T-0203 exists.
- 2026-09-19T16:54:35Z PRE-REVIEW FIX ruled on T-0202 (one branch, one PR #121) by agent/claude-opus-5; the rulings live in T-0202's Log and are not repeated here. Bearing on this task: F6 - the LA literal 29 CANNOT separate floor from round (47_445.124 m = 29.4810 mi: floor 29, round 29), so R2's "literals pinned beside the km literals" is a value proof for that chain and not a flooring proof; the Skyline literal 69 (69.7602 mi) and the synthetic theMilesAreFlooredAndNeverRoundedUp (1.988 mi -> 1) are what carry flooring. No code change to StraightLineDistance.
