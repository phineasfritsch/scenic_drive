"""Tile arithmetic and nodata handling, tested without a 2.3 GB download or a GDAL install.

The failure worth guarding is not "it crashed". It is a tile index off by one, which returns a real elevation
from the wrong square - so every road in a region gets plausible terrain that belongs to somewhere else, and
nothing downstream can tell.
"""
from __future__ import annotations

import math
import types

import pytest

from etl import dem


class AcceptsAnyTileName:
    """A stand-in for `dem.TILES` that contains every string.

    With the real TILES an out-of-hemisphere point is refused TWICE: once by the hemisphere guard, and again
    because the name it builds (`n38w-122`, `n-37w123`) is in no tile set anywhere. The second refusal hides
    the first, so `tile_for(38.0, 122.5) is None` passes with the guard deleted - which is how the guard
    shipped untested the first time. Patching plausible names into TILES does not help; the malformed name
    misses those too. Dropping membership entirely leaves the guard as the only thing that can return None.
    """
    def __contains__(self, name: object) -> bool:
        return True


def fake_runner(stdout, returncode=0, stderr=""):
    def run(argv, stdin):
        run.calls.append((argv, stdin))
        return types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    run.calls = []
    return run


class TestTileForAPoint:
    @pytest.mark.parametrize("lat,lon,tile", [
        (37.5, -122.5, "n38w123"),    # peninsula
        (37.5, -121.5, "n38w122"),    # east bay
        (36.9, -121.5, "n37w122"),    # south, Pacheco side
        (36.9, -122.5, "n37w123"),    # Santa Cruz coast
        (38.5, -122.5, "n39w123"),    # Sonoma / Napa
        (38.5, -121.8, "n39w122"),    # Solano
        (37.5, -123.2, "n38w124"),    # outer coast
        (38.5, -123.2, "n39w124"),    # Sonoma coast
    ])
    def test_each_corner_of_the_region_finds_its_tile(self, lat, lon, tile):
        assert dem.tile_for(lat, lon) == tile

    def test_a_point_in_the_ocean_tile_we_do_not_have_returns_none(self):
        """n37w124 is entirely ocean and USGS returns 404 for it. No tile is not zero metres."""
        assert dem.tile_for(36.5, -123.5) is None

    def test_a_point_outside_the_region_returns_none(self):
        assert dem.tile_for(45.0, -100.0) is None

    def test_nan_returns_none_rather_than_a_tile_named_nan(self):
        assert dem.tile_for(float("nan"), -122.0) is None
        assert dem.tile_for(37.5, float("nan")) is None

    def test_an_infinite_coordinate_returns_none_rather_than_raising(self):
        """`math.ceil(inf)` raises OverflowError, and `group_by_tile` calls `tile_for` once per road node -
        so one infinite coordinate anywhere in an extract aborted the whole ETL run instead of costing that
        one point its elevation. A NaN check sitting directly above an unguarded `ceil` read as coverage it
        did not have. Found by agent/reviewer-pr34."""
        inf = float("inf")
        assert dem.tile_for(inf, -122.0) is None
        assert dem.tile_for(-inf, -122.0) is None
        assert dem.tile_for(37.5, -inf) is None
        assert dem.tile_for(37.5, inf) is None

    def test_the_name_comes_from_the_north_west_corner(self):
        """Ceil, not floor. Getting this backwards names a tile that EXISTS, for the wrong square, so every
        elevation is plausibly wrong rather than missing - the hardest kind of wrong to notice."""
        assert dem.tile_for(37.0001, -122.0001) == "n38w123"
        assert dem.tile_for(37.9999, -122.9999) == "n38w123"

    def test_the_tile_set_matches_what_the_manifest_pins(self):
        assert len(dem.TILES) == 8
        assert "n37w124" not in dem.TILES

    @pytest.mark.parametrize("lat,lon,where", [
        (38.0, 122.5, "122.5 E - from abs(lon) this named n38w123, the peninsula's own tile"),
        (37.5, 122.5, "122.5 E at a latitude we do hold a tile for"),
        (37.5, 121.5, "121.5 E"),
        (-37.5, -122.5, "37.5 S - Chile's coast sits at California's longitudes"),
        (-38.5, -123.2, "38.5 S"),
        (0.0, -122.5, "the equator"),
        (37.5, 0.0, "the prime meridian"),
    ])
    def test_a_point_outside_the_northern_western_quadrant_has_no_tile(self, lat, lon, where):
        """The CONTRACT: `n`/`w` in nXXwYYY are claims about the hemisphere, not a prefix, so a point
        outside that quadrant has no name in this scheme and must come back None rather than folded into
        someone else's tile. These cases say nothing about which line enforces it - they pass with the
        hemisphere guard deleted, on the malformed name missing TILES. The MECHANISM is pinned one test
        down, by `test_the_guard_and_not_the_tile_set_is_what_refuses_a_point`."""
        assert dem.tile_for(lat, lon) is None, where

    def test_the_guard_and_not_the_tile_set_is_what_refuses_a_point(self, monkeypatch):
        """The only test in this file that can see the hemisphere guard at all. Delete either half of
        `lat <= 0.0 or lon >= 0.0` and this goes red; delete both and the other 45 tests here stay green,
        satisfied by the malformed name missing TILES - an accident, not a check. It is also the honest
        statement of why the guard is worth having while unreachable: TILES membership is what stops the
        collision today, and it stops stopping it the moment the tile set covers a second region.
        """
        monkeypatch.setattr(dem, "TILES", AcceptsAnyTileName())
        # Vacuity guard. `test_a_point_outside_the_region_returns_none` pins that this is None against the
        # real TILES, so a name coming back here proves the stand-in is installed and that membership is no
        # longer refusing anything - without it, a monkeypatch that silently did nothing would still pass.
        assert dem.tile_for(45.0, -100.0) == "n45w100"
        assert dem.tile_for(37.5, -122.5) == "n38w123"
        assert dem.tile_for(38.0, 122.5) is None       # 122.5 E - the collision itself
        assert dem.tile_for(38.0, 120.5) is None       # 120.5 E
        assert dem.tile_for(-37.5, -122.5) is None     # 37.5 S, off Chile
        assert dem.tile_for(0.0, -122.5) is None       # the equator
        assert dem.tile_for(37.5, 0.0) is None         # the prime meridian


class TestGrouping:
    def test_points_are_grouped_by_tile_with_their_indices(self):
        points = [(37.5, -122.5), (38.5, -122.5), (37.5, -122.6)]
        groups = dem.group_by_tile(points)
        assert groups["n38w123"] == [0, 2]
        assert groups["n39w123"] == [1]

    def test_points_with_no_tile_are_grouped_under_none(self):
        assert dem.group_by_tile([(0.0, 0.0)])[None] == [0]

    def test_order_within_a_group_is_preserved(self):
        points = [(37.1, -122.1), (37.2, -122.2), (37.3, -122.3)]
        assert dem.group_by_tile(points)["n38w123"] == [0, 1, 2]


class TestParsingValues:
    def test_plain_values_are_read(self):
        assert dem.parse_values("12.5\n300\n", 2) == [12.5, 300.0]

    def test_a_blank_line_is_a_miss_not_a_zero(self):
        assert dem.parse_values("12.5\n\n", 2) == [12.5, None]

    def test_a_non_numeric_line_is_a_miss(self):
        assert dem.parse_values("12.5\nError\n", 2) == [12.5, None]

    def test_nodata_is_absence_not_depth(self):
        """3DEP's nodata is a large negative. Treating it as an elevation puts a road 999 km underground and
        produces a gain figure that dwarfs every real mountain."""
        assert dem.parse_values("-999999\n", 1) == [None]

    def test_an_implausible_height_is_a_corrupt_read(self):
        assert dem.parse_values("99999\n", 1) == [None]

    def test_sea_level_is_a_real_elevation_and_is_kept(self):
        assert dem.parse_values("0\n", 1) == [0.0]

    def test_a_negative_but_plausible_elevation_is_kept(self):
        """Parts of the Delta really are below sea level."""
        assert dem.parse_values("-5.5\n", 1) == [-5.5]

    def test_a_short_read_raises_rather_than_silently_misaligning(self):
        with pytest.raises(ValueError, match="returned 1 values for 3"):
            dem.parse_values("12.5\n", 3)

    def test_a_long_read_raises_too(self):
        with pytest.raises(ValueError, match="returned 3 values for 1"):
            dem.parse_values("1\n2\n3\n", 1)


class TestSampling:
    def test_a_missing_tile_file_yields_misses_rather_than_raising(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        assert dem.sample_tile("n38w123", [(37.5, -122.5)]) == [None]

    def test_coordinates_are_written_lon_then_lat(self, monkeypatch, tmp_path):
        """gdallocationinfo -wgs84 wants x y, i.e. lon lat. Swapping them samples the wrong hemisphere and
        returns nodata for everything, which looks exactly like a region with no coverage."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"not really a tiff")
        runner = fake_runner("100\n")
        dem.sample_tile("n38w123", [(37.5, -122.5)], runner=runner)
        assert runner.calls[0][1] == "-122.5 37.5\n"

    def test_a_gdal_failure_raises_rather_than_reporting_no_elevation(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        with pytest.raises(RuntimeError, match="gdallocationinfo failed"):
            dem.sample_tile("n38w123", [(37.5, -122.5)],
                            runner=fake_runner("", returncode=1, stderr="boom"))

    def test_values_come_back_in_the_order_the_points_were_given(self, monkeypatch, tmp_path):
        """Two tiles, interleaved points. A sampler that returns tile-order results silently attributes one
        road's terrain to another."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        for t in ("n38w123", "n39w123"):
            (tmp_path / f"3dep-{t}.tif").write_bytes(b"x")

        def runner(argv, stdin):
            n = len(stdin.strip().splitlines())
            value = "10" if "n38w123" in argv[-1] else "900"
            return types.SimpleNamespace(stdout="\n".join([value] * n) + "\n", stderr="", returncode=0)

        points = [(37.5, -122.5), (38.5, -122.5), (37.6, -122.6), (38.6, -122.6)]
        assert dem.sample(points, runner=runner) == [10.0, 900.0, 10.0, 900.0]

    def test_points_with_no_tile_come_back_as_none_without_calling_gdal(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        runner = fake_runner("")
        assert dem.sample([(0.0, 0.0), (10.0, 10.0)], runner=runner) == [None, None]
        assert runner.calls == []

    def test_an_empty_request_is_an_empty_answer(self):
        assert dem.sample([]) == []


class TestTheSmoothingNeighbourhood:
    def test_it_is_nine_positions(self):
        assert len(dem.neighbourhood(38.0, -122.0)) == 9

    def test_the_centre_is_the_point_itself(self):
        assert dem.neighbourhood(38.0, -122.0)[4] == (38.0, -122.0)

    def test_the_box_is_square_on_the_ground_not_square_in_degrees(self):
        """At 38N a degree of longitude is 79% of a degree of latitude. Without the cos(lat) correction the
        neighbourhood is a rectangle stretched north-south, so the smoothing blurs ridges running one way
        more than the other - directional smoothing of exactly the feature relief is meant to measure.
        """
        from etl.curvature import distance_on_earth
        lat, lon = 38.0, -122.0
        cells = dem.neighbourhood(lat, lon)
        north = distance_on_earth(lat, lon, cells[7][0], lon)
        east = distance_on_earth(lat, lon, lat, cells[5][1])
        assert north == pytest.approx(east, rel=0.02), (north, east)

    def test_one_cell_is_about_ten_metres(self):
        from etl.curvature import distance_on_earth
        lat, lon = 38.0, -122.0
        north = distance_on_earth(lat, lon, dem.neighbourhood(lat, lon)[7][0], lon)
        assert 9.0 < north < 12.0, north


class TestSmoothedSampling:
    def _runner(self, values):
        """Returns the given values in order, one per requested point."""
        state = {"i": 0}

        def run(argv, stdin):
            n = len(stdin.strip().splitlines())
            out = values[state["i"]:state["i"] + n]
            state["i"] += n
            return types.SimpleNamespace(stdout="\n".join(str(v) for v in out) + "\n",
                                         stderr="", returncode=0)
        return run

    def test_it_averages_the_nine_cells(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        # Eight cells at 100 m and one spike at 190 m: the mean is 110, not 190.
        runner = self._runner([100] * 4 + [190] + [100] * 4)
        assert dem.sample_smoothed([(37.5, -122.5)], runner=runner) == [pytest.approx(110.0)]

    def test_a_spike_survives_unsmoothed_sampling(self, monkeypatch, tmp_path):
        """The contrast that makes the smoothing worth its nine reads."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        assert dem.sample([(37.5, -122.5)], runner=self._runner([190])) == [190.0]

    def test_nodata_neighbours_are_skipped_not_counted_as_zero(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        runner = self._runner([100, 100, -999999, -999999, 100, -999999, -999999, -999999, -999999])
        assert dem.sample_smoothed([(37.5, -122.5)], runner=runner) == [pytest.approx(100.0)]

    def test_an_entirely_nodata_neighbourhood_is_absence(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        assert dem.sample_smoothed([(37.5, -122.5)], runner=self._runner([-999999] * 9)) == [None]

    def test_it_asks_for_nine_positions_per_point(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        runner = fake_runner("\n".join(["100"] * 18) + "\n")
        dem.sample_smoothed([(37.5, -122.5), (37.6, -122.6)], runner=runner)
        assert len(runner.calls[0][1].strip().splitlines()) == 18

    def test_it_is_still_one_process_per_tile(self, monkeypatch, tmp_path):
        """Nine times the rows, not nine times the processes."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        (tmp_path / "3dep-n38w123.tif").write_bytes(b"x")
        runner = fake_runner("\n".join(["100"] * 27) + "\n")
        dem.sample_smoothed([(37.5, -122.5), (37.51, -122.51), (37.52, -122.52)], runner=runner)
        assert len(runner.calls) == 1
