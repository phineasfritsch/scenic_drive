"""The roads that were NOT picked to separate cleanly.

The four ways in `landcover_fixture.json` are archetypes chosen to sit far apart, and agent/reviewer-32
was right that they therefore say nothing about the general case: sampled against the same pinned tiles
with the same shipped code, an ordinary San Ramon cul-de-sac satisfied `is_wooded` and `is_built_up` at
the same time. This fixture is that counterexample and its neighbours, plus an oak-savanna road, an
oak-woodland road half a mile from it, a Delta cropland road, the one archetype whose verdict moved
when only the sample grid moved, and two rural roads that sit just under the built-up cutoff - the
anchor that round 2 showed the 0.4 did not have.

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

    def test_the_recorded_codes_are_as_many_as_the_recorded_geometry_asks_for(self):
        """`sampled_at` and `node_stride` were read by nothing, so the file could have been re-recorded
        off different nodes and stayed green. This does not prove the coordinates are the way's real OSM
        nodes - all eleven were checked against live `api.openstreetmap.org` geometry at their declared
        stride, by agent/reviewer-32 for the first nine and by me for all eleven - but it does tie the
        three recorded things to each other: change the number of centres, the buffer or the step, and the
        file stops describing itself."""
        for way in load()["ways"]:
            expected = sum(len(lc.buffer_points(lat, lon)) for lat, lon in way["sampled_at"])
            assert expected > 0, way["key"]
            for i, codes in enumerate(way["codes_by_phase"]):
                assert len(codes) == expected, (way["key"], i, len(codes), expected)

    def test_the_stride_and_the_node_count_account_for_every_centre(self):
        """`node_stride` was pure decoration until this: my own mutant N10 doubled murphy_avenue's stride
        from 9 to 18 and nothing went red, because a list of coordinates does not know how it was strided.
        With the way's OSM node count recorded beside it, `sampled_at` has to be exactly as long as
        striding that many nodes produces, so neither number can be edited on its own."""
        for way in load()["ways"]:
            wanted = len(range(0, way["node_count"], way["node_stride"])) or 1
            assert len(way["sampled_at"]) == wanted, (
                way["key"], way["node_count"], way["node_stride"], len(way["sampled_at"]))

    def test_the_node_count_is_a_list_of_real_node_ids_and_not_a_number(self):
        """Two integers cannot check each other, which my own mutant N15 proved: editing `node_count`
        58 -> 116 and `node_stride` 9 -> 18 together keeps the centre count at 7, so the test above stayed
        green on a fixture that had stopped describing a real way. `node_ids` is the anchor - OSM node ids
        are data somebody else published, so faking `node_count` now means inventing 58 ids that anyone
        can check against api.openstreetmap.org, which is the standard `sampled_at` is already held to."""
        for way in load()["ways"]:
            ids = way["node_ids"]
            assert len(ids) == way["node_count"], (way["key"], len(ids), way["node_count"])
            assert len(set(ids)) >= 2, way["key"]
            assert all(isinstance(i, int) and i > 0 for i in ids), way["key"]
            assert len(way["sampled_at"]) == len(ids[::way["node_stride"]]), (
                way["key"], len(way["sampled_at"]), way["node_stride"], len(ids))

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


class TestWhatKeepsARuralRoadOutOfBuiltUp:
    """The real-data anchor under the 0.4 built-up cutoff. There was none, and the three mutants
    `0.4 -> 0.39 / 0.35 / 0.26` all lived through a green suite because of it.

    How these two ways were found, because it matters that they were not picked for their answer: neither
    reviewer-32's 69 random sfbay ways nor my own draw contained a road in the band, so the search ran the
    other way round. A 691x691 lattice over the region bbox (477,481 points, one WorldCover code each)
    found 2,226 cells that are moderately built, nearly treeless and mostly open land; OSM had 155 roads
    at nine of those centres; 24 of the 155 sit in `0.26 <= impervious < 0.40` with the dominance ratio
    already satisfied at all four phases. `murphy_avenue` is the closest of the 24 whose reading does not
    move with the sample grid (0.3818-0.3931, spread 0.0113); Yateley Court, way 1102758612, gets nearer
    at one phase (0.3963) but swings 0.0775 across the four, which is most of the 0.10 bound this file
    enforces elsewhere and makes it a worse thing to hang a cutoff on. `san_martin` has room to spare
    (0.2970-0.3164), so the anchor does not rest on one thin margin.
    """

    KEYS = ("murphy_avenue", "san_martin")

    def test_the_ratio_does_not_disqualify_them_so_only_the_cutoff_can(self):
        """If the dominance rule already kept these roads out of BUILT_UP they would pin nothing."""
        for key in self.KEYS:
            for i, codes in enumerate(by_key()[key]["codes_by_phase"]):
                s = lc.fractions(codes)
                assert s["impervious"] >= lc.DOMINANCE_RATIO * s["canopy"], (key, i, s)

    def test_a_road_that_is_mostly_open_land_is_not_a_strip_mall_arterial(self):
        """Murphy Avenue runs through San Martin and East San Martin Avenue past the fields beside it:
        about a third of each buffer is built, more than half of it is open land, and the trees are
        incidental. Calling either a strip-mall arterial is what `0.4 -> 0.26` does."""
        for key in self.KEYS:
            for i, codes in enumerate(by_key()[key]["codes_by_phase"]):
                s = lc.fractions(codes)
                assert s["open_land"] > s["impervious"], (key, i, s)
                assert not lc.is_built_up(s), (key, i, s["impervious"], s["canopy"])

    def test_how_close_the_anchor_gets_to_the_cutoff(self):
        """0.3931 against a cutoff of 0.4. Recorded rather than implied: this margin is the honest measure
        of how much judgement is in the number, and a road at 0.41 would be called built up on the
        strength of one percentage point of roof. It is also what makes `0.4 -> 0.39` go red - which is
        the whole reason a real road had to be found instead of another synthetic count."""
        imps = [lc.fractions(c)["impervious"] for c in by_key()["murphy_avenue"]["codes_by_phase"]]
        assert 0.39 <= max(imps) < 0.40, imps


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
