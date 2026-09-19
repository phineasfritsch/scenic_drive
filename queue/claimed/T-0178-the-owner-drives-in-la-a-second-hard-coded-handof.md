---
id: T-0178
title: the owner drives in LA - a second hard-coded handoff drive (Sunset / PCH / Topanga / Mulholland) selectable on the home screen, pins Nominatim-verified like Skyline's
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T07:47:40Z
lease_expires_at: 2026-09-19T13:47:40Z
worktree: .worktrees/T-0178
branch: task/T-0178
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: [T-0153, T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/Handoff/ gains a second route type (one type per file, e.g. SantaMonicaMountainsRoute) with at most nine pins, every coordinate reverse-geocoded by Nominatim before it is written (way id + road name quoted beside the literal, one request per second, a descriptive User-Agent), destination and pins inside regions/la's bbox; a Linux test types out the pin count, the leg order and the maximum consecutive spacing per leg, RED by name when a pin is removed"
  - "the home screen offers BOTH drives (a two-row picker or segmented control, DesignTokens only, identifiers home.drive.skyline / home.drive.la, 44 pt), the title and road line follow the selected drive, the LA drive is the default when the device locale region or the last-known coarse position is Southern California - rule it, and say what happens with Location denied (the plan's 5.1.1(iv) case)"
  - "ios-compile dispatch on the branch green with the run id quoted; bash ops/lib/check-line-cap, bash ops/queue-check, bash ops/lib/check-safety-disclaimer bare at the final commit"
---
## Brief

The owner lives and commutes in Los Angeles. The plan's success criterion is "the developer drives a route this
app made" (plan:22), and every human gate is a drive; the M1.5 skeleton's only drive is the Bay Area Skyline
loop (T-0151), which the owner can check on a desk in Apple Maps or Google Maps but cannot drive. The LA region
exists on main (`services/etl/regions/la/region.json`, T-0107, PR #68, UCLA-centred bbox; T-0142 notes the
bbox's Orange County sliver).

Build the LA counterpart of T-0151 with T-0151's discipline: a loop the owner would take on a weekday evening
with 25 spare minutes - the 405 or the 10 as the freeway baseline, the scenic middle on Sunset Boulevard west,
PCH north, Topanga Canyon Boulevard up, Mulholland Drive east, back down (Sepulveda or the 405) - decision-point
pins only, the CA-27/Topanga and Mulholland junctions pinned so Apple Maps cannot shortcut through the canyon
residential grid (the rat-run the plan forbids), and the same ridge-leg spacing bound. Rule in the Log, before
code: which roads (with the Nominatim way ids), the order property that is actually true for this loop, why
each junction pin exists, and the school-zone cut-throughs the pins must exclude (Topanga's residential
streets; the Mulholland side streets). Do NOT touch SkylineRoute.swift or its tests; do not add the route line
(M4).

## Log
- 2026-09-19T00:49:41Z filed by agent/claude-fable-5-1 from the owner's instruction ("I am in LA"); depends on T-0153 because both edit ScenicHomeScreen.swift. Not started.
- 2026-09-19T06:29:45Z depends_on += T-0170 by agent/claude-fable-5-1 (00:13 panel, grounded): #110 also edits apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (10 lines, git diff --stat origin/main...origin/task/T-0170), the file this task touches; starting after #101 but before #110 merges conflicts on it. Both LA drivers on the 00:13 panel stopped on the same two strings - 'Skyline loop - ends back in San Francisco' and the I-280/Canada/CA-92/Skyline road line - 'it is not my drive'; this task is the only queued item that puts a drive the owner can start on the screen. NEXT START the moment #101 and #110 are both merged.
- 2026-09-19T07:47:40Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:47:40Z
