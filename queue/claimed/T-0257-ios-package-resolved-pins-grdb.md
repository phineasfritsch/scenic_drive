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
- 2026-10-05T13:24:06Z agent/claude-opus-5: rulings, then the three runs.
  Rulings: (a) the Brief's cause is the only cause - the probe (flag removed, nothing else) built green, so no
  second defect hides behind resolution. (b) originHash stays 3bd20783...0cfe in the file Xcode wrote: it is
  SwiftPM's hash of the project's own remote package references (MapLibre only), which T-0175 did not change; the
  file is committed as Xcode wrote it, not hand-adjusted either way. (c) the probe's ios-compile.yml change rode
  only on probe/T-0257; this branch's workflow keeps -disableAutomaticPackageResolution (the GREEN run's command
  line quotes it).
  RED (main 764e2a8): https://github.com/phineasfritsch/scenic_drive/actions/runs/37313536457 - exit 74,
  "xcodebuild: error: Could not resolve package dependencies: an out-of-date resolved file was detected at
  .../swiftpm/Package.resolved, which is not allowed when automatic dependency resolution is disabled; ... Running
  resolver because the following dependencies were added: 'grdb.swift' (https://github.com/groue/GRDB.swift.git)".
  PROBE (probe/T-0257 b42d58d, one commit deleting the -disableAutomaticPackageResolution line):
  https://github.com/phineasfritsch/scenic_drive/actions/runs/37313978500 - "** BUILD SUCCEEDED **"; tree step
  " M apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"; artifact
  ios-compile-37313978500 downloaded, its Package.resolved copied in (cmp identical; sha256 0489cb3f...e4c9 for
  both the artifact and HEAD's blob in d57814a). Pins: grdb.swift https://github.com/groue/GRDB.swift.git 7.11.1
  b83108d10f42680d78f23fe4d4d80fc88dab3212 (added); maplibre-gl-native-distribution 6.31.0
  13e41ab3d77ff5113e7e5d4ee87803b1f81f5683 (unchanged); version 3.
  GREEN (task/T-0257 d57814a, flag intact): https://github.com/phineasfritsch/scenic_drive/actions/runs/37315474498
  - "xcodebuild ... -disableAutomaticPackageResolution CODE_SIGNING_ALLOWED=NO build" then "** BUILD SUCCEEDED **";
  tree step porcelain empty (Xcode did not rewrite the committed file).
  probe/T-0257 deleted from origin ("- [deleted] probe/T-0257"; ls-remote count 0). T-9904 on T-0180's branch is
  this task; retire it when T-0180 merges.
