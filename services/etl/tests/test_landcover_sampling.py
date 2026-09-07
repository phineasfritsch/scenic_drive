"""`sample_codes` - the only code in this task that reads a raster - without the 92 MB of raster.

It had no test at all. agent/reviewer-32 mutated it four ways and every mutant lived: writing `lat lon`
instead of `lon lat`, dropping the value-count guard, ignoring a non-zero gdallocationinfo exit, and
dropping the `0 -> NODATA` mapping. `etl.dem` has exactly this shape and `tests/test_dem.py` covers all
four for it; the `runner=` injection point was already here for the same reason and nothing used it.

The failure worth guarding is not a crash. It is a sampler that returns plausible class codes for the wrong
place, or misaligns every value by one, or reports the nodata fill as a class - all of which produce a
fraction between 0 and 1 that looks exactly like an answer. This runs over 333k ways in T-0030.
"""
from __future__ import annotations

import types

import pytest

from etl import landcover as lc


def fake_runner(stdout, returncode=0, stderr=""):
    def run(argv, stdin):
        run.calls.append((argv, stdin))
        return types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    run.calls = []
    return run


@pytest.fixture
def tiles(monkeypatch, tmp_path):
    """Tile files that exist and are not rasters. Nothing opens them: the runner is injected, and what is
    under test is the arithmetic around the call, not GDAL."""
    monkeypatch.setattr(lc, "INPUTS", tmp_path)
    for name in ("n36w123", "n36w126"):
        (tmp_path / f"worldcover-{name}.tif").write_bytes(b"not really a tiff")
    return tmp_path


class TestWhereItLooksForATile:
    def test_the_file_name_is_one_the_manifest_actually_pins(self):
        """The sampler and the fetcher have to agree on the filename or every sample is a miss, and a miss
        reads as `no coverage here` rather than as `we are looking in the wrong place`. Anchored on the
        pinned manifest entries, not on a string repeated in two files."""
        from pathlib import Path

        from etl import manifest as mf
        real = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"
        names = {i.name for i in mf.parse(real.read_text(encoding="utf-8"))}
        for tile in ("N36W123", "N36W126"):
            assert lc.tile_path(tile).name in names, (tile, lc.tile_path(tile).name)

    def test_the_tile_name_is_lower_cased_for_the_file_but_not_for_the_tile(self):
        assert lc.tile_path("N36W123").name == "worldcover-n36w123.tif"

    def test_a_missing_tile_file_is_a_miss_rather_than_a_crash(self, monkeypatch, tmp_path):
        """The western tile is 4 MB of mostly ocean and easy to forget to fetch. Absent data is None."""
        monkeypatch.setattr(lc, "INPUTS", tmp_path)
        runner = fake_runner("10\n")
        assert lc.sample_codes([(37.5, -122.5)], runner=runner) == [None]
        assert runner.calls == [], "gdal was called for a tile that is not there"

    def test_a_point_with_no_tile_name_never_reaches_gdal(self, tiles):
        runner = fake_runner("10\n")
        assert lc.sample_codes([(float("nan"), -122.0)], runner=runner) == [None]
        assert runner.calls == []

    def test_an_empty_request_is_an_empty_answer(self, tiles):
        runner = fake_runner("")
        assert lc.sample_codes([], runner=runner) == []
        assert runner.calls == []


class TestWhatItSendsToGdal:
    def test_coordinates_are_written_lon_then_lat(self, tiles):
        """`gdallocationinfo -wgs84` wants x y, i.e. lon lat. Swapped, every Bay Area point becomes
        (-122.5 N, 37.5 E) - a spot in Kazakhstan on a tile we do not have, so the whole corpus comes back
        None and the region reads as having no land cover rather than as having been sampled wrong. The
        same swap is what `test_dem.py::test_coordinates_are_written_lon_then_lat` exists for."""
        runner = fake_runner("10\n")
        lc.sample_codes([(37.5, -122.5)], runner=runner)
        assert runner.calls[0][1] == "-122.5 37.5\n"

    def test_it_asks_the_tile_the_point_falls_in(self, tiles):
        runner = fake_runner("10\n")
        lc.sample_codes([(37.5, -122.5)], runner=runner)
        assert runner.calls[0][0][-1].endswith("worldcover-n36w123.tif")
        assert runner.calls[0][0][:3] == ["gdallocationinfo", "-valonly", "-wgs84"]

    def test_it_is_one_process_per_tile_not_one_per_point(self, tiles):
        """A buffer is 177 points and a corpus pass is 333k ways. One process per point is not a
        performance nit, it is a different order of magnitude."""
        runner = fake_runner("10\n10\n10\n")
        lc.sample_codes([(37.5, -122.5), (37.51, -122.51), (37.52, -122.52)], runner=runner)
        assert len(runner.calls) == 1
        assert len(runner.calls[0][1].strip().splitlines()) == 3


class TestWhatItDoesWithTheAnswer:
    def test_values_come_back_in_the_order_the_points_were_given(self, tiles):
        """Two tiles, interleaved points - the tile seam the region really has, at lon -123. A sampler that
        returns tile-order results attributes one road's land cover to another, and both answers are
        plausible class codes."""
        def runner(argv, stdin):
            n = len(stdin.strip().splitlines())
            value = "10" if "n36w123" in argv[-1] else "50"
            return types.SimpleNamespace(stdout="\n".join([value] * n) + "\n", stderr="", returncode=0)

        points = [(37.5, -122.5), (37.5, -123.5), (37.6, -122.6), (37.6, -123.6)]
        assert lc.sample_codes(points, runner=runner) == [10, 50, 10, 50]

    def test_code_zero_is_nodata_and_not_a_class(self, tiles):
        """WorldCover has no class 0; 0 is the GeoTIFF's fill value. Kept as a code it lands in no term, so
        a tile that reads 0 everywhere - the wrong band, a corrupt fetch - would report canopy 0.0 and
        impervious 0.0 with coverage 1.0: `no trees and no buildings`, indistinguishable from a car park in
        a desert. As NODATA it drops out of the denominator and `coverage` says the buffer was empty."""
        assert lc.sample_codes([(37.5, -122.5)], runner=fake_runner("0\n")) == [None]
        assert lc.fractions(lc.sample_codes([(37.5, -122.5)], runner=fake_runner("0\n"))) == {
            "coverage": 0.0}

    def test_a_real_class_code_survives_intact(self, tiles):
        assert lc.sample_codes([(37.5, -122.5)], runner=fake_runner("50\n")) == [50]

    def test_a_value_written_as_a_float_is_still_a_class(self, tiles):
        assert lc.sample_codes([(37.5, -122.5)], runner=fake_runner("50.0\n")) == [50]

    def test_blank_and_non_numeric_lines_are_misses_not_zeros(self, tiles):
        points = [(37.5, -122.5), (37.51, -122.5), (37.52, -122.5)]
        assert lc.sample_codes(points, runner=fake_runner("\nnodata\n10\n")) == [None, None, 10]

    def test_a_short_read_raises_rather_than_shifting_every_sample_by_one(self, tiles):
        """The guard `test_dem.py::test_a_short_read_raises_rather_than_silently_misaligning` exists for.
        Without it the third point silently keeps its neighbour's class and nothing downstream can tell."""
        points = [(37.5, -122.5), (37.51, -122.5), (37.52, -122.5)]
        with pytest.raises(ValueError, match="returned 2 values for 3 points"):
            lc.sample_codes(points, runner=fake_runner("10\n20\n"))

    def test_a_long_read_raises_too(self, tiles):
        with pytest.raises(ValueError, match="returned 3 values for 1 points"):
            lc.sample_codes([(37.5, -122.5)], runner=fake_runner("10\n20\n30\n"))

    def test_a_gdal_failure_raises_rather_than_reporting_land_cover(self, tiles):
        """A non-zero exit with output on stdout is the dangerous shape: ignore the exit code and the
        values are used. `-1` from a truncated raster is not `no trees`."""
        with pytest.raises(RuntimeError, match="gdallocationinfo failed on N36W123"):
            lc.sample_codes([(37.5, -122.5)],
                            runner=fake_runner("50\n", returncode=1, stderr="ERROR 4: not a raster"))

    def test_the_failure_says_what_gdal_said(self, tiles):
        with pytest.raises(RuntimeError, match="not a raster"):
            lc.sample_codes([(37.5, -122.5)],
                            runner=fake_runner("", returncode=1, stderr="ERROR 4: not a raster"))
