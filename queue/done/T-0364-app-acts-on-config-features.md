---
id: T-0364
title: The app acts on /config's feature_loop, feature_trip and feature_surprise and degrades the Loop, Trip and Surprise entry points before the tap, as T-0357 did for Plan
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-15T23:39:41Z
lease_expires_at: 2026-10-16T23:39:41Z
worktree: .worktrees/T-0364
branch: task/T-0364
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, .github/workflows/ios-screenshot.yml, queue/]
pins_affected: []
reviewer: agent/rv1-t0364
depends_on: [T-0357]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 MEASURE (Log, before code): which screens send /plan, /loop, /trip and Surprise Me today, what each shows on 503 planning_paused, what the Worker does with feature_* (config.ts FIELDS/DEFAULTS; loop.ts, trip.ts)"
  - "A2 Per-field flag decode through the shipping ConfigClient.fetch(): for each of feature_loop, feature_trip, feature_surprise x wire value {true, false, absent, null, 0, 1, \"true\", \"false\", 1.5, [], {}} x base variant {build 7 paused + other flags false, build 3 unpaused + other flags true} the answer == RemoteConfig(minAppBuild:planningPaused:featureLoop:featureTrip:featureSurprise:) exactly, the flag being the JSON boolean when it is one and true (the Worker's DEFAULT) otherwise, every other field the variant's; meta-test: every row's answer differs across the two variants"
  - "A3 A garbled or missing flag never discards a valid pause: every non-boolean flag row over a paused answer reads planningPaused true; T-0357's whole-answer refusal for min_app_build and planning_paused is unchanged (its A4 table stays green)"
  - "A4 ConfigCache keeps all five fields: the stored bytes == the sorted five-key JSON literal; a kept answer with every flag false reads back exactly through no reply / 503 / malformed; kept T-0357 two-field bytes read back with every flag true"
  - "A5 The degrade table through the shipping planners: ConfiguredPlanner (plan), ConfiguredLoopPlanner (loop), ConfiguredTripPlanner (trip), each over ScriptedTransport serving /config for EVERY planning_paused {F,T} x feature_loop x feature_trip x feature_surprise {F,T} x (min_app_build, our build) {(1,1), (2,1), (2,nil)} = 48 answers x 3 screens = 144 rows, == the expected degrade recomputed in the test (update when our build is known and below; else the pause - pausedSurpriseOff on plan when feature_surprise is false; else featureOff on loop/trip when that screen's flag is false; else clear), each after exactly one GET /config; the bare ClientLoopPlanner/ClientTripPlanner never degrade and the configured ones plan exactly as the client ones"
  - "A6 Notice table: ConfigDegrade.notice(on:) for every case x screen {plan, loop, trip} == a literal string table; nil exactly for clear; the plan paused line names where Surprise Me is, and no plan line names Surprise Me under pausedSurpriseOff"
  - "A7 Gates: LoopSheet.startPlanning() and TripSheet.startPlanning() issue no ticket under every non-clear degrade and one under clear; clearing reopens; PlanSheet's T-0357 gate unchanged over the new cases"
  - "A8 Each new test named in the Log seen RED on the pre-code tree (missing symbols) then GREEN: swift test --filter ConfigClientTests|ConfigCacheTests|ConfigDegradeTests|ConfiguredPlannerTests|ConfigFlagTests|ConfiguredSheetPlannerTests|ConfigNoticeTests"
  - "A9 ops/mutate/config.py widened over every added Sources module and line with a literal floor; the new entries run (--only): caught = all, equivalents MISSED; --prove-floor OK"
  - "A10 Apple half: P-SAFE-03 digests re-approved for every edited apps/ios and Sources file; ios-compile success; ios-screenshot success with the new plan-loopPaused and plan-tripPaused shots looked at"
  - "A11 Final head (after merging origin/main last): bare check-safety-disclaimer, check-mutate-population, check-mutate-only, check-telemetry-emit-sites, check-line-cap, check-pins-yaml, check-exec-bits, queue-check each exit 0; every touched file <= 300 lines"
---
## Brief

T-0357 (R1) reads only `min_app_build` and `planning_paused` from GET /config and gates only PlanSheet's Plan
button. The Worker also sends `feature_loop`, `feature_trip`, `feature_surprise` (booleans, services/api/src/config.ts
FIELDS), and under the kill switch /loop and /trip answer 503 planning_paused too (loop.ts, trip.ts) - the app learns
that only after the tap.

MEASURE FIRST: which screens send /loop, /trip and Surprise Me today, what each shows on 503 planning_paused, and
what a `feature_* = false` answer should do per screen (hide, or the typed copy). RULE whether ConfigReader's
whole-answer refusal (T-0357 R2) extends to the three booleans or whether they decode per field (a garbled feature
flag must not throw away a valid pause). Then tests through the shipping ConfigClient and ConfiguredPlanner, the
degrade as a table over every flag, P-SAFE-03 digests, and the config.py population widened to the new logic.

## Log
- 2026-10-15T19:35:43Z filed by agent/claude-opus-5 as T-0357's follow-up (T-0357 R1). Ids checked on origin/main
  and every origin/task/* branch: highest T-0363, so T-0364.
- 2026-10-15T23:39:42Z claimed by agent/claude-opus-5; lease until 2026-10-16T23:39:41Z
- 2026-10-15T23:46:09Z MEASURE (A1), on main 97299cc5:
  - Worker: config.ts FIELDS admits feature_loop/feature_trip/feature_surprise as booleans only, DEFAULTS all true;
    an invalid KV value drops to its default alone (config_warnings names it). Nothing else in services/api/src reads
    a feature_* field (grep "feature_" outside config.ts: only customModel.ts's closures_not_feature_collection), so
    the flags are ADVISORY: no route refuses on them. The kill switch is enforced: /loop 503 planning_paused at
    loop.ts:50/:62, /trip at trip.ts:53/:71, /plan as T-0357 measured. There is no /surprise route (index.ts ROUTES).
  - App: PlanSheetScreen's form sends /plan via LivePlanner (ConfiguredPlanner, T-0357 degrade before the tap).
    The bottom-bar "Just drive a loop" shows LoopScreen -> LiveLoopPlanner -> ClientLoopPlanner -> POST /loop; on 503
    planning_paused it shows, AFTER the tap, LoopFailure.planningPaused "Planning is resting for a moment. Try again in
    a little while." (LoopError :22). "Plan a road trip" shows RoadTripScreen -> LiveTripPlanner -> POST /trip; after
    the tap TripFailure.planningPaused, the same line (TripError :25). LoopPlanning/TripPlanning have no degrade.
  - Surprise Me: the home's SurpriseToggle (home.surprise) shows SurpriseCard, which picks from the bundled
    SurpriseDeck and hands off to Apple Maps through GatedHandoffButton - it sends NOTHING to the Worker, so a pause
    does not stop it. The home is composed by the shell apps/ios/ScenicDrive/ScenicDriveApp.swift (outside touches;
    FeatureScenicHome may import no adapter). In the plan sheet Surprise Me is only words: T-0357's pre-tap notice
    borrows PlanFailureCopy(.planningPaused).line "Planning is paused right now. Surprise Me still works." with NO
    button beside it; the post-tap failure card has the "Surprise me instead" action, which closes the sheet onto the
    home where the chip is.
- 2026-10-15T23:46:09Z RULINGS (author rule, before code):
  - R1 decoding: per field for the three flags. min_app_build and planning_paused keep T-0357 R2's whole-answer
    refusal. Each flag is the JSON boolean when it is one; absent or any other value is that flag's Worker DEFAULT
    (true) alone - the Worker's own overlay rule - so a garbled flag never discards a valid pause or a valid build.
    Fail-open on a flag is safe: the flags are advisory (A1), the Worker enforces nothing on them.
  - R2 storage: ConfigCache stores the five fields (sorted keys); bytes kept by a T-0357 build read back with the
    flags at their defaults through the same per-field rule.
  - R3 per screen, precedence: updateRequired (our build known and below min) > the pause > the screen's own flag
    false (featureOff, loop and trip only; plan has no flag) > clear. The update line applies to all three screens
    (loops and trips are plans; T-0357 R5). Each of Loop and Trip shows its notice IN PLACE OF its Go button and its
    sheet's gate issues no ticket - T-0357's shape; the tabs stay, so the driver learns why. One GET /config per form
    appearance of each screen (the Loop/Trip forms ask when shown, not on sheet open: no request for a tab never seen).
  - R4 paused copy: Loop and Trip reuse their own typed planningPaused lines by reference (no Surprise mention).
    The plan's pre-tap notice gets its own honest lines: feature_surprise true -> "Planning is paused right now.
    Surprise Me on the home screen still works." (names where it is: the sheet has no Surprise button);
    feature_surprise false -> new case pausedSurpriseOff -> "Planning is paused right now. Try again in a little
    while." This supersedes T-0357 R6's by-reference notice; PlanFailureCopy (the post-tap card, which HAS the
    Surprise action) is unchanged.
  - R5 featureOff lines: loop "Loops are switched off for now. You can still plan a drive."; trip "Road trips are
    switched off for now. You can still plan a drive."; plan (unreachable, kept total) "Planning is switched off for
    now. Try again later."
  - R6 feature_surprise on the HOME chip needs the shell (ScenicDriveApp.swift) outside touches -> follow-up task,
    filed with a checked id. Within touches the app acts on it through R4's plan copy.
  - R7 screenshots: two new rehearsals loopPaused/tripPaused; the screenshot LIST lives in
    .github/workflows/ios-screenshot.yml and its pin ops/lib/ios_screenshot_pinned.py, so touches widen to the
    workflow (and queue/, as T-0357's did).
- 2026-10-16T01:06:47Z RED first (A8): on the pre-code tree (c46adbde + the new tests only) swift test --filter
  ConfigFlagTests|ConfiguredSheetPlannerTests|ConfigNoticeTests failed to COMPILE on the missing symbols: "type
  'ConfigDegrade' has no member 'featureOff'/'pausedSurpriseOff'", "value of type 'any LoopPlanning'/'any TripPlanning'
  has no member 'degrade'", "value of type 'RemoteConfig' has no member 'featureLoop'/'featureTrip'/'featureSurprise'",
  "cannot find type 'ConfiguredLoopPlanner'/'ConfiguredTripPlanner'/'ConfigScreen' in scope", "extra arguments at
  positions #3, #4, #5 in call". GREEN on fd178c43: --filter "Config|Loop|Trip|PlanSheet" "Test run with 127 tests in
  37 suites passed"; ConfigFlagTests, ConfiguredSheetPlannerTests, ConfigNoticeTests, ConfigDegradeTests,
  ConfigCacheTests, ConfigClientTests, ConfiguredPlannerTests each "passed". T-0357 tests moved with the rulings:
  ConfigDegradeTests' notice row (R4 supersedes T-0357 R6), ConfigCacheTests' kept-bytes literal (R2, five keys).
- 2026-10-16T01:06:47Z MUTANTS (A9): config_mutations.py widened 44 -> 84 entries (45-84: the flags' decode, keys, kept encoding,
  defaults, ConfigScreen, the per-screen degrade and notices, the loop/trip gates, ConfiguredLoopPlanner,
  ConfiguredTripPlanner, the bare clients), MIN_MUTATIONS 84, MIN_TEST_FILES 7; entries 13, 15, 21, 27-31 re-anchored on
  the new text. config_run.py builds with --jobs 4. Run --only 13,15,21,27-31,45-84 on 87c2e1a9: "MUTATE FAILED
  caught=46/48" - 60 and 61 WRONG KILLER (the per-field oracle builds its expectation through the same RemoteConfig
  init, so a stored-flag mutant moves both sides; red were the cache test, the variant meta-test and the degrade
  table). Killers corrected; --only 60,61: "MUTATE OK caught=2/2". --prove-floor: "FLOOR PROOF OK: 7 of 7 arms
  refused and the control did not".
- 2026-10-16T01:06:47Z APPLE (A10): digests re-approved (11 Sources rows + 3 new in -linked-digests.txt, 11 apps/ios rows in -pinned);
  telemetry emit-site rows for LiveLoopPlanner/LiveTripPlanner moved to the ConfiguredLoop/TripPlanner lines
  (check-telemetry-emit-sites: "ok - 38 lines approved"). ios-compile run 38828783518 success; ios-screenshot run
  38828787876 success. Looked at plan-loopPaused-light (the loop form, Topanga, 60 min, "Planning is resting for a
  moment. Try again in a little while." in place of Find a loop), plan-tripPaused-dark (Griffith Observatory -> Leo
  Carrillo, 2 days, 40%, the same line in place of Plan the road trip) and plan-paused-light ("Planning is paused right
  now. Surprise Me on the home screen still works." in place of Plan).
- 2026-10-16T01:06:47Z FOLLOW-UP: T-0367 filed (R6, the home Surprise chip on feature_surprise; ids checked: highest T-0366).
- 2026-10-16T01:20:31Z FOLLOW-UP renumbered: the home Surprise chip task is T-0368 (main took T-0367 meanwhile).
- 2026-10-16T01:20:57Z FINAL (A11), origin/main 42d049fb merged LAST (one conflict: the -pinned digest rows, union - main's LiveTelemetry,
  this branch's LiveTripPlanner re-measured). On the merged head: swift test --filter
  "Config|Loop|Trip|PlanSheet|PostDrive|DriveVoice" "Test run with 147 tests in 39 suites passed"; bare gates each
  exit 0: check-safety-disclaimer (103 app .swift, 316 root + pbxproj), check-mutate-population ("floor of 165
  holds"), check-mutate-only ("219 of 219 driver runs refused"), check-telemetry-emit-sites ("40 lines approved"),
  check-line-cap ("647 Swift files ... none over 300 lines"), check-pins-yaml ("pins=50 fields=403"),
  check-exec-bits ("225 files ... all modes correct"), queue-check ("QUEUE OK (359 tasks)" after the T-0368 renumber).
  A1-A10 as logged above; A5's table 144 rows, A2's 66.
- 2026-10-16T02:17:08Z REVIEW PASS by agent/rv1-t0364 (PR #249, head d49c67d6). Acceptance A1-A11 committed before
  code (c46adbde) and not weaker than the Brief; the home Surprise chip is ruled R6 and filed as T-0368 (id unique on
  main and every origin/task/* branch). Reviewer mutants outside the population, swift test --jobs 4 --filter
  "ConfigFlagTests|ConfigCacheTests|ConfigDegradeTests|ConfiguredPlannerTests|ConfiguredSheetPlannerTests|
  ConfigNoticeTests|ConfigClientTests|LoopSheet|TripSheet|PlanSheet": RA ConfigDegrade.of `case .plan: return .clear`
  -> `config.featureSurprise ? .clear : .featureOff` RED by name (ConfiguredSheetPlannerTests "Each screen's degrade
  is the table's row ...", 8 issues); RB TripSheet gate `degrade == .clear` -> `degrade != .updateRequired && degrade
  != .planningPaused` RED by name (ConfigNoticeTests "Under a degrade the loop and trip gates issue no ticket ...",
  4 issues); baseline "72 tests in 14 suites passed". Bare gates exit 0: check-safety-disclaimer,
  check-mutate-population ("floor of 165 holds"), check-mutate-only ("219 of 219"), check-telemetry-emit-sites ("40
  lines approved"), check-line-cap, check-pins-yaml ("pins=50 fields=403"), check-exec-bits, queue-check ("QUEUE OK
  (359 tasks)"). gh pr checks 249: core pass, pins-source-only pass. iOS on d49c67d6: ios-compile 38838083392
  success, ios-screenshot 38838087609 success; looked at plan-loopPaused-light and plan-tripPaused-dark (the resting
  line in place of the Go button). merge-base --is-ancestor origin/main (42d049fb) origin/task/T-0364: exit 0.
