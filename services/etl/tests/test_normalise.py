"""The region percentile rank: the estimator, the tie rule, the population and the order.

EVERY EXPECTED NUMBER IN THIS FILE IS TYPED OUT from arithmetic shown beside it. The formula is
`(below + 0.5*equal) / population` (T-0163 log, ruling R2), so a population of 4 with no ties gives
0.125 / 0.375 / 0.625 / 0.875 and every case below is chosen so the answer is an exact decimal - a test
whose expectation is computed from the function it checks proves only that the function equals itself.

The three properties the fixture cannot see are here, each with its own named test: the TIE RULE
(`test_a_tie_group_takes_the_average_rank`), the POPULATION FILTER
(`test_the_zero_classes_do_not_set_the_curve`) and the SORT KEY
(`test_the_order_is_by_value_then_way_id_not_insertion_order`).
"""
from __future__ import annotations

import math

import pytest

from etl import byways, normalise, score, way_record as wr

RAW_TERMS = {"curvature": 640.0, "elevation_gain": 300.0, "relief": 180.0, "sinuosity": 1.4,
             "furniture": 0.1}
MAPPED = {"canopy": 0.5, "impervious": 0.25, "water": 0.1, "speed_fit": 0.6}


def raw(way_id: int, highway: str = "secondary", **kw) -> wr.WayRecord:
    fields = dict(way_id=way_id, highway=highway, **RAW_TERMS, **MAPPED)
    fields.update(kw)
    return wr.WayRecord(**fields)


class TestTheEstimator:
    def test_four_distinct_values_take_the_eighths(self):
        """n=4, no ties: (0+0.5)/4, (1+0.5)/4, (2+0.5)/4, (3+0.5)/4."""
        ranks = normalise.percentile_ranks({11: 5.0, 12: 6.0, 13: 7.0, 14: 8.0})
        assert ranks == {11: 0.125, 12: 0.375, 13: 0.625, 14: 0.875}

    def test_a_tie_group_takes_the_average_rank(self):
        """n=4 with 10.0 twice: below=0 equal=2 -> (0 + 0.5*2)/4 = 0.25 for BOTH, then (2+0.5)/4 = 0.625
        and (3+0.5)/4 = 0.875. Taking the group's first rank would say 0.125 and its last 0.375."""
        ranks = normalise.percentile_ranks({21: 10.0, 22: 10.0, 23: 30.0, 24: 40.0})
        assert ranks == {21: 0.25, 22: 0.25, 23: 0.625, 24: 0.875}

    def test_a_tie_group_in_the_middle_takes_the_average_rank(self):
        """n=8, 7.0 four times: below=2, equal=4 -> (2 + 2.0)/8 = 0.5 for all four."""
        values = {31: 1.0, 32: 2.0, 33: 7.0, 34: 7.0, 35: 7.0, 36: 7.0, 37: 8.0, 38: 9.0}
        ranks = normalise.percentile_ranks(values)
        assert [ranks[i] for i in (33, 34, 35, 36)] == [0.5, 0.5, 0.5, 0.5]
        assert ranks[31] == 0.0625 and ranks[38] == 0.9375  # (0+0.5)/8 and (7+0.5)/8

    def test_a_population_of_one_is_its_own_median(self):
        """(0 + 0.5*1)/1. The only scorable way in a region is neither the best nor the worst road in it."""
        assert normalise.percentile_ranks({41: 1817.5}) == {41: 0.5}

    def test_an_all_equal_population_is_all_median(self):
        """Every way sees below=0, equal=n: (0 + 0.5n)/n = 0.5. No branch, no division by zero."""
        assert normalise.percentile_ranks({51: 3.0, 52: 3.0, 53: 3.0, 54: 3.0}) == {
            51: 0.5, 52: 0.5, 53: 0.5, 54: 0.5}

    def test_an_empty_population_ranks_nothing(self):
        assert normalise.percentile_ranks({}) == {}

    def test_a_rank_is_never_exactly_zero_or_one(self):
        """The consequence ruling R2 states: ranking alone cannot zero a scorable way's score."""
        ranks = normalise.percentile_ranks({60 + i: float(i) for i in range(20)})
        assert min(ranks.values()) == 0.025 and max(ranks.values()) == 0.975  # 0.5/20, 19.5/20

    def test_the_ranks_run_the_same_way_as_the_values(self):
        ranks = normalise.percentile_ranks({71: 0.0, 72: 100.0})
        assert ranks[71] < ranks[72]


class TestTheOrderIsDeterministic:
    def test_the_order_is_by_value_then_way_id_not_insertion_order(self):
        """Ways 1 and 3 tie, as do 5 and 9, and the dict is built in neither way_id nor value order.
        Dropping way_id from the sort key leaves Python's stable sort holding insertion order, [3,1,5,9]."""
        assert normalise.ranked_order({5: 2.0, 3: 1.0, 9: 2.0, 1: 1.0}) == [1, 3, 5, 9]

    def test_the_ranks_do_not_depend_on_the_order_rows_arrive_in(self):
        forwards = normalise.percentile_ranks({81: 1.0, 82: 2.0, 83: 2.0, 84: 4.0})
        backwards = normalise.percentile_ranks({84: 4.0, 83: 2.0, 82: 2.0, 81: 1.0})
        assert forwards == backwards == {81: 0.125, 82: 0.5, 83: 0.5, 84: 0.875}  # (1+0.5*2)/4 = 0.5

    def test_the_returned_mapping_is_in_ranked_order(self):
        """So a caller that writes it out row by row gets a stable file, not a stable set of numbers."""
        ranks = normalise.percentile_ranks({91: 9.0, 92: 1.0, 93: 5.0})
        assert list(ranks) == [92, 93, 91]


class TestThePopulation:
    def test_the_zero_classes_do_not_set_the_curve(self):
        """Four scorable ways and one motorway, whose curvature is above all of them. The population is
        the four: (0+0.5)/4, (1+0.5)/4, (2+0.5)/4, (3+0.5)/4. With the motorway counted it would be
        (0+0.5)/5 = 0.1, 0.3, 0.5, 0.7 - and 15k motorway segments would flatten the back roads."""
        region = [raw(101, curvature=100.0), raw(102, curvature=200.0), raw(103, curvature=300.0),
                  raw(104, curvature=400.0), raw(105, "motorway", curvature=1000.0)]
        out = {record.way_id: record for record in normalise.normalise_region(region)}
        assert [out[i].curvature for i in (101, 102, 103, 104)] == [0.125, 0.375, 0.625, 0.875]
        assert [out[i].curvature for i in (101, 102, 103, 104)] != [0.1, 0.3, 0.5, 0.7]

    def test_every_zero_class_is_excluded_and_passed_through(self):
        region = [raw(120 + i, highway)
                  for i, highway in enumerate(sorted(byways.SCENIC_ZERO_CLASSES))]
        region.append(raw(130, "primary"))
        out = normalise.normalise_region(region)
        assert [record.terms_state for record in out] == [wr.EXCLUDED] * 4 + [wr.NORMALISED]
        assert [record.way_id for record in out] == [120, 121, 122, 123, 130]
        for record in out[:4]:
            assert score.score(**record.score_kwargs()) == 0.0, record.way_id

    def test_a_region_of_only_zero_classes_ranks_nothing_and_refuses_nothing(self):
        out = normalise.normalise_region([raw(141, "motorway"), raw(142, "trunk_link")])
        assert [record.terms_state for record in out] == [wr.EXCLUDED, wr.EXCLUDED]

    def test_an_empty_region_normalises_to_an_empty_region(self):
        assert normalise.normalise_region([]) == []

    def test_population_of_names_the_scorable_ways(self):
        region = [raw(151), raw(152, "trunk"), raw(153, "residential")]
        assert [record.way_id for record in normalise.population_of(region)] == [151, 153]


class TestTheRefusals:
    def test_an_already_normalised_region_is_refused_by_way_id_and_state(self):
        """Ranking a rank re-spaces the region: well defined, and wrong. Ruling R4."""
        once = normalise.normalise_region([raw(161), raw(162, curvature=900.0)])
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region(once)
        assert "161" in str(caught.value) and wr.NORMALISED in str(caught.value), caught.value

    def test_an_excluded_record_is_refused_too(self):
        once = normalise.normalise_region([raw(171, "motorway")])
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region(once)
        assert "171" in str(caught.value) and wr.EXCLUDED in str(caught.value), caught.value

    def test_a_duplicate_way_id_is_refused_by_name(self):
        """One way in the population twice weights it double and puts one arbitrary row in the output."""
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region([raw(181), raw(181, curvature=1.0), raw(182)])
        assert "181" in str(caught.value) and "twice" in str(caught.value), caught.value

    def test_one_bad_record_refuses_the_whole_region_naming_the_field(self):
        """A rank is a statement about a population: dropping the bad row moves every other answer by 1/n."""
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region([raw(191), raw(192, relief=-4.0), raw(193, canopy=2.0)])
        message = str(caught.value)
        assert "192" in message and "relief=" in message, message
        assert "193" in message and "canopy=" in message, message

    def test_a_non_record_is_refused_rather_than_duck_typed(self):
        assert normalise.refusals([{"way_id": 1, "curvature": 5.0}]) != []

    def test_a_refused_region_leaves_its_input_untouched(self):
        region = [raw(201), raw(202, relief=-1.0)]
        with pytest.raises(ValueError):
            normalise.normalise_region(region)
        assert [record.terms_state for record in region] == [wr.RAW, wr.RAW]
        assert region[0].curvature == 640.0

    def test_normalising_returns_new_records_and_leaves_the_input_raw(self):
        region = [raw(211), raw(212, curvature=1000.0)]
        out = normalise.normalise_region(region)
        assert [record.terms_state for record in region] == [wr.RAW, wr.RAW]
        assert region[0].curvature == 640.0 and region[1].curvature == 1000.0
        assert [record.curvature for record in out] == [0.25, 0.75]  # (0+0.5)/2, (1+0.5)/2


class TestTheWholeRecordSurvivesNormalisation:
    def test_the_mapped_terms_and_the_tags_are_untouched(self):
        region = [raw(221, surface=None, byway_status="OD", tunnel_meters=320.0,
                      meters_to_nearest_motorway=80.0, canopy=0.9, impervious=0.1, water=0.3,
                      speed_fit=0.55, points_of_interest=0.4)]
        out = normalise.normalise_region(region)[0]
        assert (out.canopy, out.impervious, out.water, out.speed_fit) == (0.9, 0.1, 0.3, 0.55)
        assert (out.surface, out.byway_status, out.tunnel_meters, out.meters_to_nearest_motorway) == (
            None, "OD", 320.0, 80.0)
        assert out.points_of_interest == 0.4 and out.flags() == ()

    def test_a_normalised_region_is_scorable_end_to_end(self):
        region = [raw(231, curvature=0.0), raw(232, curvature=900.0, highway="motorway"),
                  raw(233, curvature=1817.5, meters_to_nearest_motorway=math.inf)]
        for record in normalise.normalise_region(region):
            value = score.score(**record.score_kwargs())
            assert value is not None and 0.0 <= value <= 1.0, (record.way_id, value)
