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
  - "swift test -> Test run with 46 tests in 6 suites passed, exit 0"
  - "python ops/mutate/budget.py -> caught by a named test: 34 of 34   (trapped 0, compile-only 0, MISSED 0, skipped 0), exit 0"
  - "RED: python ops/mutate/budget.py --prove-vacuity -> VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=34 of 34, exit 0"
  - "RED: python ops/mutate/budget.py --prove-floor -> FLOOR PROOF OK: emptied -> refused=True, real -> accepted=True, exit 0"
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

### The third one was my mutation being wrong, and that is a finding about the code

`let the ceiling slip by one percent` aimed at `if d <= ceiling {` inside the bisection and was not caught.
That is correct behaviour, not a hole: **that line only steers the bracket.** Feasibility is filtered
separately, where `best` is updated. Loosening the bracket makes the search waste an evaluation exploring an
infeasible region; it cannot breach the invariant, because nothing infeasible can ever become `best`.

So the guard that actually enforces the ceiling is a different line, and the mutation was retargeted at it.
Re-run:

    8 of 8 mutations caught     exit 0

The separation is worth keeping deliberately: the bisection can be wrong about where to look next without
the returned answer ever being wrong about the ceiling.

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

They re-applied my originally mis-aimed bracket mutation and confirmed independently that it really is a
no-op - the Log's claim that "the bracket steers, the best guard enforces" is true and was not a defect
quietly redefined into a harmless one. They verified it twice: by re-running the mutation, and by fuzzing
the standalone-compiled sources, where the answer fingerprint changed (proving the mutation is live rather
than equivalent) while breaches stayed at zero.
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
- 2026-09-15T12:00:00Z **I then attacked the fixed suite with twelve mutations nobody had written, and six survived.** Each survivor was compiled STANDALONE - copies of the three Budget sources plus a sweep of 5891 cases covering every field of `BudgetOutcome`, the search's own cap and ceiling, each error's rendered text, and the exact sequence of lambdas the router is asked for - pristine against mutant, so no tracked file was written for a control. **Three were equivalent** (byte-identical fingerprints) and are now asserted MISSED in the EQUIVALENT arm with the reason each is equivalent, not merely the measurement: the tolerance comparison `>` -> `>=` (the bracket width is exactly 8*2^-k and 0.05 is not), the midpoint written as `(lo+hi)/2` (exact over a bracket bounded by 8), and the monotonicity scan run over the samples reversed (an all-pairs scan cannot depend on order). **Three were real, and are now caught**: dropping `isFinite` from the router guard sends an infinite duration all the way to `noFeasibleLambda` - a BudgetError, so `#expect(throws: BudgetError.self)` was satisfied by the wrong refusal, 154 cases changed; `b.lambda > a.lambda` -> `>=` accuses a router that answered the same lambda twice, 2 cases; and `budget == 0` -> `budget <= 0.5` reports a budget as spent when none of it was, 638 cases. The refusal suite now asserts cases and payloads and never a bare type.
- 2026-09-15T12:00:00Z **Not one line of `Sources/` changed in this pass.** The three Budget files are byte-identical to 9657c9e - md5 2e420d88 (LambdaSearch), 4b3c09f7 (BudgetError), c0db374c (BudgetOutcome) - and the harness prints those same three on every run. Both reviews reached the same verdict about the code and a different one about the suite: the ceiling invariant survived every mutation either reviewer or I could land, and what was wrong was what the tests, the harness and the frontmatter CLAIMED to cover. This commit is tests, the harness and the record.
- 2026-09-15T12:00:00Z GREEN, every command re-run against this tree: `swift test` -> **46 tests in 6 suites passed**, exit 0. `python ops/mutate/budget.py` -> **34 of 34 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> caught=0, MISSED 34 of 34, exit 0. `--prove-floor` -> OK, exit 0. `bash ops/check-pins` -> ok=11 pending=2 failed=0. `bash ops/queue-check` -> QUEUE OK. `bash ops/sane` -> SANE OK. `bash ops/test` -> exit 1, `FAIL: services/api exists but vitest produced no report`, which is T-0040 and not this branch: `services/api/node_modules` does not exist on this box and this PR touches no TypeScript. Line counts 285 / 172 / 177 / 253 / 283, all under the cap. Subject md5s before and after every mutating run: 2e420d88 / 4b3c09f7 / c0db374c, identical to HEAD.

- 2026-09-15T05:10:00Z **Finished by the orchestrator after the session that was fixing this ended mid-run.** The agent's work was complete and green; what it had not reached was the restore at the end of its red demonstration. `git status` showed the shipping source modified and tests failing, which reads exactly like a broken fix and is not one - the failing tests WERE the demonstration succeeding.

  Restored with `git checkout --` and re-verified from a clean tree. Nothing was lost: no commit had been
  made, and the mutation was confined to the working tree.

  The generalisation is recorded on [[T-0130]]: a red demo that mutates a tracked file and relies on a
  `finally` to restore it has a window, minutes long, in which the process can die. That is a second source
  of the same hazard the task was filed for, and it needs no second agent.
