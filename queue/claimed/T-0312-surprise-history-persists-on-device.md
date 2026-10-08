---
id: T-0312
title: The device's Surprise history persists across launches (GRDB user store beside saved drives), so the 90-day no-repeat holds without a session; the card's basis/history split gets a test of its own
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T05:02:47Z
lease_expires_at: 2026-10-09T01:02:47Z
worktree: .worktrees/T-0312
branch: task/T-0312
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PROD-02, P-PRIV-05]
reviewer: null
depends_on: [T-0310, T-0290]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST: the table (a user-store migration beside saved_drive: place id, category, corridor, UTC day - no coordinate, P-PRIV-05), retention (90 days, pruned on write), and how 'Start over' interacts with shown entries (T-0310 R7 keeps them; rule whether that stands - rv1-t0310 recordable 1 flags it for the owner)"
  - "A pure ScenicKit function chooses the card's pick basis vs the recorded history; a table test shows the card never re-picks from the history it records into (rv1-t0310 recordable 2: today only a digest row and the screenshot guard that split)"
  - "Store round-trips by full equality; migration from the in-memory state on first launch; P-PRIV-05 DDL test extended and seen red with a forbidden column; P-PROD-02 still holds; population entries MISSED before and CAUGHT by name after"
---
## Brief

T-0310 stillOpen 3 and rv1-t0310 recordables 1-2 (PR #199): the device Surprise history lives in memory only (R9), so a
relaunch forgets the 90-day no-repeat when there is no session; and the card's basis/history split has no test.

## Log
- 2026-10-08T04:02:40Z filed by agent/claude-opus-5 (orchestrator) from T-0310's stillOpen and rv1-t0310's recordables.
- 2026-10-08T05:02:47Z claimed by agent/claude-opus-5; lease until 2026-10-09T01:02:47Z
