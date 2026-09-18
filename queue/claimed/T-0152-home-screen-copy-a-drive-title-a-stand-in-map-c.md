---
id: T-0152
title: home-screen copy - a drive title, a "stand-in map" caption, and a user-facing message where the screen shows String(describing: error)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:55Z
lease_expires_at: 2026-09-19T04:32:55Z
worktree: .worktrees/T-0152
branch: task/T-0152
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by DRIVER TWO on the 2026-09-18 10:13 panel, grounded by the fable pass. On task/T-0141 (PR #88)
`ScenicHomeScreen.swift` has exactly two readable strings: `Open in Apple Maps` (:67) and the attribution
line. The map is MapLibre demotiles at zoom 8.5 (`:33`, `MapStyle.swift:16`: country polygons, nothing at
Bay Area scale - a blank map, unexplained), the drive is not drawn (MapView has no polyline/annotation
path, only the camera), and a failed handoff reaches the user as `String(describing: error)` (:91), i.e. a
Swift type name.

The friend on the TestFlight link opens it once on a Saturday because "this finds pretty drives". What they
see is a blank map and a button. The button is honest about Apple Maps opening and silent about the drive.

**Do, after PR #88 lands (do not widen that review):**
1. a title above the map naming the drive (`Skyline via Cañada Road` - the handoff already carries the
   waypoints; name what it will hand off) and one honest caption: `Preview build - this map is a stand-in,
   not your route. The drive opens in Apple Maps.` Copy per the plan's rules: active voice, says exactly what
   happens, no apology.
2. a user-facing message in place of `String(describing: error)`: what went wrong and what to do
   (`Couldn't open Apple Maps. Try again, or copy the route.`), the raw error kept in a log line, not on
   screen.
3. no new tokens, no new fonts; DesignSystem stays as it is (the plan's token table). Any `.xcstrings`
   file is serial-only (CLAUDE.md) - declare `exclusive:` if one is introduced; prefer not to introduce one
   until a second language exists.

Bounded: a screen M4 replaces. Do not draw the route line here (that is M4's route preview with real tiles);
do not add the disclaimer here (T-0153 owns it, and it gates the first plan, not the skeleton).

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 10:13 panel (Driver Two, grounded; the "collides with the fixer's edit" opportunity-cost claim was WRONG - ScenicHomeScreen.swift was untouched by the fixer). Not started.
- 2026-09-18T20:32:55Z claimed by agent/claude-opus-5; lease until 2026-09-19T04:32:55Z
