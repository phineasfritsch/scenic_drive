---
id: T-0341
title: closures_hazard reaches the app - a stale or unavailable closures snapshot, a dropped closure or a crossed closure on a plan, trip or loop answer is told to the driver in calm copy, not silently decoded away
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: [P-SAFE-02]
reviewer: null
depends_on: [T-0339]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0339 M2 (measured at bdb77ca6): the Worker adds `closures_hazard` {state: fresh|stale|unavailable, version,
fetched_at, dropped?, crosses?} to plan / trip / loop / isochrone 200s (services/api/src/closuresStore.ts:93) and no
Swift file reads it (grep closures_hazard over Sources and apps/ios: 0 hits). A plan built on a stale closures set, or
one that crosses a closure, looks identical to a fresh one on screen. MEASURE FIRST (every state and field the Worker
can send, every card that shows a route), RULE the copy into T-0339's HazardCopy table, then the acceptance: readers
fail-closed, one line per condition, whole-copy equality, shots looked at.

## Log
- 2026-10-09T08:33:30Z filed by agent/claude-opus-5 from T-0339 R4.
