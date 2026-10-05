---
id: T-0257
title: main's iOS build is red since T-0175 - the app's Package.resolved does not pin GRDB; regenerate it on the macOS runner and commit it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T12:56:22Z
lease_expires_at: 2026-10-05T18:56:22Z
worktree: .worktrees/T-0257
branch: task/T-0257
exclusive: [package-resolved]
touches: [apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved]
pins_affected: []
reviewer: null
depends_on: [T-0175]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the committed apps/ios/.../swiftpm/Package.resolved is the file Xcode itself wrote on the macOS runner (a throwaway probe branch dispatching ios-compile.yml with -disableAutomaticPackageResolution removed; the existing 'keep the log and any Package.resolved' step uploads it) - never hand-computed, because originHash is SwiftPM's; it pins GRDB.swift at 7.11.1 revision b83108d10f42680d78f23fe4d4d80fc88dab3212 and keeps maplibre-gl-native-distribution 6.31.0 unchanged"
  - "RED: ios-compile dispatched on main's head fails with 'an out-of-date resolved file was detected' (quote the run URL; T-0180's run 37306886723 is the first sighting); GREEN: ios-compile dispatched on the task branch (with -disableAutomaticPackageResolution intact) builds - run URL quoted; the probe branch is deleted from origin"
---
## Brief

T-0175 (PR #142, 186ba80) declared GRDB in the root Package.swift on every non-Windows host. The iOS app package
depends on the root package by path, so Xcode must resolve GRDB too, and the app's tracked Package.resolved (T-0167)
pins only MapLibre. Every ios-compile / ios-screenshot run with -disableAutomaticPackageResolution now refuses before
compiling: found by T-0180's confirmation run 37306886723 on its merge of main (T-0180 filed it as T-9904 on its
branch - the ops/new-task T-0128 stray-ref bug; this is that task under a real id, and T-9904 should be retired when
T-0180 merges). Blocks T-0180's merge and every iOS run.

## Log
- 2026-10-05T12:53:29Z filed by agent/claude-opus-5 (orchestrator), from T-0180's final pre-review Log.
- 2026-10-05T12:56:22Z claimed by agent/claude-opus-5; lease until 2026-10-05T18:56:22Z
