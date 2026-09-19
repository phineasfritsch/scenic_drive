---
id: T-0203
title: DriveFacts - the straight line shown in floored whole miles for a US driver, test-pinned exactly like the kilometre figure, and the label says 'as the crow flies' not 'through the pins'
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
