---
id: T-0212
title: DriveCopy/DriveSelector - the Bay Area chip says what it is, or the picker shows local drives only
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T13:05:22Z
lease_expires_at: 2026-09-19T21:05:22Z
worktree: .worktrees/T-0202
branch: task/T-0202
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/]
pins_affected: []
reviewer: null
depends_on: [T-0178]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the second drive's chip names its place (it is a San Francisco Peninsula drive) so an LA user does not read it as a mistake, or the picker hides non-local drives - rule which without reading a location; identifiers unchanged; ios-compile green"
---
## Brief

DRIVER TWO, 03:13 panel (grounded, DriveCopy.swift:33,:55): the second chip reads as 'somebody else's bookmark left
in my app'. Low priority; rides with T-0210/T-0203 on the same files.

## Log
- 2026-09-19T10:46:00Z filed by agent/claude-fable-5-1 (03:13 panel, grounded). Not started; low priority.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): its dependencies (T-0170 via #110, T-0178 via #115) are in done/. ONE BRANCH with its three siblings (T-0202, T-0203, T-0210, T-0212 all edit DriveFacts / DriveCopy / HandoffFailureCard / StraightLineDistance): claim all four together, one PR, one ios-compile. T-0211 (the freeway middle leg) stays in backlog pending the owner's return-leg choice.
- 2026-09-19T13:05:22Z claimed by agent/claude-opus-5; lease until 2026-09-19T21:05:22Z
- 2026-09-19T13:13:49Z RULINGS for all four tasks on this branch are ONE dated entry on T-0202's task file (R0 no Swift toolchain on this box, R1 payload, R2 miles, R3 timing, R4 THE SECOND CHIP - this task, ruled A: it names its place, 'SF Peninsula'; B refused because 'local' needs a location this app never reads. R5 P-SAFE-03). R4 is the one that binds here.
- 2026-09-19T13:06:31Z branch: task/T-0212 -> task/T-0202 by agent/claude-fable-5-1 (orchestrator): built on the shared branch with T-0202 (one PR, one ios-compile); no branch task/T-0212 exists.
