"""`ops/sane` check 4 over the file that ships: both clauses as numbers, and a refusal on either.

The clauses are the plan's, and this module is where they are first computed over a real tagged extract:
no road may be left without a score, and nothing the safety gates refuse - nor a motorway or trunk - may
carry a score above 0.
"""
from __future__ import annotations

import pathlib

from etl import assemble, byways, scenecheck

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
        "CHECK4 null_score=0 gated_scored=0 scored=2 refused=0 not_a_road=0"


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
