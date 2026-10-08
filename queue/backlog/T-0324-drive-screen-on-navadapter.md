---
id: T-0324
title: The drive screen on NavAdapter - a second map surface with its attribution, the motion-gated minimal surface, the rejoin banner, a door from the plan preview and a drive shot in ios-screenshot
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/, ops/mutate/, pins/PINS.yaml, .github/workflows/ios-screenshot.yml]
pins_affected: [P-ATTR-01, P-SAFE-09, P-SAFE-03]
reviewer: null
depends_on: [T-0321, T-0180]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where the drive screen lives (a feature target that never imports NavAdapter - the shell composes DriveNavigator's mode and surface into it), what the minimal surface holds (the one large action; how the rejoin state is conveyed there) and what the full surface adds, the door that starts a drive from the plan preview, and which check-map-attribution / check-safety-disclaimer rows a second MapView( surface raises"
  - "what the screen shows for a surface and mode is pure ScenicKit (Linux-tested, full-equality tables over every DriveSurface x DriveMode), and the >4.5 m/s minimal surface is what the screen shows (P-SAFE-09's 'What it cannot see' clause closed)"
  - "attribution stays visible on the drive map (P-ATTR-01's whitelist raised by name for the new surface, seen red then green)"
  - "ios-compile + ios-screenshot pass on the branch with a drive shot (a DEBUG `-screen drive` launch over a simulated location), light and dark"
---
## Brief

Filed by T-0321 (R6): NavAdapter's DriveNavigator exposes `mode` and `surface`, and every decision is ScenicKit's
DriveController, but no screen shows them yet. A drive map is a second `MapView(styleURL:` surface, refused by name by
ops/lib/check-map-attribution until its rows are raised; the shot needs ios-screenshot.yml, which T-0180 is editing
(hence depends_on). Also open from T-0321: Ferrostar step durations are 0 (the screen should show PlanPreview's ETA);
spoken guidance (TTS) and Live Activity stay separate follow-ups.

## Log
- 2026-10-08T13:20:42Z filed by agent/claude-opus-5 (owner of T-0321) from T-0321's R6.
