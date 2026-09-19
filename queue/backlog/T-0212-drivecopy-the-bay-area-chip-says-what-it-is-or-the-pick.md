---
id: T-0212
title: DriveCopy/DriveSelector - the Bay Area chip says what it is, or the picker shows local drives only
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
