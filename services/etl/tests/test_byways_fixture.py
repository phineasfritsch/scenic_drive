"""The frontage-road and divided-highway cases, against REAL Caltrans lines and REAL OSM ways.

  RED: a real frontage road running beside a real designated corridor must not inherit its designation,
       while the real second carriageway of the corridor itself must keep it. The synthetic tests in
       test_byways.py cannot decide this: they put the frontage road 100 m out, and the real one is closer
       to the byway than the freeway's own other carriageway is.

Everything here comes from the pinned Caltrans pull and from Overpass; nothing in the fixture was typed by
hand. The byway lines are clipped to a peninsula window, and the generator verified that clipping leaves
every `overlap_fraction` in this file bit-identical to the value against the unclipped line.

The roles, and the real objects behind them:
  divided_carriageway   I-280's two carriageways ("Junipero Serra Freeway", ref `I 280;CA 35`)
  frontage_road         Junipero Serra Boulevard, no ref - the frontage road beside I-280
  parallel_other_route  Skyline Boulevard, ref `CA 35`, where it runs right alongside I-280
  byway_itself          Skyline Boulevard, ref `CA 35`, on its own designated corridor
  cross_street          Kings Mountain Road, meeting Skyline at a shared node
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

from etl import byways as bw

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "byway_fixture.json"
SM280 = "caltrans_sm_280"
SM35 = "caltrans_sm_35"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def entries(group: str, keyed: bool = True) -> list[dict]:
    """The byway group as `match` entries. `keyed=False` drops the route key, which is how this module
    behaved before the key existed and is what the frontage-road tests compare against."""
    return [{"name": e["name"], "status": e["status"], "source": e["source"],
             "routes": set(e["routes"]) if keyed else set(),
             "geometry": [tuple(p) for p in e["geometry"]]}
            for e in load()["byways"][group]]


def ways(role: str) -> list[dict]:
    return [w for w in load()["ways"] if w["role"] == role]


def geom(way: dict) -> list[tuple[float, float]]:
    return [tuple(p) for p in way["geometry"]]


def best_overlap(way: dict, group: str) -> float:
    return max((bw.overlap_fraction(geom(way), e["geometry"]) for e in entries(group)), default=0.0)


class TestTheFixtureItself:
    def test_it_records_its_sources_and_their_licences(self):
        doc = load()
        assert "Caltrans" in doc["source"]
        assert "CA-OpenData" in doc["licence"] and "ODbL" in doc["licence"], doc["licence"]
        assert doc["byway_url"].startswith("https://services1.arcgis.com/")
        assert doc["caltrans_features_in_pull"] == 273

    def test_it_was_measured_at_the_constants_this_module_still_uses(self):
        """Every property below was measured at these two numbers. If either moves, the findings have to be
        re-measured rather than assumed to survive."""
        doc = load()
        assert doc["snap_tolerance_m"] == bw.SNAP_TOLERANCE_M
        assert doc["min_overlap_fraction"] == bw.MIN_OVERLAP_FRACTION

    def test_every_role_is_present_and_has_real_geometry(self):
        for role in ("divided_carriageway", "frontage_road", "parallel_other_route",
                     "byway_itself", "cross_street"):
            got = ways(role)
            assert got, role
            for w in got:
                assert len(w["geometry"]) >= 20, (role, w["way_id"])

    def test_both_byway_groups_carry_their_route_key(self):
        assert all(e["routes"] == {"280"} for e in entries(SM280))
        assert all(e["routes"] == {"35"} for e in entries(SM35))


class TestDistanceCannotSeparateThem:
    def test_a_frontage_road_is_no_further_off_than_a_second_carriageway(self):
        """The measurement the 60 m tolerance was never checked against. I-280's two carriageways sit
        25.2-30.5 m apart (median 27.7); Junipero Serra Boulevard sits 29.3-97.1 m from the Caltrans SM-280
        line (median 52.0). Those ranges OVERLAP, so no value of SNAP_TOLERANCE_M admits every second
        carriageway and excludes every frontage road. The tolerance is not the lever - the route key is."""
        a, b = [geom(w) for w in ways("divided_carriageway")[:2]]
        carriageway = sorted(bw.distance_to_line_m(p, b) for p in a)
        lines = [e["geometry"] for e in entries(SM280)]
        frontage = sorted(min(bw.distance_to_line_m(p, L) for L in lines)
                          for w in ways("frontage_road") for p in geom(w))
        assert min(frontage) < max(carriageway[:len(carriageway) * 3 // 4]), (min(frontage), carriageway[0])
        assert statistics.median(carriageway) < bw.SNAP_TOLERANCE_M
        assert min(frontage) < bw.SNAP_TOLERANCE_M


class TestTheCasesTheDocstringClaims:
    def test_a_second_carriageway_keeps_the_corridors_designation(self):
        for w in ways("divided_carriageway"):
            assert best_overlap(w, SM280) > 0.9, w["way_id"]
            m = bw.match(geom(w), entries(SM280), way_ref=w["ref"])
            assert m is not None and m["status"] == bw.DESIGNATED, (w["way_id"], m)

    def test_the_frontage_road_matches_on_geometry_alone(self):
        """The half that makes the next test load-bearing. Without this, 'the frontage road does not match'
        would be satisfied by a way that was never near the corridor in the first place."""
        for w in ways("frontage_road"):
            frac = best_overlap(w, SM280)
            assert frac >= bw.MIN_OVERLAP_FRACTION, (w["way_id"], frac)
            assert bw.match(geom(w), entries(SM280, keyed=False), way_ref=w["ref"]) is not None, w["way_id"]

    def test_the_route_key_stops_the_frontage_road_inheriting_the_designation(self):
        for w in ways("frontage_road"):
            assert not w["ref"], w["way_id"]
            assert bw.match(geom(w), entries(SM280), way_ref=w["ref"]) is None, w["way_id"]
            assert bw.bonus_for(geom(w), entries(SM280), way_ref=w["ref"],
                                way_class=w["highway"]) == 0.0, w["way_id"]

    def test_a_road_on_another_route_does_not_inherit_this_one(self):
        """Skyline Boulevard where it runs alongside I-280: overlap 1.0 against the SM-280 corridor, and it
        is not I-280. Its own corridor still finds it, which is what stops this from being a blunt gate."""
        for w in ways("parallel_other_route"):
            assert best_overlap(w, SM280) >= bw.MIN_OVERLAP_FRACTION, w["way_id"]
            assert bw.match(geom(w), entries(SM280, keyed=False), way_ref=w["ref"]) is not None
            assert bw.match(geom(w), entries(SM280), way_ref=w["ref"]) is None, w["way_id"]
            assert bw.match(geom(w), entries(SM35), way_ref=w["ref"])["status"] == bw.DESIGNATED

    def test_the_byway_itself_still_matches_with_the_key_on(self):
        for w in ways("byway_itself"):
            m = bw.match(geom(w), entries(SM35), way_ref=w["ref"])
            assert m is not None and m["status"] == bw.DESIGNATED, (w["way_id"], m)
            assert w["highway"] not in bw.SCENIC_ZERO_CLASSES, w["way_id"]
            assert bw.bonus_for(geom(w), entries(SM35), way_ref=w["ref"],
                                way_class=w["highway"]) == bw.DESIGNATED_BONUS

    def test_a_real_interstate_on_its_own_designated_corridor_still_scores_nothing(self):
        """The gate the plan's invariant requires, against real data rather than a constructed way. These
        are I-280's actual carriageways on Caltrans's actual SM RTE=280 corridor: `highway=motorway`,
        `ref=I 280;CA 35`, overlap > 0.9, status OD. S&H 263.3 lists Interstates as eligible and the pinned
        pull carries I-80/280/580/680 rows, so this is the normal case and not an edge one."""
        got = ways("divided_carriageway")
        assert got
        for w in got:
            assert w["highway"] in bw.SCENIC_ZERO_CLASSES, (w["way_id"], w["highway"])
            assert bw.match(geom(w), entries(SM280), way_ref=w["ref"])["status"] == bw.DESIGNATED
            assert bw.bonus_for(geom(w), entries(SM280), way_ref=w["ref"],
                                way_class=w["highway"]) == 0.0, w["way_id"]

    def test_a_cross_street_at_a_shared_node_does_not_match(self):
        """Kings Mountain Road meets Skyline at one node and goes elsewhere. 7 km of way against 0.034 of
        overlap - the minimum-overlap gate, not the route key, is what rejects this one."""
        for w in ways("cross_street"):
            frac = best_overlap(w, SM35)
            assert frac < bw.MIN_OVERLAP_FRACTION, (w["way_id"], frac)
            assert bw.match(geom(w), entries(SM35), way_ref=w["ref"]) is None

    def test_the_refs_the_key_depends_on_are_really_there(self):
        """If OSM stopped tagging these refs the key would reject real byway segments, so what it reads is
        asserted rather than assumed."""
        for w in ways("divided_carriageway"):
            assert bw.route_numbers(w["ref"]) == {"280", "35"}, w["ref"]
        for w in ways("byway_itself") + ways("parallel_other_route"):
            assert bw.route_numbers(w["ref"]) == {"35"}, w["ref"]
        for w in ways("frontage_road") + ways("cross_street"):
            assert bw.route_numbers(w["ref"]) == set(), w["ref"]
