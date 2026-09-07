"""Land cover arithmetic and tile geometry, without the 92 MB of raster.

The failure worth guarding is a fraction that is quietly zero. A wrong tile name, a wrong band, or NODATA
counted into the denominator all produce a number between 0 and 1 that looks like an answer, and "no trees
and no buildings" is indistinguishable from "we read the wrong thing".
"""
from __future__ import annotations

import pytest

from etl import landcover as lc


class TestTileNaming:
    @pytest.mark.parametrize("lat,lon,tile", [
        (37.5, -122.5, "N36W123"),     # most of the region
        (38.9, -121.6, "N36W123"),     # north-east corner of the bbox
        (36.9, -123.2, "N36W126"),     # the western strip the bbox reaches into
        (37.5, -123.62, "N36W126"),    # the bbox's actual west edge
        (39.0, -122.0, "N39W123"),     # one tile north
    ])
    def test_tiles_are_named_by_their_south_west_corner(self, lat, lon, tile):
        assert lc.tile_for(lat, lon) == tile

    def test_the_bbox_west_edge_is_not_in_the_main_tile(self):
        """N36W123 covers lon -123..-120. The region runs to -123.62, so the western strip needs N36W126.
        The brief said one tile 'contains the whole Bay Area'; it does not."""
        assert lc.tile_for(37.5, -123.61) != lc.tile_for(37.5, -122.9)

    def test_a_point_exactly_on_a_tile_boundary_belongs_to_the_tile_it_starts(self):
        assert lc.tile_for(36.0, -123.0) == "N36W123"
        assert lc.tile_for(39.0, -123.0) == "N39W123"

    def test_nan_gives_no_tile_rather_than_a_tile_named_nan(self):
        assert lc.tile_for(float("nan"), -122.0) == ""


class TestBufferGeometry:
    def test_the_buffer_is_a_circle_not_a_square(self):
        """The corners of a 300 m box are 212 m out. Left square, a road running diagonally past a parking
        lot picks it up from further away than one running north-south - the score would depend on which way
        the road happens to point."""
        from etl.curvature import distance_on_earth
        lat, lon = 37.5, -122.5
        for plat, plon in lc.buffer_points(lat, lon):
            assert distance_on_earth(lat, lon, plat, plon) <= lc.BUFFER_M * 1.05

    def test_it_reaches_most_of_the_way_to_the_radius(self):
        from etl.curvature import distance_on_earth
        lat, lon = 37.5, -122.5
        furthest = max(distance_on_earth(lat, lon, p[0], p[1]) for p in lc.buffer_points(lat, lon))
        assert furthest > lc.BUFFER_M * 0.8

    def test_the_buffer_is_the_same_size_east_west_as_north_south(self):
        """Without the cos(latitude) correction the buffer is an ellipse and the score becomes directional."""
        from etl.curvature import distance_on_earth
        lat, lon = 37.5, -122.5
        pts = lc.buffer_points(lat, lon)
        north = max(distance_on_earth(lat, lon, p[0], lon) for p in pts)
        east = max(distance_on_earth(lat, lon, lat, p[1]) for p in pts)
        assert north == pytest.approx(east, rel=0.1), (north, east)

    def test_the_centre_is_included(self):
        assert (37.5, -122.5) in [(round(a, 6), round(b, 6)) for a, b in lc.buffer_points(37.5, -122.5)]


class TestFractions:
    def test_all_trees_is_all_canopy(self):
        f = lc.fractions([10] * 50)
        assert f["canopy"] == 1.0
        assert f["impervious"] == 0.0

    def test_all_built_up_is_all_impervious(self):
        f = lc.fractions([50] * 50)
        assert f["impervious"] == 1.0
        assert f["canopy"] == 0.0

    def test_shrubland_counts_as_canopy_and_grassland_does_not(self):
        """Tree cover and shrubland both read as green enclosure from a car. An open golden hill is scenic
        for a different reason, and relief and water are what should pick that up."""
        assert lc.fractions([20] * 10)["canopy"] == 1.0
        assert lc.fractions([30] * 10)["canopy"] == 0.0

    def test_a_mix_is_reported_as_a_mix(self):
        f = lc.fractions([10] * 3 + [50] * 1)
        assert f["canopy"] == pytest.approx(0.75)
        assert f["impervious"] == pytest.approx(0.25)

    def test_nodata_is_excluded_from_the_denominator_not_counted(self):
        """A coastal way has half its buffer in the ocean. Dividing by the full sample count would halve its
        canopy fraction purely for being near water."""
        f = lc.fractions([10, 10, None, None])
        assert f["canopy"] == 1.0
        assert f["coverage"] == pytest.approx(0.5)

    def test_an_entirely_empty_buffer_reports_no_coverage_rather_than_zero_canopy(self):
        f = lc.fractions([None, None])
        assert f["coverage"] == 0.0
        assert "canopy" not in f, "a fraction of nothing is not 0.0, it is absent"

    def test_water_covers_the_wet_classes(self):
        assert lc.fractions([80] * 10)["water"] == 1.0
        assert lc.fractions([90] * 10)["water"] == 1.0

    def test_the_named_class_fractions_sum_to_one(self):
        f = lc.fractions([10, 20, 30, 40, 50, 60, 80, 90])
        total = sum(f[name] for name in lc.CLASSES.values())
        assert total == pytest.approx(1.0)


class TestUnknownCodes:
    def test_a_valid_raster_has_none(self):
        assert lc.unknown_codes([10, 20, 50, None]) == set()

    def test_a_wrong_band_or_wrong_raster_is_detected(self):
        """Values outside the class set land in no bucket, so every fraction would quietly be zero - which
        reads as 'no trees and no buildings' rather than 'this is not land cover data'."""
        assert lc.unknown_codes([0, 1, 255]) == {0, 1, 255}

    def test_zero_is_not_a_worldcover_class(self):
        assert 0 in lc.unknown_codes([0])


class TestProblems:
    def _summary(self, **kw):
        s = lc.fractions([10] * 6 + [50] * 4)
        s.update(kw)
        return s

    def test_a_plausible_summary_has_no_problems(self):
        assert lc.problems(self._summary()) == []

    def test_a_fraction_out_of_range_is_reported(self):
        assert any("not a fraction" in p for p in lc.problems(self._summary(canopy=1.5)))

    def test_class_fractions_that_do_not_sum_to_one_are_reported(self):
        s = self._summary()
        s["tree_cover"] = 0.9
        assert any("sum to" in p for p in lc.problems(s))

    def test_a_missing_term_is_reported(self):
        s = self._summary()
        del s["canopy"]
        assert any("canopy is missing" in p for p in lc.problems(s))


class TestTheNamedProperties:
    def test_a_redwood_road_reads_as_wooded_and_not_built_up(self):
        s = lc.fractions([10] * 45 + [30] * 5)
        assert lc.is_wooded(s)
        assert not lc.is_built_up(s)

    def test_a_strip_mall_arterial_reads_as_built_up_and_not_wooded(self):
        s = lc.fractions([50] * 40 + [30] * 10)
        assert lc.is_built_up(s)
        assert not lc.is_wooded(s)

    def test_the_two_are_distinguishable_not_marginal(self):
        wooded = lc.fractions([10] * 45 + [30] * 5)
        built = lc.fractions([50] * 40 + [30] * 10)
        assert wooded["canopy"] - built["canopy"] > 0.5
        assert built["impervious"] - wooded["impervious"] > 0.5


class TestTheVerdictIsOneVerdict:
    """`is_wooded` and `is_built_up` are not two independent facts about a road, they are one answer to
    one question: does this read as a redwood road or as a strip-mall arterial? Two independent cutoffs on
    two fractions that are not required to be complementary can say both, and on real San Ramon streets
    they did. Whichever term dominates decides, and it has to dominate by enough to be a verdict.
    """

    def test_no_pair_of_fractions_can_satisfy_both(self):
        """Exhaustive over the whole simplex, not over four curated roads. The counts stop a rule that
        simply never fires from passing this."""
        wooded = built = 0
        for c in range(101):
            for i in range(101 - c):
                s = {"canopy": c / 100.0, "impervious": i / 100.0}
                w, b = lc.is_wooded(s), lc.is_built_up(s)
                assert not (w and b), (c, i)
                wooded += w
                built += b
        assert wooded > 100, wooded
        assert built > 100, built

    def test_an_even_split_is_neither(self):
        """Half tree canopy and half buildings is a leafy suburb. Both halves are real; neither is the
        answer to which kind of road this is."""
        s = lc.fractions([10] * 50 + [50] * 50)
        assert not lc.is_wooded(s)
        assert not lc.is_built_up(s)

    def test_trees_have_to_beat_buildings_to_count_as_wooded(self):
        assert lc.is_wooded(lc.fractions([10] * 60 + [50] * 10 + [30] * 30))
        assert not lc.is_wooded(lc.fractions([10] * 60 + [50] * 40))

    def test_buildings_have_to_beat_trees_to_count_as_built_up(self):
        assert lc.is_built_up(lc.fractions([50] * 60 + [10] * 10 + [30] * 30))
        assert not lc.is_built_up(lc.fractions([50] * 55 + [10] * 45))

    def test_a_quarter_built_is_not_yet_a_strip_mall(self):
        """With the dominance rule in place, a road with no trees at all clears `impervious >= ratio *
        canopy` at any impervious above zero - so the 0.4 is the only thing between `some development` and
        `strip-mall arterial`, and nothing else in the suite pins it. Mines Road pins the canopy cutoff
        from below with real data; there is no equivalent real road for this one."""
        s = lc.fractions([50] * 25 + [30] * 75)
        assert s["impervious"] == pytest.approx(0.25)
        assert not lc.is_built_up(s)
        assert lc.is_built_up(lc.fractions([50] * 45 + [30] * 55))

    def test_not_quite_half_trees_is_not_yet_wooded(self):
        """`wooded` means canopy is the majority of what you can see, and 0.5 is what majority means. That
        is a definition, not a fit - the fitting question, which of two real terms wins, is the ratio's."""
        assert not lc.is_wooded(lc.fractions([10] * 45 + [30] * 55))
        assert lc.is_wooded(lc.fractions([10] * 55 + [30] * 45))

    def test_a_tie_is_not_a_verdict(self):
        """A ratio of exactly 1 still lets both fire on an exact tie, and exact ties happen: a 29-sample
        buffer that lands 15/14 is one rounding away from 50/50."""
        s = {"canopy": 0.5, "impervious": 0.5}
        assert not (lc.is_wooded(s) and lc.is_built_up(s))


class TestOpenLand:
    def test_the_four_terms_partition_every_class(self):
        """A class in no term is a class the score cannot see, and a class in two is counted twice.
        cropland sat in neither for the whole of this task's first pass."""
        groups = [lc.CANOPY_CLASSES, lc.IMPERVIOUS_CLASSES, lc.WATER_CLASSES, lc.OPEN_CLASSES]
        assert set().union(*groups) == set(lc.CLASSES)
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                assert not groups[a] & groups[b], (groups[a], groups[b])

    def test_grassland_and_cropland_are_open_land(self):
        assert lc.fractions([30] * 10)["open_land"] == 1.0
        assert lc.fractions([40] * 10)["open_land"] == 1.0

    def test_open_land_is_not_canopy_and_not_impervious(self):
        f = lc.fractions([30] * 5 + [40] * 5)
        assert f["canopy"] == 0.0
        assert f["impervious"] == 0.0

    def test_the_four_fractions_sum_to_one_on_any_mix(self):
        f = lc.fractions([10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100])
        assert f["canopy"] + f["impervious"] + f["water"] + f["open_land"] == pytest.approx(1.0)

    def test_an_empty_buffer_has_no_open_land_either(self):
        assert "open_land" not in lc.fractions([None, None])


class TestSummarise:
    def test_samples_are_pooled_not_averaged_per_point(self):
        """A long way through forest must not be outvoted by a short built-up stretch that happened to get
        denser sampling. Every sample counts once."""
        coords = [(37.5, -122.5), (37.51, -122.5)]
        s = lc.summarise(coords, [[10] * 90, [50] * 10])
        assert s["canopy"] == pytest.approx(0.9)
        assert s["samples"] == 100

    def test_it_reports_the_length_it_covered(self):
        s = lc.summarise([(37.5, -122.5), (37.51, -122.5)], [[10], [10]])
        assert s["length_m"] > 1000