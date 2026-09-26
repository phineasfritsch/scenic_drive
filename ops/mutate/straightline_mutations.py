"""The mutation population for Sources/Handoff/StraightLineDistance.swift. The runner is straightline.py.

Split from the runner the way scenic_tags_mutations.py is split from scenic_tags.py and
geometry_mutations.py from geometry.py: the runner is the protocol - what a verdict is and what refuses -
and this file is the evidence it runs over. ops/mutate/handoff.py, which measures the other two files in
this target, is 603 lines in one piece; CLAUDE.md caps a file at 300, so a second table was never going in
there.

## The subject, and the two files that are NOT the subject

`StraightLineDistance.swift` is what this population measures and the only path in the runner's
`SUBJECT_MODULES`. But the number it computes rests on two files it does not own, and a mutation harness
that cannot reach them measures the module's plumbing and not its arithmetic:

  * `Sources/ScenicKit/Geo/Geo.swift` holds the earth radius and the haversine. A radius 0.1% out and a
    flat equirectangular formula are the two ways the metres can be wrong while every line of the subject
    stays as written.
  * `Sources/Handoff/SkylineRoute.swift` holds the pins. "A pin moved more than a kilometre" is the rule
    `StraightLineDistanceTests` was written for, and the only place to move one is here.

They are DEPENDENCIES: mutated, reported, and deliberately NOT declared as subjects, because declaring
`Geo.swift` would claim a population over `initialBearingDegrees` and `Double.radians`, which nothing here
mutates. A stated subject wider than the measured one is the defect handoff.py's docstring was written
against.

## Each entry, and what `killers` is for

`(name, path, old, new, killers)`. `old` must appear VERBATIM in the pristine file or the run reports SKIP
and FAILS - a stale anchor is a harness gone quietly blind. No anchor is a comment: CLAUDE.md forbids it
and comments get stripped. `killers` names the tests that MUST go red, by the display name Swift Testing
prints; a mutation caught by some OTHER test is reported as CAUGHT BUT NOT BY THE TEST THAT NAMES IT and
fails the run, and an EMPTY `killers` list is refused by the floor before anything is built (agent/rv1-pr107
found that `len(red) != len(killers)` is satisfied vacuously by `0 == 0`).

## Three of these were survivors, and the entries were not weakened

Measured against the suite as T-0199 found it, not assumed:

  * `+1% mile constant` took the card from 69.760 mi to 69.070 mi, still 69, and the 1.988-mile synthetic
    to 1.969, still 1;
  * `miles from the floored kilometres` gives 112 * 0.621371 = 69.59 -> 69 on Skyline, 47 * 0.621371 =
    29.20 -> 29 on the LA chain, and 3.107 -> 3 on the 1.99-mile synthetic;
  * `flat equirectangular` totals 112_268.146 m against the haversine's 112_268.093 m - 0.053 m, inside
    the one-metre band `straightLineMeters` pins.

The rule is that a survivor buys a test, not a softer entry. `aLongEastWestLegPinsTheFormulaAndTheMileConstant`
and `theMilesComeFromTheMetresAndNotFromTheFlooredKilometres` are those tests, and they are the `killers` of
entries 7, 8, 9 and 10 below.

## The eleventh entry, and the one mutant no test at that entry point can kill

T-0199's pre-review mutant pass ran an eleventh mutation that is not a variant of any entry above: the same
double floor placed at the ENTRY POINT, `wholeMiles(for: drive)` taken from `wholeKilometers(for: drive)`,
and the whole suite stayed green. Two separate facts came out of that, and they are filed separately.

  * The entry point had NO mutation at all - entries 1-10 edit a helper or a dependency, and
    `wholeMiles(for:)` is the symbol `DriveFacts` renders. Entry 11 below mutates it.
  * The surviving mutant itself is in EQUIVALENT, with the enumeration of the entry point's whole input
    domain as its witness, because `HandoffDrive` is a closed two-case enum and both shipped drives floor
    to the same mile either way. It is NOT filed in MUTATIONS with a softened killer: there is no input at
    that entry point to name a killer over, which is a different thing from a test nobody wrote.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The declared subject. Its basename is what ops/lib/check-mutate-population.py looks for in this family's
# code when it asks whether a declaration is actually targeted.
SUBJECT = ROOT / "Sources" / "Handoff" / "StraightLineDistance.swift"
# Dependencies: mutated here, never declared as subjects. See the docstring.
GEO = ROOT / "Sources" / "ScenicKit" / "Geo" / "Geo.swift"
SKYLINE = ROOT / "Sources" / "Handoff" / "SkylineRoute.swift"
MUTATED_FILES = (SUBJECT, GEO, SKYLINE)

TEST_DIR = ROOT / "Tests" / "HandoffTests"

# Anchors, spelled once so an entry and its neighbour cannot drift apart.
RADIUS = "public static let earthRadiusMeters: Double = 6_371_008.8"
HAVERSINE = ("        let h = sin(dLat / 2) * sin(dLat / 2) + cos(lat1) * cos(lat2)"
             " * sin(dLon / 2) * sin(dLon / 2)\n"
             "        return 2 * earthRadiusMeters * asin(min(1, sqrt(h)))")
KM_FLOOR = "Int((meters(through: points) / 1_000).rounded(.down))"
MI_FLOOR = "Int((meters(through: points) / 1_609.344).rounded(.down))"
CHAIN = ("    public static let skylineRoutePoints: [Coordinate] = "
         "SkylineRoute.waypoints + [SkylineRoute.destination]")
PIN_ONE = "Coordinate(latitude: 37.70526, longitude: -122.47165)"
TWO_POINT_GUARD = "guard points.count > 1 else { return 0 }"
# The ENTRY POINT production runs: FeatureScenicHome/DriveFacts.swift:45 calls `wholeMiles(for:)`, never
# the helper under it. The body is one line and this spelling of it occurs once; the doc block above names
# `drive.chain` in prose, and CLAUDE.md forbids anchoring on a comment in any case.
ENTRY_MILES = "        wholeMiles(through: drive.chain)"

# Killer display names, spelled once each. These are the strings inside @Test("...").
CARD_KM = "the whole-kilometre figure is the number the card shows"
SCREEN_MI = "the whole-mile figure is the number the screen renders, from the same metres"
KM_FLOORED = "the figure is floored, not rounded: 1999 m of chain is 1 km and never 2"
MI_FLOORED = "the miles are floored too: 1.99 miles of chain is 1 mile and never 2"
CHAIN_IS_PINS = "the chain is the shipped pins in driving order, then the destination"
PER_POINT = "every point is within a kilometre of where this suite thinks it is"
LONG_LEG = "a 1,065 km east-west leg pins the formula and the mile constant"
NOT_FROM_KM = "the miles come from the metres, not from the floored kilometres"
OWN_CHAIN = "every drive's miles are that drive's own chain, floored from that drive's metres"
LA_SCREEN_MI = "the whole-mile figure is the number the LA drive renders, from the same metres"

MUTATIONS = [
    # 1-2. The radius, both directions. 6_371_008.8 * 1.001 and * 0.999. The card's 112_268.093 m moves to
    # 112_380.36 m and 112_155.83 m, and the one-metre band is what notices; the floored 112 km does not.
    ("the earth radius 0.1% too large", GEO, RADIUS,
     "public static let earthRadiusMeters: Double = 6_377_379.8088", [CARD_KM]),

    ("the earth radius 0.1% too small", GEO, RADIUS,
     "public static let earthRadiusMeters: Double = 6_364_637.7912", [CARD_KM]),

    # 3-4. The floor, in both renderings. The product rule is that the one direction a number on this
    # screen may be wrong in is the modest one, so .rounded() is the defect and not a refactor.
    ("the kilometre figure rounds to nearest instead of flooring", SUBJECT, KM_FLOOR,
     "Int((meters(through: points) / 1_000).rounded())", [KM_FLOORED]),

    ("the mile figure rounds to nearest instead of flooring", SUBJECT, MI_FLOOR,
     "Int((meters(through: points) / 1_609.344).rounded())", [MI_FLOORED, SCREEN_MI]),

    # 5. The chain stops at the last pin, so the leg into San Francisco is not in the number.
    ("the destination falls off the end of the shipped chain", SUBJECT, CHAIN,
     "    public static let skylineRoutePoints: [Coordinate] = SkylineRoute.waypoints", [CHAIN_IS_PINS]),

    # 6. Pin 1 moved 1667.9 m north of the I-280 on-ramp - past the kilometre the per-point bound allows,
    # and the reason that bound is written per point instead of on the total.
    ("pin 1 moved 1.7 km off the I-280 on-ramp", SKYLINE, PIN_ONE,
     "Coordinate(latitude: 37.72026, longitude: -122.47165)", [PER_POINT]),

    # 7-8. The metres-to-miles constant, 1% each way. 1_609.344 is the international mile by definition.
    # The +1% arm is the survivor: on the shipped chain and on the 1.99-mile synthetic it changes nothing.
    ("the metres-to-miles constant 1% too large", SUBJECT, MI_FLOOR,
     "Int((meters(through: points) / 1_625.43744).rounded(.down))", [LONG_LEG]),

    ("the metres-to-miles constant 1% too small", SUBJECT, MI_FLOOR,
     "Int((meters(through: points) / 1_593.25056).rounded(.down))", [LONG_LEG, SCREEN_MI]),

    # 9. ONE COMPUTATION, TWO RENDERINGS, undone: the miles converted from the floored kilometres, which
    # floors twice and loses up to a mile. The type note claims this is not done; nothing measured it.
    ("the miles derived from the floored kilometres instead of the metres", SUBJECT, MI_FLOOR,
     "Int((Double(wholeKilometers(through: points)) * 0.621371).rounded(.down))", [NOT_FROM_KM]),

    # 10. A flat equirectangular formula on the same radius. Not an equivalent mutant: 707.257 m and one
    # whole mile on a 1,065 km east-west leg, which is what LONG_LEG measures.
    ("the flat equirectangular formula on the same radius", GEO, HAVERSINE,
     "        let x = dLon * cos((lat1 + lat2) / 2)\n"
     "        return earthRadiusMeters * sqrt(x * x + dLat * dLat)", [LONG_LEG]),

    # 11. THE ENTRY POINT, which entries 1-10 never touched: every one of them edits a helper or a
    # dependency, and `wholeMiles(for:)` is the symbol production calls. The mutant hands every drive the
    # Skyline chain - the drift T-0202 was filed for, a figure that names one drive while the tap takes
    # another - so the LA screen renders 69 miles of somebody else's drive.
    ("the entry point measures the Skyline chain whatever drive it is handed", SUBJECT, ENTRY_MILES,
     "        wholeMiles(through: HandoffDrive.skyline.chain)", [OWN_CHAIN, LA_SCREEN_MI]),
]

# Mutants that provably cannot change behaviour, asserted the other way round: anything but MISSED fails.
# `(name, path, old, new, witness)`. The witness is the proof, in the entry - CLAUDE.md, Verification: an
# "equivalent mutant" ruling is an EQUIVALENT entry with a witness, never prose in a task file.
EQUIVALENT = [
    ("the two-point guard spelled >= 2 instead of > 1", SUBJECT, TWO_POINT_GUARD,
     "guard points.count >= 2 else { return 0 }",
     "`points.count` is an Int and over the integers `n > 1` and `n >= 2` are the same predicate, for "
     "every n including the negatives Array.count cannot produce. There is no chain, shipped or "
     "synthetic, that the two spellings disagree about, so there is no input to write a test on. The "
     "guard's behaviour is pinned instead by the empty-and-single-point assertions in "
     "theFigureIsFlooredAndNeverRoundedUp and theMilesAreFlooredAndNeverRoundedUp."),

    ("the entry point floored twice: the miles taken from that drive's floored kilometres", SUBJECT,
     ENTRY_MILES,
     "        Int((Double(wholeKilometers(for: drive)) * 0.621371).rounded(.down))",
     "`wholeMiles(for:)` ranges over `HandoffDrive`, a closed three-case enum whose chains are `static "
     "let`s on the route types, so the domain this mutant can be fed is exhaustible and was exhausted: "
     "Skyline 112_268.093 m -> 69.7602 mi -> 69, while floor(112.268 km) = 112 -> 69.5936 -> 69; LA "
     "47_445.124 m -> 29.4810 -> 29, while 47 -> 29.2044 -> 29; Saddle Peak (T-0236) 17_362.496 m -> "
     "10.7885 -> 10, while 17 -> 10.5633 -> 10. All three cases agree, so there is no input "
     "to write a killer over - not a weaker test, none. The HELPER form of the same double floor is "
     "MUTATIONS entry 9, killed by `the miles come from the metres, not from the floored kilometres` "
     "over a 4_999.331 m chain the test constructs, and that construction is exactly what this entry "
     "point does not accept. The equivalence is the DOMAIN's and not the arithmetic's, so it is not "
     "permanent and is not left unwatched: 268.1 m off the Skyline chain would put floor(km) at 111 -> "
     "68.97 -> 68 against the metres' 69, and `every drive's miles are that drive's own chain, floored "
     "from that drive's metres` ranges over allCases comparing this entry point with each drive's own "
     "metres - so the day a pin moves that far or a third drive lands, this entry stops reporting MISSED "
     "and the EQUIVALENT arm FAILS the run until it is ruled again."),
]

# The floor. THE REAL COUNT, not a round number under it: gates.py records a floor of 18 against a
# population of 21 letting a reviewer delete three mutations and still read a clean sheet. Adding a
# mutation means editing this number, which lives in the same file so the diff shows both halves.
MIN_MUTATIONS = 11
MIN_EQUIVALENT = 2
# Not a completeness floor: the suite may split. It refuses one thing - a glob that matched nothing, which
# would make --prove-vacuity empty nothing and prove nothing.
MIN_TEST_FILES = 1
