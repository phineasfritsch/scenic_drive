"""What a Caltrans designation is worth, which match wins, and which roads are refused the bonus.

The failure worth guarding is not a crash. It is a road scoring as scenic because of a road next to it, or
because a weight drifted away from the evidence recorded for it. The snapping arithmetic underneath lives in
test_snap.py, the route key in test_byway_route_key.py, and the real-geometry versions of the frontage-road
and cross-street cases in test_byways_fixture.py; these are the constructed cases that pin the decisions.
"""
from __future__ import annotations

import pytest

from etl import byways as bw

# A north-south line near Skyline, and a way running along it.
BYWAY = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35)]


def along(offset_deg=0.0, n=4, start=37.50, lon=-122.35):
    return [(start - i * 0.01, lon + offset_deg) for i in range(n)]


class TestStatusMeaning:
    def test_officially_designated_scores_the_full_bonus(self):
        assert bw.status_bonus("OD") == bw.DESIGNATED_BONUS

    def test_eligible_scores_too_but_less(self):
        """Eligible is a STATUTORY LISTING - the Legislature added the route to S&H 263.1-263.8 - whose
        content descends from the 1963 Caltrans Master Plan, selected on five named scenic factors (AB 998
        Assembly Transportation analysis, 4/1/2019). So E has been screened for scenery once, at route
        level, and never since; what it has never had is the per-segment visual assessment, which is step 1
        of the nomination a local government prepares AFTER the route is eligible. It scores less than OD
        and more than nothing, and both halves of that are the point."""
        assert 0 < bw.status_bonus("E") < bw.status_bonus("OD")

    def test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes(self):
        """Measured from the pinned pull: officially designated routes are 2512.5 km of the layer's
        12880.4 km, so OD_SHARE_OF_SYSTEM of the eligible system has ever been designated. That base rate
        times the designated weight is ELIGIBLE_FLOOR - what E is worth if it is worth only its chance of
        clearing the second gate. ELIGIBLE_CEILING is half of OD, because the per-segment assessment was
        never applied to an eligible-only route. Where E sits between them is a judgement; that it sits
        BETWEEN them is not.

        The pre-review value 0.10 was above this bracket, and it was derived from the false claim that
        eligibility is itself a scenic assessment."""
        assert bw.ELIGIBLE_FLOOR <= bw.ELIGIBLE_BONUS <= bw.ELIGIBLE_CEILING, (
            bw.ELIGIBLE_FLOOR, bw.ELIGIBLE_BONUS, bw.ELIGIBLE_CEILING)

    def test_the_bracket_is_half_of_od_and_the_measured_base_rate_not_something_wider(self):
        """The bracket used to live twice: as two literals in this test and as a sentence in the module
        docstring that said the ceiling was 0.15, i.e. E == OD. A weight of 0.14 was legal under the
        paragraph and red under the test. Now there is one pair of constants and both the paragraph and
        this assertion name them, so the two cannot drift apart again."""
        assert bw.ELIGIBLE_CEILING == pytest.approx(0.5 * bw.DESIGNATED_BONUS)
        assert bw.ELIGIBLE_CEILING < bw.DESIGNATED_BONUS
        assert bw.ELIGIBLE_FLOOR == pytest.approx(bw.OD_SHARE_OF_SYSTEM * bw.DESIGNATED_BONUS)
        assert 0.19 <= bw.OD_SHARE_OF_SYSTEM <= 0.20, bw.OD_SHARE_OF_SYSTEM

    def test_an_unknown_status_scores_nothing_rather_than_guessing(self):
        assert bw.status_bonus("XYZ") == 0.0
        assert bw.status_bonus(None) == 0.0

    def test_no_status_exceeds_the_plans_per_term_allowance(self):
        """MAX_BONUS is enforced here rather than by a min() at the call site. At these values
        min(MAX_BONUS, status_bonus(...)) could never bind, so it looked like a check and was not one. This
        goes red the moment any weight is raised past the plan's +0.15."""
        for status in sorted(bw.KNOWN_STATUS):
            assert bw.status_bonus(status) <= bw.MAX_BONUS, status

    def test_unknown_statuses_are_detectable(self):
        """The field has NO published coded-value domain, so Caltrans can add a value without telling
        anyone. A new value would silently score zero, which reads as 'not a byway'."""
        assert bw.unknown_statuses(["OD", "E", None]) == set()
        assert bw.unknown_statuses(["OD", "NEW"]) == {"NEW"}


class TestTheCap:
    def test_the_cap_binds_on_es_total_not_on_the_bonus_term(self):
        """The plan says '+0.15 byway, capped'. The six base E terms already sum to 1.00, so a way at 0.95
        that is also designated must land at 1.0. Capping the bonus term alone never binds and never did."""
        assert bw.apply_to_e(0.95, bw.DESIGNATED_BONUS) == pytest.approx(bw.E_CEILING)

    def test_a_total_under_the_ceiling_is_untouched(self):
        assert bw.apply_to_e(0.50, bw.DESIGNATED_BONUS) == pytest.approx(0.65)

    def test_an_unmatched_way_keeps_its_base_score_exactly(self):
        assert bw.apply_to_e(0.42, 0.0) == pytest.approx(0.42)


class TestMatching:
    def _entries(self):
        return [
            {"name": "Skyline", "status": "OD", "source": "caltrans", "geometry": BYWAY},
            {"name": "Other", "status": "E", "source": "caltrans", "geometry": BYWAY},
        ]

    def test_a_way_on_the_byway_matches_it(self):
        m = bw.match(along(), self._entries())
        assert m is not None and m["overlap"] == pytest.approx(1.0)

    def test_the_stronger_designation_wins_a_tie(self):
        assert bw.match(along(), self._entries())["status"] == "OD"

    def test_between_two_equal_designations_the_one_that_covers_more_is_the_one_reported(self):
        """`match` documents "best by STATUS, then by overlap" and nothing tested the second half:
        `test_the_stronger_designation_wins_a_tie` gives both entries the SAME geometry, so the overlap
        tiebreak never runs and deleting it entirely passed all 70 tests. With equal status the BONUS is
        identical either way - what changes is the `name` and `overlap` recorded against the way, which is
        the corridor's provenance, so a corpus built on the loser records the wrong road.

        The reversed-order assertion is the one that matters: without it, 'first entry wins' would pass."""
        way = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35), (37.46, -122.35)]
        more = [(37.501, -122.35), (37.472, -122.35)]     # covers ~70% of the way
        less = [(37.501, -122.35), (37.476, -122.35)]     # covers ~60%
        more_frac = bw.overlap_fraction(way, more)
        less_frac = bw.overlap_fraction(way, less)
        assert more_frac > less_frac >= bw.MIN_OVERLAP_FRACTION, (more_frac, less_frac)
        entries = [{"name": "less of it", "status": "OD", "geometry": less},
                   {"name": "more of it", "status": "OD", "geometry": more}]
        assert bw.match(way, entries)["name"] == "more of it"
        assert bw.match(way, list(reversed(entries)))["name"] == "more of it"
        assert bw.match(way, entries)["overlap"] == pytest.approx(more_frac)

    def test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more(self):
        """The gate is where 'is this the same road' is decided. Past it, overlap fraction measures how much
        of the OSM way a corridor covers - a function of where OSM split the way - and does not say which
        designation to carry. Ordering by overlap first let a 70%-overlapping ELIGIBLE corridor beat a
        60%-overlapping DESIGNATED one, contradicting this module's own stated intent."""
        way = [(37.50, -122.35), (37.49, -122.35), (37.48, -122.35), (37.47, -122.35), (37.46, -122.35)]
        eligible_line = [(37.501, -122.35), (37.472, -122.35)]      # covers ~70% of the way
        designated_line = [(37.501, -122.35), (37.476, -122.35)]    # covers ~60%
        e_frac = bw.overlap_fraction(way, eligible_line)
        d_frac = bw.overlap_fraction(way, designated_line)
        assert e_frac > d_frac >= bw.MIN_OVERLAP_FRACTION, (e_frac, d_frac)
        entries = [{"name": "eligible one", "status": "E", "geometry": eligible_line},
                   {"name": "designated one", "status": "OD", "geometry": designated_line}]
        assert bw.match(way, entries)["status"] == "OD"
        assert bw.bonus_for(way, entries, way_class="secondary") == bw.DESIGNATED_BONUS

    def test_a_cross_street_touching_at_a_junction_does_not_match(self):
        """It shares a node with the byway and nothing else. Without a minimum overlap it would inherit the
        designation from a single point of contact."""
        cross = [(37.49, -122.35), (37.49, -122.34), (37.49, -122.33)]
        assert bw.match(cross, self._entries()) is None

    def test_a_way_nowhere_near_matches_nothing(self):
        assert bw.match(along(offset_deg=0.05), self._entries()) is None

    def test_an_entry_with_no_geometry_is_skipped_not_matched(self):
        assert bw.match(along(), [{"name": "x", "status": "OD", "geometry": []}]) is None

    def test_a_way_lying_on_a_numbered_route_still_needs_to_claim_it(self):
        """The frontage road, in miniature. Geometry alone matches - it is right on top of the corridor -
        and the route key is the only thing that stops it inheriting the designation."""
        entries = [{"name": "CA SM route 280", "status": "OD", "source": "caltrans",
                    "routes": {"280"}, "geometry": BYWAY}]
        assert bw.overlap_fraction(along(), BYWAY) == pytest.approx(1.0)
        assert bw.match(along(), entries, way_ref=None) is None
        assert bw.match(along(), entries, way_ref="CA 35") is None
        assert bw.match(along(), entries, way_ref="I 280")["status"] == "OD"


class TestBonus:
    def test_a_designated_way_earns_the_full_bonus(self):
        entries = [{"name": "Skyline", "status": "OD", "geometry": BYWAY}]
        assert bw.bonus_for(along(), entries, way_class="secondary") == bw.DESIGNATED_BONUS

    def test_an_eligible_way_earns_less(self):
        entries = [{"name": "Somewhere", "status": "E", "geometry": BYWAY}]
        assert 0 < bw.bonus_for(along(), entries, way_class="tertiary") < bw.DESIGNATED_BONUS

    def test_an_unmatched_way_earns_nothing(self):
        entries = [{"name": "Skyline", "status": "OD", "geometry": BYWAY}]
        assert bw.bonus_for(along(offset_deg=0.05), entries, way_class="secondary") == 0.0


class TestTheMotorwayGate:
    """S&H 263.3 lists Interstates as eligible and the pinned pull has I-80/280/580/680 rows at both
    statuses, while the plan's invariant is that motorway and trunk score 0 on scenery. Without a gate the
    composition site in T-0029 would put scenery back on exactly those roads."""

    ENTRIES = [{"name": "CA SM route 280", "status": "OD", "source": "caltrans", "geometry": BYWAY}]

    def test_a_motorway_on_a_designated_corridor_earns_nothing(self):
        assert bw.match(along(), self.ENTRIES) is not None
        assert bw.bonus_for(along(), self.ENTRIES, way_class="motorway") == 0.0

    def test_every_scenic_zero_class_is_gated_not_just_motorway(self):
        for cls in sorted(bw.SCENIC_ZERO_CLASSES):
            assert bw.bonus_for(along(), self.ENTRIES, way_class=cls) == 0.0, cls
        assert bw.SCENIC_ZERO_CLASSES >= {"motorway", "trunk"}

    def test_an_ordinary_road_on_the_same_corridor_still_earns_it(self):
        """Otherwise 'the gate works' would be satisfied by a gate that rejects everything."""
        assert bw.bonus_for(along(), self.ENTRIES, way_class="tertiary") == bw.DESIGNATED_BONUS

    def test_the_match_itself_is_not_gated_only_the_score(self):
        """The designation is a fact about the corridor and stays visible in the data; what is withheld is
        the bonus. A gate inside `match` would erase the provenance too."""
        m = bw.match(along(), self.ENTRIES, way_ref=None)
        assert m is not None and m["status"] == bw.DESIGNATED

    def test_the_class_has_to_be_stated_it_cannot_be_omitted(self):
        """`way_class` is keyword-only with no default on purpose: a caller that does not know what kind of
        road it is holding must find out rather than collect a bonus by omission."""
        with pytest.raises(TypeError):
            bw.bonus_for(along(), self.ENTRIES)


class TestProblems:
    def test_a_healthy_set_has_no_problems(self):
        assert bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "E", "geometry": BYWAY}]) == []

    def test_an_empty_pull_is_reported(self):
        """An empty overlay flags nothing and looks exactly like a clean run."""
        assert any("no byways parsed" in p for p in bw.problems([]))

    def test_an_unrecognised_status_is_reported(self):
        problems = bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "NEW", "geometry": BYWAY}])
        assert any("unrecognised Status" in p for p in problems)

    def test_geometryless_entries_are_reported(self):
        problems = bw.problems([{"status": "OD", "geometry": BYWAY}, {"status": "E", "geometry": []}])
        assert any("no usable geometry" in p for p in problems)

    def test_a_pull_with_no_designated_byways_at_all_is_suspicious(self):
        problems = bw.problems([{"status": "E", "geometry": BYWAY}])
        assert any("no officially designated" in p for p in problems)

    def test_a_caltrans_entry_that_lost_its_route_key_is_reported(self):
        """Without RTE a Caltrans entry can only match on distance, which is exactly the mode that hands a
        frontage road the freeway's designation."""
        problems = bw.problems([{"status": "OD", "source": "caltrans", "routes": {"35"}, "geometry": BYWAY},
                                {"status": "E", "source": "caltrans", "routes": set(), "geometry": BYWAY}])
        assert any("no route key" in p for p in problems)

    def test_a_keyed_entry_nobody_ever_checked_is_reported(self):
        """The hole this closes. Caltrans FID 181 is keyed RTE=221 over State Route 236, so it HAS a key,
        the keyless check above never fires, and the entry silently rejects its own 28 km corridor. An
        entry that has never been through `byway_route_key.reconcile` is not known to be sound, and 'no
        problems' must not be reachable by never looking - which is exactly how this set stayed green."""
        entry = {"status": "OD", "source": "caltrans", "routes": {"221"}, "geometry": BYWAY}
        assert any("never checked against the ways" in p for p in bw.problems([entry]))
        checked = dict(entry, **{bw.KEY_VERDICT: bw.KEY_CORROBORATED})
        assert bw.problems([checked]) == []

    def test_a_re_keyed_entry_is_reported_with_the_number_the_source_got_wrong(self):
        entry = {"status": "E", "source": "caltrans", "routes": {"236"}, "key_was": ["221"],
                 bw.KEY_VERDICT: bw.KEY_REKEYED, "geometry": BYWAY}
        problems = bw.problems([dict(entry, status="OD"), entry])
        assert any("re-keyed" in p and "221" in p for p in problems), problems

    def test_an_entry_whose_key_nothing_along_it_claims_is_reported(self):
        """The verdict for a corridor with no consensus to re-key onto. It keeps its key and scores zero -
        guessing would be worse - so the only acceptable outcome is that somebody is told."""
        entry = {"status": "OD", "source": "caltrans", "routes": {"221"},
                 bw.KEY_VERDICT: bw.KEY_UNCLAIMED, "geometry": BYWAY}
        assert any("match no way at all" in p for p in bw.problems([entry]))
