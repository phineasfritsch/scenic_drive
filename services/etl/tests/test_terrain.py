"""Terrain arithmetic, checked on geometry whose answer is known before the code runs.

The failure this guards is not a crash. It is a flat road scoring as a climb, which makes every bay-margin
street compete with Skyline, and nothing downstream can tell the difference between real gain and DEM noise
once it has been summed.
"""
from __future__ import annotations

import math

import pytest

from etl import terrain as tr

FLAT = 44.0, -72.8


def profile(values):
    return list(values)


def line_north(start, count, step_deg=0.00025):
    """A straight north-south way; 0.00025 deg of latitude is about 28 m."""
    lat, lon = start
    return [(lat + i * step_deg, lon) for i in range(count)]


class TestSmoothing:
    def test_a_flat_grid_stays_flat(self):
        grid = [[10.0] * 5 for _ in range(5)]
        assert tr.smooth3x3(grid) == grid

    def test_a_single_spike_is_flattened(self):
        """One noisy cell is what invents gain. After smoothing it must be a fraction of its height."""
        grid = [[10.0] * 5 for _ in range(5)]
        grid[2][2] = 40.0
        out = tr.smooth3x3(grid)
        assert out[2][2] == pytest.approx(10.0 + 30.0 / 9)
        assert out[2][2] < 15.0

    def test_nodata_is_skipped_not_treated_as_zero(self):
        """Averaging NODATA in as 0 would pull every coastal cell toward sea level and invent a shoreline
        cliff - a bug shaped exactly like the feature this score rewards."""
        grid = [[100.0, 100.0, None], [100.0, 100.0, None], [100.0, 100.0, None]]
        out = tr.smooth3x3(grid)
        assert out[1][1] == pytest.approx(100.0)
        assert out[0][0] == pytest.approx(100.0)

    def test_a_cell_with_no_valid_neighbour_stays_nodata(self):
        assert tr.smooth3x3([[None]])[0][0] is None

    def test_an_empty_grid_does_not_raise(self):
        assert tr.smooth3x3([]) == []


class TestResampling:
    def test_a_way_is_sampled_at_a_fixed_step(self):
        """Two drawings of the same road must give the same answer, however finely each was mapped."""
        coarse = [(44.0, -72.8), (44.01, -72.8)]           # ~1112 m, two nodes
        fine = line_north((44.0, -72.8), 41, 0.00025)      # same road, 41 nodes
        n_coarse = len(tr.resample(coarse))
        n_fine = len(tr.resample(fine))
        assert abs(n_coarse - n_fine) <= 2, (n_coarse, n_fine)

    def test_the_endpoints_are_kept(self):
        coords = [(44.0, -72.8), (44.01, -72.8)]
        out = tr.resample(coords)
        assert out[0] == coords[0]
        assert out[-1] == coords[-1]

    def test_a_degenerate_way_is_returned_unchanged(self):
        assert tr.resample([(44.0, -72.8)]) == [(44.0, -72.8)]
        assert tr.resample([]) == []

    def test_repeated_nodes_do_not_divide_by_zero(self):
        coords = [(44.0, -72.8), (44.0, -72.8), (44.001, -72.8)]
        assert len(tr.resample(coords)) >= 2


class TestElevationGain:
    def test_a_flat_profile_gains_nothing(self):
        assert tr.elevation_gain([10.0] * 20) == 0.0

    def test_a_monotonic_climb_gains_its_height(self):
        assert tr.elevation_gain([0.0, 10.0, 20.0, 30.0]) == pytest.approx(30.0)

    def test_a_descent_gains_nothing(self):
        assert tr.elevation_gain([30.0, 20.0, 10.0, 0.0]) == 0.0

    def test_a_rolling_profile_counts_only_the_ups(self):
        assert tr.elevation_gain([0.0, 10.0, 0.0, 10.0, 0.0]) == pytest.approx(20.0)

    def test_noise_below_the_floor_is_not_climb(self):
        """The Alviso property in miniature: +/-0.3 m of DEM noise over a flat road is not a climb."""
        noisy = [10.0 + (0.3 if i % 2 else 0.0) for i in range(200)]
        assert tr.elevation_gain(noisy) == 0.0

    def test_noise_without_a_floor_would_have_scored_a_climb(self):
        """The same profile with the floor removed - proof the floor is load-bearing, not decoration."""
        noisy = [10.0 + (0.3 if i % 2 else 0.0) for i in range(200)]
        assert tr.elevation_gain(noisy, noise_floor_m=0.0) > 25.0

    def test_a_gap_is_bridged_rather_than_counted_as_a_step(self):
        """A bridge or a tile edge must not read as a fall to nothing and a climb back out."""
        assert tr.elevation_gain([100.0, None, None, 100.0]) == 0.0
        assert tr.elevation_gain([100.0, None, 130.0]) == pytest.approx(30.0)

    def test_an_all_nodata_profile_gains_nothing_rather_than_raising(self):
        assert tr.elevation_gain([None, None, None]) == 0.0


class TestGainPerKm:
    def test_it_normalises_by_length(self):
        assert tr.gain_per_km([0.0, 100.0], 2000.0) == pytest.approx(50.0)

    def test_zero_length_is_zero_not_a_division_error(self):
        assert tr.gain_per_km([0.0, 100.0], 0.0) == 0.0


class TestRelief:
    def test_a_flat_profile_has_no_relief(self):
        assert tr.relief([10.0] * 100) == 0.0

    def test_it_is_the_range_within_a_window(self):
        assert tr.relief([0.0, 50.0, 100.0], step_m=25.0) == pytest.approx(100.0)

    def test_a_long_steady_climb_is_not_more_dramatic_than_a_short_one(self):
        """Whole-way range would say a 40 km road climbing 600 m has as much relief as a 1 km road that
        climbs the same. It does not - relief is how much the land moves around you, not how far you get.

        The two profiles climb EXACTLY the same 600 m on purpose. An earlier version used 599.6 and 600,
        which passed with or without the windowing - a mutation replacing the window with a whole-way range
        did not fail it. Making the totals identical is what forces the windowing to be the thing under test.
        """
        long_climb = [i * (600.0 / 1599) for i in range(1600)]   # 600 m over 40 km at a 25 m step
        short_climb = [i * (600.0 / 40) for i in range(41)]      # the same 600 m over 1 km
        assert max(long_climb) == pytest.approx(max(short_climb)), "the totals must match or this proves nothing"
        assert tr.relief(long_climb) < tr.relief(short_climb) / 10

    def test_nodata_does_not_become_sea_level(self):
        assert tr.relief([500.0, None, 505.0]) == pytest.approx(5.0)

    def test_a_short_profile_does_not_raise(self):
        assert tr.relief([]) == 0.0
        assert tr.relief([42.0]) == 0.0


class TestGrade:
    def test_a_flat_road_has_no_grade(self):
        assert tr.grade_percent([10.0] * 50) == 0.0

    def test_a_ten_percent_grade_is_reported_as_ten(self):
        # 25 m step, 100 m window: 10 m of rise over 100 m.
        assert tr.grade_percent([i * 2.5 for i in range(50)]) == pytest.approx(10.0)

    def test_a_descent_counts_the_same_as_a_climb(self):
        assert tr.grade_percent([100.0 - i * 2.5 for i in range(50)]) == pytest.approx(10.0)


class TestTheNamedFixtureProperties:
    """The two the brief names, as predicates over a summary rather than as prose."""

    def _summary(self, coords, profile):
        return tr.summarise(coords, profile)

    def test_a_flat_bay_margin_road_reads_as_flat(self):
        coords = line_north((37.42, -121.97), 80)          # Alviso-ish, ~2.2 km
        noisy_flat = [2.0 + (0.4 if i % 3 else 0.0) for i in range(90)]
        s = self._summary(coords, noisy_flat)
        assert tr.is_flat(s), s
        assert not tr.is_steep(s), s

    def test_a_steep_climb_does_not_read_as_flat(self):
        coords = line_north((37.30, -122.23), 200)         # Old La Honda-ish, ~5.5 km
        climb = [i * 2.0 for i in range(220)]              # 440 m of climb
        s = self._summary(coords, climb)
        assert tr.is_steep(s), s
        assert not tr.is_flat(s), s

    def test_the_two_are_not_the_same_number(self):
        flat = self._summary(line_north((37.42, -121.97), 80),
                             [2.0 + (0.4 if i % 3 else 0.0) for i in range(90)])
        steep = self._summary(line_north((37.30, -122.23), 200), [i * 2.0 for i in range(220)])
        assert steep["gain_per_km"] > flat["gain_per_km"] * 10


class TestSanity:
    def _base(self, **kw):
        s = {"length_m": 1000.0, "coverage": 1.0, "gain_m": 50.0,
             "gain_per_km": 50.0, "relief_m": 60.0, "max_grade_pct": 8.0}
        s.update(kw)
        return s

    def test_a_plausible_summary_has_no_problems(self):
        assert tr.sanity_problems(self._base()) == []

    @pytest.mark.parametrize("bad,match", [
        ({"coverage": 1.5}, "not a fraction"),
        ({"gain_m": -1.0}, "negative"),
        ({"relief_m": -1.0}, "negative"),
        ({"max_grade_pct": 95.0}, "no drivable road"),
        ({"gain_m": 2000.0}, "climb further than it travels"),
        ({"gain_per_km": math.nan}, "NaN"),
    ])
    def test_impossibilities_are_reported(self, bad, match):
        assert any(match in p for p in tr.sanity_problems(self._base(**bad)))
