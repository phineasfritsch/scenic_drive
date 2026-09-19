"""T-0208: a way clipped into two overlapping windows takes ONE score, or the index has a step at every seam.

THE DEFECT, MEASURED BY T-0204 (PR #113) AND NOT BY THIS FILE. `osmium extract` COMPLETES a way that crosses
a clip boundary, so the 190 ways on the -118.45 seam were scored in BOTH halves of the LA street grid - and
160 of them came out with different scores:

    way 1533792498  Mulholland Drive        grid-a 0.6988   grid-b 0.7022
    way 399301293   West Sunset Boulevard   grid-a 0.6308   grid-b 0.6372

Not truncated geometry: the rows are identical. `normalise_region` ranks a way against WHATEVER ELSE LANDED
IN THE SAME CLIP, and half a city is a different curve from the other half.

WHAT THIS FILE BINDS TO. `assemble.assemble` - the symbol `python -m etl.assemble` runs, which is what the
region build runs - over two documents cut from T-0204's OWN grid-a and grid-b docs. The three shared ways
are taken from the 92 seam rows that are BYTE-IDENTICAL in both, so the two windows disagree about nothing
except their populations; the other nine ways in each window are that clip's own, so the populations really
do differ. Both of T-0204's named ways are in the 92 and both are in the fixture, by id.

The reference is built the way the region run builds it - `region_reference.raw_values` over the records
`assemble.record_from_row` produces, merged by `way_id` - so this test exercises the composition that ships,
not a hand-written distribution.
"""
from __future__ import annotations

import json
import pathlib

from etl import assemble, region_reference

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
WINDOW_A = FIXTURES / "seam_window_a.json"
WINDOW_B = FIXTURES / "seam_window_b.json"

MULHOLLAND = 1533792498
WEST_SUNSET = 399301293


def document(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def reference_over(*documents) -> dict:
    """The region reference, over the union of the windows - built through the shipping functions."""
    tables = []
    for doc in documents:
        records = [assemble.record_from_row(row, []) for row in doc["ways"]]
        tables.append(region_reference.raw_values(records))
    return region_reference.table_of(region_reference.merge(tables))


def scores(doc: dict, reference=None) -> dict:
    rows = assemble.assemble(doc, reference) if reference is not None else assemble.assemble(doc)
    return {row["way_id"]: row["score"] for row in rows}


def shared_ids(left: dict, right: dict) -> list:
    return sorted(set(left) & set(right))


def test_the_two_windows_really_do_overlap_on_the_named_seam_ways():
    """The fixture's own shape: a test about a seam needs a seam, and these are T-0204's ways by id."""
    left, right = document(WINDOW_A), document(WINDOW_B)
    both = shared_ids({row["way_id"]: row for row in left["ways"]},
                      {row["way_id"]: row for row in right["ways"]})
    assert MULHOLLAND in both
    assert WEST_SUNSET in both
    assert len(left["ways"]) > len(both) and len(right["ways"]) > len(both), "the populations must differ"


def test_a_way_in_two_overlapping_windows_takes_one_score_against_the_region_reference():
    """THE FIX, as a property of the shipping entry point: one reference, one score, every shared way."""
    left, right = document(WINDOW_A), document(WINDOW_B)
    reference = reference_over(left, right)
    a, b = scores(left, reference), scores(right, reference)
    shared = shared_ids(a, b)
    assert shared, "the two windows share no way, so this test binds nothing"
    differing = {way_id: (a[way_id], b[way_id]) for way_id in shared if a[way_id] != b[way_id]}
    assert differing == {}, (
        "a way scored in two windows against ONE reference still takes two scores: %s" % differing)


def test_the_two_named_ways_are_the_ones_the_measurement_named():
    """Named, not counted: the two ways T-0204 printed are each one number under the reference."""
    left, right = document(WINDOW_A), document(WINDOW_B)
    reference = reference_over(left, right)
    a, b = scores(left, reference), scores(right, reference)
    assert a[MULHOLLAND] == b[MULHOLLAND]
    assert a[WEST_SUNSET] == b[WEST_SUNSET]


def test_without_a_region_reference_the_same_ways_take_two_scores():
    """NOT VACUOUS: the same fixtures through the same symbol, each window ranked against itself.

    This is T-0204's finding, kept asserted rather than kept in prose. If it ever stops failing to agree,
    the fixture has lost the population difference that makes the test above mean anything.
    """
    left, right = document(WINDOW_A), document(WINDOW_B)
    a, b = scores(left), scores(right)
    differing = [way_id for way_id in shared_ids(a, b) if a[way_id] != b[way_id]]
    assert MULHOLLAND in differing
    assert WEST_SUNSET in differing
