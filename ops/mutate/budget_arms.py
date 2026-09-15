"""The two arms of ops/mutate/budget.py that must go MISSED, and the floor under the second one.

Split out of budget_mutations.py at the 300-line cap when the third review's two findings were added to
MUTATIONS. The boundary is not a line number: budget_mutations.py holds the mutations that must be CAUGHT by
a named test, and this file holds the two arms asserted the other way round - a catch here is the failure.

KNOWN_MISSED: a gap admitted on purpose. The arm fails if an entry stops being MISSED, because a gap that
closed is news and belongs in MUTATIONS.

EQUIVALENT: a mutation that cannot change behaviour. A catch here means a test has an opinion about how the
code is WRITTEN rather than what it DOES, which is a test that will break on an honest refactor.

MIN_EQUIVALENT lives here, next to the list it counts, and is the EXACT length of it. It used to be 1
against 4 entries, with nothing said about that in the Log - so three of the four could be deleted and the
floor stayed green, which is the same "documented to refuse what it does not refuse" defect this harness
keeps being blocked for. KNOWN_MISSED has no floor and needs none: empty is the honest state there, and
`len(KNOWN_MISSED)` is asserted by its own arm.
"""
from __future__ import annotations

from budget_mutations import SRC

# Mutations this suite is KNOWN not to catch, asserted the other way round: the arm FAILS if one starts
# being MISSED no longer, because a gap that closed should move up into MUTATIONS.
#
# EMPTY, and that emptiness is a claim rather than an oversight. The one entry it ever held - the
# `max(1, ...)` clamp - justified itself with "No behaviour to assert; the clamp is defensive", and the
# second review showed that reason was false: `maxEvaluations` is public and reads 1 pristine, -5 mutated.
# One assertion killed it, so it is a MUTATION now. An entry here claims no assertion can kill this
# mutation; if that reason is wrong, the arm records a closable gap as a feature, which is worse than having
# no arm at all. Every entry added here has to survive that question.
KNOWN_MISSED = []

# Cannot change behaviour, so anything but MISSED is a FAILURE.
#
# The last three survived the second fix pass's own attack, and each was then compiled STANDALONE, pristine
# against mutant, over 5891 cases covering every field of BudgetOutcome, the search's own cap and ceiling,
# each error's rendered text, and the exact sequence of lambdas the router is asked for. All three came back
# byte-identical - which is what "equivalent" has to mean here, and is the reason they are asserted MISSED
# rather than quietly dropped from the report. Each also has a REASON below, because a fingerprint that
# happened to match over one sweep is evidence and not a proof.
#
# The third review offered a fourth - `lambda > best!.lambda` -> `>=` in the tie-break, byte-identical over
# 17058 cases because the bisection never asks the same lambda twice - and correctly refused to bank it as a
# finding. It is not added here: the reason it is equivalent is a property of the CALLER (the bisection's
# lambda sequence) rather than of the helper, so a future change to the bracket could make it live, and an
# EQUIVALENT entry whose reason can expire is an arm that will one day fail for the right reason with the
# wrong message. Recorded in the task Log instead.
#
# The fourth review pushed on that distinction and it is a difference of DEGREE, which is worth saying here
# rather than leaving the sentence above to read as a bright line: the tolerance entry below also rests on
# two constants and its own comment says what a catch there would mean. What separates them is how far the
# reason lives from the mutated line and how quietly it can go stale - a constant changing is a one-line
# diff next to the entry, a bracket that starts revisiting a lambda is not - and that is a judgement, not a
# rule. The omission still costs nothing; the entry would.
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

# A LITERAL, never `len(EQUIVALENT)`: a floor computed from the list it guards moves down with the list and
# refuses nothing, which is this repository's signature defect wearing the clothes of a fix.
MIN_EQUIVALENT = 4
