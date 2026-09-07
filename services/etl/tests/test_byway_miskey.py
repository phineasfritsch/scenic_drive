"""Caltrans FID 181: the row keyed to the wrong route, and the real ways under it.

FID 181 is `CO=SCR RTE=221 Status=E` over 27.9 km of State Route 236 - Big Basin Way, through Big Basin
Redwoods State Park. The row HAS a route key, so `byways.problems`'s keyless check never fires on it, and
the key rejects every way along its own corridor. That is the failure the route key was always going to
have and nothing in the first two rounds of this task could see.

The fixture is the real Caltrans line and real OSM ways: `tests/fixtures/byway_miskey_fixture.json`. The
constructed cases for the same machinery are in `test_byway_route_key.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from etl import byway_route_key as rk
from etl import byways as bw
from etl import snap

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "byway_miskey_fixture.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def byway_entries():
    return [{"name": e["name"], "status": e["status"], "source": e["source"], "routes": set(e["routes"]),
             "geometry": [tuple(p) for p in e["geometry"]]} for e in load()["byway"]]


def fixture_ways(role: str | None = None):
    return [{"way_id": w["way_id"], "name": w["name"], "highway": w["highway"], "ref": w["ref"],
             "role": w["role"], "osm_pull": w.get("osm_pull"), "geometry": [tuple(p) for p in w["geometry"]]}
            for w in load()["ways"] if role is None or w["role"] == role]


class TestTheFixtureItself:
    def test_it_records_its_sources_and_the_row_it_is_about(self):
        doc = load()
        assert "Caltrans" in doc["source"] and "CA-OpenData" in doc["licence"] and "ODbL" in doc["licence"]
        assert doc["byway_url"].startswith("https://services1.arcgis.com/")
        assert doc["caltrans_features_in_pull"] == 273
        assert doc["caltrans_fid"] == 181
        assert doc["caltrans_properties"]["RTE"] == "221"
        assert doc["caltrans_properties"]["CO"] == "SCR"
        assert doc["caltrans_properties"]["Status"] == bw.ELIGIBLE

    def test_the_row_says_221_and_there_is_no_row_for_the_route_it_really_is(self):
        """The confirmation that this is a Caltrans error and not an OSM one: 236 appears nowhere in the
        273-row pull, though the row's own LOCATION names SR 9 at both ends of what is SR 236."""
        doc = load()
        assert doc["rte_rows_for_236_in_the_pull"] == 0
        assert doc["the_route_this_actually_is"] == "236"
        assert "17.70" in doc["caltrans_properties"]["DYNSEGPM"]

    def test_it_was_measured_at_the_constants_this_module_still_uses(self):
        doc = load()
        assert doc["snap_tolerance_m"] == snap.SNAP_TOLERANCE_M
        assert doc["min_overlap_fraction"] == snap.MIN_OVERLAP_FRACTION

    def test_the_corridor_is_inside_the_region_this_milestone_actually_builds(self):
        """The claim that a wrong key costs M2 a real corridor, rather than costing some other part of the
        state a hypothetical one. Santa Cruz is not one of the nine ABAG counties but the sfbay bbox
        deliberately reaches past it, so this row IS in the extract."""
        box = json.loads((FIXTURE.parents[2] / "regions" / "sfbay" / "region.json")
                         .read_text(encoding="utf-8"))["bbox"]
        pts = [p for e in byway_entries() for p in e["geometry"]]
        assert pts
        for lat, lon in pts:
            assert box["min_lat"] <= lat <= box["max_lat"], lat
            assert box["min_lon"] <= lon <= box["max_lon"], lon

    def test_the_census_the_re_key_argument_rests_on_is_carried_with_the_fixture(self):
        """`byway_route_key`'s case for re-keying rather than falling back to geometry is a claim about
        the WHOLE corridor - 25.4 km of trail, service road and residential grid also clears the gate - and
        the fixture carries only a sample of it. The census the paragraph quotes travels here so it is data
        somebody can check, not a number in a comment that nothing can contradict."""
        c = load()["census"]
        assert c["ways_within_150m_of_the_corridor"] > c["ways_clearing_the_overlap_gate"] > 100
        assert c["km_clearing_the_gate_that_claim_the_source_key_221"] == 0.0
        by_class = c["km_clearing_the_gate_by_class"]
        assert by_class["tertiary"] == pytest.approx(c["km_clearing_the_gate_reffed_CA_236"], abs=0.05)
        assert sum(v for k, v in by_class.items() if k != "tertiary") > 20.0, by_class
        votes = c["reffed_votes_m"]
        assert max(votes, key=votes.get) == "236"
        assert votes["236"] / sum(votes.values()) >= rk.MIN_CONSENSUS_SHARE

    def test_both_osm_pulls_are_recorded_and_every_way_says_which_one_it_came_from(self):
        """Two pulls from different mirrors six weeks of OSM apart. Mixed provenance is fine; mixed
        provenance nobody can see is not."""
        doc = load()
        assert set(doc["osm_pulls"]) == {"a", "b"}
        for pull in doc["osm_pulls"].values():
            assert "overpass" in pull["source"].lower() and pull["query"]
        assert {w["osm_pull"] for w in doc["ways"]} == {"a", "b"}

    def test_the_refs_the_whole_finding_rests_on_are_really_there(self):
        for w in fixture_ways("the_corridor_itself"):
            assert w["ref"] == "CA 236" and w["name"] == "Big Basin Way", w["way_id"]
        for w in fixture_ways("not_the_road"):
            assert not w["ref"], w["way_id"]
        assert {w["ref"] for w in fixture_ways("another_route")} == {"CA 9"}


class TestTheRealMisKeyedCorridor:
    def test_the_key_caltrans_gave_it_matches_none_of_its_own_road(self):
        """27.9 km of eligible byway scoring nothing, and the row HAS a key, so nothing reported it."""
        entries = byway_entries()
        assert all(e["routes"] == {"221"} for e in entries)
        corridor = fixture_ways("the_corridor_itself")
        assert sum(snap.length_m(w["geometry"]) for w in corridor) > 25000
        for w in corridor:
            assert max(snap.overlap_fraction(w["geometry"], e["geometry"]) for e in entries) \
                >= bw.MIN_OVERLAP_FRACTION, w["way_id"]
            assert bw.match(w["geometry"], entries, way_ref=w["ref"]) is None, w["way_id"]
            assert bw.bonus_for(w["geometry"], entries, way_ref=w["ref"],
                                way_class=w["highway"]) == 0.0, w["way_id"]

    def test_the_corridor_names_the_route_the_row_should_have_carried(self):
        claimed = {}
        for entry in byway_entries():
            per_part = rk.claimed_lengths(entry, fixture_ways())
            assert max(per_part, key=per_part.get) == "236", per_part
            for number, metres in per_part.items():
                claimed[number] = claimed.get(number, 0.0) + metres
        assert set(claimed) == {"236", "9"}, claimed
        assert claimed["236"] > 25000, claimed
        assert claimed["236"] / sum(claimed.values()) > rk.MIN_CONSENSUS_SHARE

    def test_reconcile_re_keys_it_and_the_corridor_scores_again(self):
        fixed = rk.reconcile(byway_entries(), fixture_ways())
        assert [e[bw.KEY_VERDICT] for e in fixed] == [bw.KEY_REKEYED] * len(fixed)
        assert all(e["routes"] == {"236"} and e["key_was"] == ["221"] for e in fixed)
        recovered = 0.0
        for w in fixture_ways("the_corridor_itself"):
            bonus = bw.bonus_for(w["geometry"], fixed, way_ref=w["ref"], way_class=w["highway"])
            assert bonus == bw.ELIGIBLE_BONUS, w["way_id"]
            recovered += snap.length_m(w["geometry"])
        assert recovered == pytest.approx(28143, abs=200), recovered

    def test_the_repair_does_not_hand_the_bonus_to_everything_nearby(self):
        """Why the fix is a re-key and not a fall-back to geometry. Every way here clears the overlap gate
        against the real Caltrans line and none of them is the byway: the 7.7 km Skyline-to-the-Sea Trail
        and three more park trails, an unnamed park service road, Fallen Leaf Drive off Boulder Creek's
        residential grid, and a track. Geometry alone would score all of them; a corridor keyed to 236
        scores none.

        The class SPREAD is the assertion that matters, not the count. When these were four `path` ways a
        gate on highway class - reject path/footway/track, which is a plausible-looking substitute for the
        route key - passed this test while letting a residential street inherit an eligible designation.
        The service road and Fallen Leaf Drive are here so that substitution goes red."""
        fixed = rk.reconcile(byway_entries(), fixture_ways())
        impostors = fixture_ways("not_the_road")
        assert len(impostors) >= 4
        assert {w["highway"] for w in impostors} >= {"path", "service", "residential"}, \
            sorted({w["highway"] for w in impostors})
        for w in impostors:
            assert max(snap.overlap_fraction(w["geometry"], e["geometry"]) for e in fixed) \
                >= bw.MIN_OVERLAP_FRACTION, w["way_id"]
            assert bw.bonus_for(w["geometry"], fixed, way_ref=w["ref"],
                                way_class=w["highway"]) == 0.0, w["way_id"]

    def test_a_way_on_a_different_numbered_route_is_still_refused(self):
        """CA 9 crosses this corridor in Boulder Creek. The re-key must not turn the gate off."""
        fixed = rk.reconcile(byway_entries(), fixture_ways())
        for w in fixture_ways("another_route"):
            assert bw.bonus_for(w["geometry"], fixed, way_ref=w["ref"], way_class=w["highway"]) == 0.0
