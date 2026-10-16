---
id: T-0366
title: After a handoff the app asks "Prettier than your usual way?" at the next open, only with a known stopped speed
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T18:23:44Z
lease_expires_at: 2026-10-17T18:23:44Z
worktree: .worktrees/T-0366
branch: task/T-0366
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: agent/rv2-t0366
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
- 2026-10-16T18:29:32Z MEASURED (agent/claude-opus-5, before any code):
  M1 What a handoff leaves behind: still nothing ON THE DEVICE. Since T-0361 the two successful handoffs report a
     moment - ScenicHomeScreen's `gatedHandoff` `onFailure: { ...; if $0 == nil { moments?.report(.driveHandedToAppleMaps) } }`
     and `openSurprise` `... moments?.report(.surpriseHandedToAppleMaps)` through the `homeMoments` environment key,
     which the shell sets to PlanAdapter's `LiveMoments()` - but nothing is persisted: the only @AppStorage in
     FeatureScenicHome is still `safety.disclaimer.acknowledged.v1` (plus VehicleSetting's), no UserDefaults key
     names a handoff. T-0358 M2's "records nothing" is out of date by the moment report only.
  M2 Speed sources: NavAdapter alone imports CoreLocation (DriveLocationTap wraps Ferrostar's CoreLocationProvider,
     built in DriveNavigator with `activityType: .automotiveNavigation`, which asks for When In Use when an in-app
     drive starts; Info.plist carries NSLocationWhenInUseUsageDescription). Nothing outside a drive reads a fix. The
     shell (ScenicDriveApp) imports NavAdapter and composes it with the features; FeatureScenicHome cannot import it.
  M3 The model: PostDriveQuestion.asks(outcome: .handedOff, moment: .appOpened, surface: .full, alreadyAsked: false)
     is the only next-open row that asks (PostDriveQuestionTests.everyRow); DriveSurface(speedMetersPerSecond:) is
     `.full` only for a known speed in [0, 4.5]; NaN, negative and infinite are moving (P-SAFE-09).
  M4 Render site and guards: ScenicHomeScreen.swift is 299 lines (cap 300). sheetSummary is frozen whole by
     check-safety-disclaimer-sheet (s2) SUMMARY_BLOCK; the shell's `struct ScenicDriveApp` by
     check-safety-disclaimer-frozen FROZEN_APP_SHELL and its bytes by check-safety-disclaimer-pinned
     PINNED_SHELL_DIGEST; FeatureScenicHome's file set and bytes by PINNED_HOME rows. HomeSheet lays summary() in a
     `VStack(spacing: 12)`: any always-present child, even zero-height, would take 12 pt and move the home.
- 2026-10-16T18:29:32Z RULINGS (agent/claude-opus-5):
  R1 The marker is ONE Int, "opens left" (0...3), in UserDefaults under `postDrive.handoffOpensLeft` - no place, no
     time at all, no route, no drive id; it never leaves the device (nothing reads it but the next-open decision).
     It is written by ScenicKit's `HandoffMarkingMoments`, an AppMomentReporting the shell wraps around LiveMoments
     for `homeMoments`: on `.driveHandedToAppleMaps` and `.surpriseHandedToAppleMaps` (the two moments reported only
     after a successful open, M1) it sets 3, and it forwards every moment unchanged. So the marker is set on exactly
     the path the moment is, with no edit to ScenicHomeScreen's handoff lines or GatedHandoffButton. A second
     handoff before an open resets to 3 (one question for the two; at most once per drive holds).
  R2 Expiry is by opens, not by time: each foreground open with a pending marker reads one fix; a full surface asks
     and sets 0 AT THE ASK (a kill before answering never re-asks); any other open spends one (3 -> 2 -> 1 -> 0).
     So the question is asked at the first stopped open among the three after a handoff, or never. A stored value
     outside 0...3 is clamped (negative -> 0, above 3 -> 3). No pending marker -> no fix is read at all.
  R3 The one-shot fix: NavAdapter's `LiveOpenFix` (a CLLocationManager of its own) reads `authorizationStatus`
     and calls `requestLocation()` ONLY for `.authorizedWhenInUse`/`.authorizedAlways`; any other status is no fix.
     It never calls a request*Authorization method - permission comes from an in-app drive (M2), so a free-tier
     driver who never started one is never asked (unknown speed = moving, P-SAFE-09). ScenicKit's `PostDriveFix`
     decides the surface from the raw reading: full only when speedAccuracy is finite and >= 0, the fix's age is in
     [0, 10] s (a cached stopped fix from before the drive must not ask a moving driver), and the speed is full by
     DriveSurface. Speed and age are read and dropped; nothing stores them.
  R4 How the home receives it: the shell builds one `PostDriveOpenModel` (FeatureScenicHome, @Observable) from the
     marker store, LiveOpenFix and LivePostDriveAnswers, puts it in the home's environment, and calls `opened()` on
     scenePhase .active (initial included, so a cold launch after a handoff counts). The decision is ScenicKit's
     `PostDriveNextOpen.opened(marker:fix:)`, which also re-reads the marker after the fix arrives (two overlapping
     opens ask at most once).
  R5 Where it renders: the home sheet's summary, first, as `PostDriveOpenSlot()` - a view whose body is the existing
     PostDriveCard only while the model is asking, and nothing otherwise (so no 12 pt spacing, the home unchanged
     with no marker). Not a modal. SUMMARY_BLOCK gains that one line in the same commit; ScenicHomeScreen goes to 300.
  R6 The sink: the card's answer goes through `PostDriveQuestion.send(_:to:)` to the same LivePostDriveAnswers the
     drive screen uses; Skip sends nothing. The answer does not touch the marker (it was spent at the ask).
  R7 Disagreement plan vs Brief: none beyond M1. The Brief allows "a Bool or a drive counter"; R1's count of opens
     left is that counter (it counts down opens, it holds no time).
- 2026-10-16T18:29:32Z ACCEPTANCE (written before code; re-run and re-quoted at the final pre-review commit):
  A1 `swift test --jobs 4 --scratch-path .build/t-0366 --filter "PostDriveNextOpenTests|PostDriveFixTests|HandoffMarkingMomentsTests|PostDriveQuestionTests"`
     passes every test, including the lifecycle table through PostDriveNextOpen.opened (stored marker x fix, whole
     result), every sequence of four opens after a handoff, the answers after an ask, and the fix bounds table.
  A2 RED first: the same command before the ScenicKit types exist fails to compile, naming them.
  A3 `python ops/mutate/postdrive.py` MUTATE OK caught=N/N (N >= the literal MIN_MUTATIONS); `--prove-floor` OK.
  A4 Bare gates exit 0: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py,
     check-telemetry-emit-sites.py, check-store-links.py, check-ios-compile-guardrails.py, ios_screenshot_pinned.py,
     check-map-attribution, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check.
  A5 ios-compile and ios-screenshot green on the pushed head; the home shots (light, dark, ax5) looked at and
     unchanged (no marker on a fresh simulator).
- 2026-10-16T19:15:16Z RED then GREEN (agent/claude-opus-5):
  A2 RED at the tests-only tree (the three new suites written, no ScenicKit type): the A1 command exit=1, did not
     compile - `error: cannot find 'PostDriveFix' in scope`, `cannot find type 'OpenFixReading' in scope`,
     `cannot find type 'HandoffMarkerStoring' in scope`, `cannot find 'HandoffMarkingMoments' in scope`,
     `cannot find 'PostDriveNextOpen' in scope`.
  A1 GREEN with the types: first run 13/14 - defaultsDomainIsOneInt() FAILED (on Windows Foundation the domain
     value interpolated as "Optional(2)"; the test now compares the key set and the Int values whole, no string
     form); then `Test run with 14 tests in 4 suites passed`, exit=0.
  Gate seen RED by the change itself: check-safety-disclaimer exit 1 `sheetSummary line 2 of 27: approved
  Text(DriveCopy.title(for: selectedDrive)), found PostDriveOpenSlot()`, then the shell's and ScenicHomeScreen's
  digests and the two new FeatureScenicHome files refused by name; each re-approved in this diff (SUMMARY_BLOCK,
  FROZEN_APP_SHELL, PINNED_HOME + app file-set rows, both shell digest rows, LiveOpenFix row, six ScenicKit rows in
  check-safety-disclaimer-linked-digests.txt).
  A3 `python ops/mutate/postdrive.py`: `caught by the test that names it: 33 of 33 (wrong killer 0, trapped 0,
     compile-only 0, MISSED 0, skipped 0)`, `MUTATE OK caught=33/33 equivalent_caught=0` (E1 MISSED as required);
     `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control did not`. MIN_MUTATIONS = 33.
  A5 on 019efee4: ios-compile run 38950081028 success; ios-screenshot run 38950085685 success. LOOKED at
     home-light-collapsed, home-dark-collapsed, home-ax5-collapsed: grabber, then the title, the menu chips, the
     conditions line and Open in Apple Maps, exactly the home as before - no card, no extra gap above the title.
- 2026-10-16T19:33:06Z ACCEPTANCE RE-RUN at the final pre-review commit (agent/claude-opus-5), after `git fetch
  origin` + `git merge origin/main` (Already up to date):
  A1 `Test run with 14 tests in 4 suites passed`, exit=0; the whole ScenicKitTests filter `Test run with 507 tests
     in 98 suites passed`, exit=0.
  A2 as quoted above (RED by name before the types existed).
  A3 MUTATE OK caught=33/33 equivalent_caught=0; FLOOR PROOF OK 7 of 7 (subjects unchanged since that run).
  A4 every bare gate exit 0: check-safety-disclaimer, check-mutate-population.py (`every added module is covered or
     allowlisted; the floor of 169 holds` - it first refused HandoffMarkerStoring.swift and OpenFixReading.swift by
     name, two code-free protocols now in mutate-population-allowlist.json with reasons), check-mutate-only.py,
     check-telemetry-emit-sites.py, check-store-links.py, check-ios-compile-guardrails.py, ios_screenshot_pinned.py,
     check-map-attribution, check-line-cap (ScenicHomeScreen.swift 300 lines), check-pins-yaml.py, check-exec-bits,
     queue-check.
  A5 as quoted above, on 019efee4; every apps/ios byte since is unchanged (later commits touch ops/ and queue/ only).
  NOT DONE: P-PRIV-05's named-test table does not bind HandoffMarkingMomentsTests.defaultsDomainIsOneInt() (the
  marker's whole stored domain is one Int under one key); binding it re-approves that row's digest and count.
- 2026-10-16T20:39:29Z agent/claude-opus-5 (orchestrator): rv1 FAIL was ancestry only (T-0188's ETL/ScenicKit test files landed). Merged origin/main (clean, no apps/ios change). On the merged head 7f46321d: A1 'Test run with 14 tests in 4 suites passed' (PostDriveNextOpenTests|PostDriveFixTests|HandoffMarkingMomentsTests|PostDriveQuestionTests); A4 bare gates all exit 0 (check-safety-disclaimer, check-mutate-population, check-mutate-only, check-telemetry-emit-sites, check-store-links, check-ios-compile-guardrails, ios_screenshot_pinned, check-map-attribution, check-line-cap, check-pins-yaml, check-exec-bits, queue-check).
- 2026-10-16T21:00:42Z agent/rv2-t0366 (reviewer, round 2 - ancestry/CI/gates): PASS on b01d4d9f. git diff 019efee4 origin/task/T-0366 --stat -- apps/ios is empty. git diff origin/main origin/task/T-0366 --stat lists only this task's Sources/ScenicKit/PostDrive, Tests/ScenicKitTests/PostDrive, ScenicApp Sources, ScenicDriveApp.swift, ops/lib, ops/mutate files and its queue file (24 files, 1044+/8-). swift test filter PostDriveNextOpenTests|PostDriveFixTests|HandoffMarkingMomentsTests|PostDriveQuestionTests: Test run with 14 tests in 4 suites passed. Bare gates all exit 0: check-safety-disclaimer, check-mutate-population (floor of 169 holds), check-mutate-only (234 of 234 refused), check-telemetry-emit-sites, check-store-links, check-ios-compile-guardrails, ios_screenshot_pinned, check-line-cap (694 files none over 300), check-pins-yaml (pins=52), check-exec-bits, queue-check (QUEUE OK 371). gh pr checks 271: core pass, pins-source-only pass. ios-compile 38950081028 and ios-screenshot 38950085685 green on 019efee4, no apps/ios byte changed since. Ancestry: origin/main 334b1891 is not an ancestor; the only missing commit is 334b1891 queue: file T-0382 (one queue/backlog file) - queue-only drift, accepted.
