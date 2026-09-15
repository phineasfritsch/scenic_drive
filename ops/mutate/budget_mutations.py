"""The mutation population for ops/mutate/budget.py: what to break, and what this suite must say about it.

Split out of budget.py at the 300-line cap. The driver is the protocol - build, run, require a NAMED test to
fail, restore and verify - and this file is the evidence it runs over. Keeping the population in one file
means a list that has been emptied or quietly trimmed shows up as one diff hunk, next to the floor that
counts it.

THE FLOOR, and why a mutation harness needs one. The pass condition is `caught == len(MUTATIONS)`, and an
EMPTY list satisfies it: 0 of 0, exit 0, a clean sheet over nothing measured. ops/lib/check-exec-bits refuses
on exactly this shape - *"an empty or truncated set must never read as 'all modes correct'"* - and so does
this. A run that finds fewer than MIN_MUTATIONS REFUSES instead of reporting success, and lowering the floor
is a deliberate edit somebody has to justify in a diff.

What the floor is NOT: a certificate that these are the right mutations. MIN_MUTATIONS is the size of this
list at the commit the second review measured - 22 - and that review found the list INCOMPLETE, not honest:
F-C was a live gap that appeared in neither MUTATIONS nor KNOWN_MISSED while the run printed 22 of 22. The
floor catches an emptied or gutted population and nothing finer; at 22 against today's population, deleting
a single entry still passes. Same shape as MIN_FILES = 17 guarding 23 required files in check-exec-bits.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Budget" / "LambdaSearch.swift"
ERR = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetError.swift"
OUT = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetOutcome.swift"

# Every source a mutation may touch. The driver snapshots and restores exactly these.
SUBJECTS = (SRC, ERR, OUT)

# ALL THREE suites. reviewer-pr71's blocking finding: commit bc5e7f6 split ten tests into
# LambdaSearchBudgetUseTests.swift and --prove-vacuity kept emptying only the first file, so it reported
# "VACUITY PROOF FAILED: 8 mutations were reported caught" while the task log recorded OK. The harness's own
# message - "with no tests present" - was false; it was measuring the sibling test file. A demonstration
# that decayed at the last commit, and exactly the shape of defect this repository exists to catch.
#
# The refusal suite is the third such split, made in this commit for the same 300-line cap, and it is listed
# here in the same commit. That this entry is LOAD-BEARING was demonstrated rather than assumed: with the
# refusal suite removed from this list, --prove-vacuity leaves it standing, it catches "the shortest route
# seen is reported as the longest" - the one mutation only it catches - and the run reports
# `VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1. With all three listed: MISSED 1 of 1, exit 0. A suite
# missing from this list fails the proof loudly; it does not weaken it quietly.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchBudgetUseTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchRefusalTests.swift"]

MIN_MUTATIONS = 22
MIN_EQUIVALENT = 1

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
]

# Mutations this suite is KNOWN not to catch, asserted the other way round: the arm FAILS if one starts
# being MISSED no longer, because a gap that closed should move up into MUTATIONS.
#
# EMPTY, and that emptiness is a claim rather than an oversight. The one entry it ever held - the
# `max(1, ...)` clamp - justified itself with "No behaviour to assert; the clamp is defensive", and the
# second review showed that reason was false: `maxEvaluations` is public and reads 1 pristine, -5 mutated.
# One assertion killed it, so it is a MUTATION above now. An entry here claims no assertion can kill this
# mutation; if that reason is wrong, the arm records a closable gap as a feature, which is worse than having
# no arm at all. Every entry added here has to survive that question.
KNOWN_MISSED = []

# Cannot change behaviour, so anything but MISSED is a FAILURE - a catch means a test has an opinion about
# how the code is WRITTEN rather than what it DOES.
#
# The last three survived the second fix pass's own attack, and each was then compiled STANDALONE, pristine
# against mutant, over 5891 cases covering every field of BudgetOutcome, the search's own cap and ceiling,
# each error's rendered text, and the exact sequence of lambdas the router is asked for. All three came back
# byte-identical - which is what "equivalent" has to mean here, and is the reason they are asserted MISSED
# rather than quietly dropped from the report. Each also has a REASON below, because a fingerprint that
# happened to match over one sweep is evidence and not a proof.
EQUIVALENT = [
    ("start the evaluation counter from a different literal zero", SRC,
     "        var evaluations = 0",
     "        var evaluations = 0o0"),

    # The bracket width is exactly 8 * 2^-k on every iteration - maxLambda is 8 and the midpoint halves a
    # dyadic rational exactly - and lambdaTolerance 0.05 is not of that form, so `>` and `>=` can never
    # disagree. A catch here would mean one of those two constants stopped being what this reasoning assumes.
    ("the lambdaTolerance termination becomes inclusive", SRC,
     "        while evaluations < maxEvaluations, hi - lo > Self.lambdaTolerance {",
     "        while evaluations < maxEvaluations, hi - lo >= Self.lambdaTolerance {"),

    # Algebraically equal, and over a bracket bounded by 8 both forms are exact in binary floating point, so
    # the router is asked for identical lambdas to the last bit.
    ("the midpoint is written as the average of the ends", SRC,
     "            let mid = lo + (hi - lo) / 2",
     "            let mid = (lo + hi) / 2"),

    # The scan compares every ordered pair, so the order the samples arrive in cannot change its answer.
    # Worth asserting: a test that pinned the scan by sample ORDER rather than by content would catch this.
    ("the monotonicity scan runs over the samples reversed", SRC,
     "            monotonicityViolated: Self.violatesMonotonicity(seen)",
     "            monotonicityViolated: Self.violatesMonotonicity(Array(seen.reversed()))"),
]
