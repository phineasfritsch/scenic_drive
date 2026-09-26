---
id: T-0245
title: ops/plan --menu - the full-equality oracle covers the WHOLE printed output under every flag the acceptance uses (none, --max 20, 15, 10), and ROW n is paired with URL n
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T20:43:47Z
lease_expires_at: 2026-09-27T04:43:47Z
worktree: .worktrees/T-0245
branch: task/T-0245
exclusive: []
touches: [Tests/ScenicPlanCLITests/, ops/mutate/menu_mutations.py]
pins_affected: []
reviewer: null
depends_on: [T-0239]
verify: [ops/test, ops/check-pins]
acceptance:
  - "one test through MenuCommand.run per invocation (no flag, --max 20, --max 15, --max 10) on both recorded trips (Tests/Fixtures/t0239/topanga-malibu, zuma-agoura) asserts the ENTIRE printed output equals a recomputation in the test from the recorded rows through the committed builders - every ROW line, every URL line, and that ROW n's index equals URL n's index; rv4-t0239's two survivors (X2: decision points from row 0 only when --max is below the cap; X1: ROW lines numbered index + 1) are RED by name, then green, and join ops/mutate/menu_mutations.py by name"
---
## Brief

From agent/rv4-t0239's FAIL on PR #132 (2026-09-26): round 4's equality oracle ran only the no-flag invocation, and
nothing tied a ROW line's number to its URL line's number. PR #132 merged after four rounds with this gap recorded
(CLAUDE.md rounds rule; the finding is not a P-SAFE pin - the ceiling tests caught every ceiling mutant). The lesson:
equality over the whole output, under every flag the acceptance names, from the start.

## Log
- 2026-09-26T18:19:17Z filed by agent/claude-opus-5 (orchestrator) from rv4-t0239's B1-B2.
- 2026-09-26T20:43:24Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0239 merged (PR #132, 94b5d06).
- 2026-09-26T20:43:47Z claimed by agent/claude-opus-5; lease until 2026-09-27T04:43:47Z
- 2026-09-26T21:09:18Z RULINGS by agent/claude-opus-5 (owner), before the first commit:
  R1 THE RECOMPUTATION. `MenuCommand.run` formats its `ROUTER` and `URL` lines inline - there is no formatter
  to call - so the test types those two formats itself from T-0239's quoted output (`ROUTER recorded <dir>`,
  `URL <n> waypoints=<k> <url>`). Everything else comes from committed builders, none of them MenuCommand's:
  the menu is rebuilt from `RecordedAlternatives.load(directory:ladder: RouteMenu.ladder, origin:,
  destination:)` and `RouteMenu(fastest:candidates:maxMinutes:)` with the flag's literal cap (45 for no flag,
  then 20, 15, 10) - not `MenuCommand.menu`; the endpoints are parsed from the trip literals - not taken from
  `MenuArguments`; the header is `RouteMenu.header()`, each ROW is `MenuRow.line(n)` with the test's own n,
  each URL `AppleMapsDirections(source:destination:waypoints: PlanWaypoints.decisionPoints(table:path:))`.
  The whole printed output is compared to the whole recomputation as ONE string (`joined(separator: "\n")`).
  `MenuRow.line` takes the number as an argument, so a numbering fault inside it would sit on both sides: the
  pairing is also asserted on the printed lines alone - after the two header lines they alternate `ROW n` /
  `URL n` with n the position (the first two fields of each line).
  R2 THE FILE. MenuCLITests.swift is 274 lines, so the test is `Tests/ScenicPlanCLITests/WholeMenuCLITests.swift`
  (80 lines). ops/mutate/menu_run.py (not in `touches:`) filters `RouteMenuTests|MenuCLITests` as a regex, so
  the suite's type name contains `MenuCLITests`. It names nothing from MenuCLITests.swift, because
  `menu.py --prove-vacuity` replaces that file with an empty suite and this one must still compile; it joins
  `TEST_FILES` (MIN_TEST_FILES 2 -> 3) so the vacuity proof empties it too.
  R3 "ONE TEST PER INVOCATION" is one `@Test` iterating the 8 invocations (4 flags x 2 trips), each `#expect`
  labelled `<trip> [<flags>]` - the shape of every MenuCLITests test; a parameterized `@Test`'s issue line is
  a shape menu_run.py's FAIL_LINE has not been measured on.
  R4 THE SURVIVORS' SPELLING. queue/done/T-0239 names X1 and X2 but does not spell them; spelled here on
  MenuCommand.swift and entered by name as MUTATIONS 31-32 (MIN_MUTATIONS 30 -> 32), killer the new test:
  X2 `PlanWaypoints.decisionPoints(table: row.table, path: row.path)` ->
  `PlanWaypoints.decisionPoints(table: (arguments.maxMinutes < RouteMenu.capMinutes ? menu.rows[0] : row).table, path: (arguments.maxMinutes < RouteMenu.capMinutes ? menu.rows[0] : row).path)`;
  X1 `lines.append(row.line(index))` -> `lines.append(row.line(index + 1))`.
- 2026-09-26T21:09:18Z RED THEN GREEN by agent/claude-opus-5, `swift test --scratch-path .build/T0245 --filter
  "MenuCLITests"` (both CLI suites, 14 tests), one mutant at a time on MenuCommand.swift, restored by
  `git checkout` after each:
  GREEN before (new suite alone): `Test run with 1 test in 1 suite passed`.
  X1 exit=1: `Test run with 14 tests in 2 suites failed ... with 16 issues`, every issue in
  "ops/plan --menu prints exactly its recomputation from the recorded rows under no flag and --max 20, 15, 10,
  and ROW n is followed by URL n" - 8 at WholeMenuCLITests.swift:73 (whole output) and 8 at :76 (ROW n / URL n),
  one per invocation; the 13 MenuCLITests tests passed on it (rv4's survivor reproduced).
  X2 exit=1: `... 14 tests in 2 suites failed ... with 5 issues`, all 5 in the same test at :73 - T1 --max 20
  and 15, T4 --max 20, 15 and 10, the invocations under a cap below 45 that print >= 2 rows (T1 --max 10
  prints one row, whose pins are row 0's own); the no-flag invocations stayed green, as rv4 said.
- 2026-09-26T23:06:58Z ACCEPTANCE RE-RUN by agent/claude-opus-5 (owner) at the final pre-review commit, on 65395b6 +
  this Log entry; `git fetch origin` found origin/main still at 2d76d03 (the claim commit, an ancestor), so the
  merge below is a no-op and these figures are the merged head's:
  (1) `python ops/mutate/menu.py` (committed harness, pristine md5 == HEAD for all five subjects): `population
  mutations=32 (floor 32) equivalent=2 (floor 2) ... test files=3 filter=RouteMenuTests|MenuCLITests`,
  `BASELINE exit=0`, `caught by the test that names it: 32 of 32 (wrong killer 0, trapped 0, compile-only 0,
  MISSED 0, skipped 0)`, both EQUIVALENT entries MISSED, `MUTATE OK caught=32/32 equivalent_caught=0`, exit 0.
  `caught rv4 X2: the URLs built from row 0's route when --max is below the cap by: ops/plan --menu prints
  exactly its recomputation from the recorded rows under no flag and --max 20, 15, 10, and ROW n is followed by
  URL n`; `caught rv4 X1: the ROW lines numbered index + 1 by:` the same test.
  (2) `python ops/mutate/menu.py --prove-vacuity`: `caught by the test that names it: 0 of 32 (... MISSED 32
  ...)`, `VACUITY PROOF OK: with the 3 test file(s) emptied, caught=0 (need 0) and MISSED=32 of 32`, exit 0.
  (3) `python ops/mutate/menu.py --prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control did not`
  (arm "a test file missing": `TESTS found 1 of the 3 test files, below the floor of 3`).
  (4) `swift test --scratch-path .build/T0245` exit 0: `Test run with 368 tests in 53 suites passed`, 0 issues.
  (5) `python ops/lib/check-mutate-population.py` exit 0: `P-PROC-06: every added module is covered or
  allowlisted; the floor of 41 holds`. (6) `bash ops/lib/check-line-cap` exit 0: `P-SRC-02: 134 Swift files
  tracked (Sources=50, Tests=57, apps/ios=27), none over 300 lines` (WholeMenuCLITests.swift 80, MenuCLITests.swift
  274 unchanged, ops/mutate/menu_mutations.py 188). (7) `bash ops/lib/check-exec-bits` exit 0: `P-OPS-01: 107
  files, 23 required present, all modes correct` (menu_mutations.py 100644). (8) `bash ops/queue-check` exit 0:
  `QUEUE OK (239 tasks)`. (9) `bash ops/check-pins --source-only` exit 0: `PINS ok=15 skipped=16 pending=1
  expired=0 failed=0 tier=linux source-only`. `ops/test` and the full `ops/check-pins` not run (orchestrator
  instruction); CI is their confirmation. Ready for review by an agent who is not the owner.
