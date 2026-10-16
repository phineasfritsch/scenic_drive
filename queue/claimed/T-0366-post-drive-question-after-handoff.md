---
id: T-0366
title: After a handoff the app asks "Prettier than your usual way?" at the next open, only with a known stopped speed
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T18:23:44Z
lease_expires_at: 2026-10-17T18:23:44Z
worktree: .worktrees/T-0366
branch: task/T-0366
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0358]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0358 R3 ruled the free tier's trigger "at the next open after a handoff" (region monitoring needs an owner
capability) and put it in ScenicKit's model: `PostDriveQuestion.asks(outcome: .handedOff, moment: .appOpened,
surface: .full, alreadyAsked: false)` is the only next-open row that asks. The APP half was not wired, because the
home has no speed: FeatureScenicHome imports no CoreLocation, and P-SAFE-09 treats an unknown speed as moving, so a
next-open question would either never show or show to a moving driver.

MEASURE FIRST: what a handoff leaves behind today (T-0358 M2: nothing - GatedHandoffButton and the Surprise card open
Apple Maps and record nothing); where a one-shot location fix with a speed can come from (NavAdapter owns
CoreLocation through Ferrostar's provider; the shell composes NavAdapter and the features).
RULE: the handoff marker (a Bool or a drive counter only - no place, no time finer than needed, no route; P-PRIV-05),
when it expires, the one-shot fix (permission already granted for drives; never prompt for it here), how the home
receives the surface (an environment value or closure set by the shell, as `postDriveAnswers` is), where the
question renders (the home sheet, not a modal), and that the answer goes through the same `postDriveAnswers` sink.
Tests: the model's next-open rows already exist (PostDriveQuestionTests.everyRow); add a table over the marker's
lifecycle (handoff -> open stopped/moving/unknown -> asked/skipped -> next open) through the shipping entry point.
Every apps/ios Swift edit re-approves its P-SAFE-03 digests; the shell's frozen lines move in the same commit.

## Log
- 2026-10-15T22:52:00Z filed by agent/claude-opus-5 from T-0358 R3 (the free tier's next-open trigger, app half).
- 2026-10-16T18:23:44Z claimed by agent/claude-opus-5; lease until 2026-10-17T18:23:44Z
