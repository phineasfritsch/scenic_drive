"""A wrong heading is worse than none: it looks like an answer."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl import streetview as sv  # noqa: E402

# Sunset Blvd through Bel-Air, west to east.
SUNSET = [(34.0736, -118.4630), (34.0745, -118.4585), (34.0751, -118.4540)]


def test_bearing_cardinals():
    assert sv.bearing(34.0, -118.0, 35.0, -118.0) == pytest.approx(0.0, abs=0.5)      # north
    assert sv.bearing(34.0, -118.0, 34.0, -117.0) == pytest.approx(90.0, abs=0.5)     # east
    assert sv.bearing(34.0, -118.0, 33.0, -118.0) == pytest.approx(180.0, abs=0.5)    # south
    assert sv.bearing(34.0, -118.0, 34.0, -119.0) == pytest.approx(270.0, abs=0.5)    # west


def test_bearing_refuses_a_point_too_close_to_define_a_direction():
    """None, never 0. Zero means due north and would be a silent lie."""
    assert sv.bearing(34.0, -118.0, 34.0, -118.0) is None
    assert sv.bearing(34.0, -118.0, 34.0000001, -118.0000001) is None


def test_bearing_refuses_nan():
    assert sv.bearing(float("nan"), -118.0, 34.0, -118.0) is None


def test_url_shape_and_precision():
    u = sv.pano_url(34.0689, -118.4452, 76.4)
    assert u.startswith("https://www.google.com/maps/@?")
    assert "map_action=pano" in u
    assert "viewpoint=34.068900,-118.445200" in u
    assert "heading=76.4" in u


def test_url_omits_heading_when_there_is_none():
    assert "heading" not in sv.pano_url(34.0689, -118.4452, None)


def test_url_is_never_the_static_api():
    """The whole legal argument is that this emits a link a person opens, not an image request.

    Pinned as a test rather than left to the docstring, because 'just fetch the thumbnail' is the obvious
    next feature and it is the one that turns the app's map stack into a licensing problem.
    """
    u = sv.pano_url(34.0689, -118.4452, 0.0)
    assert "streetview" not in u and "key=" not in u and "/api/" not in u


def test_url_rejects_impossible_coordinates():
    with pytest.raises(ValueError):
        sv.pano_url(91.0, -118.0)
    with pytest.raises(ValueError):
        sv.pano_url(34.0, 181.0)
    with pytest.raises(ValueError):
        sv.pano_url(float("nan"), -118.0)


def test_look_along_faces_down_the_road():
    """The expected heading is derived HERE, not read back out of `sv.bearing`.

    The first draft asserted `f"heading={sv.bearing(*SUNSET[0], *SUNSET[1]):.1f}"` - an expectation computed
    by the thing under test, which passes for any pair of consistent-but-wrong functions and leans on
    `test_bearing_cardinals` to notice.

    Sunset's first leg runs 0.0009 deg north and 0.0045 deg east of (34.0736, -118.4630). On the local
    plane that is 0.0009 * 111320 = 100.2 m north and 0.0045 * 111320 * cos(34.074 deg) = 414.9 m east, so
    the heading is atan2(414.9, 100.2) = 76.43 deg. Over a 430 m leg the great-circle answer differs from
    the flat one by thousandths of a degree, far inside the one decimal place the URL carries.
    """
    assert "heading=76.4" in sv.look_along(SUNSET, 0)


def test_look_along_at_the_last_point_uses_the_previous_one():
    """A way should aim the same way along itself from either end, not lose its heading at the tail."""
    assert "heading=" in sv.look_along(SUNSET, len(SUNSET) - 1)


def test_a_single_point_gets_no_heading_rather_than_a_fabricated_one():
    assert "heading" not in sv.look_along([(34.0, -118.0)], 0)


def test_midpoint_is_by_length_not_by_index():
    """The defect this test exists for: the first implementation returned the index of the SEGMENT holding
    the half-way mark, which for an evenly drawn way is 0 - the START of the road."""
    assert sv.midpoint_index(SUNSET) == 1

    # Four tightly spaced points then one far away. The index midpoint is 2; the LENGTH midpoint is not.
    skewed = [(34.0, -118.0), (34.0, -117.999), (34.0, -117.998), (34.0, -117.997), (34.0, -117.90)]
    assert sv.midpoint_index(skewed) == 3, "by index this would be 2"


def test_midpoint_of_degenerate_geometry():
    assert sv.midpoint_index([(34.0, -118.0)]) == 0
    assert sv.midpoint_index([(34.0, -118.0)] * 5) == 0     # every point identical: no middle to find


def test_midpoint_refuses_empty():
    with pytest.raises(ValueError):
        sv.midpoint_index([])
