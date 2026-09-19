---
id: T-0199
title: ops/mutate/handoff - the StraightLineDistance population (an earth-radius swap, a formula swap as an EQUIVALENT entry with its witness, floor -> nearest, a dropped chain point) with a literal floor; T-0170's STILL OPEN (a)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T17:45:21Z
lease_expires_at: 2026-09-19T22:45:21Z
worktree: .worktrees/T-0199
branch: task/T-0199
exclusive: []
touches: [ops/mutate/, Tests/HandoffTests/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/mutate/handoff.py (or the existing handoff driver widened - rule it) carries a MUTATIONS table over Sources/Handoff/StraightLineDistance.swift: the radius changed by 0.1%, .rounded(.down) -> .rounded(), the destination dropped from the chain, a pin moved 1.5 km - each killed BY NAME by the test the entry names (swift test --scratch-path <own> --filter HandoffTests); MIN_MUTATIONS literal floor; --prove-floor red then green"
  - "the flat equirectangular formula on the same radius is an EQUIVALENT entry with the mutant pass's witness (haversine 112,268.093 m vs flat 112,268.146 m over the shipped chain; 707 m on a 1,065 km east-west leg) - or the test doc at StraightLineDistanceTests.swift:41-43 narrowed to 'a gross radius change' and a long synthetic leg added so a formula change IS caught; rule which"
  - "bash ops/check-pins --source-only, bash ops/lib/check-exec-bits, bash ops/queue-check bare at the final commit"
---
## Brief

From T-0170's Log (STILL OPEN (a), ruling R5) and the 00:13 panel's grounding: StraightLineDistance is a new
numeric module under Sources/ and CLAUDE.md's Verification section makes it ship its mutation population under
ops/mutate/ with a literal floor; ops/ was outside T-0170's touches, so three mutants were run by hand (all killed
by name) and the population was filed. The pre-review mutant pass found the flat-formula mutant equivalent at the
card's precision and the test doc overclaiming.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from T-0170's STILL OPEN (a) and the 00:13 panel (grounded). Not started; after #110 merges.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): T-0170 is in done/; the StraightLineDistance population (now with the LA chain from T-0178) - P-PROC-06 lists the module as DEBT.
- 2026-09-19T17:45:21Z claimed by agent/claude-opus-5; lease until 2026-09-19T22:45:21Z
- 2026-09-19T17:45:22Z at claim by agent/claude-fable-5-1 (orchestrator): #121 landed wholeMiles(through:) on StraightLineDistance.swift (floored from the same metres; the LA literal 29.48 cannot separate floor from round - the Skyline 69.76 and the synthetic 1.988-mile test carry it) - the population covers wholeMiles too. Swift 6.3.3 is NATIVE on this Windows box (C:/Users/phineasf/AppData/Local/Programs/Swift/Toolchains/6.3.3+Asserts/usr/bin/swift, on PATH in git-bash); ops/mutate/handoff.py already runs swift build/test with --scratch-path .build/mutate-handoff.
- 2026-09-19T17:52:05Z RULING by agent/claude-opus-5 (owner), before any code. Measured first: `wc -l ops/mutate/handoff.py` = 603.
  (R1) A NEW DRIVER, `ops/mutate/straightline.py` + `ops/mutate/straightline_mutations.py`, not a widening of handoff.py.
  Two reasons, both mechanical. (i) handoff.py is 603 lines and CLAUDE.md caps a file at 300; the repo's own answer to a
  runner that outgrew the cap is the split scenic_tags.py/scenic_tags_mutations.py and geometry.py/geometry_mutations.py
  document (`R5's seven took the runner past the 300-line cap`), so adding a table to a file already at 2x the cap is the
  wrong direction. (ii) handoff.py's SUBJECT_MODULES shape is a tuple of the files its MUTATIONS edit, and its
  `population_floor()` refuses when a declared subject is mutated by nothing; StraightLineDistance's population must also
  mutate `Sources/ScenicKit/Geo/Geo.swift` (the radius and the formula live there, NOT in the subject) and
  `Sources/Handoff/SkylineRoute.swift` (the moved pin), which are DEPENDENCIES, not subjects. Folding them into handoff.py
  would either leave them undeclared inside a file whose floor reads the declaration, or widen handoff.py's stated subject
  to two ScenicKit/route files it does not measure - the "stated subject wider than actual subject" defect handoff.py's own
  docstring was written against. The new driver therefore declares SUBJECT_MODULES = ("Sources/Handoff/StraightLineDistance.swift",)
  ONLY, and states the two dependency files as dependencies. Protocol borrowed, not reinvented: gates.py's named-test regex
  and `failing_test_names`, geometry.py's `killers` list per entry (a catch that is not BY THE NAMED TEST is a FAILURE, and
  an emptied `killers` list is refused before any build), handoff.py's `--prove-vacuity` and `--prove-floor`, and
  scenic_tags.py's `MUTATE OK caught=N/N` closing line.
  (R2) THE MUTATIONS, each with the test that kills it BY NAME (display names, which is what Swift Testing prints):
  1 radius x1.001 (Geo.swift 6_371_008.8 -> 6_377_379.8088) and 2 radius x0.999 (-> 6_364_637.7912), both killed by
  "the whole-kilometre figure is the number the card shows" (the 1 m band on 112_268.093 m); 3 `.rounded(.down)` ->
  `.rounded()` in `wholeKilometers(through:)`, killed by "the figure is floored, not rounded: 1999 m of chain is 1 km and
  never 2"; 4 the same in `wholeMiles(through:)`, killed by "the miles are floored too: 1.99 miles of chain is 1 mile and
  never 2" AND "the whole-mile figure is the number the screen renders, from the same metres" (69.76 -> 70); 5 the
  destination dropped from `skylineRoutePoints`, killed by "the chain is the shipped pins in driving order, then the
  destination"; 6 pin 1 moved 1.7 km (37.70526 -> 37.72026, 1667.9 m up from the I-280 on-ramp), killed by "every point is
  within a kilometre of where this suite thinks it is"; 7 the metres-to-miles constant 1% too LARGE (1_609.344 ->
  1_625.43744) and 8 1% too SMALL (-> 1_593.25056); 9 `wholeMiles` derived from the floored kilometres
  (`Double(wholeKilometers(through:)) * 0.621371`) instead of the metres; 10 the flat equirectangular formula on the same
  radius. MEASURED BEFORE FILING, not assumed: 7, 9 and 10 are NOT killed by the suite as it stands. 7 at +1% takes the
  card from 69.760 mi to 69.070 mi - still 69 - and the 1.988-mile synthetic to 1.969 - still 1; 9 gives 112 km * 0.621371
  = 69.59 -> 69 on Skyline, 47 * 0.621371 = 29.20 -> 29 on LA (the claim-time line's point: 29.48 separates nothing) and
  3.107 -> 3 on the 1.99-mile synthetic; 10 totals 112_268.146 m against 112_268.093 m, 0.053 m, INSIDE the one-metre band.
  Per the task's rule the entries are not weakened: two tests are ADDED to Tests/HandoffTests/StraightLineDistanceTests.swift,
  demonstrated RED against the live mutants and green with them restored.
  (R3) THE FLAT FORMULA IS NOT AN EQUIVALENT MUTANT, so it ships in MUTATIONS with a test that kills it, not in EQUIVALENT.
  An EQUIVALENT entry asserts "no input separates this from the original"; the witness in the task is itself a separating
  input - 707.257 m and one whole mile on a 1,065 km east-west leg (37.00000,-122.00000 -> 37.00000,-110.00000:
  haversine 1_064_944.819 m / 661 mi, flat 1_065_652.075 m / 662 mi, both recomputed here). Filing a mutant as EQUIVALENT
  when a two-line test kills it records a closable gap as a feature, which is what handoff.py's KNOWN_MISSED note calls
  worse than no entry at all. So: new test `aLongEastWestLegPinsTheFormulaAndTheMileConstant` (display name "a 1,065 km
  east-west leg pins the formula and the mile constant") pins that leg's metres to 1 m and its miles to 661, killing 10, 7
  and 8; new test `theMilesComeFromTheMetresAndNotFromTheFlooredKilometres` ("the miles come from the metres, not from the
  floored kilometres") uses the only chain length that separates the two floorings - 0.04496 deg of latitude is 4_999.331 m,
  3.1064 mi -> 3, while floor(4.999 km) * 0.621371 = 2.4855 -> 2 - killing 9. And the doc on
  `StraightLineDistanceTests.straightLineMeters` is NARROWED in the same commit: it claimed the one-metre band catches "a
  different formula", which the 0.053 m above disproves; it now claims the radius only and points at the long leg for the
  formula. EQUIVALENT is not left empty - it carries `guard points.count > 1` -> `>= 2`, whose witness is arithmetic: over
  Int, `n > 1` and `n >= 2` are the same predicate, so no chain separates them and no test can be written.
  (R4) MIN_MUTATIONS = 10, the REAL count and not a round number under it (gates.py's lesson: a floor of 18 against 21 let
  a reviewer delete three mutations and still read a clean sheet). `--prove-floor` demonstrates the refusal on seven arms
  plus a clean control, with NO build: MUTATIONS emptied; MUTATIONS truncated to 9; the floor raised to 11 against the real
  population of 10 (the task's floor+1 arm); EQUIVALENT emptied; one entry's `killers` emptied; every mutation that edits
  the declared subject removed; TESTS globbed down to 0.
  (R5) REGISTRATION in ops/lib/check-mutate-population.py: "straightline.py" joins DRIVERS (that whitelist REFUSES, exit 2,
  on any ops/mutate/*.py with a `__main__` block it does not classify, so a new driver is not optional there) and
  "Sources/Handoff/StraightLineDistance.swift" joins COVERED_FLOOR, whose literal floor rises 23 -> 24 and whose DEBT list
  loses that module. straightline_mutations.py has no `__main__` block and is read as part of the straightline* family by
  `driver_code`, exactly as scenic_tags_mutations.py is. That file is under ops/lib/, outside this task's original
  `touches:`, so `touches:` gains `ops/lib/` in the commit that carries this entry, BEFORE the gate change is staged.
- 2026-09-19T18:09Z the cheap checks, RED then GREEN, quoted as they landed (agent/claude-opus-5).
  `python ops/mutate/straightline.py --prove-floor` -> seven arms refused and the control did not, exit 0:
    FLOOR ARM   MUTATIONS emptied - a clean sheet over nothing           MUTATIONS holds 0 entries, below the floor of 10
    FLOOR ARM   MUTATIONS one short of the floor                         MUTATIONS holds 9 entries, below the floor of 10
    FLOOR ARM   the floor raised to 11 against a population of 10        MUTATIONS holds 10 entries, below the floor of 11
    FLOOR ARM   EQUIVALENT emptied                                       EQUIVALENT holds 0 entries, below the floor of 1
    FLOOR ARM   one entry's killers emptied - 0 red of 0 named           these entries name no killer: the earth radius 0.1% too large. ...
    FLOOR ARM   every mutation of the declared subject removed           MUTATIONS holds 4 entries, below the floor of 10
    FLOOR ARM   TESTS globbed down to nothing - vacuity would empty nothing TESTS globbed 0 files from HandoffTests, below the floor of 1
    FLOOR ARM   CONTROL: unpatched                                       no refusal, as required
    FLOOR PROOF OK: 7 of 7 arms refused and the control did not
  RED A, the floor against the SHIPPED population and not a patched one - `MIN_MUTATIONS = 10` edited to `11` on disk,
  `python ops/mutate/straightline.py` -> "REFUSING TO RUN: MUTATIONS holds 10 entries, below the floor of 11", exit 2, no
  build attempted; restored to 10 (`150:MIN_MUTATIONS = 10`) and the run proceeds.
  RED B, the registration - "straightline.py" removed from DRIVERS in ops/lib/check-mutate-population.py,
  `python ops/lib/check-mutate-population.py` -> "P-PROC-06: ops/mutate: runnable driver(s) in neither DRIVERS nor PROBES:
  straightline.py. Classify a new driver; never ignore one.", exit 2; restored and GREEN: "P-PROC-06: 74 modules, 25
  covered by 12 populations, 27 allowlisted, 0 added by this branch ... every added module is covered or allowlisted; the
  floor of 24 holds" (23 -> 24, and Sources/Handoff/StraightLineDistance.swift has left the 23-entry DEBT list, which is
  now 22 and still names Geo.swift and SkylineRoute.swift - the two dependencies this population mutates and, correctly,
  does not claim).
  `swift test --scratch-path .build/T0199 --filter HandoffTests` with the two new tests in place: "Test run with 86 tests
  in 12 suites passed after 0.102 seconds", exit 0 (84 before; the two added are the long east-west leg and the miles that
  do not come from the floored kilometres).
- 2026-09-19T21:26:00Z the acceptance block, whole, on the merged head, and the ruling on a main that moved under
  it (agent/claude-opus-5, owner). The session that filed R1-R5 and the 18:09Z RED/GREEN pairs died on a usage
  limit inside this block; nothing below is re-derived from its stdout - every line is from a run made after the
  resume, on a merged head.
  (M1) THE MERGE. `git fetch origin && git merge --no-edit origin/main`, three times, because main moved under the
  block twice. The FIRST merge (#122, T-0217 extractadapter) carried one CONTENT CONFLICT, in
  ops/lib/check-mutate-population.py: main had added "extractadapter.py" to DRIVERS, this branch "straightline.py".
  Resolved as the union, alphabetical, 13 names, neither side dropped. COVERED_FLOOR auto-merged (main's
  accessrule.py and extractadapter.py beside this branch's StraightLineDistance.swift), and the floor is computed
  from it, so the gate now reads 26 and NOT the 24 quoted at 18:09Z: 23 + main's two + this branch's one. That
  restated floor is the number the merged head prints. Merge commits 259da45, cc04100, 9bfe1bf, 8c3521f.
  (M2) THE BLOCK, BARE, on 9bfe1bf (its merge of origin/main 28d7745), in order, each exit quoted:
    python ops/mutate/straightline.py
      caught by the test that names it: 10 of 10   (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)
      MUTATE OK  caught=10/10 equivalent_caught=0                                                       exit 0
    python ops/mutate/straightline.py --prove-vacuity
      VACUITY PROOF OK: with the 12 test file(s) emptied, caught=0 (need 0) and MISSED=10 of 10          exit 0
    python ops/mutate/straightline.py --prove-floor
      FLOOR PROOF OK: 7 of 7 arms refused and the control did not                                       exit 0
    swift test --scratch-path .build/T0199 --filter HandoffTests
      Test run with 86 tests in 12 suites passed after 0.095 seconds                                    exit 0
    python ops/lib/check-mutate-population.py
      P-PROC-06: every added module is covered or allowlisted; the floor of 26 holds                    exit 0
    bash ops/check-pins --source-only
      PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only                         exit 0
    bash ops/lib/check-line-cap
      P-SRC-02: 92 Swift files tracked (Sources=29, Tests=42, apps/ios=21), none over 300 lines         exit 0
    bash ops/lib/check-exec-bits
      P-OPS-01: 87 files, 23 required present, all modes correct                                        exit 0
    bash ops/queue-check
      QUEUE OK (221 tasks)                                                                              exit 0
  (M3) THE PER-MUTATION DETAIL, printed in full by the run on merge head 259da45 and reprinted in its closing
  counts by the 9bfe1bf re-run (same population, same three pristine md5s):
    population  mutations=10 (floor 10)  equivalent=1 (floor 1)  subject=StraightLineDistance.swift  test files=12
    dependencies mutated, never declared: Geo.swift, SkylineRoute.swift
    pristine StraightLineDistance.swift md5 8413b2c95c79dc4cedd40cb452da40bb == HEAD
    pristine Geo.swift md5 8107f142ef73e0a759a0e7fe089ead4d == HEAD
    pristine SkylineRoute.swift md5 11aab6adad7e703e6e83290cdc1362c8 == HEAD
    BASELINE    --filter HandoffTests   exit=0
    caught  the earth radius 0.1% too large      by: a 1,065 km east-west leg pins the formula and the mile constant | the figure is floored, not rounded: 1999 m of chain is 1 km and never 2 | the whole-kilometre figure is the number the card shows | the miles come from the metres, not from the floored kilometres | the whole-kilometre figure is the number the LA drive shows
    caught  the earth radius 0.1% too small      by: a 1,065 km east-west leg pins the formula and the mile constant | the whole-kilometre figure is the number the card shows | the whole-kilometre figure is the number the LA drive shows
    caught  the kilometre figure rounds to nearest instead of flooring   by: the figure is floored, not rounded: 1999 m of chain is 1 km and never 2 | a 1,065 km east-west leg pins the formula and the mile constant | the miles come from the metres, not from the floored kilometres
    caught  the mile figure rounds to nearest instead of flooring        by: the whole-mile figure is the number the screen renders, from the same metres | a 1,065 km east-west leg pins the formula and the mile constant | the miles are floored too: 1.99 miles of chain is 1 mile and never 2
    caught  the destination falls off the end of the shipped chain       by: the whole-kilometre figure is the number the LA drive shows | the distance accessor reports each drive's own figure | each drive maps to its own route, and the default is the LA drive | every point is within a kilometre of where this suite thinks it is | the whole-mile figure is the number the screen renders, from the same metres | the chain is the shipped pins in driving order, then the destination | the whole-kilometre figure is the number the card shows
    caught  pin 1 moved 1.7 km off the I-280 on-ramp                     by: seven pins still build a handoff URL | every point is within a kilometre of where this suite thinks it is | every pin is the coordinate the reverse geocode returned | the whole-kilometre figure is the number the card shows | the whole-mile figure is the number the screen renders, from the same metres | the distance accessor reports each drive's own figure | the whole-kilometre figure is the number the LA drive shows | the chain is the shipped pins in driving order, then the destination
    caught  the metres-to-miles constant 1% too large                    by: a 1,065 km east-west leg pins the formula and the mile constant
    caught  the metres-to-miles constant 1% too small                    by: the miles are floored too: 1.99 miles of chain is 1 mile and never 2 | the whole-mile figure is the number the screen renders, from the same metres | a 1,065 km east-west leg pins the formula and the mile constant
    caught  the miles derived from the floored kilometres instead of the metres   by: the miles come from the metres, not from the floored kilometres
    caught  the flat equirectangular formula on the same radius          by: a 1,065 km east-west leg pins the formula and the mile constant
    MISSED  the two-point guard spelled >= 2 instead of > 1   exit=0  no test objected   <- the EQUIVALENT entry;
      anything but MISSED there is a FAILURE, and its witness is arithmetic (over Int, `n > 1` and `n >= 2` are the
      same predicate, so no chain separates them).
  R3 held under measurement, not under argument: the flat-formula mutant is CAUGHT, by name, by the long east-west
  leg, so it is a MUTATION and not the EQUIVALENT entry the Brief offered; entries 7 and 9 are caught by the two
  tests added for them. 10 of 10 by the named killer, 0 wrong-killer, 0 trapped, 0 compile-only, 0 MISSED.
  (M4) THE ANCESTOR RULING. `git merge-base --is-ancestor origin/main HEAD` exited 1 after the cc04100 block and
  again after the 9bfe1bf block: the block takes ~13 minutes (two mutation passes, eleven swift builds each) and
  other sessions pushed queue commits inside every one of those windows. Chasing it by re-running the whole block
  is unbounded, so it was ruled by MEASURING the delta instead of asserting it. Merged once more - 8c3521f, over
  origin/main 7585e39 - and:
    git diff --name-only 9bfe1bf HEAD
      queue/LOCKS/root-package.lock
      queue/claimed/T-0219-p-data-03-corpus-half-meta-region-is-stamped-by-etl-corpus-a.md
      queue/claimed/T-0224-etl-measurement-the-residential-and-service-way-length-di.md
      queue/done/T-0224-etl-measurement-the-residential-and-service-way-length-di.md
      services/etl/tests/measure_way_lengths.py
      services/routing/tests/measure_runs.py
  No gate, no pin file, no Sources/ file and no services/etl/etl/ module: not one input of the mutation stages or
  of the Handoff suite moved, and services/etl/tests/ is outside check-mutate-population's MODULE_ROOTS. The five
  checks that DO read the tree were re-run bare on 8c3521f and printed the same lines as (M2) - PINS ok=15
  skipped=16 pending=1 expired=0 failed=0; P-PROC-06 floor of 26 holds; P-SRC-02 92 Swift files, none over 300;
  P-OPS-01 87 files, 23 required present, all modes correct; QUEUE OK (221 tasks) - and there
  `git merge-base --is-ancestor origin/main HEAD` exits 0. The push follows this commit.
  (M5) wc -l, every touched file, on 8c3521f (the task file measured before this entry was appended):
    354 ops/mutate/straightline.py
    154 ops/mutate/straightline_mutations.py
    208 Tests/HandoffTests/StraightLineDistanceTests.swift
    297 ops/lib/check-mutate-population.py
    116 queue/claimed/T-0199-ops-mutate-handoff-the-straightlinedistance-population.md
  `git ls-files -s` on the three ops files: 100644 each, which is what the task's instruction and P-OPS-01 require
  of an ops/**/*.py that is not on the required-executable list.
  RECORDED, not buried: straightline.py is 354 lines, over CLAUDE.md's 300-line cap. The mechanical gate quoted
  above (P-SRC-02) counts Swift files only and no ops/mutate driver is under 300 (handoff.py 603). R1's reason for
  a new driver rather than a widening still holds - the split keeps this runner at 508 lines across two files
  against handoff.py's 603 in one - but the cap is written for every file, this one is over it, and a reviewer
  should read that here rather than discover it.
- 2026-09-19T21:54:53Z RULING by agent/claude-opus-5 (owner) on the pre-review mutant pass
  (.artifacts/signoffs/t0199-mutant-pass.md - solid, ONE survivor, PROBE 11) and on the 300-line cap,
  before the commit that closes them.
  (R6) PROBE 11 - the double floor at the ENTRY POINT - IS NOT CONSTRUCTIBLE AS A KILLED MUTATION, and is
  filed as EQUIVALENT with the domain enumeration as its witness. The pass's verdict line, quoted:
  `MISSED        PROBE 11: wholeMiles(for:) derived from the floored wholeKilometers(for:) exit=0  no test
  objected`. The instruction was to bind a test to `wholeMiles(for:)` over a chain the test CONSTRUCTS.
  Measured before writing anything: `wholeMiles(for drive: HandoffDrive)` takes a `HandoffDrive`, and
  `HandoffDrive` is `enum HandoffDrive: String, CaseIterable` with exactly TWO cases whose `chain` is
  `waypoints + [destination]` read from `SkylineRoute`/`SantaMonicaMountainsRoute` `static let`s. There is
  no case to construct, no chain parameter and no injection point, so a test cannot hand that entry point
  4 km of anything. The bands named in the instruction are real and I recomputed them - 3_700 m = 2.2991 mi
  -> 2 against floor(3 km) x 0.621371 = 1.8641 -> 1; 1_650 m = 1.0253 -> 1 against floor(1 km) x 0.621371 =
  0.6214 -> 0 - but they are bands on `wholeMiles(through:)`, the HELPER, which is population entry 9 and is
  already killed BY NAME over the 4_999.331 m chain `theMilesComeFromTheMetresAndNotFromTheFlooredKilometres`
  constructs (3 mi against the double floor's 2). The named fallback does not exist either: there is no
  `ops/plan` in this tree (`ls ops/`: agent-preflight, api-url, check-pins, claim, deploy, deploy-routing,
  etl-*, lib, lock, merge, mutate, new-task, prod-read, publish-tiles, queue-check, queue-next, queue-sweep,
  review, sane, score-review, test), and the card is
  `apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/DriveFacts.swift:45`, an Apple-only target that the
  Linux package's `HandoffTests` cannot import and this box cannot build. So the two shipped drives ARE the
  entry point's whole input domain, both agree either way (Skyline 112_268.093 m -> 69.7602 -> 69 vs
  floor(112.268 km) = 112 -> 69.5936 -> 69; LA 47_445.124 m -> 29.4810 -> 29 vs 47 -> 29.2044 -> 29), and
  the honest filing is an EQUIVALENT entry whose witness is that exhaustion - NOT a MUTATIONS entry with a
  killer softened until it passes. The witness states the margin, because a domain equivalence is not an
  arithmetic one and must not be filed as permanent: 268.1 m off the Skyline chain puts floor(km) at 111 ->
  68.9722 -> 68 against the metres' 69, and 445.1 m off the LA chain puts it at 46 -> 28.5831 -> 28 against
  29. The tripwire is written, not promised: the new test ranges over `HandoffDrive.allCases` comparing this
  entry point with each drive's OWN metres, so the day a pin moves that far or a third drive lands, this
  EQUIVALENT entry stops reporting MISSED and the arm FAILS the run until it is ruled again. Recorded
  plainly: the double floor AT `wholeMiles(for:)` is unkillable today. That is the gap, it is in the
  population as a witnessed entry and in this Log, and it is not being reported as covered.
  (R7) The pass's OTHER finding, which is the one that buys a mutation: the entry point had no mutation at
  all. Entries 1-10 each edit a helper (`meters`, `wholeKilometers(through:)`, `wholeMiles(through:)`,
  `skylineRoutePoints`) or a dependency (`Geo.swift`, `SkylineRoute.swift`); nothing in the population
  edited the body of the symbol `DriveFacts` renders, so a rewrite of `wholeMiles(for:)` was measured by
  nobody. MUTATION 11: `wholeMiles(through: drive.chain)` -> `wholeMiles(through: HandoffDrive.skyline.chain)`
  - the entry point measuring the Skyline chain whatever drive it is handed, which is T-0202's drift (a
  figure that names one drive while the tap takes another) and renders 69 miles of somebody else's drive on
  the LA screen. Its killers, both named: the new
  `every drive's miles are that drive's own chain, floored from that drive's metres` and the standing
  `the whole-mile figure is the number the LA drive renders, from the same metres`. MIN_MUTATIONS 10 -> 11
  and MIN_EQUIVALENT 1 -> 2, the REAL counts and not round numbers under them (R4's rule), and `--prove-floor`
  gains an eighth arm demonstrating the raised EQUIVALENT floor refusing.
  (R8) THE CAP: `wc -l ops/mutate/straightline.py` = 354 against CLAUDE.md's 300. Ruled SPLIT, not exempt.
  The exemption argument exists and I am naming it rather than leaning on it: every ops/mutate driver is
  over the cap today, handoff.py at 603. A precedent for a violation is not a licence, and this repo's own
  answer to a runner that outgrew the cap is a family split - budget.py beside budget_arms.py,
  budget_boundaries.py, budget_paths.py and budget_tree.py; geometry.py beside geometry_arms.py and
  geometry_tree.py; scenic_tags.py beside scenic_tags_mutations.py. So the MUTANT RUNNER moves out:
  `FAIL_LINE`, `failing_test_names`, `empty_suite`, `head_bytes`, `not_at_head`, `build`, `test`, `run_all`,
  `SCRATCH`, `FILTER` go to `ops/mutate/straightline_run.py`, and straightline.py keeps the CLI, the floors
  and the proof arms - the part that decides whether a run is ALLOWED to happen. The population is untouched
  by the split; the only semantic change is that `HARNESS` gains the third file, so the runner is compared
  with `git show HEAD:` before a run like the other two (a runner edited on disk is precisely the false
  verdict that guard exists for). The family is still ONE driver to the gate: check-mutate-population.py:125
  globs `ops/mutate/<stem>*.py` for `driver_code`, and its DRIVERS whitelist refuses only files carrying a
  `__main__` block - straightline_run.py has none, exactly as straightline_mutations.py has none. Measured
  after: straightline.py 242, straightline_run.py 149, straightline_mutations.py 197,
  Tests/HandoffTests/StraightLineDistanceTests.swift 237 (was 208) - every one under 300, and the new file
  is 100644 like every other ops/mutate/*.py (it is imported, never invoked).
