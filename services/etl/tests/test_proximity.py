"""Tunnel metres and metres to the nearest motorway.

EVERY EXPECTED VALUE IS TYPED OUT in `fixtures/geometry_terms_fixture.json` from the arithmetic in that
case's `workings` field: 6373000 * degrees * pi/180 for a length along a meridian, and 111320*cos(lat) /
110540 metres per degree for the flat projection the distances are measured in. Nothing here asks
`etl.proximity` what the answer should be.

THE THREE FAILURES THIS FILE IS BUILT AGAINST.
  * `tunnel=no` counted as a tunnel. The tag exists to say the way is NOT one, so a key-presence or
    truthiness test gets it exactly backwards and takes a fifth off the score of every way that carries it.
  * the distance measured from the way's NODES. OSM node density is arbitrary, so the nearest point of an
    encounter is usually mid-segment: the `nearest_point_inside_a_long_way_segment` case answers 884.90 m
    that way where the truth is 55.27 m, and 150 m is the boundary being decided.
  * a crossing measured from endpoints. Two segments that cross are at distance 0 and no endpoint distance
    sees it - the crossing case's four endpoint distances are all 441.61 m, which is pinned below next to
    the 0.0.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from etl import proximity, score, snap

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "geometry_terms_fixture.json").read_text())
TUNNEL_CASES = FIXTURE["tunnel_cases"]
TUNNEL_IDS = [c["name"] for c in TUNNEL_CASES]
MOTORWAY_CASES = FIXTURE["motorway_cases"]
MOTORWAY_IDS = [c["name"] for c in MOTORWAY_CASES]


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case[key]]


def motorways_of(case):
    return [[(lat, lon) for lat, lon in line] for line in case["motorways"]]


class TestFixture:
    def test_every_case_is_named_once(self):
        names = TUNNEL_IDS + MOTORWAY_IDS
        assert len(names) == len(set(names)), names

    def test_every_case_shows_its_arithmetic(self):
        for case in TUNNEL_CASES + MOTORWAY_CASES:
            assert case["workings"].strip(), case["name"]

    def test_the_shapes_that_matter_are_all_present(self):
        for name in ("tunnel_no_is_not_a_tunnel", "tunnel_culvert_is_refused",
                     "tunnel_value_is_case_and_space_normalised",
                     "tunnel_multi_segment_is_the_whole_way",
                     "tunnel_three_node_under_the_threshold", "tunnel_four_node_over_the_threshold"):
            assert name in TUNNEL_IDS, name
        for name in ("crossing_a_motorway", "nearest_point_inside_a_long_way_segment",
                     "two_motorways_nearest_wins", "two_motorways_nearest_first",
                     "motorway_nearest_on_its_later_segment", "way_nearest_on_its_later_segment",
                     "just_inside_the_scorer_s_proximity_boundary",
                     "just_outside_the_scorer_s_proximity_boundary", "no_motorways_at_all"):
            assert name in MOTORWAY_IDS, name

    def test_no_geometry_in_the_fixture_is_only_two_nodes(self):
        """The hole review round 1 found: every polyline here had exactly one segment, so the double loop in
        `line_distance_m` and the sum in `tunnel_meters` were never exercised over more than one of them
        and three wrong implementations were green. Asserted rather than left to the next case."""
        assert max(len(c["coordinates"]) for c in TUNNEL_CASES) >= 3
        assert max(len(c["coordinates"]) for c in MOTORWAY_CASES) >= 3
        assert max((len(line) for c in MOTORWAY_CASES for line in c["motorways"]), default=0) >= 3


class TestTunnelValues:
    """The accepted set, against literals. A set like this stays honest no other way."""

    def test_the_accepted_values_are_exactly_these_three(self):
        assert proximity.TUNNEL_VALUES == frozenset({"yes", "building_passage", "avalanche_protector"})

    def test_no_is_not_among_them(self):
        assert "no" not in proximity.TUNNEL_VALUES

    def test_culvert_is_not_among_them(self):
        """A culvert is the pipe a stream runs through under the road, not the road being in a tunnel."""
        assert "culvert" not in proximity.TUNNEL_VALUES

    def test_a_non_string_value_is_not_a_tunnel(self):
        """A parser that hands back a bool or None must not make `True in {"yes", ...}` the question."""
        assert proximity.is_tunnel({"tunnel": True}) is False
        assert proximity.is_tunnel({"tunnel": None}) is False
        assert proximity.is_tunnel({}) is False

    def test_covered_is_not_read(self):
        """`covered=yes` is a different key with a different meaning; if it is ever wanted it gets its own
        constant and its own test, not a quiet widening of this one."""
        assert proximity.tunnel_meters([(37.49, -122.0), (37.5, -122.0)], {"covered": "yes"}) == 0.0


class TestMotorwayClasses:
    def test_the_four_classes_against_literals(self):
        """Imported from byways rather than restated (score.py does the same), so this assertion is what
        turns a change of meaning there into a failure here instead of a wider penalty in the corpus."""
        assert set(proximity.MOTORWAY_CLASSES) == {"motorway", "motorway_link", "trunk", "trunk_link"}

    def test_a_primary_road_is_not_a_motorway(self):
        assert proximity.is_motorway({"highway": "primary"}) is False
        assert proximity.is_motorway({}) is False

    def test_a_link_is_a_motorway(self):
        assert proximity.is_motorway({"highway": "motorway_link"}) is True
        assert proximity.is_motorway({"highway": "trunk_link"}) is True


class TestSearchRadius:
    def test_the_radius_cannot_decide_the_scorer_s_multiplier(self):
        """`score` compares the metres this module reports against MOTORWAY_PROXIMITY_M. If the radius were
        anywhere near that distance, "no motorway near this way" and "a motorway just past the threshold"
        would become the same answer and the radius, not the threshold, would be setting the penalty. The
        relation is asserted; neither number is restated."""
        assert proximity.MOTORWAY_SEARCH_RADIUS_M >= 2 * score.MOTORWAY_PROXIMITY_M

    def test_the_radius_is_a_parameter_not_a_law(self):
        way = [(37.49, -121.9988677), (37.5, -121.9988677)]
        motorway = [[(37.49, -122.0), (37.5, -122.0)]]
        assert proximity.meters_to_nearest_motorway(way, motorway, radius_m=50.0) == math.inf
        assert proximity.meters_to_nearest_motorway(way, motorway, radius_m=150.0) < 150.0

    def test_the_radius_is_inclusive(self):
        """A distance exactly at the radius is reported. Pinned on the crossing pair, whose distance is
        exactly 0.0, so the boundary case needs no tolerance to state."""
        crossing = [c for c in MOTORWAY_CASES if c["name"] == "crossing_a_motorway"][0]
        assert proximity.meters_to_nearest_motorway(
            coords_of(crossing), motorways_of(crossing), radius_m=0.0) == 0.0


class TestTunnelCases:
    @pytest.mark.parametrize("case", TUNNEL_CASES, ids=TUNNEL_IDS)
    def test_the_tunnel_metres_match_the_fixture(self, case):
        metres = proximity.tunnel_meters(coords_of(case), case["tags"])
        assert metres == pytest.approx(case["expected_meters"], abs=case["abs"]), case["workings"]

    @pytest.mark.parametrize("case", TUNNEL_CASES, ids=TUNNEL_IDS)
    def test_is_tunnel_agrees_with_the_metres(self, case):
        assert proximity.is_tunnel(case["tags"]) is (case["expected_meters"] > 0.0), case["workings"]


class TestMotorwayCases:
    @pytest.mark.parametrize("case", MOTORWAY_CASES, ids=MOTORWAY_IDS)
    def test_the_metres_to_the_nearest_motorway_match_the_fixture(self, case):
        metres = proximity.meters_to_nearest_motorway(coords_of(case), motorways_of(case))
        expected = float(case["expected_meters"])
        if math.isinf(expected):
            assert metres == math.inf, case["workings"]
        else:
            assert metres == pytest.approx(expected, abs=case["abs"]), case["workings"]


class TestSegmentGeometry:
    def test_a_crossing_is_zero_where_every_endpoint_is_hundreds_of_metres_away(self):
        """0.005 deg of longitude from the motorway = 0.005 * 111320 * cos(37.495 deg) = 0.005 * 88322.007
        = 441.61 m, and that is what all four endpoint-to-segment distances measure. The crossing test is
        the only reason the answer is 0.0, so both numbers are pinned in one place."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "crossing_a_motorway"][0]
        a, b = coords_of(case)
        c, d = motorways_of(case)[0]
        endpoints_only = min(snap.point_to_segment_m(a, c, d), snap.point_to_segment_m(b, c, d),
                             snap.point_to_segment_m(c, a, b), snap.point_to_segment_m(d, a, b))
        assert endpoints_only == pytest.approx(441.61, abs=0.05)
        assert proximity.segment_distance_m(a, b, c, d) == 0.0

    def test_a_collinear_pair_falls_through_to_the_endpoints(self):
        """The crossing test is deliberately strict - collinear and touching pairs are not "proper"
        crossings - because the endpoint distances already answer 0.0 for them, and a permissive
        orientation test on degenerate input is where this kind of code goes wrong."""
        a, b = (37.49, -122.0), (37.5, -122.0)
        c, d = (37.495, -122.0), (37.505, -122.0)
        assert proximity._crosses(a, b, c, d) is False
        assert proximity.segment_distance_m(a, b, c, d) == pytest.approx(0.0, abs=1e-06)

    def test_the_nearest_point_may_be_inside_a_long_segment_of_either_line(self):
        """0.0005 deg * 110540 m/deg = 55.27 m, with the way's own nodes 883.16 m away to each side. A
        measurement that only walks the way's nodes answers 884.90 m; one that only walks the motorway's
        answers the same on the mirrored case. Both directions are measured."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "nearest_point_inside_a_long_way_segment"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert proximity.line_distance_m(way, motorway) == pytest.approx(55.27, abs=0.01)
        assert proximity.line_distance_m(motorway, way) == pytest.approx(55.27, abs=0.01)
        nodes_only = min(snap.distance_to_line_m(p, motorway) for p in way)
        assert nodes_only == pytest.approx(884.90, abs=0.05)


class TestMultiSegmentGeometry:
    """The module docstring's own sentence - "every segment of the way is measured against every segment of
    the motorway" - asserted instead of asserted in prose. Until these cases existed every geometry here had
    exactly two nodes, and three implementations that lose the x0.7 or the x0.15 outright were green."""

    def test_the_nearest_approach_may_be_on_a_later_segment_of_the_motorway(self):
        """The candidate's first segment is 0.0566 * 88322.007 = 4999.03 m away, past the search radius;
        its second comes back to 0.0011323 * 88322.007 = 100.007 m. Walking only the candidate's first
        segment reports math.inf, which is score.py's "no motorway near this way"."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "motorway_nearest_on_its_later_segment"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert len(motorway) == 3
        assert proximity.line_distance_m(way, motorway) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(way, motorway[:2]) > proximity.MOTORWAY_SEARCH_RADIUS_M
        assert proximity.meters_to_nearest_motorway(way, [motorway]) == pytest.approx(100.0, abs=0.05)

    def test_the_nearest_approach_may_be_on_a_later_segment_of_the_way(self):
        """The mirror, and a separate wrong implementation: the outer loop is over the WAY's segments and
        nothing above would notice if it stopped after the first."""
        case = [c for c in MOTORWAY_CASES if c["name"] == "way_nearest_on_its_later_segment"][0]
        way, motorway = coords_of(case), motorways_of(case)[0]
        assert len(way) == 3
        assert proximity.line_distance_m(way, motorway) == pytest.approx(100.0, abs=0.05)
        assert proximity.line_distance_m(way[:2], motorway) > proximity.MOTORWAY_SEARCH_RADIUS_M
        assert proximity.meters_to_nearest_motorway(way, [motorway]) == pytest.approx(100.0, abs=0.05)

    def test_the_candidate_order_cannot_change_the_answer(self):
        """[far, near] and [near, far] are the same question. The caller is an R-tree query with no reason
        to sort, so keeping the last candidate rather than the smallest loses the x0.7 half the time."""
        far_first = [c for c in MOTORWAY_CASES if c["name"] == "two_motorways_nearest_wins"][0]
        near_first = [c for c in MOTORWAY_CASES if c["name"] == "two_motorways_nearest_first"][0]
        assert coords_of(near_first) == coords_of(far_first)
        assert motorways_of(near_first) == list(reversed(motorways_of(far_first)))
        one = proximity.meters_to_nearest_motorway(coords_of(far_first), motorways_of(far_first))
        two = proximity.meters_to_nearest_motorway(coords_of(near_first), motorways_of(near_first))
        assert one == two == pytest.approx(100.0, abs=0.05)


class TestTunnelLength:
    def test_a_multi_segment_tunnel_is_measured_end_to_end(self):
        """THE RULING, pinned. `tunnel=` is a tag on the WAY, so "tunnel metres" is the way's whole length
        even when only part of its geometry is under the hill: a road that enters a tunnel halfway along is
        two ways in OSM, and where it is not, the metres are wrong in the data and not here. The two legs
        are 0.02 deg and 0.01 deg, so first-segment-only (2224.5967) and last-segment-only (1112.2983) are
        both visible against the whole 2224.5967 + 1112.2983 = 3336.8950."""
        case = [c for c in TUNNEL_CASES if c["name"] == "tunnel_multi_segment_is_the_whole_way"][0]
        coords = coords_of(case)
        assert len(coords) == 3
        assert proximity.tunnel_meters(coords, case["tags"]) == pytest.approx(3336.8950, abs=0.001)
        assert proximity.tunnel_meters(coords[:2], case["tags"]) == pytest.approx(2224.5967, abs=0.001)
        assert proximity.tunnel_meters(coords[1:], case["tags"]) == pytest.approx(1112.2983, abs=0.001)

    def test_the_metres_fall_either_side_of_the_threshold_score_cuts_at(self):
        """score.py cuts at TUNNEL_THRESHOLD_M and this module supplies the number it cuts. Two ways drawn
        with the same 0.001 deg legs, two of them and three: 2 * 111.2298 = 222.4597 m under the cut and
        3 * 111.2298 = 333.6895 m over it. Neither the threshold nor the metres are restated here - the one
        is imported and the others come from the fixture - and a way measured on one segment alone reads
        111.2298 m and falls on the wrong side of it."""
        under = [c for c in TUNNEL_CASES if c["name"] == "tunnel_three_node_under_the_threshold"][0]
        over = [c for c in TUNNEL_CASES if c["name"] == "tunnel_four_node_over_the_threshold"][0]
        assert proximity.tunnel_meters(coords_of(under), under["tags"]) < score.TUNNEL_THRESHOLD_M
        assert proximity.tunnel_meters(coords_of(over), over["tags"]) > score.TUNNEL_THRESHOLD_M


class TestProximityBoundary:
    def test_the_metres_fall_either_side_of_the_proximity_score_cuts_at(self):
        """The same for the other boundary: 0.00135 * 110540 = 149.229 m inside and 0.00137 * 110540 =
        151.4398 m outside, two parallel east-west pairs so no cos(lat) enters it. The inside case's 0.77 m
        of margin is inside the 0.94 m between this flat model and the spherical one at 37.5 deg, so it
        also pins which model `snap.point_to_segment_m` measures on, where that difference decides."""
        inside = [c for c in MOTORWAY_CASES if c["name"] == "just_inside_the_scorer_s_proximity_boundary"][0]
        outside = [c for c in MOTORWAY_CASES
                   if c["name"] == "just_outside_the_scorer_s_proximity_boundary"][0]
        near = proximity.meters_to_nearest_motorway(coords_of(inside), motorways_of(inside))
        far = proximity.meters_to_nearest_motorway(coords_of(outside), motorways_of(outside))
        assert near < score.MOTORWAY_PROXIMITY_M
        assert far > score.MOTORWAY_PROXIMITY_M


class TestTheZeroClassesAreNotGatedHere:
    def test_a_motorway_s_own_geometry_still_gets_both_terms(self):
        """The owner's ruling for this task, and score.py's own (score.py:29-32, :139): a motorway scores 0
        and is still routable, so its terms are produced like any other way's - the scorer zeroes it, this
        module does not gate. Nothing here reads `highway` except `is_motorway`, which selects the
        candidates measured AGAINST and never judges the way being measured."""
        way = [(37.49, -122.0), (37.5, -122.0)]
        near = [[(37.49, -121.9988677), (37.5, -121.9988677)]]
        assert proximity.tunnel_meters(way, {"highway": "motorway", "tunnel": "yes"}) == pytest.approx(
            1112.2983, abs=0.001)
        assert proximity.meters_to_nearest_motorway(way, near) == pytest.approx(100.0, abs=0.05)


class TestRefusal:
    def test_a_one_coordinate_way_refuses_by_name_before_the_tags_are_read(self):
        with pytest.raises(ValueError, match=r"tunnel_meters: needs at least 2 coordinates, got 1"):
            proximity.tunnel_meters([(37.49, -122.0)], {"tunnel": "yes"})

    def test_a_one_coordinate_way_refuses_the_motorway_distance_by_name(self):
        with pytest.raises(ValueError, match=r"meters_to_nearest_motorway: needs at least 2 coordinates"):
            proximity.meters_to_nearest_motorway([(37.49, -122.0)], [])

    def test_a_degenerate_candidate_refuses_and_says_which_one(self):
        """A motorway geometry of one node would otherwise contribute no segment pair, `min()` over an
        empty sequence would raise a bare ValueError from the standard library, and the candidate that was
        wrong would not be named."""
        way = [(37.49, -122.0), (37.5, -122.0)]
        good = [(37.49, -121.9988677), (37.5, -121.9988677)]
        with pytest.raises(ValueError, match=r"motorway\[1\]: needs at least 2 coordinates, got 1"):
            proximity.meters_to_nearest_motorway(way, [good, [(37.49, -122.0)]])
