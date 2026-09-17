"""The mutations that MOVE A THRESHOLD instead of deleting a guard or inverting a comparison.

Split out of budget_mutations.py at the 300-line cap, along the boundary that file's own comment already
draws: everything there is structural - a guard removed, a comparison flipped, a value swapped for another
field - and everything here shifts a number by a hair. They are appended to `MUTATIONS` and counted by the
single floor `MIN_MUTATIONS` in budget_mutations.py, so deleting an entry from EITHER file refuses.

Why the split falls here rather than at a line number. This is the defect this package has now been blocked
for four rounds running, in four different guards, always with the same shape: a fixture family that sits
NEAR a boundary instead of ON it constrains the threshold to an INTERVAL and pins nothing inside it.

  * F3   - usedBudget, pinned to (0.4, 0.55] of the budget by two fixtures either side of it.
  * F-R2 - the router's `d >= 0` guard, pinned to (-1, 0] by `-1` illegal and `0` legal.
  * F-SG1 - the bracket-steering `d <= ceiling`, whose only over-ceiling fixtures were 10 s and 4000 s over.
  * the fifth review's BLOCKING 1 - the `d <= ceiling` that decides what may be RETURNED, pinned only to
    [ceiling, ceiling + 1) by a single fixture sitting exactly one second on the wrong side. That is the
    CLAUDE.md invariant - *"returned ETA <= fastest + budget. Always"* - and `+ 0.5`, `* 1.0001` and
    `.nextUp` each survived all 50 tests at 84f9c82, returning an ETA above the ceiling with nothing
    objecting. The review measured `+ 0.999` surviving the same way; that one is their run, not this one.

So each threshold gets TWO entries: the realistic spelling a developer would actually write (a float
tolerance, a rounded second), and the smallest representable step there is. A test that kills the second
cannot be satisfied by a fixture that merely sits close, because there is no Double between `x.nextUp` and
`x` for a loosened threshold to hide in. Both are kept rather than only the tight one: the loose spelling is
what the defect looks like in a diff, and a future reader needs to recognise it there.
"""
from __future__ import annotations

from budget_paths import OUT, SRC

BOUNDARY_MUTATIONS = [
    # --- the fourth review's F-SG1, and N-SG5 beside it -----------------------------------------------
    # The BRACKET-STEERING guard at LambdaSearch.swift:94 - NOT the `best` guard at :77 that
    # budget_mutations.py's second entry covers. :77 decides what may be RETURNED; :94 decides what is ever
    # MEASURED, and only a measured route can be returned, so the Log sentence calling this one "a no-op"
    # that "makes the search waste an evaluation" was false and is struck where it stands. The reviewer's
    # standalone sweep measured 1066 of 7296 cases changing, 158 of them the RETURNED DURATION; what was
    # re-run here is that both spellings survived all 48 tests at 6863e29, and that each now fails a test by
    # name.
    #
    # The predecessor entry names the line it does NOT touch ("on the guard that enforces it") and was read
    # for three rounds as covering both. An entry distinguished from its sibling only in prose gets read as
    # the sibling.
    ("let the ceiling slip by one percent, on the guard that STEERS the bracket", SRC,
     "            if d <= ceiling {",
     "            if d <= ceiling * 1.01 {"),

    # The other direction, which no fixture could see: a route landing EXACTLY on the ceiling fits - the
    # invariant is `<=` - so the upper half of the bracket is still worth searching. Every other flat curve
    # here sits well under its ceiling, where `<` and `<=` cannot disagree.
    ("a duration exactly on the ceiling steers the bracket downward", SRC,
     "            if d <= ceiling {",
     "            if d < ceiling {"),

    # N-SG5. The ceiling sweep used whole-minute budgets only, so `ceiling` had no witness at a FRACTIONAL
    # one: 715 of 7296 cases changed, an 1800.4 s ceiling reading back as 1800.0, and nothing objected.
    ("the outcome rounds the ceiling to a whole second", OUT,
     "        self.ceiling = ceiling",
     "        self.ceiling = ceiling.rounded()"),

    # --- the fifth review's BLOCKING 1: the guard that ENFORCES the product invariant -----------------
    # `* 1.01` on this line is already in budget_mutations.py, and that it failed four named tests is what
    # made the header of LambdaSearchSteeringTests call this guard "covered". Covered against a ONE PERCENT
    # slip, and that is all it meant: each of the three below survived all 50 tests at 84f9c82 with no named
    # test objecting, and each returns an ETA ABOVE the ceiling. With fastest 1800, budget 1500 and a router
    # answering 1800 at lambda 0 and 3300.3 elsewhere, pristine returns lambda 0 / 1800 s and the mutant
    # returns lambda 4 / 3300.3 s against a 3300 s ceiling. Which tests each of them fails today is read out
    # of a run and recorded in the task Log, never counted in a comment here that nothing re-runs.
    ("the enforcing guard forgives half a second over the ceiling", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling + 0.5, best == nil || d > best!.duration"),

    ("the enforcing guard forgives a hundredth of a percent over the ceiling", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling * 1.0001, best == nil || d > best!.duration"),

    # The last-bit spelling, which is what makes the boundary PINNED rather than bracketed more tightly:
    # there is no Double between this threshold and `ceiling` for a fixture to fall through.
    ("the enforcing guard forgives the smallest step over the ceiling there is", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling.nextUp, best == nil || d > best!.duration"),

    # --- the fifth review's BLOCKING 2: the same repair on the steering guard --------------------------
    # F-SG1's fixture puts its infeasible samples ten seconds over a 3300 s ceiling, which constrains this
    # guard to [ceiling, ceiling + 10) and no further: `+ 1` and `.nextUp` both survived all 50 tests at
    # 84f9c82 (the review measured `+ 9.9` too), and each reproduces F-SG1's own consequence - the bracket
    # climbs to 4, 6, 7, 7.5, 7.75, nothing measured there can become `best`, and the user is handed the
    # fastest route with usedBudget false.
    ("the steering guard forgives a whole second over the ceiling", SRC,
     "            if d <= ceiling {",
     "            if d <= ceiling + 1 {"),

    ("the steering guard forgives the smallest step over the ceiling there is", SRC,
     "            if d <= ceiling {",
     "            if d <= ceiling.nextUp {"),

    # --- the fifth review's NON-BLOCKING 3: usedBudget, the F3 shape one order of magnitude down -------
    # `usedBudgetBoundaryIsExact` pinned 2550 and 2549, which admits any shift under a second; a tenth of a
    # second was enough to report a route buying 749.95 s of a 1500 s budget as having used at least half.
    ("the usedBudget threshold slips a tenth of a second", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget - 0.1,"),

    ("the usedBudget threshold slips the smallest step there is", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: budget == 0 || winner.duration >= "
     "(fastest + Self.minBudgetUse * budget).nextDown,"),

    # --- the fifth review's OBSERVATION, closed rather than carried forward ----------------------------
    # Not a threshold, and here because it is the fifth review's and belongs beside its siblings. The two
    # constructor guards only disagree when BOTH inputs are bad, and no fixture in `refusesBadInputs` had
    # two. Swapped, a caller holding (-1, -1) is told the budget is the problem.
    ("the two constructor guards are checked in the other order", SRC,
     "        guard fastest.isFinite, fastest > 0 else { throw BudgetError.notADuration(fastest) }\n"
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }\n"
     "        guard fastest.isFinite, fastest > 0 else { throw BudgetError.notADuration(fastest) }"),

    # --- the sixth review's F-R6-1, second half: the number that is NOT the ceiling --------------------
    # The structural half of this line - `min(duration, ceiling)` - is in budget_mutations.py. This is the
    # policy at the head of this file applied to it: the pin has to be exact, not merely "not the ceiling".
    # Already CAUGHT at caa8c57, and recorded because that was MEASURED rather than assumed - it fails
    # sixteen named tests, `the returned duration is the one the router gave for the returned lambda, not an
    # estimate` among them. The precedent is F-F, an entry added after a Log claimed it uncovered and a run
    # said otherwise: a mutation believed caught and never listed is a mutation nobody re-checks.
    ("the outcome stores the smallest step off the duration it was handed", OUT,
     "        self.duration = duration",
     "        self.duration = duration.nextUp"),

    # --- the sixth review's F-R6-2: extraTime, the OTHER number this type hands a user -----------------
    # Exactly N-SG5 three entries above, ten lines down the same 64-line file and left behind by it. The
    # ceiling got a fractional witness in the fifth round (a 0.4 s budget in `ceilingAlwaysHolds`);
    # `extraTime` did not, because both fixtures in `extraTime reports what was bought, with the sign it was
    # bought at` are whole seconds - 1440 and -60 - and every duration the search produces from those
    # fixtures is whole too. So this survived all 53 tests at caa8c57 with nothing objecting, and a user who
    # bought 30.5 extra seconds was told 31. Killed by BudgetOutcomeTests, at 1800.5 - 1800 == 0.5, both
    # exact in binary. Spelled at 1800.4 the fixture is red against the pristine source
    # (1800.4 - 1800 == 0.40000000000009095), which is the sixth review's own process note.
    ("extraTime rounds what was bought to a whole second", OUT,
     "        duration - fastest",
     "        (duration - fastest).rounded()"),

    # The smallest-step spelling, so the fraction is PINNED rather than bracketed by whatever a rounding
    # rule happens to preserve. Already CAUGHT at caa8c57 - measured, one named test, `extraTime reports what
    # was bought, with the sign it was bought at` - and listed for the same reason as the entry above it.
    ("extraTime moves what was bought by the smallest step there is", OUT,
     "        duration - fastest",
     "        (duration - fastest).nextUp"),

    # --- the seventh review's F-R7-1 and F-R7-2: the same line, the two directions nobody had asked ------
    # `min(duration, ceiling)` was killed in the sixth round; its twin on the OTHER user-facing number,
    # laundering `extraTime` to the ceiling instead of the duration, survived all 55 - the test holding the
    # killing fixture (5000 over 3300) never asked it for extraTime. And every `fastest` in every suite was
    # a whole number, so rounding the FASTEST side survived too. Both killed by BudgetOutcomeTests.
    ("extraTime is laundered to the ceiling", OUT,
     "        duration - fastest",
     "        min(duration - fastest, ceiling - fastest)"),

    ("extraTime rounds the fastest side, which every fixture had whole", OUT,
     "        duration - fastest",
     "        duration - fastest.rounded()"),

    # --- F-R7-3: the four fields the suite's name covered and its assertions did not ---------------------
    ("the outcome clamps lambda to maxLambda", OUT,
     "        self.lambda = lambda",
     "        self.lambda = min(lambda, LambdaSearch.maxLambda)"),

    ("the outcome floors lambda at zero", OUT,
     "        self.lambda = lambda",
     "        self.lambda = max(lambda, 0)"),

    ("the outcome clamps evaluations to the twelve its doc names", OUT,
     "        self.evaluations = evaluations",
     "        self.evaluations = min(evaluations, 12)"),

    ("the outcome floors evaluations at one", OUT,
     "        self.evaluations = evaluations",
     "        self.evaluations = max(evaluations, 1)"),

    ("the outcome reports the budget used whenever the duration reached the ceiling", OUT,
     "        self.usedBudget = usedBudget",
     "        self.usedBudget = usedBudget || duration >= ceiling"),

    ("the outcome forgets a violation seen on the first evaluation", OUT,
     "        self.monotonicityViolated = monotonicityViolated",
     "        self.monotonicityViolated = monotonicityViolated && evaluations > 1"),

    # --- the sixth review's F-R6-3: the clamp that is only asserted in one direction -------------------
    # `max(1, maxEvaluations)` has two jobs and a test for one of them. F-E promoted it out of KNOWN_MISSED
    # because `maxEvaluations` is PUBLIC and is what a caller reads to see what a plan may cost - and then
    # `a cap below one is clamped to one, and a legal cap is left alone` witnessed the second half of its own
    # name at the single point 3. Twelve is the number a developer reaches for here, because the plan caps a
    # whole plan at twelve requests; this search is one part of such a plan, so capping it here is both wrong
    # and invisible - a caller asking for 20 reads 12 back. Survived all 53 tests at caa8c57.
    ("a cap above the plan's twelve requests is silently lowered to twelve", SRC,
     "        self.maxEvaluations = max(1, maxEvaluations)",
     "        self.maxEvaluations = max(1, min(maxEvaluations, 12))"),

    # The same clamp set so high no plausible fixture VALUE would sit above it. An integer clamp has no
    # `nextUp`, so what stands in for the smallest-representable-step entry here is a threshold that only an
    # assertion about the IDENTITY can see: any test that pins a handful of legal caps one by one passes this
    # unless one of them happens to be larger. Found by attacking the fix for the entry above rather than by
    # a review; it survived all 53 tests at caa8c57 too, and it is why the fixture list in that test ends at
    # 10_000 instead of at 13.
    ("a cap is silently lowered to a ceiling no fixture would reach", SRC,
     "        self.maxEvaluations = max(1, maxEvaluations)",
     "        self.maxEvaluations = max(1, min(maxEvaluations, 9999))"),
]
