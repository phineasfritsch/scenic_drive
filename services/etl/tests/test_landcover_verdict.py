"""`is_wooded` / `is_built_up`: one verdict, and where its three numbers actually sit.

Moved here from test_landcover.py unchanged (the file was at 281 of its 300 lines and these are one
subject), with three edge pins added. The edges are the point: agent/reviewer-32's mutation run walked
`0.5 -> 0.49`, `0.4 -> 0.39/0.35/0.26` and `>= -> >` straight through a green suite, so the constants were
decorative. Two of them are pinned here by definition and one by a real road, in
test_landcover_boundary.py - the difference is stated, not blurred.
"""
from __future__ import annotations

import pytest

from etl import landcover as lc


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

    def test_exactly_the_ratio_is_enough(self):
        """`>=`, not `>`. The definitional edge the whole exclusivity proof stands on: at
        `canopy == ratio * impervious` the majority term is ahead by exactly the margin the rule asks for,
        and `>` would make the answer depend on a rounding bit. `SURVIVED M20 is_wooded ratio uses >
        instead of >=` was reviewer-32's - nothing sat on the edge."""
        assert lc.is_wooded({"canopy": 0.6, "impervious": 0.3})
        assert not lc.is_wooded({"canopy": 0.6, "impervious": 0.3 + 1e-9})
        assert lc.is_built_up({"impervious": 0.6, "canopy": 0.3})
        assert not lc.is_built_up({"impervious": 0.6, "canopy": 0.3 + 1e-9})

    def test_a_quarter_built_is_not_yet_a_strip_mall(self):
        """With the dominance rule in place, a road with no trees at all clears `impervious >= ratio *
        canopy` at any impervious above zero - so the 0.4 is the only thing between `some development` and
        `strip-mall arterial`."""
        s = lc.fractions([50] * 25 + [30] * 75)
        assert s["impervious"] == pytest.approx(0.25)
        assert not lc.is_built_up(s)
        assert lc.is_built_up(lc.fractions([50] * 45 + [30] * 55))

    def test_the_built_up_cutoff_is_at_four_tenths_and_not_a_hundredth_below(self):
        """The pin the last round claimed and did not have: `0.4 -> 0.26` and `0.4 -> 0.35` and
        `0.4 -> 0.39` all survived, because `test_a_quarter_built_is_not_yet_a_strip_mall` only reaches
        0.25. These counts are exact in binary64 (39/100 == 0.39), so this is the cutoff itself and not an
        approximation of it. What it does NOT do is say 0.4 is the right number - that is a judgement about
        how much development makes a road built up, and the real-data half of it is Murphy Avenue in
        test_landcover_boundary.py, which sits at 0.3931."""
        assert not lc.is_built_up(lc.fractions([50] * 39 + [30] * 61))
        assert lc.is_built_up(lc.fractions([50] * 40 + [30] * 60))

    def test_not_quite_half_trees_is_not_yet_wooded(self):
        """`wooded` means canopy is the majority of what you can see, and 0.5 is what majority means. That
        is a definition, not a fit - the fitting question, which of two real terms wins, is the ratio's."""
        assert not lc.is_wooded(lc.fractions([10] * 45 + [30] * 55))
        assert lc.is_wooded(lc.fractions([10] * 55 + [30] * 45))

    def test_the_wooded_cutoff_is_at_a_half_and_not_a_hundredth_below(self):
        """Same edge on the canopy side, where `0.5 -> 0.49` also survived. The real-data anchor here is
        Mines Road at canopy 0.4859, which is what kills `0.5 -> 0.46`; between 0.46 and 0.5 there is no
        road in the fixtures, so this closes the gap by definition."""
        assert not lc.is_wooded(lc.fractions([10] * 49 + [30] * 51))
        assert lc.is_wooded(lc.fractions([10] * 50 + [30] * 50))

    def test_a_tie_is_not_a_verdict(self):
        """A ratio of exactly 1 still lets both fire on an exact tie, and exact ties happen: a 29-sample
        buffer that lands 15/14 is one rounding away from 50/50."""
        s = {"canopy": 0.5, "impervious": 0.5}
        assert not (lc.is_wooded(s) and lc.is_built_up(s))
