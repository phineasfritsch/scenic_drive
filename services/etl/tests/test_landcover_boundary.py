"""The roads that were NOT picked to separate cleanly.

The four ways in `landcover_fixture.json` are archetypes chosen to sit far apart, and agent/reviewer-32
was right that they therefore say nothing about the general case: sampled against the same pinned tiles
with the same shipped code, an ordinary San Ramon cul-de-sac satisfied `is_wooded` and `is_built_up` at
the same time. This fixture is that counterexample and its neighbours, plus an oak-savanna road, an
oak-woodland road half a mile from it, a Delta cropland road, and the one archetype whose verdict moved
when only the sample grid moved.

Every way is recorded at four grid phases half a step apart. The land underneath is identical at every
phase, so anything that moves between them is a sampling artefact and nothing else - which makes this
file the measurement of the aliasing, not an opinion about it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from etl import landcover as lc

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "landcover_boundary_fixture.json"

# Grid phase must not move canopy by more than this. Measured, not chosen: at the 50 m step this fixture
# was first recorded at, the worst way moved 0.2759 - which at canopy's 0.24 weight in E is 0.066 of the
# score coming from nowhere but where the grid landed. The bound has to sit below that and above what the
# shipped step actually achieves.
MAX_PHASE_SPREAD = 0.10


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def by_key():
    return {w["key"]: w for w in load()["ways"]}


def verdict(summary: dict) -> str:
    wooded, built = lc.is_wooded(summary), lc.is_built_up(summary)
    if wooded and built:
        return "BOTH"
    return "WOODED" if wooded else ("BUILT_UP" if built else "neither")


class TestTheFixtureItself:
    def test_it_records_its_source_and_its_licence(self):
        doc = load()
        assert "WorldCover" in doc["source"]
        assert "CC-BY-4.0" in doc["licence"], "an attribution licence with no attribution recorded"

    def test_it_was_recorded_at_the_geometry_the_code_actually_uses(self):
        """A fixture recorded at a different buffer or step measures a different question. This is also
        what pins BUFFER_STEP_M: coarsen the sampler and this file no longer describes it."""
        doc = load()
        assert doc["buffer_m"] == lc.BUFFER_M
        assert doc["buffer_step_m"] == lc.BUFFER_STEP_M

    def test_every_way_is_recorded_at_more_than_one_phase(self):
        """One phase cannot show that phase does not matter."""
        for way in load()["ways"]:
            assert len(way["codes_by_phase"]) >= 4, way["key"]
            assert len({len(c) for c in way["codes_by_phase"]}) == 1, way["key"]

    def test_no_unknown_class_codes_anywhere(self):
        for way in load()["ways"]:
            for codes in way["codes_by_phase"]:
                assert lc.unknown_codes(codes) == set(), way["key"]

    def test_these_are_not_the_archetypes_again(self):
        """The point of this file is roads that were not curated. If it ends up holding the same ways as
        the archetype fixture it has stopped being evidence about anything."""
        archetypes = json.loads(
            (FIXTURE.parent / "landcover_fixture.json").read_text(encoding="utf-8"))
        overlap = {w["way_id"] for w in load()["ways"]} & {w["way_id"] for w in archetypes["ways"]}
        assert len(overlap) <= 1, overlap


class TestNoRoadIsEverBoth:
    def test_not_at_any_phase_of_any_way(self):
        """The invariant `test_no_road_is_both` asserts, checked against roads that were not chosen to
        satisfy it. This is the test that was red: canyon_creek read canopy 0.5254 / impervious 0.4746 at
        one phase, clearing both independent thresholds at once."""
        for way in load()["ways"]:
            for i, codes in enumerate(way["codes_by_phase"]):
                assert verdict(lc.fractions(codes)) != "BOTH", (way["key"], i)

    def test_the_leafy_suburb_is_neither_a_redwood_road_nor_a_strip_mall(self):
        """Canyon Creek is half tree canopy and half buildings, and both halves are real. What it is not
        is Skyline; a rule that calls it wooded has stopped meaning anything."""
        way = by_key()["canyon_creek"]
        for i, codes in enumerate(way["codes_by_phase"]):
            s = lc.fractions(codes)
            assert verdict(s) == "neither", (i, s["canopy"], s["impervious"])
            assert s["canopy"] > 0.4 and s["impervious"] > 0.4, s


class TestGridPhaseDoesNotDecideTheAnswer:
    def test_canopy_moves_less_than_the_bound_when_only_the_grid_moves(self):
        for way in load()["ways"]:
            canopies = [lc.fractions(c)["canopy"] for c in way["codes_by_phase"]]
            spread = max(canopies) - min(canopies)
            assert spread <= MAX_PHASE_SPREAD, (way["key"], spread, canopies)

    def test_impervious_moves_less_than_the_bound_too(self):
        for way in load()["ways"]:
            imps = [lc.fractions(c)["impervious"] for c in way["codes_by_phase"]]
            assert max(imps) - min(imps) <= MAX_PHASE_SPREAD, (way["key"], imps)

    def test_the_recorded_spreads_are_what_the_recorded_codes_give(self):
        """Stops the spreads being edited to fit the bound without the codes moving with them."""
        for way in load()["ways"]:
            canopies = [lc.fractions(c)["canopy"] for c in way["codes_by_phase"]]
            imps = [lc.fractions(c)["impervious"] for c in way["codes_by_phase"]]
            assert max(canopies) - min(canopies) == pytest.approx(
                way["canopy_phase_spread"], abs=1e-4), way["key"]
            assert max(imps) - min(imps) == pytest.approx(
                way["impervious_phase_spread"], abs=1e-4), way["key"]

    def test_a_curated_archetype_keeps_its_verdict_at_every_phase(self):
        """alviso_flat2 is in the archetype fixture as BUILT_UP. At the 50 m step it read BUILT_UP at two
        phases and `neither` at the other two, with nothing but the grid moved - the archetype fixture's
        own recorded classification was a coin-flip on sampling."""
        way = by_key()["alviso_flat2"]
        verdicts = {verdict(lc.fractions(c)) for c in way["codes_by_phase"]}
        assert verdicts == {"BUILT_UP"}, verdicts

    def test_the_verdicts_recorded_for_every_phase_still_recompute(self):
        for way in load()["ways"]:
            got = [verdict(lc.fractions(c)) for c in way["codes_by_phase"]]
            assert got == way["verdicts_by_phase"], way["key"]


class TestTheClassMapping:
    def test_oak_savanna_is_not_woodland_and_the_raster_says_so(self):
        """Mines Road and Morgan Territory Road are half a mile apart in the same range. One is savanna,
        one is oak woodland, and the difference is the whole question of what `canopy` means. Folding
        grassland into canopy would put Mines Road at ~1.0 - above Skyline - which is why it is not."""
        mines = lc.fractions(by_key()["mines_road"]["codes_by_phase"][0])
        morgan = lc.fractions(by_key()["morgan_territory"]["codes_by_phase"][0])
        assert morgan["canopy"] > mines["canopy"] + 0.15, (morgan["canopy"], mines["canopy"])
        assert lc.is_wooded(morgan)
        assert not lc.is_wooded(mines)
        assert mines["canopy"] + mines["grassland"] > 0.9, mines

    def test_the_savanna_road_is_open_land_not_nothing(self):
        """`neither wooded nor built up` used to be the end of the sentence for Mines Road. Grassland is
        not canopy, but it is not absence either, and the term that names it has to exist for T-0029 to
        be able to weigh it."""
        mines = lc.fractions(by_key()["mines_road"]["codes_by_phase"][0])
        assert mines["open_land"] > 0.5, mines
        assert mines["impervious"] < 0.05, mines

    def test_the_delta_road_reports_the_cropland_it_is_covered_in(self):
        """Vorden Road's dominant class is cropland, which fed no term at all: the score's only reading of
        a Delta levee road was `not trees, not buildings`."""
        vorden = lc.fractions(by_key()["vorden_road"]["codes_by_phase"][0])
        assert vorden["cropland"] > 0.3, vorden
        assert vorden["open_land"] > vorden["canopy"] + vorden["impervious"], vorden

    def test_every_way_here_is_fully_accounted_for(self):
        """canopy, impervious, water and open_land partition the classes, so a road can never be mostly
        something the score has no name for."""
        for way in load()["ways"]:
            s = lc.fractions(way["codes_by_phase"][0])
            total = s["canopy"] + s["impervious"] + s["water"] + s["open_land"]
            assert total == pytest.approx(1.0), (way["key"], total)
