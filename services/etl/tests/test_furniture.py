"""Street furniture per kilometre, checked against counts and divisions written out by hand.

Every expected number here is typed out with its arithmetic in the comment above it, and the accepted tag
set is compared against a literal dict rather than against the module's own constant reshaped - a set
"checked" by rebuilding it from the thing under test would pass after any edit to it, which is precisely how
a term quietly changes meaning between two releases.

The invariant that matters most in this file: the value is RAW. It is not in 0..1, it is not clamped and it
is not inverted. `score.scenery_mean` consumes `0.12 * (1 - furniture)` (score.py:92) AFTER T-0163's region
normaliser has ranked it, and a well-meaning clamp added here would be invisible to every other test in the
repository - so `test_the_rate_is_unbounded_and_is_not_normalised_here` exists to go red on it.
"""
from __future__ import annotations

import math

import pytest

from etl import furniture as fn

LAMP = {"highway": "street_lamp"}
SIGNAL = {"highway": "traffic_signals"}
CROSSING = {"highway": "crossing"}
PLAIN = {}


class TestWhatCounts:
    def test_the_accepted_value_sets_are_the_ones_that_were_argued(self):
        assert fn.FURNITURE_VALUES == {
            "highway": frozenset({"crossing", "stop", "street_lamp", "traffic_signals"}),
            "barrier": frozenset({"bollard"}),
        }

    def test_the_any_value_keys_are_the_ones_that_were_argued(self):
        assert fn.FURNITURE_KEYS_ANY_VALUE == frozenset({"traffic_calming"})
        assert fn.ANY_VALUE_EXCEPTIONS == frozenset({"no"})

    @pytest.mark.parametrize("tags", [
        {"highway": "street_lamp"},
        {"highway": "traffic_signals"},
        {"highway": "stop"},
        {"highway": "crossing"},
        {"barrier": "bollard"},
        {"traffic_calming": "table"},
        {"traffic_calming": "hump"},
        {"traffic_calming": "cushion"},
        {"traffic_calming": "chicane"},
        {"traffic_calming": "rumble_strip"},
        {"traffic_calming": "a_value_nobody_has_invented_yet"},
    ])
    def test_the_accepted_set_counts(self, tags):
        assert fn.is_furniture(tags) is True

    def test_traffic_calming_is_accepted_by_key_so_a_new_value_still_counts(self):
        """Enumerating the wiki's value list would file every new calming type as "not urban"."""
        assert fn.is_furniture({"traffic_calming": "island"}) is True

    def test_traffic_calming_no_does_not_count(self):
        """R11: `=no` on this key states that the junction explicitly has NONE."""
        assert fn.is_furniture({"traffic_calming": "no"}) is False

    def test_an_empty_value_does_not_count(self):
        assert fn.is_furniture({"traffic_calming": ""}) is False

    @pytest.mark.parametrize("tags", [
        {"barrier": "gate"},
        {"barrier": "lift_gate"},
        {"barrier": "cycle_barrier"},
        {"highway": "turning_circle"},
        {"highway": "passing_place"},
        {"highway": "mini_roundabout"},
        {"highway": "bus_stop"},
        {"highway": "residential"},
        {"amenity": "cafe"},
        {"shop": "bakery"},
        {"railway": "level_crossing"},
        {"tourism": "viewpoint"},
        {"name": "Skyline Boulevard"},
    ])
    def test_what_is_deliberately_not_counted(self, tags):
        """R12. A gate is the SAFETY gate's input (plan:81); a passing place is evidence of the opposite."""
        assert fn.is_furniture(tags) is False

    def test_an_untagged_node_does_not_count(self):
        assert fn.is_furniture(PLAIN) is False


class TestCounting:
    def test_one_node_carrying_two_accepted_tags_counts_once(self):
        """R10: a raised crossing is `highway=crossing` AND `traffic_calming=table` on ONE node."""
        raised_crossing = {"highway": "crossing", "traffic_calming": "table"}
        assert fn.furniture_count([raised_crossing]) == 1

    def test_the_count_is_the_number_of_matching_nodes(self):
        # 6 nodes, of which street_lamp + traffic_signals + bollard match and 3 do not: 3
        nodes = [LAMP, SIGNAL, {"barrier": "bollard"}, PLAIN, {"barrier": "gate"}, {"highway": "bus_stop"}]
        assert fn.furniture_count(nodes) == 3

    def test_a_way_with_no_nodes_counts_nothing(self):
        assert fn.furniture_count([]) == 0

    def test_a_way_whose_nodes_are_all_plain_counts_nothing(self):
        assert fn.furniture_count([PLAIN, PLAIN, PLAIN]) == 0

    def test_a_generator_is_accepted(self):
        """The way record will hand this a lazy sequence of node tags, not a materialised list."""
        assert fn.furniture_count(tags for tags in [LAMP, PLAIN, SIGNAL]) == 2


class TestTheRawRate:
    def test_three_pieces_on_fifteen_hundred_metres(self):
        # 3 / (1500 / 1000) = 3 / 1.5 = 2.0
        nodes = [LAMP, SIGNAL, CROSSING]
        assert fn.furniture_per_km(nodes=nodes, length_m=1500.0) == 2.0

    def test_one_piece_on_two_hundred_and_fifty_metres(self):
        # 1 / (250 / 1000) = 1 / 0.25 = 4.0
        assert fn.furniture_per_km(nodes=[SIGNAL], length_m=250.0) == 4.0

    def test_nothing_on_two_kilometres_is_zero_per_km(self):
        # 0 / (2000 / 1000) = 0 / 2.0 = 0.0
        assert fn.furniture_per_km(nodes=[PLAIN, {"barrier": "gate"}], length_m=2000.0) == 0.0

    def test_the_rate_is_unbounded_and_is_not_normalised_here(self):
        """R9: 0..1 is T-0163's job. A clamp added here would be invisible everywhere else."""
        # 30 pieces / (200 / 1000) = 30 / 0.2 = 150.0
        assert fn.furniture_per_km(nodes=[SIGNAL] * 30, length_m=200.0) == 150.0

    def test_the_rate_is_not_inverted_here(self):
        """score.py:92 applies the `1 -`. A busy street must come out of THIS module larger, not smaller."""
        busy = fn.furniture_per_km(nodes=[LAMP, SIGNAL, CROSSING], length_m=1000.0)
        quiet = fn.furniture_per_km(nodes=[PLAIN], length_m=1000.0)
        # 3 / 1.0 = 3.0 against 0 / 1.0 = 0.0
        assert busy == 3.0
        assert quiet == 0.0
        assert busy > quiet

    def test_a_zero_length_way_has_no_rate(self):
        """R13: 0.0 would claim the way is rural. None is "no opinion"."""
        assert fn.furniture_per_km(nodes=[SIGNAL], length_m=0.0) is None

    @pytest.mark.parametrize("length_m", [-1.0, -1500.0, math.nan, math.inf, -math.inf])
    def test_a_length_that_cannot_carry_a_rate_has_no_rate(self, length_m):
        assert fn.furniture_per_km(nodes=[SIGNAL], length_m=length_m) is None

    def test_a_one_metre_way_still_produces_its_arithmetic_rather_than_a_special_case(self):
        """Short-way outliers are a rank-normalisation problem (T-0163), not a reason to lie here."""
        # 1 / (1 / 1000) = 1 / 0.001 = 1000.0
        assert fn.furniture_per_km(nodes=[SIGNAL], length_m=1.0) == 1000.0

    def test_metres_per_km_is_a_thousand(self):
        assert fn.METRES_PER_KM == 1000.0
