"""T-0208: a way clipped into two overlapping windows takes ONE score, or the index has a step at every seam.

THE DEFECT, MEASURED BY T-0204 (PR #113) AND NOT BY THIS FILE. `osmium extract` COMPLETES a way that crosses
a clip boundary, so the 190 ways on the -118.45 seam were scored in BOTH halves of the LA street grid - and
160 of them came out with different scores:

    way 1533792498  Mulholland Drive        grid-a 0.6988   grid-b 0.7022
    way 399301293   West Sunset Boulevard   grid-a 0.6308   grid-b 0.6372

Not truncated geometry: the rows are identical. `normalise_region` ranks a way against WHATEVER ELSE LANDED
IN THE SAME CLIP, and half a city is a different curve from the other half.

WHAT THIS FILE BINDS TO. `assemble.main` - the entry point `python -m etl.assemble` runs, and the one the
region build's second pass ran on all 152 tiles with `--reference` - through a document on disk, a reference
file written by `region_reference.dump`, and the scored table it writes (rv1-t0208 B1: a test that stopped
at `assemble.assemble` stayed green while `main` dropped the flag). The library-level tests below it pin
the same property one layer down. The fixtures are two documents cut from T-0204's OWN grid-a and grid-b
docs. The three shared ways are taken from the 92 seam rows that are BYTE-IDENTICAL in both, so the two
windows disagree about nothing except their populations; the other nine ways in each window are that clip's
own, so the populations really do differ. Both of T-0204's named ways are in the 92 and both are in the
fixture, by id.

The reference is built the way the region run builds it - `region_reference.raw_values` over the records
`assemble.record_from_row` produces, merged by `way_id` - so this test exercises the composition that ships,
not a hand-written distribution.
"""
from __future__ import annotations

import json
import pathlib
import shutil

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


def cli_scores(tmp_path: pathlib.Path, window: pathlib.Path, *flags) -> dict:
    """`python -m etl.assemble` as pass 2 ran it: a document on disk in, the scored table on disk out."""
    source = tmp_path / window.name
    shutil.copyfile(window, source)
    out = tmp_path / (window.stem + "-scores.json")
    assert assemble.main(["--input", str(source), "--out", str(out)] + list(flags)) == 0
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    return {row["way_id"]: row["score"] for row in rows}


def test_the_cli_with_a_region_reference_gives_a_way_in_two_windows_one_score(tmp_path):
    """THE FIX, through the shipping entry point: `main --reference` on each window, one score per shared way."""
    reference = tmp_path / "la-reference.json"
    region_reference.dump(reference_over(document(WINDOW_A), document(WINDOW_B)), reference)
    a = cli_scores(tmp_path, WINDOW_A, "--reference", str(reference))
    b = cli_scores(tmp_path, WINDOW_B, "--reference", str(reference))
    shared = shared_ids(a, b)
    assert MULHOLLAND in shared and WEST_SUNSET in shared, "the CLI tables lost the named seam ways"
    differing = {way_id: (a[way_id], b[way_id]) for way_id in shared if a[way_id] != b[way_id]}
    assert differing == {}, (
        "python -m etl.assemble --reference still gives a way in two windows two scores: %s" % differing)


def test_the_cli_without_a_reference_ranks_one_self_contained_window_against_itself(tmp_path):
    """The flag's OTHER path: no `--reference` is the per-window ranking, right for one self-contained document.

    Equal to the library's no-reference answer, window by window, and - the same fixtures, so not vacuous -
    Mulholland still takes two scores, which is what the flag exists to end.
    """
    a = cli_scores(tmp_path, WINDOW_A)
    b = cli_scores(tmp_path, WINDOW_B)
    assert a == scores(document(WINDOW_A))
    assert b == scores(document(WINDOW_B))
    assert a[MULHOLLAND] != b[MULHOLLAND]


def test_the_two_windows_really_do_overlap_on_the_named_seam_ways():
    """The fixture's own shape: a test about a seam needs a seam, and these are T-0204's ways by id."""
    left, right = document(WINDOW_A), document(WINDOW_B)
    both = shared_ids({row["way_id"]: row for row in left["ways"]},
                      {row["way_id"]: row for row in right["ways"]})
    assert MULHOLLAND in both
    assert WEST_SUNSET in both
    assert len(left["ways"]) > len(both) and len(right["ways"]) > len(both), "the populations must differ"


def test_a_way_in_two_overlapping_windows_takes_one_score_against_the_region_reference():
    """THE FIX one layer down, at `assemble.assemble`: one reference, one score, every shared way."""
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
