---
id: T-9904
title: main's iOS build is red since T-0175 (186ba80): root Package.swift declares GRDB on non-Windows hosts, and apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved does not pin it, so every -disableAutomaticPackageResolution build refuses with 'an out-of-date resolved file was detected' (T-0180's run 37306886723 on its merge of main); regenerate Package.resolved on a Mac runner (exclusive)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [package-resolved]
touches: [apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
