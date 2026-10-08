---
id: T-0309
title: First-run onboarding asks for the vehicle (only "standard car" enabled) and shows the safety disclaimer; VehicleProfile lives in ScenicKit and rides every plan request; Settings shows the vehicle
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T23:30:45Z
lease_expires_at: 2026-10-08T19:30:45Z
worktree: .worktrees/T-0309
branch: task/T-0309
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0294, T-0271]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: how the disclaimer gate works today (SafetyDisclaimer in FeatureScenicHome, P-SAFE-03 'gates the first plan'), where onboarding sits so it cannot weaken that gate (onboarding may show the disclaimer, but the plan gate still reads the same accepted key and still blocks the first plan), and whether VehicleProfile goes on the wire now (the Worker's /plan whitelist - read services/api/src/plan.ts; if it has no vehicle field, the profile stays on device in this task and a follow-up is filed, never widening the Worker here)"
  - "ScenicKit VehicleProfile: a closed enum with .standard enabled and every other case present-but-disabled with its reason (plan: 'only .standard enabled'); an onboarding state machine (vehicle -> disclaimer -> done) with a full-equality transition table and a test that skipping or backing out never marks the disclaimer accepted"
  - "P-SAFE-03 still holds: a test drives first launch through onboarding and shows no plan request before acceptance (counting transport = 0); both bare guards rc=0; any new presentation over the map is full-height or gets a typed whole-line approval (P-ATTR-01), never a widened pattern"
  - "Settings shows the vehicle row; ios-compile + ios-screenshot pass on the head; digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt; a mutation population for the state machine with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Decisions: "Vehicle | VehicleProfile enum, only .standard enabled | Liability floor"; UI: "Onboarding (vehicle,
disclaimer)"; Settings lists vehicle. Neither exists in the code today (grep: no VehicleProfile, no onboarding). Calm copy
(memory owner-route-intent).

## Log
- 2026-10-07T23:30:36Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M4 vehicle + onboarding).
- 2026-10-07T23:30:45Z claimed by agent/claude-opus-5; lease until 2026-10-08T19:30:45Z
