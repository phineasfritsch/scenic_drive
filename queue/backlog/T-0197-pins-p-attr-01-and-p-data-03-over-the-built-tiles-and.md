---
id: T-0197
title: pins - P-ATTR-01 (the Protomaps attribution visible on every map surface at every detent) and P-DATA-03 (PMTiles/corpus meta.region == the active region; built_at under 30 days) entered in pins/PINS.yaml with runs_on and assertions that run
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, services/tiles/, ops/lib/]
pins_affected: [P-ATTR-01, P-DATA-03]
reviewer: null
depends_on: [T-0165, T-0195]
verify: [ops/test, ops/check-pins]
acceptance:
  - "P-DATA-03 (runs_on: [linux]) asserts through services/tiles/check_pmtiles.py over the built artifact that meta.region equals the active region and built_at is under 30 days - seen red on a stale built_at fixture first; the corpus half names the corpus manifest field it reads or is recorded as pending with the task that owns it"
  - "P-ATTR-01 (runs_on: [mac]) names the XCUITest identifier and the snapshot it will assert over once T-0180's XCUITest half exists; until then its assertion is the structural check that MapStyle's attributionText for the protomaps case is the plan's string and that AttributionFooter is not accessibilityHidden (a grep-free anchor on identifiers), demonstrated red first"
  - "bash ops/check-pins --source-only bare at the final commit; PINS.yaml ids unique"
---
## Brief

From T-0165's STILL OPEN 6 (PR #109): the plan's pin table carries P-ATTR-01 and P-DATA-03 and pins/PINS.yaml has
neither (grep -c -> 0). T-0165 built the artifact P-DATA-03 asserts over; T-0195 puts the Protomaps string on the
surface P-ATTR-01 asserts over.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 6 (PR #109). Not started; after T-0195.
