---
id: T-0401
title: plansheet mutation population gains T-0396's preview lines (whyLine, etaHero, routeMeters, distanceLabel)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/plansheet_mutations.py, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0396]
verify: [ops/test]
acceptance: []
---
## Brief

T-0396 added arithmetic to Sources/ScenicKit/PlanSheet/PlanPreview.swift (a PREVIEW subject of
ops/mutate/plansheet_mutations.py) but its touches did not include ops/mutate/. Its Log records five hand mutants
all killed by Tests/ScenicKitTests/PlanSheet/PlanPreviewLinesTests.swift: the tenths bound `< 100` -> `<= 100`,
the `route.count >= 2` guard -> `>= 1`, the leg sum -> ends only, tenths truncated instead of rounded, and the why
line counting etaMinutes. Add those five as rows (killers = the PlanPreviewLinesTests display names), add the test
file to TEST_FILES, raise the literal floor by five, and show the driver run green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0396 (mutation population outside its touches).
