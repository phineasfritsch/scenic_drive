"""The region percentile rank: the estimator, the tie rule, the population and the order.

EVERY EXPECTED NUMBER IN THIS FILE IS TYPED OUT from arithmetic shown beside it. The formula is
`(below + 0.5*equal) / population` (T-0163 log, ruling R2), so a population of 4 with no ties gives
0.125 / 0.375 / 0.625 / 0.875 and every case below is chosen so the answer is an exact decimal - a test
whose expectation is computed from the function it checks proves only that the function equals itself.

The three properties the fixture cannot see are here, each with its own named test: the TIE RULE
(`test_a_tie_group_takes_the_average_rank`), the POPULATION FILTER
(`test_the_zero_classes_do_not_set_the_curve`) and the SORT KEY
(`test_the_order_is_by_value_then_way_id_not_insertion_order`). The last two classes are WHICH POPULATION
a rank counts against: a supplied `reference`, and the ways that declined to answer.
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


class TestARankAgainstASuppliedReference:
    """The seam for the region-relativity question (STILL OPEN in T-0163's task file): the estimator does
    not change, only the population it counts against, and the default is today's answer."""
    def test_a_way_is_ranked_inside_the_reference_population_it_is_added_to(self):
        """reference [10, 20, 30]. 5 -> below=0, equal=0+1 -> (0+0.5)/4 = 0.125. 20 -> below=1, equal=1+1
        -> (1+1.0)/4 = 0.5. 25 -> below=2, equal=1 -> (2+0.5)/4 = 0.625. 35 -> (3+0.5)/4 = 0.875."""
        ranks = normalise.ranks_against({301: 25.0, 302: 20.0, 303: 5.0, 304: 35.0}, [10.0, 20.0, 30.0])
        assert ranks == {303: 0.125, 302: 0.5, 301: 0.625, 304: 0.875}

    def test_a_rank_against_a_reference_is_still_never_exactly_zero_or_one(self):
        """Why the way itself is counted in: without it, a way below every reference value takes exactly
        0.0 and one above every value exactly 1.0, and a scorable way on 0.0 is what ruling R2 and
        CLAUDE.md's invariant reserve for a zero CLASS. reference [0, 1, 2]: (0+0.5)/4 and (3+0.5)/4."""
        assert normalise.ranks_against({311: -5.0, 312: 5000.0}, [0.0, 1.0, 2.0]) == {311: 0.125,
                                                                                     312: 0.875}

    def test_a_reference_makes_a_ways_rank_independent_of_its_neighbours(self):
        """Two ways at one value against reference [10, 20, 30]: below=2, equal=0+1 -> (2+0.5)/4 = 0.625
        EACH, neither seeing the other. The region's own population says 0.5 each (below=0, equal=2,
        n=2) - and 0.5 for the pair whatever their values were."""
        assert normalise.ranks_against({321: 25.0, 322: 25.0}, [10.0, 20.0, 30.0]) == {321: 0.625,
                                                                                      322: 0.625}
        assert normalise.percentile_ranks({321: 25.0, 322: 25.0}) == {321: 0.5, 322: 0.5}

    def test_normalise_region_ranks_the_named_terms_against_the_reference_and_the_rest_against_itself(self):
        """curvature against reference [0, 200, 400, 600]: 100 -> below=1, equal=0+1 -> (1 + 0.5)/5 = 0.3;
        500 -> below=3, equal=1 -> (3 + 0.5)/5 = 0.7. elevation_gain is NOT in the mapping and keeps the
        region's own curve: (0 + 0.5)/2 = 0.25 and (1 + 0.5)/2 = 0.75 - the pair those two ways would get
        for ANY two distinct values, which is the region-relativity this argument exists to fix."""
        region = [raw(331, curvature=100.0, elevation_gain=10.0),
                  raw(332, curvature=500.0, elevation_gain=20.0)]
        out = {record.way_id: record for record in
               normalise.normalise_region(region, reference={"curvature": [0.0, 200.0, 400.0, 600.0]})}
        assert [out[331].curvature, out[332].curvature] == [0.3, 0.7]
        assert [out[331].elevation_gain, out[332].elevation_gain] == [0.25, 0.75]

    def test_the_default_is_the_regions_own_population_and_nothing_moves(self):
        """No argument and an explicit None are the same run: (0+0.5)/4, (1+0.5)/4, (2+0.5)/4, (3+0.5)/4."""
        region = [raw(340 + i, curvature=100.0 * i) for i in (1, 2, 3, 4)]
        plain = [record.curvature for record in normalise.normalise_region(region)]
        explicit = [record.curvature for record in normalise.normalise_region(region, reference=None)]
        assert plain == explicit == [0.125, 0.375, 0.625, 0.875]

    def test_a_reference_for_a_term_that_is_not_ranked_is_refused_by_name(self):
        # canopy is MAPPED (ruling R1): a reference for it would be silently ignored, which is worse.
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region([raw(351)], reference={"canopy": [0.1, 0.2]})
        assert "canopy" in str(caught.value), caught.value

    def test_an_empty_reference_is_refused_rather_than_divided_by(self):
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region([raw(361)], reference={"curvature": []})
        assert "curvature" in str(caught.value) and "empty" in str(caught.value), caught.value

    def test_a_reference_value_that_is_not_a_finite_number_is_refused_by_name(self):
        """A NaN compares false both ways, so it would sit in the population and change every divisor."""
        for bad in (float("nan"), math.inf, "600"):
            with pytest.raises(ValueError) as caught:
                normalise.normalise_region([raw(371)], reference={"relief": [1.0, bad]})
            assert "relief" in str(caught.value), (bad, caught.value)


class TestAWayThatDeclinedToAnswer:
    """`sinuosity_declined`: T-0161 returns its floor for a closed way, which is not a measurement."""
    def test_a_declined_sinuosity_is_out_of_the_population_and_comes_back_at_the_floor(self):
        """Four ways answered (1.1, 1.2, 1.3, 1.4) and one declined. The population is the four:
        (0+0.5)/4 ... (3+0.5)/4. Counting the closed way in would say 0.1, 0.3, 0.5, 0.7, and thousands
        of roundabouts at one repeated floor value would flatten the curve outright."""
        region = [raw(401, sinuosity=1.1), raw(402, sinuosity=1.2), raw(403, sinuosity=1.3),
                  raw(404, sinuosity=1.4), raw(405, sinuosity=1.0, sinuosity_declined=True)]
        out = {record.way_id: record for record in normalise.normalise_region(region)}
        assert [out[i].sinuosity for i in (401, 402, 403, 404)] == [0.125, 0.375, 0.625, 0.875]
        assert [out[i].sinuosity for i in (401, 402, 403, 404)] != [0.1, 0.3, 0.5, 0.7]
        assert out[405].sinuosity == wr.DECLINED_RANK == 0.0
        assert out[405].flags() == (wr.POI_ABSENT_FLAG, wr.SINUOSITY_DECLINED_FLAG)

    def test_declining_one_term_does_not_take_the_way_off_the_other_curves(self):
        """Still in the curvature population, n=4: 0.125/0.375/0.625/0.875. The three ways that answered
        share sinuosity 1.4 and tie at (0 + 0.5*3)/3 = 0.5."""
        region = [raw(411, curvature=100.0), raw(412, curvature=200.0, sinuosity_declined=True),
                  raw(413, curvature=300.0), raw(414, curvature=400.0)]
        out = {record.way_id: record for record in normalise.normalise_region(region)}
        assert [out[i].curvature for i in (411, 412, 413, 414)] == [0.125, 0.375, 0.625, 0.875]
        assert [out[i].sinuosity for i in (411, 413, 414)] == [0.5, 0.5, 0.5]
        assert out[412].sinuosity == 0.0

    def test_a_region_where_every_way_declined_ranks_no_sinuosity_and_refuses_nothing(self):
        """The empty-population case through a real region: `percentile_ranks({})` is `{}`, every way
        takes the floor, the other four terms rank as usual (both at 640.0: (0 + 0.5*2)/2 = 0.5)."""
        out = normalise.normalise_region([raw(421, sinuosity_declined=True),
                                          raw(422, sinuosity_declined=True)])
        assert [record.sinuosity for record in out] == [0.0, 0.0]
        assert [record.curvature for record in out] == [0.5, 0.5]

    def test_a_declined_way_still_scores_and_scores_below_the_way_that_answered(self):
        """A penalty, not a refusal: plan:86 weights sinuosity 0.15 and 441 keeps the other 0.85 of M.
        442 is the only way in the sinuosity population, so it takes (0 + 0.5)/1 = 0.5."""
        out = normalise.normalise_region([raw(441, sinuosity_declined=True), raw(442)])
        values = [score.score(**record.score_kwargs()) for record in out]
        assert all(value is not None and 0.0 < value <= 1.0 for value in values), values
        assert values[0] < values[1], values


class TestTheRefusals:
    def test_an_already_normalised_region_is_refused_by_way_id_and_state(self):
        """Ranking a rank re-spaces the region: well defined, and wrong. Ruling R4."""
        once = normalise.normalise_region([raw(161), raw(162, curvature=900.0)])
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region(once)
        assert "161" in str(caught.value) and wr.NORMALISED in str(caught.value), caught.value

    def test_an_already_normalised_region_names_every_offender_and_not_just_the_first(self):
        """Recordable R-3 from PR #93's review, taken: `refusals` and `with_ranks`'s `_require_raw` both
        refuse a second pass and the two tests around this one cannot tell them apart. `_require_raw`
        raises on the FIRST record, so what the region-whole check adds is the LIST of offenders."""
        once = normalise.normalise_region([raw(451), raw(452, curvature=900.0)])
        with pytest.raises(ValueError) as caught:
            normalise.normalise_region(once)
        message = str(caught.value)
        assert "451" in message and "452" in message, message

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
