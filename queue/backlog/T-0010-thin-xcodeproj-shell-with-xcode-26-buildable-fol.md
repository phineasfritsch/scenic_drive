---
id: T-0010
title: Thin .xcodeproj shell with Xcode 26 buildable folders + apps/ios/Packages/ScenicApp package (Mac session)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [pbxproj, package-swift]
touches: [apps/ios/, Package.swift]
pins_affected: []
reviewer: null
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
