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
- 2026-10-07T23:34:20Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  - MEASURED. The gate today: `ScenicHomeScreen` owns `@AppStorage("safety.disclaimer.acknowledged.v1") private var
    isSafetyDisclaimerAcknowledged` (the key once; check-safety-disclaimer key_set = PlanSheetScreen.swift(1) +
    ScenicHomeScreen.swift(1), ack_set = GatedHandoffButton(2) + ScenicHomeScreen(6)); the ONE write is
    `isSafetyDisclaimerAcknowledged = true` inside `SafetyDisclaimer(onAccept: {` in the home's `.sheet(isPresented:
    $isShowingDisclaimer)`, which opens only from a blocked handoff tap (`onBlocked`). The plan sheet READS the key and
    feeds `PlanSheet(disclaimerAccepted:)`; `PlanSheet.startPlanning()` returns nil while it is false. There is no
    first-launch presentation: a user who never taps the handoff never sees the disclaimer. ScenicHomeScreen.swift is
    297 lines (3 under the cap). `grep -n -i vehicle services/api/src/plan.ts` = 0 lines: the Worker's /plan body
    whitelist has no vehicle field. `grep -rn VehicleProfile Sources apps` = 0. Entitlements depends on DesignSystem
    only; the shell imports features only (no ScenicKit); Package.swift is serial-only and not in touches.
  - R1 GATE UNTOUCHED. Onboarding is the EXISTING disclaimer sheet grown a first step, not a second writer:
    `SafetyDisclaimer` runs the ScenicKit `Onboarding` machine (vehicle -> disclaimer -> done) and calls the same
    `onAccept` only when the machine reports `disclaimerAccepted`; the write stays the one line inside
    `SafetyDisclaimer(onAccept: {`, key_set is unchanged, and the plan gate reads the same key. The home gains ONE
    line: a `.task` that raises `isShowingDisclaimer` on launch when the key is false or no vehicle is stored (ack_set
    ScenicHomeScreen 6 -> 7, typed in the guard). The sheet keeps `interactiveDismissDisabled()`; no new
    presentation over the map, so P-ATTR-01's surface/presentation whitelist does not move.
  - R2 ON DEVICE. VehicleProfile does NOT go on the wire in this task (plan.ts has no vehicle field; widening the
    Worker is out of scope). It is stored on device under `VehicleProfile.storageKey` and shown in Settings; the
    wire field is a follow-up (stillOpen), never a Worker edit here.
  - R3 TYPES. ScenicKit `VehicleProfile` (closed, CaseIterable: standard, lowClearance, motorcycle, trailer, rv;
    `isEnabled` only for .standard; every other case carries a calm `disabledReason`; `stored(_:)` maps an absent,
    unknown or disabled raw value to .standard). `OnboardingStep` and `OnboardingEvent` (choose, next, back, skip,
    accept) and `Onboarding` (step, vehicle, disclaimerAccepted). The disclaimer cannot be skipped: skip from the
    vehicle step goes to the disclaimer with the vehicle unchanged; skip, back, next or choose never set
    `disclaimerAccepted`; only `accept` on the disclaimer step does. A disabled vehicle is refused (state unchanged).
  - R4 LAYERING. Settings (Entitlements, no ScenicKit) takes `vehicle: String`; the shell passes
    `VehicleSetting.name`, a public FeatureScenicHome enum over ScenicKit (the shell already imports that module).
    The shell's launch corpus offer additionally waits for `VehicleSetting.isChosen`, so the corpus sheet and the
    onboarding sheet are never raised in the same frame (only one sheet presents; the other would be dropped and
    leave `isShowingDisclaimer` stuck true). A fresh install is offered places on its second launch - recorded gap.
  - R5 P-SAFE-03 TEST. ScenicAPIClientTests (CountingPlanTransport) is outside touches; the test lives in
    ScenicKitTests with a counting `RoutePlanning` conformer, driving first launch through `Onboarding` event by event
    and, at every prefix, building `PlanSheet(disclaimerAccepted: onboarding.disclaimerAccepted)`, calling the
    shipping gate `startPlanning()` and the planner on any ticket: count 0 before accept, 1 after (non-vacuous).
  - R6 RED FIRST by name: the tests are committed against stubs that compile and are wrong; population
    ops/mutate/onboarding.py (+_mutations, _run) with a literal floor; three entries shown MISSED with the killer
    suite emptied (--prove-vacuity) and CAUGHT by name after.
