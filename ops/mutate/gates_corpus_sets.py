#!/usr/bin/env python3
"""The rule-SET half of the mutation corpus. The rest is ops/mutate/gates_corpus.py; the runner is gates.py.

Split out of gates_corpus.py when round 8 of PR #82 added the three widenings below and the single file would
have gone past the 300-line cap CLAUDE.md sets. The concern boundary is exact and mechanical: **every
mutation here is anchored on a SET LITERAL in Gates.swift** - `unpavedSurfaces`, `closedAccess`,
`refusableBarriers`, `refusedTracktypes`, `refusedSmoothness`, `refusedServiceValues` - and every mutation
anchored on a rule, a reason or the entry point stays in gates_corpus.py. `narrow the track gate to spare a
well-graded track` moved back there under the split for exactly that reason: it reads like a set mutation and
is anchored on the RULE.

There are no path constants here and that is deliberate. `set_mutations()` takes the `Gates.swift` path from
its caller, so this file cannot drift out of agreement with gates_corpus.py about where the subject lives -
a second copy of `ROOT / "Sources" / ...` is the kind of duplication that fixes one half of a move.

Each entry is `(name, file, old, new)` on the same contract as gates_corpus.py: `old` must appear verbatim in
the pristine file or the runner reports SKIP and FAILS the run, and anchors are code, never comments.
"""
from __future__ import annotations

# The rule sets, verbatim from Sources/ScenicKit/Gates/Gates.swift. Anchors, so they are the code's own text.
UNPAVED_SET = '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",'
CLOSED_SET = '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]'
BARRIER_SET = '    public static let refusableBarriers: Set<String> = ["gate"]'
TRACKTYPE_SET = '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]'
SMOOTHNESS_SET = '        "bad", "very_bad", "horrible", "very_horrible", "impassable",'
SERVICE_SET = '        "driveway", "parking_aisle", "drive-through", "emergency_access",'


def set_mutations(GATES):
    """Every mutation anchored on one of the six refused sets. `GATES` is the Gates.swift path."""
    return [
        ("drop compacted and fine_gravel from the unpaved set", GATES, UNPAVED_SET,
         '        "gravel", "dirt", "ground", "sand", "unpaved",'),

        ("call asphalt unpaved", GATES, UNPAVED_SET, UNPAVED_SET + ' "asphalt",'),

        # The widening direction, on values a "be thorough" edit actually reaches for. `asphalt` above was
        # covered by the four paved values the old allowed-side list happened to name; cobblestone and sett
        # were not, and a cobbled lane becoming a HARD SAFETY REFUSAL is the opposite of a scenic router's
        # job. Second review of PR #82.
        ("call cobblestone and sett unpaved, refusing a scenic cobbled lane", GATES, UNPAVED_SET,
         UNPAVED_SET + '\n        "cobblestone", "sett",'),

        # The same direction again, on three values the SIXTH review found no allowed-side pin named; all
        # three survived the whole suite with exit 0 and a control red. `GatesSetBoundaryTests` objects now.
        # It pins the plan's lists verbatim rather than calling any of the three widenings wrong: a widening
        # has to be a deliberate edit that turns a named test red, not a tidy-up that ships in silence.
        ("call wood and metal unpaved, refusing every planked or grid bridge deck", GATES, UNPAVED_SET,
         UNPAVED_SET + '\n        "wood", "metal",'),

        ("let destination-only access through", GATES, CLOSED_SET,
         '    public static let closedAccess: Set<String> = ["private", "no", "permit"]'),

        ("refuse permissive access", GATES, CLOSED_SET,
         '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination",\n'
         '                                                   "permissive"]'),

        ("refuse customers access, widening the closed set past the plan's four values", GATES, CLOSED_SET,
         '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination",\n'
         '                                                   "customers"]'),

        ("refuse a locked lift gate too, widening the barrier set past the plan's one value", GATES,
         BARRIER_SET, '    public static let refusableBarriers: Set<String> = ["gate", "lift_gate"]'),

        ("move the tracktype boundary, letting grade3 through", GATES, TRACKTYPE_SET,
         '    public static let refusedTracktypes: Set<String> = ["grade4", "grade5"]'),

        ("move the tracktype boundary the other way, refusing grade2", GATES, TRACKTYPE_SET,
         '    public static let refusedTracktypes: Set<String> = ["grade2", "grade3", "grade4", "grade5"]'),

        ("refuse intermediate smoothness, which the plan allows", GATES, SMOOTHNESS_SET,
         '        "intermediate", "bad", "very_bad", "horrible", "very_horrible", "impassable",'),

        ("let a merely bad road through", GATES, SMOOTHNESS_SET,
         '        "very_bad", "horrible", "very_horrible", "impassable",'),

        # `refusedServiceValues` was the one rule set with neither a member-by-member test nor a shrink
        # mutation, and the two members the old suite never named are exactly the two this drops. Added
        # for PR #82.
        ("shrink refusedServiceValues to the two values the old suite named", GATES, SERVICE_SET,
         '        "driveway", "parking_aisle",'),

        # --- the three WIDENINGS added in round 8 of PR #82, one per set the equality did not pin ---------
        #
        # `theRefusedSetsAreExactlyThePlansLists` used to pin three of the six sets while its display name,
        # its header and its own comment claimed all of them. agent/rv8b-pr82 widened `refusedServiceValues`
        # with `"bus"` and the whole suite stayed green - a hard safety gate widening in silence, with a
        # control red proving `highway=service` + `service=bus` really went from `.allowed` to
        # `.refused(.serviceWay)`. The equality now covers all six sets and these three mutations are what
        # keep that measured rather than asserted.
        #
        # The VALUES are chosen so that each one is caught by the equality ALONE. `GatesTests` enumerates
        # every value OSM defines for `tracktype` (grade1-5) and `smoothness` (excellent..impassable) on both
        # sides, so a widening inside those vocabularies is already caught by a behaviour test and would not
        # show whether the new pin does anything. `grade6` and `rough` are outside them - the shape a
        # defensive "just in case" widening actually takes - and `service` has no closed vocabulary at all.
        ("refuse a bus lane as a service way, the widening the eighth review got past the whole suite",
         GATES, SERVICE_SET, SERVICE_SET + ' "bus",'),

        ("widen refusedTracktypes with a grade OSM does not define, which no value test enumerates", GATES,
         TRACKTYPE_SET,
         '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5", "grade6"]'),

        ("widen refusedSmoothness with a value outside OSM's ordering, which no value test names", GATES,
         SMOOTHNESS_SET,
         '        "bad", "very_bad", "horrible", "very_horrible", "impassable", "rough",'),
    ]
