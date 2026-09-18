"""The property T-0027's brief names, against real roads and real WorldCover.

  RED: a fixture through a known industrial area must score high impervious;
       a fixture on Skyline must score high canopy. Both from the raster, not hand-entered.

The codes are the raw class values sampled in a 150 m circular buffer around every eighth node of each way,
committed so the test needs neither GDAL nor the 92 MB of raster - while nothing in the file was typed by
hand. These are the same ways the terrain fixture uses, which is deliberate: the two layers have to agree
about which road is which before they are ever combined into a score.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from etl import landcover as lc

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "landcover_fixture.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def by_key():
    return {w["key"]: w for w in load()["ways"]}


class TestTheFixtureItself:
    def test_it_records_its_source_and_its_licence(self):
        doc = load()
        assert "WorldCover" in doc["source"]
        assert "CC-BY-4.0" in doc["licence"], "an attribution licence with no attribution recorded"
        assert doc["buffer_m"] == lc.BUFFER_M

    def test_every_way_has_real_samples(self):
        for way in load()["ways"]:
            assert len(way["codes"]) >= 50, way["key"]

    def test_no_unknown_class_codes_anywhere(self):
        """A wrong band or a non-WorldCover raster produces values outside the class set, which land in no
        bucket and make every fraction quietly zero."""
        for way in load()["ways"]:
            assert lc.unknown_codes(way["codes"]) == set(), way["key"]

    def test_the_buffer_is_denser_than_the_way_is_long(self):
        """A single sample per node would be a transect, not a buffer, and would miss the parking lot beside
        the road entirely."""
        for way in load()["ways"]:
            assert len(way["codes"]) > len(way["sampled_at"]) * 5, way["key"]


class TestTheNamedProperties:
    def test_skyline_scores_high_canopy(self):
        s = lc.fractions(by_key()["skyline"]["codes"])
        assert lc.is_wooded(s), s
        assert s["canopy"] > 0.7, s["canopy"]

    def test_old_la_honda_scores_high_canopy_too(self):
        s = lc.fractions(by_key()["old_la_honda"]["codes"])
        assert lc.is_wooded(s)
        assert s["canopy"] > 0.7

    def test_the_industrial_bay_margin_scores_high_impervious(self):
        for key in ("alviso_flat", "alviso_flat2"):
            s = lc.fractions(by_key()[key]["codes"])
            assert lc.is_built_up(s), (key, s)
            assert s["impervious"] > 0.4, (key, s["impervious"])

    def test_the_wooded_and_built_up_roads_are_far_apart(self):
        """A separation that only just clears the threshold is one that will misclassify the next road."""
        wooded = lc.fractions(by_key()["skyline"]["codes"])
        built = lc.fractions(by_key()["alviso_flat"]["codes"])
        assert wooded["canopy"] - built["canopy"] > 0.5
        assert built["impervious"] - wooded["impervious"] > 0.5

    def test_no_road_is_both(self):
        for way in load()["ways"]:
            s = lc.fractions(way["codes"])
            assert not (lc.is_wooded(s) and lc.is_built_up(s)), way["key"]

    def test_each_way_matches_the_classification_recorded_for_it(self):
        for way in load()["ways"]:
            s = lc.fractions(way["codes"])
            actual = "WOODED" if lc.is_wooded(s) else ("BUILT_UP" if lc.is_built_up(s) else "neither")
            assert actual == way["expected"], (way["key"], actual, s)


class TestAgreementWithTheTerrainFixture:
    def test_the_two_layers_describe_the_same_roads(self):
        """Both fixtures are built from the same ways. If the way ids ever diverge, one of them was rebuilt
        against a different extract and the score would be combining two different roads."""
        terrain = json.loads((FIXTURE.parent / "terrain_fixture.json").read_text(encoding="utf-8"))
        assert {w["way_id"] for w in terrain["ways"]} == {w["way_id"] for w in load()["ways"]}

    def test_the_wooded_roads_are_the_steep_ones_and_the_built_up_ones_are_flat(self):
        """Not a law of nature - it is true of the Bay Area, where the forest is on the hills and the
        industry is on the bay margin. If it stops being true the fixtures have drifted apart."""
        terrain = {w["key"]: w for w in json.loads(
            (FIXTURE.parent / "terrain_fixture.json").read_text(encoding="utf-8"))["ways"]}
        for key, way in by_key().items():
            wooded = lc.is_wooded(lc.fractions(way["codes"]))
            steep = terrain[key]["recorded_summary"]["gain_per_km"] >= 25.0
            assert wooded == steep, (key, wooded, steep)


class TestTheRecordedSummariesStillHold:
    def test_recomputing_reproduces_what_was_recorded(self):
        for way in load()["ways"]:
            recomputed = lc.fractions(way["codes"])
            for key in ("canopy", "impervious", "water"):
                assert recomputed[key] == pytest.approx(way["recorded_summary"][key], abs=1e-4), way["key"]