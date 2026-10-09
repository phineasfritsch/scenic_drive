---
id: T-0349
title: The app wires the corridor learner - DriveNavigator feeds CorridorLearner.observe per fix, LivePlanner retimes answers through RetimingPlanner over one learner restored from CorridorRatioStore, and the shell hands it to DriveHost (T-0343 R9; needs an owner-approved P-SAFE-03 digest edit)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-learned-speeds-sites.txt, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0343]
verify: [ops/check-pins]
acceptance:
  - "NavAdapter: DriveNavigator(preview:sender:learner: CorridorLearner? = nil) holds clock = learner?.clock(for: preview), and forward(_:) calls learner.observe(coordinate:speedMetersPerSecond:at: location.timestamp, on: &controller, clock: &clock) per fix when it has a learner (controller.observe on the same DriveFix otherwise); DriveHost(preview:sender:learner:content:) passes it through"
  - "PlanAdapter: one @MainActor learner (LivePlanner.learner or a LiveCorridorLearner type), restored from CorridorRatioStore at Application Support/user.sqlite via LearnedCorridorSpeeds(timeZone: .current, restoring:) (nil or a failed store -> an empty learner), saving rows through replaceAll(with:); LivePlanner.make() answers RetimingPlanner(inner: ClientPlanner(...), learner:, now: { Date() })"
  - "The shell's DriveHost line passes the learner; ops/lib/check-safety-disclaimer-frozen's approved shell line and ops/lib/check-safety-disclaimer-pinned's digests re-approved in the same commit BY THE OWNER or with the owner's permission (the permission classifier refused an agent's re-approval on 2026-10-09, T-0343 R9)"
  - "P-PRIV-05: every new app line naming a guarded identifier approved in ops/lib/check-learned-speeds-sites.txt, seen red first; ios-compile and ios-screenshot success with the plan-preview and drive shots looked at"
---
## Brief

Filed by T-0343 (R9). T-0343 shipped the Linux slice - ScenicKit's CorridorLearner (the drive's one feed: the
controller first, then the CorridorClock at the fix's own Date, a save of the whole table when an edge is taught),
RetimingPlanner (the plan answer retimed at answer time), LearnedCorridorSpeeds(timeZone:restoring:) with every bound,
and PlaceStore's CorridorRatioStore over the user store's v4 corridor_ratio table. Its app edits were written and
compiled into nothing: every Swift file under apps/ios is byte-pinned by P-SAFE-03 (ops/lib/check-safety-disclaimer-
pinned, rv2-t0273 B1) and the shell's DriveHost line is a frozen render block, and the agent's re-approval of those
digests was refused by the permission classifier. This task is that wiring, with the digest edit made or permitted
by the owner. The exact diff is in T-0343's Log (R1, R4, R9).

## Log
- 2026-10-09T18:15:30Z filed by agent/claude-opus-5 (T-0343 owner) from T-0343 R9.
