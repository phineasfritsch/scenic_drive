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
