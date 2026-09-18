"""Raw sinuosity: the ratio, its floor, and the closed way that would otherwise divide by zero.

EVERY EXPECTED VALUE IS TYPED OUT, in `fixtures/geometry_terms_fixture.json`, from the arithmetic in that
case's `workings` field - metres are 6373000 * degrees * pi/180 on a meridian and the ratio of two arcs of
one great circle is the ratio of their degrees, whatever the radius is. Nothing here calls
`etl.sinuosity` to find out what it should say. Two of the cases are exact by construction and are
asserted with no meaningful tolerance: a two-node way's path and gap are the same call, and a meridian
hairpin's 0.03 deg over 0.01 deg is 3.0.

The failure this file is built against is a term that reads plausible on every real way and is nonsense on
the two shapes nobody looks at: the loop, whose endpoints are one point, and the lasso, whose endpoints are
metres apart and whose raw ratio is in the hundreds. Both are pinned by name below.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from etl import sinuosity

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "geometry_terms_fixture.json").read_text())
CASES = FIXTURE["sinuosity_cases"]
IDS = [c["name"] for c in CASES]


def coords_of(case):
    return [(lat, lon) for lat, lon in case["coordinates"]]


class TestFixture:
    """The fixture itself, so a case cannot be added without its arithmetic or quietly dropped."""

    def test_every_case_is_named_once(self):
        assert len(IDS) == len(set(IDS)), IDS

    def test_every_case_shows_its_arithmetic(self):
        """`workings` is a JSON field in a committed file, not a comment: comments get stripped."""
        for case in CASES:
            assert case["workings"].strip(), case["name"]
            assert "expected_sinuosity" in case or "expected_min_sinuosity" in case, case["name"]

    def test_the_shapes_that_matter_are_all_present(self):
        """A straight way, a right angle, a switchback, a closed loop, a lasso and the open way just
        outside the closed threshold. Named individually, because dropping one is how a guard stops being
        tested while the file still looks full."""
        for name in ("straight_two_node", "right_angle_dogleg", "hairpin_meridian",
                     "closed_loop_rectangle", "near_closed_lasso", "just_open_rectangle"):
            assert name in IDS, name


class TestConstants:
    def test_the_declined_answer_is_the_floor_of_the_scale(self):
        """1.0, never inf and never a large number: a closed way credited with a huge raw sinuosity would
        take the top of its region's rank-normalised range away from a genuinely sinuous road."""
        assert sinuosity.CLOSED_WAY_SINUOSITY == 1.0

    def test_the_closed_threshold_is_a_real_distance(self):
        """Zero would make the guard cosmetic - it would catch only the exactly-repeated node and let a
        lasso through - and a threshold near the length of a short way would swallow real ones."""
        assert 1.0 <= sinuosity.CLOSED_ENDPOINT_M <= 30.0

    def test_two_coordinates_is_the_minimum(self):
        assert sinuosity.MIN_COORDINATES == 2


class TestCases:
    @pytest.mark.parametrize("case", CASES, ids=IDS)
    def test_the_endpoint_gap_matches_the_fixture(self, case):
        gap = sinuosity.endpoint_gap_m(coords_of(case))
        assert gap == pytest.approx(case["expected_gap_m"], abs=case["gap_abs"]), case["workings"]

    @pytest.mark.parametrize("case", CASES, ids=IDS)
    def test_closedness_matches_the_fixture(self, case):
        assert sinuosity.is_closed_way(coords_of(case)) is case["closed"], case["workings"]

    @pytest.mark.parametrize("case", CASES, ids=IDS)
    def test_the_sinuosity_matches_the_fixture(self, case):
        value = sinuosity.way_sinuosity(coords_of(case))
        if "expected_sinuosity" in case:
            assert value == pytest.approx(case["expected_sinuosity"], rel=case["rel"]), case["workings"]
        else:
            assert value > case["expected_min_sinuosity"], (value, case["workings"])

    @pytest.mark.parametrize("case", CASES, ids=IDS)
    def test_no_case_is_below_the_floor(self, case):
        """A ratio of a path to a straight line cannot be less than 1.0. It could be, by 1e-9, if the two
        halves came from two earth models - which is why both are snap.length_m."""
        assert sinuosity.way_sinuosity(coords_of(case)) >= 1.0


class TestRawNotNormalised:
    def test_the_term_is_raw_and_unbounded_not_a_0_to_1_score(self):
        """T-0163 rank-normalises this inside a region. A value above 1.0 is the evidence that nothing here
        clamped or rescaled - score.out_of_range would reject this number, and should: it is not that term
        yet."""
        hairpin = [c for c in CASES if c["name"] == "hairpin_meridian"][0]
        assert sinuosity.way_sinuosity(coords_of(hairpin)) > 1.0

    def test_a_lasso_is_declined_rather_than_credited(self):
        """The guard's whole point. The same geometry with a 22 m gap scores in the hundreds (the
        `just_open_rectangle` case), so 1.0 here is the guard firing and not a coincidence of shape."""
        lasso = [c for c in CASES if c["name"] == "near_closed_lasso"][0]
        just_open = [c for c in CASES if c["name"] == "just_open_rectangle"][0]
        assert sinuosity.way_sinuosity(coords_of(lasso)) == 1.0
        assert sinuosity.way_sinuosity(coords_of(just_open)) > 100.0

    def test_a_closed_loop_does_not_divide_by_zero(self):
        loop = [c for c in CASES if c["name"] == "closed_loop_rectangle"][0]
        assert sinuosity.endpoint_gap_m(coords_of(loop)) == 0.0
        assert sinuosity.way_sinuosity(coords_of(loop)) == sinuosity.CLOSED_WAY_SINUOSITY


class TestRefusal:
    """A way with fewer than two coordinates gets no value. A default returned here would score, would look
    plausible, and nothing would ever print it."""

    def test_a_one_coordinate_way_refuses_by_name(self):
        with pytest.raises(ValueError, match=r"way_sinuosity: needs at least 2 coordinates, got 1"):
            sinuosity.way_sinuosity([(37.49, -122.0)])

    def test_an_empty_way_refuses_by_name(self):
        with pytest.raises(ValueError, match=r"way_sinuosity: needs at least 2 coordinates, got 0"):
            sinuosity.way_sinuosity([])

    def test_the_gap_refuses_on_its_own_name(self):
        with pytest.raises(ValueError, match=r"endpoint_gap_m: needs at least 2 coordinates, got 1"):
            sinuosity.endpoint_gap_m([(37.49, -122.0)])

    def test_the_refusal_names_its_caller(self):
        """`proximity` imports this refusal instead of writing a second message for the same rule, so the
        caller's name has to come from the argument."""
        with pytest.raises(ValueError, match=r"tunnel_meters: needs at least 2 coordinates, got 1"):
            sinuosity.require_geometry([(37.49, -122.0)], "tunnel_meters")
