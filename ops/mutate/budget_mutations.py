"""The mutation population for ops/mutate/budget.py: what to break, and what this suite must say about it.

Split out of budget.py at the 300-line cap. The driver is the protocol - build, run, require a NAMED test to
fail, restore and verify - and this file is the evidence it runs over: the mutations that must be CAUGHT.
The two arms asserted the other way round, KNOWN_MISSED and EQUIVALENT, are in budget_arms.py, split off at
the same cap along that boundary. Keeping each list whole means one that has been emptied or quietly trimmed
shows up as one diff hunk, next to the floor that counts it.

THE FLOOR, and why a mutation harness needs one. The pass condition is `caught == len(MUTATIONS)`, and an
EMPTY list satisfies it: 0 of 0, exit 0, a clean sheet over nothing measured. ops/lib/check-exec-bits refuses
on exactly this shape - *"an empty or truncated set must never read as 'all modes correct'"* - and so does
this. A run that finds fewer than MIN_MUTATIONS REFUSES instead of reporting success, and lowering the floor
is a deliberate edit somebody has to justify in a diff.

THE FLOOR IS THE REAL COUNT, and that is a correction. It used to be 22 against a population of 34, with a
comment saying it "catches an emptied or gutted population and nothing finer" - so deleting twelve entries
still read as a clean sheet, and the third review said plainly that a floor which does not refuse what it is
documented to refuse is not a floor. MIN_MUTATIONS is now the exact length of the list, written as a LITERAL
(`len(MUTATIONS)` would move down with the list and refuse nothing), so deleting ONE entry refuses. The cost
is that adding a mutation means editing the number a few lines above the list you just edited;
`--prove-floor` demonstrates the empty case AND the one-entry-short case, so the number is never taken on
trust.

What the floor is still NOT: a certificate that these are the right mutations. The second review found this
list INCOMPLETE, not dishonest - F-C was a live gap that appeared in neither MUTATIONS nor KNOWN_MISSED while
the run printed 22 of 22 - and the third review found two more, both the "fixture family covers one branch of
a condition" shape. A floor counts entries; only an attack finds the missing one.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Budget" / "LambdaSearch.swift"
ERR = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetError.swift"
OUT = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetOutcome.swift"

# Every source a mutation may touch. The driver snapshots and restores exactly these.
SUBJECTS = (SRC, ERR, OUT)

# TEST_FILES - the suites --prove-vacuity empties - moved to budget_tree.py when this file hit the 300-line
# cap again. That module is "what the run does to the working tree", and emptying and restoring four tracked
# test files is exactly that; its docstring was already the place explaining why they are exempt from the
# HEAD check. This file keeps what to break; that one keeps what the run writes to.

# The exact size of the list below, as a literal. Not a slack bound: at MIN_MUTATIONS = 22 against 34
# entries, deleting twelve mutations printed a clean sheet, which is the same "documented to refuse
# something it does not refuse" defect the tests in this package keep being blocked for. MIN_EQUIVALENT is
# in budget_arms.py, next to the list IT counts.
MIN_MUTATIONS = 41

MUTATIONS = [
    # --- structural: the author's original eight ------------------------------------------------------
    ("return the bracket instead of a measured candidate", SRC,
     "        return BudgetOutcome(\n            lambda: winner.lambda,\n"
     "            duration: winner.duration,",
     "        return BudgetOutcome(\n            lambda: lo,\n"
     "            duration: winner.duration,"),

    ("let the ceiling slip by one percent, on the guard that enforces it", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling * 1.01, best == nil || d > best!.duration"),

    ("among feasible routes, prefer the fastest instead of the most scenic", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling, best == nil || d < best!.duration"),

    ("skip the lambda = 0 seed and start from the bisection", SRC,
     "        _ = try evaluate(0)",
     "        // seed removed"),

    ("trust the router's numbers", SRC,
     "            guard d.isFinite, d >= 0 else {\n"
     "                throw BudgetError.routerReturnedNonsense(lambda: lambda, duration: d)\n"
     "            }",
     "            // guard removed"),

    ("compare only consecutive samples for monotonicity", SRC,
     "        for a in samples {\n            for b in samples where b.lambda > a.lambda {\n"
     "                if b.duration < a.duration { return true }\n            }\n        }",
     "        for (a, b) in zip(samples, samples.dropFirst()) {\n"
     "            if b.lambda > a.lambda && b.duration < a.duration { return true }\n        }"),

    ("call the budget used whenever anything was found", SRC,
     "usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "usedBudget: true,"),

    ("keep the last feasible candidate rather than the best", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration\n"
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "            if d <= ceiling {"),

    # --- the six a reviewer found uncaught. Every mutation above is STRUCTURAL - delete a guard, invert a
    # --- comparison - and not one touches a number, which is exactly where this suite was blind.
    ("minBudgetUse 0.5 -> 0.05, so 90 seconds of a 25-minute budget counts as used", SRC,
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.05"),

    ("minBudgetUse 0.5 -> 0.95, so almost nothing ever counts as used", SRC,
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.95"),

    ("maxLambda 8 -> 16, sending four of six router requests into an infeasible region", SRC,
     "public static let maxLambda = 8.0",
     "public static let maxLambda = 16.0"),

    ("lambdaTolerance 0.05 -> 0.75, giving back a router request for nothing", SRC,
     "public static let lambdaTolerance = 0.05",
     "public static let lambdaTolerance = 0.75"),

    ("the ceiling is one second more generous than the budget", SRC,
     "    public var ceiling: TimeInterval { fastest + budget }",
     "    public var ceiling: TimeInterval { fastest + budget + 1 }"),

    ("accept a fractionally negative budget", SRC,
     "guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "guard budget.isFinite, budget > -1 else { throw BudgetError.notABudget(budget) }"),

    # --- and two more of my own in the same spirit ----------------------------------------------------
    ("default maxEvaluations from 6 to 2", SRC,
     "maxEvaluations: Int = 6",
     "maxEvaluations: Int = 2"),

    ("drop the tie-break, keeping whichever equally fast route was seen first", SRC,
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "                || (d == best!.duration && lambda < best!.lambda) {"),

    # --- reviewer-pr71's findings F1 to F4 ----------------------------------------------------------------
    # F3: the "at least half the budget" boundary had no witness on either side.
    ("usedBudget becomes strict, so exactly half the budget stops counting", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: budget == 0 || winner.duration > fastest + Self.minBudgetUse * budget,"),

    ("a zero budget stops counting as used", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: winner.duration >= fastest + Self.minBudgetUse * budget,"),

    # F2: the tolerance termination fired in no test at all, so deleting it was free - and widening it gave
    # back a router request for nothing, with the whole suite green.
    ("drop the lambdaTolerance termination, spending router requests for nothing", SRC,
     "        while evaluations < maxEvaluations, hi - lo > Self.lambdaTolerance {",
     "        while evaluations < maxEvaluations {"),

    # F4: BudgetError's whole CustomStringConvertible conformance had no behavioural coverage. These strings
    # reach a log and a bug report.
    ("the error message reports the lambda as the duration", ERR,
     '            return "router returned \\(duration) s at lambda \\(lambda)"',
     '            return "router returned \\(lambda) s at lambda \\(duration)"'),

    ("the no-feasible-lambda message loses the ceiling it was measured against", ERR,
     '            return "no lambda produced a route within the \\(ceiling) s ceiling in \\(evaluations) "',
     '            return "no lambda produced a route within the ceiling in \\(evaluations) "'),

    ("a bad budget is reported as a bad duration", SRC,
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notADuration(budget) }"),

    # --- the second review's findings F-B, F-C, F-E to F-I --------------------------------------------
    # The shape they all share: a value this type COMPUTES, reaching a caller with nothing asserting it.
    #
    # F-C. Named in the previous Log as real and deliberately unfixed, and then listed in neither MUTATIONS
    # nor KNOWN_MISSED, so `22 of 22 ... MISSED 0` printed a clean sheet over a gap the same commit
    # documented. A gap merely absent from the list is a gap nobody can see - including when the list is
    # this one.
    ("the monotonicity scan skips its last outer sample", SRC,
     "        for a in samples {",
     "        for a in samples.dropLast() {"),

    # F-F. The previous Log claimed this one was uncovered. It was not - it is caught, and was caught at that
    # commit too. Claimed from belief instead of from a re-run, so it is in the list now and the run says so.
    ("the bisection midpoint moves to 60 percent of the bracket", SRC,
     "            let mid = lo + (hi - lo) / 2",
     "            let mid = lo + (hi - lo) * 0.6"),

    # F-G. Infeasible samples are recorded ON PURPOSE: they are the evidence for the monotonicity scan and
    # the source of the "shortest seen" number in a refusal. Recording only the feasible ones hides a real
    # violation and degrades the refusal message to "the shortest seen was inf s".
    ("record only the feasible samples for the monotonicity scan", SRC,
     "            seen.append((lambda, d))",
     "            if d <= ceiling { seen.append((lambda, d)) }"),

    # F-B. noFeasibleLambda is the only BudgetError whose payload the search COMPUTES rather than echoes
    # back from an input, and it was the only one with no payload assertion. Three different wrong sentences
    # reached the reader with the suite green.
    ("the shortest route seen is reported as the longest", SRC,
     r"            let shortest = seen.map(\.duration).min() ?? .infinity",
     r"            let shortest = seen.map(\.duration).max() ?? .infinity"),

    ("the refusal reports zero evaluations, hiding what it cost", SRC,
     "            throw BudgetError.noFeasibleLambda(ceiling: ceiling, best: shortest, "
     "evaluations: evaluations)",
     "            throw BudgetError.noFeasibleLambda(ceiling: ceiling, best: shortest, evaluations: 0)"),

    ("the refusal reports a zero ceiling", SRC,
     "            throw BudgetError.noFeasibleLambda(ceiling: ceiling, best: shortest, "
     "evaluations: evaluations)",
     "            throw BudgetError.noFeasibleLambda(ceiling: 0, best: shortest, "
     "evaluations: evaluations)"),

    # F-E. This was a KNOWN_MISSED entry claiming "no behaviour to assert". False: maxEvaluations is public
    # and reads back 1 pristine, -5 mutated. A gap booked as permanent that one assertion closes.
    ("drop the max(1, ...) clamp on maxEvaluations", SRC,
     "max(1, maxEvaluations)", "maxEvaluations"),

    # F-H. Every fixture had duration > fastest, so extraTime's SIGN had no witness: the difference between
    # "you saved a minute" and "you spent a minute".
    ("extraTime reports the absolute difference, losing the sign", OUT,
     "        duration - fastest",
     "        abs(duration - fastest)"),

    # F-I. refusesNonsense covers .nan, .infinity and -1; zero is the boundary the guard admits.
    ("a router duration of exactly zero is called nonsense", SRC,
     "            guard d.isFinite, d >= 0 else {",
     "            guard d.isFinite, d > 0 else {"),

    # --- three the SECOND fix pass found by attacking its own work ------------------------------------
    # None of these came from a review. Each survived the suite as it stood after the findings above were
    # closed, and each was proved to be a real behaviour change by a standalone control before a line of
    # test was written for it (the counts below are cases whose fingerprint changed, out of 5891).
    #
    # 154 cases. An infinite duration passes `d >= 0`, is never feasible, and the search ends in
    # noFeasibleLambda saying "the shortest seen was inf s" - a BudgetError, so a type-only assertion is
    # satisfied by it. This is why the refusal suite asserts cases and payloads and never bare types.
    ("drop isFinite from the router guard, keeping only d >= 0", SRC,
     "            guard d.isFinite, d >= 0 else {",
     "            guard d >= 0 else {"),

    # 2 cases, both of them shapes only the helper's own callers can produce: monotonicity is about a LARGER
    # lambda measuring shorter, so two samples at the same lambda are not a violation.
    ("equal lambdas count as a monotonicity violation", SRC,
     "            for b in samples where b.lambda > a.lambda {",
     "            for b in samples where b.lambda >= a.lambda {"),

    # 638 cases. The short-circuit is for a budget of ZERO, not for a small one: widened, it reports a
    # budget as spent when none of it was.
    ("the zero-budget short-circuit becomes a half-second tolerance", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: budget <= 0.5 || winner.duration >= fastest + Self.minBudgetUse * budget,"),

    # --- the third review's two blocking findings, F-R1 and F-R2 --------------------------------------
    # Both are the same shape as each other and as most of the list above: a guard with two halves, and a
    # fixture family that only ever exercises one of them. Each SURVIVED all 46 tests at 33d1715 - measured,
    # not assumed - and each is a real behaviour change with a standalone control behind it.
    #
    # F-R1, 70 of 17058 cases. `fastest > 0` already refuses NaN, so the family's (.nan, 60) fixture is not a
    # witness for `isFinite`; infinity is the only value the two halves disagree about, and it was the one
    # combination the family omitted. An infinite `fastest` makes `ceiling = fastest + budget` infinite, so
    # the ceiling invariant is not breached but VACUOUS - the worse of the two failures.
    ("drop isFinite from the constructor guard, keeping only fastest > 0", SRC,
     "        guard fastest.isFinite, fastest > 0 else { throw BudgetError.notADuration(fastest) }",
     "        guard fastest > 0 else { throw BudgetError.notADuration(fastest) }"),

    # The same hole spelled the way a well-meaning edit would spell it: NaN-safe, infinity-blind. Listed
    # separately because a test that happened to pin only NaN would catch the entry above and miss this one.
    ("the constructor guard rejects NaN but admits infinity", SRC,
     "        guard fastest.isFinite, fastest > 0 else { throw BudgetError.notADuration(fastest) }",
     "        guard !fastest.isNaN, fastest > 0 else { throw BudgetError.notADuration(fastest) }"),

    # F-R2, 1701 of 17058 cases. -1 illegal and 0 legal brackets the threshold in (-1, 0] and pins nothing
    # inside it. A router answering -0.2 s then reaches the caller as a route, with usedBudget true and
    # extraTime -1800.2.
    ("the router guard tolerates half a second of negative duration", SRC,
     "            guard d.isFinite, d >= 0 else {",
     "            guard d.isFinite, d >= -0.5 else {"),

    # And the adjacent threshold, which is what makes the boundary PINNED rather than bracketed more
    # tightly: there is no Double between this and 0 for a fixture to fall through.
    ("the router guard tolerates the largest negative Double there is", SRC,
     "            guard d.isFinite, d >= 0 else {",
     "            guard d.isFinite, d >= -Double.leastNonzeroMagnitude else {"),

    # --- the fourth review's F-SG1, and N-SG5 beside it -----------------------------------------------
    # The BRACKET-STEERING guard at LambdaSearch.swift:94 - NOT the `best` guard at :77 that the second
    # entry of this list covers. :77 decides what may be RETURNED; :94 decides what is ever MEASURED, and
    # only a measured route can be returned, so the Log sentence calling this one "a no-op" that "makes the
    # search waste an evaluation" was false and is struck where it stands. The reviewer's standalone sweep
    # measured 1066 of 7296 cases changing, 158 of them the RETURNED DURATION; what was re-run here is that
    # both spellings survived all 48 tests at 6863e29, and that each now fails a test by name.
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
]
