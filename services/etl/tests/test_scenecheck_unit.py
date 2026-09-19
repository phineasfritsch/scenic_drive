"""T-0204 R5: the UNIT the window predicate is read on, validated by the read-back oracle.

T-0204's whole acceptance is a comparison of `scenic_score_unit` values - the 0..10 integer is a four-bit
quantisation in which Topanga and a Brentwood residential street both read 7. So the number the predicate
is read on is the number that had no contract at all: `top()` did `float(tags.get(KEY_UNIT, detail) or 0.0)`
and would have ranked a way whose unit was missing (on its INTEGER, silently), `abc` (a ValueError out of
the ranking), `nan` (which compares false against every bound, so it sorts wherever the sort leaves it) or
`9.9` (a unit that is not a unit).

FIVE RULES, all in `classify`, so `counts` and `top` give the one answer they gave before:
absent on a scored way · not a real ASCII number · outside 0..1 · and - the binding one - a unit whose
`tagwriter.quantise` is not the integer beside it. The quantiser is IMPORTED AND CALLED, never restated:
a second copy of the rounding is how the writer and the checker agree with each other while both are wrong.

Every test here binds to the shipping symbols `etl.scenecheck.counts`, `.top` and `.main` - the entry point
`ops/sane` check 4 runs - over a read-back document, never to a helper.
"""
from __future__ import annotations

import pathlib

from etl import scenecheck, tagwriter

NODES = [(21, 34.0100, -118.70000), (22, 34.0110, -118.69900), (23, 34.0200, -118.69000)]

ARABIC_SEVEN = "٧"
ARABIC_UNIT = "٠.٦٥٤٣"  # 0.6543 in Arabic-Indic digits


def osm(tmp_path: pathlib.Path, ways: list, name: str) -> pathlib.Path:
    """A minimal read-back document with three nodes and the given ways: (id, tags)."""
    lines = ["<?xml version='1.0' encoding='UTF-8'?>", '<osm version="0.6" generator="test">']
    for node_id, lat, lon in NODES:
        lines.append('<node id="%d" version="1" lat="%.5f" lon="%.5f"/>' % (node_id, lat, lon))
    for way_id, tags in ways:
        body = "".join('<tag k="%s" v="%s"/>' % (k, v) for k, v in tags.items())
        refs = "".join('<nd ref="%d"/>' % n[0] for n in NODES)
        lines.append('<way id="%d" version="1">%s%s</way>' % (way_id, refs, body))
    lines.append("</osm>")
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def scored(**over) -> dict:
    """A well-formed scored way: 0.6543 quantises to the 7 beside it."""
    tags = {"highway": "tertiary", "name": "Latigo Canyon Road", "scenic_score": "7",
            "scenic_score_unit": "0.6543"}
    tags.update(over)
    return tags


def only_malformed(tmp_path: pathlib.Path, tags: dict, name: str) -> dict:
    """One good way and one suspect way; the counts the oracle gives for them."""
    path = osm(tmp_path, [(1, scored()), (2, tags)], name=name)
    return {"counts": scenecheck.counts(path), "ranked": [r["way_id"] for r in scenecheck.top(path, 5)],
            "exit": scenecheck.main([str(path), "--top", "0"]), "path": path}


def test_a_scored_way_with_no_unit_at_all_is_malformed_and_does_not_rank(tmp_path):
    """The ranking used to fall back to the INTEGER when the unit was absent, and say nothing."""
    tags = {"highway": "tertiary", "name": "Unitless Road", "scenic_score": "9"}
    out = only_malformed(tmp_path, tags, "no-unit.osm.xml")
    assert (out["counts"]["malformed"], out["counts"]["scored"]) == (1, 1)
    assert out["ranked"] == [1]
    assert out["exit"] == 4


def test_a_unit_that_is_not_a_number_names_the_way_instead_of_raising(tmp_path, capsys):
    """`float('abc')` out of `top()` is a crash, and a crash names nothing and ranks nothing."""
    out = only_malformed(tmp_path, scored(scenic_score_unit="abc"), "unit-abc.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["ranked"] == [1]
    assert out["exit"] == 4
    assert "scenic_score_unit=abc is not a number" in capsys.readouterr().err


def test_a_nan_unit_is_malformed_rather_than_sorted_wherever_the_sort_leaves_it(tmp_path):
    """NaN compares false against every bound, so a NaN unit is a row no predicate can rule on."""
    out = only_malformed(tmp_path, scored(scenic_score_unit="nan"), "unit-nan.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["ranked"] == [1]
    assert out["exit"] == 4


def test_a_unit_above_one_is_malformed(tmp_path):
    """`score.score` produces 0..1 and refuses anything else; 1.5 is not a unit score.

    1.5 beside a 10 and not 9.9 beside a 9, deliberately: the writer CLAMPS, so 1.5 quantises to the 10
    beside it and the pair agrees. Only the range clause can object to this way, so only this way tests it.
    """
    out = only_malformed(tmp_path, scored(scenic_score="10", scenic_score_unit="1.5000"),
                         "unit-high.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["exit"] == 4


def test_a_negative_unit_is_malformed(tmp_path):
    out = only_malformed(tmp_path, scored(scenic_score="0", scenic_score_unit="-0.2000"),
                         "unit-low.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["exit"] == 4


def test_a_unit_that_does_not_quantise_to_the_integer_beside_it_is_malformed(tmp_path, capsys):
    """The two tags are one fact written twice. A way whose pair disagrees is a way with two scores.

    This is the rule that found 17 real ways in T-0204's three read-backs (still-open 6): the writer takes
    the integer from the unrounded score and prints the unit at four decimals, so a score just under a
    `.x5` boundary ships as `0.5500` beside a `5`.
    """
    out = only_malformed(tmp_path, scored(scenic_score="6", scenic_score_unit="0.6543"),
                         "unit-mismatch.osm.xml")
    assert (out["counts"]["malformed"], out["counts"]["scored"]) == (1, 1)
    assert out["ranked"] == [1]
    assert out["exit"] == 4
    assert "quantises to 7, not the 6 beside it" in capsys.readouterr().err


def test_the_quantisation_is_the_writers_own_and_not_a_second_copy(tmp_path, monkeypatch):
    """Move the writer's rounding and the checker moves with it - the only binding an int allows.

    `0.6543` is a 7 under round-half-up of the score times ten. Scale by 100 and it is a 65, so a way
    tagged 7 becomes malformed WITHOUT this file changing: the checker calls `tagwriter.quantise`.
    """
    path = osm(tmp_path, [(1, scored())], name="quantiser.osm.xml")
    assert scenecheck.counts(path)["malformed"] == 0
    monkeypatch.setattr(tagwriter, "SCORE_SCALE", 100)
    assert scenecheck.counts(path)["malformed"] == 1


def test_a_non_ascii_digit_in_the_unit_is_not_a_number(tmp_path):
    """`float('٠.٥')` is 0.5 to Python. No producer of this file is allowed to write those bytes."""
    out = only_malformed(tmp_path, scored(scenic_score_unit=ARABIC_UNIT), "unit-arabic.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["ranked"] == [1]
    assert out["exit"] == 4


def test_a_non_ascii_digit_in_the_integer_is_not_a_number(tmp_path):
    """`int('٧')` is 7 to Python, and the same guard is why. The integer half of the same rule."""
    out = only_malformed(tmp_path, scored(scenic_score=ARABIC_SEVEN), "score-arabic.osm.xml")
    assert out["counts"]["malformed"] == 1
    assert out["ranked"] == [1]
    assert out["exit"] == 4


def test_the_integer_boundaries_are_the_two_values_just_outside_the_range(tmp_path):
    """11 and -1, not 42 and -3: an off-by-one bound is the bound a big number never tests."""
    for raw, unit in (("11", "1.0000"), ("-1", "0.0000")):
        out = only_malformed(tmp_path, scored(scenic_score=raw, scenic_score_unit=unit),
                             "boundary%s.osm.xml" % raw)
        assert out["counts"]["malformed"] == 1, raw
        assert out["exit"] == 4, raw


def test_the_two_values_just_inside_the_range_are_scored(tmp_path):
    """The other half of the boundary: 0 and 10 are scores the router holds, and they rank."""
    path = osm(tmp_path, [(1, scored(scenic_score="0", scenic_score_unit="0.0000")),
                          (2, scored(scenic_score="10", scenic_score_unit="1.0000"))],
               name="inside.osm.xml")
    found = scenecheck.counts(path)
    assert (found["malformed"], found["scored"]) == (0, 2)
    assert [row["way_id"] for row in scenecheck.top(path, 5)] == [2, 1]
    assert scenecheck.main([str(path), "--top", "0"]) == 0


def test_the_ranking_carries_the_unit_it_validated(tmp_path):
    """`top` reports the unit as a number, from the same tag `classify` ruled on."""
    path = osm(tmp_path, [(1, scored())], name="carried.osm.xml")
    row = scenecheck.top(path, 1)[0]
    assert row["scenic_score_unit"] == 0.6543
    assert row["scenic_score"] == tagwriter.quantise(row["scenic_score_unit"])
