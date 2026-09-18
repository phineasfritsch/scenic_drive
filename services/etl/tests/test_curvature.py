"""Curvature, checked against the Curvature project's published Vermont values.

The oracle is theirs, not ours. That is the whole point: a fixture regenerated from our own output would
bless whatever error we had, which is the trap T-0011 hit and rejected with the solar fixtures. These values
come out of `vermont.c_300.kmz`, pinned by sha256 in the manifest, and every way in the fixture is one the
five-step method is provably comparable on - see the `selection` list inside the fixture for the three
conditions and why each excludes what it does.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from etl import curvature as cv

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "curvature_oracle.json"
TOLERANCE = 0.02          # the brief's 2%
MIN_AGREEMENT = 0.93      # measured 95.0% on the full eligible set of 2307; floor set below it, not at it


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def circle(radius_m: float, n: int = 24, lat0: float = 44.0, lon0: float = -72.8):
    """n points evenly around a circle of the given radius, as (lat, lon)."""
    deg_lat = radius_m / (cv.RAD_EARTH_M * math.pi / 180)
    deg_lon = deg_lat / math.cos(math.radians(lat0))
    return [(lat0 + deg_lat * math.sin(2 * math.pi * i / n),
             lon0 + deg_lon * math.cos(2 * math.pi * i / n)) for i in range(n + 1)]


class TestGeometryPrimitives:
    def test_distance_matches_a_known_separation(self):
        # One degree of latitude on their sphere: rad_earth_m * pi/180.
        expected = cv.RAD_EARTH_M * math.pi / 180
        assert cv.distance_on_earth(44.0, -72.8, 45.0, -72.8) == pytest.approx(expected, rel=1e-9)

    def test_identical_points_are_zero_distance(self):
        assert cv.distance_on_earth(44.0, -72.8, 44.0, -72.8) == 0.0

    def test_two_points_a_metre_apart_do_not_blow_up(self):
        """Their `cos > 1` guard. Without it acos raises on short segments, which is most segments."""
        d = cv.distance_on_earth(44.0, -72.8, 44.000009, -72.8)
        assert 0.0 <= d < 2.0

    def test_the_circumcircle_of_a_known_triangle(self):
        # 3-4-5 right triangle: circumradius is half the hypotenuse.
        assert cv.circum_circle_radius(3, 4, 5) == pytest.approx(2.5, rel=1e-12)

    def test_an_equilateral_triangle(self):
        assert cv.circum_circle_radius(1, 1, 1) == pytest.approx(1 / math.sqrt(3), rel=1e-12)

    @pytest.mark.parametrize("sides", [(0, 1, 1), (1, 0, 1), (1, 1, 0), (-1, 1, 1)])
    def test_a_degenerate_triangle_returns_the_flat_radius(self, sides):
        assert cv.circum_circle_radius(*sides) == cv.DEGENERATE_RADIUS

    def test_collinear_points_do_not_raise(self):
        """math.fabs inside their sqrt is what stops a triangle-inequality violation being a domain error."""
        assert cv.circum_circle_radius(1.0, 1.0, 2.0) >= cv.DEGENERATE_RADIUS


class TestRadiiOnKnownGeometry:
    def test_a_circle_of_known_radius_is_recovered(self):
        """The strongest check that does not need the oracle: points on a circle of radius R must yield R."""
        for radius in (30.0, 100.0, 400.0):
            segments = cv.segments_for(circle(radius))
            cv.assign_radii(segments)
            interior = [s.radius for s in segments[1:-1]]
            assert all(abs(r - radius) / radius < 0.02 for r in interior), (radius, interior[:3])

    def test_a_straight_line_is_flat(self):
        coords = [(44.0 + i * 0.001, -72.8) for i in range(10)]
        segments = cv.segments_for(coords)
        cv.assign_radii(segments)
        assert all(s.radius > cv.LEVEL_1_MAX_RADIUS for s in segments)

    def test_a_single_segment_way_is_straight_by_definition(self):
        segments = cv.segments_for([(44.0, -72.8), (44.001, -72.8)])
        cv.assign_radii(segments)
        assert segments[0].radius == cv.MAX_RADIUS

    def test_only_the_last_segment_is_capped(self):
        """Their cap lives in the `else` branch, so interior radii can exceed MAX_RADIUS. Bug-compatible."""
        coords = [(44.0 + i * 0.01, -72.8 + (0.0000001 if i == 2 else 0)) for i in range(6)]
        segments = cv.segments_for(coords)
        cv.assign_radii(segments)
        assert segments[-1].radius <= cv.MAX_RADIUS
        assert any(s.radius > cv.MAX_RADIUS for s in segments[:-1])


class TestWeighting:
    @pytest.mark.parametrize("radius,level,weight", [
        (10.0, 4, 2.0), (29.999, 4, 2.0), (30.0, 3, 1.6), (59.999, 3, 1.6),
        (60.0, 2, 1.3), (99.999, 2, 1.3), (100.0, 1, 1.0), (174.999, 1, 1.0),
        (175.0, 0, 0.0), (10000.0, 0, 0.0),
    ])
    def test_each_band_and_its_boundary(self, radius, level, weight):
        s = cv.Segment(start=(0, 0), end=(0, 0), length=100.0, radius=radius)
        cv.assign_curvature([s])
        assert s.curvature_level == level
        assert s.curvature == pytest.approx(100.0 * weight)


class TestAgainstTheCurvatureProject:
    """The oracle. Values from their code, over the same OSM ways, with the same geometry."""

    def test_the_fixture_says_how_it_was_selected(self):
        doc = load()
        assert doc["source"].endswith("vermont.c_300.kmz")
        assert doc["source_sha256"]
        assert len(doc["selection"]) >= 3, "a subset without written criteria is a cherry-pick"

    def test_the_fixture_is_not_trivially_small(self):
        assert len(load()["ways"]) >= 200

    def test_agreement_with_the_published_values(self):
        doc = load()
        errors = []
        for way in doc["ways"]:
            got = cv.way_curvature([tuple(c) for c in way["coords"]], way["way_id"])
            want = way["oracle_curvature"]
            errors.append((abs(got - want) / want, way["way_id"], got, want))
        within = [e for e in errors if e[0] <= TOLERANCE]
        share = len(within) / len(errors)
        worst = sorted(errors, reverse=True)[:5]
        assert share >= MIN_AGREEMENT, (
            f"only {share:.1%} of {len(errors)} ways agree within {TOLERANCE:.0%}; worst: "
            + ", ".join(f"way {w} got {g:.1f} want {t:.1f} ({e:.1%})" for e, w, g, t in worst)
        )

    def test_the_typical_way_agrees_far_more_closely_than_the_tolerance(self):
        """A 2% pass rate can hide a systematic bias. The median is what shows there is not one."""
        doc = load()
        errors = sorted(abs(cv.way_curvature([tuple(c) for c in w["coords"]], w["way_id"]) - w["oracle_curvature"])
                        / w["oracle_curvature"] for w in doc["ways"])
        assert errors[len(errors) // 2] < 0.005

    def _agreement(self, **kw):
        doc = load()
        errors = [abs(cv.way_curvature([tuple(c) for c in w["coords"]], w["way_id"], **kw) - w["oracle_curvature"])
                  / w["oracle_curvature"] for w in doc["ways"]]
        return sum(1 for e in errors if e <= TOLERANCE) / len(errors)

    def test_changing_a_weight_fails_the_oracle(self, monkeypatch):
        """The oracle has to be able to reject something, or it is decoration."""
        monkeypatch.setattr(cv, "LEVELS", ((30.0, 4, 1.0), (60.0, 3, 1.6), (100.0, 2, 1.3), (175.0, 1, 1.0)))
        assert self._agreement() < MIN_AGREEMENT

    def test_moving_a_band_threshold_fails_the_oracle(self, monkeypatch):
        monkeypatch.setattr(cv, "LEVELS", ((30.0, 4, 2.0), (60.0, 3, 1.6), (100.0, 2, 1.3), (250.0, 1, 1.0)))
        assert self._agreement() < MIN_AGREEMENT

    def test_taking_the_larger_of_the_two_circumcircles_fails_the_oracle(self, monkeypatch):
        """Their comment says the smaller radius was a deliberate choice. This is what the other choice costs."""
        original = cv.assign_radii

        def larger(segments):
            original(segments)
            for i in range(1, len(segments) - 1):
                segments[i].radius = max(segments[i].radius, segments[i - 1].radius)
        monkeypatch.setattr(cv, "assign_radii", larger)
        assert self._agreement() < MIN_AGREEMENT

    def test_the_earth_radius_is_NOT_detectable_at_this_tolerance(self, monkeypatch):
        """Recorded because it is worth knowing what 2% cannot see.

        `rad_earth_m = 6373000` is not WGS84's 6378137, and swapping it is exactly the tidy-up an agent
        would make. It scales every length by 0.08%, which a 2% tolerance cannot notice - agreement moves
        from ~95% to ~94%. So this oracle verifies the ALGORITHM, not the constant. The constant is held by
        `test_distance_matches_a_known_separation` instead, which compares against an exact value.
        """
        monkeypatch.setattr(cv, "RAD_EARTH_M", 6378137)
        assert self._agreement() > 0.90

    def test_dropping_the_deflection_filter_fails_the_oracle(self):
        """Same argument for the filter: if removing it changes nothing, it was never being tested."""
        doc = load()
        errors = [abs(cv.way_curvature([tuple(c) for c in w["coords"]], w["way_id"], deflection_filter=False)
                      - w["oracle_curvature"]) / w["oracle_curvature"] for w in doc["ways"]]
        share = sum(1 for e in errors if e <= TOLERANCE) / len(errors)
        assert share < MIN_AGREEMENT, f"the deflection filter is not load-bearing here ({share:.1%})"
