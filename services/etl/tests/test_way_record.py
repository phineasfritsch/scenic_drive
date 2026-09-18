"""The record's validator: what it refuses, by field name, and in which state.

The record exists because a dict cannot say whether 300.0 is metres of climb or a rank (see
`etl/way_record.py`). These tests hold it to that: every refusal is asserted by the FIELD NAME in the
message, not by the fact that something was refused, because "invalid record" three stages downstream is
the message that costs an afternoon.

The seam itself is asserted here too, against `inspect.signature(score.score)` rather than against a list
retyped in this file: a term added to `score.score` must land in RANKED_TERMS, MAPPED_TERMS or
DEFERRED_TERMS, and this test is what says so out loud.
"""
from __future__ import annotations

import inspect
import math

import pytest

from etl import score, way_record as wr

# The terms a raw record carries, in producer units: a curvature sum, metres, metres, a ratio, a rate.
RAW_TERMS = {"curvature": 640.0, "elevation_gain": 300.0, "relief": 180.0, "sinuosity": 1.4,
             "furniture": 0.1}
MAPPED = {"canopy": 0.5, "impervious": 0.25, "water": 0.1, "speed_fit": 0.6}
RANKS = {"curvature": 0.8, "elevation_gain": 0.6, "relief": 0.4, "sinuosity": 0.5, "furniture": 0.2}


def raw(**kw) -> wr.WayRecord:
    """A valid raw record, with `kw` overriding one thing at a time."""
    fields = dict(way_id=700000001, highway="secondary", **RAW_TERMS, **MAPPED)
    fields.update(kw)
    return wr.WayRecord(**fields)


class TestTheSeam:
    def test_every_keyword_score_takes_is_a_field_on_the_record(self):
        keywords = set(inspect.signature(score.score).parameters)
        assert keywords <= set(wr.WayRecord.field_names()), sorted(keywords - set(wr.WayRecord.field_names()))

    def test_every_unit_term_score_wants_is_classified_ranked_mapped_or_deferred(self):
        """A term added to score.py with no classification would arrive raw and be scored as a rank."""
        assert set(wr.SCORE_TERMS) == set(score.UNIT_TERMS), (
            "unclassified: %s / unknown to score.py: %s"
            % (sorted(set(score.UNIT_TERMS) - set(wr.SCORE_TERMS)),
               sorted(set(wr.SCORE_TERMS) - set(score.UNIT_TERMS))))

    def test_the_three_classifications_do_not_overlap(self):
        names = wr.RANKED_TERMS + wr.MAPPED_TERMS + wr.DEFERRED_TERMS
        assert len(set(names)) == len(names), names

    def test_score_kwargs_is_exactly_scores_keywords(self):
        record = raw().with_ranks(RANKS)
        assert set(record.score_kwargs()) == set(inspect.signature(score.score).parameters)

    def test_a_normalised_record_scores_without_a_refusal(self):
        value = score.score(**raw().with_ranks(RANKS).score_kwargs())
        assert value is not None and 0.0 <= value <= 1.0, value


class TestTheValidatorNamesTheField:
    def test_a_raw_term_that_is_negative_is_refused_by_name(self):
        """Producer units are non-negative: a negative curvature sum or a negative climb is a bug upstream."""
        problems = raw(curvature=-1.0).problems()
        assert any(p.startswith("curvature=") and "negative" in p for p in problems), problems
        assert not any(p.startswith("relief") for p in problems), problems

    def test_a_raw_term_that_is_not_finite_is_refused_by_name(self):
        for bad in (math.inf, float("nan")):
            problems = raw(elevation_gain=bad).problems()
            assert any(p.startswith("elevation_gain=") and "finite" in p for p in problems), (bad, problems)

    def test_a_mapped_term_above_one_is_refused_by_name(self):
        problems = raw(canopy=1.0001).problems()
        assert any(p.startswith("canopy=") and "0..1" in p for p in problems), problems

    def test_a_mapped_term_below_zero_is_refused_by_name(self):
        problems = raw(water=-0.0001).problems()
        assert any(p.startswith("water=") and "0..1" in p for p in problems), problems

    def test_a_mapped_term_that_is_not_a_number_is_refused_by_name(self):
        problems = raw(speed_fit="0.6").problems()
        assert any(p.startswith("speed_fit=") for p in problems), problems

    def test_a_raw_term_is_allowed_to_be_far_outside_zero_to_one(self):
        """The whole point of the raw state: 1817.5 is a real curvature sum (see T-0112's measurements)."""
        assert raw(curvature=1817.5, elevation_gain=1500.0, relief=900.0).problems() == []

    def test_a_way_id_that_is_not_a_positive_integer_is_refused(self):
        for bad in (0, -7, 1.5, True, "700000001"):
            problems = raw(way_id=bad).problems()
            assert any(p.startswith("way_id=") for p in problems), (bad, problems)

    def test_an_infinite_tunnel_is_refused_here_because_score_refuses_it_too(self):
        """score.py:133 returns None on an infinite tunnel. A tunnel of unknown length is not every length."""
        assert any(p.startswith("tunnel_meters=") for p in raw(tunnel_meters=math.inf).problems())
        assert score.score(highway="secondary", tunnel_meters=math.inf,
                           **{name: 0.5 for name in score.UNIT_TERMS}) is None

    def test_a_negative_distance_to_a_motorway_is_refused(self):
        assert any(p.startswith("meters_to_nearest_motorway=")
                   for p in raw(meters_to_nearest_motorway=-1.0).problems())

    def test_infinity_is_a_valid_distance_to_a_motorway(self):
        """No motorway anywhere near is what score.py's own default says (score.py:122)."""
        assert raw(meters_to_nearest_motorway=math.inf).problems() == []

    def test_a_points_of_interest_outside_zero_to_one_is_refused_by_name(self):
        assert any(p.startswith("points_of_interest=") for p in raw(points_of_interest=1.4).problems())

    def test_a_surface_that_is_not_a_string_is_refused_by_name(self):
        assert any(p.startswith("surface=") for p in raw(surface=3).problems())

    def test_an_unknown_terms_state_is_refused_by_name(self):
        assert any(p.startswith("terms_state=") for p in raw(terms_state="ranked").problems())


class TestUnknownAndMissingFields:
    def test_an_unknown_field_is_named_rather_than_left_to_a_type_error(self):
        mapping = dict(way_id=700000001, highway="secondary", **RAW_TERMS, **MAPPED)
        mapping["elevationGain"] = 300.0
        mapping["scenic_score"] = 0.7
        with pytest.raises(ValueError) as caught:
            wr.WayRecord.from_mapping(mapping)
        assert "elevationGain" in str(caught.value) and "scenic_score" in str(caught.value), caught.value

    def test_a_missing_term_is_named(self):
        mapping = dict(way_id=700000001, highway="secondary", **RAW_TERMS, **MAPPED)
        del mapping["relief"]
        del mapping["canopy"]
        with pytest.raises(ValueError) as caught:
            wr.WayRecord.from_mapping(mapping)
        assert "relief" in str(caught.value) and "canopy" in str(caught.value), caught.value

    def test_a_complete_mapping_round_trips(self):
        mapping = dict(way_id=700000001, highway="secondary", **RAW_TERMS, **MAPPED)
        assert wr.WayRecord.from_mapping(mapping) == raw()


class TestTheStatesRefuseEachOther:
    def test_a_raw_record_refuses_to_be_scored(self):
        """Raw metres through score.score answer None (score.py:131), three stages from the mistake."""
        with pytest.raises(ValueError) as caught:
            raw().score_kwargs()
        assert "700000001" in str(caught.value) and wr.RAW in str(caught.value), caught.value

    def test_the_raw_terms_score_none_if_they_reach_the_scorer_anyway(self):
        """Why the refusal above is worth having, demonstrated rather than asserted about."""
        record = raw()
        terms = {name: getattr(record, name) for name in score.UNIT_TERMS if name != "points_of_interest"}
        assert score.score(highway="secondary", points_of_interest=0.0, **terms) is None

    def test_a_normalised_record_cannot_be_ranked_again(self):
        record = raw().with_ranks(RANKS)
        with pytest.raises(ValueError) as caught:
            record.with_ranks(RANKS)
        assert wr.NORMALISED in str(caught.value) and "700000001" in str(caught.value), caught.value

    def test_ranking_refuses_a_partial_set_of_ranks(self):
        partial = {name: 0.5 for name in wr.RANKED_TERMS if name != "furniture"}
        with pytest.raises(ValueError) as caught:
            raw().with_ranks(partial)
        assert "furniture" in str(caught.value), caught.value

    def test_ranking_refuses_a_rank_for_a_term_that_is_not_ranked(self):
        with pytest.raises(ValueError) as caught:
            raw().with_ranks(dict(RANKS, canopy=0.5))
        assert "canopy" in str(caught.value), caught.value

    def test_a_normalised_record_with_a_rank_outside_zero_to_one_is_refused_by_name(self):
        record = raw().with_ranks(dict(RANKS, relief=1.4))
        assert any(p.startswith("relief=") and "0..1" in p for p in record.problems()), record.problems()

    def test_excluding_a_scorable_way_is_refused(self):
        with pytest.raises(ValueError) as caught:
            raw().excluded_from_population()
        assert "secondary" in str(caught.value), caught.value

    def test_an_excluded_record_holds_no_rank(self):
        """Ruling R3: EXCLUDED_RANK is not a measurement, and the validator says so by field name."""
        record = raw(highway="motorway").excluded_from_population()
        assert record.terms_state == wr.EXCLUDED
        for name in wr.RANKED_TERMS:
            assert getattr(record, name) == wr.EXCLUDED_RANK, name
        assert record.problems() == []
        smuggled = record.__class__(**dict(
            {f: getattr(record, f) for f in record.field_names()}, curvature=0.8))
        assert any(p.startswith("curvature=") and "EXCLUDED_RANK" in p for p in smuggled.problems())

    def test_an_excluded_record_keeps_its_mapped_terms(self):
        """Only the ranked fields are pinned: canopy was measured and the measurement survives."""
        record = raw(highway="trunk", canopy=0.77).excluded_from_population()
        assert record.canopy == 0.77
        assert score.score(**record.score_kwargs()) == 0.0


class TestPointsOfInterestIsDeferredNotDefaulted:
    def test_an_absent_value_is_flagged_and_substituted_rather_than_guessed(self):
        record = raw().with_ranks(RANKS)
        assert record.points_of_interest is None
        assert record.flags() == (wr.POI_ABSENT_FLAG,)
        assert record.score_kwargs()["points_of_interest"] == wr.POI_ABSENT == 0.0

    def test_a_value_that_is_there_is_passed_through_and_not_flagged(self):
        record = raw(points_of_interest=0.75).with_ranks(RANKS)
        assert record.flags() == ()
        assert record.score_kwargs()["points_of_interest"] == 0.75

    def test_the_substitution_is_visible_in_the_score(self):
        """A silent 0.5 would be indistinguishable from a measured 0.5; 0.0 with a flag is not."""
        absent = score.score(**raw().with_ranks(RANKS).score_kwargs())
        present = score.score(**raw(points_of_interest=0.5).with_ranks(RANKS).score_kwargs())
        assert absent < present, (absent, present)
