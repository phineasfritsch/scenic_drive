---
id: T-0117
title: ScenicKit RouteScore: is this route actually pretty, length-weighted and invariant to how the router split the edges
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:54:42Z
lease_expires_at: 2026-09-08T15:54:42Z
worktree: .worktrees/T-0117
branch: task/T-0117
exclusive: []
touches: [Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/, ops/mutate/, .gitignore]
pins_affected: []
reviewer: agent/sg-pr73
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test --scratch-path <yours> -> 'Test run with 42 tests in 6 suites passed', exit 0"
  - "python ops/mutate/routescore.py -> 'caught by a named test: 36 of 36   (trapped 0, compile-only 0, MISSED 0, skipped 0)'; both EQUIVALENT mutants MISSED as required; exit 0"
  - "RED: python ops/mutate/routescore.py --prove-vacuity -> 'VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=36 of 36', exit 0"
  - "RED: the same harness with every anchor stale, population size untouched, --prove-vacuity -> 36 SKIP lines and 'VACUITY PROOF FAILED: with no tests present, caught=0 (need 0) and MISSED=0 of 36', exit 1"
  - "RED: DELETING any mutation now refuses. Removing the two restored '>=' -> '>' mutations (36 -> 34) gives 'REFUSING: 34 mutations and 2 equivalent mutants, expected at least 36 and 2.' / 'A harness that examines nothing exits 0 and proves nothing.', exit 2. At MIN_MUTATIONS = 28 that same deletion printed '29 of 29' and exited 0 - that was F1."
  - "RED: ADDING a mutation without raising the floor also refuses (36 -> 37): 'REFUSING: 37 mutations and 2 equivalent mutants against floors of 36 and 2.' / 'The floor is slack by 1 and 0, so that many could be deleted again in silence', exit 2."
  - "ops/test -> 'TESTS linux=145/76 ios=skipped failed=0 skipped=0' then 'OK', exit 0 - WHERE services/api/node_modules is present (npm ci in services/api from the committed lockfile, ~7 s). Where it is absent, main included, it exits 1 at the Worker tier with 'services/api exists but vitest produced no report' before reaching the TESTS line. Environmental, T-0040; no JS or TS in this diff."
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


---

## Sign-off pass: agent/signoff-pr73 returned FAIL, and all three blocking findings were right

A first reviewer passed this. A second, independent review failed it with three blocking findings, every one
measured with controls rather than read off the diff. All three are now closed.

- 2026-09-09T02:40:00Z **B2 was the serious one: a previously-caught mutation had been DELETED with a reason that measurement shows is false.** The harness and the Log both said the `>=` -> `>` mutation was *"unobservable: at a run of exactly 800 m both `>=` and `>` clear `800 - tolerance`"*. That sentence is true; the conclusion drawn from it is not. `>=` and `>` differ on exactly one input class - `run == episodeMinLength - tolerance` **exactly as a double** - and since `tolerance = scale * 1e-9`, a witness is a fixed point of `X == 800.0 - (X + dull) * 1e-9`. That is a one-parameter family, not one lucky value.
- 2026-09-09T02:40:00Z **I verified the reviewer's witness independently before trusting it**, in Python rather than by re-reading their report: `0x1.8ffffff94a036p+9` is `799.9999992`, and `800.0 - 799.9999992e-9` is also exactly `799.9999992`, so `>=` counts the episode and `>` drops it. Then I searched for the second site's witness myself by walking outward from the approximate root: with a 200 m dull tail, `0x1.8ffffff79c843p+9` is the exact fixed point. **Both mutations are restored and both are caught.** Written as hex float literals, because a decimal literal that round-trips on this toolchain is not guaranteed to be the same bit pattern elsewhere, and one ulp destroys the witness.
- 2026-09-09T02:40:00Z The old justification also claimed *"the four below cover the same boundary and more of it"*. They do not: all four mutate the **tolerance**, and none reaches the `>=` vs `>` comparison at the boundary itself - which is exactly why the restored pair went MISSED against a suite in which all four were caught. Deleting a previously-caught mutation with a false reason is worse than a `KNOWN_MISSED` entry with a bad reason, because nothing will ever re-check it.
- 2026-09-09T02:40:00Z **B1: the harness reported a clean sheet over nothing.** With `MUTATIONS` and `EQUIVALENT` emptied it printed `caught by a named test: 0 of 0 ... exit 0` and `VACUITY PROOF OK ... MISSED=0 of 0` - the vacuity proof certifying its own vacuity. The asymmetry is the finding: this harness already detected stale ANCHORS (31 SKIP lines, exit 1, and that is in the acceptance block), but not a deleted POPULATION - and the deleted population is what actually happened here, in B2, with nothing to say the count had fallen from 31 to 29. `MIN_MUTATIONS = 28` / `MIN_EQUIVALENT = 2` now refuse. RED: `REFUSING: 0 mutations and 2 equivalent mutants, expected at least 28 and 2. / A harness that examines nothing exits 0 and proves nothing.`, exit 2.
- 2026-09-09T02:40:00Z **The same defect was in every harness I wrote today, including the one I was holding up as the corrected reference.** `ops/mutate/gates.py` on `task/T-0133` had it, and the reviewer said so explicitly - *"the reference is not a defence for it"*. Floors added to `gates.py`, `segmentscore.py`, `guidance.py`, `hazards.py` and `retrace.py` on their own branches.
- 2026-09-09T02:40:00Z **B3: the baseline build was not retried** while every mutation build already was, so one transient `I/O error (code: 512)` on a fresh scratch directory aborts the run with *"baseline does not build"* having measured nothing. Fixed; this is the defect filed as the second half of [[T-0132]], which landed on `main` six minutes after this branch's head and so was never inherited.
- 2026-09-09T02:40:00Z **The acceptance block was wrong in two ways and is rewritten.** Line 1 claimed `ops/test -> TESTS linux=142/76 ... exit 0`; that command exits 1 everywhere on this box at the Worker tier and never reaches the `TESTS` summary at all, so the line asserted output that cannot be produced. It is replaced by an explicit NOTE recording the environmental cause ([[T-0040]]) rather than a claim. Lines 3 and 4 said `29 of 29`; the count is now **31**, and the floor above is what makes that number mean something.
- 2026-09-09T02:40:00Z `RouteScoreBoundaryTests.swift` reached 321 lines with the witness test in it, over the 300 cap. The exact-double witnesses moved to `RouteScoreWitnessTests.swift` - they need hex float literals and a rationale of their own, so the split follows a real seam. **The harness's `TESTS` tuple was updated in the same commit**, because a suite split the vacuity proof does not know about silently stops it emptying all the tests, which has now happened five times here ([[T-0132]]).
- 2026-09-09T02:40:00Z GREEN: `swift test` -> **40 tests in 6 suites passed**. `python ops/mutate/routescore.py` -> **31 of 31 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=31 of 31`, exit 0. `bash ops/check-pins` -> `ok=11 skipped=0 pending=2 expired=0 failed=0`.
- 2026-09-09T02:40:00Z NOT CLOSED, and named rather than left implied: the reviewer's N1 (the tolerance USE SITES survive replacement by a literal down to `1e-6` on the episode site and `1e-5` on the percentile site), N2 and N3 (two arithmetic claims in comments that are wrong - 7.93% written as 9.6%, three orders of magnitude written as six), and N4 (a comment whose stated scope exceeds its assertion on long routes). N2 and N3 are comment defects in a file whose subject is checks that claim more than they cover, so they should not sit long.

---

## Fourth review pass: agent/so-pr73 returned FAIL on three blocking findings. All three are closed.

Every number below was re-measured in this worktree (`.worktrees/T-0117`, scratch `.build-T0117d`); nothing
is copied from the report. The independent Python replays are `.artifacts/t117d-measure.py` and
`t117d-band.py`, the survived/caught probes `.artifacts/t117d-probe.py`, the floor repro
`.artifacts/t117d-floor.py`, the stale-anchor run `.artifacts/t117d-stale.py`.

### F1 - the population floor did not refuse the deletion its own comment named. CLOSED.

`MIN_MUTATIONS = 28` against `len(MUTATIONS) = 31`. Reproduced first, with no tracked file edited:

    population 31 -> 29 ; MIN_MUTATIONS = 28
    BASELINE                                                              exit=0
    caught by a named test: 29 of 29   (trapped 0, compile-only 0, MISSED 0, skipped 0)
    EXIT=0        <- no REFUSING line. The exact state the sign-off round blocked on.

Three mutations of slack, and the comment above the constant presented it as the cure for precisely the
31 -> 29 deletion it does not notice. The floor is now the EXACT population, and the check is two-sided,
because a floor set below the population is how the slack got there in the first place:

    36 -> 34 (the two restored `>=` -> `>`)  REFUSING: 34 mutations ... expected at least 36 and 2.  exit 2
    36 -> 35 (any single deletion)           REFUSING: 35 mutations ... expected at least 36 and 2.  exit 2
    36 -> 37 (added, floor not raised)       REFUSING: ... The floor is slack by 1 and 0 ...          exit 2
    MUTATIONS=[] and EQUIVALENT=[]           REFUSING: 0 mutations ... exits 0 and proves nothing.    exit 2

Adding a mutation now costs one more edited line in the same commit. That is the price of the acceptance
line's "36 of 36" meaning anything.

### F2 - the twin of the restored comparison was uncovered. CLOSED, with a mutation and a witness.

`for (i, c) in running.enumerated() where c >= target - tolerance` is the same `>=`-against-a-tolerated-
boundary comparison as the two episode closing sites this commit exists to re-pin. SURVIVED, measured
against the shipped source before any fix:

    PROBE F2: percentile boundary: `>=` -> `>`
      swift test exit=0   Test run with 40 tests in 6 suites passed
      SURVIVED: no named test recorded an issue

**The witness was not placed by computing anything from RouteScore.** `>=` and `>` differ only where
`c == target - tolerance` exactly as a double; with a 1000 m high edge that is a fixed point of
`a == (a + 1000)*0.9 - (a + 1000)*1e-9`. I solved it in Python by walking outward from the algebraic root
with `nextafter` and comparing bit patterns - and the measurement corrected my own first design, which is
worth recording because it is this session's signature defect in miniature: I had assumed the solution was
a single double and that one ulp below it would land on the other side. **It is a BAND of ten consecutive
doubles** (`0x1.193fffcb923a1p+13` ... `0x1.193fffcb923aap+13`), because the bound is flat under rounding
across them - so "one ulp below" is still inside the band and would have asserted nothing. The fixture sits
FIVE ulps into the band, five from either edge.

    @Test("the percentile boundary landing exactly on the tolerated bound takes the lower score")

    [0x1.193fffcb923a6p+13 @0.1, 1000 @0.9] -> p90 == 0.1   (mutant returns 0.9)
    [0x1.193fffcb92399p+13 @0.1, 1000 @0.9] -> p90 == 0.9   (eight ulps below the band)

Both expected values are the fixtures' own literal scores, not anything the function computed. RED then
green, by failing test NAME:

    PROBE F2 after   swift test exit=1   Test run with 42 tests in 6 suites failed ... with 1 issue
      CAUGHT by 1 named test: "the percentile boundary landing exactly on the tolerated bound takes the
      lower score"

### F3 - the restored-mutation comment was false by measurement. CORRECTED.

It gave the witness condition as the fixed point `X == 800.0 - X * 1e-9` and then claimed
`0x1.8ffffff94a036p+9` discriminates "at BOTH closing sites". Measured on the suite's own shape:

    [0x1.8ffffff94a036p+9 @0.9, 200 @0.1]   scale 999.9999992, bound 799.999999
    episodes(>=) = 1  AND  episodes(>) = 1          <- no discrimination at the in-loop site at all

Reaching the in-loop site requires a following edge with positive length, so `scale > X`, so the bound
falls BELOW X and `>` is satisfied too. The in-loop condition is `X == 800.0 - (X + dull) * 1e-9`, which is
why the test beside it always needed the other constant (`0x1.8ffffff79c843p+9`) and always stated the
equation correctly. Only the harness prose was wrong; it now states both sites separately, with the
measurement of the false claim written next to it.

### N1 - the same defect INSIDE the fix written to close the last round. CLOSED.

`RouteScoreWitnessTests` said "one ulp below it is NOT an episode, so this test pins the comparison" and
then asserted `episodes([ScoredEdge(length: 700.0, score: 0.9)]) == 0` - 100 m below the boundary, eleven
orders of magnitude out. The property was true and nothing checked it. The assertion is now the real one,
`0x1.8ffffff94a035p+9` (799.9999991999999, exactly one ulp below the at-end witness, gap
1.1368683772161603e-13 m), in a test of its own. The coarse case is not lost: `thresholdStrictness`
already pins 799 m at zero.

### N2 and N3 - the tolerance USE SITES, disclosed-and-unclosed for two rounds. CLOSED.

The constant was pinned; the two multiplications that apply it were not. All three survived the suite:

    percentile tolerance made ABSOLUTE (N3)          SURVIVED -> caught by the F2 witness
    percentile tolerance inlined at total*1e-5 (N2)  SURVIVED -> caught by the F2 far-side fixture
    episode tolerance inlined at scale*1e-6  (N2)    SURVIVED -> caught by the one-ulp-below fixture

This is why the two fixtures at each site STRADDLE the boundary rather than sitting on it. Measured flip
points: the episode pair refuses any tolerance constant at or above `1.0000000837403711e-09`, the
percentile pair any at or above `1.0000001666368189e-09`. Five mutations added, 31 -> 36, all five caught:

    caught      require the percentile boundary to be EXCEEDED rather than reached            exit=1
    caught      inline the percentile tolerance use site at 1e-5 of route length              exit=1
    caught      make the percentile tolerance absolute instead of relative to route length    exit=1
    caught      inline the episode tolerance use site at 1e-6 of route length                 exit=1
    caught      make the episode tolerance absolute instead of relative to route length       exit=1

### N4 - two arithmetic claims in comments that are wrong. CORRECTED, both divided rather than believed.

    RouteScoreBoundaryTests "a 9.6% relative move"  -> 0.420333 -> 0.387 is 7.930214%. 9.6% belongs to the
                                                       OTHER fixture [800 @0.9, 2000 @0.1] (0.348333 ->
                                                       0.315 = 9.569%), quoted correctly in `episodes`.
    RouteScore.episodes "six orders of magnitude"   -> 1 mm against 1 m is three. The conclusion survives;
                                                       only the number was wrong.

### Harness rules, each re-checked rather than inherited

  * **Floor vs real population**: was 28 vs 31, now 36 vs 36, two-sided. Demonstrated red four ways above.
  * **Baseline build retried**: `if build() != 0 and build() != 0` is present at BOTH sites
    (`routescore.py:340` mutation, `:389` baseline). Unchanged by this pass; verified by grep, not assumed.
  * **`--prove-vacuity` empties EVERY file that could catch a mutation**: `TESTS` carries all three
    RouteScore files, and `grep -l 'RouteScore\|ScoredEdge'` over the other four files in
    `Tests/ScenicKitTests/` returns nothing, so there is no fourth file to miss. The run returns
    `caught=0 (need 0) and MISSED=36 of 36`, exit 0 - and completeness is self-proving here, because a file
    left un-emptied would show up as a catch or a non-MISSED. The two tests added this pass went into
    `RouteScoreWitnessTests.swift`, already in `TESTS`, so no new drift.
  * **The EQUIVALENT arm requires MISSED specifically**: with every anchor stale the two equivalents SKIP
    rather than MISS and the run prints `EQUIVALENT ARM FAILED: 0 of 2 went MISSED as required`, exit 1.
  * **SKIP is its own bucket**: 36 SKIP, `caught ... (trapped 0, compile-only 0, MISSED 0, skipped 36)`.

### Demo discipline

Every probe mutates a tracked file and restores it. The restore is verified by hashing the bytes and
comparing - `git rev-parse HEAD:<path>` for the before-runs, the captured pre-run blob for the after-runs -
not by trusting a `finally`. All eight probe runs reported `restored=True`, and `git status --porcelain`
after every run shows only the four files this pass intends to change.

### Found, NOT fixed, and out of scope by this repository's own rules

`pins/floor_linux.txt` is **76** against a real `ops/test` count of **145** - 69 of slack, the exact F1
shape one level up: 69 linux tests could be deleted with `ops/test` still green. I did not touch it. It is
a serial-only file (CLAUDE.md) that this task does not hold `exclusive:` on, it is outside this task's
`touches:`, and `ops/test` says floors "are ratcheted UP by a reviewer only". It needs its own task.

Also named rather than implied: the acceptance NOTE about `ops/test` is now **conditional**, because the
old one does not reproduce. `services/api/node_modules` is PRESENT in this worktree and absent on main, so
the command exits 0 here with `TESTS linux=145/76 ios=skipped failed=0 skipped=0` and exits 1 only where
that directory is missing. The previous line claimed it "exits 1 everywhere"; that is not true on this box,
and it is the third round in a row an acceptance line has been wrong about this command.

### GREEN

    swift test --scratch-path .build-T0117d          Test run with 42 tests in 6 suites passed      exit 0
    python ops/mutate/routescore.py                  caught by a named test: 36 of 36               exit 0
                                                     (trapped 0, compile-only 0, MISSED 0, skipped 0)
                                                     both EQUIVALENT mutants MISSED
    python ops/mutate/routescore.py --prove-vacuity  caught=0 (need 0) and MISSED=36 of 36          exit 0
    bash ops/test                                    TESTS linux=145/76 ios=skipped failed=0        exit 0
    bash ops/check-pins                              PINS ok=11 pending=2 expired=0 failed=0        exit 0
    bash ops/check-pins --source-only                PINS ok=4 skipped=9 pending=0 failed=0         exit 0
    bash ops/queue-check                             QUEUE OK (107 tasks)                           exit 0

---

## Sign-off: agent/sg-pr73 returned PASS. Nothing blocking survived.

Reviewed from two detached worktrees of my own (`.worktrees/rvw-pr73`, `.worktrees/rvw-pr73b`), each with
its own `--scratch-path`. Every subject was extracted with `git show HEAD:<path>` rather than copied from a
working tree, and hashed against the HEAD blob before AND after every run that mutates a file; both
worktrees end with `git status --porcelain` empty.

### The acceptance block reproduces character for character, all seven lines

    swift test --scratch-path .build-rvwpr73      Test run with 42 tests in 6 suites passed         exit 0
    python ops/mutate/routescore.py               caught by a named test: 36 of 36
                                                  (trapped 0, compile-only 0, MISSED 0, skipped 0)
                                                  both EQUIVALENT mutants MISSED                    exit 0
    python ops/mutate/routescore.py --prove-vacuity
                                                  VACUITY PROOF OK: with no tests present,
                                                  caught=0 (need 0) and MISSED=36 of 36             exit 0
    every anchor stale, --prove-vacuity           36 SKIP lines, VACUITY PROOF FAILED: ...
                                                  caught=0 (need 0) and MISSED=0 of 36              exit 1
    36 -> 34 (the two restored `>=` -> `>`)       REFUSING: 34 mutations and 2 equivalent mutants,
                                                  expected at least 36 and 2.                       exit 2
    36 -> 37 (added, floor not raised)            REFUSING: 37 ... against floors of 36 and 2.
                                                  The floor is slack by 1 and 0 ...                 exit 2
    bash ops/test                                 FAIL: services/api exists but vitest produced
                                                  no report                                         exit 1
    npm ci in services/api, then bash ops/test    TESTS linux=145/76 ios=skipped failed=0 skipped=0
                                                  OK                                                exit 0

BOTH branches of the conditional `ops/test` line were run, not just the one this box happens to be in:
`services/api/node_modules` was absent (exit 1 at the Worker tier, T-0040, nothing to do with this diff),
and after `npm ci` from the committed lockfile the same command prints the claimed line and exits 0. Also
`check-pins` ok=11 pending=2 failed=0, `--source-only` ok=4 skipped=9, `queue-check` QUEUE OK (107 tasks).

### The two-sided floor refuses in BOTH directions, and on EQUIVALENT too

By importing `ops/mutate/routescore.py` by path and overriding the population in memory - the tracked file
was never edited. Six cases, all before any build, all exit 2: `MUTATIONS=[]` and `EQUIVALENT=[]` (both with
and without `--prove-vacuity`); 36 -> 35; 36 -> 34; 36 -> 37; EQUIVALENT 2 -> 1 and 2 -> 3. The floor
predecessor was confirmed rather than believed: `git show 645fcef:ops/mutate/routescore.py` has
`MIN_MUTATIONS = 28` and a one-sided `len(MUTATIONS) < MIN_MUTATIONS`, which is the F1 state exactly.

### The hex-float witnesses are exact fixed points, verified in Python from the equation, not from the report

    at-end   X = 0x1.8ffffff94a036p+9 = 799.9999992   scale = X
             800.0 - X*1e-9 == X  -> True   episodes(>=) = 1, episodes(>) = 0
    in-loop  X = 0x1.8ffffff79c843p+9 = 799.999999    scale = X + 200 = 999.999999
             800.0 - (X+200)*1e-9 == X -> True   episodes(>=) = 1, episodes(>) = 0

Each is the ONLY double satisfying its own equation (walked outward with `nextafter`: band size 1 at both
sites), so one ulp either way destroys the witness and the hex literals are load-bearing. F3's correction is
confirmed independently: the at-end constant does NOT discriminate at the in-loop site - on
`[0x1.8ffffff94a036p+9 @0.9, 200 @0.1]` both operators give 1. The one-ulp-below fixture
`0x1.8ffffff94a035p+9` is exactly one ulp below (gap 1.1368683772161603e-13) and is not an episode. The
percentile witness `0x1.193fffcb923a6p+13` sits inside a band of exactly ten consecutive doubles
`0x1.193fffcb923a1p+13 ... 0x1.193fffcb923aap+13`, five ulps above the low edge, and the far-side fixture is
eight ulps below the band - all as stated.

### Every previously claimed fix was re-broken and read back BY FAILING TEST NAME

The harness reports "caught" without naming the test, so all eight were re-run against the shipped source:

    `>=` -> `>` in-loop          <- "a run landing exactly on the tolerated boundary is an episode, at
    `>=` -> `>` at-end              both closing sites"
    percentile `>=` -> `>`       <- "the percentile boundary landing exactly on the tolerated bound takes
    percentile tolerance -> 0       the lower score" (+ "...stable under re-splitting", 29 issues)
    episode tolerance 1e-6       <- "a run one ulp short of the tolerated boundary is not an episode"
    episode tolerance absolute   <- "a run landing exactly on the tolerated boundary is an episode, ..."
    percentile tolerance 1e-5    <- "the percentile boundary landing exactly on the tolerated bound ..."
    percentile tolerance abs.    <- "the percentile boundary landing exactly on the tolerated bound ..."

Both declared EQUIVALENT mutants genuinely survive with no named test objecting, as the arm requires.

### Fifteen mutations nobody wrote, against the shipped source: fourteen caught, one survivor

Caught, each with the failing test named: doubling either tolerance; sorting the percentile by LENGTH;
never resetting `run`; swapping the mean and p90 weights at the USE SITE; taking the episode scale over the
pretty edges only; making the episode bound relative to 800 m instead of to the route; scaling the
percentile bound instead of subtracting the tolerance; HARD-EXCLUDING motorway (the CLAUDE.md invariant,
caught by `motorwayScoresAsADudAndIsAnHonestFailure` among five others); counting at most one episode;
removing the clamp floor; taking p90 unsorted; and two in `ScoredEdge`, which the harness does not mutate
at all - a score of exactly 0 becoming invalid, and scores above 1 being accepted.

### The harness was attacked and refused every time

`FAIL_LINE` broken with the subject pristine -> 36 trapped, caught 0, exit 1. `FAIL_LINE` made to match
everything -> 36 of 36 "caught" but the EQUIVALENT arm fails it, exit 1. Every anchor stale -> 36 SKIP,
exit 1 in both modes. Every mutation a no-op -> "mutation did not land", exit 1. Baseline build failing once
then succeeding -> proceeds (`routescore.py:389`, matching the per-mutation retry at `:340`); failing twice
-> "baseline does not build", exit 2. A subject left MUTATED on disk -> baseline red, exit 2, nothing
measured. `--prove-vacuity` completeness re-derived rather than taken on trust: `grep -rl` over every
`.swift` file in the repo returns exactly the two sources and the three test files already in `TESTS`, and
there is only one test target.

### NOT BLOCKING, recorded so it is not lost

  * **One surviving mutation, with a control.** Removing `total.isFinite` from
    `RouteScore.swift:101` survives all 42 tests. It is not equivalent: on
    `[.greatestFiniteMagnitude @0.5, .greatestFiniteMagnitude @0.5]` - two individually VALID edges - the
    shipped code returns nil and the mutant returns
    `RouteScore(value: 0.225, mean: 0.0, p90: 0.5, dudFraction: 0.0, episodeCount: 3, totalLength: inf)`,
    three phantom episodes and all. Control: an untracked test asserting that route is nil passed on the
    pristine tree (43 tests in 7 suites) and failed by name under the mutation; it was then deleted. Not a
    blocker - a path-detail interval cannot reach 1e308 m - but it belongs with the unreachable fallbacks
    already disclosed under "Not fixed, deliberately" at `RouteScore.swift:122`/`:134`, and it is the one
    guard in the file with no coverage and no disclosure.
  * `routescore.py:380` still says "**both** test files are replaced by empty suites"; `TESTS` has carried
    three since the witness suite was split out. The code is right and the banner under-claims.
  * `RouteScoreWitnessTests.swift:81` "five from either edge" is five ulps from the low edge and four from
    the high (band `...a1` to `...aa`, fixture `...a6`). The conclusion it supports - not one ulp from
    flipping either way - holds.
  * The two measured flip points quoted at `RouteScoreWitnessTests.swift:61` and `:90`
    (1.0000000837403711e-09 and 1.0000001666368189e-09) are looser than the real ones I measured
    (1.0000000126860977e-09 and 1.000000075687348e-09, each exact: it flips at t and not at t-1ulp). The
    statements stay TRUE - the fixtures refuse strictly more than claimed - and the 1e-6/1e-5/1e-8
    conclusions were confirmed by running those mutations.
  * PR #73's GitHub description still reads "swift test -> 29 tests in 4 suites" and
    "`.artifacts/mutate-T0117.py` -> 8 of 8 mutations caught" against a shipped 42 tests in 6 suites and
    `ops/mutate/routescore.py` with 36. Worth correcting before merge, but not a blocker and not a
    regression: PR #70, already on main, carries the identical stale shape.
  * `pins/floor_linux.txt` is 76 against a real 145, exactly as this task already recorded. Out of scope
    here (serial-only file, no `exclusive:` held) and it needs its own task.
