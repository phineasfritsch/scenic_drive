"""One concern: a polyline is the sum or the minimum over its SEGMENTS, never its first-to-last chord.

THE HOLE THIS FILE EXISTS FOR, found by review round 2 and reproduced before anything here was written.
`geometry_terms_fixture.json` grew along the NODE-COUNT axis - 3- and 4-node geometries, cases either side
of both thresholds - and every one of its multi-node geometries is either drawn on a single meridian or has
its nearest approach at an END node. So two mutants that keep both endpoints and throw the middle away
survived the WHOLE 580-test suite:
  * `tunnel_meters`: `length_m(coords)` -> `length_m([coords[0], coords[-1]])`. A 322 m bore with one
    ordinary kink then measures 284.7484 m, which is under score.TUNNEL_THRESHOLD_M, and a tunnel scores as
    open scenic road. On a monotone collinear way the sum of the segments and the chord are the SAME NUMBER,
    which is why 3336.8950 and 333.6895 could not see it.
  * `line_distance_m`: the candidate polyline -> its chord. A motorway whose nearest approach is its middle
    node then reads `inf` instead of 100.0070 m and the x0.7 is lost outright. Replacing every polyline in
    that fixture by its chord left all twelve motorway answers bit-identical - a proof, not an argument.
The subset-of-the-segments cases over there and the endpoints-only cases here are different failures and
neither set implies the other: both of the V motorway's segments below touch its apex, so `motorway[:2]`
answers 100.0070 there and `[motorway[0], motorway[-1]]` answers `inf`.

`TestFixtureShape` is the structural guard, so that the next round cannot regress this by adding another
straight line: every geometry of three or more nodes in EITHER fixture has to bend, and the three that are
deliberately drawn on one meridian are named. A new collinear case turns that test red rather than green.

Expected values are typed out in `fixtures/geometry_bends_fixture.json` from the arithmetic in each case's
`workings` field. Nothing here asks `etl.proximity` what an answer should be, and the cross-track metric the
guard measures collinearity with is written out below rather than imported from the module it guards.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from etl import proximity, score, snap

FIXTURES = Path(__file__).parent / "fixtures"
BENDS = json.loads((FIXTURES / "geometry_bends_fixture.json").read_text())
TERMS = json.loads((FIXTURES / "geometry_terms_fixture.json").read_text())

TUNNEL_CASES = BENDS["tunnel_cases"]
TUNNEL_IDS = [c["name"] for c in TUNNEL_CASES]
MOTORWAY_CASES = BENDS["motorway_cases"]
MOTORWAY_IDS = [c["name"] for c in MOTORWAY_CASES]

# The only geometries of 3+ nodes allowed to be collinear, each named with the failure it is there for.
# All three are drawn on one meridian with DELIBERATELY UNEQUAL legs, which is what makes an implementation
# that measures a SUBSET of the segments visible; a chord shortcut is invisible to them and that is the
# whole point of this file. A fourth collinear geometry has to be added here by hand, which is the guard.
COLLINEAR_BY_DESIGN = frozenset({
    "tunnel_multi_segment_is_the_whole_way",        # 0.02 and 0.01 deg: first-only and last-only differ
    "tunnel_three_node_under_the_threshold",        # 2 x 0.001 deg, the control under score's 300 m cut
    "tunnel_four_node_over_the_threshold",          # 3 x 0.001 deg, the same way over it
})

# A node this far off its geometry's first-to-last chord is a bend and not rounding. The smallest deviation
# in either fixture is the switchback bore's 44.16 m (0.0005 deg of longitude at this latitude), so the
# bound is a quarter of the closest real case and nowhere near any of them.
MIN_CROSS_TRACK_M = 10.0


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case[key]]


def motorways_of(case):
    return [[(lat, lon) for lat, lon in line] for line in case["motorways"]]


def chord_of(line):
    return [line[0], line[-1]]


def cross_track_m(point, first, last):
    """Metres from a point to the INFINITE line through `first` and `last`, in the flat projection.

    111320*cos(lat) metres per degree of longitude and 110540 per degree of latitude - the same projection
    `snap.point_to_segment_m` uses, written out here so the guard does not lean on the module it guards.
    Unclamped on purpose: a way that doubles back has its interior node beyond the chord's end, and the
    question the guard asks is whether the node is OFF the line, not whether it is between its endpoints.
    """
    lat0 = math.radians((first[0] + last[0]) / 2)
    kx, ky = 111320.0 * math.cos(lat0), 110540.0
    px, py = point[1] * kx, point[0] * ky
    ax, ay = first[1] * kx, first[0] * ky
    bx, by = last[1] * kx, last[0] * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def geometries_of(fixture):
    """`(case name, polyline)` for every geometry in a fixture's tunnel and motorway cases."""
    for case in fixture.get("tunnel_cases", []) + fixture.get("motorway_cases", []):
        yield case["name"], coords_of(case)
        for line in case.get("motorways", []):
            yield case["name"], [(lat, lon) for lat, lon in line]


class TestBentTunnelBores:
    """`tunnel_meters` sums the way's SEGMENTS. A bore is not the straight line between its portals."""

    @pytest.mark.parametrize("case", TUNNEL_CASES, ids=TUNNEL_IDS)
    def test_the_bore_measures_its_path_and_not_its_chord(self, case):
        metres = proximity.tunnel_meters(coords_of(case), case["tags"])
        assert metres == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        assert metres > case["expected_chord_m"] + 25.0, case["workings"]

    @pytest.mark.parametrize("case", TUNNEL_CASES, ids=TUNNEL_IDS)
    def test_the_chord_this_case_claims_is_the_chord_of_its_geometry(self, case):
        """The fixture's `expected_chord_m` is the other half of every claim above, so it is pinned too -
        against `snap.length_m` of the two end nodes, which is what a chord IS and is not `tunnel_meters`."""
        coords = coords_of(case)
        chord = snap.length_m(chord_of(coords))
        assert chord == pytest.approx(case["expected_chord_m"], abs=case["chord_abs"]), case["workings"]

    def test_a_bent_bore_crosses_the_threshold_only_along_its_path(self):
        """THE PRODUCT COST, pinned. 322.1038 m of tunnel is over score.TUNNEL_THRESHOLD_M and earns the
        x0.15; the same bore's chord is 284.7484 m and is not. Neither number is restated here - the cut is
        imported from score.py and the metres come from the fixture - and a sinuosity of 1.1312 is enough:
        every bore whose path lies in (300, 300 x sinuosity] metres is on the wrong side of the cut when it
        is measured end to end."""
        crossing = [c for c in TUNNEL_CASES if c["crosses_the_threshold"]]
        assert crossing, TUNNEL_IDS
        for case in crossing:
            coords = coords_of(case)
            assert proximity.tunnel_meters(coords, case["tags"]) > score.TUNNEL_THRESHOLD_M, case["name"]
            assert snap.length_m(chord_of(coords)) < score.TUNNEL_THRESHOLD_M, case["name"]

    def test_the_bent_bore_under_the_threshold_is_under_it_by_either_measure(self):
        """The control, so the cases above cannot pass by accident of where the threshold sits: a bore that
        bends just as much and stays under 300 m along BOTH measurements. Its path and its chord still
        differ by 29.48 m, so the shortcut is visible here as a value where it is not one as a multiplier."""
        case = [c for c in TUNNEL_CASES if not c["crosses_the_threshold"]][0]
        coords = coords_of(case)
        path = proximity.tunnel_meters(coords, case["tags"])
        chord = snap.length_m(chord_of(coords))
        assert path < score.TUNNEL_THRESHOLD_M
        assert chord < score.TUNNEL_THRESHOLD_M
        assert path - chord == pytest.approx(29.4812, abs=0.001)


class TestNearestApproachOffTheChord:
    """`line_distance_m` takes the minimum over every PAIR of segments. The nearest approach of two roads
    is at an interior vertex or inside an interior segment essentially always: an R-tree hands back motorway
    polylines that run past the way in both directions."""

    @pytest.mark.parametrize("case", MOTORWAY_CASES, ids=MOTORWAY_IDS)
    def test_the_metres_to_the_nearest_motorway_match_the_fixture(self, case):
        metres = proximity.meters_to_nearest_motorway(coords_of(case), motorways_of(case))
        assert metres == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]
        assert metres < score.MOTORWAY_PROXIMITY_M, case["workings"]

    @pytest.mark.parametrize("case", MOTORWAY_CASES, ids=MOTORWAY_IDS)
    def test_the_bending_polyline_reduced_to_its_chord_loses_the_encounter(self, case):
        """The fixture's `expected_chord_meters` claim, pinned per case. Exactly one of the two lines in
        each case bends; reducing THAT one to its two end nodes puts the answer past
        MOTORWAY_SEARCH_RADIUS_M, which reaches score.py as `inf` - its default for a way with no motorway
        near it. Reducing a two-node line to its chord is a no-op and is not asserted as if it were one."""
        assert case["expected_chord_meters"] == "inf"
        way, motorway = coords_of(case), motorways_of(case)[0]
        reduced = []
        if len(way) >= 3:
            reduced.append(proximity.line_distance_m(chord_of(way), motorway))
        if len(motorway) >= 3:
            reduced.append(proximity.line_distance_m(way, chord_of(motorway)))
        assert reduced, case["name"]
        for metres in reduced:
            assert metres > proximity.MOTORWAY_SEARCH_RADIUS_M, case["workings"]

    def test_the_nearest_approach_may_be_at_an_interior_node_of_the_motorway(self):
        """A V-shaped motorway 5 km east of the way at both ends, in to 100.0070 m at its apex. Its chord is
        4999.03 m out, past the radius. Both of its segments touch the apex, so this is NOT the subset
        failure `motorway[:2]` already covers: motorway[:2] and motorway[1:] each still answer 100.0070."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "motorway_nearest_at_its_middle_node"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert len(motorway) == 3
        assert proximity.line_distance_m(way, motorway) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(way, motorway[:2]) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(way, motorway[1:]) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(way, chord_of(motorway)) > proximity.MOTORWAY_SEARCH_RADIUS_M
        assert proximity.meters_to_nearest_motorway(way, [motorway]) < score.MOTORWAY_PROXIMITY_M

    def test_the_nearest_approach_may_be_at_an_interior_node_of_the_way(self):
        """The mirror, and a different line of the function: the outer loop walks the WAY's segments, and
        replacing the way by its chord is a separate wrong implementation from replacing the candidate."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "way_nearest_at_its_middle_node"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert len(way) == 3
        assert proximity.line_distance_m(way, motorway) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(chord_of(way), motorway) > proximity.MOTORWAY_SEARCH_RADIUS_M
        assert proximity.meters_to_nearest_motorway(way, [motorway]) < score.MOTORWAY_PROXIMITY_M

    def test_the_way_may_bend_toward_the_motorway_between_its_end_nodes(self):
        """The nearest approach at no node at all: a U-shaped way whose MIDDLE segment runs 99.4860 m north
        of a 176 m motorway stub, with both of its outer segments 1240.5038 m away - past the radius. An
        implementation that walks only the way's first and last segments answers `inf` here, and every
        geometry in the other fixture is too short to notice, because two- and three-node polylines have no
        segment that is neither first nor last."""
        case = [c for c in MOTORWAY_CASES
                if c["name"] == "way_bends_toward_the_motorway_between_its_end_nodes"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert len(way) == 4
        assert proximity.line_distance_m(way, motorway) == pytest.approx(99.486, abs=0.001)
        assert proximity.line_distance_m(way[1:3], motorway) == pytest.approx(99.486, abs=0.001)
        outer = min(proximity.line_distance_m(way[:2], motorway),
                    proximity.line_distance_m(way[-2:], motorway))
        assert outer == pytest.approx(1240.5038, abs=0.001)
        assert outer > proximity.MOTORWAY_SEARCH_RADIUS_M
        assert proximity.meters_to_nearest_motorway(way, [motorway]) < score.MOTORWAY_PROXIMITY_M


class TestFixtureShape:
    """The structural guard. These tests are about the FIXTURES, not about `proximity`, and they are the
    reason the next round cannot close a mutant by adding one more straight line."""

    def test_no_multi_node_geometry_is_collinear_unless_it_is_named(self):
        """EVERY geometry of three or more nodes in either fixture has an interior node at least
        MIN_CROSS_TRACK_M off its own first-to-last chord, except the three named above. This is the exact
        property whose absence let both endpoint-only mutants survive all 580 tests, and it fails SAFE: a
        new straight case is red here until somebody puts its name in COLLINEAR_BY_DESIGN on purpose."""
        straight = []
        for fixture in (TERMS, BENDS):
            for name, line in geometries_of(fixture):
                if len(line) < 3 or name in COLLINEAR_BY_DESIGN:
                    continue
                deviation = max(cross_track_m(p, line[0], line[-1]) for p in line[1:-1])
                if deviation < MIN_CROSS_TRACK_M:
                    straight.append((name, round(deviation, 4)))
        assert straight == [], straight

    def test_the_named_collinear_cases_are_exactly_the_three_that_are_there_for_subsets(self):
        """The exclusion list is pinned against the fixture both ways: every name in it exists, and every
        one of them really is collinear. A name left behind after its case is reshaped would silently widen
        the exemption, and a name for a case that bends would hide nothing but would still be a lie."""
        named = {name for fixture in (TERMS, BENDS) for name, _ in geometries_of(fixture)}
        assert COLLINEAR_BY_DESIGN <= named, COLLINEAR_BY_DESIGN - named
        for fixture in (TERMS, BENDS):
            for name, line in geometries_of(fixture):
                if name not in COLLINEAR_BY_DESIGN or len(line) < 3:
                    continue
                deviation = max(cross_track_m(p, line[0], line[-1]) for p in line[1:-1])
                assert deviation == pytest.approx(0.0, abs=1e-06), (name, deviation)

    def test_some_tunnel_case_crosses_the_threshold_along_its_path_alone(self):
        """The property the tunnel side needed, asserted about the fixture rather than about one case: at
        least one bore is over score.TUNNEL_THRESHOLD_M along its path and under it along its chord. Without
        one, `tunnel_meters` can be replaced by its chord and no multiplier in the corpus changes."""
        crossing = [c for c in TUNNEL_CASES
                    if c["expected_meters"] > score.TUNNEL_THRESHOLD_M > c["expected_chord_m"]]
        assert crossing, [(c["name"], c["expected_meters"], c["expected_chord_m"]) for c in TUNNEL_CASES]
        flagged = {c["name"] for c in TUNNEL_CASES if c["crosses_the_threshold"]}
        assert {c["name"] for c in crossing} == flagged

    def test_some_motorway_case_needs_an_interior_vertex_of_the_candidate(self):
        """The property the proximity side needed: at least one case where the candidate's chord is past
        MOTORWAY_SEARCH_RADIUS_M while the way is inside score.MOTORWAY_PROXIMITY_M of the polyline. In
        `geometry_terms_fixture.json` replacing every polyline by its chord left all twelve answers
        bit-identical, which is how the second mutant survived."""
        found = []
        for case in MOTORWAY_CASES:
            way, motorway = coords_of(case), motorways_of(case)[0]
            if len(motorway) < 3:
                continue
            if (proximity.line_distance_m(way, chord_of(motorway)) > proximity.MOTORWAY_SEARCH_RADIUS_M
                    and proximity.line_distance_m(way, motorway) < score.MOTORWAY_PROXIMITY_M
                    and case["expected_meters"] < score.MOTORWAY_PROXIMITY_M):
                found.append(case["name"])
        assert found, MOTORWAY_IDS

    def test_every_case_shows_its_arithmetic_and_is_named_once_across_both_fixtures(self):
        names = [c["name"] for c in TUNNEL_CASES + MOTORWAY_CASES]
        other = [c["name"] for c in TERMS["tunnel_cases"] + TERMS["motorway_cases"]]
        assert len(names + other) == len(set(names + other)), names + other
        for case in TUNNEL_CASES + MOTORWAY_CASES:
            assert case["workings"].strip(), case["name"]
