"""The two properties T-0026's brief names, against real roads and real 3DEP elevation.

  RED: a known-flat fixture (Alviso / bay margin) must score near 0 gain;
       a known-steep one (Old La Honda) must not.

Both the geometry and the sampled profile are committed, so this runs with no GDAL, no rasters and no
container - but neither was invented here. The geometry is the mappers' own nodes out of the Bay Area
extract; the elevations came out of the pinned tiles.

Why that matters, from this task's own log: the first attempt used hand-typed polylines, seven points for a
5.3 km mountain road. Straight lines between points that far apart cut across canyons the road contours
around, and Old La Honda scored a 44% maximum grade while Skyline scored 59%. No drivable road is remotely
that steep. The elevations were real; they were not elevations of the road. With the mappers' geometry the
same roads score 13.65% and 10.47%, which is what those roads are.

(That pair read 14.6% and 8.3% until commit e0166e7 re-recorded the fixture with 3x3 smoothing, and this
docstring went on quoting the old numbers - caught by agent/reviewer-31. They are prose and nothing asserts
on them, which is precisely how they drifted; what holds the real values is
`TestTheRecordedSummariesStillHold`, which recomputes rather than reads. A comment stating numbers the file
no longer produces is the beginning of a comment nobody trusts.)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from etl import terrain as tr

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "terrain_fixture.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def by_key():
    return {w["key"]: w for w in load()["ways"]}


def summarise(way):
    return tr.summarise([tuple(c) for c in way["coords"]], way["profile"])


class TestTheFixtureItself:
    def test_it_records_where_both_halves_came_from(self):
        doc = load()
        assert "3DEP" in doc["dem_source"]
        assert doc["osm_source"]
        assert len(doc["ways"]) >= 4

    def test_every_way_has_real_mapper_geometry_not_a_typed_line(self):
        """A 5 km road with 7 nodes is a straight line across canyons. The mappers' nodes are what make the
        profile follow the road, and that is the difference between a 14% grade and a 44% one."""
        for way in load()["ways"]:
            length = tr.profile_length_m([tuple(c) for c in way["coords"]])
            if length > 1000:
                spacing = length / (len(way["coords"]) - 1)
                assert spacing < 120, f"{way['key']}: {spacing:.0f} m between nodes is a typed line"

    def test_every_way_is_fully_covered_by_the_tiles(self):
        for way in load()["ways"]:
            assert summarise(way)["coverage"] == 1.0, way["key"]


class TestTheNamedProperties:
    def test_the_flat_bay_margin_roads_score_near_zero_gain(self):
        for key in ("alviso_flat", "alviso_flat2"):
            s = summarise(by_key()[key])
            assert tr.is_flat(s), f"{key} scored {s['gain_per_km']} m/km"
            assert s["gain_m"] < 2.0, f"{key} gained {s['gain_m']} m over {s['length_m']} m of bay margin"

    def test_old_la_honda_does_not_read_as_flat(self):
        s = summarise(by_key()["old_la_honda"])
        assert tr.is_steep(s), s
        assert not tr.is_flat(s), s

    def test_the_two_are_far_apart_not_marginally_apart(self):
        """A threshold that only just separates them is a threshold that will misclassify the next road."""
        flat = summarise(by_key()["alviso_flat2"])
        steep = summarise(by_key()["old_la_honda"])
        assert steep["gain_per_km"] > flat["gain_per_km"] * 20

    def test_skyline_reads_as_scenic_terrain_too(self):
        """The product's own reference road. If Skyline does not score terrain, nothing will."""
        s = summarise(by_key()["skyline"])
        assert tr.is_steep(s), s
        assert s["relief_m"] > 30


class TestNoRoadScoresAnImpossibleGrade:
    def test_every_fixture_way_passes_the_sanity_check(self):
        for way in load()["ways"]:
            assert tr.sanity_problems(summarise(way)) == [], way["key"]

    @pytest.mark.parametrize("key,ceiling", [("old_la_honda", 20.0), ("skyline", 15.0)])
    def test_the_mountain_roads_have_plausible_maximum_grades(self, key, ceiling):
        """Old La Honda averages about 8% and tops out near 12-15%. The hand-typed version of this fixture
        scored 44%, which is the number that revealed the geometry was wrong rather than the arithmetic."""
        s = summarise(by_key()[key])
        assert s["max_grade_pct"] < ceiling, f"{key} at {s['max_grade_pct']}% is not a road"


class TestTheRecordedSummariesStillHold:
    def test_recomputing_reproduces_what_was_recorded(self):
        """The committed summary is what the committed profile produces. If someone changes the arithmetic,
        this says so rather than letting the fixture drift into agreement with the new behaviour."""
        for way in load()["ways"]:
            assert summarise(way) == way["recorded_summary"], way["key"]
