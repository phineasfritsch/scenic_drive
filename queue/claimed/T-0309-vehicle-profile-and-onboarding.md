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
- 2026-10-08T00:15:00Z BUILT. agent/claude-opus-5 (owner).
  - RED FIRST (deviation: the stubs were run, not committed - VehicleProfile.isEnabled `true`, disabledReason
    `nil`, Onboarding.send setting `disclaimerAccepted = true` on every event). `swift test --filter
    ScenicKitTests\.(OnboardingTransitionTests|VehicleProfileTests|OnboardingPlanGateTests)` against them:
    `× "accept marks the disclaimer accepted only from the disclaimer step"`, `× "stored: absent, unknown and
    disabled raw values read back as standard"`, `× "first launch through onboarding: zero plan requests before
    accept, one after"`, `× "only standard is enabled; every other case is present with its reason, whole"`,
    `× "transition table: send(event) from each state equals the row's whole expected value"`, `× "skipping or
    backing out never marks the disclaimer accepted"`; `Test run with 8 tests in 3 suites failed ... with 75
    issues`. GREEN with the bodies, PlanSheetTests alongside: `Test run with 18 tests in 4 suites passed`.
  - GUARDS. First run refused by name: ack_set (`ScenicHomeScreen.swift(7)` vs 6), frozen FROZEN_SCREEN_BODY line
    28 and FROZEN_APP_SHELL line 10, then the FeatureScenicHome file set (`added VehicleChoice.swift
    VehicleSetting.swift`). Retyped as whole lines: ack_set 6 -> 7 with its reason line; the `.task` line in
    FROZEN_SCREEN_BODY; the corpus and Settings lines in FROZEN_APP_SHELL and DOORS_VIEWS; digests re-approved in
    -pinned (PINNED_FEATURE +2, PINNED_APP_SWIFT +2 and SafetyDisclaimer/ScenicHomeScreen/SettingsScreen/shell,
    PINNED_SHELL_DIGEST) and in check-safety-disclaimer-linked-digests.txt (+4 Sources/ScenicKit/Vehicle rows).
    Then `check-safety-disclaimer rc=0` (`isSafetyDisclaimerAcknowledged = true written exactly once, at line 132,
    inside the SafetyDisclaimer(onAccept: { block`; key_set unchanged) and `check-map-attribution rc=0`;
    `check-safety-disclaimer-mutations`: `prove-red: 60/60 mutations refused by name`.
  - POPULATION ops/mutate/onboarding.py (floor 15 mutations, 1 EQUIVALENT, 3 test files; DRIVERS and COVERED_FLOOR
    typed; OnboardingStep/OnboardingEvent allowlisted as no-code enums). `--prove-floor`: `7 of 7 arms refused and
    the control did not`. Full run at 3bea21ca: `caught by the test that names it: 15 of 15 (wrong killer 0,
    trapped 0, compile-only 0, MISSED 0, skipped 0)`, `MISSED E1 choose skips an equal vehicle`, `MUTATE OK
    caught=15/15 equivalent_caught=0`. MISSED-then-CAUGHT: `--only 2,4,11 --prove-vacuity` (killer suites
    emptied): `MISSED 2 skip on the disclaimer accepts`, `MISSED 4 accept finishes without recording`, `MISSED 11
    stored reads back a disabled case`, `VACUITY PROOF OK ... MISSED=3 of 3`; with the suites: all three `caught`.
  - iOS CI at 3bea21ca: ios-compile run 37704762964 `success`; ios-screenshot run 37704766118 `success`.
  - GAPS (stillOpen): VehicleProfile is not on the wire (plan.ts has no vehicle field) - a follow-up for the
    Worker whitelist + PlanRequestBody; a fresh install is offered the places download on its second launch (R4);
    under a `-screen` debug launch the Settings sheet and the onboarding sheet are raised together and one is
    dropped (release builds launch to home); nothing here has been rendered or tapped (XCUITest, T-0180).
- 2026-10-08T00:46:30Z CI ROUND (PR #198 at acec3c43): `core` and `pins-source-only` failed on `P-STORE-01
  (ops/lib/check-store-links.py): 10 refusal(s)` - a whitelist I had not run (the shell's SettingsScreen( and
  corpus lines, `settings.vehicle`, the Settings' sections run, the frozen SettingsScreen digest). Retyped whole
  lines in ops/lib/store_links_pinned.py and re-approved ST's digest. `check-store-links.py` rc=0; `--prove-red:
  33/33 rows as required (29 mutants refused by name, 4 legitimate edits green)`; `ops/check-pins --source-only`:
  `PINS ok=17 skipped=26 pending=1 expired=0 failed=0`.
