"""`ops/sane` check 4 over the file that ships: both clauses as numbers, and a refusal on either.

The clauses are the plan's, and this module is where they are first computed over a real tagged extract:
no road may be left without a score, and nothing the safety gates refuse - nor a motorway or trunk - may
carry a score above 0.
"""
from __future__ import annotations

import pathlib

from etl import assemble, byways, scenecheck, tagwriter

NODES = [(21, 34.0100, -118.70000), (22, 34.0110, -118.69900), (23, 34.0200, -118.69000)]


def osm(tmp_path: pathlib.Path, ways: list, name: str = "tagged.osm.xml") -> pathlib.Path:
    """A minimal OSM XML document with three nodes and the given ways: (id, tags)."""
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
    tags = {"highway": "tertiary", "name": "Latigo Canyon Road", "scenic_score": "7",
            "scenic_score_unit": "0.6543"}
    tags.update(over)
    return tags


def test_a_road_with_no_score_is_counted_as_a_number_and_refuses(tmp_path):
    """Clause one: a way that should have a score and has none. The count is the answer, not a message."""
    path = osm(tmp_path, [(1, scored()), (2, {"highway": "secondary", "name": "Mulholland Highway"})])
    counts = scenecheck.counts(path)
    assert counts["null_score"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_motorway_with_a_score_above_zero_is_counted_as_a_number_and_refuses(tmp_path):
    """Clause two, the class half: motorway and trunk score 0 - that is the invariant, not an opinion."""
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="motorway", scenic_score="3"))])
    counts = scenecheck.counts(path)
    assert counts["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_private_way_with_a_score_above_zero_is_counted_and_refuses(tmp_path):
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="residential", access="private"))])
    assert scenecheck.counts(path)["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_an_unpaved_way_with_a_score_above_zero_is_counted_and_refuses(tmp_path):
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="unclassified", surface="gravel"))])
    assert scenecheck.counts(path)["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_track_with_a_score_above_zero_is_counted_and_refuses(tmp_path):
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="track"))])
    assert scenecheck.counts(path)["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_motorway_at_the_smallest_score_above_zero_is_counted_and_refuses(tmp_path):
    """The clause is `> 0`, not `> a threshold`, and 1 is the score that says so.

    Every other gated fixture in this file carries 3 (the motorway) or 7 (private, gravel, track), so a
    checker that only objected above 1 - or above 2, or 5 - would count every one of them and still let a
    shipped PBF through with a motorway at 1. The smallest violation is the one that has to be counted.
    """
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="motorway", scenic_score="1"))])
    assert scenecheck.counts(path)["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_private_way_at_the_smallest_score_above_zero_is_counted_and_refuses(tmp_path):
    """The gate half of the same boundary: `access=private` at 1 is a violation, not a rounding artefact."""
    path = osm(tmp_path, [(1, scored()),
                          (2, scored(highway="residential", access="private", scenic_score="1"))])
    assert scenecheck.counts(path)["gated_scored"] == 1
    assert scenecheck.main([str(path)]) == 4


def test_a_gated_way_scored_zero_is_not_a_violation(tmp_path):
    """The gates force 0.0; 0 is what a refused-for-safety road is allowed to carry."""
    path = osm(tmp_path, [(1, scored()),
                          (2, scored(highway="track", scenic_score="0", scenic_gate="track"))])
    assert scenecheck.counts(path)["gated_scored"] == 0
    assert scenecheck.main([str(path)]) == 0


def test_a_refused_way_is_not_counted_as_a_null_score(tmp_path):
    """Ruling R2: `scenic_refused=1` is a way that should NOT have a score, so it is not a hole."""
    path = osm(tmp_path, [(1, scored()),
                          (2, {"highway": "unclassified", "scenic_refused": "1",
                               "scenic_refused_why": "dem: no elevation sample"})])
    counts = scenecheck.counts(path)
    assert counts["null_score"] == 0
    assert counts["refused"] == 1
    assert scenecheck.main([str(path)]) == 0


def test_a_way_with_no_highway_tag_is_counted_as_neither(tmp_path):
    """A park is not a road. It is not a null score and it is not a refusal."""
    path = osm(tmp_path, [(1, scored()), (2, {"leisure": "park", "name": "Malibu Creek State Park"})])
    counts = scenecheck.counts(path)
    assert (counts["null_score"], counts["refused"], counts["not_a_road"]) == (0, 0, 1)


def test_a_clean_file_reports_both_clauses_zero_and_exits_zero(tmp_path, capsys):
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="motorway", scenic_score="0"))])
    assert scenecheck.main([str(path)]) == 0
    assert capsys.readouterr().out.splitlines()[0] == \
        "CHECK4 null_score=0 gated_scored=0 malformed=0 scored=2 refused=0 not_a_road=0"


def test_the_top_ten_ranks_by_score_and_names_each_way_its_class_and_one_coordinate(tmp_path):
    path = osm(tmp_path, [(1, scored(scenic_score="7", scenic_score_unit="0.6543")),
                          (2, scored(name="Decker Canyon Road", scenic_score="9",
                                     scenic_score_unit="0.8800")),
                          (3, scored(name="Fernwood Pacific Drive", scenic_score="5",
                                     scenic_score_unit="0.4500"))])
    top = scenecheck.top(path, 2)
    assert [r["name"] for r in top] == ["Decker Canyon Road", "Latigo Canyon Road"]
    assert [r["scenic_score"] for r in top] == [9, 7]
    assert top[0]["highway"] == "tertiary"
    assert (round(top[0]["lat"], 5), round(top[0]["lon"], 5)) == (34.0110, -118.69900)
    assert "Decker Canyon Road" in scenecheck.format_top(top)


def test_an_unnamed_way_still_appears_in_the_ranking(tmp_path):
    """A road without a name is still a road; leaving it out would flatter the list."""
    path = osm(tmp_path, [(1, {"highway": "tertiary", "scenic_score": "8", "scenic_score_unit": "0.7500"})])
    assert scenecheck.top(path, 5)[0]["name"] == ""


def test_the_gate_rules_are_the_assemblys_own_and_not_a_second_copy(tmp_path):
    """Two copies of a gate is how two answers for one road reach the corpus."""
    assert scenecheck.gate_reason is assemble.gate_reason
    assert scenecheck.ZERO_CLASSES is byways.SCENIC_ZERO_CLASSES


# --- T-0204: the read-back oracle's own contract (rv1-pr111's three recordables, ruling R1) ---------------
# The writer clamps to 0..10; the CHECKER reads the bytes that ship and may not assume the writer wrote them.


def test_a_score_above_the_range_the_router_holds_is_malformed_and_does_not_rank(tmp_path):
    """A tertiary tagged 42 was counted as `scored` and ranked #1 in the read the owner makes."""
    path = osm(tmp_path, [(1, scored()), (2, scored(name="Overbright Street", scenic_score="42"))])
    found = scenecheck.counts(path)
    assert (found["malformed"], found["scored"]) == (1, 1)
    assert [row["way_id"] for row in scenecheck.top(path, 5)] == [1]
    assert scenecheck.main([str(path)]) == 4


def test_a_negative_score_is_malformed_and_does_not_slip_past_the_gate_clause(tmp_path):
    """A motorway at -3 cleared clause 2, because `-3 > 0` is false - the gate saw nothing to object to."""
    path = osm(tmp_path, [(1, scored()), (2, scored(highway="motorway", scenic_score="-3"))])
    found = scenecheck.counts(path)
    assert (found["malformed"], found["gated_scored"], found["scored"]) == (1, 0, 1)
    assert scenecheck.main([str(path)]) == 4


def test_a_non_integer_score_names_the_way_instead_of_raising(tmp_path, capsys):
    """`int('7.5')` was a ValueError out of the oracle: a crash is not a refusal, and it names nothing."""
    path = osm(tmp_path, [(1, scored()), (2, scored(scenic_score="7.5")),
                          (3, scored(scenic_score="abc"))])
    found = scenecheck.counts(path)
    assert found["malformed"] == 2
    assert scenecheck.main([str(path)]) == 4
    err = capsys.readouterr().err
    assert "way 2 scenic_score=7.5" in err
    assert "way 3 scenic_score=abc" in err


def test_a_way_that_is_both_refused_and_scored_gets_one_answer_from_both_halves(tmp_path):
    """Two halves, two answers: `counts` called it refused and skipped it while `top` ranked it.

    Ruling R2 of T-0168 says a refused way carries NO score, so a way carrying both is neither refused nor
    scored - it is malformed, in the counts and in the ranking, because both ask the same `classify`.
    """
    path = osm(tmp_path, [(1, scored()),
                          (2, scored(name="Contradiction Road", scenic_score="9",
                                     scenic_score_unit="0.9900", scenic_refused="1",
                                     scenic_refused_why="dem: no elevation sample"))])
    found = scenecheck.counts(path)
    assert (found["malformed"], found["refused"], found["scored"]) == (1, 0, 1)
    assert [row["way_id"] for row in scenecheck.top(path, 5)] == [1]
    assert scenecheck.main([str(path)]) == 4


def test_the_range_is_the_writers_own_and_not_a_second_copy(tmp_path, monkeypatch):
    """The bounds are READ FROM `tagwriter` at call time, not copied into this module.

    An int cannot be asserted with `is` the way `gate_reason` is (0 and 10 are interned), so the binding is
    demonstrated the only way that means anything: move the writer's bound and the checker moves with it.
    """
    path = osm(tmp_path, [(1, scored(scenic_score="12", scenic_score_unit="1.2000"))])
    assert scenecheck.counts(path)["malformed"] == 1
    monkeypatch.setattr(tagwriter, "SCORE_MAX", 42)
    assert scenecheck.counts(path)["malformed"] == 0


def test_the_third_clause_is_printed_as_a_number_on_the_same_line(tmp_path, capsys):
    """`malformed` is a CHECK4 clause, so it is a number on the line whether or not it is zero."""
    path = osm(tmp_path, [(1, scored()), (2, scored(scenic_score="99"))])
    assert scenecheck.main([str(path), "--top", "0"]) == 4
    assert capsys.readouterr().out.splitlines()[0] == \
        "CHECK4 null_score=0 gated_scored=0 malformed=1 scored=1 refused=0 not_a_road=0"
