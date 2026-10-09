---
id: T-0343
title: "T-0343: the corridor learner - feed entry, restore, retiming planner, on-device store (Linux slice)"
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T17:35:13Z
lease_expires_at: 2026-10-10T05:35:13Z
worktree: .worktrees/T-0343
branch: task/T-0343
exclusive: []
touches: [Sources/ScenicKit/, Sources/PlaceStore/, Tests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0325, T-0342]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE R1-R8 in a dated Log entry before any code (the 2026-10-09T17:41:58Z entry)."
  - "Restore (R2): LearnedCorridorSpeeds(timeZone:restoring:) over [CorridorSlotRow] (cell UInt64, hour Int, ratio Double, samples Int) is nil unless EVERY row has hour in 0...167, ratio in [0.3, 1.0] (NaN refused), samples >= 1 and no (cell, hour) repeats; else its slots equal the rows. Table over every bound (hour -1, 0, 167, 168, Int.min, Int.max; ratio nextDown(0.3), 0.3, 1.0, nextUp(1.0), NaN, -infinity, +infinity; samples Int.min, 0, 1, Int.max; a repeated slot), each row alone and beside a good row, answers compared WHOLE. `rows` answers every slot sorted by (cell, hour), and restoring it equals the learner that wrote it."
  - "Feed (R1): CorridorLearner.observe(coordinate:speedMetersPerSecond:at:on:clock:) builds the DriveFix from the one Date (timestamp = date.timeIntervalSinceReferenceDate), runs DriveController.observe, then CorridorClock.observe on the controller's session at that Date, and calls save with the learner's whole `rows` exactly when an edge was taught; app wiring: T-0349. Tests: the commands and the save calls per fix of a clean drive, a skip, no runs and a reroute, compared whole."
  - "Preview (R4): RetimingPlanner(inner:learner:now:) answers .preview(RetimedPreview.of(p, timeRuns: runs, by: learner.speeds, departsAt: now())) when p carries runs, the preview unchanged without runs, .failure and .offered unchanged; app wiring: T-0349. Table compared WHOLE."
  - "End to end (R5, P-SAFE-07): five drives through CorridorLearner.observe, each followed by a relaunch (a new learner restored from the last saved rows), clear RetimingPlanner's badge on the fifth and not before, previews compared whole; bound by name in P-SAFE-07."
  - "Persistence (R3): PlaceStore CorridorRatioStore(path:) over the user store's v4 table corridor_ratio (cell, hour, ratio, samples) with CHECK constraints on every bound; replaceAll(with:) is one transaction (a refused row leaves the table unchanged), list() answers it sorted; a second store on the same path reads the same rows (relaunch); cells above Int64.max round-trip. UserStorePrivacyTests' whole column map gains corridor_ratio and no column matches /home|address|breadcrumb|trail|speed/; the migration tests list v4. GRDB suites green in CI linux-core."
  - "P-PRIV-05 (R6): CorridorSlotRow, CorridorLearner, CorridorRatioRecord and CorridorRatioStore join the guarded identifiers; every new site (ScenicKit, PlaceStore, PlanAdapter, NavAdapter) approved in the whitelist, seen RED by name before approval and green after; LearnedSpeedsPrivacyTests casts the new ScenicKit types, a PlaceStore test casts CorridorRatioRecord."
  - "Tests RED first by name against stubs, then green; digest rows re-approved; ops/mutate/traffic population extended to the new subjects with a raised literal floor, the new entries CAUGHT by name; check-mutate-population, check-line-cap, check-pins-yaml, queue-check green; ios-compile and ios-screenshot success with the plan-preview and drive shots looked at."
  - "The rest FILED (R8): reroute answers carry time runs so a rerouted drive keeps learning (T-0348)."
  - "R9 (re-ruled 2026-10-09T18:15:30Z): the app wiring - DriveNavigator.forward calling CorridorLearner.observe, DriveHost's learner parameter, LivePlanner.make() wrapping RetimingPlanner over the one learner restored from CorridorRatioStore, the shell line, their P-PRIV-05 sites - is FILED as T-0349: every Swift file under apps/ios is byte-pinned in ops/lib/check-safety-disclaimer-pinned and the permission classifier refused that re-approval; this task ships the ScenicKit and PlaceStore slice only."
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
- 2026-10-09T17:35:13Z claimed by agent/claude-opus-5; lease until 2026-10-10T05:35:13Z
- 2026-10-09T17:41:58Z MEASURE then RULE (agent/claude-opus-5), before any code.
  MEASURED: (m1) nothing in apps/ names LearnedCorridorSpeeds, CorridorClock or RetimedPreview; the P-PRIV-05 guard
  whitelists 17 sites in 7 files, all in Sources/ScenicKit/Traffic/. (m2) PlaceStore depends on GRDB only and
  ScenicKit on nothing (root Package.swift, serial, not touched): PlaceStore cannot name a ScenicKit type, nor the
  reverse. (m3) NavAdapter depends on ScenicKit + Ferrostar only - it can open no PlaceStore; PlanAdapter has
  ScenicKit + ScenicAPIClient + PlaceStore + Telemetry. (m4) DriveFix.timestamp is documented as "any monotone
  clock"; DriveNavigator.forward fills it with location.timestamp.timeIntervalSinceReferenceDate. (m5) RerouteReply
  carries no time runs (Sources/ScenicKit/Drive/RerouteReply.swift). (m6) The plan sheet's previews come from the
  shell's LivePlanner.make() (ScenicDriveApp.swift) through RoutePlanning; PlanRehearsal fixtures bypass it.
  (m7) UserStorePrivacyTests compares the whole {table: [columns]} map; three migrations v1..v3.
  RULINGS. R1 (the clock's feed): one ScenicKit entry, CorridorLearner.observe(coordinate:speedMetersPerSecond:at:
  on:clock:), builds the DriveFix from the fix's Date and feeds the clock after controller.observe at that same
  Date - so the date cannot drift from the fix, and the order is ScenicKit's, testable on Linux. DriveNavigator
  holds the CorridorClock (learner.clock(for: preview), nil without runs) and calls the entry per fix with
  location.timestamp. CorridorLearner is a @MainActor final class: the one learner in the process, owned by
  PlanAdapter's LiveCorridorLearner.shared; the shell hands it to DriveHost (a new defaulted parameter) - the only
  shell edit (ScenicDriveApp.swift added to touches; a buildable-folder Swift file, no pbxproj). R2 (restore):
  LearnedCorridorSpeeds(timeZone:restoring: [CorridorSlotRow]) - a new plain row type, since PlaceStore cannot
  name CorridorSlot - nil on ANY bad row (fails toward saying less: an empty learner keeps the badge); the cell is
  not validated (a value no route has is never read). `rows` is the export. Zone: TimeZone.current at launch
  (T-0320 R5, the hour is local). R3 (persistence): user-store migration v4-corridor-ratio, table corridor_ratio
  (cell INTEGER holding the UInt64 bit pattern, hour, ratio REAL, samples) WITHOUT ROWID, PRIMARY KEY (cell, hour),
  CHECK on every bound; no column matches /home|address|breadcrumb|trail|speed/. The per-cell table is a coarse
  record of driven places by design (the plan's on-device learner); it never leaves the device (no Codable, no
  path to ScenicAPIClient/Telemetry). Written whole (replaceAll) on the main actor each time an edge is taught - a
  small table, a few writes a minute at most. A store that cannot open leaves an in-memory learner. R4 (the
  card): retimed at ANSWER time by RetimingPlanner wrapping LivePlanner.make()'s planner, departsAt = now(), so
  the card and the drive (DriveSession seeds its ETA from the preview, T-0330 R4) show the same ETA; the card
  draws the outcome unchanged (no FeaturePlanSheet edit - T-0346 is in flight there). Rehearsal shots bypass the
  planner and keep the server's badge. fastestEtaSeconds stays the server's and the budget ceiling stays the
  Worker's (T-0325 R4(d)). R5: the M7 exit on the Linux path through the shipped entry points with a relaunch
  between drives. R6: the P-PRIV-05 guard grows by CorridorSlotRow, CorridorLearner, CorridorRatioRecord,
  CorridorRatioStore and every new site. R7: loop and trip previews are not retimed (other card types; no runs
  reach them). R8: after a reroute the clock teaches nothing more (m5; T-0325 R3) - filed as a follow-up.
- 2026-10-09T18:15:30Z RED then GREEN, GUARD, and a RE-RULING R9 (agent/claude-opus-5).
  ScenicKit RED: against early-return stubs (restore `return nil`, rows `return []`, the learner's save `if false`,
  the planner `return outcome`), `swift test --filter 'ScenicKitTests\.(LearnedSpeedsRestoreTests|CorridorLearnerTests|
  RetimingPlannerTests|LearnedSpeedsPrivacyTests)'` exit 1, "Test run with 6 tests in 4 suites failed ... with 49
  issues", FAILED by name: "restore: every bound of hour, ratio and samples, alone and beside a good row; a repeated
  slot refuses all", "rows answers every slot by cell then hour, and restoring them equals the learner that wrote
  them", "each fix teaches through the shipped entry: a save of the whole table exactly when an edge completes",
  "five drives, each followed by a relaunch, clear the planner's badge on the fifth and not before", "previews with
  runs are retimed at now(); a preview without runs, a failure and an offer pass unchanged" (the privacy cast stays
  green: nothing is Codable). GREEN: the same filter plus LearnedCorridorSpeedsTests, CorridorClockTests and
  RetimedPreviewTests, "Test run with 16 tests in 7 suites passed". `ops/lib/run-named-tests.py P-SAFE-07`:
  NAMED P-SAFE-07 passed=23/23.
  PlaceStore (GRDB-gated; swift:6.1-noble under WSL docker with libsqlite3-dev, no git inside): RED with the v4
  migration unregistered - FAILED by name "records round-trip whole, by stored cell then hour; a second store on the
  file reads the same; a write replaces all" and "every bound of hour, ratio and samples one step either side; a
  refused write or a repeated slot keeps the table" (no such table: corridor_ratio), "no column of the migrated user
  store matches home|address|breadcrumb|trail|speed; the columns are R3's", and the two upgrade tests (GRDB "undefined
  migration" trap); GREEN with v4: "Test run with 16 tests passed" over CorridorRatioStoreTests,
  CorridorRatioRecordFieldsTests, UserStorePrivacyTests, UserStoreMigrationTests, SurpriseShownStoreTests,
  SavedDriveStoreTests - SQLite's 0.3 and 1.0 CHECK bounds hold exactly at Swift's one-ulp neighbours.
  P-PRIV-05 GUARD: the four new identifiers added, the guard exit 1 with "FAILED - 33 unapproved, 0 missing of 17
  approved" naming every new line (ScenicKit, PlaceStore, PlanAdapter, NavAdapter); approved; --prove-red 14 of 14
  red by name (four new rows) with the control green.
  R9 RE-RULING: `bash ops/lib/check-safety-disclaimer` (P-SAFE-03) refused the app edits - every Swift file under
  apps/ios is byte-pinned in ops/lib/check-safety-disclaimer-pinned, and the shell line is a frozen render block -
  and the permission classifier REFUSED the digest re-approval in check-safety-disclaimer-pinned. Per the brief's
  instruction the app edits (DriveNavigator, DriveHost, LivePlanner, the shell line, LiveCorridorLearner) are
  withdrawn, unapproved, and FILED as T-0349 with the exact wiring; their P-PRIV-05 sites are withdrawn with them
  (the whitelist now holds 38 sites in 12 files). This PR ships the Linux slice: the feed, the restore, the
  planner wrapper and the store, each tested through its shipping symbol. The feedTable row "a reroute" became "runs
  that do not tile the line" (a reroute through DriveController needs a ticketed RerouteReply; T-0325's
  transitionTable holds the clock's reroute row and T-0348 owns the reroute path).
- 2026-10-09T19:11:31Z CI AND MUTANTS (agent/claude-opus-5; code commit e3ffbfc6).
  ios-compile run 37972620056: success. ios-screenshot run 37972624773: success; plan-preview-light and drive-light
  LOOKED AT - the preview shows the line, "55 min - 20 min longer than the fastest way", the estimate badge, both
  hazard lines, the conditions line and the OSM credit; the drive shows the line, the map and route credit and End
  drive. No app file changed in this PR (R9), so both are the unchanged app over the new ScenicKit.
  MUTANTS NOT RUN: `python ops/mutate/traffic.py --only 64,...,81` could not build its baseline on this box twice -
  first a GRDB checkout pinned by a Package.resolved the Linux docker run had written into the worktree (removed),
  then a swift-frontend hang with no file written for 3+ minutes after 40 (killed, tree clean). The population
  grows to 81 entries with a literal floor (check-mutate-population reads it); the 18 new entries (64-81) are NOT
  yet seen CAUGHT - an open item for the reviewer's pre-review mutant pass, not a claim.
- 2026-10-09T21:07:02Z ROUND 1 RULINGS (agent/claude-opus-5; rv1-t0343 FAIL on PR #232 head abe61917), before code.
  Orchestrator ruling B4 (RESCOPE): the orchestrator, who filed T-0343, rescopes it to the Linux slice. The task
  file and PR #232 are retitled "T-0343: the corridor learner - feed entry, restore, retiming planner, on-device
  store (Linux slice)"; in the acceptance block the app clauses of R1 (DriveNavigator.forward) and R4
  (LivePlanner.make()) are struck and each replaced with "app wiring: T-0349". Dated record output is not rewritten:
  only the title and those two acceptance clauses change. queue/backlog/T-0349 was read and already names the three
  app sites - DriveNavigator forward observing with location.timestamp, the DriveHost learner parameter, and
  LivePlanner.make() answering RetimingPlanner over the one learner restored from CorridorRatioStore - so nothing is
  added there. The P-SAFE-03 digest re-approval of apps/ios files stays the OWNER's call; no apps/ios row is touched.
  Orchestrator ruling B2: America/Los_Angeles joins UTC as an INPUT VARIANT of restoreBounds() and rowsRoundTrip()
  (restored learner equals the writer, zone kept) and of fiveDrivesAcrossRelaunch() (rows = f(zone): the taught
  hours are UTC [8, 9, 9, 9] and LA [1, 2, 2, 2] at the fixed departure 2026-10-05T08:59Z = 01:59 PDT; the
  RetimingPlanner preview at that departure matches whole), with a meta-assertion that the same kept rows answer
  differently restored in UTC and in LA (an hour-crossing slot), so no row ignores the zone. Population entry 82
  (self.timeZone = TimeZone(identifier: "UTC")! in init?(timeZone:restoring:)): MISSED at abe61917 (rv1-t0343),
  CAUGHT by name after this round via --only 82.
  Orchestrator ruling B1: traffic.py SUBJECT_MODULES gains CorridorLearner.swift, CorridorSlotRow.swift and
  RetimingPlanner.swift (entries 75-81 already mutate them); the two PlaceStore modules get allowlist entries with
  their reasons - CorridorRatioRecord a four-field value with no code, CorridorRatioStore SQL I/O whose bounds are
  the v4 SQLite CHECKs held by CorridorRatioStoreTests.boundTable and whose only conversion (Int64 bitPattern) is
  held by roundTripAcrossLaunches. Gate: bare check-mutate-population exit 0.
  B3: git fetch origin in the main checkout, merge origin/main as the last step, re-run, push.
- 2026-10-09T21:42:53Z ROUND 1 RESULTS (agent/claude-opus-5; code commit 36bdae50).
  Suites: swift test --filter over the seven touched suites - "Test run with 16 tests in 7 suites passed".
  Mutant 82 (python ops/mutate/traffic.py --only 82, after clearing a .build/mt whose module cache collided with
  another scratch path - "module vcruntime is defined in both", environment): "caught 82 the restore reads every
  zone as UTC by: restore: every bound ... | rows answers every slot ... | five drives, each followed by a
  relaunch ..." and "MUTATE OK caught=1/1 (--only: 1 of 82 entries)". MISSED at abe61917 is rv1-t0343 B2's
  measurement, not re-run here.
  P-PROC-06: bare python ops/lib/check-mutate-population.py - "every added module is covered or allowlisted; the
  floor of 147 holds", exit 0. queue-check: QUEUE OK. No Sources/ file changed this round, so no digest row is
  re-approved; apps/ios rows stay the owner's call (T-0349). PR #232 retitled with gh pr edit.
