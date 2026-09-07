"""Byway snapping and the Eligible-versus-Designated decision.

The failure worth guarding is not a crash. It is a frontage road inheriting the freeway's designation, or a
cross street inheriting a byway's because it touches one at a junction - both produce a road that scores as
scenic because of a road next to it.
"""
from __future__ import annotations

import pytest

from etl import byways as bw

# A north-south line near Skyline, and a way running along it.
BYWAY = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]


def along(offset_deg=0.0, n=4, start=37.50, lon=-122.35):
    return [(start - i * 0.01, lon + offset_deg) for i in range(n)]


class TestStatusMeaning:
    def test_officially_designated_scores_the_full_bonus(self):
        assert bw.status_bonus("OD") == bw.DESIGNATED_BONUS

    def test_eligible_scores_too_but_less(self):
        """Eligible is the state's own assessment of the LANDSCAPE. Official designation additionally
        requires a local government to have applied and adopted a Corridor Protection Program, which is
        paperwork, not scenery. Scoring only OD would drop 207 of 273 Caltrans segments - and would drop
        rural corridors hardest, because they are the ones with no local government to file."""
        assert 0 < bw.status_bonus("E") < bw.status_bonus("OD")

    def test_an_unknown_status_scores_nothing_rather_than_guessing(self):
        assert bw.status_bonus("XYZ") == 0.0
        assert bw.status_bonus(None) == 0.0

    def test_the_bonus_is_capped_at_the_plans_allowance(self):
        assert bw.DESIGNATED_BONUS <= bw.MAX_BONUS

    def test_unknown_statuses_are_detectable(self):
        """The field has NO published coded-value domain, so Caltrans can add a value without telling
        anyone. A new value would silently score zero, which reads as 'not a byway'."""
        assert bw.unknown_statuses(["OD", "E", None]) == set()
        assert bw.unknown_statuses(["OD", "NEW"]) == {"NEW"}


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
        import math
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
        """~100 m east. At a loose tolerance a frontage road collects the freeway's designation."""
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
        """A segment along both an eligible and a designated corridor takes the designated one - the
        stronger evidence is the one worth carrying."""
        assert bw.match(along(), self._entries())["status"] == "OD"

    def test_a_cross_street_touching_at_a_junction_does_not_match(self):
        """It shares a node with the byway and nothing else. Without a minimum overlap it would inherit the
        designation from a single point of contact."""
        cross = [(37.49, -122.35), (37.49, -122.34), (37.49, -122.33)]
        assert bw.match(cross, self._entries()) is None

    def test_a_way_nowhere_near_matches_nothing(self):
        assert bw.match(along(offset_deg=0.05), self._entries()) is None

    def test_an_entry_with_no_geometry_is_skipped_not_matched(self):
        assert bw.match(along(), [{"name": "x", "status": "OD", "geometry": []}]) is None


class TestBonus:
    def test_a_designated_way_earns_the_capped_bonus(self):
        entries = [{"name": "Skyline", "status": "OD", "geometry": BYWAY}]
        assert bw.bonus_for(along(), entries) == bw.MAX_BONUS

    def test_an_eligible_way_earns_less(self):
        entries = [{"name": "Somewhere", "status": "E", "geometry": BYWAY}]
        assert 0 < bw.bonus_for(along(), entries) < bw.MAX_BONUS

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
