---
id: T-0236
title: the map draws the drive - the engine's Saddle Peak route becomes the app's first drive, its real road geometry drawn as a line on the map with the camera fitted to it; the credit pill stops covering MapLibre's (i) button
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/]
pins_affected: [P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0182, T-0199]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a third HandoffDrive, the engine's route from PR #124 (Topanga village -> Fernwood Pacific -> Tuna Canyon -> Saddle Peak -> Schueren -> Piuma -> Malibu Canyon; ops/plan over Tests/Fixtures/t0182/plan-pair at +25, lambda 7.75): its nine decision-point waypoints and destination EXACTLY as ops/plan printed them (the URL is quoted in T-0182's Log), its name, road list and sentences in the same shape the other two drives use (digit-free timing sentence, the card's own sentence, the straight-line figure through StraightLineDistance), becomes the DEFAULT and FIRST drive in the picker; the Westwood loop and the SF Peninsula stay as the second and third choices. Every existing Linux test that iterates HandoffDrive.allCases stays green with the new case, and the new drive's own literals are pinned RED first"
  - "the road GEOMETRY of that route - the recorded GraphHopper path (1,393 points), simplified with a stated tolerance in metres and the resulting point count quoted - ships as a bundled GeoJSON LineString under apps/ios/ScenicDrive/ (the buildable folder syncs it into the app, no Package.swift or pbxproj edit), produced by a committed deterministic script from the fixture so it can be re-derived; MapAdapter draws it as a line layer in the `route` token colour with a casing, above the basemap and below the labels, and fits the camera to its bounds with padding that clears the sheet and the button; a drive WITHOUT geometry (the loop, the Peninsula) draws no line and keeps today's camera - never straight lines between pins, which would cross the mountains"
  - "the map caption for the Saddle Peak drive says the line is the route the engine chose over Saddle Peak instead of PCH; the other drives keep theirs. The credit pill no longer overlaps MapLibre's own attribution (i) button (the first screenshots show it covered at bottom right): move one or the other and rule why the (i) stays reachable (it is MapLibre's attribution control - never hide it)"
  - "bash ops/lib/check-map-attribution + --prove-red, bash ops/lib/check-drive-copy + --prove-red (its typed case-site counts updated for the new case), bash ops/lib/check-safety-disclaimer (P-SAFE-03 counts unchanged), swift test --scratch-path .build/T0236 --filter HandoffTests count line, python ops/lib/check-mutate-population.py (any new numeric symbol populated or allowlisted with a reason), check-line-cap, check-exec-bits, queue-check bare; ios-compile green on the head; then ONE dispatch of ios-screenshot.yml on the branch and the two PNGs downloaded to the MAIN checkout's .artifacts/screens/ as home-light-T0236.png / home-dark-T0236.png, what they show described in the Log (the line on the map, the camera, the pill clear of the (i))"
---
## Brief

The first screenshots of the app ever taken (PR #127, run 36180944684, iPhone 17 / iOS 26.2) show a coherent home
screen and a map that shows nothing: no route, and a caption that says so ("The map doesn't show roads yet"). The
credit pill also sits on top of MapLibre's (i) button. The owner, shown the engine's first route as a web preview,
answered "looks promising" - that route is Topanga to Malibu over Saddle Peak and Piuma instead of PCH, and it is
the only drive we have REAL road geometry for (the recorded GraphHopper path in Tests/Fixtures/t0182/plan-pair/
lambda-7.75.json). Making it the first drive, drawn, is the single change that turns the walking skeleton into
something presentable. It is also plan:22's success criterion in the app itself: "a route this app made".

The loop's freeway middle leg (T-0211) is untouched here and still owed; the loop simply stops being the default.

## Log
- 2026-09-25T20:18:52Z filed by agent/claude-opus-5-5 (orchestrator, from the first CI screenshots of the app - PR #127's run 36180944684). Starts when PR #124 (T-0182, the route) and PR #125 (T-0199, Tests/HandoffTests) have merged.
