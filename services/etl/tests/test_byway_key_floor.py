"""ONE FLOOR, BOTH DIRECTIONS: the key has to hold its corridor on the terms a rival needs to take it.

Round 3 found that CORROBORATED was decided on a bare membership test. Round 4 gave the defending side
`MIN_CONSENSUS_M` - but only through `_outvoting`, which ALSO requires one rival to hold
`MIN_CONSENSUS_SHARE`, so where no single rival cleared both bars `corridor_verdict` returned before either
floor was read and a sub-floor fragment still bought a wrong key its silence. Round 5 demonstrated that on
real FID 181 geometry twice, and demonstrated the mirror image: a key over the metres floor at a 7.6% share
kept 12.4 km of Big Basin Way as CONTESTED.

Both are the same defect, so both are pinned here rather than beside the verdicts they happen to touch:
every test in this file is about `byway_route_key._holds` being asked of the KEY and of a RIVAL on the same
terms. The real-geometry cases use the same fixture as `test_byway_miskey.py`; the constructed ones use
their own lines. The interval that had NO test before this file is `0 < key_m < MIN_CONSENSUS_M` on a
corridor where nothing can outvote the key - every earlier verdict test with a sub-floor key had key_m = 0.
"""
from __future__ import annotations

import pytest

from etl import byway_route_key as rk
from etl import byways as bw
from etl import snap
from tests.test_byway_miskey import byway_entries, fixture_ways

# 3.3 km, the constructed corridor the verdict tests use; SHORT_LINE is under MIN_CONSENSUS_M, so no
# number can ever hold it - the case where `_outvoting` is empty whatever the ways say.
LINE = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]
SHORT_LINE = [(37.50, -122.35), (37.4970, -122.35)]


def entry(routes, line=None):
    return {"routes": set(routes), "status": bw.ELIGIBLE, "source": "caltrans", "geometry": line or LINE}


def way(ref, a, b, lon=-122.35):
    return {"ref": ref, "geometry": [(a, lon), (b, lon)]}


class TestTheKeyDefendsOnTheSameTermsARivalNeeds:
    def test_a_sub_floor_fragment_cannot_corroborate_a_key_no_rival_is_big_enough_to_take(self):
        """The hole round 5 found. The corridor is 333 m, so NOTHING can reach MIN_CONSENSUS_M - which is
        exactly why the old code never consulted a floor here: `_outvoting` came back empty and the
        function returned CORROBORATED on `key_m > 0`. A 33 m mis-tagged fragment was the whole evidence."""
        e = entry({"221"}, SHORT_LINE)
        assert snap.length_m(SHORT_LINE) < rk.MIN_CONSENSUS_M
        stub = way("CA 221", 37.50, 37.4997)
        rival = way("CA 9", 37.4997, 37.4994)
        claimed, reffed_m = rk._claims(e, [stub, rival])
        assert claimed["221"] == pytest.approx(33.4, abs=0.5), claimed      # literals, measured once
        assert claimed["9"] == pytest.approx(33.4, abs=0.5), claimed
        assert 0 < claimed["221"] < rk.MIN_CONSENSUS_M                      # the untested interval
        assert not rk._outvoting(claimed, reffed_m, {"221"}, claimed["221"])   # nobody can take it
        verdict, routes, _ = rk.corridor_verdict(e, [stub, rival])
        assert verdict == bw.KEY_UNDER_EVIDENCED
        assert routes == {"221"}, "the key is KEPT - this module never falls back to geometry"

    def test_a_sub_floor_fragment_cannot_corroborate_a_key_on_a_corridor_that_cannot_agree(self):
        """The second half of the hole: the corridor is long enough, but its rival evidence splits so no
        single number holds MIN_CONSENSUS_SHARE. `_outvoting` is empty again, and the 33 m fragment used
        to be enough to call that agreement."""
        e = entry({"221"})
        stub = way("CA 221", 37.50, 37.4997)
        a = way("CA 9", 37.50, 37.4880, lon=-122.3504)
        b = way("CA 84", 37.4880, 37.47, lon=-122.3496)
        claimed, reffed_m = rk._claims(e, [stub, a, b])
        assert claimed["9"] == pytest.approx(1334.8, abs=1.0), claimed       # literals, measured once
        assert claimed["84"] == pytest.approx(2002.1, abs=1.0), claimed
        assert max(claimed[n] for n in ("9", "84")) >= rk.MIN_CONSENSUS_M    # a rival clears the METRES
        assert max(claimed[n] / reffed_m for n in ("9", "84")) < rk.MIN_CONSENSUS_SHARE   # not the SHARE
        assert not rk._outvoting(claimed, reffed_m, {"221"}, claimed["221"])
        verdict, routes, _ = rk.corridor_verdict(e, [stub, a, b])
        assert (verdict, routes) == (bw.KEY_UNDER_EVIDENCED, {"221"})

    def test_the_key_and_a_rival_are_judged_by_the_same_function_on_the_same_evidence(self):
        """The rule itself, stated as a symmetry: hold the evidence fixed and swap WHICH number is the
        key. Keyed to the number that holds 100% of the corridor, it is corroborated; keyed to the one
        holding 3%, the same evidence re-keys it. Nothing about the verdict may depend on which side of
        the comparison the source's number happens to sit on."""
        evidence = [way("CA 236", 37.50, 37.47), way("CA 221", 37.50, 37.4991)]
        claimed, reffed_m = rk._claims(entry({"236"}), evidence)
        assert rk._holds(claimed["236"], reffed_m) and not rk._holds(claimed["221"], reffed_m)
        assert rk.corridor_verdict(entry({"236"}), evidence)[0] == bw.KEY_CORROBORATED
        assert rk.corridor_verdict(entry({"221"}), evidence)[:2] == (bw.KEY_REKEYED, {"236"})

    def test_a_key_under_the_floor_is_printed_by_problems_because_reported_is_the_point(self):
        """UNDER_EVIDENCED exists to be seen. CORROBORATED is the one verdict `problems()` never prints,
        so a verdict that silently joined it would repeat the failure that cost FID 181 28 km."""
        e = entry({"221"}, SHORT_LINE)
        fixed = rk.reconcile([e], [way("CA 221", 37.50, 37.4997)])
        assert fixed[0][bw.KEY_VERDICT] == bw.KEY_UNDER_EVIDENCED
        lines = [p for p in bw.problems(fixed) if "too little to establish" in p]
        assert len(lines) == 1 and "221" in lines[0], bw.problems(fixed)

    def test_an_under_evidenced_key_is_not_the_same_verdict_as_one_nothing_claims_at_all(self):
        """Two situations, two repairs: UNDER_EVIDENCED has a claim and a number to go and look at,
        UNCLAIMED has nothing at all. `byways.KEY_*` keeps them apart so `problems()` can say which."""
        e = entry({"221"}, SHORT_LINE)
        nothing = rk.reconcile([e], [way("CA 9", 37.50, 37.4997)])[0]
        something = rk.reconcile([e], [way("CA 221", 37.50, 37.4997)])[0]
        assert nothing[bw.KEY_VERDICT] == bw.KEY_UNCLAIMED and nothing["key_claim_m"] == 0.0
        assert something[bw.KEY_VERDICT] == bw.KEY_UNDER_EVIDENCED and something["key_claim_m"] > 0

    def test_every_keyed_entry_records_what_the_key_held_and_what_it_was_a_share_of(self):
        """RV7-3: `key_claim_m` used to be stamped only on the loud verdicts, so CORROBORATED - the one
        `problems()` never prints - was also the one with no audit trail. The verdict is a judgement about
        two numbers; both are on every keyed entry now, and an entry with no key carries neither."""
        road = way("CA 236", 37.50, 37.47)
        for ways_, verdict in [([road], bw.KEY_REKEYED),
                               ([way("CA 221", 37.50, 37.47)], bw.KEY_CORROBORATED),
                               ([way("CA 9", 37.4900, 37.4895)], bw.KEY_UNCLAIMED)]:
            out = rk.reconcile([entry({"221"})], ways_)[0]
            assert out[bw.KEY_VERDICT] == verdict
            assert out["key_claim_m"] >= 0.0 and out["reffed_claim_m"] > 0.0, (verdict, out)
        unkeyed = rk.reconcile([{"routes": set(), "geometry": LINE}], [road])[0]
        assert unkeyed[bw.KEY_VERDICT] == bw.KEY_UNKEYED
        assert "key_claim_m" not in unkeyed and "reffed_claim_m" not in unkeyed

    def test_problems_counts_the_byways_affected_not_the_distinct_route_numbers(self):
        """RV7-5. Forty rows sharing one wrong RTE value is forty corridors losing their ways; counting
        distinct STRINGS reported that as `1 route number(s)`, which is the smallest number in the data."""
        entries = [entry({"221"}), entry({"221"}), entry({"221"})]
        fixed = rk.reconcile(entries, [way("CA 236", 37.50, 37.47)])
        line = next(p for p in bw.problems(fixed) if "re-keyed" in p)
        assert line.startswith("3 byway(s)"), line
        assert "['221']" in line, line


class TestTheRealCorridorUnderTheNewFloor:
    def test_a_fragment_cannot_silence_a_slice_of_the_real_corridor_no_number_can_win(self):
        """Round 5's case A on the real geometry it was found on: FID 181's first nine vertices, 354.3 m
        of Big Basin Way. One 30.8 m way tagged with Caltrans's wrong `CA 221` used to turn a reported
        corridor into a silent one - on real OSM ways, not constructed ones."""
        e = dict(byway_entries()[0])
        e["geometry"] = e["geometry"][:9]
        assert snap.length_m(e["geometry"]) == pytest.approx(354.3, abs=1.0)
        stub = {"way_id": "mistagged", "name": "fragment", "highway": "tertiary", "ref": "CA 221",
                "role": "fake", "geometry": [e["geometry"][0], e["geometry"][1]]}
        assert snap.length_m(stub["geometry"]) == pytest.approx(30.8, abs=0.5)
        fixed = rk.reconcile([e], fixture_ways() + [stub])
        assert fixed[0][bw.KEY_VERDICT] == bw.KEY_UNDER_EVIDENCED
        assert fixed[0]["key_claim_m"] == pytest.approx(30.8, abs=0.5)
        assert any("too little to establish" in p for p in bw.problems(fixed))

    def test_fragments_worth_a_twelfth_of_the_key_evidence_cannot_hold_the_real_corridor(self):
        """Round 5's MUST_FIX on the real corridor. 25 fragments tagged `ref=CA 221` on FID 181's own
        vertices total 1033.2 m - over MIN_CONSENSUS_M, and 7.6% of the reffed length along part 0. On a
        bare metres floor that flipped part 0 to CONTESTED and cost 12389.1 m of Big Basin Way its bonus.
        The share floor is what refuses it: 7.6% is not holding a corridor."""
        entries = byway_entries()
        line = entries[0]["geometry"]
        frags = [{"way_id": f"frag-{i}", "name": "fragment", "highway": "tertiary", "ref": "CA 221",
                  "role": "fake", "geometry": [line[i], line[i + 1]]} for i in range(25)]
        assert sum(snap.length_m(f["geometry"]) for f in frags) == pytest.approx(1033.2, abs=2.0)
        fixed = rk.reconcile(entries, fixture_ways() + frags)
        part0 = fixed[0]
        assert part0["key_claim_m"] > rk.MIN_CONSENSUS_M                      # over the METRES floor
        assert part0["key_claim_m"] / part0["reffed_claim_m"] < 0.10          # and holding nothing
        assert [e[bw.KEY_VERDICT] for e in fixed] == [bw.KEY_REKEYED, bw.KEY_REKEYED]
        recovered = sum(snap.length_m(w["geometry"]) for w in fixture_ways("the_corridor_itself")
                        if bw.bonus_for(w["geometry"], fixed, way_ref=w["ref"],
                                        way_class=w["highway"]) > 0)
        assert recovered == pytest.approx(28143, abs=200), recovered

    def test_mis_tagged_fragments_worth_a_fifth_of_the_evidence_stop_any_number_holding_it(self):
        """What the floor costs on the other side, measured rather than left to be discovered.

        The fragments never touch the 12389.1 m of real `ref=CA 236` along part 0 - but they ARE reffed
        ways, so they enlarge the length every share is a share OF, and the rival's share falls although
        its metres do not. At 82 of them 236 is at 0.800 and stops holding the corridor; nothing holds it,
        so the key is kept and part 0 loses its 12389.1 m again. That is the rule and not a leak - a fifth
        of a corridor's evidence disagreeing is a corridor that has established no number - and the
        difference from the code round 5 read is that it is REPORTED. There the same corridor came back
        CORROBORATED, the one verdict `problems()` never prints. The boundary is here as a number so that
        moving it has to be deliberate."""
        entries = byway_entries()
        line = entries[0]["geometry"]
        frags = [{"way_id": f"frag-{i}", "name": "fragment", "highway": "tertiary", "ref": "CA 221",
                  "role": "fake", "geometry": [line[i], line[i + 1]]} for i in range(82)]
        assert sum(snap.length_m(f["geometry"]) for f in frags) == pytest.approx(2974.2, abs=3.0)
        fixed = rk.reconcile(entries, fixture_ways() + frags)
        part0 = fixed[0]
        assert part0["key_claim_m"] == pytest.approx(2974.2, abs=3.0), part0["key_claim_m"]
        assert part0["reffed_claim_m"] == pytest.approx(15489.3, abs=5.0), part0["reffed_claim_m"]
        assert part0[bw.KEY_VERDICT] == bw.KEY_UNDER_EVIDENCED           # not corroborated, not silent
        assert any("too little to establish" in p for p in bw.problems(fixed))
        earning = sum(snap.length_m(w["geometry"]) for w in fixture_ways("the_corridor_itself")
                      if bw.bonus_for(w["geometry"], fixed, way_ref=w["ref"],
                                      way_class=w["highway"]) > 0)
        assert earning == pytest.approx(15753.8, abs=200), earning       # part 1 only: part 0's is gone

    def test_a_way_doubling_back_votes_more_metres_than_the_corridor_is_long(self):
        """RV7-4, pinned as a KNOWN limit rather than left undescribed. The floors are metres of WAY along
        the corridor, not metres of corridor, so a way folded back and forth over a 222.5 m corridor votes
        2669.5 m and clears a floor the corridor itself can never reach. The module docstring says why the
        obvious cap is not the repair (it breaks divided highways) and that measuring corridor COVERAGE is
        its own task. This test exists so that when that task lands, this number changes visibly."""
        corridor = {"routes": {"221"}, "geometry": [(37.50, -122.35), (37.498, -122.35)]}
        folded = []
        for i in range(12):
            folded += [(37.50, -122.35), (37.498, -122.35)] if i % 2 == 0 else \
                      [(37.498, -122.35), (37.50, -122.35)]
        w = {"ref": "CA 236", "geometry": folded}
        assert snap.length_m(corridor["geometry"]) == pytest.approx(222.5, abs=1.0)
        claimed = rk.claimed_lengths(corridor, [w])
        assert claimed["236"] == pytest.approx(2669.5, abs=2.0)
        assert claimed["236"] > 10 * snap.length_m(corridor["geometry"])
        assert rk.corridor_verdict(corridor, [w])[0] == bw.KEY_REKEYED
