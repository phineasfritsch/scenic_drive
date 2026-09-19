"""T-0204 R3: does the mixed street grid rank BELOW the canyon window?

THE PREDICATE, stated so it can be false: let `C10` be the canyon window's tenth row by the ranking
`etl.scenecheck.top` prints. The grid window's top ten rank below the canyon window's top ten iff every
one of the grid's ten `scenic_score_unit` values is strictly less than `C10`'s. The unit value and not the
0..10 integer, because the integer is a quantisation in which two ways 0.04 apart both read 7, and a tie
is not "below".

THE ANSWER ON THE REAL DATA IS NO, and this test is RED on purpose. Two Mulholland Drive segments inside
T-0204's window (ways 518410361 at 0.7361 and 787842196 at 0.7299) score above the canyon window's tenth
(way 1237332026, Fernwood Pacific Drive, 0.7284). T-0204's acceptance asked for this predicate; the run
produced fixtures that refute it. The finding is the deliverable - see the task Log and PR #113 - and the
test stays red until the index is changed or the acceptance is re-ruled by a task that measures again.
Deleting or loosening this test hides the one queued thing that can disconfirm the scenic index.

`test_the_predicate_can_hold` exists so the red above is a fact about the data and not about the test: the
same function passes on a window that really is below.
"""
from __future__ import annotations

import json
import pathlib

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
CANYON = FIXTURES / "canyon_top25.json"
GRID = FIXTURES / "grid_top25.json"
TOP_TEN = 10
UNIT = "scenic_score_unit"


def load(path: pathlib.Path) -> list:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)["rows"]


def outranking(grid_rows: list, canyon_rows: list) -> tuple:
    """The grid rows in the top ten that are NOT strictly below the canyon's tenth, with that bound."""
    bound = canyon_rows[TOP_TEN - 1][UNIT]
    return [row for row in grid_rows[:TOP_TEN] if row[UNIT] >= bound], bound


def test_the_predicate_can_hold():
    """Not vacuous: the same predicate passes on a window whose ten are all below the bound."""
    canyon = load(CANYON)
    below = [dict(row, **{UNIT: row[UNIT] - 0.2}) for row in load(GRID)]
    offenders, bound = outranking(below, canyon)
    assert bound > 0.0
    assert offenders == []


def test_the_grid_windows_top_ten_ranks_below_the_canyon_windows():
    canyon = load(CANYON)
    grid = load(GRID)
    offenders, bound = outranking(grid, canyon)
    named = ["%s (%s, way %d) %.4f" % (row["name"] or "<unnamed>", row["highway"], row["way_id"],
                                       row[UNIT]) for row in offenders]
    assert offenders == [], (
        "T-0204's acceptance is FALSE on the measured data: %d of the grid window's top ten are not "
        "below the canyon window's tenth (%.4f, %s): %s"
        % (len(offenders), bound, canyon[TOP_TEN - 1]["name"], "; ".join(named)))
