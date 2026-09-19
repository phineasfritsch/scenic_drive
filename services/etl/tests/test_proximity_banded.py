"""One concern: the minimum of the segment-pair matrix can sit FAR OFF ITS DIAGONAL.

THE HOLE THIS FILE EXISTS FOR, recorded by agent/rv4-pr94 in its PASS entry on PR #94 rather than bought as
a fifth review round. `line_distance_m` takes the minimum over every pair of segments; a BANDED window -
`... for i in range(n) for j in range(m) if abs(i - j) <= 1`, the shape a monotone-sweep pruning has, and
the one an optimisation writes when it assumes two polylines run alongside each other - survived all 608
tests at the time. It is none of the four shapes the earlier rounds blocked on:
  * it keeps the FIRST and the LAST segment of both lines, so neither subset case sees it;
  * it keeps the INTERIOR-INTERIOR pairs, so review round 3's case does not see it either - that case's
    minimum is at (i=1, j=1) and (i=2, j=1), on the diagonal and one cell off it;
  * it is not a chord, not a candidate order and not a normalisation.
What it assumes is that the two polylines are traversed in step. They are not: an R-tree hands back a
motorway stub of one or two segments next to a way of dozens, so `j` barely moves while `i` runs the length
of the way, and the encounter can be anywhere in that column.

THE CASE, `minimum_far_off_the_diagonal_of_the_segment_pair_matrix` in `geometry_bends_fixture.json`: a
seven-node way (segments s0..s5) against a 176 m motorway stub of ONE segment, so `j` is 0 throughout and
the band can select nothing but `i` in (0, 1). The way runs east 1105.4000 m south of the stub, climbs to
within 99.4860 m of it for its middle segment s3 and drops back, so the minimum is attained ONLY at
(i=3, j=0) - three cells off the diagonal. The band sees s0 and s1 alone and answers 2009.4750 m, past
`MOTORWAY_SEARCH_RADIUS_M`, which reaches `score.py` as `inf`: not a blurred distance but the x0.7 lost
outright for a way running 99 m from a motorway.

`TestBandedWindowShape` is the structural guard, on its own axis and asked of the FIXTURES rather than of
`proximity`: at least one case somewhere has its minimum at least two cells off the diagonal. Every fixture
case could bend, could need an interior-interior pair, and still be answered by a banded window - which is
the state both fixtures were in when rv4-pr94 measured them. It walks the matrix with the flat
segment-to-segment metric written out below, never `proximity`'s, so the guard does not lean on the module
it guards; the expected metres are typed out in the fixture from the arithmetic in the case's `workings`.
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

BANDED_CASE_NAME = "minimum_far_off_the_diagonal_of_the_segment_pair_matrix"

# The window this file exists to refute: a pair is visited only if its two segment indices are this close.
# A literal, because it is the mutant's parameter and not a property of anything in `etl/`.
BAND = 1


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case[key]]


def motorways_of(case):
    return [[(lat, lon) for lat, lon in line] for line in case["motorways"]]


def banded_case():
    """The one case this file is about, looked up by name so a fixture that loses it fails HERE and says so
    rather than raising an index error three assertions later."""
    named = [c for c in BENDS["motorway_cases"] if c["name"] == BANDED_CASE_NAME]
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
    """Minimum metres between segment a-b and segment c-d, at one of the four endpoints. None of the
    fixture's pairs cross, and a crossing pair would only read SMALLER here, so this guard cannot be fooled
    into reporting an off-diagonal minimum that is not one."""
    return min(_point_to_segment_m(a, c, d), _point_to_segment_m(b, c, d),
               _point_to_segment_m(c, a, b), _point_to_segment_m(d, a, b))


def matrix(line, other):
    """`{(i, j): metres}` over every pair of segments, with this file's own metric."""
    return {(i, j): pair_metres(line[i], line[i + 1], other[j], other[j + 1])
            for i in range(len(line) - 1) for j in range(len(other) - 1)}


def offset_of_the_minimum(line, other):
    """`|i - j|` at the closest pair of segments: how far off the diagonal a band has to reach to see it."""
    cells = matrix(line, other)
    best = min(cells.values())
    return min(abs(i - j) for (i, j), v in cells.items() if v == best)


def banded_minimum(line, other, band=BAND):
    """The minimum a banded window can still see. Computed with `proximity.segment_distance_m`, which the
    mutant does not change - the claim is about WHICH PAIRS `line_distance_m` visits, and the fixture's
    typed `banded_pair_meters` is the oracle for the value."""
    return min(proximity.segment_distance_m(line[i], line[i + 1], other[j], other[j + 1])
               for i in range(len(line) - 1) for j in range(len(other) - 1) if abs(i - j) <= band)


def motorway_cases():
    for fixture in (TERMS, BENDS):
        for case in fixture.get("motorway_cases", []):
            for motorway in motorways_of(case):
                yield case["name"], coords_of(case), motorway


class TestTheMinimumFarOffTheDiagonal:
    """`line_distance_m` takes the minimum over EVERY pair of segments, not over a window around the
    diagonal of the pair matrix."""

    def test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix(self):
        """The value and the cell. 99.4860 m is a pure latitude difference, 0.0009 deg x 110540, from the
        motorway stub to the way's middle segment; the minimum is attained at (i=3, j=0) and nowhere else,
        three cells off the diagonal, and the whole encounter is inside score.MOTORWAY_PROXIMITY_M."""
        case = banded_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert (len(way), len(motorway)) == (7, 2)
        metres = proximity.line_distance_m(way, motorway)
        assert metres == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        assert proximity.meters_to_nearest_motorway(way, [motorway]) == pytest.approx(
            case["expected_meters"], abs=case["abs"]), case["workings"]
        assert metres < score.MOTORWAY_PROXIMITY_M, case["workings"]
        i, j = case["minimum_cell"]
        assert abs(i - j) > BAND, case["workings"]
        assert offset_of_the_minimum(way, motorway) == abs(i - j), case["workings"]
        assert proximity.line_distance_m(way[i:i + 2], motorway) == pytest.approx(
            case["expected_meters"], abs=case["abs"]), case["workings"]

    def test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres(self):
        """THE PRODUCT COST, pinned. Every pair a banded window still visits reads 2009.4750 m or more -
        past MOTORWAY_SEARCH_RADIUS_M, which `meters_to_nearest_motorway` reports as `inf`, score.py's
        default for a way with no motorway near it. So the window does not lose precision, it loses the
        x0.7 outright and hands this way a scenic score 1/0.7 = 43% higher than plan:85 gives it. Neither
        number is restated here: the metres come from the fixture, the radius and the cut from the code."""
        case = banded_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        banded = banded_minimum(way, motorway)
        assert banded == pytest.approx(case["banded_pair_meters"], abs=case["banded_abs"]), case["workings"]
        assert banded > proximity.MOTORWAY_SEARCH_RADIUS_M, case["workings"]
        reported = banded if banded <= proximity.MOTORWAY_SEARCH_RADIUS_M else math.inf
        assert reported == math.inf, case["workings"]
        assert proximity.meters_to_nearest_motorway(way, [motorway]) < score.MOTORWAY_PROXIMITY_M
        assert banded / proximity.line_distance_m(way, motorway) > 20.0, case["workings"]


class TestBandedWindowShape:
    """The structural guard, on its own axis. A fixture can bend everywhere, and can need a pair interior
    to both polylines, and still have every minimum within one cell of the diagonal - which is exactly the
    state both fixtures were in when the banded window survived all 608 tests."""

    def test_some_motorway_case_has_its_minimum_at_least_two_cells_off_the_diagonal(self):
        """At least one case, in either fixture, whose closest pair of segments has `|i - j| > BAND`. The
        argmin is computed with this file's own segment metric, never `proximity.segment_distance_m`, so no
        mutant of the module can make this guard agree with it. It fails SAFE: a fixture that loses this
        case is red here rather than quietly unmeasured on the whole banded axis."""
        far = [(name, offset_of_the_minimum(way, motorway))
               for name, way, motorway in motorway_cases()
               if offset_of_the_minimum(way, motorway) > BAND]
        assert far, [(name, offset_of_the_minimum(w, m)) for name, w, m in motorway_cases()]

    def test_the_banded_case_column_is_the_one_its_workings_types_out(self):
        """The fixture's arithmetic, checked against this file's own metric rather than against the module.
        The stub has one segment, so the matrix is a single COLUMN, and every one of its six numbers is
        typed out in `workings`: 2789.6886, 2009.4750, 801.0995, 99.4860, 801.0995, 2009.4750."""
        case = banded_case()
        way, motorway = coords_of(case), motorways_of(case)[0]
        cells = matrix(way, motorway)
        column = [round(cells[(i, 0)], 4) for i in range(len(way) - 1)]
        assert column == [2789.6886, 2009.475, 801.0995, 99.486, 801.0995, 2009.475], case["workings"]
        best = min(cells.values())
        assert best == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        attaining = sorted(k for k, v in cells.items() if v == pytest.approx(best, abs=1e-09))
        assert attaining == [tuple(case["minimum_cell"])], (attaining, case["workings"])
        within = min(v for (i, j), v in cells.items() if abs(i - j) <= BAND)
        assert within == pytest.approx(case["banded_pair_meters"], abs=case["banded_abs"]), case["workings"]
