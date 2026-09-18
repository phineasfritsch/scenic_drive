"""`speed_fit`, checked against arithmetic written out by hand.

Every expected number in this file is typed out, with the division that produces it shown in the comment
above it. Three tests are PROPERTIES rather than values and say so - the symmetry test compares the function with
itself at 65-d and 65+d, `walk` is pinned to WALK_PACE_KMH, and the unknown-class fallback is pinned to
DEFAULT_SPEED_KMH["road"] as well as to the literal 50.0. Apart from those, none of them is obtained by
calling the function under test, or by re-deriving it from the
module's own constants at test time: a test that computes its expectation from the thing it checks passes
whatever the constants say, which makes the two most product-defining numbers in the term - the apex and the
two feet - unpinned while looking tested.

The plan gives four words about this term (plan:89, "`speed_fit` triangular at 65 km/h"). Everything else
these tests pin is a ruling in T-0162's task log, and the ruling's identifier is named where it applies.
"""
from __future__ import annotations

import math

import pytest

from etl import score
from etl import speedfit as sf
from etl import tagfilter as tf


class TestTheTriangle:
    def test_the_apex_is_one_at_sixty_five(self):
        # The rising limb at the apex: (65 - 25) / (65 - 25) = 40 / 40 = 1.0
        assert sf.speed_fit(65.0) == 1.0

    def test_both_feet_are_zero(self):
        """R1: the plan gives the apex and neither foot. 25 and 105 are the ruling."""
        assert sf.speed_fit(25.0) == 0.0
        assert sf.speed_fit(105.0) == 0.0

    def test_forty_five_and_eighty_five_are_both_a_half(self):
        """The consequence of a SYMMETRIC triangle, which is what R1 decided."""
        # rising:  (45 - 25) / (65 - 25) = 20 / 40 = 0.5
        # falling: (105 - 85) / (105 - 65) = 20 / 40 = 0.5
        assert sf.speed_fit(45.0) == 0.5
        assert sf.speed_fit(85.0) == 0.5

    def test_the_rising_limb_at_thirty_five(self):
        # (35 - 25) / (65 - 25) = 10 / 40 = 0.25
        assert sf.speed_fit(35.0) == 0.25

    def test_the_falling_limb_at_ninety_five(self):
        # (105 - 95) / (105 - 65) = 10 / 40 = 0.25
        assert sf.speed_fit(95.0) == 0.25

    def test_the_rising_limb_at_sixty(self):
        # (60 - 25) / (65 - 25) = 35 / 40 = 0.875
        assert sf.speed_fit(60.0) == 0.875

    def test_the_falling_limb_at_seventy(self):
        # (105 - 70) / (105 - 65) = 35 / 40 = 0.875
        assert sf.speed_fit(70.0) == 0.875

    @pytest.mark.parametrize("speed", [0.0, 5.0, 24.9, 110.0, 200.0, 1000.0])
    def test_beyond_either_foot_is_zero_and_never_negative(self, speed):
        """A linear ramp that is not clipped goes negative, and `score.out_of_range` would reject the row."""
        assert sf.speed_fit(speed) == 0.0

    @pytest.mark.parametrize("speed", [math.inf, -math.inf, math.nan])
    def test_a_non_finite_speed_is_zero(self, speed):
        assert sf.speed_fit(speed) == 0.0

    @pytest.mark.parametrize("delta", [1.0, 5.0, 10.0, 20.0, 39.0])
    def test_the_triangle_is_symmetric_about_the_apex(self, delta):
        """R1 again, as a property: the term says "how far from 65 km/h" and nothing else."""
        assert sf.speed_fit(65.0 - delta) == pytest.approx(sf.speed_fit(65.0 + delta), abs=1e-12)

    def test_every_speed_from_zero_to_two_hundred_is_a_unit_value(self):
        for tenth in range(0, 2001):
            value = sf.speed_fit(tenth / 10.0)
            assert 0.0 <= value <= 1.0, tenth / 10.0


class TestMaxspeedParsing:
    def test_a_bare_number_is_kilometres_per_hour(self):
        assert sf.parse_maxspeed("65") == 65.0
        assert sf.parse_maxspeed("32.5") == 32.5

    def test_mph_is_converted_with_the_exact_international_mile(self):
        # 45 * 1.609344 = 72.42048
        assert sf.parse_maxspeed("45 mph") == pytest.approx(72.42048, abs=1e-9)
        # 25 * 1.609344 = 40.2336
        assert sf.parse_maxspeed("25 mph") == pytest.approx(40.2336, abs=1e-9)

    def test_the_redundant_km_h_suffix_parses_as_written(self):
        assert sf.parse_maxspeed("50 km/h") == 50.0

    @pytest.mark.parametrize("raw", ["45mph", "45 MPH", "45Mph", "  45 mph  "])
    def test_the_suffix_is_case_insensitive_and_the_space_optional(self, raw):
        # 45 * 1.609344 = 72.42048, whatever the spelling
        assert sf.parse_maxspeed(raw) == pytest.approx(72.42048, abs=1e-9)

    def test_signals_and_none_are_named_as_carrying_no_number(self):
        """R3 and R4. Named in the module so the decision is an identifier, not a regex accident."""
        assert "signals" in sf.NO_NUMBER_VALUES
        assert "none" in sf.NO_NUMBER_VALUES

    def test_signals_falls_to_the_class_default(self):
        """R3: a variable-limit sign states that the number changes; there is no number to read."""
        assert sf.parse_maxspeed("signals") is None
        # residential default 40: (40 - 25) / (65 - 25) = 15 / 40 = 0.375
        assert sf.speed_fit_for_tags(highway="residential", maxspeed="signals") == 0.375

    def test_none_falls_to_the_class_default_rather_than_to_zero(self):
        """R4: `none` on a California way is a mis-tag, and 0.0 would be fabricated evidence."""
        assert sf.parse_maxspeed("none") is None
        # tertiary default 60: (60 - 25) / (65 - 25) = 35 / 40 = 0.875
        assert sf.speed_fit_for_tags(highway="tertiary", maxspeed="none") == 0.875

    def test_walk_parses_and_lands_below_the_lower_foot(self):
        """R5: `walk` IS a speed statement, unlike the other two. The 0.0 is what is pinned, not the 5."""
        assert sf.parse_maxspeed("walk") == sf.WALK_PACE_KMH
        assert sf.speed_fit_for_tags(highway="residential", maxspeed="walk") == 0.0

    @pytest.mark.parametrize("raw", ["CA:urban", "DE:rural", "50 @ (22:00-06:00)", "30;50", "60 knots",
                                     "fast", "", "   ", "50 km/h ; 30 km/h"])
    def test_the_shapes_we_deliberately_do_not_resolve(self, raw):
        """R2: each needs a resolver this term does not have, and a wrong number read confidently is worse."""
        assert sf.parse_maxspeed(raw) is None

    @pytest.mark.parametrize("raw", ["0", "0.0", "-20", "-20 mph"])
    def test_zero_and_negative_values_are_not_speeds(self, raw):
        assert sf.parse_maxspeed(raw) is None

    def test_an_absent_tag_is_not_a_speed(self):
        assert sf.parse_maxspeed(None) is None

    def test_an_absurd_number_is_accepted_and_scores_zero(self):
        """R6: a typo'd 400 fails in the direction of "less scenic", which is the safe direction."""
        assert sf.parse_maxspeed("400") == 400.0
        assert sf.speed_fit_for_tags(highway="residential", maxspeed="400") == 0.0


class TestTheDefaultTable:
    """The table is local to the module (R7) and pinned here against literals, entry by entry."""

    EXPECTED = {
        "motorway": 105.0,
        "motorway_link": 60.0,
        "trunk": 100.0,
        "trunk_link": 55.0,
        "primary": 90.0,
        "primary_link": 50.0,
        "secondary": 70.0,
        "secondary_link": 45.0,
        "tertiary": 60.0,
        "tertiary_link": 40.0,
        "unclassified": 55.0,
        "residential": 40.0,
        "living_street": 20.0,
        "service": 25.0,
        "track": 25.0,
        "road": 50.0,
    }

    def test_the_table_is_exactly_the_one_that_was_argued(self):
        assert sf.DEFAULT_SPEED_KMH == self.EXPECTED

    def test_every_highway_value_the_extract_keeps_has_a_default(self):
        """R8. A class added to the filter must not quietly arrive at the unknown-class fallback."""
        for cls, values in tf.WAY_CLASSES.items():
            for value in values:
                assert sf.default_speed_kmh(value) is not None, f"{cls}/{value} has no default speed"

    def test_the_table_has_no_entry_the_extract_does_not_keep(self):
        """The other direction: a table entry for a class nobody keeps is a speed nobody can check."""
        kept = {v for values in tf.WAY_CLASSES.values() for v in values}
        assert set(sf.DEFAULT_SPEED_KMH) == kept

    def test_an_unrecognised_class_has_no_table_entry(self):
        assert sf.default_speed_kmh("gravel_goat_path") is None
        assert sf.default_speed_kmh(None) is None

    def test_the_unknown_class_fallback_is_the_speed_of_highway_road(self):
        """R7: "a class we do not know" and OSM's "classification unknown" are the same state."""
        assert sf.UNKNOWN_CLASS_SPEED_KMH == 50.0
        assert sf.UNKNOWN_CLASS_SPEED_KMH == sf.DEFAULT_SPEED_KMH["road"]


class TestFromTagsToTheTerm:
    def test_a_parsed_maxspeed_beats_the_class_default(self):
        """A residential street posted at 65 is scored on the 65, not on the table's 40."""
        assert sf.speed_kmh_for_tags(highway="residential", maxspeed="65") == 65.0
        assert sf.speed_fit_for_tags(highway="residential", maxspeed="65") == 1.0

    def test_an_unreadable_maxspeed_falls_back_to_the_class(self):
        assert sf.speed_kmh_for_tags(highway="residential", maxspeed="CA:urban") == 40.0
        # (40 - 25) / (65 - 25) = 15 / 40 = 0.375
        assert sf.speed_fit_for_tags(highway="residential", maxspeed="CA:urban") == 0.375

    @pytest.mark.parametrize("highway,expected", [
        ("residential", 0.375),     # 40:  (40 - 25) / 40 = 15 / 40 = 0.375
        ("living_street", 0.0),     # 20:  at or below the lower foot
        ("service", 0.0),           # 25:  exactly the lower foot
        ("tertiary", 0.875),        # 60:  (60 - 25) / 40 = 35 / 40 = 0.875
        ("unclassified", 0.75),     # 55:  (55 - 25) / 40 = 30 / 40 = 0.75
        ("secondary", 0.875),       # 70:  (105 - 70) / 40 = 35 / 40 = 0.875
        ("primary", 0.375),         # 90:  (105 - 90) / 40 = 15 / 40 = 0.375
        ("trunk", 0.125),           # 100: (105 - 100) / 40 = 5 / 40 = 0.125
        ("motorway", 0.0),          # 105: exactly the upper foot
    ])
    def test_the_class_defaults_score_what_the_arithmetic_says(self, highway, expected):
        assert sf.speed_fit_for_tags(highway=highway) == expected

    def test_a_road_posted_in_mph(self):
        # 55 mph = 55 * 1.609344 = 88.51392; (105 - 88.51392) / 40 = 16.48608 / 40 = 0.412152
        assert sf.speed_fit_for_tags(highway="primary", maxspeed="55 mph") == pytest.approx(0.412152,
                                                                                           abs=1e-9)

    def test_an_unrecognised_class_with_no_tag_uses_the_fallback(self):
        # 50: (50 - 25) / (65 - 25) = 25 / 40 = 0.625
        assert sf.speed_fit_for_tags(highway="gravel_goat_path") == 0.625
        assert sf.speed_fit_for_tags(highway=None) == 0.625

    def test_the_term_is_a_float_for_every_class_the_extract_keeps(self):
        for values in tf.WAY_CLASSES.values():
            for value in values:
                term = sf.speed_fit_for_tags(highway=value)
                assert isinstance(term, float)
                assert 0.0 <= term <= 1.0, value


class TestTheSeamWithScore:
    """The consumer's own validator is the arbiter of whether this term is usable, not this file's opinion."""

    def test_score_accepts_the_produced_term_for_every_kept_class(self):
        for values in tf.WAY_CLASSES.values():
            for value in values:
                terms = {name: 0.5 for name in score.UNIT_TERMS}
                terms["speed_fit"] = sf.speed_fit_for_tags(highway=value)
                assert score.out_of_range(terms) == [], value

    def test_score_accepts_the_produced_term_for_the_awkward_maxspeed_strings(self):
        for raw in (None, "", "signals", "none", "walk", "400", "45 mph", "CA:urban", "65"):
            terms = {name: 0.5 for name in score.UNIT_TERMS}
            terms["speed_fit"] = sf.speed_fit_for_tags(highway="secondary", maxspeed=raw)
            assert score.out_of_range(terms) == [], raw
