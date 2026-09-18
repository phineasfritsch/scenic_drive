---
id: T-0010
title: Thin .xcodeproj shell with Xcode 26 buildable folders + apps/ios/Packages/ScenicApp package (Mac session)
state: done
owner: agent/claude-fable-5-1
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [pbxproj, package-swift]
touches: [apps/ios/, Package.swift]
pins_affected: []
reviewer: agent/rv2-pr88
depends_on: [T-0001]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "xcodebuild -list shows scheme ScenicDrive; xcshareddata/xcschemes and Package.resolved committed"
  - "SKIP_IOS=0 ops/test on the Mac prints ios=N/0 with N >= 1"
  - "RED: swift test at the root on Linux still passes and never resolves MapLibre/Ferrostar"
---
## Brief

~2 MacinCloud hours. App target = buildable folder apps/ios/ScenicDrive. ScenicApp package depends on the root by path.

## Log
- 2026-09-18T02:50:00Z superseded in scope by [[T-0141]] (the same tree, authored here and compiled by Xcode Cloud); moves to done/ when T-0141's PR merges.
- 2026-09-18T18:20:00Z moved to done/ by agent/claude-fable-5-1: superseded by T-0141, merged as PR #88 (e3bc79a). Its deliverable - the thin pbxproj with a buildable folder, the shared scheme, ci_post_clone.sh - was reviewed in that PR by agent/rv2-pr88 (round 2 PASS), who is recorded as reviewer here for that reason; nobody reviewed this task on its own.
