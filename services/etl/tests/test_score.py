"""The composite score, and the rank order that is the only thing proving it means anything.

A unit test on the formula proves arithmetic. The pairs below prove the score ranks roads the way a driver
would, and the meta-tests prove the pairs can actually fail - because a rank-order set that passes under any
formula is decoration.
"""
from __future__ import annotations

import pytest

from etl import score as sc


def terms(**kw):
    base = {"curv": 0.0, "elev_gain": 0.0, "speed_fit": 0.0, "sinuosity": 0.0,
            "canopy": 0.0, "relief": 0.0, "impervious": 0.0, "poi": 0.0,
            "water": 0.0, "furniture": 0.0}
    base.update(kw)
    return base


# The pair the geometric mean exists to separate, from the plan: a curvy industrial road that maxes the
# driving terms and has nothing to look at, against a straight redwood road that is all scenery.
CURVY_INDUSTRIAL = terms(curv=1.0, sinuosity=1.0, speed_fit=0.8, elev_gain=0.3,
                         canopy=0.02, relief=0.05, impervious=0.85, furniture=0.8, poi=0.0, water=0.0)
STRAIGHT_REDWOOD = terms(curv=0.15, sinuosity=0.1, speed_fit=0.7, elev_gain=0.2,
                         canopy=0.95, relief=0.5, impervious=0.02, furniture=0.05, poi=0.3, water=0.1)


class TestTheConstants:
    def test_the_weights_and_exponents_are_coherent(self):
        assert sc.weight_problems() == []

    def test_the_score_is_scenery_led(self):
        """0.35 on M, 0.65 on E. A motorcycle product would invert these; this one is a car product."""
        assert sc.ALPHA_E > sc.ALPHA_M

    def test_the_weight_check_can_actually_fail(self, monkeypatch):
        monkeypatch.setattr(sc, "E_WEIGHTS", dict(sc.E_WEIGHTS, canopy=0.34))
        assert any("sum to" in p for p in sc.weight_problems())


class TestGates:
    """Positive evidence only, and safety only."""

    @pytest.mark.parametrize("tags,reason", [
        ({"surface": "gravel"}, "surface=gravel"),
        ({"surface": "dirt"}, "surface=dirt"),
        ({"tracktype": "grade3"}, "tracktype=grade3"),
        ({"highway": "track"}, "highway=track"),
        ({"access": "private"}, "access=private"),
        ({"motor_vehicle": "no"}, "motor_vehicle=no"),
        ({"highway": "service", "service": "driveway"}, "service=driveway"),
        ({"barrier": "gate", "locked": "yes"}, "barrier=gate+locked=yes"),
        ({"ford": "yes"}, "ford=yes"),
    ])
    def test_each_hazard_gates_and_says_why(self, tags, reason):
        assert reason in sc.gate_reasons(tags)
        assert sc.score(STRAIGHT_REDWOOD, tags) == 0.0

    def test_an_unknown_surface_is_not_gated(self):
        """'Unknown' is not 'unpaved'. Gating on the ABSENCE of a tag would remove most rural roads in the
        region - which are the roads this product exists to find."""
        assert sc.gate_reasons({"highway": "unclassified"}) == []
        assert sc.score(STRAIGHT_REDWOOD, {"highway": "unclassified"}) > 0

    def test_a_paved_surface_is_not_gated(self):
        assert sc.gate_reasons({"surface": "asphalt"}) == []

    def test_an_unlocked_gate_is_not_gated(self):
        assert sc.gate_reasons({"barrier": "gate"}) == []

    def test_a_parking_service_road_is_gated_but_an_alley_style_service_road_is_not(self):
        assert sc.gate_reasons({"highway": "service", "service": "parking_aisle"})
        assert sc.gate_reasons({"highway": "service"}) == []


class TestMotorwaysArePenalisedNotExcluded:
    """CLAUDE.md's product invariant, restated as a test because this file is where it would be tidied."""

    @pytest.mark.parametrize("highway", ["motorway", "motorway_link", "trunk", "trunk_link"])
    def test_they_score_zero(self, highway):
        assert sc.score(STRAIGHT_REDWOOD, {"highway": highway}) == 0.0

    @pytest.mark.parametrize("highway", ["motorway", "trunk"])
    def test_but_they_are_NOT_gated(self, highway):
        """The router penalises them. Gating them here would make every Bay Area commute over 15 km
        unroutable rather than unattractive."""
        assert sc.gate_reasons({"highway": highway}) == []
        assert sc.explain(STRAIGHT_REDWOOD, {"highway": highway})["gated"] is False
        assert sc.explain(STRAIGHT_REDWOOD, {"highway": highway})["zero_scored_class"] is True


class TestTheGeometricMean:
    def test_the_redwood_road_outranks_the_curvy_industrial_one(self):
        """The pair the whole formula exists to separate."""
        assert sc.score(STRAIGHT_REDWOOD) > sc.score(CURVY_INDUSTRIAL)

    def test_a_linear_sum_separates_the_pair_only_half_as_well(self):
        """The brief says swapping the geometric mean for a linear sum INVERTS this pair. Measured, it does
        not - not for these values:

            industrial  M=0.820 E=0.064   geometric 0.156   linear 0.328
            redwood     M=0.263 E=0.663   geometric 0.479   linear 0.523

        The linear sum still ranks them correctly, because the industrial road's impervious=0.85 and
        furniture=0.8 punish E hard enough on their own. What the geometric mean actually buys here is
        SEPARATION: a ratio of 3.07 against 1.59, nearly twice the gap.

        That matters for ranking a whole region rather than a pair. A 1.59 gap is within the noise of the
        term estimates; a 3.07 gap is not. The inversion the brief describes is real but needs a different
        corner of the space - `test_a_linear_sum_does_inverting_pairs_exist` builds one.
        """
        def linear(t):
            return sc.ALPHA_M * sc.mean_m(t) + sc.ALPHA_E * sc.mean_e(t)
        geo_ratio = sc.score(STRAIGHT_REDWOOD) / sc.score(CURVY_INDUSTRIAL)
        lin_ratio = linear(STRAIGHT_REDWOOD) / linear(CURVY_INDUSTRIAL)
        assert geo_ratio > lin_ratio * 1.5, (geo_ratio, lin_ratio)

    def test_a_linear_sum_does_invert_some_pairs(self):
        """The property the brief is pointing at, in the corner where it bites: a road that maxes the driving
        terms and is merely bland (rather than actively paved over) beats a balanced road under a sum, and
        loses to it under the product."""
        maxed_drive = terms(curv=1.0, sinuosity=1.0, speed_fit=1.0, elev_gain=1.0,
                            canopy=0.15, relief=0.15, impervious=0.55, furniture=0.55)
        balanced = terms(curv=0.35, sinuosity=0.35, speed_fit=0.6, elev_gain=0.4,
                         canopy=0.45, relief=0.45, impervious=0.25, furniture=0.2, poi=0.2, water=0.15)

        def linear(t):
            return sc.ALPHA_M * sc.mean_m(t) + sc.ALPHA_E * sc.mean_e(t)
        assert linear(maxed_drive) > linear(balanced), "the sum should prefer the one-sided road"
        assert sc.score(balanced) > sc.score(maxed_drive), "the product should prefer the balanced one"

    def test_a_road_strong_in_only_one_half_cannot_score_well(self):
        all_drive = terms(curv=1.0, sinuosity=1.0, speed_fit=1.0, elev_gain=1.0,
                          canopy=0.2, relief=0.2, impervious=0.5, furniture=0.5)
        all_scenery = terms(canopy=1.0, relief=1.0, poi=1.0, water=1.0,
                            curv=0.2, sinuosity=0.2, speed_fit=0.2, elev_gain=0.2)
        both = terms(curv=0.6, sinuosity=0.6, speed_fit=0.6, elev_gain=0.6,
                     canopy=0.6, relief=0.6, poi=0.6, water=0.6, impervious=0.4, furniture=0.4)
        assert sc.score(both) > sc.score(all_drive)
        assert sc.score(both) > sc.score(all_scenery)

    def test_zero_in_either_half_is_zero_overall(self):
        """A road with perfect scenery and no driving qualities at all scores zero, and so does the reverse.
        That is the product doing its job, not a bug: `M ** 0.35` of zero is zero however good E is."""
        scenery_only = terms(canopy=1.0, relief=1.0, poi=1.0, water=1.0)
        assert sc.mean_m(scenery_only) == 0.0
        assert sc.score(scenery_only) == 0.0
        drive_only = terms(curv=1.0, sinuosity=1.0, speed_fit=1.0, elev_gain=1.0,
                           impervious=1.0, furniture=1.0)
        assert sc.mean_e(drive_only) == 0.0
        assert sc.score(drive_only) == 0.0


class TestInvertedTerms:
    def test_impervious_enters_inverted(self):
        clean = terms(canopy=0.5, impervious=0.0)
        paved = terms(canopy=0.5, impervious=1.0)
        assert sc.mean_e(clean) > sc.mean_e(paved)

    def test_furniture_enters_inverted(self):
        assert sc.mean_e(terms(canopy=0.5, furniture=0.0)) > sc.mean_e(terms(canopy=0.5, furniture=1.0))

    def test_a_missing_term_is_not_renormalised_away(self):
        """A road we know nothing about must not score like a road we know is good.

        `{"canopy": 1.0}` alone scores 0.24 - only canopy's own weight - rather than being renormalised onto
        the one term that happens to be present, which would give it 1.0 and rank an unmeasured road top.
        """
        assert sc.mean_e({"canopy": 1.0}) == pytest.approx(0.24)

    def test_an_unmeasured_inverted_term_is_not_a_free_point(self):
        """This is the subtle half. `impervious=0.0` is a MEASUREMENT - no pavement here - and earns the full
        0.16. A MISSING impervious is not that; it is ignorance, and it earns nothing.

        Treating them the same either penalises a genuinely clean road or rewards an unmeasured one, and the
        second is worse: it puts roads nobody has looked at at the top of the ranking.
        """
        measured_clean = sc.mean_e({"canopy": 1.0, "impervious": 0.0, "furniture": 0.0})
        unmeasured = sc.mean_e({"canopy": 1.0})
        assert measured_clean > unmeasured
        assert measured_clean == pytest.approx(0.24 + 0.16 + 0.12)


class TestBywayBonus:
    def test_a_byway_scores_higher_than_the_same_road_without_one(self):
        plain = sc.score(STRAIGHT_REDWOOD)
        flagged = sc.score(STRAIGHT_REDWOOD, byway_bonus=0.15)
        assert flagged > plain

    def test_the_bonus_is_capped(self):
        assert sc.mean_e(terms(canopy=0.5), byway_bonus=99.0) == \
               sc.mean_e(terms(canopy=0.5), byway_bonus=sc.BYWAY_CAP)

    def test_a_negative_bonus_cannot_subtract(self):
        assert sc.mean_e(terms(canopy=0.5), byway_bonus=-1.0) == sc.mean_e(terms(canopy=0.5))

    def test_e_cannot_exceed_one(self):
        """E is a mean of fractions and the exponent is only meaningful on [0, 1]. A road already at 0.95
        that is also a byway is not 1.10 scenic."""
        maxed = terms(canopy=1.0, relief=1.0, poi=1.0, water=1.0, impervious=0.0, furniture=0.0)
        assert sc.mean_e(maxed, byway_bonus=0.15) <= 1.0

    def test_a_byway_bonus_cannot_rescue_a_gated_road(self):
        assert sc.score(STRAIGHT_REDWOOD, {"surface": "gravel"}, byway_bonus=0.15) == 0.0


class TestRange:
    def test_the_score_is_a_fraction(self):
        for t in (CURVY_INDUSTRIAL, STRAIGHT_REDWOOD, terms(), terms(canopy=1.0, curv=1.0)):
            assert 0.0 <= sc.score(t) <= 1.0

    def test_the_best_possible_road_scores_one(self):
        perfect = terms(curv=1.0, elev_gain=1.0, speed_fit=1.0, sinuosity=1.0,
                        canopy=1.0, relief=1.0, poi=1.0, water=1.0, impervious=0.0, furniture=0.0)
        assert sc.score(perfect) == pytest.approx(1.0)

    def test_the_worst_possible_road_scores_zero(self):
        assert sc.score(terms(impervious=1.0, furniture=1.0)) == 0.0


class TestExplain:
    def test_it_reports_the_parts_and_the_gate_reasons(self):
        e = sc.explain(STRAIGHT_REDWOOD, {"surface": "dirt"})
        assert e["score"] == 0.0
        assert e["gated"] is True
        assert "surface=dirt" in e["gate_reasons"]

    def test_a_passable_road_reports_its_two_means(self):
        e = sc.explain(STRAIGHT_REDWOOD)
        assert e["M"] > 0 and e["E"] > 0
        assert e["gate_reasons"] == []