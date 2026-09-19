"""T-0208: the region reference table, and the bisect mid-rank that has to equal `ranks_against`.

WHY A SECOND RANKER AT ALL. `normalise.ranks_against` counts `below` and `equal` with a linear scan of the
reference for every way. Over the LA region's reference - about 550,000 values a term - that is 3e11
comparisons a term and would never finish, so `normalise_region` sorts each term once and ranks with
`bisect`. Two implementations of one formula are only safe while something makes them agree, so the first
test below is that: the same numbers, exactly, over a population with ties, a value below every reference
value, a value above every one, and a value equal to the smallest and to the largest.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from etl import normalise, region_reference, way_record
from etl.way_record import RANKED_TERMS

RAW_VALUES = [3.0, 1.0, 2.0, 2.0, 5.0, 2.0, 4.0, 1.0, 9.0, 7.0]
PROBES = {11: 0.5, 12: 1.0, 13: 2.0, 14: 2.5, 15: 9.0, 16: 12.0, 17: 2.0}


def record(way_id: int, highway: str = "tertiary", **over) -> way_record.WayRecord:
    fields = {"way_id": way_id, "highway": highway, "curvature": 1.0 * way_id, "elevation_gain": 2.0,
              "relief": 3.0, "sinuosity": 1.1, "furniture": 0.5, "canopy": 0.4, "impervious": 0.2,
              "water": 0.1, "speed_fit": 0.9}
    fields.update(over)
    return way_record.WayRecord(**fields)


def test_the_bisect_rank_equals_ranks_against_value_for_value():
    """THE BINDING. `ranks_against` is the definition; the sorted-reference form must be the same number.

    Not "close": the two are compared exactly, because a rank that drifts by 1e-16 per way is a rank that
    depends on which of two functions ran, which is the very thing this task exists to end.
    """
    from etl.normalise import ranks_against, ranks_against_sorted
    slow = ranks_against(PROBES, list(RAW_VALUES))
    fast = ranks_against_sorted(PROBES, sorted(RAW_VALUES))
    assert fast == slow
    assert set(fast) == set(PROBES)
    assert all(0.0 < value < 1.0 for value in fast.values())


def test_the_bisect_rank_is_not_vacuous_and_separates_the_probes():
    """If both sides returned the same constant the test above would pass. They do not."""
    from etl.normalise import ranks_against_sorted
    fast = ranks_against_sorted(PROBES, sorted(RAW_VALUES))
    assert fast[11] < fast[13] < fast[14] < fast[15] < fast[16]
    assert fast[13] == fast[17], "equal values take equal ranks"


def test_the_reference_is_the_ranking_population_and_not_the_whole_region():
    """R2: zero classes are out of the curve, and a way that declined sinuosity is out of THAT term only."""
    records = [record(1), record(2, highway="motorway"), record(3, sinuosity_declined=True)]
    values = region_reference.raw_values(records)
    assert set(values) == set(RANKED_TERMS)
    assert sorted(values["curvature"]) == [1, 3], "the motorway is not in the curve"
    assert sorted(values["curvature"].values()) == [1.0, 3.0]
    assert sorted(values["sinuosity"]) == [1], "the way that declined is out of the sinuosity term"
    assert sorted(values["sinuosity"].values()) == [1.1]


def test_a_way_documented_in_two_tiles_is_counted_once():
    """R1's dedup key: `way_id`, first tile in sorted tile order. A way counted twice weights the curve."""
    left = region_reference.raw_values([record(1), record(2)])
    right = region_reference.raw_values([record(2), record(3)])
    merged = region_reference.merge([left, right])
    assert sorted(merged["curvature"]) == [1.0, 2.0, 3.0]
    assert region_reference.table_of(merged)["curvature"] == [1.0, 2.0, 3.0]


def test_the_merge_takes_the_first_tiles_value_for_a_way_in_two_tiles():
    """The rule is stated and asserted, so a later merge cannot quietly become last-wins or max."""
    left = {"curvature": {7: 10.0}}
    right = {"curvature": {7: 99.0}}
    assert region_reference.merge([left, right])["curvature"] == {7: 10.0}


def test_the_table_is_sorted_and_its_digest_is_over_the_values_not_the_file():
    """The count and sha256 the Log quotes: a table that was re-ordered is a different reference."""
    table = region_reference.table_of({"curvature": {2: 5.0, 1: 1.0}, "relief": {1: 2.0}})
    assert table["curvature"] == [1.0, 5.0]
    expected = hashlib.sha256(json.dumps(table, sort_keys=True,
                                         separators=(",", ":")).encode("utf-8")).hexdigest()
    assert region_reference.digest(table) == expected
    assert region_reference.counts(table) == {"curvature": 2, "relief": 1}


def test_the_table_round_trips_through_the_file_the_run_writes(tmp_path):
    """`--reference` reads what the reference pass wrote, digest included."""
    table = region_reference.table_of({"curvature": {1: 1.0, 2: 2.0}, "relief": {1: 0.5}})
    path = tmp_path / "la-reference.json"
    region_reference.dump(table, path)
    back = region_reference.load(path)
    assert back == table
    assert region_reference.digest(back) == region_reference.digest(table)


def test_a_reference_the_normaliser_would_refuse_is_refused_here_too():
    """One vocabulary of refusal: `normalise.reference_refusals` is the judge, not a second opinion."""
    assert normalise.reference_refusals(region_reference.table_of({"curvature": {1: 1.0}})) == []
    with pytest.raises(ValueError):
        region_reference.dump({"not_a_term": [1.0]}, None)


def test_a_reference_file_that_cannot_be_ranked_against_is_refused_on_the_way_in(tmp_path):
    """Refused where it is READ too: a four-hour region pass must not start against an empty curve."""
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"curvature": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        region_reference.load(path)


def test_the_reference_must_be_sorted_before_it_is_bisected():
    """`normalise_region` sorts each term itself, so a caller's order cannot change a rank.

    `bisect` over an unsorted list returns a confident wrong answer rather than raising, which is the
    quietest way this whole design could have failed.
    """
    records = [record(1, curvature=5.0), record(2, curvature=1.0)]
    ordered = normalise.normalise_region(records, {"curvature": [1.0, 2.0, 3.0, 9.0]})
    jumbled = normalise.normalise_region(records, {"curvature": [9.0, 1.0, 3.0, 2.0]})
    assert [row.curvature for row in jumbled] == [row.curvature for row in ordered]
    assert len({row.curvature for row in ordered}) == 2, "the two ways must not share a rank here"
