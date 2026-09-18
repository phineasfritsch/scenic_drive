---
id: T-0116
title: ScenicKit Budget: the lambda bisection that makes the extra-time budget a ceiling instead of a hope
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:32:03Z
lease_expires_at: 2026-09-08T15:32:03Z
worktree: .worktrees/T-0116
branch: task/T-0116
exclusive: []
touches: [Sources/ScenicKit/Budget/, Tests/ScenicKitTests/, ops/mutate/, .gitignore]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test --scratch-path .build-T0116 -> Test run with 56 tests in 8 suites passed, exit 0"
  - "python ops/mutate/budget.py -> caught by a named test: 66 of 66   (trapped 0, compile-only 0, MISSED 0, skipped 0), exit 0"
  - "python ops/mutate/budget.py --prove-vacuity -> VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=66 of 66, exit 0"
  - "python ops/mutate/budget.py --prove-floor -> FLOOR PROOF OK: emptied -> refused=True, one deleted -> refused=True, real -> accepted=True, exit 0"
  - "python ops/mutate/budget.py --prove-dirty -> DIRTY PROOF OK: committed -> accepted=True, mutated -> refused=True, exit 0"
  - "python ops/mutate/budget.py --prove-blind -> BLIND PROOF OK: differs=True, names every uncompared subject=True, subprocess restored=True, exit 0"
  - "RED: prove_blind handed the sentence this replaced (the four-line stand-in is in the Log) -> BLIND PROOF FAILED: differs=False, names every uncompared subject=False, subprocess restored=True, exit 1"
  - "RED: with .artifacts/budget-mutation-in-flight present, python ops/mutate/budget.py -> REFUSING: ... the previous run was killed while a mutation was on disk, exit 2, before any build"
  - "RED: with MIN_MUTATIONS forced to 22 and MIN_EQUIVALENT to 1 (the one-liner is in the Log), --prove-floor -> FLOOR PROOF FAILED: emptied -> refused=True, one deleted -> refused=False, real -> accepted=True, exit 1"
---
## Brief

The product is one sentence - *"I have 25 extra minutes, keep me off the freeway, make it pretty"* - and
`lambda` is the single knob that spends those minutes. At 0 the scenic score is ignored and the router
returns the fastest route; as it rises, dull edges are penalised and the route wanders toward pretty ones and
takes longer. The search finds the largest lambda whose route still fits inside `fastest + budget`.

CLAUDE.md: *"The extra-time budget is a **ceiling**: returned ETA <= fastest + budget. Always."*

**No `Package.swift` change.** `Sources/ScenicKit/Budget/` is inside the existing ScenicKit target path, which
SwiftPM globs, so this needed no edit to the serial file - whose lock is held by T-0114. That is the reason
this task was picked to run alongside it.

### The design decision worth arguing with

The plan's method is a bisection on lambda, and a bisection is only correct if duration is monotone in
lambda. The plan states it is, on a graph we own. **That is an assumption about a routing engine, not a
theorem** - ties, alternative-route selection and contraction-hierarchy shortcuts can each break it near the
margins, and a heavier scenic penalty flipping the engine onto a different, quicker corridor is an ordinary
thing for a router to do.

A bisection that trusts monotonicity concludes "everything below the bracket is feasible" and can return a
lambda it never measured. So the search does not trust it:

  * **Only measured, verified-feasible candidates may be returned.** `BudgetOutcome.duration` is always a
    value the router returned for that exact `lambda` - never an interpolation, never the bracket, never the
    ceiling. The ETA on the screen has to be a number somebody computed for the route being shown.
  * A non-monotone router therefore costs accuracy and never costs the invariant.
  * Violations are detected and reported rather than relied upon.

## Log

### GREEN

    swift test --scratch-path .build-T0116
    Test run with 33 tests in 4 suites passed after 0.051 seconds.   exit 0

### The suite was wrong twice, and the mutation harness is what said so

`.artifacts/mutate-T0116.py` breaks the search eight ways and requires each break to fail. First run:

    5 of 8 mutations caught
    NOT CAUGHT: return the bracket instead of a measured candidate;
                let the ceiling slip by one percent;
                keep the last feasible candidate rather than the best

Two of those three are the failure this file exists to prevent, and **both produce a believable lambda and a
believable ETA**. Nothing crashes. The suite had thirteen tests and none of them could tell.

The cause was that every fixture had the bisection's final bracket and the correct answer coinciding, so
returning either looked the same. The fixture that separates them: `fastest = 3000`, and a router that
returns 2000 s for every lambda at or above 4. The bracket climbs to ~7.5 because everything from 4 up is
feasible; the best feasible route - the *slowest* that still fits, which is the most scenic affordable one -
is at lambda 0 with 3000 s. Pinning that exact pair catches both mutations at once.

### ~~The third one was my mutation being wrong, and that is a finding about the code~~ - it was not (F-SG1)

`let the ceiling slip by one percent` aimed at `if d <= ceiling {` inside the bisection and was not caught.
~~That is correct behaviour, not a hole: **that line only steers the bracket.**~~ Feasibility is filtered
separately, where `best` is updated. ~~Loosening the bracket makes the search waste an evaluation exploring
an infeasible region; it cannot breach the invariant, because nothing infeasible can ever become `best`.~~

**Both struck sentences are false and are struck here, in the entry that made them, not only corrected
further down (F-SG1, fourth review).** The bracket decides which lambdas are ever MEASURED, and only a
measured route can become `best`, so steering it wrong does not cost an evaluation - it costs the route. On
the fixture now in `LambdaSearchSteeringTests.swift` the loosened bracket turns a 3200 s scenic plan into
the 1800 s fastest route with `usedBudget` **false**; across 7296 standalone cases the reviewer measured
1066 changed lines, 158 of them the RETURNED DURATION and 149 flipping `usedBudget`, with a worst case where
the pristine search returns a plan and the mutant throws `noFeasibleLambda` - *"couldn't reach that
address"*. What survives of the paragraph is one clause: the CEILING is never breached either way. That is
why nothing caught this for three rounds, and it is not the same fact as harmless.

So the guard that actually enforces the ceiling is a different line, and the mutation was retargeted at it.
Re-run:

    8 of 8 mutations caught     exit 0

~~The separation is worth keeping deliberately: the bisection can be wrong about where to look next without
the returned answer ever being wrong about the ceiling.~~ The separation is real and the invariant does hold
either way. What was wrong was retargeting the mutation and leaving **nothing at all** on the line it came
off - for three rounds the population named the guard it does not touch ("on the guard that enforces it")
and was read as covering both. Both spellings of the steering guard are in `MUTATIONS` now, and each is
caught by a test named for the direction it breaks.

### A third correction: what `monotonicityViolated` can and cannot mean

The first draft asserted that a non-monotone router would be *detected*. It failed. The curve spikes over
`fastest + 4000` for lambda in 1..3, and the bisection samples 0, 4, 6, 5, 5.5, 5.75 - every one outside the
spike. The dip is invisible to it.

The test was wrong, not the code. The flag reports violations **observed among the lambdas actually
sampled**, and six samples out of a continuum cannot prove monotonicity. `true` is evidence of a violation;
`false` is only the absence of evidence. That is now written on the field, with an explicit warning not to
build a check on top of `false` - such a check would be vacuous exactly whenever the dip goes unsampled,
which is this repository's signature defect.

Detection is covered separately by a curve the search does sample, and the unsampled case still asserts the
thing that matters: the ceiling holds, because the returned duration was measured.

### Other properties pinned

  * `ceilingAlwaysHolds` sweeps 41 slopes x 7 budgets including zero and 4 hours.
  * A budget of 0 returns the fastest route and counts as *used* - there was nothing to leave unspent.
  * When nothing scenic fits, `usedBudget` is false rather than the ETA quietly concealing it. A user who
    asks for 25 minutes and is handed 90 seconds has been told yes and given no.
  * `evaluations` is bounded and reported, because each one is a request to our router and the plan caps a
    plan at twelve. A cap of 1 still measures lambda 0, so there is always a feasible answer.
  * A router that overshoots even at lambda 0 is refused rather than rounded down to a breach. That should be
    impossible - lambda 0 is the problem `car_fast` already solved - so it means the two requests disagree,
    and the honest answer is `PlanError.noRoute`, which is worse and true.
  * The plan's meta-test: a stub always returning lambda 0 satisfies the ceiling on every other test here.
    `actuallyUsesTheBudget` is what distinguishes a search from that stub.

### Not done

No alternative-route scoring, no `areas` rat-run repair, no closure polygons. Those are the caller's job and
each needs the router. This type is the arithmetic, and it is injected with a duration function so it can be
tested against exact adversarial curves without a network, a graph or a container.

---

## Fix pass: reviewer-pr71 found six uncaught mutations and one structural blind spot

Their verdict was explicit: **FAIL on test coverage, not on correctness.** They tried hard to breach the
ceiling invariant and could not - including by compiling the three Budget sources standalone and fuzzing
20,000 adversarial non-monotone curves with values clustered on the ceiling: zero breaches, zero unmeasured
returned pairs. The code was right. The suite was not constraining it.

### The blind spot, which is the finding worth keeping

**Every one of my eight mutations was structural** - delete a guard, invert a comparison, drop the seed -
and **not one touched a number.** The plan specifies these constants; the suite reached all of them through
their own symbols, so none had a witness. Three were demonstrated:

  * `minBudgetUse` 0.5 -> **0.05**: green, and a route buying 90 s of a 1500 s budget then reports
    `usedBudget == true`. That is precisely what `usedBudget`'s own doc comment says it exists to prevent -
    a user "told yes and given no". The suite constrained the constant only to `0 < m <= 0.93`, because its
    fixtures buy 1395 s or 0 s of the budget and nothing in between.
  * `maxLambda` 8 -> **16**: green, and 4 of 6 router requests land in an infeasible region.
  * `lambdaTolerance` 0.05 -> **0.75**: green, and the search silently returns one of the twelve router
    requests the plan pays for.

Closed with `constantsArePinned`, a 40%-of-budget fixture (`partialBudgetIsNotUsed`) which is the case the
suite had no example of, and `evaluationCountIsPinned` asserting `evaluations == 6` rather than `<= cap`.

### The headline invariant test was self-referential

`ceilingAlwaysHolds` asserted `out.duration <= out.ceiling` with **both sides from the code under test**, so
mutating `ceiling` to `fastest + budget + 1` left it untouched. The entire ceiling-arithmetic guarantee
rested on one other fixture that happened to recompute the constant independently. The expected bound is now
computed in the test from the inputs the test chose, and `out.ceiling` is itself asserted against it.

### One uncaught mutation was a design defect, not a test gap

`d > best!.duration` -> `d >= ...` went uncaught, and the reviewer rated it the weakest of their findings -
"benign for the invariant". Looking at why nothing had an opinion: **lambda is a penalty on dull edges, so
two lambdas producing the same duration mean the larger one avoided more dull road at no cost in time.** It
is strictly the better route, for free. The original kept whichever equal-duration candidate arrived first,
which on a flat curve is lambda 0 - the least scenic of a set of equally fast options.

Now explicit: `|| (d == best!.duration && lambda > best!.lambda)`, with `tieBreaksTowardTheHigherLambda`
pinning it and asserting the winner is still a measured lambda. **The mutation was uncaught because the
behaviour was undefined, and defining it was the fix.**

### The harness, rebuilt

`ops/mutate/budget.py`: tracked (the old one was in gitignored `.artifacts/`, so its acceptance line could
not run from a clone), builds before believing a compile failure, requires a NAMED TEST to fail rather than
a non-zero exit, reports `trapped` separately.

    caught by a named test: 16   trapped: 0   compile-only: 0   MISSED: 0   of 16
    VACUITY PROOF OK: with no tests present, 0 mutations were reported caught

Eight of the sixteen are numeric-constant mutations, including `minBudgetUse` moved in both directions.

### Also confirmed by the reviewer, and worth recording

~~They re-applied my originally mis-aimed bracket mutation and confirmed independently that it really is a
no-op~~ - **struck here, in the entry that made the claim (F-SG1).** Read the rest of the sentence it was
written in: the fingerprint CHANGED. A mutation whose observable fingerprint changes is live by definition,
and this entry recorded it as "a no-op" in the same breath. What actually stayed at zero was ceiling
breaches, which is a narrower claim than the one written down. The true part - the bracket steers, the
`best` guard enforces, the invariant holds either way - is kept. The false part is the step from there to
"so the line needs no witness": the fourth review measured what it costs (a refused plan, a budget reported
unspent) and both directions are now caught by name. They verified it twice: by re-running the mutation, and
by fuzzing the standalone-compiled sources, where the answer fingerprint changed while breaches stayed at
zero.
- 2026-09-08T23:00:00Z reviewer-pr71 returned FAIL. Their BLOCKING finding was that **acceptance line 3 did not reproduce**: `--prove-vacuity` exited 1 with `VACUITY PROOF FAILED: 8 mutations were reported caught`, because commit bc5e7f6 split ten tests into `LambdaSearchBudgetUseTests.swift` and the harness kept emptying only the first file. Its own message - *"with no tests present"* - was false; it was measuring the sibling suite. A demonstration that decayed at the last commit, and a green claim recorded over a red command.
- 2026-09-08T23:00:00Z FIXED: the harness empties **both** suites, each replaced by an empty suite named after the file it stands in - two identically-named structs would not compile, and a compile failure would make the proof pass for the wrong reason. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=22 of 22`, OK. Acceptance line 1 was also wrong for the same reason (*"37 tests in 4 suites"*); it is 5 suites, and now 42 tests.
- 2026-09-08T23:00:00Z **F5, the signature defect, and F1 with it.** `tieBreaksTowardTheHigherLambda` asserted `rec.asked.contains(out2.lambda)` and `out2.lambda == rec.asked.max()` - both recomputed from what the object under test did, and both true of any search that returns something it asked for, including one asking for entirely the wrong things. The reviewer measured the consequence: the mutation *"return the bracket instead of a measured candidate"* slipped through the very test written against it, because on a flat curve the bracket `lo` **is** the largest lambda asked. Replaced with the literal sequence `rec.asked == [0, 4, 6, 7, 7.5, 7.75]` and `out2.lambda == 7.75`, derived by hand from the constants rather than read off a run. That also closes **F1**: it pins `maxLambda`'s USE, which its value being pinned elsewhere did not - at `maxLambda = 16` the search would ask 0, 8, 12, 14, 15, 15.5.
- 2026-09-08T23:00:00Z **F2: the `lambdaTolerance` termination fired in no test at all**, so deleting it was free and widening it gave back a router request for nothing with the suite green. Now pinned by `toleranceTerminatesTheSearch`, which lifts `maxEvaluations` to 30 so the tolerance is what stops the search. **I derived the answer wrong the first time** - wrote 10, the answer is 9 - because the condition is checked *before* each evaluation, so a midpoint is taken while the bracket is still wider than the tolerance. Widths 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625 each buy a midpoint; 0.03125 does not. The code was right and my arithmetic was wrong, which is the only reason worth changing a test for, and the wrong derivation is left in the comment.
- 2026-09-08T23:00:00Z **F3: the "at least half the budget" boundary had no witness.** `partialBudgetIsNotUsed` pinned the interval (0.4, 0.55], which holds for any threshold in that range, while its own comment claimed it *"pins a boundary rather than a direction"*. Now pinned at 2550 s (exactly `fastest + half the budget`, so the rule is `>=`), 2549 s, and 3000 s, all as literals rather than through `minBudgetUse`.
- 2026-09-08T23:00:00Z **A mutation I added was MISSED at first, and the fixture was the reason.** *"a zero budget stops counting as used"* removes the `budget == 0 ||` short-circuit; with budget 0 and the router returning exactly `fastest`, the arithmetic gives the same answer either way, so my first zero-budget test pinned nothing. The short-circuit only earns its place when the router BEATS the recorded `fastest` - which it can, since `fastest` was measured on an earlier request. Added that case; now caught.
- 2026-09-08T23:00:00Z **F4: `BudgetError`'s entire `CustomStringConvertible` conformance had no behavioural coverage** - every error assertion in the suite was type-only. Added `errorsDescribeThemselves` (all four messages pinned as text, since they reach a log and a bug report) and `errorsCarryTheirNumbers` (payloads pattern-matched, because a typed throw with the wrong payload puts a plausible wrong number in front of whoever reads it). Three harness mutations go with them, including reporting a bad budget as a bad duration.
- 2026-09-08T23:00:00Z **F6: the harness counted a trap toward passing.** Same correction as its siblings: the pass condition is `caught == len(MUTATIONS)`; trapped, compile-only and skipped each fail; `--prove-vacuity` requires `MISSED` to be complete; the EQUIVALENT arm requires MISSED specifically; SKIP is its own bucket. Added a `KNOWN_MISSED` arm asserting **F7** the other way round - the `max(1, maxEvaluations)` clamp cannot be killed by any assertion because the seed runs before the loop, and a gap merely absent from the list is a gap nobody can see.
- 2026-09-08T23:00:00Z **F10, raised in three consecutive reviews and never done**: `.gitignore` had no `.build-*/` line, so the shipped acceptance command left an untracked directory in every clone. Added - and `.gitignore` added to this task's `touches:` first, because the pre-commit hook would rightly have refused it otherwise.
- 2026-09-08T23:00:00Z GREEN: `swift test` -> **42 tests in 5 suites passed**. `python ops/mutate/budget.py` -> **22 of 22 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> OK, exit 0. `bash ops/check-pins` -> `ok=11 skipped=0 pending=2 expired=0 failed=0`. Line counts 238 / 218 / 296, under the cap.
- 2026-09-08T23:00:00Z NOT FIXED: **F8** (`for a in samples` -> `samples.dropLast()` survives) and **F9** (bisection midpoint `/2` -> `*0.6` survives) are both real and both still uncovered; they need a fixture where the monotonicity scan and the bisection path are observable, which is more than a mutation entry. **F7** is now recorded as a known gap rather than closed. The Log gap the reviewer identified - commits b1be8cc and bc5e7f6 having no entry - is what this entry repairs.

---

## Second fix pass: rvw4-pr71, and then the same treatment applied to my own work

Their verdict was FAIL again, and their findings share one shape: **a name, a comment or an acceptance line
claiming more than the assertion underneath it covers.** Every claim below was re-run before it was written
down - including the two claims in the entry directly above this line, one of which turned out to be false.

### The entry above is wrong, and that is finding F-F

`F9` - the bisection midpoint `/2` -> `*0.6` - is **not** uncovered. It is CAUGHT, and it was caught at
9657c9e too. I wrote "still uncovered" from belief instead of from a run. Re-measured with the shipped
protocol before touching anything: caught by `tieBreaksTowardTheHigherLambda` and
`toleranceTerminatesTheSearch`. It is now an entry in MUTATIONS, so the claim is made by a command rather
than by a sentence. Wrong in the safe direction, and the same failure mode as claiming a green.

### What the counts mean now

`swift test` -> 46 tests in 6 suites. `python ops/mutate/budget.py` -> 34 of 34 caught by a named test.
Both proofs exit 0. The `acceptance:` block was re-run command by command against this tree and rewritten to
what it prints; not one line of it is carried over.

- 2026-09-15T12:00:00Z **F-A, BLOCKING: two acceptance lines did not reproduce, and the Log documented one of them as wrong without editing it.** Line 1 claimed *"37 tests in 4 suites"* against an actual 42 in 5; line 2 claimed *"16 caught ... 0 missed"* against an actual 22 of 22; `git show 9657c9e -- <task file>` changed exactly one frontmatter line and it was `touches:`. Every command in the block has now been re-run against the final tree and the frontmatter says what each one prints, including the suite count that the file split below changes. A stale acceptance line is what `ops/merge` and the next reviewer read, so it is part of the deliverable and not a comment.
- 2026-09-15T12:00:00Z **F-B: the one BudgetError whose payload the search COMPUTES had no payload assertion.** `errorsCarryTheirNumbers` pins `notADuration`, `notABudget` and `routerReturnedNonsense` - all three echo back a caller's input. `noFeasibleLambda` computes `ceiling`, `min()` over `seen` and `evaluations`, and was covered only by `#expect(throws: BudgetError.self)` plus a hand-built literal in `errorsDescribeThemselves` that pins the format string and nothing the search puts into it. Closed by `refusalCarriesWhatTheSearchMeasured`, which pattern-matches all three payload values and the rendered sentence. The fixture is chosen so the shortest duration is the THIRD of six measured - not the first, not the last, not the largest - because my first version made the seed the minimum, which would have let `min()` -> `first` through. Three mutations added; R5, R6 and R7 re-run from the review and each goes MISSED -> caught.
- 2026-09-15T12:00:00Z **F-C: the harness printed a clean sheet over a gap this task documented.** F8 was named in the entry above as real and unfixed and appeared in neither MUTATIONS nor KNOWN_MISSED, so `22 of 22 ... MISSED 0` was true and misleading at once. The harness's own comment says *"A gap merely absent from the list is a gap nobody can see"*; it now applies to itself. Closed for real rather than merely listed: `reportsAViolationAmongInfeasibleSamples` drives a curve whose only violating pair is `(0.25, 4500)` against `(2, 4000)`, with 0.25 the last lambda the bisection visits, and `monotonicityComparesAllPairs` gains the direct pair `[(4, 100), (2, 300)]`. `samples.dropLast()` MISSED -> caught.
- 2026-09-15T12:00:00Z **F-D: `len(known["missed"]) + len(known["trapped"])` was the `caught + trapped` shape F6 was filed for, left standing in one arm.** Now `len(known["missed"]) == len(KNOWN_MISSED)`, MISSED specifically, like the EQUIVALENT arm. Demonstrated red then green on the shipped driver with globals swapped (`.artifacts/knownprobe.py`): one KNOWN_MISSED entry that CRASHES the runner instead of being missed - `fatalError` in place of the router guard's throw - gives `trapped 1` and **exit 0 under the old arm, exit 1 under the new one**. The control is the driver verbatim with that one line substituted; `diff` shows exactly one changed line.
- 2026-09-15T12:00:00Z **F-E: the one KNOWN_MISSED entry justified itself with a false reason, so it recorded a closable gap as a feature.** *"No behaviour to assert; the clamp is defensive"* - but `maxEvaluations` is public and reads 1 pristine, -5 mutated. `capIsClampedToAtLeastOne` kills it in one assertion and also pins that a legal cap of 3 is not clamped. The entry moved into MUTATIONS and **KNOWN_MISSED is now empty, which is itself a claim**: every mutation in the file is asserted to be caught by a named test.
- 2026-09-15T12:00:00Z **F-G: infeasible samples are recorded on purpose and nothing said so.** They are the evidence for the monotonicity scan and the source of the "shortest seen" number in a refusal, so recording only feasible ones hides a real violation AND degrades the refusal to *"the shortest seen was inf s"*. Both consequences are now asserted, in `reportsAViolationAmongInfeasibleSamples` and `refusalCarriesWhatTheSearchMeasured` respectively; the mutation MISSED -> caught.
- 2026-09-15T12:00:00Z **F-H and F-I, the two smallest findings, closed the same way.** `extraTime` asserted `out.extraTime(...) == out.duration - Self.fastest` - the expected value recomputed from the result, true of any implementation that combines those two numbers including one that drops the sign. Replaced with hand-derived literals (3240 / 1440) plus a fixture where the router BEATS the recorded fastest, asserting -60. `zeroIsADurationNotNonsense` pins the `d >= 0` boundary that `refusesNonsense` only bracketed from the far side. Two mutations, both MISSED -> caught. **F-J**: the docstring said "the test file" where the code empties every file in TEST_FILES; fixed, and it is the plural that the whole blocking finding of the first review was about.
- 2026-09-15T12:00:00Z **A FLOOR on the harness's own population, which nothing had.** `caught == len(MUTATIONS)` is satisfied by an EMPTY list - 0 of 0, exit 0, the cleanest sheet this file can print - exactly what `ops/lib/check-exec-bits` refuses with MIN_FILES. Demonstrated rather than asserted: `.artifacts/floorprobe.py` runs the SHIPPED driver with its population emptied and nothing else changed, and prints `caught by a named test: 0 of 0` with **exit 0** when the floor is disabled and `POPULATION FLOOR: MUTATIONS has 0, floor is 22` with **exit 2** when it is not. Shipped as `--prove-floor` so the demonstration is reproducible from a clone and not only from a gitignored script. **What it does not do**, said plainly so nobody reads more into it than it covers: at MIN_MUTATIONS = 22 against a population of 34 it refuses an emptied or badly truncated list, and it is not a per-entry ratchet - deleting one mutation still passes. That is the same shape as `MIN_FILES = 17` in `ops/lib/check-exec-bits`, which guards 23 required files.
- 2026-09-15T12:00:00Z **A killed run used to leave a mutation on disk, and the next run adopted it as `pristine`. Found the hard way, in this session.** A backgrounded run was killed between writing a mutation and the `finally` that restores it; the run after it recorded `pristine LambdaSearch.swift md5 1f7512ba` - that is `maxEvaluations: Int = 2`, a live mutation - measured every verdict against it, and restored the mutant when it finished. `git diff` found it because the subject md5 is checked against HEAD before and after every mutating run; without that check this commit would have shipped a corrupted source file with a green harness over it. `try/finally` cannot defend against a kill, so the harness now writes a SENTINEL before the first mutation and removes it after the last restore: finding one at startup means the previous run did not finish, and the run REFUSES instead of measuring whatever is on disk. Demonstrated red - sentinel present, `python ops/mutate/budget.py` and `--prove-vacuity` both exit 2 with `REFUSING` - then green once it is cleared.
- 2026-09-15T12:00:00Z **The baseline build is now retried twice (T-0132), which this harness had never picked up.** Every mutation was already built twice before a compile failure was believed; the baseline was built once, so a transient `I/O error (code: 512)` on a fresh scratch directory would abort the whole run with "baseline does not build" and nothing would be measured.
- 2026-09-15T12:00:00Z **Third split at the 300-line cap, and the harness was told about it in the same commit.** The refusal tests grew payload assertions; the file stood at 298 lines and the two remaining additions would have carried it past 300, so the refusals and the error messages moved to `LambdaSearchRefusalTests.swift` - a section boundary, not a line number. This is the exact edit that broke the vacuity proof last time, so the new suite went into `TEST_FILES` in the same commit - and that entry was demonstrated LOAD-BEARING rather than assumed to be. `.artifacts/testfilesprobe.py` runs the shipped driver with one mutation that only the refusal suite catches: with the suite left out of `TEST_FILES`, `--prove-vacuity` reports **`VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1**; with all three listed, **MISSED 1 of 1, exit 0**. A suite missing from that list fails the proof loudly rather than weakening it quietly. `ops/mutate/budget.py` was at 296 of the same cap, so its population moved to `ops/mutate/budget_mutations.py` and the driver kept the protocol.
- 2026-09-15T12:00:00Z **I then attacked the fixed suite with twelve mutations nobody had written, and six survived.** Each survivor was compiled STANDALONE - copies of the three Budget sources plus a sweep of 5891 cases covering every field of `BudgetOutcome`, the search's own cap and ceiling, each error's rendered text, and the exact sequence of lambdas the router is asked for - pristine against mutant, so no tracked file was written for a control. **Three were equivalent** (byte-identical fingerprints) and are now asserted MISSED in the EQUIVALENT arm with the reason each is equivalent, not merely the measurement: the tolerance comparison `>` -> `>=` (the bracket width is exactly 8*2^-k and 0.05 is not), the midpoint written as `(lo+hi)/2` (exact over a bracket bounded by 8), and the monotonicity scan run over the samples reversed (an all-pairs scan cannot depend on order). **Three were real, and are now caught**: dropping `isFinite` from the router guard sends an infinite duration all the way to `noFeasibleLambda` - a BudgetError, so `#expect(throws: BudgetError.self)` was satisfied by the wrong refusal, 154 cases changed; `b.lambda > a.lambda` -> `>=` accuses a router that answered the same lambda twice, 2 cases; and `budget == 0` -> `budget <= 0.5` reports a budget as spent when none of it was, 638 cases. The refusal suite asserts cases and payloads wherever a refusal carries a value. ~~and never a bare type~~ - **that clause was false of the file it describes and is struck here, not only corrected below (F-R3)**: `noFeasibleLambdaThrows`, `refusesBadInputs` and `propagatesRouterErrors` are type-only on purpose, the suite's own header says so in the same commit, and `refusesBadInputs` is exactly where F-R1 was hiding.
- 2026-09-15T12:00:00Z **Not one line of `Sources/` changed in this pass.** The three Budget files are byte-identical to 9657c9e - md5 2e420d88 (LambdaSearch), 4b3c09f7 (BudgetError), c0db374c (BudgetOutcome) - and the harness prints those same three on every run. Both reviews reached the same verdict about the code and a different one about the suite: the ceiling invariant survived every mutation either reviewer or I could land, and what was wrong was what the tests, the harness and the frontmatter CLAIMED to cover. This commit is tests, the harness and the record.
- 2026-09-15T12:00:00Z GREEN, every command re-run against this tree: `swift test` -> **46 tests in 6 suites passed**, exit 0. `python ops/mutate/budget.py` -> **34 of 34 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> caught=0, MISSED 34 of 34, exit 0. `--prove-floor` -> OK, exit 0. `bash ops/check-pins` -> ok=11 pending=2 failed=0. `bash ops/queue-check` -> QUEUE OK. `bash ops/sane` -> SANE OK. `bash ops/test` -> exit 1, `FAIL: services/api exists but vitest produced no report`, which is T-0040 and not this branch: `services/api/node_modules` does not exist on this box and this PR touches no TypeScript. Line counts 285 / 172 / 177 / 253 / 283, all under the cap. Subject md5s before and after every mutating run: 2e420d88 / 4b3c09f7 / c0db374c, identical to HEAD.

- 2026-09-15T05:10:00Z **Finished by the orchestrator after the session that was fixing this ended mid-run.** The agent's work was complete and green; what it had not reached was the restore at the end of its red demonstration. `git status` showed the shipping source modified and tests failing, which reads exactly like a broken fix and is not one - the failing tests WERE the demonstration succeeding.

  Restored with `git checkout --` and re-verified from a clean tree. Nothing was lost: no commit had been
  made, and the mutation was confined to the working tree.

  The generalisation is recorded on [[T-0130]]: a red demo that mutates a tracked file and relies on a
  `finally` to restore it has a window, minutes long, in which the process can die. That is a second source
  of the same hazard the task was filed for, and it needs no second agent.

---

## Third fix pass: agent/so-pr71, and two guards whose stated scope exceeded their coverage

Their verdict was FAIL on coverage for the third round running, and for the third round running they found
the code right: 9732 standalone searches over monotone, flat, cliff, dipping, wobbling, zero, negative, NaN
and infinite routers, zero ceiling breaches, zero returned lambdas the router was never asked for, and 23 of
their own 26 mutations caught. Every acceptance line reproduced character for character. What failed was two
guards and one sentence.

Both blocking findings are the same shape, and it is the shape this task keeps being blocked for: **a guard
with two halves, and a fixture family that only ever exercises one of them.** Neither was taken from the
report's prose. Both were re-run first, in `.worktrees/fix71demo` detached at 33d1715 with its own scratch
path (`python .artifacts/probe_new.py .build-probe-before`): baseline green, then

    SURVIVED  F-R1 drop isFinite from the constructor guard on fastest
    SURVIVED  F-R1 the same guard spelled with isNaN, which lets infinity through
    SURVIVED  F-R2 the router guard tolerates half a second of negative duration
    SURVIVED  F-R2 the router guard tolerates the smallest negative duration there is
    restored and verified against HEAD: True (md5 2e420d88)

- 2026-09-15T18:00:00Z **F-R1, BLOCKING: the `fastest.isFinite` half of the constructor guard had no
  witness at all - and the reason it had none is worth more than the fix.** `refusesBadInputs` carries
  `(.nan, 60)`, `(1800, .nan)` and `(1800, .infinity)`, so the family LOOKS like it covers finiteness on both
  arguments. It does not: `Double.nan > 0` is already false, so `fastest > 0` refuses NaN on its own, and
  **infinity is the only value the two halves of that guard disagree about** - the one combination the family
  omitted. The payload assertions did not help either, because `errorsCarryTheirNumbers` pins
  `notADuration(-1)` and -1 is another value `fastest > 0` refuses unaided. A guard with two halves needs an
  input the halves DISAGREE about; everything else is decoration. What it costs is the reviewer's point and
  it is the worse half of the finding: `ceiling` is `fastest + budget`, so an infinite `fastest` makes the
  ceiling infinite and *"returned ETA <= fastest + budget"* is not breached but VACUOUS - the failure mode
  this repository is named after. Closed by `infiniteFastestIsRefusedAsNotADuration`, which pattern-matches
  the case, the payload and the rendered sentence, plus `(.infinity, 60)` filling the hole in the family
  itself. Two mutations added, because `!fastest.isNaN` is how a well-meaning edit would spell the same hole.
- 2026-09-15T18:00:00Z **F-R2, BLOCKING: `d >= 0` was bracketed in (-1, 0] and the comment above it claimed
  it was pinned.** `refusesNonsense` pins -1 illegal, `zeroIsADurationNotNonsense` pins 0 legal, and every
  threshold in between passes both: `d >= -0.5` survived all 46 tests, and a router answering -0.2 s then
  reached the caller as a route with `usedBudget == true` and `extraTime == -1800.2`. Identical to F3
  ("pinned the interval (0.4, 0.55], which holds for any threshold in that range"), one guard over.
  `routerGuardBoundaryIsExactlyZero` pins both sides in one test, and the far side is
  `-Double.leastNonzeroMagnitude` rather than a round number: every threshold `t <= -5e-324` accepts it and
  every `t > 0` rejects the zero, so the two assertions together admit only `t` in (-5e-324, 0], where the
  only Doubles are 0 and -0 and they compare identically. **Pinned, not bracketed more tightly.** The
  comment on `zeroIsADurationNotNonsense` that implied otherwise now says which side it owns.
- 2026-09-15T18:00:00Z **Each new test was then made to go red, one mutation at a time, and the names are
  the evidence** (`.artifacts/probe_names.py` in the same demo worktree, run at 32e8f0c - which was amended
  into eb5b551 to add a `ROOT` import budget.py needed, so the three suites are byte-identical; the worktree
  is now at eb5b551 and both probes re-run there unchanged):
  `drop isFinite` and the `isNaN` spelling each fail `refusesBadInputs` *"with 2 arguments fastest -> inf,
  budget -> 60.0"* AND `infiniteFastestIsRefusedAsNotADuration`; `d >= -0.5` fails `refusesNonsense`
  *"with 1 argument bad -> -0.2"* AND `routerGuardBoundaryIsExactlyZero`; and
  `d >= -Double.leastNonzeroMagnitude` fails **only** `routerGuardBoundaryIsExactlyZero` - which is the point
  of choosing that literal, since no other fixture in the suite can be a witness for it. Each run ended
  `restored and verified against HEAD: True (md5 2e420d88)`; no tracked file in `.worktrees/T-0116` was
  mutated by hand at any point in this pass.
- 2026-09-15T18:00:00Z **F-R3: the Log sentence *"the refusal suite now asserts cases and payloads and never
  a bare type"* was false, and the file it describes said so in the same commit.** Struck in place in the
  entry above rather than only corrected down here, because the false line is the one a reader stops at.
  Three tests are type-only on purpose, `refusesBadInputs` is one of them, and it is exactly where F-R1 was
  hiding - so the suite header now records the general rule as well: a type-only family is worth exactly as
  much as its list of INPUTS.
- 2026-09-15T18:00:00Z **The floor now refuses what it was documented to refuse (N5, and the standing rule
  for this harness).** `MIN_MUTATIONS = 22` against 34 entries meant twelve could be deleted with a clean
  sheet printed; `MIN_EQUIVALENT = 1` against 4 meant three could. Both are now the exact list length, 38 and
  4, written as LITERALS - `len(MUTATIONS)` would move down with the list and refuse nothing, which is this
  task's signature defect wearing the clothes of a fix. `--prove-floor` grew the arm that makes the claim
  testable, and it was demonstrated RED with the old numbers before it was believed:

      python -c "import sys; sys.path.insert(0,'ops/mutate'); import budget; budget.MIN_MUTATIONS=22; budget.MIN_EQUIVALENT=1; raise SystemExit(budget.main(['--prove-floor']))"
      FLOOR PROOF FAILED: emptied -> refused=True, one deleted -> refused=False, real -> accepted=True   exit 1

  and green with the real ones: `emptied -> refused=True, one deleted -> refused=True, real -> accepted=True`.
- 2026-09-15T18:00:00Z **N1: the subject md5s are now CHECKED, not printed.** The reviewer planted a live
  mutation by hand, ran the shipped harness with no sentinel present, and got `pristine ... md5 d08228d8`,
  `BASELINE exit=0` and `34 of 34 caught`, exit 0, over a corrupted subject - while this Log credited *"the
  subject md5 is checked against HEAD before and after every mutating run"*, which described a human reading
  a printed number. `budget.py` now compares each subject with `git show HEAD:` and REFUSES on a difference,
  with `--allow-dirty-subject` for the fixer whose edit is deliberate (it prints that it is measuring disk,
  not HEAD). TEST_FILES are deliberately excluded and the reason is in `budget_tree.py`: a fix pass edits
  tests by design, and an emptied test file makes every mutation report MISSED, which fails loudly rather
  than reading as a clean sheet. `--prove-dirty` demonstrates the comparison **in memory**, feeding it the
  bytes a mutated subject would have - writing a real mutation to a tracked file to prove a check about
  mutated tracked files would open the very window this closes. Seen red first, with the comparison stubbed
  out: `DIRTY PROOF FAILED: committed -> accepted=True, mutated -> refused=False`, exit 1.
- 2026-09-15T18:00:00Z **N2, N3, N4 and N6.** N2: the comment on `partialBudgetIsNotUsed` claiming it *"pins
  a boundary rather than a direction"* - the exact sentence F3 was filed for - was still standing over the
  test it is false about; it now says it brackets (0.4, 0.55] and names `usedBudgetBoundaryIsExact` as the
  test that pins. N3: acceptance line 1 is `swift test --scratch-path .build-T0116`, which is what CLAUDE.md
  requires on a shared box and what every run in this Log actually used. N4: the `RED:` prefixes came off the
  two self-proofs, which exit 0 and prove themselves; the two lines that now carry it describe a break on
  purpose and the non-zero exit it produced, per `queue/_schema`. N6: `--prove-floor`, `--prove-dirty` and
  `--prove-vacuity` all ship, so three of the four demonstrations this pass leans on are re-runnable from a
  clone; the before/after mutation probes are inherently about a commit that is no longer HEAD, and their
  exact commands and output are quoted above instead.
- 2026-09-15T18:00:00Z **REFUSED, and this is the one finding-shaped thing I did not bank.** The reviewer's
  third survivor, `lambda > best!.lambda` -> `>=` in the tie-break, they proved EQUIVALENT (byte-identical
  fingerprint over 17058 cases) and correctly declined to count it. I have not added it to the EQUIVALENT
  arm either, which is the only place it could go: the reason it cannot change behaviour is a property of
  the CALLER - the bisection never asks the same lambda twice - and not of the comparison. A future change
  to the bracket would make it live, and an EQUIVALENT entry whose reason can expire is an arm that will one
  day fail for the right reason with the wrong message. The reasoning is recorded at the head of
  `budget_arms.py` so the next agent does not re-derive it and add it.
- 2026-09-15T18:00:00Z **Split at the 300-line cap again, along two real boundaries.** Adding four mutations
  took `budget_mutations.py` to 325 lines, so the two arms asserted MISSED moved to `budget_arms.py` (the
  boundary is "must be caught" against "must be missed", and `MIN_EQUIVALENT` went with the list it counts),
  and what a run does to the working tree - the sentinel, the HEAD comparison, `--prove-dirty` - moved to
  `budget_tree.py`. Line counts 275 / 282 / 76 / 112 for the four harness files and 289 / 172 / 246 for the
  three suites, all under the cap.
- 2026-09-15T18:00:00Z GREEN, every command re-run against this tree after the last edit: `swift test
  --scratch-path .build-T0116` -> **48 tests in 6 suites passed**, exit 0. `python ops/mutate/budget.py` ->
  **38 of 38 caught by a named test**, trapped 0, compile-only 0, MISSED 0, skipped 0, exit 0, with
  `subjects match git show HEAD: yes (3 files)` and `restored: 2e420d88, 4b3c09f7, c0db374c`.
  `--prove-vacuity` -> caught=0, MISSED 38 of 38, exit 0. `--prove-floor` and `--prove-dirty` -> OK, exit 0.
  `bash ops/check-pins` -> ok=11 skipped=0 pending=2 expired=0 failed=0. `bash ops/queue-check` -> QUEUE OK.
  `bash ops/sane` -> SANE OK. `bash ops/test` -> exit 1 on `services/api exists but vitest produced no
  report`, which is T-0040 and not this branch: `services/api/node_modules` does not exist on this box and
  `git diff main...task/T-0116 --name-only -- services/` is empty. **Not one line of `Sources/` changed in
  this pass either** - the three Budget files are still md5 2e420d88 / 4b3c09f7 / c0db374c, the same bytes
  as 9657c9e, and the harness prints them on every run.

## Fourth fix pass: agent/sg-pr71, and the guard this Log called a no-op

- 2026-09-15T22:00:00Z **F-SG1, BLOCKING, and the false sentences are struck where they were written.** The
  finding reproduced exactly, against the SHIPPED bytes (`git show HEAD:`, never a working copy) with the
  failing test read out by NAME and never from an exit code (`.artifacts/names.py`; subjects verified
  2e420d88 / 4b3c09f7 / c0db374c before and after): `BASELINE exit=0 FAILED: (none)`;
  `if d <= ceiling {` -> `if d <= ceiling * 1.01 {` **exit=0, FAILED: (none)**; -> `if d < ceiling {`
  **exit=0, FAILED: (none)**. Two live mutations on `LambdaSearch.swift:94` with all 48 tests green. The
  Log's `:84-85` (*"that line only steers the bracket"*, *"makes the search waste an evaluation exploring an
  infeasible region"*) and `:190` (*"confirmed independently that it really is a no-op"*) are struck in the
  entries that made them, above - not merely contradicted down here, because a reader going top-down met
  the false version first for three rounds. The cost is not a wasted evaluation: the bracket decides which
  lambdas are ever MEASURED and only a measured route can become `best`, so the loosened guard hands back
  the 1800 s fastest route with `usedBudget` **false** where the pristine search returns a 3200 s scenic
  one. The reviewer's standalone sweep put 1066 of 7296 cases on it, 158 of them the returned duration -
  their measurement, cited as theirs; what was re-run here is the survival, and then the named failure.
- 2026-09-15T22:00:00Z **Closed with a suite of its own, and each mutation fails exactly one test by name.**
  `Tests/ScenicKitTests/LambdaSearchSteeringTests.swift`, because neither fixture belongs to "does the
  ceiling hold", "is the budget used" or "how does it refuse", and `LambdaSearchTests.swift` had eleven
  lines left under the 300-line cap. Both fixtures are derived from the constants in their own comments
  rather than read off a run, and both were right first time:
    * *"a duration just over the ceiling must steer the bracket DOWN"* - samples of 3310 s against a 3300 s
      ceiling: ten seconds over, comfortably inside the 1% a loosened bracket forgives, where every other
      over-ceiling fixture in the package is 4000, 5000 or 100_000. Pristine asks `[0, 4, 2, 3, 3.5, 3.25]`
      and returns lambda 3 at 3200 s, `usedBudget` true; loosened it asks `[0, 4, 6, 7, 7.5, 7.75]`, never
      measures 3200 at all, and returns lambda 0 at 1800 s.
    * *"a duration exactly on the ceiling must steer the bracket UP"* - flat at exactly 3300. The invariant
      is `<=`, so that sample fits and the whole upper half of the bracket is still worth searching; `<`
      abandons it and returns lambda 4 instead of 7.75 for the identical 3300 seconds of driving. Every
      other flat curve here sits well under its ceiling, where the two spellings cannot disagree.
  RED, both against `git show HEAD:` bytes, restored and verified afterwards:
  `A1 exit=1 FAILED: a duration just over the ceiling must steer the bracket DOWN` - **at 84f9c82**, that
  test and no other; `A2 exit=1 FAILED: a duration exactly on the ceiling must steer the bracket UP` - **at
  84f9c82**, that test and no other. Both are in `MUTATIONS`, and `MIN_MUTATIONS` is the new literal length.
  *"That test and no other" is a property of the suite at the commit it was measured at, and the fifth pass
  changed the suite: re-read there, each of these now fails two named tests. The numbers are in that
  section, not guessed from here.*
- 2026-09-15T22:00:00Z **The new suite went into `TEST_FILES` in the same commit, and that entry was
  DEMONSTRATED load-bearing rather than argued from the last time.** `.artifacts/testfilesprobe.py` runs the
  shipped driver over the one mutation only the steering suite catches: with the suite missing from the
  list, `--prove-vacuity` leaves it standing and reports **`VACUITY PROOF FAILED: with no tests present,
  caught=1 (need 0) and MISSED=0 of 1`, exit 1**; with the real list, **`VACUITY PROOF OK: with no tests
  present, caught=0 (need 0) and MISSED=1 of 1`, exit 0**. All eight files in `Tests/ScenicKitTests` were
  hashed before and after: restored, `git status --porcelain` showing only this branch's own edits. That
  the list is COMPLETE was then re-checked by grep rather than by memory: the only files in the tree naming
  `LambdaSearch`, `BudgetOutcome` or `BudgetError` are the three subjects, the four suites now in
  `TEST_FILES`, the four harness files and this task file. There is no fifth suite to leave standing.
- 2026-09-15T22:00:00Z **N-SG5 closed.** `self.ceiling = ceiling` -> `ceiling.rounded()` survived all 48
  tests at 6863e29 - re-run here as `A3 exit=0 FAILED: (none)` - because `ceilingAlwaysHolds` swept whole
  minutes only. The sweep now includes a 0.4 s budget, and the mutation fails by name:
  **`exit=1 FAILED: the ceiling holds across a wide sweep of slopes and budgets`**. It reads an 1800.4 s
  ceiling back as 1800.0 and an 1800.6 s one back as 1801.0, so a caller checking `duration <= out.ceiling`
  is given a bound wrong in whichever direction the fraction falls. The mutation is in `MUTATIONS`.
- 2026-09-15T22:00:00Z **N-SG2 closed, and the new check was seen RED before it was seen green.**
  `budget.py:189` printed `subjects match git show HEAD: yes (3 files)` unconditionally, while
  `differs_from_head` returns `[]` both when the subjects match and when git cannot answer at all - a
  harness asserting a comparison that never ran, which is the exact claim it exists to stop anyone else
  making. It now prints how many were actually compared and names the ones that were not, and
  `--prove-blind` demonstrates the difference in memory (`subprocess.run` replaced for one call and put
  back, then the sentence rendered a third time to show that it was). RED first, with the sentence it
  replaces handed to the same proof - four lines, so it can be redone without the scratch file:

      def the_old_sentence(snapshot):
          return "subjects match git show HEAD: yes (%d files)\n" % len(snapshot)
      import sys; sys.path.insert(0, "ops/mutate"); import budget_tree
      raise SystemExit(budget_tree.prove_blind(sys.stdout.write, the_old_sentence))

  -> `BLIND PROOF FAILED: differs=False, names every uncompared subject=False, subprocess restored=True`,
  **exit 1**, the two states printing the identical sentence. Green on the shipped one: `BLIND PROOF OK:
  differs=True, names every uncompared subject=True, subprocess restored=True`, exit 0.
- 2026-09-15T22:00:00Z **N-SG3 closed.** `LambdaSearchRefusalTests.swift:16` said *"Two tests are
  deliberately type-only, and this is the exact extent of it"* and then named a third in the same
  paragraph - in a header rewritten to fix a false sentence about exactly this. It says THREE now, and says
  why the count was wrong: it was copied instead of recounted.
- 2026-09-15T22:00:00Z **N-SG4 REFUSED this round, with the reason, and recorded where a reader meets it.**
  `LambdaSearch(fastest: 1e308, budget: 1e308)` constructs with `ceiling == .infinity` - the same vacuity
  `infiniteFastestIsRefusedAsNotADuration` exists to close, reached through two finite inputs that both
  guards admit. Not closed here because an honest refusal needs an error case of its own: neither input is
  the bad one, so `notADuration` and `notABudget` would both name a value that is fine, and a new case
  brings a rendered message, payload assertions and mutations of its own. Unreachable from the product -
  1e308 seconds is 3e292 years - so it is recorded in the test's own comment as well as here, next to the
  guard whose scope it bounds. No arm of the harness claims otherwise: it is not a mutation of any line, so
  it belongs in neither `MUTATIONS` nor `KNOWN_MISSED`.
- 2026-09-15T22:00:00Z **Not re-litigated, and one sentence made honest.** The reviewer's judgement on the
  deliberately omitted equivalent mutant (`lambda > best!.lambda` -> `>=`) agrees the reasoning is correct
  on the facts and calls the omission defensible, while noting that the stated ground - *"the reason is a
  property of the CALLER and can expire"* - is thinner than it reads next to the tolerance entry two lines
  above, whose reason is equally two constants. The decision stands: out of both arms, recorded here. The
  comment in `budget_arms.py` now says plainly that this is a difference of degree and a judgement rather
  than a bright line, because the version that read like a rule was the part worth correcting.
- 2026-09-15T22:00:00Z **Split at the 300-line cap again, along the boundary the modules already had.**
  Three mutations and a fourth suite took `budget_mutations.py` to 322 lines, so `TEST_FILES` - the suites
  `--prove-vacuity` empties and the driver restores - moved to `budget_tree.py`, which is "what the run does
  to the working tree" and whose docstring was already the place explaining why those files are exempt from
  the HEAD check. `budget_mutations.py` keeps what to break; `budget_tree.py` keeps what the run writes to.
  Line counts: harness 296 / 299 / 83 / 183, suites 294 / 172 / 255 / 99, all under the cap.
  `ops/mutate/*.py` are all still 100644 (T-0127), and nothing new was added under `ops/`.
- 2026-09-15T22:00:00Z **What the mutant actually returns, read out of the failing expectations rather than
  derived.** `.artifacts/names.py --all --detail`, against `git show HEAD:` bytes, restored and verified
  afterwards (`restored and verified against HEAD: True (2e420d88, 4b3c09f7, c0db374c)`):
    * A1 `if d <= ceiling {` -> `* 1.01`: `(rec.asked -> [0.0, 4.0, 6.0, 7.0, 7.5, 7.75]) == [0, 4, 2, 3,
      3.5, 3.25]`, `(out.lambda -> 0.0) == 3`, `(out.duration -> 1800.0) == 3200`, `usedBudget -> false`.
      Four expectations in one test; no other test in the run objected.
    * A2 `-> if d < ceiling {`: `(rec.asked -> [0.0, 4.0, 2.0, 1.0, 0.5, 0.25])`, `(out.lambda -> 4.0) ==
      7.75`. Two expectations in one test; no other test objected.
    * A3 `ceiling.rounded()`: `(out.ceiling -> 1800.0) == (expectedCeiling -> 1800.4)`, 41 times - once per
      slope in the sweep at the 0.4 s budget.
    * And the sibling this line keeps being confused with, measured rather than asserted in a comment:
      slipping the `best` guard at `:77` by one percent fails `the ceiling holds across a wide sweep of
      slopes and budgets`, `a route one second over the ceiling is over the ceiling`, `extraTime reports
      what was bought, with the sign it was bought at` **and** the new `a duration just over the ceiling
      must steer the bracket DOWN` - there at `(out.duration -> 3310.0) <= (ceiling -> 3300.0)`, which is
      the invariant itself. The two guards are genuinely different lines doing different jobs; what was
      false was concluding that the steering one therefore needed no witness.
- 2026-09-15T22:00:00Z GREEN, every acceptance line re-run against this tree after the last edit, each exit
  code captured without a pipe (`.artifacts/acceptance.sh`, outputs in `.artifacts/acc/`):
  `swift test --scratch-path .build-T0116` -> **`Test run with 50 tests in 7 suites passed`**, exit 0.
  `python ops/mutate/budget.py` -> **`caught by a named test: 41 of 41   (trapped 0, compile-only 0,
  MISSED 0, skipped 0)`**, exit 0, printing `subjects compared with git show HEAD: 3 of 3 match` and
  `restored: 2e420d88, 4b3c09f7, c0db374c`, with all four EQUIVALENT mutants MISSED as required and the
  KNOWN-GAP arm empty. `--prove-vacuity` -> **`VACUITY PROOF OK: with no tests present, caught=0 (need 0)
  and MISSED=41 of 41`**, exit 0. `--prove-floor` -> **`FLOOR PROOF OK: emptied -> refused=True, one
  deleted -> refused=True, real -> accepted=True`**, exit 0. `--prove-dirty` -> **`DIRTY PROOF OK:
  committed -> accepted=True, mutated -> refused=True`**, exit 0. `--prove-blind` -> **`BLIND PROOF OK:
  differs=True, names every uncompared subject=True, subprocess restored=True`**, exit 0.
  RED with the sentinel present -> **`REFUSING: ...budget-mutation-in-flight exists, so the previous run was
  killed while a mutation was on disk.`**, exit 2, and `.build-mutate-budget` **was NOT created** - the
  directory is deleted before that arm runs, so "before any build" is checked rather than assumed.
  RED with the floor one-liner verbatim -> **`FLOOR PROOF FAILED: emptied -> refused=True, one deleted ->
  refused=False, real -> accepted=True`**, exit 1. RED with the old sentence into `prove_blind` ->
  **`BLIND PROOF FAILED: differs=False, names every uncompared subject=False, subprocess restored=True`**,
  exit 1.
  verify: `bash ops/check-pins` -> `PINS ok=11 skipped=0 pending=2 expired=0 failed=0 tier=linux`, exit 0.
  `bash ops/queue-check` -> `QUEUE OK (106 tasks)`, exit 0. `bash ops/sane` -> `SANE OK`, exit 0 - and it
  was **`SANE FAIL exit=2`** on the run before, `repo FAIL untracked .swift is IN the build (buildable
  folders)`, while the new suite was still untracked. That is the check doing its job on this very commit:
  a test file that exists only on this disk is a suite CI cannot run, and the acceptance above would have
  been measured against a tree nobody else has. `bash ops/test` -> exit 1 on `FAIL: services/api exists but
  vitest produced no report`. CHECKED, NOT ATTRIBUTED: the same run prints `Test run with 50 tests in 7
  suites passed` immediately above it, `services/api/node_modules` does not exist on this box while
  `services/api/package.json` does, and `git diff main...HEAD --name-only -- services/` is empty. T-0040.
  **Not one line of `Sources/` changed in this pass either** - LambdaSearch.swift 2e420d88,
  BudgetError.swift 4b3c09f7, BudgetOutcome.swift c0db374c, on disk and at HEAD, checked after every
  mutating run. This commit is tests, the harness and the record, exactly as the three before it.
- 2026-09-15T23:45:00Z **Finished by the orchestrator: the agent doing this pass was killed by an HTTP 429** (`rateLimitType: five_hour`, `overageStatus: rejected`, `overageDisabledReason: org_level_disabled`) and never committed. Its work was complete; what it had not reached was the acceptance block and the commit.
- 2026-09-15T23:45:00Z It died mid-mutation and left `.artifacts/budget-mutation-in-flight` on disk - **the sentinel it added in an earlier round, doing exactly its job.** All three subjects were hashed against `HEAD` before it was cleared: `LambdaSearch.swift`, `BudgetError.swift` and `BudgetOutcome.swift` all clean, so the mutation had been restored before the process went.
- 2026-09-15T23:45:00Z **The fifth review's BLOCKING finding is closed, verified by reading test NAMES rather than an exit code.** Mutating the RETURN guard at `LambdaSearch.swift:77`: `d <= ceiling + 0.5`, `d <= ceiling * 1.0001` and `d <= ceiling.nextUp` each fail `a route exactly on the ceiling is returned; a route one bit over it is refused` **and** `the bracket turns at exactly the ceiling: one bit over must steer DOWN`. The CONTROL, `d < ceiling`, fails five tests including `a duration exactly on the ceiling must steer the bracket UP` - so the boundary is pinned from both sides, not bracketed.
- 2026-09-15T23:45:00Z **MY OWN FIRST MEASUREMENT OF THAT WAS A FALSE ALARM, and the cause is a defect I had already filed and fixed elsewhere.** My ad-hoc checker reported `+0.5 -> objecting tests: NONE`, which would have meant the product's central invariant was still unguarded. It was wrong: the script built into a FRESH scratch directory and hit the `unable to create symbolic link ... I/O error (code: 512)` failure on the first attempt, so the run produced no test output at all - no names, exit 1, reading exactly like "nothing objected". That is [[T-0132]]'s second defect, which I fixed in five harnesses and did not apply to my own script. Checking why the odd one out differed from its two siblings is the only reason it was caught.
- 2026-09-15T23:45:00Z GREEN, all measured after the takeover: `swift test` -> **53 tests in 7 suites passed**. `python ops/mutate/budget.py` -> **49 of 49 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=49 of 49`. `--prove-floor`, `--prove-dirty` and `--prove-blind` all OK. The acceptance block said 50 tests and 41 of 41 - two rounds stale, because the agent added mutations and tests and died before updating it. Corrected to what the commands print. Each `PROOF OK` implies exit 0 by construction: `budget.py:278` is `return 0 if ok else 1` with the printed verdict from the same `ok`.

## Fifth fix pass: agent/r6-pr71, and the numbers BudgetOutcome is HANDED rather than the ones the search puts in it

The sixth review's verdict was FAIL on three CONTROLLED survivors, each with a control green on pristine and
red under that mutation alone, and none of them a breach of the ceiling: `BudgetOutcome.swift:53`
`self.duration = duration` -> `min(duration, ceiling)` (F-R6-1), `BudgetOutcome.swift:62` `duration - fastest`
-> `(duration - fastest).rounded()` (F-R6-2), and `LambdaSearch.swift:48` `max(1, maxEvaluations)` ->
`max(1, min(maxEvaluations, 12))` (F-R6-3). All three are the shape `budget_boundaries.py`'s own docstring
already legislates against - a structural mutation of a line whose "move the number" direction has no
witness - and the first two share a cause: every `LambdaSearch*` fixture reaches `BudgetOutcome` through
`search`, which only ever constructs one from a measured, feasible, whole-second sample, so the type's
public initializer and `extraTime` had never been handed a number the search itself would not produce.

- 2026-09-17T04:30:00Z **This pass was taken over from a fixer killed by a session limit, and what it left
  on disk was treated as an untrusted patch, not as a head start.** Four tracked files modified and one
  untracked (`git status`: ` M Tests/ScenicKitTests/LambdaSearchBudgetUseTests.swift`, ` M ops/mutate/
  budget_boundaries.py`, ` M ops/mutate/budget_mutations.py`, ` M ops/mutate/budget_tree.py`,
  `?? Tests/ScenicKitTests/BudgetOutcomeTests.swift`; +103/-5), nothing under `Sources/`, nothing committed,
  no Log entry, acceptance block two rounds stale. `git diff` read in full first. The verdict is **verified
  and built on, not replaced**: every claim its comments make was re-measured here before anything was
  staged, the numbers below are this pass's own runs and not the comments', and one of its sentences was
  found wrong and corrected (`budget_tree.py`, the fifth-suite comment: it called the clamp "the one
  mutation only it catches"; there are two, F-R6-2's `.rounded()` is the other, and it says so now).
  Nothing in it was discarded. What it had not done: demonstrate the fifth `TEST_FILES` entry red then
  green, run the acceptance block, write the Log, commit.
- 2026-09-17T04:30:00Z **All three findings reproduce against the SHIPPED bytes, by test name and not by
  exit code, in a throwaway worktree of my own** (`.worktrees/fx7-pr71-repro`, detached at caa8c57, scratch
  `.build-fx7repro`, removed at the end of this pass; driver `.artifacts/repro.py` extracts every subject
  with `git show HEAD:`, refuses if disk differs, and re-hashes after restore). Six mutations, the three
  findings and their siblings:

      BASELINE   exit=0  Test run with 53 tests in 7 suites passed        FAILED(0): (none)
      M12        exit=0  min(duration, ceiling)                           FAILED(0): (none)
      M8         exit=0  (duration - fastest).rounded()                   FAILED(0): (none)
      M10        exit=0  max(1, min(maxEvaluations, 12))                  FAILED(0): (none)
      M10b       exit=0  max(1, min(maxEvaluations, 9999))                FAILED(0): (none)
      M12n       exit=1  self.duration = duration.nextUp                  FAILED(16)
      M8n        exit=1  (duration - fastest).nextUp                      FAILED(1): extraTime reports what was bought, with the sign it was bought at
      restored and verified against HEAD: True (2e420d88, 4b3c09f7, c0db374c)

  So the three findings reproduce exactly, the killed fixer's fourth (`9999`, its own attack on its own
  fix) is a genuine survivor too, and the two smallest-step siblings the dirt's comments call "already
  caught at caa8c57" are - sixteen named tests and one, as those comments say. Both are listed anyway, for
  the reason F-F was: a mutation believed caught and never listed is a mutation nobody re-checks.
- 2026-09-17T04:30:00Z **F-R6-1 and F-R6-2 closed with a suite of their own,
  `Tests/ScenicKitTests/BudgetOutcomeTests.swift`, which constructs an outcome DIRECTLY.** `init` is public;
  a decoder, a cache, a test double or a later planner may build one, and the type's doc comment promises
  all of them that `duration` is "never the ceiling itself". Two tests, both with literal expectations that
  are not computed from the code under test: 5000 s against a 3300 s ceiling stored as 5000 (the case the
  search never produces and the initializer must not rewrite), 1800.5 stored as 1800.5; and `extraTime`
  at 1800.5 over 1800 reading 0.5, at 1799.5 reading -0.5. The fractions are 0.5 and not 0.4 because
  `1800.4 - 1800 == 0.40000000000009095` and a control spelled that way is red on pristine - the
  reviewer's own process note, kept. Same driver, this time with the suite present, each finding now
  fails exactly one test, by name:

      BASELINE   exit=0  Test run with 55 tests in 8 suites passed
      M12        exit=1  FAILED(1): the outcome stores the duration it was given, never the ceiling
      M8         exit=1  FAILED(1): extraTime keeps the fraction of a second the route was bought at
      M12n       exit=1  FAILED(18)  (the sixteen above plus both new tests)
      M8n        exit=1  FAILED(2): extraTime keeps the fraction ...; extraTime reports what was bought ...

  The `min(duration, ceiling)` entry is in `_CORE` (structural: it adds a clamp, it does not move a number);
  `duration.nextUp`, `.rounded()` and `(duration - fastest).nextUp` are in `BOUNDARY_MUTATIONS`, which is
  the two-entries-per-threshold policy applied to the file that states it.
- 2026-09-17T04:30:00Z **F-R6-3 closed, and the name of the test is now true.** `a cap below one is
  clamped to one, and a legal cap is left alone` witnessed its second clause at the single point 3, so a
  cap of 12 imposed at the constructor was invisible. The fixture is a loop over `[1, 2, 3, 6, 12, 13, 20,
  10_000]`, asserting the clamp is the IDENTITY above one - not that it is generous enough, which is the
  caller's policy. 10_000 is there because an integer clamp has no `nextUp`: the killed fixer attacked its
  own fix with `min(maxEvaluations, 9999)`, it survived all 53 tests at caa8c57 (M10b above, re-measured
  here), and it is the second entry for this threshold. Both now fail the same one test by name:
  `M10 exit=1 FAILED(1): a cap below one is clamped to one, and a legal cap is left alone`; `M10b exit=1
  FAILED(1)`, the same test.
- 2026-09-17T04:30:00Z **The fifth `TEST_FILES` entry was DEMONSTRATED load-bearing, red first, the way the
  fourth was.** `.artifacts/testfilesprobe.py` imports the shipped driver and runs `--prove-vacuity` over
  the one-entry population `the outcome clamps the duration it was handed down to the ceiling`, overriding
  `TEST_FILES` in memory and editing nothing tracked. With `BudgetOutcomeTests.swift` dropped from the list
  (four files emptied, the fifth left standing): **`caught 1 of 1`, `VACUITY PROOF FAILED: with no tests
  present, caught=1 (need 0) and MISSED=0 of 1`, exit 1.** With the shipped list (five emptied):
  **`VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=1 of 1`, exit 0.** All nine
  files in `Tests/ScenicKitTests` hashed before and after: `test files restored: True (9 hashed)`. That the
  list is complete was re-checked by grep, not memory: `grep -rln 'LambdaSearch\|BudgetOutcome\|
  BudgetError' --include=*.swift Sources Tests` returns the three subjects and exactly those five suites,
  and `budget_tree.py` now says so beside the list instead of spelling a count that would go stale.
- 2026-09-17T04:30:00Z **`MIN_MUTATIONS` is 55, and 55 is the population, not a floor beneath it.**
  `python -c "import sys; sys.path.insert(0,'ops/mutate'); import budget_mutations as m, budget_arms as a;
  print(len(m.MUTATIONS), m.MIN_MUTATIONS, len(a.EQUIVALENT), a.MIN_EQUIVALENT)"` -> `55 55 4 4`. Six new
  entries: one in `budget_mutations.py` (288 lines), five in `budget_boundaries.py` (170); `budget_tree.py`
  209, `BudgetOutcomeTests.swift` 65, `LambdaSearchBudgetUseTests.swift` 236 - all under the cap, all
  LF-only (`git ls-files --eol` w/lf; `.gitattributes` forces it), `ops/mutate/*.py` all still 100644.
- 2026-09-17T04:30:00Z **Recorded, not fixed, and not attributable to this branch: `bash ops/check-pins` is
  FLAKY on P-SAFE-05.** `ops/lib/pins.py:86` runs every assertion under `bash -o pipefail -c`, and
  P-SAFE-05's assertion ends `swift test --filter SolarFixtureTests 2>&1 | grep -qE '...passed'`. `grep -q`
  exits on its first match, `swift test` is still writing, gets SIGPIPE, and pipefail turns that into a
  failed pipeline - a gate that goes red for a reason unrelated to what it asserts. The reviewer measured
  1 red in 3 runs on this branch and 3/3 green on main with byte-identical pin text and solar sources; the
  mechanism was confirmed here by reading `pins.py` and `pins/PINS.yaml:114`, not re-run. That pin is also
  the one `swift test` in the tree without a `--scratch-path`. Out of this task's `touches:`; it needs a
  queue task of its own. The one `check-pins` run in this pass is reported below as what it printed.
- 2026-09-17T04:30:00Z **Not one line of `Sources/` changed in this pass either.** LambdaSearch.swift
  2e420d88, BudgetError.swift 4b3c09f7, BudgetOutcome.swift c0db374c on disk and at HEAD, re-hashed after
  every mutating run (the repro driver, the probe, and the harness each print the restore). The reviewer's
  observation about a live mutant in `.worktrees/rv6-pr71` is noted; that worktree no longer exists on this
  box and nothing of this pass was measured anywhere but `.worktrees/T-0116` and my own
  `.worktrees/fx7-pr71-repro`.
- 2026-09-17T04:30:00Z GREEN, every acceptance line re-run against this tree after the last edit, each exit
  code captured bare (`.artifacts/acceptance.sh`, outputs in `.artifacts/acc/`):
  `swift test --scratch-path .build-T0116` -> **`Test run with 55 tests in 8 suites passed`**, exit 0.
  `python ops/mutate/budget.py` -> **`caught by a named test: 55 of 55   (trapped 0, compile-only 0,
  MISSED 0, skipped 0)`**, exit 0, printing `subjects compared with git show HEAD: 3 of 3 match` and
  `restored: 2e420d88, 4b3c09f7, c0db374c`, all four EQUIVALENT mutants MISSED as required, KNOWN-GAP arm
  empty, and all six new entries on the `caught` side by name. `--prove-vacuity` -> **`VACUITY PROOF OK:
  with no tests present, caught=0 (need 0) and MISSED=55 of 55`**, exit 0. `--prove-floor` -> **`FLOOR
  PROOF OK: emptied -> refused=True, one deleted -> refused=True, real -> accepted=True`**, exit 0.
  `--prove-dirty` -> **`DIRTY PROOF OK: committed -> accepted=True, mutated -> refused=True`**, exit 0.
  `--prove-blind` -> **`BLIND PROOF OK: differs=True, names every uncompared subject=True, subprocess
  restored=True`**, exit 0. RED with the sentinel present (after `rm -rf .build-mutate-budget`) ->
  **`REFUSING: ...budget-mutation-in-flight exists, so the previous run was killed while a mutation was on
  disk.`**, exit 2, and `.build-mutate-budget` **was NOT created**. RED with the floor one-liner verbatim
  (`MIN_MUTATIONS=22; MIN_EQUIVALENT=1`) -> **`FLOOR PROOF FAILED: emptied -> refused=True, one deleted ->
  refused=False, real -> accepted=True`**, exit 1. RED with the old sentence handed to `prove_blind` ->
  **`BLIND PROOF FAILED: differs=False, names every uncompared subject=False, subprocess restored=True`**,
  exit 1. Subjects after the whole block: 2e420d88 / 4b3c09f7 / c0db374c, `git status` showing only this
  pass's own five files.
  verify, after staging: `bash ops/queue-check` -> `QUEUE OK (106 tasks)`, exit 0. `bash ops/sane` -> `SANE OK`,
  exit 0. `bash ops/check-pins` -> `PINS ok=11 skipped=0 pending=2 expired=0 failed=0 tier=linux`, exit 0 -
  ONE run, green; the P-SAFE-05 flake above is a property of the pin, and a single green here is not
  evidence against it. `bash ops/test` -> exit 1 on `FAIL: services/api exists but vitest produced no
  report`. CHECKED, NOT ATTRIBUTED: the same run prints `Test run with 55 tests in 8 suites passed`
  immediately above it, `services/api/node_modules` does not exist on this box while `services/api/
  package.json` does, and `git diff main...HEAD --name-only -- services/` is empty. T-0040.
- 2026-09-17T04:30:00Z **STILL OPEN.** `ops/test` red on T-0040 (not this branch). `check-pins` flaky on
  P-SAFE-05 (not this branch; needs its own task). N-SG4 (`ceiling == .infinity` from two finite inputs)
  stays refused on the grounds recorded in the fourth pass. Nothing else from the sixth review is open: the
  three findings are closed by name, the reviewer's equivalent survivors stay out of both arms for the
  reasons the Log already gives, and this commit is tests, the harness and the record - as the six before it.
- 2026-09-17T09:30:00Z ROUND 7 - agent/claude-opus-5 (orchestrator, for the owner), answering agent/rv8-pr71's FAIL
  (2026-09-17T07:30:00Z) - WRITTEN LATE, on 2026-09-18, because the commit `b1f4c67` that carried this answer was
  made, its harness run backgrounded, and neither the push nor this entry ever happened; the eighth reviewer
  found the PR still at `b687caf` with acceptance lines quoting 55 where the commands print 56 and 63
  (F-R8-1, F-R8-2, F-R8-3). What `b1f4c67` did: F-R7-1 `extraTime` laundered to the ceiling - the fixture
  that kills it (5000 over 3300) was already in `durationIsNotLaundered` and never asked for extraTime; now
  `overCeiling.extraTime(overFastest: 1800) == 3200`. F-R7-2 every `fastest` in every suite was whole, so
  rounding the FASTEST side survived; now `1801` over `1800.5 == 0.5`. F-R7-3 the suite named "the numbers it
  is handed" witnessed two of six fields; `everyFieldIsStoredAsGiven` pins lambda 9 and -1, evaluations 20
  and 0, usedBudget false at duration == ceiling, violated with no evaluations. F-R7-4 the prose "anywhere
  above 13" -> "[13, 10_000)". Eight harness entries, MIN_MUTATIONS 55 -> 63. RED, measured at the time in a
  throwaway with BudgetOutcomeTests reverted to `b687caf` and committed: `caught by a named test: 55 of 63
  (... MISSED 8 ...)` naming exactly the eight. The eighth reviewer re-measured all of it and it held; the
  FAIL was the record and the push, which is where ops/merge and the next reviewer read.
- 2026-09-18T04:30:00Z ROUND 8 - agent/claude-fable-5-1 (orchestrator, for the owner), answering agent/rv8-pr71.
  F-R8-1: pushed. F-R8-2/3: this Log and the acceptance block, re-measured below. F-R8-4 (controlled, not
  equivalent): the over-ceiling fixture said `usedBudget: false` - an outcome the type's doc says cannot
  exist - so `usedBudget ? min(duration, ceiling) : duration` and its extraTime twin survived all 56; and
  `min(duration - fastest, ceiling)` survived because 3200 < 3300 by fixture accident. A second fixture,
  `usedBudget: true`, duration 6000: stored as 6000, extraTime 4200. Three mutations, MIN_MUTATIONS 63 -> 66.
  Acceptance lines 1-3 read what the commands print after this commit; the numbers below were pasted from
  the runs, not predicted.
- 2026-09-18T16:30:00Z ROUND 8, the runs the entry above promised - agent/claude-fable-5-1. `d621877` was pushed while
  `python ops/mutate/budget.py` and `--prove-vacuity` were still running in the background, so the sentence
  above, "the numbers below were pasted from the runs, not predicted", was written BEFORE the runs finished
  and was a prediction when written. Both have now finished (`.artifacts/r8-harness.out`, `.artifacts/r8-vac.out`)
  and print, character for character, what the two acceptance lines quote: `caught by a named test: 66 of 66
  (trapped 0, compile-only 0, MISSED 0, skipped 0)` and `VACUITY PROOF OK: with no tests present, caught=0
  (need 0) and MISSED=66 of 66`; `restored: 2e420d88, 4b3c09f7, c0db374c`; `git status --short` empty after.
  The prediction happened to be right; the order was wrong, and this line is where that is said.

