"""The arm of ops/mutate/geometry.py asserted the other way round: mutations that CANNOT change behaviour.

A catch here means a test has an opinion about how the code is WRITTEN rather than what it DOES, which is a
test that breaks on an honest refactor. Split out of geometry_mutations.py along the boundary budget_arms.py
uses - that file holds what must be CAUGHT, this one what must go MISSED - and MIN_EQUIVALENT lives next to
the list it counts.

EVERY ENTRY CARRIES A REASON AND A WITNESS, and the witness is not prose. CLAUDE.md: *an "equivalent mutant"
ruling is an EQUIVALENT entry with a witness, never prose in a task file.* The witness is a FINGERPRINT -
ops/mutate/geometry_probe.py's digest over every answer `sinuosity` and `proximity` give for every case in
every geometry fixture - taken over the pristine copy and again over the mutated copy by the runner, on
every run. An entry passes only if BOTH hold: the digests are byte-identical, and no named test went red.
Either one alone is weak. Identical digests over a degenerate fixture population is exactly how four review
rounds of PR #94 were bought; "no test objected" is the definition of a survivor, not of an equivalence.

THE WORKED NON-EXAMPLE, and the reason this arm exists in this shape. Review round 3 of PR #94 ruled one
mutant of `line_distance_m` EQUIVALENT and wrote it into the task file as settled fact: drop the segment
pairs interior to both polylines, `... for i in range(n) for j in range(m) if i in (0, n - 1) or j in
(0, m - 1)`. The argument had two clauses. (a) "the minimum distance between two disjoint segments is
attained at an endpoint of at least one of them" - TRUE in the plane. (b) "every interior segment's
endpoints belong to the first or the last segment too" - FALSE from five nodes on: for n0..n4 the node n2 is
an endpoint of s1 and s2 and of neither s0 nor s3. The ruling survived because the fixtures were 3 nodes
against 2 and one 4-node way against a 2-node stub, so clause (b) happened to hold everywhere it was
measured. It is a MUTATION now, in the interior-interior class, and `python ops/mutate/geometry.py
--non-example` runs it through this arm's own test and prints the two digests DIFFERING, with the case and
the two numbers - 99.4860 m against 406.4842 m, which is score.MOTORWAY_PROXIMITY_M's x0.7 lost and a
scenic score 1/0.7 too high. A prose ruling cannot be re-run; this one refutes itself on every run.

WHAT AN ENTRY MAY NOT REST ON. budget_arms.py declines an entry whose reason is a property of the CALLER
rather than of the mutated code, because such a reason expires silently. Every reason below is a property of
the mutated expression itself - the symmetry of a function, the truncation rule of `zip`, the commutativity
of `min` over floats, the order of pure conjuncts - and each is checkable by reading the four lines around
the anchor. KNOWN_MISSED has no counterpart here and needs none: this population has no admitted gaps, and
an entry claiming "no assertion can kill this" would have to survive the question budget_arms.py asks of it.
"""
from __future__ import annotations

from geometry_mutations import NEAREST, PAIR_LOOP, PROX, SNAP

# (label, rel, old, new, reason). The witness is computed, not written down: see the docstring.
EQUIVALENT = [
    ("measure the candidate against the way instead of the way against the candidate", PROX, PAIR_LOOP,
     PAIR_LOOP.replace("segment_distance_m(a, b, c, d)", "segment_distance_m(c, d, a, b)"),
     "segment_distance_m is symmetric in its two segments BY CONSTRUCTION, not by coincidence: it returns "
     "min over the same four point-to-segment terms with the pairs exchanged, and _crosses swaps (d1, d2) "
     "with (d3, d4) in a conjunction that is symmetric in those two halves. Both of those are in the four "
     "lines above the anchor."),

    ("snap.length_m pairs the coordinates with an explicit slice instead of relying on zip", SNAP,
     "    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(line, line[1:]))",
     "    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(line[:-1], line[1:]))",
     "zip stops at the shorter argument, so zip(line, line[1:]) and zip(line[:-1], line[1:]) yield the "
     "same pairs for every length including 0 and 1. The NEAR MISS is in MUTATIONS one class away: "
     "zip(line, line[1:-1]) drops the last segment and is caught by name."),

    ("the candidate distance is the first argument of min rather than the second", PROX, NEAREST,
     "        nearest = min(line_distance_m(coords, motorway), nearest)",
     "min is commutative over the floats this loop produces. The accumulator starts at math.inf and "
     "line_distance_m returns a non-NaN float or raises, so the one case where min's argument order is "
     "observable - a NaN, which min returns whenever it is seen first - cannot arise."),

    ("_crosses tests the degeneracies before the sides rather than after", PROX,
     "    return ((d1 > 0) != (d2 > 0) and d1 != 0 and d2 != 0\n"
     "            and (d3 > 0) != (d4 > 0) and d3 != 0 and d4 != 0)",
     "    return (d1 != 0 and d2 != 0 and (d1 > 0) != (d2 > 0)\n"
     "            and d3 != 0 and d4 != 0 and (d3 > 0) != (d4 > 0))",
     "All six conjuncts are pure comparisons of four floats already computed above the anchor: no call, no "
     "side effect, nothing that can raise. Reordering a conjunction of total pure terms changes what is "
     "evaluated, never what it evaluates to."),
]

# A LITERAL and the EXACT length of the list above, for the reason MIN_MUTATIONS is one: a floor of 1
# against 4 entries - which is what budget_arms.py carried until the review of PR #73 - lets three quarters
# of an arm be deleted with every gate still green.
MIN_EQUIVALENT = 4
