---
id: T-0343
title: The app learns corridor speeds - NavAdapter feeds CorridorClock after every fix, the learner persists across launches in PlaceStore, and the preview shows RetimedPreview's ETA and badge (T-0325 R3/R4 follow-up, M7 exit)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Sources/PlaceStore/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0325, T-0342]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed by T-0325 (R3, R4, R7). ScenicKit has the whole Linux path (T-0325): CorridorClock.observe(_ session:, at:,
into:) teaches LearnedCorridorSpeeds the edges the shipped DriveSession drove end to end on the line, and
RetimedPreview.of gives the preview the retimed ETA and badge; five drives clear the badge in
RetimedPreviewTests.fiveDrivesClearTheBadge(). Nothing in apps/ calls either, and the learner lives nowhere.

The claimer MEASURES then RULES: where the one learner lives in the app and who owns it (NavAdapter's
DriveNavigator.forward builds each DriveFix from location.timestamp; the clock needs the session after
controller.observe and that Date); PlaceStore persistence across launches - a user-store table of (cell, hour, ratio,
samples) with no column matching /home|address|breadcrumb|trail|speed/ (UserStorePrivacyTests compares the whole
column map), a restore initializer on LearnedCorridorSpeeds that validates every row by full-equality tables over
every bound (hour 0...167, ratio [0.3, 1.0], samples >= 1), no Codable anywhere (P-PRIV-05 whitelist re-approved for
every new site, including the app's); PlanAdapter/PlanPreviewCard showing RetimedPreview.of with departsAt = now. The
GRDB-gated suites run only in CI linux-core. iOS screenshots looked at.

## Log
- 2026-10-09T11:37:54Z filed by agent/claude-opus-5 (T-0325 owner) from T-0325 R3/R4/R7.
