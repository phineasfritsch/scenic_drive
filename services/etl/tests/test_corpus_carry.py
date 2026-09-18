"""--previous: after a way is split in two, >= 98% of the previous segment ids still resolve.

Why this number matters: the plan stores a saved drive as segment ids on the device and re-resolves them
against each new corpus. A way split into two new way ids changes every segment id derived from it, so
without a carry-forward every saved drive over that road becomes "needs re-plan" the week somebody edits it.

The fixture pair is the whole experiment. `corpus_extract.json` has 7 ways; `corpus_extract_split.json` is
the same roads with way 104 cut at its node 13 - 650 m along, deliberately NOT on a 100 m segment mark, so
one previous segment straddles the cut - and the halves renumbered 204 and 205. Way 104 is gone from the
second extract entirely, exactly as an OSM split leaves it.

The counts are literals, measured once from the committed fixtures and typed out with the arithmetic:

    previous corpus                      79 segments
    ids that survive with no help        67      (the 6 untouched ways)
    ids on way 104, which must alias     12      79 - 67 = 12
    ids that resolve                     79      67 + 12 = 79  ->  10000/10000 bp
    the floor                            79 * 98 = 7742 per 100; 79 * 100 = 7900 >= 7742
    without the carry-forward            67 * 100 = 6700 < 7742   ->  red

`resolved` is counted here by querying `segments` and `segment_alias` directly, never by reading the
`count.ids_*` meta rows the builder wrote: a test that reads the builder's own tally of its own work checks
nothing.
"""
from __future__ import annotations

import pathlib
import sqlite3

from etl import corpus
from etl.contentdigest import file_sha256
from etl.corpusmatch import MIN_COVER_PCT, previous_segments

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
SPLIT = FIXTURES / "corpus_extract_split.json"
BUILT_AT = "2026-09-18T00:00:00Z"

PREVIOUS_SEGMENTS = 79
SPLIT_SEGMENTS = 78
NATURALLY_CARRIED = 67
ALIASED = 12
LOST = 0
FLOOR_PCT = 98
SPLIT_WAY = 104
SPLIT_HALVES = (204, 205)


def _pair(tmp_path, name="new.sqlite"):
    previous = tmp_path / "prev.sqlite"
    corpus.build(EXTRACT, previous, BUILT_AT)
    out = tmp_path / name
    report = corpus.build(SPLIT, out, BUILT_AT, previous=previous)
    return report, previous, out


def _resolves(conn, old_id: int) -> bool:
    if conn.execute("SELECT 1 FROM segments WHERE segment_id = ?", (old_id,)).fetchone():
        return True
    return conn.execute(
        "SELECT 1 FROM segment_alias WHERE old_segment_id = ?", (old_id,)).fetchone() is not None


def test_the_fixtures_really_are_one_way_split_in_two(tmp_path):
    _, previous, out = _pair(tmp_path)
    old = sqlite3.connect(previous)
    new = sqlite3.connect(out)
    try:
        old_ways = {r[0] for r in old.execute("SELECT way_id FROM osm_features")}
        new_ways = {r[0] for r in new.execute("SELECT way_id FROM osm_features")}
    finally:
        old.close()
        new.close()
    assert SPLIT_WAY in old_ways
    assert SPLIT_WAY not in new_ways
    assert set(SPLIT_HALVES) <= new_ways
    assert old_ways - new_ways == {SPLIT_WAY}


def test_at_least_98_percent_of_previous_ids_resolve_after_a_way_split(tmp_path):
    _, previous, out = _pair(tmp_path)
    old_ids = [sid for sid, _ in previous_segments(previous)]
    conn = sqlite3.connect(out)
    try:
        resolved = sum(1 for sid in old_ids if _resolves(conn, sid))
        survived = sum(
            1 for sid in old_ids
            if conn.execute("SELECT 1 FROM segments WHERE segment_id = ?", (sid,)).fetchone())
        segments = conn.execute("SELECT count(*) FROM segments").fetchone()[0]
    finally:
        conn.close()
    assert len(old_ids) == PREVIOUS_SEGMENTS
    assert segments == SPLIT_SEGMENTS
    assert survived == NATURALLY_CARRIED
    assert resolved * 100 >= PREVIOUS_SEGMENTS * FLOOR_PCT
    assert resolved == NATURALLY_CARRIED + ALIASED


def test_every_alias_points_at_a_real_segment_within_the_cover_floor(tmp_path):
    _, _, out = _pair(tmp_path)
    conn = sqlite3.connect(out)
    try:
        rows = conn.execute(
            "SELECT old_segment_id, segment_id, cover_pct FROM segment_alias ORDER BY old_segment_id"
        ).fetchall()
        dangling = conn.execute(
            "SELECT count(*) FROM segment_alias a "
            "LEFT JOIN segments s ON s.segment_id = a.segment_id WHERE s.segment_id IS NULL"
        ).fetchone()[0]
    finally:
        conn.close()
    assert len(rows) == ALIASED
    assert dangling == 0
    assert all(MIN_COVER_PCT <= pct <= 100 for _, _, pct in rows)
    assert len({old for old, _, _ in rows}) == ALIASED


def test_the_build_records_the_carry_it_actually_achieved(tmp_path):
    report, _, out = _pair(tmp_path)
    conn = sqlite3.connect(out)
    try:
        meta = dict(conn.execute(
            "SELECT key, value FROM meta WHERE key IN "
            "('carry_rate','count.ids_carried','count.ids_aliased','count.ids_lost','count.matcher_ways')"
        ).fetchall())
    finally:
        conn.close()
    assert report["ids_lost"] == LOST
    assert meta["count.ids_carried"] == str(NATURALLY_CARRIED)
    assert meta["count.ids_aliased"] == str(ALIASED)
    assert meta["count.ids_lost"] == str(LOST)
    assert meta["count.matcher_ways"] == "1"
    assert meta["carry_rate"] == "10000"


def test_a_build_with_no_previous_records_no_carry(tmp_path):
    out = tmp_path / "solo.sqlite"
    corpus.build(EXTRACT, out, BUILT_AT)
    conn = sqlite3.connect(out)
    try:
        meta = dict(conn.execute(
            "SELECT key, value FROM meta WHERE key IN "
            "('carry_rate','previous_content_sha256','count.segment_alias')").fetchall())
    finally:
        conn.close()
    assert meta == {"carry_rate": "", "previous_content_sha256": "", "count.segment_alias": "0"}


def test_two_carried_builds_from_one_previous_are_byte_identical(tmp_path):
    """The matcher is on the build path, so it has to be as deterministic as the rest of it: an alias chosen
    by whichever candidate the rtree happened to return first would break P-DATA-01 only on the weeks an OSM
    way was edited, which is the worst possible schedule for a bug."""
    _, previous, first = _pair(tmp_path, "one.sqlite")
    second = tmp_path / "two.sqlite"
    corpus.build(SPLIT, second, BUILT_AT, previous=previous)
    assert file_sha256(first) == file_sha256(second)
