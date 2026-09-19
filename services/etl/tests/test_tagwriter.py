"""The tagged-PBF rewrite's tag pass: what lands on a way, and that two runs are byte-identical.

P-DATA-01 is the first test here and was red before `etl/tagwriter.py` had a `write`. The byte-identical
property is the whole reason the tag pass is a stream copy rather than a rebuild: `osmium cat` on both ends
encodes and decodes, and everything between them is a pure function of the input.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

from etl import score, tagwriter

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "scenic_clip.osm.xml"
ETL_ROOT = pathlib.Path(__file__).resolve().parents[1]
# Five seeds because a two-element set and a six-way permutation both have to move across them.
HASH_SEEDS = ("0", "1", "2", "3", "4")
# The child re-imports THIS module for the table, so there is one table and never a copy that drifts.
CHILD = ("import sys; sys.path.insert(0, sys.argv[1]);"
         "from tests.test_tagwriter import table, refused;"
         "from etl import tagwriter;"
         "tagwriter.write(sys.argv[2], sys.argv[3], table(), refused())")
SCENIC_WAY = 101
MOTORWAY = 102
PRIVATE_WAY = 103
TRACK_WAY = 104
REFUSED_WAY = 105
PARK_WAY = 106


def terms(**over) -> dict:
    out = {name: 0.5 for name in score.UNIT_TERMS}
    out.update(over)
    return out


def row(way_id: int, highway: str, value, gate_reason=None, flags=()) -> dict:
    return {"way_id": way_id, "highway": highway, "score": value, "gate_reason": gate_reason,
            "terms_state": "normalised", "terms": terms(), "flags": list(flags)}


def table() -> list:
    return [row(SCENIC_WAY, "tertiary", 0.6543, flags=["points_of_interest_absent"]),
            row(MOTORWAY, "motorway", 0.0),
            # TWO flags on purpose: one flag cannot show the order a set would have chosen for them.
            row(PRIVATE_WAY, "residential", 0.0, gate_reason="no_access",
                flags=["sinuosity_declined", "points_of_interest_absent"]),
            row(TRACK_WAY, "track", 0.0, gate_reason="track")]


def refused() -> list:
    return [{"way_id": REFUSED_WAY, "why": "dem: no elevation sample"}]


def written(tmp_path, rows=None, gone=None, source=FIXTURE):
    out = tmp_path / "tagged.osm.xml"
    counts = tagwriter.write(source, out, table() if rows is None else rows,
                             refused() if gone is None else gone)
    return out, counts


def tags_of(text: str, way_id: int) -> dict:
    """The tags of one way, read back out of the written document."""
    import xml.etree.ElementTree as ET
    for way in ET.fromstring(text).findall("way"):
        if int(way.get("id")) == way_id:
            return {t.get("k"): t.get("v") for t in way.findall("tag")}
    raise AssertionError("way %d is not in the written document" % way_id)


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def written_under_seed(out: pathlib.Path, seed: str) -> str:
    """Write the same input again in a FRESH interpreter whose hash seed is `seed`, and digest it."""
    env = dict(os.environ, PYTHONHASHSEED=seed)
    done = subprocess.run([sys.executable, "-c", CHILD, str(ETL_ROOT), str(FIXTURE), str(out)],
                          cwd=str(ETL_ROOT), env=env, capture_output=True, text=True)
    assert done.returncode == 0, "the child writer failed under PYTHONHASHSEED=%s:\n%s" % (seed, done.stderr)
    return sha256_of(out)


def test_the_writer_is_byte_identical_over_two_runs_of_the_same_input(tmp_path):
    """P-DATA-01. The second run is a SEPARATE INTERPRETER, under a different PYTHONHASHSEED.

    Two writes inside one process share one hash seed, so every defect that lets `hash` choose an order -
    `sorted(ways, key=hash)`, `FLAG_SEPARATOR.join(set(flags))` - makes the two runs agree with each other
    and disagree with tomorrow's. The property is about the shipped bytes, and the evidence it exists for
    was two container invocations fifteen minutes apart (the real-run entry in T-0168's log), so the test
    has that shape: one write here, one in a child, digests equal across five seeds.
    """
    first, _ = written(tmp_path / "a")
    a = sha256_of(first)
    for seed in HASH_SEEDS:
        b = written_under_seed(tmp_path / ("seed-" + seed) / "tagged.osm.xml", seed)
        assert a == b, "the tag pass is not byte-identical under PYTHONHASHSEED=%s: %s vs %s" % (seed, a, b)


def test_the_score_is_round_half_up_of_the_unit_score_times_ten():
    """Ruling R1. Half goes UP, and the range is closed at both ends."""
    assert tagwriter.quantise(0.0) == 0
    assert tagwriter.quantise(0.04) == 0
    assert tagwriter.quantise(0.05) == 1
    assert tagwriter.quantise(0.6499) == 6
    assert tagwriter.quantise(0.65) == 7
    assert tagwriter.quantise(0.9999) == 10
    assert tagwriter.quantise(1.0) == 10


def test_the_quantised_score_never_leaves_the_encoded_range():
    """GraphHopper holds it in 4 bits; a term bug upstream must not become a value the router cannot hold."""
    assert tagwriter.quantise(-0.5) == 0
    assert tagwriter.quantise(3.0) == 10


def test_a_scored_way_carries_the_integer_the_unit_score_and_every_term(tmp_path):
    out, _ = written(tmp_path)
    tags = tags_of(out.read_text(encoding="utf-8"), SCENIC_WAY)
    assert tags["scenic_score"] == "7"
    assert tags["scenic_score_unit"] == "0.6543"
    for name in score.UNIT_TERMS:
        assert tags["scenic_" + name] == "0.5000", name
    assert tags["scenic_flags"] == "points_of_interest_absent"
    assert tags["highway"] == "tertiary", "the way's own tags must survive the pass"
    assert tags["name"] == "Latigo Canyon Road"


def test_a_refused_way_carries_scenic_refused_and_no_score(tmp_path):
    """Ruling R2: a refusal is never a silent 0, because 0 means dull and is a motorway's honest score."""
    out, _ = written(tmp_path)
    tags = tags_of(out.read_text(encoding="utf-8"), REFUSED_WAY)
    assert tags["scenic_refused"] == "1"
    assert tags["scenic_refused_why"] == "dem: no elevation sample"
    assert "scenic_score" not in tags


def test_a_row_the_assembly_scored_none_is_written_as_a_refusal(tmp_path):
    """`score.score` returns None when a term is outside 0..1. That is a refusal, not a zero."""
    rows = [r for r in table() if r["way_id"] != SCENIC_WAY] + [row(SCENIC_WAY, "tertiary", None)]
    out, counts = written(tmp_path, rows=rows)
    tags = tags_of(out.read_text(encoding="utf-8"), SCENIC_WAY)
    assert tags["scenic_refused"] == "1"
    assert "scenic_score" not in tags
    assert counts["refused"] == 2 and counts["scored"] == 3


def test_a_motorway_is_scored_zero_and_not_refused(tmp_path):
    """CLAUDE.md's product invariant: motorway/trunk carry scenic_score 0 and stay routable."""
    out, _ = written(tmp_path)
    tags = tags_of(out.read_text(encoding="utf-8"), MOTORWAY)
    assert tags["scenic_score"] == "0"
    assert "scenic_refused" not in tags


def test_a_gated_way_names_the_gate_that_fired(tmp_path):
    out, _ = written(tmp_path)
    assert tags_of(out.read_text(encoding="utf-8"), PRIVATE_WAY)["scenic_gate"] == "no_access"
    assert tags_of(out.read_text(encoding="utf-8"), TRACK_WAY)["scenic_gate"] == "track"


def test_a_way_with_no_highway_tag_is_written_through_untouched(tmp_path):
    """A park is not a road: it is neither scored nor refused, and nothing scenic is written on it."""
    out, _ = written(tmp_path)
    tags = tags_of(out.read_text(encoding="utf-8"), PARK_WAY)
    assert tags == {"leisure": "park", "name": "Malibu Creek State Park"}


def test_the_count_line_names_every_population(tmp_path):
    _, counts = written(tmp_path)
    assert tagwriter.count_line(counts) == "WRITE ways=6 scored=4 refused=1 gated=2 not_a_road=1"


def test_a_road_in_the_file_that_the_table_never_saw_refuses_the_run(tmp_path):
    """Dropping a road silently is how a population shrinks between two stages with nothing to show it."""
    rows = [r for r in table() if r["way_id"] != MOTORWAY]
    with pytest.raises(ValueError, match="102"):
        written(tmp_path, rows=rows)


def test_a_table_row_for_a_way_that_is_not_in_the_file_refuses_the_run(tmp_path):
    rows = table() + [row(999, "tertiary", 0.5)]
    with pytest.raises(ValueError, match="999"):
        written(tmp_path, rows=rows)


def test_a_way_that_already_carries_a_scenic_tag_refuses_the_run(tmp_path):
    """A second pass over an already-tagged file would double the tags rather than replace them."""
    once, _ = written(tmp_path / "once")
    with pytest.raises(ValueError, match="scenic_score"):
        written(tmp_path / "twice", source=once)


def test_the_cli_writes_the_table_and_prints_the_count_line(tmp_path, capsys):
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"refused": refused()}), encoding="utf-8")
    scored = tmp_path / "scored.json"
    scored.write_text(json.dumps({"rows": table()}), encoding="utf-8")
    out = tmp_path / "tagged.osm.xml"
    rc = tagwriter.main(["--input", str(FIXTURE), "--table", str(scored),
                         "--document", str(doc), "--out", str(out)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "WRITE ways=6 scored=4 refused=1 gated=2 not_a_road=1"
    assert tags_of(out.read_text(encoding="utf-8"), SCENIC_WAY)["scenic_score"] == "7"
