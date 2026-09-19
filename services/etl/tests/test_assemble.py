"""The assembly's four gate assertions, the closed-loop rank, and the wiring between record and producer.

THE FOUR GATES are the ones the plan's `ops/sane` check 4 needs and T-0146's second acceptance line names:
no NULL score; motorway, trunk, private and unpaved ways exactly 0.0; every term in 0..1; ScenicKit parity
to 1e-6. Each is named `test_gate_...` so a red run says which gate broke rather than which file.

WHAT PINS WHAT. `fixtures/assembly_fixture.json` is hand-written and pins the ASSEMBLY - which producer
feeds which field, the declined flag, the gates, the zero classes and the sinuosity ranks, which are typed
out below with their arithmetic. It carries no `expected_score`: its ranked terms come out of
`curvature.way_curvature` and `terrain.relief` over real geometry, and a hand-computed expectation for
those would be a second implementation of the producer rather than an oracle (ruling R8).
The score ARITHMETIC is pinned by `Tests/Fixtures/scoring/segment_terms.json`, whose expectations were
transcribed by hand from plan:78-87 by neither scorer, and that file is what the parity gate drives through
`assemble.score_record` - the record -> `score_kwargs()` -> `score.score` seam this module tests.
`Tests/ScenicKitTests/SegmentScoreContractTests.swift` asserts the same rows of the same file at the same
tolerance, which is what makes it parity and not a self-comparison.

THE RANKED HALF OF THE WIRING IS `tests/test_assemble_wiring.py`: nothing in THIS file can see a RANKED
term read off the wrong producer, because every assertion here is made after `normalise_region` turned
those five into ranks, and a rank keeps no trace of the number it came from (PR #102's review, B1).
"""
from __future__ import annotations

import json
import math
import pathlib
import re

import pytest

from etl import assemble, byways, score, way_record

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURE = HERE / "fixtures" / "assembly_fixture.json"
SCORING_FIXTURE = ROOT / "Tests" / "Fixtures" / "scoring" / "segment_terms.json"
GATES_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"
GATE_REASON_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "GateReason.swift"

TOLERANCE = 1e-6

MOTORWAY = 800000001
TRUNK = 800000002
PRIVATE = 800000003
UNPAVED = 800000004
LOOP = 800000005
STRAIGHT = 800000006
SECONDARY = 800000007
UNSURVEYED = 800000008
NO_MOTOR_VEHICLE = 800000009
DESCENT = 800000010

# The seven ways that ANSWERED sinuosity, in the order their literals sort: 1.02, 1.15, 1.25, 1.30, 1.45,
# 1.60, 1.80. The mid-rank formula over a population of seven (normalise.py's docstring) is (i + 0.5*1)/7,
# typed as the division it is rather than as a transcribed decimal, because sevenths do not terminate. The
# population is seven and not ten: the two zero classes are EXCLUDED (normalise.py:33) and the closed loop
# DECLINED. Ways 800000009 and 800000010 joined it in the fix for PR #102's review, which is why these are
# no longer the fifths the 23:45:11Z entry recorded.
ANSWERING_SINUOSITY_RANKS = {STRAIGHT: 0.5 / 7, UNPAVED: 1.5 / 7, DESCENT: 2.5 / 7, PRIVATE: 3.5 / 7,
                             UNSURVEYED: 4.5 / 7, NO_MOTOR_VEHICLE: 5.5 / 7, SECONDARY: 6.5 / 7}

# The great-circle arc of 0.00005 deg of latitude on the sphere `distance_on_earth` uses
# (curvature.RAD_EARTH_M = 6373000), transcribed here rather than measured: 0.00005 * pi/180 * 6373000
# = 5.561491661479931. `distance_on_earth` is the spherical LAW OF COSINES, quirks included
# (curvature.py:31-48), which loses precision for two points a few metres apart - its own docstring says
# so - hence a tolerance of a millimetre rather than an ulp. What the test is pinning is the METRE, which
# is what `CLOSED_ENDPOINT_M` is compared against; the fourth decimal place is the model's business.
CLOSED_LOOP_ENDPOINT_GAP_M = 5.561491661479931
CLOSED_LOOP_GAP_TOLERANCE_M = 1e-3

# speedfit is triangular: 25 km/h, apex 65 km/h, 105 km/h, so the feet are 40 km/h apart on both sides
# (speedfit.py:34-36), and 1 mph = 1.609344 km/h (speedfit.py:39). Typed out:
#   65 mph = 104.60736 km/h -> (105 - 104.60736)/40 = 0.39264/40  = 0.009816
#   35 mph =  56.32704 km/h -> (56.32704 - 25)/40  = 31.32704/40  = 0.783176
EXPECTED_SPEED_FIT = {MOTORWAY: 0.009816, SECONDARY: 0.783176}
# landcover.fractions over the row's ten codes, counted by hand. canopy is classes {10, 20}, impervious
# {50}, water {80, 90, 95} (landcover.py:49-51); every code in this fixture is valid, so the denominator
# is 10 for every way.
#   800000001 [50,50,50,50,50,30,30,10,10,50] -> canopy 2/10, impervious 6/10, water 0/10
#   800000007 [10,10,10,10,10,10,20,30,80,10] -> canopy 8/10 (six 10s, one 20, one more 10),
#                                                  impervious 0/10, water 1/10
EXPECTED_LANDCOVER = {MOTORWAY: {"canopy": 0.2, "impervious": 0.6, "water": 0.0},
                      SECONDARY: {"canopy": 0.8, "impervious": 0.0, "water": 0.1}}

STATUS_FOR_TIER = {"none": None, "eligible": byways.ELIGIBLE, "designated": byways.DESIGNATED}


def _document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


DOCUMENT = _document()
TABLE = assemble.assemble(DOCUMENT)
BY_WAY = {row["way_id"]: row for row in TABLE}


def _coords(way_id: int) -> list:
    row = next(r for r in DOCUMENT["ways"] if r["way_id"] == way_id)
    return [(float(p[0]), float(p[1])) for p in row["coords"]]


def test_gate_no_row_has_a_null_score():
    """`ops/sane` check 4, first assertion. A NULL in this column is the corpus saying 'unknown'."""
    null = sorted(row["way_id"] for row in TABLE if row["score"] is None)
    assert null == [], "rows with a NULL score: %s" % null
    assert len(TABLE) == len(DOCUMENT["ways"]) == 10


def test_gate_motorway_and_trunk_score_exactly_zero_and_are_not_gated():
    """CLAUDE.md: they carry 0 and are still ROUTABLE. The 0.0 must come from the class, not a gate."""
    for way_id in (MOTORWAY, TRUNK):
        row = BY_WAY[way_id]
        assert row["score"] == 0.0, "way %d scored %r" % (way_id, row["score"])
        assert row["gate_reason"] is None, "way %d was GATED: %r" % (way_id, row["gate_reason"])
        assert row["terms_state"] == way_record.EXCLUDED


def test_gate_private_and_unpaved_ways_score_exactly_zero():
    """The safety gates, by name. `surface=gravel` is positive evidence; `access=private` forbids us."""
    assert BY_WAY[PRIVATE]["score"] == 0.0, BY_WAY[PRIVATE]
    assert BY_WAY[PRIVATE]["gate_reason"] == assemble.GATE_NO_ACCESS
    assert BY_WAY[UNPAVED]["score"] == 0.0, BY_WAY[UNPAVED]
    assert BY_WAY[UNPAVED]["gate_reason"] == assemble.GATE_UNPAVED_SURFACE
    # Unknown is not unpaved: the way with no surface tag is scored, not refused.
    assert BY_WAY[UNSURVEYED]["gate_reason"] is None
    assert BY_WAY[UNSURVEYED]["score"] > 0.0


def test_gate_every_term_is_in_the_unit_interval():
    """Every term the score was computed from, by way and term name. Not clamped anywhere - checked."""
    bad = []
    for row in TABLE:
        for name in score.UNIT_TERMS:
            value = row["terms"][name]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                bad.append("way %d: %s=%r is not a number" % (row["way_id"], name, value))
            elif not math.isfinite(value) or value < 0.0 or value > 1.0:
                bad.append("way %d: %s=%r is outside 0..1" % (row["way_id"], name, value))
    assert bad == [], "; ".join(bad)


def _scoring_rows() -> list:
    if not SCORING_FIXTURE.exists():
        raise AssertionError("fixture missing: %s" % SCORING_FIXTURE)
    return json.loads(SCORING_FIXTURE.read_text(encoding="utf-8"))["rows"]


def _metres(value) -> float:
    return math.inf if value == assemble.INFINITY else float(value)


def test_gate_scenickit_parity_to_1e_6_over_the_shared_scoring_fixture():
    """The record -> `score_kwargs()` -> `score.score` seam against the hand-transcribed oracle.

    `Tests/ScenicKitTests/SegmentScoreContractTests.swift` reads the same bytes at the same tolerance.
    Disagreements are reported BY ROW ID: a count tells the next agent nothing.
    """
    rows = _scoring_rows()
    assert len(rows) == 1000, len(rows)
    worst = []
    for index, row in enumerate(rows):
        record = way_record.WayRecord(
            way_id=index + 1, highway=row["highway"], curvature=row["curvature"],
            elevation_gain=row["elevationGain"], relief=row["relief"], sinuosity=row["sinuosity"],
            furniture=row["furniture"], canopy=row["canopy"], impervious=row["impervious"],
            water=row["water"], speed_fit=row["speedFit"], points_of_interest=row["pointsOfInterest"],
            surface=row["surface"], byway_status=STATUS_FOR_TIER[row["bywayTier"]],
            tunnel_meters=float(row["tunnelMeters"]),
            meters_to_nearest_motorway=_metres(row["metersToNearestMotorway"]),
            terms_state=way_record.NORMALISED)
        got = assemble.score_record(record)
        if got is None or abs(got - row["expected"]) >= TOLERANCE:
            worst.append("%s: got %r, oracle %r" % (row["id"], got, row["expected"]))
    assert worst == [], "%d of %d rows disagree with the oracle by >= %g: %s" % (
        len(worst), len(rows), TOLERANCE, "; ".join(worst[:5]))


def test_the_closed_loop_declines_sinuosity_instead_of_ranking_as_the_straightest_road():
    """T-0146's first acceptance line.

    The loop's sinuosity literal is the region's smallest (1.0, `sinuosity.CLOSED_WAY_SINUOSITY`, a FLOOR
    and not a measurement). Left in the population it takes the lowest rank in the region - it IS the
    region's straightest road - and it moves every other way's rank, because the divisor is the population
    size. Declined, it holds `DECLINED_RANK` exactly, which is not a rank at all: `normalise`'s estimator
    can never return 0.0 (the extremes are `0.5/n` and `1 - 0.5/n`), so the value itself says which of the
    two happened, and `flags()` says it by name.
    """
    loop = BY_WAY[LOOP]
    assert loop["terms"]["sinuosity"] == way_record.DECLINED_RANK, (
        "way %d holds sinuosity=%r and scores %r: that is a RANK, so the loop is in the population and is "
        "the region's straightest road (the lowest rank in a population of eight is (0 + 0.5*1)/8)"
        % (LOOP, loop["terms"]["sinuosity"], loop["score"]))
    assert loop["terms"]["sinuosity"] == 0.0
    assert way_record.SINUOSITY_DECLINED_FLAG in loop["flags"], loop["flags"]
    # The control: same highway class, a sinuosity literal one notch above the floor, endpoints apart.
    assert way_record.SINUOSITY_DECLINED_FLAG not in BY_WAY[STRAIGHT]["flags"]


def test_the_answering_ways_take_the_ranks_of_a_population_of_seven():
    """The loop's absence from the population is visible in the other seven ranks, not only in its own.

    With the loop counted in, the population is eight, the loop's 1.0 sorts below all seven, and every one
    of these moves up one place: 1.5/8, 2.5/8, 3.5/8, 4.5/8, 5.5/8, 6.5/8 and 7.5/8 - that is 0.1875,
    0.3125, 0.4375, 0.5625, 0.6875, 0.8125 and 0.9375, none of which is a seventh.
    """
    got = {way_id: BY_WAY[way_id]["terms"]["sinuosity"] for way_id in ANSWERING_SINUOSITY_RANKS}
    assert got == pytest.approx(ANSWERING_SINUOSITY_RANKS, abs=1e-12), got


def test_the_closed_way_predicate_uses_the_same_constant_as_the_sinuosity_producer():
    """Ruling R3: 10.0 m, `<=`, and `snap`'s length model - the same three as T-0161's `is_closed_way`."""
    assert assemble.CLOSED_ENDPOINT_M == 10.0
    assert assemble.endpoint_gap_m(_coords(LOOP)) == pytest.approx(
        CLOSED_LOOP_ENDPOINT_GAP_M, abs=CLOSED_LOOP_GAP_TOLERANCE_M)
    assert assemble.is_closed_way(_coords(LOOP)) is True
    assert assemble.is_closed_way(_coords(STRAIGHT)) is False
    with pytest.raises(ValueError, match="at least 2 coordinates"):
        assemble.endpoint_gap_m([(37.0, -122.0)])


def test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands():
    """The literal above pins 10.0 on ONE side. This dies the day `etl.sinuosity` exists and the two differ.

    No `pytest.skip`: the suite is skip-free and stays that way, so on main - where T-0161 (PR #94) has not
    landed and there is no `etl.sinuosity` - this returns and asserts nothing, by name.
    """
    try:
        from etl import sinuosity
    except ImportError:
        return
    assert (assemble.is_closed_way is sinuosity.is_closed_way
            and assemble.CLOSED_ENDPOINT_M is sinuosity.CLOSED_ENDPOINT_M), (
        "T-0161 landed: do the one-line swap in assemble.py")


def _swift_set(name: str) -> set:
    text = GATES_SWIFT.read_text(encoding="utf-8")
    match = re.search(r"let %s: Set<String> = \[(.*?)\]" % name, text, re.S)
    assert match, "%s is not declared in %s" % (name, GATES_SWIFT)
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def test_the_gate_sets_are_the_ones_scenickit_gates_on():
    """Anchored on the Swift declarations, not on a comment: two internally consistent files would put two
    different answers for one road in the corpus, and neither would look wrong on its own."""
    assert set(assemble.UNPAVED_SURFACES) == _swift_set("unpavedSurfaces")
    assert set(assemble.CLOSED_ACCESS) == _swift_set("closedAccess")
    cases = set(re.findall(r"^\s*case (\w+)", GATE_REASON_SWIFT.read_text(encoding="utf-8"), re.M))
    assert {"unpavedSurface", "track", "noAccess"} <= cases, sorted(cases)
    assert assemble.GATE_REASONS == ("unpaved_surface", "track", "no_access")


def test_the_mapped_terms_are_what_their_producers_return():
    """The wiring for the four MAPPED terms only, which arrive as values and are never ranked.

    The RANKED five are `tests/test_assemble_wiring.py`'s, on the RAW record; this docstring used to claim
    a hazard this test cannot see (PR #102's review, B1).
    """
    for way_id, expected in EXPECTED_SPEED_FIT.items():
        assert BY_WAY[way_id]["terms"]["speed_fit"] == pytest.approx(expected, abs=1e-12), way_id
    for way_id, expected in EXPECTED_LANDCOVER.items():
        for name, value in expected.items():
            assert BY_WAY[way_id]["terms"][name] == pytest.approx(value, abs=1e-12), (way_id, name)


def test_the_byway_overlay_reaches_exactly_the_way_it_overlaps():
    """`byways.match` is a region-level lookup, so a bonus landing on the wrong way is a real failure."""
    records = [assemble.record_from_row(row, DOCUMENT["byways"]) for row in DOCUMENT["ways"]]
    designated = sorted(r.way_id for r in records if r.byway_status == byways.DESIGNATED)
    assert designated == [SECONDARY], designated
    assert [r.way_id for r in records if r.byway_status not in (None, byways.DESIGNATED)] == []


def test_the_count_line_names_every_absence():
    """Ten ways, two zero classes, THREE gated, one declined sinuosity, no `points_of_interest` anywhere.

    The third gate is way 800000009's `motor_vehicle=no` (Gates.swift:161): `gated=2` is what dropping it
    would read as.
    """
    assert assemble.count_line(TABLE) == ("ASSEMBLE ways=10 zero_class=2 gated=3 "
                                          "sinuosity_declined=1 points_of_interest_absent=10 null_score=0")


def test_the_cli_writes_the_table_and_prints_the_counts(tmp_path, capsys):
    out = tmp_path / "scores.json"
    assert assemble.main(["--input", str(FIXTURE), "--out", str(out)]) == 0
    assert capsys.readouterr().out.strip() == assemble.count_line(TABLE)
    assert json.loads(out.read_text(encoding="utf-8"))["rows"] == TABLE


def test_a_producer_that_declines_refuses_the_way_by_name():
    """Ruling R10: no substitution. A rate of 0.0 would state 'this way is rural' about a way with no length."""
    row = dict(DOCUMENT["ways"][0])
    row["coords"] = [[37.1, -122.0], [37.1, -122.0]]
    with pytest.raises(ValueError, match="furniture_per_km declined"):
        assemble.record_from_row(row, [])
    without_class = dict(DOCUMENT["ways"][0], tags={"surface": "asphalt"})
    with pytest.raises(ValueError, match="no highway tag"):
        assemble.record_from_row(without_class, [])
