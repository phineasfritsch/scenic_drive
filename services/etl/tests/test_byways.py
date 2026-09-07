"""Byway snapping, the Eligible-versus-Designated decision, and the route key.

The failure worth guarding is not a crash. It is a frontage road inheriting the freeway's designation, or a
cross street inheriting a byway's because it touches one at a junction - both produce a road that scores as
scenic because of a road next to it. Real-geometry versions of those two live in test_byways_fixture.py;
these are the constructed cases that pin the arithmetic.
"""
from __future__ import annotations

import math

import pytest

from etl import byways as bw
from etl.curvature import distance_on_earth

# A north-south line near Skyline, and a way running along it.
BYWAY = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]


def along(offset_deg=0.0, n=4, start=37.50, lon=-122.35):
    return [(start - i * 0.01, lon + offset_deg) for i in range(n)]


def length_m(way):
    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(way, way[1:]))


class TestStatusMeaning:
    def test_officially_designated_scores_the_full_bonus(self):
        assert bw.status_bonus("OD") == bw.DESIGNATED_BONUS

    def test_eligible_scores_too_but_less(self):
        """Eligible is a STATUTORY LISTING - the Legislature added the route to S&H 263.1-263.8. The scenic
        criteria are applied by the nominating local government at DESIGNATION time, so an eligible-only
        route has never had them applied. It still scores, because the reason most eligible routes are never
        designated is that no local government filed a Corridor Protection Program, and having no local
        government to file correlates with being rural rather than with being unscenic."""
        assert 0 < bw.status_bonus("E") < bw.status_bonus("OD")

    def test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes(self):
        """Measured from the pinned pull: officially designated routes are 2512.5 km of the layer's
        12880.4 km, so 19.5% of the eligible system has ever been designated. That base rate times the
        designated weight is the FLOOR - what E is worth if it is worth only its chance of clearing the
        second gate. Half of OD is the ceiling this file will defend, because the criteria were never
        applied to an eligible-only route at all. Where E sits between them is a judgement; that it sits
        BETWEEN them is not.

        The pre-review value 0.10 was above this bracket, and it was derived from the false claim that
        eligibility is itself a scenic assessment."""
        floor = 0.195 * bw.DESIGNATED_BONUS
        ceiling = 0.5 * bw.DESIGNATED_BONUS
        assert floor <= bw.ELIGIBLE_BONUS <= ceiling, (floor, bw.ELIGIBLE_BONUS, ceiling)

    def test_an_unknown_status_scores_nothing_rather_than_guessing(self):
        assert bw.status_bonus("XYZ") == 0.0
        assert bw.status_bonus(None) == 0.0

    def test_no_status_exceeds_the_plans_per_term_allowance(self):
        """MAX_BONUS is enforced here rather than by a min() at the call site. At these values
        min(MAX_BONUS, status_bonus(...)) could never bind, so it looked like a check and was not one. This
        goes red the moment any weight is raised past the plan's +0.15."""
        for status in sorted(bw.KNOWN_STATUS):
            assert bw.status_bonus(status) <= bw.MAX_BONUS, status

    def test_unknown_statuses_are_detectable(self):
        """The field has NO published coded-value domain, so Caltrans can add a value without telling
        anyone. A new value would silently score zero, which reads as 'not a byway'."""
        assert bw.unknown_statuses(["OD", "E", None]) == set()
        assert bw.unknown_statuses(["OD", "NEW"]) == {"NEW"}


class TestTheCap:
    def test_the_cap_binds_on_es_total_not_on_the_bonus_term(self):
        """The plan says '+0.15 byway, capped'. The six base E terms already sum to 1.00, so a way at 0.95
        that is also designated must land at 1.0. Capping the bonus term alone never binds and never did."""
        assert bw.apply_to_e(0.95, bw.DESIGNATED_BONUS) == pytest.approx(bw.E_CEILING)

    def test_a_total_under_the_ceiling_is_untouched(self):
        assert bw.apply_to_e(0.50, bw.DESIGNATED_BONUS) == pytest.approx(0.65)

    def test_an_unmatched_way_keeps_its_base_score_exactly(self):
        assert bw.apply_to_e(0.42, 0.0) == pytest.approx(0.42)


class TestRouteKey:
    def test_a_ref_gives_up_its_route_numbers(self):
        assert bw.route_numbers("I 280;CA 35") == {"280", "35"}
        assert bw.route_numbers("I-280") == {"280"}
        assert bw.route_numbers("US 101") == {"101"}

    def test_a_business_route_is_not_the_mainline(self):
        """'US 101 Business' runs beside US 101 and is explicitly not it. Reading the digits out of the
        middle of a suffixed ref would hand it the mainline's designation."""
        assert bw.route_numbers("US 101 Business") == set()

    def test_an_absent_ref_claims_no_route(self):
        assert bw.route_numbers(None) == set()
        assert bw.route_numbers("") == set()

    def test_an_entry_with_no_route_key_falls_back_to_geometry(self):
        """The FHWA layer carries a trail name and no route number, so its entries cannot use this test."""
        assert bw.route_matches(set(), None) is True
        assert bw.route_matches(None, "CA 35") is True

    def test_an_entry_with_a_route_key_needs_the_way_to_name_it(self):
        assert bw.route_matches({"280"}, "I 280") is True
        assert bw.route_matches({"280"}, "CA 35") is False
        assert bw.route_matches({"280"}, None) is False

    def test_a_concurrency_names_both_routes(self):
        assert bw.route_matches({"35"}, "I 280;CA 35") is True


class TestDistance:
    def test_a_point_on_the_line_is_at_zero(self):
        assert bw.distance_to_line_m((37.49, -122.35), BYWAY) < 1.0

    def test_distance_is_not_directional(self):
        """Without the cos(latitude) factor an east-west offset reads ~26% further than it is at this
        latitude, and the snap tolerance silently becomes an ellipse.

        The offsets are chosen so the two distances are EQUAL when the correction is applied, and the
        tolerance is tight. An earlier version used a round 0.0056 deg and `rel=0.15`, which passed with the
        correction and passed without it - a mutation removing cos(lat) changed nothing, so the test was
        decorative for the exact thing it is named after.
        """
        lat, lon = 37.49, -122.35
        north_deg = 0.005
        # The east offset that is the same distance on the ground as `north_deg` of latitude.
        east_deg = north_deg * 110540.0 / (111320.0 * math.cos(math.radians(lat)))
        north = bw.distance_to_line_m((37.50 + north_deg, lon), BYWAY)
        east = bw.distance_to_line_m((lat, lon + east_deg), BYWAY)
        assert north == pytest.approx(east, rel=0.02), (north, east)

    def test_a_single_point_line_still_measures(self):
        assert bw.distance_to_line_m((37.49, -122.35), [(37.50, -122.35)]) > 0


class TestOverlap:
    def test_a_way_along_the_byway_overlaps_fully(self):
        assert bw.overlap_fraction(along(), BYWAY) == pytest.approx(1.0)

    def test_a_way_far_away_does_not_overlap(self):
        assert bw.overlap_fraction(along(offset_deg=0.02), BYWAY) == 0.0

    def test_a_frontage_road_just_outside_the_tolerance_does_not_overlap(self):
        """~100 m east. Note that this is the EASY case: real frontage roads sit 20-45 m out, inside the
        tolerance, which is why the route key and not the tolerance is what excludes them."""
        assert bw.overlap_fraction(along(offset_deg=0.00115), BYWAY) == 0.0

    def test_a_second_carriageway_just_inside_the_tolerance_does(self):
        """~30 m: the two halves of a divided highway are the same road."""
        assert bw.overlap_fraction(along(offset_deg=0.00034), BYWAY) > 0.9

    def test_overlap_is_measured_by_length_not_by_node_count(self):
        """OSM node density varies enormously - a curve is drawn with many nodes, a straight with two. By
        node count a short curly section would outvote a long straight one and the answer would depend on how
        the road was mapped."""
        curly = [(37.50 - i * 0.0002, -122.35) for i in range(11)]      # 10 short segments, on the byway
        straight_away = [(37.498, -122.35), (37.498, -122.30)]          # one long segment, far off it
        way = curly + straight_away[1:]
        assert bw.overlap_fraction(way, BYWAY) < 0.2

    def test_a_long_chord_is_credited_only_where_it_is_actually_near(self):
        """A single 2-node segment crossing the byway: both endpoints ~530 m off it, the midpoint on it.
        Judging one midpoint per OSM segment credited the WHOLE 1060 m as near and scored 1.0. Real OSM
        segments reach this length - 2.33% of inter-node segments in the measured corridors exceed 200 m and
        the longest is 858 m - so this is not synthetic paranoia.

        The near length must now be about 2x the tolerance - the band the way spends inside it. The 30 m
        slack is a LITERAL, not `bw.SAMPLE_STEP_M`: written against the constant, loosening the step to 500 m
        loosened the assertion with it and the mutation survived. A test whose tolerance comes from the thing
        it is testing measures nothing."""
        chord = [(37.49, -122.356), (37.49, -122.344)]
        total = length_m(chord)
        assert total > 1000, total
        near = bw.overlap_fraction(chord, BYWAY) * total
        assert near == pytest.approx(2 * bw.SNAP_TOLERANCE_M, abs=30.0), near

    def test_the_sampling_step_is_fine_enough_for_the_bound_to_mean_anything(self):
        """The guarantee is 'nothing further than tolerance + step/2 is credited as near'. At a step near or
        above the tolerance that sentence is true and worthless."""
        assert bw.SAMPLE_STEP_M <= bw.SNAP_TOLERANCE_M / 2, (bw.SAMPLE_STEP_M, bw.SNAP_TOLERANCE_M)

    def test_a_degenerate_way_overlaps_nothing(self):
        assert bw.overlap_fraction([(37.5, -122.35)], BYWAY) == 0.0


class TestMatching:
    def _entries(self):
        return [
            {"name": "Skyline", "status": "OD", "source": "caltrans", "geometry": BYWAY},
            {"name": "Other", "status": "E", "source": "caltrans", "geometry": BYWAY},
        ]

    def test_a_way_on_the_byway_matches_it(self):
        m = bw.match(along(), self._entries())
        assert m is not None and m["overlap"] == pytest.approx(1.0)

    def test_the_stronger_designation_wins_a_tie(self):
        assert bw.match(along(), self._entries())["status"] == "OD"

    def test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more(self):
        """The gate is where 'is this the same road' is decided. Past it, overlap fraction measures how much
        of the OSM way a corridor covers - a function of where OSM split the way - and does not say which
        designation to carry. Ordering by overlap first let a 70%-overlapping ELIGIBLE corridor beat a
        60%-overlapping DESIGNATED one, contradicting this module's own stated intent."""
        way = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35), (37.46, -122.35)]
        eligible_line = [(37.501, -122.35), (37.472, -122.35)]      # covers ~70% of the way
        designated_line = [(37.501, -122.35), (37.476, -122.35)]    # covers ~60%
        e_frac = bw.overlap_fraction(way, eligible_line)
        d_frac = bw.overlap_fraction(way, designated_line)
        assert e_frac > d_frac >= bw.MIN_OVERLAP_FRACTION, (e_frac, d_frac)
        entries = [{"name": "eligible one", "status": "E", "geometry": eligible_line},
                   {"name": "designated one", "status": "OD", "geometry": designated_line}]
        assert bw.match(way, entries)["status"] == "OD"
        assert bw.bonus_for(way, entries) == bw.DESIGNATED_BONUS

    def test_a_cross_street_touching_at_a_junction_does_not_match(self):
        """It shares a node with the byway and nothing else. Without a minimum overlap it would inherit the
        designation from a single point of contact."""
        cross = [(37.49, -122.35), (37.49, -122.34), (37.49, -122.33)]
        assert bw.match(cross, self._entries()) is None

    def test_a_way_nowhere_near_matches_nothing(self):
        assert bw.match(along(offset_deg=0.05), self._entries()) is None

    def test_an_entry_with_no_geometry_is_skipped_not_matched(self):
        assert bw.match(along(), [{"name": "x", "status": "OD", "geometry": []}]) is None

    def test_a_way_lying_on_a_numbered_route_still_needs_to_claim_it(self):
        """The frontage road, in miniature. Geometry alone matches - it is right on top of the corridor -
        and the route key is the only thing that stops it inheriting the designation."""
        entries = [{"name": "CA SM route 280", "status": "OD", "source": "caltrans",
                    "routes": {"280"}, "geometry": BYWAY}]
        assert bw.overlap_fraction(along(), BYWAY) == pytest.approx(1.0)
        assert bw.match(along(), entries, way_ref=None) is None
        assert bw.match(along(), entries, way_ref="CA 35") is None
        assert bw.match(along(), entries, way_ref="I 280")["status"] == "OD"


class TestBonus:
    def test_a_designated_way_earns_the_full_bonus(self):
        entries = [{"name": "Skyline", "status": "OD", "geometry": BYWAY}]
        assert bw.bonus_for(along(), entries) == bw.DESIGNATED_BONUS

    def test_an_eligible_way_earns_less(self):
        entries = [{"name": "Somewhere", "status": "E", "geometry": BYWAY}]
        assert 0 < bw.bonus_for(along(), entries) < bw.DESIGNATED_BONUS

    def test_an_unmatched_way_earns_nothing(self):
        entries = [{"name": "Skyline", "status": "OD", "geometry": BYWAY}]
        assert bw.bonus_for(along(offset_deg=0.05), entries) == 0.0


class TestProblems:
    def test_a_healthy_set_has_no_problems(self):
        assert bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "E", "geometry": BYWAY}]) == []

    def test_an_empty_pull_is_reported(self):
        """An empty overlay flags nothing and looks exactly like a clean run."""
        assert any("no byways parsed" in p for p in bw.problems([]))

    def test_an_unrecognised_status_is_reported(self):
        problems = bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "NEW", "geometry": BYWAY}])
        assert any("unrecognised Status" in p for p in problems)

    def test_geometryless_entries_are_reported(self):
        problems = bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "E", "geometry": []}])
        assert any("no usable geometry" in p for p in problems)

    def test_a_pull_with_no_designated_byways_at_all_is_suspicious(self):
        problems = bw.problems([{"status": "E", "geometry": BYWAY}])
        assert any("no officially designated" in p for p in problems)

    def test_a_caltrans_entry_that_lost_its_route_key_is_reported(self):
        """Without RTE a Caltrans entry can only match on distance, which is exactly the mode that hands a
        frontage road the freeway's designation."""
        problems = bw.problems([{"status": "OD", "source": "caltrans", "routes": {"35"}, "geometry": BYWAY},
                                {"status": "E", "source": "caltrans", "routes": set(), "geometry": BYWAY}])
        assert any("no route key" in p for p in problems)
