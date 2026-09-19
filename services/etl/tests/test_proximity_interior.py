"""One concern: the nearest approach of two polylines can need a pair of segments INTERIOR TO BOTH of them.

THE HOLE THIS FILE EXISTS FOR, found by review round 3 in the round-3 record itself. The round-3 entry
ruled one mutant of `line_distance_m` EQUIVALENT and wrote that under STILL OPEN as settled fact - dropping
the interior-interior segment pairs, `... for i in range(n) for j in range(m) if i in (0, n-1) or j in
(0, m-1)`. The argument had two clauses. (a) "the minimum distance between two disjoint segments is
attained at an endpoint of at least one of them" is TRUE in the plane. (b) "every interior segment's
endpoints belong to the first or the last segment too" is FALSE from five nodes on: for n0..n4 the node n2
is an endpoint of s1 and s2 and of neither s0 nor s3. So when the nearest approach runs from such a node to
a segment interior to the other polyline, the value is computed only in the dropped cells and no retained
pair reproduces it. The mutant is equivalent only when ONE of the two polylines has at most four nodes,
which is exactly the shape of every case both fixtures carried: 3 nodes against 2, and one 4-node way
against a 2-node stub. Applied alone at c0dfe1a it left `130 passed` and the whole `602 passed` green.

In production this is the NORMAL case, not a corner: a real way and a real motorway both carry dozens of
nodes and run past each other, so their nearest approach is interior-interior essentially always. The cost
is the same one round 2 blocked on - `meters_to_nearest_motorway` answering 406.4842 m where the truth is
99.4860 m, which is score.MOTORWAY_PROXIMITY_M's x0.7 lost and a scenic score 1/0.7 = 43% too high.

`TestInteriorPairShape` is the structural guard, and it is a DIFFERENT question from the one
`test_proximity_bends.py::TestFixtureShape` asks: that one asks whether a geometry bends, this one asks
whether any case's nearest approach is attained at a pair of segments interior to both polylines. It walks
the per-pair matrix with the flat segment-to-segment metric written out below - never `proximity`'s - so
the guard does not lean on the module it guards, and it fails SAFE: on the fixtures as they stood at
c0dfe1a it is red.

Expected values are typed out in `fixtures/geometry_bends_fixture.json` from the arithmetic in the case's
`workings` field, which names the two minimum cells of the matrix.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from etl import proximity, score

FIXTURES = Path(__file__).parent / "fixtures"
BENDS = json.loads((FIXTURES / "geometry_bends_fixture.json").read_text())
TERMS = json.loads((FIXTURES / "geometry_terms_fixture.json").read_text())

INTERIOR_CASE_NAME = "nearest_approach_interior_to_both_polylines"


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case[key]]


def motorways_of(case):
    return [[(lat, lon) for lat, lon in line] for line in case["motorways"]]


def interior_case():
    """The one case this file is about, looked up by name so a fixture that loses it fails HERE and says so
    rather than raising an index error three assertions later."""
    named = [c for c in BENDS["motorway_cases"] if c["name"] == INTERIOR_CASE_NAME]
    assert named, [c["name"] for c in BENDS["motorway_cases"]]
    return named[0]


def _flat(point, lat0):
    """(x, y) metres in the same flat projection the module measures in - 111320*cos(lat) metres per degree
    of longitude and 110540 per degree of latitude - written out here rather than imported."""
    kx = 111320.0 * math.cos(math.radians(lat0))
    return point[1] * kx, point[0] * 110540.0


def _point_to_segment_m(p, a, b):
    """Metres from point to segment, clamped, on (lat, lon) pairs. Own implementation, own projection."""
    lat0 = (a[0] + b[0]) / 2
    (px, py), (ax, ay), (bx, by) = _flat(p, lat0), _flat(a, lat0), _flat(b, lat0)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def pair_metres(a, b, c, d):
    """Minimum metres between segment a-b and segment c-d, at one of the four endpoints (clause (a), which
    is true). None of the fixture's pairs cross, and a crossing pair would only read SMALLER here, so the
    guard below cannot be fooled into reporting an interior minimum that is not one."""
    return min(_point_to_segment_m(a, c, d), _point_to_segment_m(b, c, d),
               _point_to_segment_m(c, a, b), _point_to_segment_m(d, a, b))


def argmin_pair(line, other):
    """`(metres, i, j)` for the closest pair of segments: `i` indexes `line`'s segments, `j` `other`'s."""
    return min((pair_metres(line[i], line[i + 1], other[j], other[j + 1]), i, j)
               for i in range(len(line) - 1) for j in range(len(other) - 1))


def retained_minimum(line, other):
    """The minimum the interior-interior mutant can still see: every pair touching a first or last segment.
    Computed with `proximity.segment_distance_m`, which the mutant does not change - the claim is about
    WHICH PAIRS `line_distance_m` visits, and the fixture's typed 406.4842 is the oracle for the value."""
    n, m = len(line) - 1, len(other) - 1
    return min(proximity.segment_distance_m(line[i], line[i + 1], other[j], other[j + 1])
               for i in range(n) for j in range(m) if i in (0, n - 1) or j in (0, m - 1))


def motorway_cases():
    for fixture in (TERMS, BENDS):
        for case in fixture.get("motorway_cases", []):
            for motorway in motorways_of(case):
                yield case["name"], coords_of(case), motorway


class TestNearestApproachInteriorToBothPolylines:
    """`line_distance_m` takes the minimum over EVERY pair of segments, not over the pairs that touch an
    end of one line or the other."""

    def test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines(self):
        """The value, and the two shapes it takes. 99.4860 m is a pure latitude difference, 0.0009 deg x
        110540, from the way's middle node to the motorway's middle segment: five nodes against four, the
        smallest pair that can show this at all. The same 99.4860 comes back from the two INTERIOR
        sub-polylines alone, and the whole encounter is inside score.MOTORWAY_PROXIMITY_M."""
        case = interior_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert (len(way), len(motorway)) == (5, 4)
        metres = proximity.line_distance_m(way, motorway)
        assert metres == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        assert proximity.line_distance_m(way[1:4], motorway[1:3]) == pytest.approx(
            case["expected_meters"], abs=case["abs"]), case["workings"]
        assert proximity.meters_to_nearest_motorway(way, [motorway]) == pytest.approx(
            case["expected_meters"], abs=case["abs"]), case["workings"]
        assert metres < score.MOTORWAY_PROXIMITY_M, case["workings"]

    def test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold(self):
        """THE PRODUCT COST, pinned. Every pair an interior-interior shortcut would still visit reads
        406.4842 m or more - outside score.MOTORWAY_PROXIMITY_M - so the shortcut does not merely lose
        precision, it loses the x0.7 outright and hands this way a scenic score 1/0.7 higher than plan:85
        gives it. Neither number is restated here: the metres come from the fixture and the cut from
        score.py."""
        case = interior_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        retained = retained_minimum(way, motorway)
        assert retained == pytest.approx(case["retained_pair_meters"],
                                         abs=case["retained_abs"]), case["workings"]
        assert retained > score.MOTORWAY_PROXIMITY_M, case["workings"]
        assert proximity.line_distance_m(way, motorway) < score.MOTORWAY_PROXIMITY_M
        assert retained / proximity.line_distance_m(way, motorway) > 4.0, case["workings"]


class TestInteriorPairShape:
    """The structural guard, on its own axis. `TestFixtureShape` over in `test_proximity_bends.py` asks
    whether geometries BEND; a fixture can bend everywhere and still have every minimum on an end segment,
    which is exactly the state both fixtures were in at c0dfe1a."""

    def test_some_motorway_case_has_its_minimum_at_a_pair_interior_to_both_polylines(self):
        """At least one case, in either fixture, whose closest pair of segments is interior on BOTH sides -
        `0 < i < n-1` and `0 < j < m-1`. The argmin is computed here with this file's own segment metric,
        never `proximity.segment_distance_m`, so no mutant of the module can make this guard agree with it.
        Red on the fixtures as they stood at c0dfe1a: their motorway cases are 3 nodes against 2, plus one
        4-node way against a 2-node stub, and none of them has an interior segment on both sides at all."""
        interior = []
        for name, way, motorway in motorway_cases():
            _, i, j = argmin_pair(way, motorway)
            if 0 < i < len(way) - 2 and 0 < j < len(motorway) - 2:
                interior.append((name, i, j))
        assert interior, [(name, len(way), len(mot)) for name, way, mot in motorway_cases()]

    def test_the_interior_case_matrix_is_the_one_its_workings_types_out(self):
        """The fixture's arithmetic, checked against this file's own metric rather than against the module:
        the minimum is 99.4860 m and it is attained at (i=1,j=1) and (i=2,j=1) and NOWHERE else, which is
        the whole of the claim - two cells, both of them interior x interior."""
        case = interior_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        cells = {(i, j): pair_metres(way[i], way[i + 1], motorway[j], motorway[j + 1])
                 for i in range(len(way) - 1) for j in range(len(motorway) - 1)}
        best = min(cells.values())
        assert best == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        attaining = sorted(k for k, v in cells.items() if v == pytest.approx(best, abs=1e-09))
        assert attaining == [(1, 1), (2, 1)], (attaining, case["workings"])
        assert min(v for k, v in cells.items() if k not in attaining) == pytest.approx(
            case["retained_pair_meters"], abs=case["retained_abs"]), case["workings"]
