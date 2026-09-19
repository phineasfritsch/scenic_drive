"""T-0204: which ways reach the canyon window's tenth score - as a WHITELIST, over the measured fixtures.

THE HISTORY, because this file is the record of a refutation. T-0204's acceptance said "every one of the
grid window's top ten scores BELOW the canyon window's tenth (0.7284)". That predicate is FALSE on the real
data, and the run that measured it shipped it red: two Mulholland Drive ridge segments (ways 518410361 at
0.7361 and 787842196 at 0.7299) sit inside the grid bbox because its northern edge (34.15) runs along the
Santa Monica Mountains crest, so the "mixed street grid" window CONTAINS canyon-rim road.

THE ORCHESTRATOR'S RULING (agent/claude-fable-5-1, the filer of the task, quoted in the task Log): the
acceptance was mis-specified by its filer, the finding stands as written and is not hidden, and the test
becomes the WHITELIST form of the same fact - CLAUDE.md, "anchor a guard on a WHITELIST ... never on a
blacklist". The ONLY grid-window ways at or above the canyon window's tenth are the ridge segments named in
`RIDGE_ALLOWLIST`; ANY other way that reaches the bound - a Westwood, Brentwood or Bel Air street, a fire
road, a newly re-scored Mulholland segment - turns this file RED BY NAME. The refutation is therefore
still asserted (the two ways are named, in the open, and no third one may join them quietly) and the suite
is green, so a later regression is visible instead of being hidden under a test that was already red.

WHAT IS PINNED, all of it on identifiers and measured numbers and none of it on a comment: the bound's WAY
ID and its value; the allowlist's IDS AND NAMES; 25 rows per fixture with contiguous ranks in descending
unit order; a TIE at the bound counting as NOT below; and the SHAPE of a fixture row tied to the shipping
symbol `etl.scenecheck.top` over a committed read-back, so these fixtures cannot drift away from what the
oracle actually produces.

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

# The canyon window's tenth row, measured: way 1237332026, Fernwood Pacific Drive, 0.7284.
BOUND_WAY_ID = 1237332026
BOUND_NAME = "Fernwood Pacific Drive"
BOUND_UNIT = 0.7284

# THE WHITELIST. Every way allowed to reach the bound, by id AND by name. Today exactly the two ridge
# segments the run found; anything else at or above the bound is a failure that names the way.
RIDGE_ALLOWLIST = {518410361: "Mulholland Drive", 787842196: "Mulholland Drive"}

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


def test_the_only_grid_ways_reaching_the_bound_are_the_named_ridge_segments():
    """THE WHITELIST. Any other way at or above 0.7284 is red, by id and by name.

    This is the refutation of T-0204's acceptance, kept asserted rather than kept red: the two ways that
    outrank Fernwood Pacific are named here, and a third one - or a Westwood street, or a fire road -
    cannot join them without this test saying which way it is.
    """
    offenders = at_or_above(load(GRID)["rows"], BOUND_UNIT)
    assert {row["way_id"] for row in offenders} == set(RIDGE_ALLOWLIST), (
        "the grid window's ways at or above the canyon window's tenth (%.4f, %s) are no longer exactly "
        "the allowlisted ridge segments: %s" % (BOUND_UNIT, BOUND_NAME, named(offenders)))
    assert {row["way_id"]: row["name"] for row in offenders} == RIDGE_ALLOWLIST, (
        "an allowlisted way id is not the road it was allowed for: %s" % named(offenders))


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


def test_the_predicate_can_hold():
    """Not vacuous: the same read finds nothing on a window whose ten really are all below the bound."""
    below = [dict(row, **{UNIT: round(row[UNIT] - 0.2, 4)}) for row in load(GRID)["rows"]]
    assert at_or_above(below, BOUND_UNIT) == []


def test_the_seam_merge_rule_is_recorded_and_the_rows_obey_it():
    """R2's rule: an overlapping way is taken at the MAX of its two clips, never at the author's choice."""
    grid = load(GRID)
    assert "max" in grid["meta"]["seam_merge"].lower()
    rows = {row["way_id"]: row for row in grid["rows"]}
    checked = 0
    for seam in grid["meta"]["seam_disagreements"]:
        row = rows.get(seam["way_id"])
        if row is not None:
            assert abs(row[UNIT] - max(seam["grid_a"], seam["grid_b"])) < EXACT, seam
            checked += 1
    assert checked == len([s for s in grid["meta"]["seam_disagreements"] if s["way_id"] in rows])


def test_the_fixture_row_is_the_shape_the_shipping_oracle_produces(tmp_path):
    """BINDING: the fixtures are what `etl.scenecheck.top` - the symbol `ops/sane` runs - produces.

    Over a COMMITTED READ-BACK cut from the canyon window's own `window-readback.osm.xml` (four real ways
    with their own nodes and their shipped `scenic_*` tags), not over a hand-written table. A fixture whose
    fields drifted from the oracle's would make every assertion above a statement about a JSON file.
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
