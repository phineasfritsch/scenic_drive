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
- 2026-10-15T22:48:04Z RED then GREEN (agent/claude-opus-5). RED: `swift test --filter
  'ScenicKitTests\.(PostDriveQuestionTests|DriveVoiceArrivalTests)'` before any Sources/ edit did not compile, each
  missing by name (`cannot find type 'PostDriveOutcome' in scope`, `'PostDriveMoment'`, and on). GREEN after the model:
  `swift test --filter 'ScenicKitTests\.(PostDriveQuestionTests|DriveVoiceArrivalTests|DriveDisplayTests|DriveVoiceTests|DriveMotionGateTests|DriveContinuedTests)'`
  -> `Test run with 35 tests in 6 suites passed`. Guards seen RED by the app edits before re-approval:
  check-drive-display exit 1 (`23 found, 21 approved`, the two DriveScreen lines and the new navigator line unapproved,
  the old one missing); check-telemetry-emit-sites `FAILED - 3 refusals` (the LivePostDriveAnswers site, the
  LiveTelemetry line as unlisted site and as an event outside an emit row); check-safety-disclaimer exit 1 (the
  shell's frozen `host` line). Then green: check-drive-display 23 approved, --prove-red 7/7 (new row: the screen asks
  whatever the display says); emit sites `ok - 35 lines approved; 4 of 14 cases emitted once, 10 pending by task`,
  --prove-red `ok - 17 rows` (the two pending-row rows moved to `pending paywall T-0361`, since postDriveAnswer is no
  longer pending; new row: the post_drive_answer emit demoted). check-safety-disclaimer exit 0.
  AMENDMENTS (no ruling reversed): A1's hasArrived test is its own suite, DriveVoiceArrivalTests (DriveVoiceTests.swift
  is 287 lines; one type per file, 300 cap). R11: the five PostDrive files are ALLOWLISTED in
  ops/lib/mutate-population-allowlist.json with reasons (no number in any of them; PostDriveQuestion is a boolean held
  whole by the 24-row map), not added to drive.py - check-mutate-population `every added module is covered or
  allowlisted; the floor of 157 holds`. The shell's frozen `host` line (check-safety-disclaimer-frozen) moves with R7.
- 2026-10-15T22:52:00Z filed T-0366 (backlog): R3's next-open question after a handoff, app half (ids on main and every
  open task/* branch listed first; highest T-0365; `T-0366` found nowhere).
- 2026-10-15T23:23:42Z FINAL (agent/claude-opus-5): merged origin/main (a8fcf659, T-0356's InstallBoundTelemetry)
  LAST; conflicts in check-telemetry-emit-sites.txt (main's InstallBoundTelemetry rows kept, this task's emit row and
  LivePostDriveAnswers site added, pending row removed) and check-safety-disclaimer-pinned (main's taken, this task's
  seven app digests and the shell digest re-approved on the merged bytes). Acceptance re-run on the merged tree:
  A1+A3 `swift test --filter 'ScenicKitTests\.(PostDrive\w*|Drive\w*)Tests|TelemetryTests\.(TelemetryClientTests|TelemetryEventEncodingTests)'`
     -> `Test run with 74 tests in 13 suites passed`.
  A2 check-telemetry-emit-sites exit 0 `ok - 40 lines approved; 4 of 14 cases emitted once, 10 pending by task`;
     --prove-red `ok - 17 rows`.
  A4 exit 0 each, bare: check-safety-disclaimer; check-mutate-population (`every added module is covered or
     allowlisted; the floor of 157 holds`); check-mutate-only; check-line-cap (`625 Swift files ... none over 300`);
     check-pins-yaml (`pins=50 fields=403`); check-exec-bits; queue-check (`QUEUE OK (356 tasks)`); check-drive-display
     (23 approved; --prove-red 7/7); check-drive-voice (7 approved); check-ferrostar-imports.
  A5 on 449c234b (pre-merge app code): ios-compile run 38819649176 success; ios-screenshot run 38819652424 success;
     drive-light.png looked at: the moving (minimal) surface - map, credit, one large End drive - and no question.
     No prompt shot (R10: the screen LIST is outside touches).
- 2026-10-16T00:47:35Z agent/claude-opus-5 (owner): rv1-t0358 FAIL was ancestry-only (main gained PR #244 T-0357 config, then PR #247 T-0354). Merged origin/main as e1286282 (one conflict in ops/lib/check-safety-disclaimer-pinned, resolved as a union: WaitlistRoutePlanner takes main's digest 481433dd, ScenicDriveApp.swift keeps this branch's 8aaa166d = merged bytes = PINNED_SHELL_DIGEST, the three PostDrive rows kept) and again with the ops-only T-0354 merge. On the merged head: swift test "Test run with 839 tests in 169 suites passed"; check-safety-disclaimer rc=0; check-mutate-population "floor of 165 holds" rc=0; check-telemetry-emit-sites "ok - 40 lines approved; 4 of 14 cases emitted once, 10 pending by task" rc=0; check-drive-display "23 approved" rc=0; check-pins-yaml rc=0; ios_screenshot_pinned rc=0; check-mutate-only rc=0; queue-check rc=0.
