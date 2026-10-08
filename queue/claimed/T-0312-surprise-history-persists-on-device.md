---
id: T-0312
title: The device's Surprise history persists across launches (GRDB user store beside saved drives), so the 90-day no-repeat holds without a session; the card's basis/history split gets a test of its own
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T05:02:47Z
lease_expires_at: 2026-10-09T01:02:47Z
worktree: .worktrees/T-0312
branch: task/T-0312
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PROD-02, P-PRIV-05]
reviewer: null
depends_on: [T-0310, T-0290]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST: the table (a user-store migration beside saved_drive: place id, category, corridor, UTC day - no coordinate, P-PRIV-05), retention (90 days, pruned on write), and how 'Start over' interacts with shown entries (T-0310 R7 keeps them; rule whether that stands - rv1-t0310 recordable 1 flags it for the owner)"
  - "A pure ScenicKit function chooses the card's pick basis vs the recorded history; a table test shows the card never re-picks from the history it records into (rv1-t0310 recordable 2: today only a digest row and the screenshot guard that split)"
  - "Store round-trips by full equality; migration from the in-memory state on first launch; P-PRIV-05 DDL test extended and seen red with a forbidden column; P-PROD-02 still holds; population entries MISSED before and CAUGHT by name after"
---
## Brief

T-0310 stillOpen 3 and rv1-t0310 recordables 1-2 (PR #199): the device Surprise history lives in memory only (R9), so a
relaunch forgets the 90-day no-repeat when there is no session; and the card's basis/history split has no test.

## Log
- 2026-10-08T04:02:40Z filed by agent/claude-opus-5 (orchestrator) from T-0310's stillOpen and rv1-t0310's recordables.
- 2026-10-08T05:02:47Z claimed by agent/claude-opus-5; lease until 2026-10-09T01:02:47Z
- 2026-10-08T05:07:46Z MEASURED, then RULED before any code, by agent/claude-opus-5 (owner). Read: SurpriseCard.swift,
  SurpriseShowing.swift, SurpriseHistory.swift, Surprise.swift, CivilDate.swift, SurpriseDeck.swift, the root and
  ScenicApp Package.swift, Sources/PlaceStore/{SavedDriveStore,UserStoreMigrations}.swift, Tests/PlaceStoreTests/
  {UserStorePrivacyTests,UserStoreMigrationTests}.swift, queue/done/T-0310 (R7, R9, stillOpen ii), T-0290 (R1-R8),
  ops/mutate/session*.py, ops/lib/mutate_population_table.py, the -linked digests and -pinned.
  MEASURED: (a) the card holds `history` and `basis` as two @State SurpriseHistory values (SurpriseCard.swift lines
  15-18); recording sets only `history` (line 71), "not this" and "Start over" set both (lines 173-174, 189-190), and
  no code outside the view states the split - nothing tests it. (b) `SurpriseHistory.Shown.date` is the LOCAL civil
  date: SurpriseDeck.context(at:) reads `Calendar.current` (SurpriseDeck.swift line 45-48). (c) Surprise.shownDays =
  90 and the pick blocks a shown id while `days(date, since: shown.date) < shownDays` (Surprise.swift line 70): an
  entry is read by the pick for days 0..89 after it and never again. (d) the user store is Application Support/
  user.sqlite, opened by FeaturePlanSheet's SavedDriveShelf.store, migrations ["v1-saved-drives", "v2-needs-replan"];
  FeatureSurpriseMe already depends on PlaceStore. (e) PlaceStore depends on GRDB only - it cannot import ScenicKit.
  (f) SavedDriveStore's file gate `inspect(path:)` is `private static`. (g) no ops/ guard or test names `basis`.
  RULINGS:
  - R1 THE TABLE. Migration "v3-surprise-shown" (third in UserStoreMigrations.identifiers) creates `surprise_shown
    (place_id TEXT NOT NULL CHECK (length(place_id) > 0), category TEXT NOT NULL, corridor TEXT NOT NULL, day INTEGER
    NOT NULL, PRIMARY KEY (place_id, day)) WITHOUT ROWID` in user.sqlite beside saved_drive. No coordinate, cell,
    position or time of day (P-PRIV-05). The primary key is SurpriseShowing's own same-day rule (one row per place per
    day). PlaceStore's value is `SurpriseShownRecord {placeID: String, category: String, corridor: String, day: Int}`
    (String and Int only - PlaceStore cannot see ScenicKit's SurpriseCategory, (e)).
  - R2 DISAGREEMENT "UTC day": the in-memory entries are keyed by the LOCAL civil date (b), and the same-day rule and
    the 90-day window compare those dates. Storing the UTC day of the instant would put an evening showing west of
    Greenwich on tomorrow's key and break both. RULED: `day` is the civil date the card used, as whole days since
    1970-01-01 of that calendar date (ScenicKit `SurpriseShownDay.number(_:)` / `.date(_:)`, a round-trip pair) -
    a day with no zone and no time, which is what the acceptance's "UTC day" asks the column to be (no timestamp).
  - R3 RETENTION 90 days, pruned on write. `SurpriseShownDay.oldestKept(today:)` = number(today) - (Surprise.
    shownDays - 1): the oldest day the pick still reads (c). `SurpriseShownStore.record(_:keepingFrom:)` inserts
    (INSERT OR IGNORE) and then deletes every row with day < keepingFrom, in one transaction, and returns list().
    Reads never write. A table test binds the bound to the pick itself: an id shown on oldestKept is blocked by
    Surprise.pick, one shown the day before is not.
  - R4 START OVER: T-0310 R7 STANDS - Start over clears the feedback only; shown entries stay, in memory and on disk.
    Reason it stands: the 90-day no-repeat is the product's novelty promise and Start over is offered only on the
    empty card after "not this" answers; clearing shown would resurface yesterday's place and still not clear the
    ledger's 90 days for a sessioned device, so the two halves would disagree. No concrete reason to change it was
    found. The owner is asked to confirm (rv1-t0310 recordable 1) - recorded in stillOpen.
  - R5 THE SPLIT, pure. ScenicKit `SurpriseCardHistory {history, basis}` is the card's whole state; the card holds
    one @State of it. `showing(_:on:)` (SurpriseShowing.recording into history; basis unchanged; nil when already
    shown that day), `declining(_:)` (feedback appended; basis = history), `startingOver()` (feedback cleared;
    basis = history), `restoring(_:)` (the stored entries united into BOTH history and basis, de-duplicated by
    (id, date), stored first in store order then the in-memory entries not already present; the in-memory
    recordings never enter basis, so a restore never re-picks away from the place on the card). Table test over
    initial variants {empty, stored only, feedback only, both} x the four operations, each row's whole value by
    full equality to a recomputation, plus the invariant row: across every sequence, `showing` leaves basis
    byte-equal and Surprise.pick over basis unchanged.
  - R6 FIRST LAUNCH. The previous build kept nothing on disk (R9), so the first launch of this one finds an existing
    v1+v2 user.sqlite (or none): v3 is added in place and every saved drive is preserved by full equality (GRDB
    test). The in-memory state at that moment is whatever the card recorded before the store answered; restoring(_:)
    unions it in (R5) and the card then writes the WHOLE history.shown with record(_:keepingFrom:) (idempotent by the
    primary key), so nothing recorded before the read is lost. The card reads the store in its first .task BEFORE
    ledgerRead is set, so in practice the in-memory set is empty at restore; the union is the rule anyway.
  - R7 FEEDBACK is not persisted (the acceptance's table names shown entries only); a relaunch forgets "not this"
    answers (30-day not-my-thing included). Recorded in stillOpen for the owner.
  - R8 THE STORE `SurpriseShownStore(path:)` (GRDB, one type per file) shares SavedDriveStore's file gate -
    `inspect(path:)` becomes internal, unchanged - and the migrator; its DatabaseQueue sets busyMode .timeout(5 s)
    because SavedDriveShelf holds a second connection to the same file. The app's bridge FeatureSurpriseMe
    `SurpriseShownLog` opens Application Support/user.sqlite lazily, maps records to Shown (an unknown category
    row is dropped), and every failure (no store, a refused file, a busy write) is swallowed: the card keeps its
    in-memory history - T-0310's behaviour, fail-safe for the pick.
  - R9 P-PRIV-05: UserStorePrivacyTests' whole map gains surprise_shown [place_id, category, corridor, day] and a
    second regex /lat|lon|coord|cell|geo|location|position/ over surprise_shown's columns; seen red in the swift:6.1
    image with a forbidden column added to v3. Native: `SurpriseShownRecordFieldsTests/noFieldIsACoordinate()` - a
    Mirror whitelist (labels exactly the four, leaves String or Int). Both bound in named-tests.json P-PRIV-05.
    P-PROD-02: run-named-tests P-PROD-02 re-run; the pick is unchanged (only its history input is restored).
  - R10 POPULATION ops/mutate/shownhistory{,_mutations,_run}.py (session.py's three-file shape) over
    SurpriseCardHistory.swift and SurpriseShownDay.swift, native killers, literal floor; SurpriseShownRecord (no
    code) and SurpriseShownStore (GRDB, bound by the GRDB suite, as SavedDriveStore) allowlisted. Three entries run
    MISSED before their tests land, CAUGHT by name after.
  - R11 DIGESTS: -linked-digests rows for every new/changed Sources file; -pinned PINNED_SURPRISE/PINNED_APP_SWIFT
    for SurpriseCard and the new SurpriseShownLog, re-approved after being seen red.
- 2026-10-08T05:59:21Z RED, GREEN, GRDB, POPULATION and DIGESTS, agent/claude-opus-5:
  - RED first, by name, at 1a151300 (SurpriseCardHistory's four operations answering nil/self, SurpriseShownDay
    answering 0 and 1970-01-01, SurpriseShownRecord carrying a stub `latitude: Double`): `swift test --filter
    "SurpriseCardHistoryTests|SurpriseShownDayTests|SurpriseShownRecordFieldsTests"` -> `Test run with 5 tests in 3
    suites failed`; red: `A known calendar date is its hand-counted day number...` (9 of 10 rows), `Every operation
    over every starting state is its recomputed history and basis, whole` (16 issues), `The oldest kept day on
    2026-10-07 is 89 days back: 2026-07-10`, `a stored shown place is {placeID, category, corridor, day}, String and
    Int leaves only - no coordinate` (the stub latitude); green only the meta-test `No operation's expectation
    ignores the state it starts from` (it reads expectations, not the stubs).
  - GREEN at 7216e222: the same filter `Test run with 5 tests in 3 suites passed`; `--filter "ScenicKitTests\.
    Surprise|PlaceStoreTests"` -> `Test run with 85 tests in 23 suites passed` natively. Card: one @State
    SurpriseCardHistory; the first .task restores SurpriseShownLog.load() and saves the union before the ledger read
    (R6); recordShown saves history.shown after state.showing; Start over -> startingOver(), "not this" ->
    declining(_:).
  - GRDB in the CI image (swift:6.1-noble, "Swift version 6.1.3 (swift-6.1.3-RELEASE)", libsqlite3-dev as CI, a
    tar copy - git never ran in WSL; .build/grdb.sh), filter `PlaceStoreTests\.(SurpriseShownStoreTests|
    UserStorePrivacyTests|UserStoreMigrationTests|SurpriseShownRecordFieldsTests|SavedDriveStoreTests)`:
    RED ARM (the copy's v3 DDL given `cell TEXT NOT NULL DEFAULT ""`): `Expectation failed: ((columns
    ["surprise_shown"] ?? ["missing"]).filter { $0.contains(coordinate) } -> ["cell"]) == []` and the whole-map
    expectation, `Test run with 14 tests failed ... with 2 issues`. GREEN (the tree as committed): `Suite
    "SurpriseShownRecord fields" passed`, `Suite "UserStore privacy" passed`, `Suite "SurpriseShownStore" passed`
    (round-trip, prune at keepingFrom - 1 / keepingFrom, the v1+v2 upgrade with the saved drive whole, the shared
    gate), `Suite "UserStore migrations" passed` (refusal cross product now 4 prefixes), `Suite "SavedDriveStore"
    passed`; 20 tests passed.
  - POPULATION ops/mutate/shownhistory{,_mutations,_run}.py, 20 entries (floor 20), 1 EQUIVALENT with witness (E1
    the era's zero), 2 test files. HOLD-BACKS at 7216e222 (before the sweep, the retention and the never-re-picks
    rows existed): `MISSED 16 the century rule off by a day`, `MISSED 18 the pick's window inclusive`, `MISSED 19 the
    pick's window a day short`, `MISSED 20 the pick's shown block off`, `MUTATE FAILED caught=0/4`. Rows added at
    d5bcf2b2; full run there: 1-19 `caught` by name (16 `by: Every day from 1600 to 2400 is a valid calendar date
    that numbers back to itself`, 18 and 19 `by: The pick blocks a place shown on the oldest kept day and not one
    shown the day before`), `MISSED E1` as an equivalent must, and `WRONG KILLER 20` - it named the never-re-picks
    test, which stays green because a place shown today is ALSO set aside by the 30-day category/corridor rule.
    Ruled: entry 20 names the retention test alone (54f8cced); `--only 20` -> `caught 20 ... by: The pick blocks a
    place shown on the oldest kept day...`, `MUTATE OK caught=1/1`. `--prove-floor` -> `FLOOR PROOF OK: 7 of 7
    arms refused and the control did not`. Entry 1 (showing moves the basis) is caught by the never-re-picks test
    and the table both.
  - DIGESTS at 512f5b05, seen red first: `P-SAFE-03: the pinned render surface changed: FeatureSurpriseMe's file set
    is not the approved one: added SurpriseShownLog.swift.`, then `P-SAFE-03: the pinned linked trees changed:
    root: added Sources/PlaceStore/SurpriseShownRecord.swift Sources/PlaceStore/SurpriseShownStore.swift Sources/
    ScenicKit/Surprise/SurpriseCardHistory.swift Sources/ScenicKit/Surprise/SurpriseShownDay.swift.` -pinned:
    SurpriseCard (PINNED_SURPRISE and PINNED_APP_SWIFT) re-approved, SurpriseShownLog added to both;
    -linked-digests: SavedDriveStore and UserStoreMigrations re-approved, four rows added. check-safety-disclaimer
    exit=0.
  - NAMED: `run-named-tests.py P-PROD-02` -> `NAMED P-PROD-02 passed=7/7`; P-PRIV-05 -> `NAMED P-PRIV-05
    passed=49/50`, the one red `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING` -
    GRDB-gated, absent on Windows as T-0290 R7 predicted; green in the image above and in CI's core job.
    SurpriseShownRecordFieldsTests/noFieldIsACoordinate() passed by name.
  - iOS CI dispatched on 512f5b05: ios-compile 37734303277, ios-screenshot 37734306221.
- 2026-10-08T06:20:00Z ACCEPTANCE RE-RUN on the merged head e119fb0c (git fetch origin + merge of origin/main
  681c9a13 - main added queue/ready/T-0314 only; no conflict), agent/claude-opus-5:
  1. RULE FIRST: the 05:07:46Z entry (measurements a-g, R1-R11) committed alone at 4e115de2 before any code. Table
     surprise_shown(place_id, category, corridor, day) beside saved_drive, no coordinate (R1); "UTC day" ruled as the
     card's civil day number (R2); 90 days pruned on write at oldestKept = today - 89 (R3); Start over keeps shown -
     T-0310 R7 stands, the owner is asked to confirm (R4).
  2. The split: ScenicKit SurpriseCardHistory, the card's only history state; SurpriseCardHistoryTests' table (4
     starting states x 5 operations, whole value by full equality) + meta-test, and `Recording the place on the card
     never moves the pick; recording into the basis would` (pick over basis unchanged after showing, pick over the
     recorded history different).
  3. Store round-trip by full equality, the v1+v2 -> v3 first-launch upgrade with the saved drive whole, the
     in-memory union (restoring) - SurpriseShownStoreTests green in the swift:6.1 image; P-PRIV-05 DDL test extended
     and seen red with `cell` (above); P-PROD-02 `passed=7/7`; population 16/18/19/20 MISSED before, CAUGHT by name
     after.
  4. On e119fb0c: `swift test --filter "ScenicKitTests\.Surprise|PlaceStoreTests|ScenicAPIClientTests"` -> `Test
     run with 131 tests in 32 suites passed` + XCTest `Executed 47 tests, with 1 test skipped and 0 failures`;
     check-safety-disclaimer exit=0, check-map-attribution exit=0, check-store-links exit=0; check-mutate-population
     `every added module is covered or allowlisted; the floor of 104 holds`; check-line-cap `388 Swift files tracked
     (Sources=185, Tests=143, apps/ios=60), none over 300 lines`; check-pins-yaml `PINS-YAML ok pins=44 fields=355`;
     queue-check `QUEUE OK (305 tasks)`. iOS CI on 512f5b05 (the app tree since: unchanged): ios-compile 37734303277
     `completed success` (3m6s), ios-screenshot 37734306221 `completed success` (12m13s).
  - NOT DONE (stillOpen): (i) OWNER CONFIRM R4 - Start over keeps shown places (in memory, on disk and in the
    ledger); (ii) R7 - "not this" feedback is not persisted, so a relaunch forgets a 30-day not-my-thing; (iii) the
    file name "user.sqlite" is typed twice (SavedDriveShelf, SurpriseShownLog) - two feature targets cannot share a
    constant without a PlaceStore edit; a drift would split the user store silently.
- 2026-10-08T06:40:00Z CI core RED on PR #202 (run 37736847921, `error: fatalError`, no JUnit report), agent/claude-
  opus-5. Reproduced in the swift:6.1 image: `macro expansion #expect:1:1: error: the compiler is unable to
  type-check this expression in reasonable time` - the sweep's `#expect(last - first == 801 * 365 + 195 - 1, ...)`
  (added at d5bcf2b2, after the earlier image run). Fixed at 170a26c7: the span is a typed `let span: Int`, and the
  store test's `expected + [...]` comparison a typed `let second` (same values, same names). Image: `Suite
  "SurpriseCardHistoryTests" passed`, `Suite "SurpriseShownStore" passed`, `Suite "SurpriseShownDayTests" passed`,
  `Test run with 11 tests passed`. Native: `Test run with 131 tests in 32 suites passed`; touched-row mutants
  `--only 11,16` -> `MUTATE OK caught=2/2` (16 by the sweep); check-line-cap `388 Swift files ..., none over 300
  lines`. Sources and the app tree unchanged, so digests and iOS CI stand.
- 2026-10-08T07:21:00Z rv1-t0312 FAIL (PR #202, head b59f42c5) answered, agent/claude-opus-5. B1: merged
  origin/main (PR #201 T-0313). The one conflict, `ops/lib/mutate_population_table.py` DRIVERS, resolved as the
  exact union (`"session.py", "shownhistory.py", "tripsheet.py"`); COVERED_FLOOR, -linked-digests.txt, -pinned,
  -doors, -frozen and mutate-population-allowlist.json auto-merged. On the merged tree: every digest row recomputed
  (`sed 's/\r$//' | sha256sum`) equals its file, none re-approved; check-safety-disclaimer-linked rc=0, -pinned
  rc=0, -doors rc=0, -frozen rc=0; check-store-links rc=0; check-mutate-population `253 modules, 131 covered by 32
  populations, 101 allowlisted, 4 added by this branch` / `the floor of 114 holds` rc=0. Native touched suites
  plus HandoffSourceTests (main changed it): `Test run with 12 tests in 4 suites passed`; the GRDB half
  (`#if canImport(GRDB)`: SurpriseShownStore, UserStorePrivacy, UserStoreMigration) does not compile on Windows,
  so B2 is answered by linux-core on the pushed head, quoted in the next line. Recorded, not fixed: (i) only the
  REPICK test holds the basis/history invariant (the card's place never enters the pick basis); (ii) the first
  frame can flicker before the shown history loads; (iii) the user store opens lazily on the main thread.
