"""One concern: what `assemble.record_from_row` read off which producer, BEFORE anything became a rank.

WHY THIS FILE EXISTS. PR #102's review swapped two lines of `record_from_row` -
`elevation_gain=terrain.relief(profile)` and `relief=terrain.elevation_gain(profile)` - and all fifteen
tests of `test_assemble.py` passed while two scores moved. They passed because every assertion in that file
is made on the table, and by then `normalise_region` has replaced all five RANKED terms with their
population ranks. A rank keeps no trace of the number it came from: if both terms are ranked over the same
population, reading one off the other's producer is a permutation of two ladders, not a wrong number.

SO THE ASSERTIONS HERE ARE ON THE RAW RECORD, the one `record_from_row` returns before `assemble()` hands
the region to `normalise_region`. That is the last place `terrain.elevation_gain`'s own 121.0 exists.

WHERE THE LITERALS COME FROM. Each is one value on one NAMED way, derived once, outside the suite, and
typed in below with its arithmetic. No test here calls a producer to compute its own expectation - that
would assert the wiring against itself and pass under exactly the swap above. Ruling R8 (no hand-computed
SCORE for a ranked term) is not in the way: a producer's raw output is not a score, and the arithmetic for
gain and relief is addition and subtraction over eight numbers that are in the fixture.

THE FIXTURE'S OTHER HALF OF THE ANSWER. Two literals would not have been enough on their own: before ways
800000009 and 800000010 were added, four of the six ranked ways held the SAME rank in `elevation_gain` and
in `relief`, so the swap moved only two scores. The sawtooth and the long descent separate the two ladders
on every way in the population, and `test_the_gain_and_relief_ladders_are_not_one_ladder` keeps them apart.
"""
from __future__ import annotations

import inspect
import json
import math
import pathlib
import re

import pytest

from etl import assemble, score

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURE = HERE / "fixtures" / "assembly_fixture.json"
GATES_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"

MOTORWAY = 800000001
PRIVATE = 800000003
UNPAVED = 800000004
LOOP = 800000005
STRAIGHT = 800000006
SECONDARY = 800000007
UNSURVEYED = 800000008
NO_MOTOR_VEHICLE = 800000009
DESCENT = 800000010

DOCUMENT = json.loads(FIXTURE.read_text(encoding="utf-8"))
RAW = {row["way_id"]: assemble.record_from_row(row, DOCUMENT["byways"]) for row in DOCUMENT["ways"]}
TABLE = {row["way_id"]: row for row in assemble.assemble(DOCUMENT)}

# `terrain.elevation_gain` sums the positive steps of the profile that exceed NOISE_FLOOR_M = 0.5 (strictly
# greater); `terrain.relief` is max - min, because eight samples at a 25 m step are one 1 km window. Both
# hand-computed from the fixture's own `elevation_profile`, one way per line:
#   800000007 [300,318,341,329,356,378,361,392] +18 +23 -12 +27 +22 -17 +31
#             gain 18+23+27+22+31 = 121.0                    relief 392 - 300 =  92.0
#   800000009 [100,112,100,112,100,112,100,112] +12 -12 +12 -12 +12 -12 +12
#             gain 12+12+12+12   =  48.0                     relief 112 - 100 =  12.0
#   800000010 [400,380,355,358,330,310,290,250] -20 -25  +3 -28 -20 -20 -40
#             gain 3             =   3.0  (one step up)      relief 400 - 250 = 150.0
#   800000006 [60,60.5,...,63.5] seven steps of exactly +0.5, none of them ABOVE the 0.5 floor
#             gain               =   0.0                     relief 63.5 - 60 =   3.5
RAW_ELEVATION_GAIN = {SECONDARY: 121.0, NO_MOTOR_VEHICLE: 48.0, DESCENT: 3.0, STRAIGHT: 0.0}
RAW_RELIEF = {SECONDARY: 92.0, NO_MOTOR_VEHICLE: 12.0, DESCENT: 150.0, STRAIGHT: 3.5}

# `curvature.way_curvature(<way 800000007's seven coordinates>, 800000007)` -> 476.08176703651884, the one
# call, made once outside this suite and recorded here. Its arithmetic, from the same call's segments: the
# way is six segments, each of them one arm of the same regular zig-zag, so each carries a circumcircle
# radius of ~55.2766 m. 55.2766 is under 60 and not under 30, which is band 3 of curvature.LEVELS, weight
# 1.6. Four segments measure 49.591790115721246 m and two 49.59197196746963 m -
#   4 * 49.591790115721246 + 2 * 49.59197196746963 = 297.55110439782424 m of way
#   297.55110439782424 * 1.6                       = 476.0817670365188
# and the last digit of the recorded value is the order the six products are summed in, not a disagreement.
SECONDARY_CURVATURE = 476.08176703651884

# `furniture.furniture_per_km` is nodes / km and nothing else. Way 800000005 carries three furniture nodes -
# `traffic_calming=table`, `highway=crossing`, `highway=street_lamp`, all three in `furniture.py`'s sets -
# over `snap.length_m` of its seven coordinates, 132.14281164945845 m, recorded once from that call:
#   3 / (132.14281164945845 / 1000) = 22.702710518664
LOOP_LENGTH_M = 132.14281164945845
LOOP_FURNITURE_NODES = 3

# The two fields `record_from_row` reads as typed literals when the row carries them (LITERAL_FIELDS).
READ_TUNNEL_METERS = {SECONDARY: 120.0}
READ_MOTORWAY_DISTANCE_M = {UNSURVEYED: 90.0}
# The rows that omit BOTH, and so must take score.py's own defaults.
OMITS_BOTH = (MOTORWAY, PRIVATE, UNPAVED, LOOP, NO_MOTOR_VEHICLE, DESCENT)

# The mid-rank ladder over the population of eight - ten ways less the two zero classes, which are EXCLUDED
# rather than ranked (normalise.py:33): (i + 0.5*1)/8 for i in 0..7.
RANK_LADDER = tuple((index + 0.5) / 8 for index in range(8))
# Where each way sits on it, per term, by sorting the raw values above and in the fixture:
#   gain    0.0(006) 3.0(010) 4.0(005) 48.0(009) 51.0(003) 67.0(008) 84.0(004) 121.0(007)
#   relief  2.0(005) 3.5(006) 12.0(009) 51.0(003) 53.0(008) 67.0(004) 92.0(007) 150.0(010)
GAIN_ORDER = (STRAIGHT, DESCENT, LOOP, NO_MOTOR_VEHICLE, PRIVATE, UNSURVEYED, UNPAVED, SECONDARY)
RELIEF_ORDER = (LOOP, STRAIGHT, NO_MOTOR_VEHICLE, PRIVATE, UNSURVEYED, UNPAVED, SECONDARY, DESCENT)

# `Gates.verdict`'s nine refusal branches, by the tag key each one is written on (Gates.swift:154-172).
# Four are ported into `assemble.gate_reason`; the five that are not are named in `assemble`'s docstring.
PORTED_GATE_KEYS = ("surface", "highway", "access", "motor_vehicle")
UNPORTED_GATE_RULES = 5


def _swift_verdict_branches() -> int:
    """How many branches of `Gates.verdict` refuse, counted in the CODE and not in a doc comment."""
    lines = GATES_SWIFT.read_text(encoding="utf-8").splitlines()
    code = [line for line in lines if not line.lstrip().startswith("//")]
    return sum(line.count("return .refused(") for line in code)


def _swift_set(name: str) -> set:
    match = re.search(r"let %s: Set<String> = \[(.*?)\]" % name,
                      GATES_SWIFT.read_text(encoding="utf-8"), re.S)
    assert match, "%s is not declared in %s" % (name, GATES_SWIFT)
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def test_the_ranked_terms_are_the_raw_numbers_their_producers_returned():
    """B1 of PR #102's review: the pin the swap survived. Every value here is pre-`normalise_region`."""
    for way_id, expected in RAW_ELEVATION_GAIN.items():
        assert RAW[way_id].elevation_gain == expected, (
            "way %d: elevation_gain is %r, and terrain.elevation_gain over its profile is %r - a term read "
            "off the wrong producer is invisible one rank later" % (way_id, RAW[way_id].elevation_gain, expected))
    for way_id, expected in RAW_RELIEF.items():
        assert RAW[way_id].relief == expected, (
            "way %d: relief is %r, terrain.relief says %r" % (way_id, RAW[way_id].relief, expected))
    assert RAW[SECONDARY].curvature == pytest.approx(SECONDARY_CURVATURE, rel=1e-12), RAW[SECONDARY].curvature
    assert RAW[LOOP].furniture == pytest.approx(
        LOOP_FURNITURE_NODES / (LOOP_LENGTH_M / 1000.0), rel=1e-12), RAW[LOOP].furniture
    # sinuosity is the fifth ranked term and the only one READ rather than produced (LITERAL_FIELDS).
    assert RAW[SECONDARY].sinuosity == 1.8, RAW[SECONDARY].sinuosity


def test_the_gain_and_relief_ladders_are_not_one_ladder():
    """RECORDABLE 1 of PR #102's review: the fixture, not only the pin above, has to separate the two.

    If every way held the same rank in both terms, the swap in B1 would be a permutation of one ladder onto
    itself and no SCORE would move - which is how a fixture stops being evidence without anything failing.
    Asserted as the two orders, so a red run says which way moved rather than that a count changed.
    """
    for order, term in ((GAIN_ORDER, "elevation_gain"), (RELIEF_ORDER, "relief")):
        got = {way_id: TABLE[way_id]["terms"][term] for way_id in order}
        assert got == pytest.approx(dict(zip(order, RANK_LADDER)), abs=1e-12), (term, got)
    shared = [way_id for way_id in GAIN_ORDER
              if TABLE[way_id]["terms"]["elevation_gain"] == TABLE[way_id]["terms"]["relief"]]
    assert shared == [], "these ways hold one rank in both terms, so the two ladders overlap there: %s" % shared


def test_the_restated_distance_defaults_are_score_pys_own():
    """B2, first half: the two constants say they restate `score.score`'s defaults. Read them and compare.

    Anchored on the signature - `inspect` over the function object - because the claim is about what
    `score.score` does when the argument is left out, and a copied literal drifting from it is exactly the
    failure this closes.
    """
    defaults = inspect.signature(score.score).parameters
    assert assemble.DEFAULT_TUNNEL_M == defaults["tunnel_meters"].default
    assert assemble.DEFAULT_MOTORWAY_DISTANCE_M == defaults["meters_to_nearest_motorway"].default
    assert assemble.DEFAULT_TUNNEL_M == 0.0
    assert assemble.DEFAULT_MOTORWAY_DISTANCE_M == math.inf


def test_a_row_that_omits_a_distance_field_takes_the_restated_default():
    """B2, second half: six of the ten rows omit both fields, and `= 0.0` for the motorway distance would
    put all six inside `score.MOTORWAY_PROXIMITY_M` and multiply them down with the suite green."""
    for way_id in OMITS_BOTH:
        record = RAW[way_id]
        assert record.meters_to_nearest_motorway == math.inf, (
            "way %d omits meters_to_nearest_motorway and holds %r: a finite default is a claim that every "
            "unmeasured way is beside a freeway" % (way_id, record.meters_to_nearest_motorway))
        assert record.tunnel_meters == 0.0, (way_id, record.tunnel_meters)
    assert RAW[STRAIGHT].meters_to_nearest_motorway == math.inf  # written out in the row, as "Infinity"


def test_the_distance_literals_a_row_does_carry_reach_the_record_unchanged():
    """B2, third half: the default must not swallow a value that IS in the row."""
    for way_id, expected in READ_TUNNEL_METERS.items():
        assert RAW[way_id].tunnel_meters == expected, (way_id, RAW[way_id].tunnel_meters)
    for way_id, expected in READ_MOTORWAY_DISTANCE_M.items():
        assert RAW[way_id].meters_to_nearest_motorway == expected, (
            way_id, RAW[way_id].meters_to_nearest_motorway)


def test_motor_vehicle_no_is_refused_as_no_access_the_way_gates_swift_refuses_it():
    """B3: `Gates.swift:161` is the second half of the rule `GateReason.swift:31` documents -
    "`access` forbids the public, or `motor_vehicle = no`" - and only the first half was ported."""
    tags = {"highway": "residential", "motor_vehicle": "no", "surface": "asphalt"}
    assert assemble.gate_reason(tags) == assemble.GATE_NO_ACCESS, assemble.gate_reason(tags)
    # And on a real row of the region, so the gate reaches the table and the count line, not only the rule.
    assert TABLE[NO_MOTOR_VEHICLE]["gate_reason"] == assemble.GATE_NO_ACCESS
    assert TABLE[NO_MOTOR_VEHICLE]["score"] == assemble.GATE_SCORE
    # `motor_vehicle` on any other value is not a refusal: positive evidence only, as everywhere else here.
    assert assemble.gate_reason({"highway": "residential", "motor_vehicle": "yes"}) is None
    assert assemble.gate_reason({"highway": "residential", "motor_vehicle": "destination"}) is None


def test_the_unported_gate_rules_are_counted_against_gates_verdict_and_not_described():
    """B3's second half: "five further rules" was written when four of them had no name here and one of
    them, `motor_vehicle=no`, was missing from the enumeration entirely. Count the branches instead."""
    branches = _swift_verdict_branches()
    assert branches == 9, "Gates.verdict now has %d refusal branches, not 9" % branches
    assert len(PORTED_GATE_KEYS) + UNPORTED_GATE_RULES == branches
    assert set(PORTED_GATE_KEYS) <= _swift_set("consideredTagKeys"), sorted(PORTED_GATE_KEYS)
    assert assemble.gate_reason({"highway": "track"}) == assemble.GATE_TRACK
    # The five that are NOT ported, one row each, stated as the behaviour that follows from not porting
    # them: allowed here, refused by ScenicKit. This is the delta the Log's dated correction names, and it
    # is asserted rather than described so that porting one of them without moving the count goes red.
    for tags in ({"highway": "unclassified", "tracktype": "grade4"},
                 {"highway": "residential", "smoothness": "bad"},
                 {"highway": "residential", "barrier": "gate", "locked": "yes"},
                 {"highway": "residential", "ford": "yes"},
                 {"highway": "service", "service": "driveway"}):
        assert assemble.gate_reason(tags) is None, tags
