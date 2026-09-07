"""Every constant the Curvature reimplementation copies from upstream, pinned against a LITERAL.

This file exists because of a defect that has now been found three times in this task, each time one level
further out, and each time by someone who had just been told about the previous one:

  1. `MAX_RADIUS` and `DEGENERATE_RADIUS` were asserted only as `cv.MAX_RADIUS == cv.MAX_RADIUS`-shaped
     comparisons, so sweeping them 175 -> 100000 and 0 -> inf changed nothing (agent/reviewer-34, round 3).
  2. Fixing those, I wrote a class that deliberately EXCLUDED `RAD_EARTH_M` on the grounds that
     `test_distance_matches_a_known_separation` already pinned it. It did not. That test read
     `expected = cv.RAD_EARTH_M * math.pi / 180` and compared it against `acos(...) * RAD_EARTH_M` - both
     sides scale with the constant, and the whole thing passes at `RAD_EARTH_M = 1` (reviewer-34, round 4).
     So the one constant the oracle explicitly RECORDS as invisible to it was guarded by nothing at all.
  3. `SQUASH_RADIUS_M` and `CELL_DEG` in `oracle_select.py` had it too; they are pinned in
     `test_oracle_select.py` for the same reason.

The lesson is written here rather than in a commit message because it is the reason this file exists: when a
test compares a computed value against an expression containing the constant under test, it is checking the
arithmetic and nothing else. The 2% oracle cannot see a constant either - `test_curvature.py` records that as
a deliberate negative result for the earth radius. So constants get literals, and only literals.
"""
from __future__ import annotations

import math

import pytest

from etl import curvature as cv


class TestTheUpstreamConstantsArePinnedByValue:
    """Each literal is the value in the named upstream file, not a value derived from our own module."""

    def test_the_earth_radius(self):
        # geomath.py: rad_earth_m = 6373000. NOT WGS84's 6378137 - matching the oracle beats being right,
        # and `test_the_earth_radius_is_NOT_detectable_at_this_tolerance` records that the oracle cannot
        # tell the difference. That is exactly why it needs a literal here.
        assert cv.RAD_EARTH_M == 6373000

    def test_the_radius_caps(self):
        # add_segment_length_and_radius.py: MAX_RADIUS = 10000
        assert cv.MAX_RADIUS == 10000.0
        # radiusmath.py returns this for a zero-area or zero-length triangle. Equal to MAX_RADIUS today, and
        # separately named because upstream makes them separately, in different files.
        assert cv.DEGENERATE_RADIUS == 10000.0

    def test_the_curvature_bands(self):
        # add_segment_curvature.py, in the order it tests them, with strict `<`.
        assert cv.LEVELS == ((30.0, 4, 2.0), (60.0, 3, 1.6), (100.0, 2, 1.3), (175.0, 1, 1.0))

    def test_the_deflection_filter_constants(self):
        # filter_segment_deflections.py: min_variance = gap_distance / level_1_max_radius, look-aheads 3..7.
        assert cv.LEVEL_1_MAX_RADIUS == 175.0
        assert cv.LOOK_AHEADS == (3, 4, 5, 6, 7)
        # The band edge and the filter's divisor are the SAME upstream number. Tuning one without the other
        # silently changes two behaviours and matches neither.
        assert cv.LEVELS[-1][0] == cv.LEVEL_1_MAX_RADIUS


class TestTheDistanceIsInRealMetres:
    def test_one_degree_of_latitude(self):
        """The check `test_distance_matches_a_known_separation` was supposed to be and was not.

        The literal 6373000 lives HERE, in the test. Swapping the module's constant now fails this; before,
        it changed both sides of the comparison and failed nothing.
        """
        assert cv.distance_on_earth(44.0, -72.8, 45.0, -72.8) == \
            pytest.approx(6373000 * math.pi / 180, rel=1e-9)

    def test_a_degree_of_longitude_is_shorter_this_far_north(self):
        """Anchors the shape of the formula, not just its scale: at 44N a degree of longitude is cos(44)
        of a degree of latitude, so a test that only checked one distance would miss a formula that had
        lost its latitude term."""
        lat_deg = cv.distance_on_earth(44.0, -72.8, 45.0, -72.8)
        lon_deg = cv.distance_on_earth(44.0, -72.8, 44.0, -71.8)
        assert lon_deg / lat_deg == pytest.approx(math.cos(math.radians(44.0)), rel=1e-3)
