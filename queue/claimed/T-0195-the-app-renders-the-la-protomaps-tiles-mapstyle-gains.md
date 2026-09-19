---
id: T-0195
title: the app renders the LA Protomaps tiles - MapStyle gains a protomaps case (the built la.pmtiles through MapLibre's pmtiles protocol, services/tiles/styles as the style), attributionText becomes '(c) OpenStreetMap contributors - Protomaps', the demo-tiles case retired from the walking skeleton
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T06:53:46Z
lease_expires_at: 2026-09-19T12:53:46Z
worktree: .worktrees/T-0195
branch: task/T-0195
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/]
pins_affected: []
reviewer: null
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MapStyle has a protomaps case whose style is one of services/tiles/styles/*.json (light/dark by appearance) and whose source is the LA PMTiles - RULE in the Log how the file reaches the device in this build (bundled in the app target for the walking skeleton, sized and quoted; the first-run download sheet is M4's) and how MapLibre reads it (the pmtiles:// protocol handler pinned by version in Package.resolved - exclusive: on that file if it changes); attributionText for that case is exactly '(c) OpenStreetMap contributors - Protomaps' (the plan's string, the (c) as the copyright sign) and a Linux-free test in the Apple package or a structural check pins it"
  - "the home screen's map surface uses the protomaps case; AttributionFooter shows the Protomaps string at every detent (the invariant); ios-compile dispatch green with the run id quoted; no MapLibre import outside MapAdapter (the structural check the package already has)"
  - "the demo-tiles case stays only if something still needs it - say what, or delete it and its '(c) MapLibre - Natural Earth' string"
  - "bash ops/lib/check-line-cap and bash ops/queue-check bare at the final commit"
---
## Brief

From T-0165's STILL OPEN 3 (the PMTiles build, PR #109): the artifact exists and the corner is reserved, but the
app still renders MapLibre's demo tiles and credits '(c) MapLibre - Natural Earth' - the product invariant
(attribution visible on every map surface) is only half met until the tiles ARE Protomaps and the string is the
plan's. M1.5's exit clause is the owner opening the app on the phone and tapping into Apple Maps on a drive the
owner can drive - in Los Angeles, over LA tiles. T-0009 (TestFlight) is the human step that puts it on the phone.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 3 (PR #109). Not started; after #109 merges.
- 2026-09-19T06:53:41Z PROMOTED to ready/ by agent/claude-fable-5-1: #109 (T-0165) merged e31a7f1 - la.pmtiles 63,520,949 bytes is on disk in the shared work dir and the styles are committed; this task is the tiles-to-phone half the 00:13 panel named, and it touches MapAdapter/DesignSystem only, so it does not collide with #110 or T-0178 on ScenicHomeScreen.swift.
- 2026-09-19T06:53:46Z claimed by agent/claude-opus-5; lease until 2026-09-19T12:53:46Z
