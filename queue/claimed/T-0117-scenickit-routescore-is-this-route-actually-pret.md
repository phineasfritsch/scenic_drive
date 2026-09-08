---
id: T-0117
title: ScenicKit RouteScore: is this route actually pretty, length-weighted and invariant to how the router split the edges
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:54:42Z
lease_expires_at: 2026-09-08T15:54:42Z
worktree: .worktrees/T-0117
branch: task/T-0117
exclusive: []
touches: [Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/, ops/mutate/, .gitignore]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/test -> TESTS linux=142/76 ios=skipped failed=0 skipped=0, exit 0"
  - "swift test -> 39 tests in 5 suites passed, exit 0"
  - "python ops/mutate/routescore.py -> 29 of 29 caught by a named test; 0 trapped, 0 compile-only, 0 MISSED, 0 skipped; both EQUIVALENT mutants MISSED as required; exit 0"
  - "RED: python ops/mutate/routescore.py --prove-vacuity -> caught=0 and MISSED=29 of 29 with the tests replaced by empty suites, exit 0"
  - "RED: the same harness with every anchor stale -> VACUITY PROOF FAILED, exit 1 (the old pass condition printed OK, exit 0)"
---
## Brief

`LambdaSearch` (T-0116) finds the routes that FIT the time budget. This decides which of them is worth
driving, and whether any of them is.

    0.60 * mean + 0.25 * p90 - 0.15 * dudFraction + 0.10 * min(1, episodes / 3)

Four terms, four different questions, and dropping any one of them lets a bad route score well:

  * **mean** - pretty on average? Alone it rewards a route that is uniformly mediocre.
  * **p90** - is any of it really good? A flat 0.5 the whole way is a commute, not a drive.
  * **dudFraction** - how much is actively dull? The only negative term, and the one that stops a route
    buying a good mean with one spectacular canyon bolted onto twenty minutes of arterial.
  * **episodes** - is the pretty part *sustained*? Prettiness scattered over fifty 200 m fragments is a
    scenic drive's worth of scenery arranged so you never get to enjoy any of it.

Below `honestFailureThreshold` the product says *"not much pretty within 25 minutes of this drive"* instead
of presenting a dull route as an answer.

**No `Package.swift` change**: `Sources/ScenicKit/Scoring/` is inside the existing ScenicKit target path,
which SwiftPM globs. The lock on that serial file is held by T-0114 and was not needed here.

### The difficulty is length weighting, and it is the whole task

The router may return one OSM way as six path-detail intervals, six ways as one, and the route in either
direction. **None of that changes the drive, so none of it may change the score.** A per-edge mean lets a
router that splits a dull edge in half give that edge two votes; a percentile taken over the edge list
answers a question about the router's segmentation rather than about the road.

Every statistic is computed over metres. The plan pins this as two properties - *"RouteScore invariant under
reversal (1e-9) and re-encoding (0.5%)"* - and those are the assertions here that can fail for a real reason.

## Log

### GREEN

    swift test --scratch-path .build-T0117
    Test run with 29 tests in 4 suites passed after 0.030 seconds.   exit 0

### RED, eight ways, and seven of them are the *natural* implementation

    caught  mean over the edge list instead of over metres         exit=1
    caught  percentile by index instead of by length               exit=1
    caught  dud fraction over the edge list instead of over metres exit=1
    caught  ask the episode question per edge                      exit=1
    caught  forget the episode that the route ends on              exit=1
    caught  add the dud fraction instead of subtracting it         exit=1
    caught  drop the clamp and let a duds-only route score negative exit=1
    caught  score an empty route rather than refusing it           exit=1
    8 of 8 mutations caught                                        exit=0

The first four are not sabotage - they are what you write if you are not thinking about metres.
`edges.reduce(0) { $0 + $1.score } / count` is the shorter line, `sorted[Int(0.9 * count)]` is the obvious
percentile, and `if edge.score > 0.6 && edge.length >= 800` is the obvious episode test. Each produces a
number for every route and each describes the router instead of the road.

The fixtures that separate them are small and specific:

  * **10 m at 1.0 against 10 km at 0.1.** Two edges either way. The index percentile calls this route
    spectacular; the length-weighted one returns 0.1, which is what the drive is.
  * **A 5 km canyon returned as twelve 420 m intervals.** Every interval is under the 800 m episode minimum
    on its own, so the per-edge test counts zero episodes for the prettiest road in the region. This is the
    normal case, not an exotic one - OSM splits ways at junctions.
  * **Fifty 200 m gems separated by 300 m of arterial.** Excellent mean, zero episodes.

### One mutation was not caught, and the reason is a finding rather than a hole

`score an empty route as zero rather than refusing` first targeted only `guard !edges.isEmpty`. Nothing
objected, correctly: `guard total > 0, total.isFinite` catches the empty case on its own, so removing the
first guard changes no behaviour. **The two guards are redundant for the empty input.**

That redundancy is kept deliberately - `!edges.isEmpty` states the intent at the point a reader looks for it,
and the cost is a comparison - but a mutation that changes nothing must not be recorded as a caught defect.
Retargeted at both guards together, so an empty route becomes `0/0` and propagates a NaN into a score, it is
caught by `emptyIsNil`.

The distinction matters here specifically: returning 0 for an empty route would make *"the router found
nothing"* indistinguishable from *"the router found a freeway"*, and those need different words on screen.

### `dudThreshold` is not from the plan, and is labelled as such

The plan names the `dud_frac` term and its 0.15 weight and **does not specify the threshold**. 0.25 is chosen
to mean "actively dull rather than merely unremarkable": it puts motorway and trunk (0 by construction) and
bare arterial into the dud bucket while leaving ordinary residential and unclassified out. It is a named
constant, not an inlined literal, so that tuning it is a one-line change with a test that moves - and the
source says plainly that it was chosen here rather than handed down, because a tuning constant mistaken for
a specified one is a constant nobody dares to tune.

### Consistent with the product invariants

`motorwayIsADud` asserts the CLAUDE.md rule from the scoring side: an 8 km motorway shoulder counts fully
toward `dudFraction` and the route still scores, still keeps its episode, and is still returnable. Penalised,
not excluded - the freeway shoulder around a scenic middle is the shape most drives over 15 km have to take.

### Not done

No RouteScore-based candidate selection, no rat-run detection, no `areas` re-issue. Those need the router
and belong to the caller. This is the arithmetic, and it takes a plain array so it can be tested against
exact adversarial shapes with no network, graph or container.

---

## Fix pass: reviewer-pr73 found a real bug in the shipped code

Not a test gap. **`lengthWeightedPercentile` was not invariant under re-splitting** - the one property this
whole task exists to guarantee, and the one the plan pins at 0.5%.

`let target = total * fraction` took `total` from a separate `reduce`, while `cumulative` was a different
partial sum. Floating-point addition is not associative, so the two disagreed in their last bits; when the
percentile boundary fell exactly on an edge boundary, `cumulative >= target` went whichever way the noise
pointed and p90 jumped to the next distinct score.

Demonstrated by the reviewer against the compiled source, on `[9000 m @ 0.1, 1000 m @ 0.9]` - where the
boundary sits exactly at p90 - split into k equal pieces per interval, which is what the router does at
junctions:

    k = 1, 2, 4                              p90 = 0.1   value = 0.031333
    k = 3, 7, 9, 12, 21, 22, 23, 26, 28, ...  p90 = 0.9   value = 0.231333

A 0.200 swing on a 0...1 score, from nothing but how the path was segmented, against a test tolerance of
1e-9. `reEncodingInvariant` passed only because the `realistic` fixture never puts the boundary on an edge
boundary - its worst delta over the same range of k is 9.99e-16. Reversal invariance was genuinely fine.

**Fixed** by accumulating the total in the same order and by the same additions as the running sum, and
breaking the residual tie deterministically toward the lower score with a tolerance relative to the route's
own length. `percentileIsStableOnTheBoundary` now runs the reviewer's exact fixture over k = 1...40.

### Four test gaps behind it, all closed

  * **The percentile's sort direction had no witness.** Its only direct fixture, `[10 m @ 1.0, 10 km @ 0.1]`,
    returns 0.1 under *both* directions, so one character turning p90 into p10 left the suite green - and
    moved the realistic route's p90 from 0.83 to 0.00. New fixture is asymmetric.
  * **Which percentile is used was pinned by nothing.** `matchesTheFormula` recomputes the expected value
    from `s.p90`, so it stays self-consistent under any definition; 0.90 -> 0.70 survived it.
  * **Threshold strictness was stated only in doc comments**, which CLAUDE.md forbids anchoring on. No
    fixture used a score of exactly 0.6 or 0.25, or a run of exactly 800 m. All three now have one - and the
    harness caught that a run of exactly 800 m needs TWO fixtures, because a run ending the route is closed
    after the loop while one closed by a dull stretch is closed inside it.
  * **`dudThreshold`'s own claim was false.** The source said it was named rather than inlined "so that
    tuning it is a one-line change with a test that moves". Nothing moved. Now it does.

### The harness, rebuilt

Moved to `ops/mutate/routescore.py` (tracked; `.artifacts/` is gitignored, so the old acceptance line could
not be run from a clone), builds each mutation before believing a compile failure, requires a NAMED TEST to
fail rather than a non-zero exit, and reports `trapped` separately for a mutation detected by a crash.

    caught by a named test: 20   trapped: 0   compile-only: 0   MISSED: 0   of 20
    VACUITY PROOF OK: with no tests present, 0 mutations were reported caught

Eight of the twenty are numeric-constant mutations. **A reviewer on T-0116 pointed out that every mutation
in that harness was structural and not one touched a number** - which is exactly where such a suite is
blind, and it was true here too.

### One mutation is a no-op, and that is recorded rather than hidden

Taking the total with a separate `reduce` is no longer independently a defect: the boundary tolerance
absorbs the discrepancy. Either half of the fix is sufficient alone, so the mutation that reproduces the
shipped bug has to remove BOTH - which is the shape the code had when the reviewer found it. That is what
the mutation now does.

---

## Second fix pass: the boundary test asserted consistency, never correctness

reviewer2-pr73 confirmed the headline re-encoding bug is genuinely fixed, F2-F4 closed with real behaviour
tests, the harness move right and the vacuity proof real - then blocked on the test written to close F1.

`percentileIsStableOnTheBoundary` compared every split against `whole.p90` and `whole.value`, **both taken
from the function under test on the same fixture**. It asserted the percentile was CONSISTENT across splits
and never that it was RIGHT. Flipping one character - `c >= target - tolerance` to `target + tolerance` -
restores the exact 0.200 swing the first reviewer blocked on, with this test green.

The expected values are now literals worked out by hand: 90% of 10000 m is 9000 m, the first 9000 m scores
0.1, so p90 is 0.1; and the four terms give 0.60*0.18 + 0.25*0.1 - 0.15*0.9 + 0.10/3 = 0.031333. The
unsplit route is checked against them too, so the fixture itself has a witness.

`flip the boundary tolerance to the wrong side` is now a mutation in the harness: 21 caught, 0 missed.

---

## Third fix pass: the same boundary bug, one function further down

reviewer-rvw-pr73 confirmed the percentile fix and the boundary test, then blocked on B1 - **`episodes()`
had the identical defect the percentile had just been fixed for**, and on four items the second review had
already asked for and not received.

### VERIFICATION (F8 - the third reviewer to ask for these; here they are)

    ops/test                                      TESTS linux=142/76 ios=skipped failed=0 skipped=0   exit 0
    ops/check-pins                                PINS ok=11 skipped=0 pending=2 expired=0 failed=0   exit 0
    ops/check-pins --source-only                  PINS ok=4 skipped=9 pending=0 expired=0 failed=0    exit 0
    ops/queue-check                               QUEUE OK (107 tasks)                                exit 0
    swift test --scratch-path .build-T0117fix     39 tests in 5 suites passed                         exit 0
    python ops/mutate/routescore.py               29 of 29 caught, 0 trapped/compile-only/MISSED/skip exit 0
    python ops/mutate/routescore.py --prove-vacuity  caught=0, MISSED=29 of 29                        exit 0

`ops/test` had never been recorded because it could not pass on this box: it exits 1 at the Worker tier
with "services/api exists but vitest produced no report" whenever `services/api/node_modules` is absent,
and it was absent in main and in every task worktree. `npm ci` in services/api (7 s, from the committed
lockfile) is all it needed. That is an environment fact, not a code change - no JS or TS is in this diff.

### B1 - BLOCKER, and it was product logic, not a test gap

`episodes()` accumulated `run` across edges and then compared it against `episodeMinLength` with a bare
`>=`. The percentile got a boundary tolerance at line 130 for exactly this reason; `episodes()` did not.
800 m returned by the router as k equal intervals does not sum to 800 m, so the episode was thrown away.

RED, against the SHIPPED source (a245704, RouteScore.swift md5 565d52d707c1b7b5ea2abade336fd899) in an
isolated copy, with the new assertion transplanted onto it and nothing else changed:

    swift test --scratch-path .build-b1red        Test run with 35 tests in 5 suites FAILED   exit 1
      episodes lost to re-splitting: junction k=6, 7, 13, 14, 15, 17, 18, 21, 22, 24, 26, 27, 29, 31,
                                     34, 36, 38; endsTheRoute k=12, 14, 17, 21, 23, 26, 28, 30, 31, 34, 36
      route score moved with segmentation alone: k=12 value=0.387 ... (expected 0.4203333)

The junction list is the Brief's own case - a canyon the router returns as 400 m + 400 m - and it matches
the reviewer's list exactly. The score moves 0.420333 -> 0.387, 7.9% relative, against a 1e-9 suite
tolerance and the plan's 0.5% re-encoding pin.

GREEN: `boundaryTolerance` is now a named constant used by BOTH statistics, and
`episodeOfExactlyTheMinimumSurvivesResplitting` sweeps k = 1...40 over three fixtures - a run that ends the
route, the Brief's junction, and a run closed by a dull stretch - because the two places a run can be
closed need separate witnesses. Four harness mutations guard it (drop the tolerance / flip it to the wrong
side, at each of the two closing sites); all four are caught.

### B2, B3, B5, B6 - the reviewer's own mutations, MISSED before and caught after

Each was re-run against the pre-fix tree with the pre-fix harness, then against the fixed tree:

    B2 / N2  percentile fraction 0.90 -> 0.86        MISSED  ->  caught
    B2 / N3  percentile fraction 0.90 -> 0.89        MISSED  ->  caught
    B3 / R2  tolerance total*1e-9 -> total*0.04      MISSED  ->  caught
    B5 / R3  drop the episode cap min(1.0, ...)      MISSED  ->  caught
    B6 / N1  isHonestFailure `<` -> `<=`             MISSED  ->  caught

  * **B2** - `percentileFractionIsPinned` put its boundary at 75% of the length, pinning the fraction only
    to (0.85, 0.90]. `percentileFractionIsPinnedFromBothSides` puts it 1 m either side of 90% of a 10 km
    route: `[8999 m @ 0.1, 1001 m @ 0.9]` must give p90 = 0.9 and `[9001 m @ 0.1, 999 m @ 0.9]` must give
    p90 = 0.1, which pins it to (0.8999, 0.9001]. Both expectations are literals.
  * **B3** - the tolerance is now `RouteScore.boundaryTolerance`, named and pinned, and the same fixture
    holds its SIZE below 1e-4 of route length by behaviour rather than by the constant alone.
  * **B5** - `episodeTermSaturatesAtTheTarget` uses 3 episodes (value 0.613) and 8 episodes (value 0.571,
    which without the cap is 0.737667). Both literals worked by hand.
  * **B6** - `honestFailureIsStrictAtItsThreshold` needed a route whose value is EXACTLY 0.45, which no
    fixture had. `[1024 m @ 0.51, 1024 m @ 0.54]`: no duds, no episodes, mean 0.525, p90 0.54, and
    0.60*0.525 + 0.25*0.54 = 0.315 + 0.135 = 0.45 to the last bit. The test asserts the fixture lands on
    the threshold before asserting the strictness, so it cannot go vacuous.

### B4 - the claim was inverted, and the reason is worse than the reviewer could see

R7 said "Either half of the fix suffices on its own" and the reviewer measured the opposite. Measuring the
other half explains why: **`sorted.reduce { $0 + $1.length }` and the loop's own `cumulative` are the same
left fold over the same sequence in the same order, so the two totals are bit-identical for every input** -
worst difference over the reviewer's fixture at k = 1...400, exactly 0.0. The separate reduce was never a
defect and was never part of the fix; the tolerance is the whole fix (with it, 0 of 400 splits flip; without
it, 180 of 400, with or without the separate reduce).

Three consequences, all applied: the false mechanism is corrected in the source comment, in
`percentileIsStableOnTheBoundary`'s comment and here; the two mutations that claimed to be halves are now
ONE mutation named for what it is ("restore the shipped bug: drop the percentile boundary tolerance"); and
the equivalence is no longer a claim - "take the percentile total from a separate reduce, as the shipped
code did" is an EQUIVALENT mutant that the harness requires to go MISSED, so if it ever starts being caught
the run fails and someone finds out.

### B7 - the test's name asserted the opposite of what its fixture does. Renamed and pinned, NOT retuned

`motorwayIsADud` was titled "...without disqualifying the route" and asserted only `value > 0`, while the
fixture's actual verdict is `isHonestFailure == true` (0.320162 against 0.45). Renamed to
`motorwayScoresAsADudAndIsAnHonestFailure`, and the verdict is now asserted rather than left implicit.

**I did not move 0.45.** The CLAUDE.md invariant is that motorway is penalised and not excluded, and that
holds: the route scores, keeps its episode, and is returned - `isHonestFailure` is a presentation signal,
not exclusion. Whether a route that is 51% motorway by length should be shown or refused is a tuning
question that needs the router and a real corpus, and retuning a constant so a fixture reads better is
exactly how a threshold gets laundered. The constant now documents its own provenance (the plan does not
specify it, the formula's ceiling is 0.95, this fixture scores 0.320162) and names the assertion that has
to move with it if it is ever recalibrated.

### B8 and B9 - the shared harness defect, demonstrated rather than argued

Both were reproduced red on the old logic and green on the new, in isolated copies:

    B8  every anchor replaced by a string absent from the source, --prove-vacuity
          OLD  caught 0, MISSED 21 of 21   VACUITY PROOF OK       exit 0   <- the defect
          NEW  caught 0, skipped 29 of 29  VACUITY PROOF FAILED   exit 1
    B9  the harness's own FAIL_LINE regex broken, three real mutations that DO fail a named test
          OLD  caught 0, trapped 3                                exit 0   <- the defect
          NEW  caught 0 of 3                                      exit 1

B9 was a code reading in the review; it is a measurement now. The harness is rebuilt on the corrected
reference (ops/mutate/guidance.py on task/T-0129): the pass condition is `caught == len(MUTATIONS)`, a
trap / a compile failure / a stale anchor each fail the run, SKIP is its own bucket, `--prove-vacuity`
requires `caught == 0 AND missed == len(MUTATIONS)`, and the EQUIVALENT arm requires MISSED specifically.

**The score before and after, honestly:** the old harness scored 21 caught / 0 trapped / 0 compile-only /
0 MISSED, exit 0 - so on this subject the trapped-counts-as-pass rule was latent and was masking nothing.
The number did not drop when the rule was tightened. It went 21 -> 29 because eight mutations were added
for the gaps above, and one pair was merged into one for B4.

### One mutation was REMOVED, and that is a coverage change, so it is recorded

`require a run to EXCEED the episode minimum rather than reach it` (`>=` -> `>`) used to be caught. With
the tolerance present it is unobservable: at a run of exactly 800 m both `>=` and `>` clear
`800 - tolerance`. Measured, not assumed - it went MISSED at both closing sites when tried. Keeping it
would report a gap that is not one. The four new episode-tolerance mutations cover the same boundary and
more of it, and `thresholdStrictness` still pins the behaviour (800 m is an episode, 799 m is not).

### File discipline

`RouteScoreTests.swift` reached 325 lines, over the 300 cap, so the boundary tests moved to
`RouteScoreBoundaryTests.swift` (a suite per file, filename == type name): 254 and 289 lines,
`RouteScore.swift` 214. The harness's `--prove-vacuity` blanks both test files, not one.

### Not fixed, deliberately

  * **`honestFailureThreshold` = 0.45 itself** - see B7. Documented and pinned, not retuned.
  * **The unreachable fallbacks at `RouteScore.swift` lines 122 and 134** (N5). `guard total > 0` cannot
    fire (every valid edge has positive length) and the trailing `return sorted.last?.score ?? 0` cannot be
    reached for `fraction` in 0...1. Both are `return` statements the compiler requires; removing them
    needs a restructure of the function that is not a finding and would churn code under review.
  * **`min(1.0, ...)` on the clamp** is dead while the episode cap holds (raw <= 0.95). It is now an
    EQUIVALENT mutant with the proof written out, rather than an untested line pretending to be tested.
  * **F7** is fixed: `.build-*/` is in `.gitignore` (`.gitignore` added to `touches:`). Every
    `swift build/test` here must pass its own `--scratch-path`, so these directories are guaranteed to
    exist and three reviews in a row reported them as untracked.

### A defect found on the way, not fixed here

`ops/new-task --help` does not print help - it files a backlog task titled `--help`. Reproduced and the
stray file removed. `ops/lib/queue.py` is outside this task's `touches:` and T-0096 already covers that
module.

