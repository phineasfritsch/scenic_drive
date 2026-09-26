"""T-0204/T-0208: which ways reach the canyon window's tenth score - as a WHITELIST, over the fixtures.

THE HISTORY, because this file is the record of a refutation AND of its repair. T-0204's acceptance said
"every one of the grid window's top ten scores BELOW the canyon window's tenth". That predicate was FALSE
on T-0204's data: two Mulholland Drive ridge segments (ways 518410361 and 787842196) sit inside the grid
bbox because its northern edge (34.15) runs along the Santa Monica Mountains crest, so the "mixed street
grid" window CONTAINS canyon-rim road. The orchestrator ruled that the finding stands and that the test
becomes the WHITELIST form of the same fact - CLAUDE.md, "anchor a guard on a WHITELIST ... never on a
blacklist" - and `RIDGE_ALLOWLIST` named the two ways so that no third could join them quietly.

WHAT T-0208 CHANGED, and why the allowlist is now EMPTY. Every score T-0204 ranked was computed against
the ways that happened to land in its own clip; T-0208 ranks the whole region against ONE reference. Under
it the two ridge segments are still the grid window's two best roads - they have not been re-ranked away,
and `test_the_two_mulholland_ridge_segments_...` names them and asserts exactly that - but neither reaches
the canyon window's tenth any more. The allowlist therefore SHRINKS TO NOTHING. It was re-derived from the
measurement, never re-ranked to keep a way in it (T-0208 R4), and `RIDGE_ALLOWLIST` is kept as the shape
this guard has so that a way climbing back over the bound is a named failure rather than a silent one.

AN EMPTY WHITELIST IS A PREDICATE THAT CAN PASS OVER NOTHING, so two other tests carry its weight:
`test_the_read_finds_a_way_that_reaches_the_bound` raises the grid rows over the bound and requires all
ten to be found, and `test_a_tie_at_the_bound_counts_as_not_below` requires the tie fixture's one raised
way to be found. The read is shown to work in both directions before it is believed when it finds nothing.

WHAT IS PINNED, all of it on identifiers and measured numbers and none of it on a comment: the bound's WAY
ID and its value; the two ridge ids and names; 25 rows per fixture with contiguous ranks in descending unit
order; a TIE at the bound counting as NOT below; the 190 seam ways and their agreement; and the SHAPE of a
fixture row tied to the shipping symbol `etl.scenecheck.top` over a committed read-back.

THE RANKING IS BY `scenic_score_unit`, NEVER BY POSITION IN THE FILE: every read below sorts. A fixture
re-recorded in another order, or sorted by way id, cannot make the predicate true.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from etl import scenecheck

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
CANYON = FIXTURES / "canyon_top25.json"
GRID = FIXTURES / "grid_top25.json"
TIE = FIXTURES / "grid_tie_top25.json"
SAMPLE = FIXTURES / "window_readback_sample.osm.xml"

TOP_TEN = 10
FIXTURE_ROWS = 25
UNIT = "scenic_score_unit"
ROW_FIELDS = {"way_id", "name", "highway", "lat", "lon", "scenic_score", UNIT, "rank"}

# The canyon window's tenth row, measured over la-tagged.osm.pbf: way 13409451, 0.7594.
# T-0204 measured 1237332026 Fernwood Pacific Drive 0.7284 against its own clip's population.
BOUND_WAY_ID = 13409451
BOUND_NAME = "South Topanga Canyon Boulevard"
BOUND_UNIT = 0.7594

# THE WHITELIST. Every way allowed to reach the bound, by id AND by name. Under the region reference that
# is NO WAY AT ALL; anything at or above the bound is a failure that names the way.
RIDGE_ALLOWLIST: dict = {}

# The two ways the allowlist used to hold: still the grid window's best, now below the bound. Measured.
RIDGE_WAYS = {518410361: "Mulholland Drive", 787842196: "Mulholland Drive"}
RIDGE_BEST_UNIT = 0.7325

# The seam T-0208 exists for: the ways `osmium extract` completes into BOTH halves of the grid window.
SEAM_WAYS = 190
# The two the Brief named, with the one score each now carries in both halves (T-0204: 0.6988 vs 0.7022
# and 0.6308 vs 0.6372).
NAMED_SEAM = {1533792498: 0.6952, 399301293: 0.6203}

EXACT = 1e-9


def load(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ranked(rows: list) -> list:
    """The rows in the order the unit puts them in, best first. Never the order they are stored in."""
    return sorted(rows, key=lambda row: (-row[UNIT], row["way_id"]))


def bound_row(canyon_rows: list) -> dict:
    return ranked(canyon_rows)[TOP_TEN - 1]


def at_or_above(rows: list, bound: float) -> list:
    """The top ten by unit that are NOT strictly below the bound. A tie is not below - hence `>=`."""
    return [row for row in ranked(rows)[:TOP_TEN] if row[UNIT] >= bound]


def named(rows: list) -> str:
    return "; ".join("%s (%s, way %d) %.4f" % (row["name"] or "<unnamed>", row["highway"], row["way_id"],
                                               row[UNIT]) for row in rows)


@pytest.mark.parametrize("path", [CANYON, GRID, TIE], ids=["canyon", "grid", "tie"])
def test_each_fixture_is_twenty_five_rows_ranked_contiguously_and_descending_by_the_unit(path):
    """The fixture's own shape, so the reads below cannot be answered by a truncated or reordered file."""
    rows = load(path)["rows"]
    assert len(rows) == FIXTURE_ROWS
    assert [row["rank"] for row in rows] == list(range(1, FIXTURE_ROWS + 1))
    assert all(set(row) == ROW_FIELDS for row in rows)
    units = [row[UNIT] for row in rows]
    assert units == sorted(units, reverse=True)
    assert [row["way_id"] for row in rows] == [row["way_id"] for row in ranked(rows)]


def test_the_bound_is_the_canyon_windows_tenth_way_by_the_unit_and_its_measured_value():
    """The bound is pinned to a WAY and a NUMBER, so a re-recorded canyon fixture cannot move it silently."""
    row = bound_row(load(CANYON)["rows"])
    assert row["way_id"] == BOUND_WAY_ID
    assert row["name"] == BOUND_NAME
    assert abs(row[UNIT] - BOUND_UNIT) < EXACT


def test_no_grid_way_reaches_the_bound_except_the_allowlisted_ones():
    """THE WHITELIST. Any way at or above 0.7594 is red, by id and by name.

    T-0204's refutation is kept asserted rather than kept red, and under one region normalisation
    population the allowlist it needed is empty: no way of the mixed grid window reaches the canyon
    window's tenth. A Westwood street, a fire road, or a re-scored Mulholland segment climbing over the
    bound cannot happen without this test saying which way it is.
    """
    offenders = at_or_above(load(GRID)["rows"], BOUND_UNIT)
    assert {row["way_id"] for row in offenders} == set(RIDGE_ALLOWLIST), (
        "the grid window's ways at or above the canyon window's tenth (%.4f, %s) are no longer exactly "
        "the allowlisted ways: %s" % (BOUND_UNIT, BOUND_NAME, named(offenders)))
    assert {row["way_id"]: row["name"] for row in offenders} == RIDGE_ALLOWLIST, (
        "an allowlisted way id is not the road it was allowed for: %s" % named(offenders))


def test_the_two_mulholland_ridge_segments_are_still_the_grid_windows_best_and_are_now_below_the_bound():
    """The allowlist shrank because the SCORES moved, not because the ways were ranked away.

    Both ways T-0204 named are still in the grid window's top ten - the crest is still inside the bbox and
    it is still the best road in it - and both are now strictly below the canyon window's tenth. If a
    future change drops them out of the window, or pushes them back over the bound, this names them.
    """
    rows = ranked(load(GRID)["rows"])[:TOP_TEN]
    found = {row["way_id"]: row for row in rows if row["way_id"] in RIDGE_WAYS}
    assert {way_id: row["name"] for way_id, row in found.items()} == RIDGE_WAYS, named(rows)
    assert all(row[UNIT] < BOUND_UNIT for row in found.values()), named(list(found.values()))
    assert abs(max(row[UNIT] for row in found.values()) - RIDGE_BEST_UNIT) < EXACT


def test_the_bound_the_whitelist_is_read_against_is_the_canyon_fixtures_own_tenth():
    """The two numbers are one number: the literal above and the measured row are the same value."""
    assert abs(bound_row(load(CANYON)["rows"])[UNIT] - BOUND_UNIT) < EXACT


def test_a_tie_at_the_bound_counts_as_not_below():
    """`>=`, not `>`: T-0204 R3 ruled that a tie is not "below", and the acceptance word was BELOW."""
    tie = load(TIE)
    way_id = tie["meta"]["tie_way_id"]
    rows = tie["rows"]
    tied = [row for row in rows if row["way_id"] == way_id]
    assert [abs(row[UNIT] - BOUND_UNIT) < EXACT for row in tied] == [True]
    offenders = at_or_above(rows, BOUND_UNIT)
    assert [row["way_id"] for row in offenders] == [way_id], named(offenders)


def test_the_read_finds_a_way_that_reaches_the_bound():
    """Not vacuous: the same read that finds nothing on the grid finds all ten when they are over it.

    The allowlist is empty, so `test_no_grid_way_reaches_the_bound_...` is a predicate about an empty set
    and would pass over a read that can never find anything. This is the direction that proves it can.
    """
    over = [dict(row, **{UNIT: round(row[UNIT] + 0.2, 4)}) for row in load(GRID)["rows"]]
    assert len(at_or_above(over, BOUND_UNIT)) == TOP_TEN
    below = [dict(row, **{UNIT: round(row[UNIT] - 0.2, 4)}) for row in load(GRID)["rows"]]
    assert at_or_above(below, BOUND_UNIT) == []


def test_the_seam_ways_are_recorded_and_every_one_of_them_carries_ONE_score():
    """T-0208's whole point, over the population the fixture names rather than over a rule's wording.

    `osmium extract` completes every way crossing -118.45, so the grid window's two halves are read back
    with 190 ways in common. T-0204 measured 160 of them carrying DIFFERENT scores and had to arbitrate
    with a MAX; under one region reference there is nothing to arbitrate. `seam_ways` records all 190 with
    BOTH halves' units - an empty list would make this test pass over nothing, so its length is pinned.
    """
    grid = load(GRID)
    seam = grid["meta"]["seam_ways"]
    assert len(seam) == SEAM_WAYS
    assert grid["meta"]["seam_differ"] == 0
    assert [entry for entry in seam if entry["grid_a"] != entry["grid_b"]] == []
    rows = {row["way_id"]: row for row in grid["rows"]}
    for entry in seam:
        row = rows.get(entry["way_id"])
        if row is not None:
            assert abs(row[UNIT] - entry["grid_a"]) < EXACT, entry
    measured = {entry["way_id"]: entry for entry in seam if entry["way_id"] in NAMED_SEAM}
    assert set(measured) == set(NAMED_SEAM), "the two ways the Brief named are not on the seam any more"
    for way_id, expected in NAMED_SEAM.items():
        assert abs(measured[way_id]["grid_a"] - expected) < EXACT, measured[way_id]
        assert abs(measured[way_id]["grid_b"] - expected) < EXACT, measured[way_id]


def test_the_fixture_row_is_the_shape_the_shipping_oracle_produces(tmp_path):
    """BINDING: the fixtures are what `etl.scenecheck.top` - the symbol `ops/sane` runs - produces.

    Over a COMMITTED READ-BACK cut from the canyon window's own read-back of `la-tagged.osm.pbf` (four
    real ways with their own nodes and their shipped `scenic_*` tags), not over a hand-written table. A
    fixture whose fields drifted from the oracle's would make every assertion above a statement about a
    JSON file.
    """
    rows = scenecheck.top(SAMPLE, TOP_TEN)
    assert rows, "the committed read-back sample ranks nothing"
    assert all(set(row) == ROW_FIELDS for row in rows)
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))
    units = [row[UNIT] for row in rows]
    assert units == sorted(units, reverse=True)
    assert scenecheck.counts(SAMPLE)["malformed"] == 0
    canyon = {row["way_id"]: row for row in load(CANYON)["rows"]}
    shared = [row for row in rows if row["way_id"] in canyon]
    assert shared, "the sample shares no way with the canyon fixture, so it binds nothing"
    for row in shared:
        assert abs(row[UNIT] - canyon[row["way_id"]][UNIT]) < EXACT
        assert row["name"] == canyon[row["way_id"]]["name"]
