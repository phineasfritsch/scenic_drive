---
id: T-0358
title: After a drive the app asks "Prettier than your usual way?" once and records post_drive_answer - the funnel's answer stage
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-15T22:21:25Z
lease_expires_at: 2026-10-16T22:21:25Z
worktree: .worktrees/T-0358
branch: task/T-0358
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0355]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10: only the wire case exists (Sources/Telemetry/TelemetryEvent.swift post_drive_answer); no UI. The
plan: "Prettier than your usual way?" after a drive (paid: at drive_completed; free: at destination arrival via
region monitoring, else at next open) feeds W1/W4 and the Bradley-Terry tuning. Region monitoring needs a capability
(owner) - rule the free-tier trigger as "at next open after a handoff" if so.

MEASURE FIRST: where a drive completes in the app (DriveSession / drive screen) and what a handoff leaves behind.
RULE: when the question shows (once per drive, never during motion - P-SAFE-06's motion gate), the answer set, what is
sent (the telemetry case only, through T-0355's client), and dismissal. Tests on the ScenicKit model that decides
when to ask (a table over drive outcomes x tiers x motion). Every apps/ios Swift edit needs the P-SAFE-03 digest
re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-4).
- 2026-10-15T22:21:25Z claimed by agent/claude-opus-5; lease until 2026-10-16T22:21:25Z
- 2026-10-15T22:26:16Z MEASURED (agent/claude-opus-5, before any code):
  M1 Where a drive completes. The in-app drive is ScenicDriveApp's `DriveHost` (NavAdapter) composed with
     FeatureScenicHome's `DriveScreen`; it ends ONLY through DriveScreen's "End drive" (`onEnd: { self.drive = nil }`
     in the shell). Arrival is known in exactly one place: DriveVoice's private `arrived` latch (destination within
     `arrivalMeters` = 30 m along the line, guiding only; reset by a taken reroute's new line). DriveNavigator.publish()
     builds `display` BEFORE `voice.utterances(after:)`, so a display read at a fix cannot see that fix's arrival.
     Nothing about a drive outlives the screen: no store, no UserDefaults key.
  M2 What a handoff leaves behind: nothing. GatedHandoffButton and the Surprise card open Apple Maps; the only
     @AppStorage in FeatureScenicHome is `safety.disclaimer.acknowledged.v1`. No record of the handoff, its route or
     its time exists after it.
  M3 The wire: Sources/Telemetry `TelemetryEvent.postDriveAnswer(prettier: Bool)` -> label `prettier`/`not_prettier`
     (TelemetryEventEncodingTests rows 31-32; the Worker's telemetryPoint.ts admits exactly those two labels).
     TelemetryClientTests.everyEventPostsExactlyItsRequest() already compares the WHOLE request of both rows to its
     recomputation. ops/lib/check-telemetry-emit-sites.txt: `pending postDriveAnswer T-0358`; every emit is one line
     in PlanAdapter/LiveTelemetry.swift.
  M4 Tier: the app has no entitlement state (no purchase flag anywhere under Sources/ or apps/ios; the paywall is a
     screen). No speed source outside NavAdapter: FeatureScenicHome imports no CoreLocation, the home has no fix.
  M5 Layering: FeatureScenicHome cannot import PlanAdapter/Telemetry (ScenicApp Package.swift); the surpriseLedger
     environment key (FeatureSurpriseMe, set by the shell) is the existing pattern. The ios-screenshot screen LIST is in
     .github/workflows/ios-screenshot.yml, outside touches.
- 2026-10-15T22:26:16Z RULINGS (agent/claude-opus-5):
  R1 Tier = where the drive ran. With no entitlement state (M4), the plan's split (paid: at drive_completed; free: at
     arrival or next open) is a split by surface: in-app guidance (the paid surface) vs a handoff (the free surface).
     ScenicKit's `PostDriveOutcome` carries it: `.arrived` / `.endedEarly` (in-app) and `.handedOff`. A separate tier
     enum with no source in the app would be a dead input.
  R2 When (in-app, drive_completed): when the driver taps End drive on a drive that has ARRIVED (DriveVoice's arrival,
     M1), on the FULL surface (stopped: a known speed in [0, 4.5] m/s - P-SAFE-09, the plan's P-SAFE-06 motion gate),
     and not already asked for this drive. Ended before arrival: never asked. Moving at End: not asked, the drive ends.
     If the driver starts moving while the question shows (display goes minimal), the question closes, nothing is sent
     and the drive ends - the driver had already chosen to end it.
  R3 Free tier: region monitoring needs an owner capability (always-location/background modes), so the free trigger is
     "at next open after a handoff". The model rules it (`.handedOff` at `.appOpened`, stopped, not asked -> ask), but
     the APP half is NOT wired here: the home has no speed (M4) and an unknown speed is moving (P-SAFE-09), so a
     next-open question would either never show or show to a moving driver. Follow-up task filed for a one-shot fix at
     open (NavAdapter, composed by the shell) plus the handoff marker. Handoffs still leave nothing behind (M2).
  R4 Once per drive: the model takes `alreadyAsked`; DriveScreen (one per drive - the shell rebuilds DriveHost per
     plan) keeps the latch. Asked = shown, whatever the answer: the question never returns for that drive.
  R5 Answer set: "Prettier" -> prettier, "Not really" -> not_prettier, "Skip" (dismissal) -> nothing sent. The wire
     case is a Bool and the Worker admits two labels (M3); there is no third label.
  R6 What is sent: only `TelemetryEvent.postDriveAnswer(prettier:)`, through LiveTelemetry's TelemetryClient (T-0355),
     constructed on one line in LiveTelemetry.swift; its emit row replaces the pending row. No route, place or time.
  R7 Wiring: ScenicKit protocol `PostDriveAnswering`; FeatureScenicHome environment key `postDriveAnswers` (default
     nil = nothing sent); PlanAdapter `LivePostDriveAnswers` calls LiveTelemetry; the shell sets the key on the drive
     host. The shell file is outside the filed touches: TOUCHES WIDENED by exactly apps/ios/ScenicDrive/ScenicDriveApp.swift
     (not serial-only; its digest is re-approved in check-safety-disclaimer-pinned). No Package.swift edit is needed.
  R8 Arrival reaches the screen through DriveDisplay: `arrived: Bool` (default false), filled by DriveNavigator from
     DriveVoice's new read-only `hasArrived`, with publish() reordered so the voice runs first (M1). DriveScreen reads
     only `display` (check-drive-display's approved lines move with it).
  R9 Copy: "Prettier than your usual way?" (the plan's words); buttons "Prettier", "Not really", "Skip" - calm, no
     score, no stars (owner-route-intent).
  R10 Screenshot: no screen case is within touches (M5), so no prompt shot; ios-screenshot must stay green and the
     drive shot (moving at 15 m/s) must show no question.
  R11 Population: PostDriveQuestion's decision gets mutants in the drive family (ops/mutate/drive_mutations.py,
     SUBJECT_MODULES widened); the answer/outcome/moment enums and the protocol are non-numeric.
- 2026-10-15T22:26:16Z ACCEPTANCE (agent/claude-opus-5; re-run and re-quoted at the final commit):
  A1 `swift test --filter 'ScenicKitTests\.(PostDriveQuestionTests|DriveDisplayTests|DriveVoiceTests|DriveMotionGateTests)'`
     all pass, and PostDriveQuestionTests was seen RED by name before the model existed. It holds:
     a) everyRow(): the WHOLE cross product PostDriveOutcome x PostDriveMoment x DriveSurface x alreadyAsked (3x2x2x2 =
        24 rows) through `PostDriveQuestion.asks(...)`, compared as one map to the expected map whose only true rows are
        (arrived, driveEnded, full, false) and (handedOff, appOpened, full, false);
     b) noInputIgnored(): for each of the four inputs some pair of rows differing only in it answers differently;
     c) afterEveryDisplay(): `asks(after:alreadyAsked:)` over every DriveSurface x DriveMode x arrived x alreadyAsked
        through DriveDisplay(surface:mode:arrived:) - true exactly when full, arrived and not asked;
     d) answerSet(): allCases == [prettier, notPrettier, dismissed], titles and `prettier` (true, false, nil) by
        full equality, the prompt by exact string.
     DriveVoiceTests gains hasArrived (false before, true at the arrival line, false again on a taken reroute's line).
  A2 `python ops/lib/check-telemetry-emit-sites.py` exit 0 with `emit postDriveAnswer` at LiveTelemetry.swift and no
     pending row for it; `--prove-red` every row red with the control green.
  A3 `swift test --filter 'TelemetryTests\.TelemetryClientTests'` passes (the emitted request, both answers, equal to
     its recomputation through the shipping TelemetryClient).
  A4 Gates exit 0, run bare: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py,
     check-telemetry-emit-sites.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check,
     check-drive-display.py, check-drive-voice.py, check-ferrostar-imports.py.
  A5 ios-compile success and ios-screenshot success on task/T-0358; the drive shot looked at (no question).
