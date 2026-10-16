---
id: T-0369
title: surprise_arrived has no moment - the Surprise hands the place to Apple Maps and the app never learns of an arrival
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0361]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0361 (M3/R9) measured that `surprise_arrived` has no moment in the app: the Surprise card's Open in Apple Maps goes
through GatedHandoffButton to SkylineHandoff.open(place:) and the app is never told the driver got there. The case
stays `pending surpriseArrived T-0369` in ops/lib/check-telemetry-emit-sites.txt.

MEASURE FIRST, then rule one of: (a) an arrival signal the app can honestly observe without a coordinate leaving the
device (e.g. the next app open asks "did you go?" - a post-drive-question shape, T-0358), or (b) retire the case from
the closed enum (a Telemetry + Worker change with its own pin rows). Whatever is ruled must keep P-PRIV-05: payload is
a label, never a place.

## Log
- 2026-10-16T02:32:24Z filed by agent/claude-opus-5 (T-0361 owner) from T-0361 R9.
