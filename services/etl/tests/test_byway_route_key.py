"""The route key: reading it, gating on it, and catching Caltrans getting it wrong.

The key is what stops a frontage road inheriting the freeway's designation, because distance cannot: a
frontage road sits in the same band as the freeway's own second carriageway. The failure worth guarding here
is the key's own: a row keyed to the WRONG number still has a key, so the keyless check never fires, and it
rejects its entire corridor in silence. That is not hypothetical - Caltrans FID 181 is 27.9 km of State
Route 236 filed as RTE=221, and `test_byway_miskey.py` runs these same functions over that real row and the
real OSM ways under it. This file is the constructed cases that pin each decision on its own.
"""
from __future__ import annotations

from etl import byway_route_key as rk
from etl import byways as bw
from etl import snap

# A north-south line, and ways along it, for the constructed cases.
LINE = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]


def way_along(lon=-122.35, ref=None, n=4):
    return {"ref": ref, "geometry": [(37.50 - i * 0.01, lon) for i in range(n)]}


class TestReadingARef:
    def test_a_ref_gives_up_its_route_numbers(self):
        assert bw.route_numbers("I 280;CA 35") == {"280", "35"}
        assert bw.route_numbers("I-280") == {"280"}
        assert bw.route_numbers("US 101") == {"101"}

    def test_a_business_route_is_not_the_mainline(self):
        """'US 101 Business' runs beside US 101 and is explicitly not it. Reading the digits out of the
        middle of a suffixed ref would hand it the mainline's designation."""
        assert bw.route_numbers("US 101 Business") == set()

    def test_an_absent_ref_claims_no_route(self):
        assert bw.route_numbers(None) == set()
        assert bw.route_numbers("") == set()

    def test_an_entry_with_no_route_key_falls_back_to_geometry(self):
        """The FHWA layer carries a trail name and no route number, so its entries cannot use this test."""
        assert bw.route_matches(set(), None) is True
        assert bw.route_matches(None, "CA 35") is True

    def test_an_entry_with_a_route_key_needs_the_way_to_name_it(self):
        assert bw.route_matches({"280"}, "I 280") is True
        assert bw.route_matches({"280"}, "CA 35") is False
        assert bw.route_matches({"280"}, None) is False

    def test_a_concurrency_names_both_routes(self):
        assert bw.route_matches({"35"}, "I 280;CA 35") is True


class TestWhatTheCorridorClaims:
    def test_only_reffed_ways_vote(self):
        """An unreffed way says nothing about which NUMBER the corridor is. That is the whole reason a
        wrong key cannot be repaired by falling back to geometry: along FID 181, 25.3 km of the 53.5 km
        clearing the gate is trails, service roads and a residential grid."""
        entry = {"routes": {"221"}, "geometry": LINE}
        claimed = rk.claimed_lengths(entry, [way_along(ref=None), way_along(ref="CA 236")])
        assert set(claimed) == {"236"}

    def test_a_way_that_does_not_clear_the_overlap_gate_does_not_vote(self):
        """A cross street SHARING A NODE with the corridor and leaving at right angles. It has to start
        inside the corridor's box or the bbox reject decides this instead of the overlap gate - which is
        what the first version of this test did: it put the way 4 km east, the box threw it out, and
        deleting the gate from `claimed_lengths` entirely left all 117 byway tests green (mutation M39).
        A cross street votes with its WHOLE length if the gate is gone, so a 3 km road touching a corridor
        at one junction could out-vote the route the corridor really is and drive a wrong re-key."""
        entry = {"routes": {"221"}, "geometry": LINE}
        cross = {"ref": "CA 236", "geometry": [(37.49, -122.35), (37.49, -122.34), (37.49, -122.33)]}
        lo_lat, hi_lat, lo_lon, hi_lon = rk._padded(LINE, snap.SNAP_TOLERANCE_M)
        # Inside the box, so the bbox reject is not what refuses it - the overlap gate has to.
        assert lo_lat <= cross["geometry"][0][0] <= hi_lat
        assert lo_lon <= cross["geometry"][0][1] <= hi_lon
        assert snap.overlap_fraction(cross["geometry"], LINE) < bw.MIN_OVERLAP_FRACTION
        assert rk.claimed_lengths(entry, [cross]) == {}

    def test_a_concurrency_votes_for_both_of_its_numbers(self):
        entry = {"routes": {"221"}, "geometry": LINE}
        claimed = rk.claimed_lengths(entry, [way_along(ref="I 280;CA 35")])
        assert set(claimed) == {"280", "35"}
        assert claimed["280"] == claimed["35"] > 0

    def test_a_way_nowhere_near_is_rejected_by_the_bounding_box_not_just_by_the_gate(self):
        """The bbox reject is what makes this affordable over a whole region. It has to agree with the
        slow path, so a way outside the box must be one the gate would have refused anyway."""
        entry = {"routes": {"221"}, "geometry": LINE}
        elsewhere = {"ref": "CA 236", "geometry": [(40.0, -120.0), (40.01, -120.0)]}
        assert rk.claimed_lengths(entry, [elsewhere]) == {}
        assert snap.overlap_fraction(elsewhere["geometry"], LINE) < bw.MIN_OVERLAP_FRACTION


class TestTheVerdict:
    def test_a_key_the_corridor_claims_is_corroborated_and_untouched(self):
        entry = {"routes": {"236"}, "geometry": LINE}
        verdict, routes, _ = rk.corridor_verdict(entry, [way_along(ref="CA 236")])
        assert verdict == bw.KEY_CORROBORATED
        assert routes == {"236"}

    def test_a_key_nothing_claims_is_re_keyed_to_what_the_corridor_says(self):
        """The FID 181 case in miniature: the row says 221, every way under it says 236."""
        entry = {"routes": {"221"}, "geometry": LINE}
        verdict, routes, claimed = rk.corridor_verdict(entry, [way_along(ref="CA 236")])
        assert verdict == bw.KEY_REKEYED
        assert routes == {"236"}
        assert claimed["236"] >= rk.MIN_CONSENSUS_M

    def test_a_short_stub_cannot_re_key_a_corridor(self):
        """MIN_CONSENSUS_M. One reffed fragment at a junction is not evidence about a 28 km corridor."""
        entry = {"routes": {"221"}, "geometry": LINE}
        stub = {"ref": "CA 9", "geometry": [(37.4900, -122.35), (37.4905, -122.35)]}
        assert snap.length_m(stub["geometry"]) < rk.MIN_CONSENSUS_M
        verdict, routes, _ = rk.corridor_verdict(entry, [stub])
        assert verdict == bw.KEY_UNCLAIMED
        assert routes == {"221"}

    def test_a_corridor_that_cannot_agree_keeps_its_key_and_is_reported(self):
        """MIN_CONSENSUS_SHARE. Two numbers splitting the corridor evenly is not a consensus, and guessing
        between them is worse than scoring zero and saying so."""
        entry = {"routes": {"221"}, "geometry": LINE}
        a = way_along(lon=-122.3504, ref="CA 9")
        b = way_along(lon=-122.3496, ref="CA 84")
        verdict, routes, claimed = rk.corridor_verdict(entry, [a, b])
        assert len(claimed) == 2
        assert max(claimed.values()) / sum(claimed.values()) < rk.MIN_CONSENSUS_SHARE
        assert verdict == bw.KEY_UNCLAIMED
        assert routes == {"221"}

    def test_an_entry_with_no_key_at_all_is_not_the_same_thing_as_a_wrong_one(self):
        """An FHWA row has no route number to check, and geometry-only is its designed mode, not a fault."""
        verdict, routes, _ = rk.corridor_verdict({"routes": set(), "geometry": LINE}, [])
        assert verdict == bw.KEY_UNKEYED
        assert routes == set()


class TestReconcile:
    def test_it_stamps_every_entry_and_mutates_none_of_them(self):
        entries = [{"routes": {"221"}, "geometry": LINE}]
        out = rk.reconcile(entries, [way_along(ref="CA 236")])
        assert all(e[bw.KEY_VERDICT] for e in out)
        assert entries[0] == {"routes": {"221"}, "geometry": LINE}, "input was mutated"

    def test_a_re_key_records_what_the_source_said_and_what_outvoted_it(self):
        """The repair has to be auditable from the entry, not only from a log line somebody deleted."""
        out = rk.reconcile([{"routes": {"221"}, "geometry": LINE}], [way_along(ref="CA 236")])
        assert out[0]["routes"] == {"236"}
        assert out[0]["key_was"] == ["221"]
        assert out[0]["key_evidence_m"] > rk.MIN_CONSENSUS_M

    def test_problems_sees_a_re_key_and_stops_seeing_the_unchecked_warning(self):
        entries = [{"status": "OD", "source": "caltrans", "routes": {"221"}, "geometry": LINE}]
        before = bw.problems(entries)
        assert any("never checked against the ways" in p for p in before), before
        after = bw.problems(rk.reconcile(entries, [way_along(ref="CA 236")]))
        assert not any("never checked against the ways" in p for p in after), after
        assert any("re-keyed" in p and "221" in p for p in after), after
