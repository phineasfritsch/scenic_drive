"""The snapping geometry: how close a way runs to a reference line, and how much of it does.

The failure worth guarding here is arithmetic that is silently directional or silently coarse - a tolerance
that is an ellipse because cos(latitude) was dropped, or an overlap that credits a whole 1 km chord because
one midpoint happened to land on the line. Both were real; both are pinned below.
"""
from __future__ import annotations

import math

import pytest

from etl import snap
from etl.curvature import distance_on_earth

# A north-south line near Skyline, and a way running along it.
BYWAY = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]


def along(offset_deg=0.0, n=4, start=37.50, lon=-122.35):
    return [(start - i * 0.01, lon + offset_deg) for i in range(n)]


def length_m(way):
    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(way, way[1:]))


class TestDistance:
    def test_a_point_on_the_line_is_at_zero(self):
        assert snap.distance_to_line_m((37.49, -122.35), BYWAY) < 1.0

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
        north = snap.distance_to_line_m((37.50 + north_deg, lon), BYWAY)
        east = snap.distance_to_line_m((lat, lon + east_deg), BYWAY)
        assert north == pytest.approx(east, rel=0.02), (north, east)

    def test_a_single_point_line_still_measures(self):
        assert snap.distance_to_line_m((37.49, -122.35), [(37.50, -122.35)]) > 0


class TestOverlap:
    def test_a_way_along_the_byway_overlaps_fully(self):
        assert snap.overlap_fraction(along(), BYWAY) == pytest.approx(1.0)

    def test_a_way_far_away_does_not_overlap(self):
        assert snap.overlap_fraction(along(offset_deg=0.02), BYWAY) == 0.0

    def test_a_frontage_road_just_outside_the_tolerance_does_not_overlap(self):
        """~100 m east. Note that this is the EASY case: real frontage roads sit 20-45 m out, inside the
        tolerance, which is why the route key and not the tolerance is what excludes them."""
        assert snap.overlap_fraction(along(offset_deg=0.00115), BYWAY) == 0.0

    def test_a_second_carriageway_just_inside_the_tolerance_does(self):
        """~30 m: the two halves of a divided highway are the same road."""
        assert snap.overlap_fraction(along(offset_deg=0.00034), BYWAY) > 0.9

    def test_overlap_is_measured_by_length_not_by_node_count(self):
        """OSM node density varies enormously - a curve is drawn with many nodes, a straight with two. By
        node count a short curly section would outvote a long straight one and the answer would depend on how
        the road was mapped."""
        curly = [(37.50 - i * 0.0002, -122.35) for i in range(11)]      # 10 short segments, on the byway
        straight_away = [(37.498, -122.35), (37.498, -122.30)]          # one long segment, far off it
        way = curly + straight_away[1:]
        assert snap.overlap_fraction(way, BYWAY) < 0.2

    def test_a_long_chord_is_credited_only_where_it_is_actually_near(self):
        """A single 2-node segment crossing the byway: both endpoints ~530 m off it, the midpoint on it.
        Judging one midpoint per OSM segment credited the WHOLE 1060 m as near and scored 1.0. Real OSM
        segments reach this length - 2.33% of inter-node segments in the measured corridors exceed 200 m and
        the longest is 858 m - so this is not synthetic paranoia.

        The near length must now be about 2x the tolerance - the band the way spends inside it. The 30 m
        slack is a LITERAL, not `snap.SAMPLE_STEP_M`: written against the constant, loosening the step to 500 m
        loosened the assertion with it and the mutation survived. A test whose tolerance comes from the thing
        it is testing measures nothing."""
        chord = [(37.49, -122.356), (37.49, -122.344)]
        total = length_m(chord)
        assert total > 1000, total
        near = snap.overlap_fraction(chord, BYWAY) * total
        assert near == pytest.approx(2 * snap.SNAP_TOLERANCE_M, abs=30.0), near

    def test_the_sampling_step_is_fine_enough_for_the_bound_to_mean_anything(self):
        """The guarantee is 'nothing further than tolerance + step/2 is credited as near'. At a step near or
        above the tolerance that sentence is true and worthless."""
        assert snap.SAMPLE_STEP_M <= snap.SNAP_TOLERANCE_M / 2, (snap.SAMPLE_STEP_M, snap.SNAP_TOLERANCE_M)

    def test_a_degenerate_way_overlaps_nothing(self):
        assert snap.overlap_fraction([(37.5, -122.35)], BYWAY) == 0.0

