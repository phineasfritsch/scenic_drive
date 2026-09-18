"""P-DATA-01: two builds of one extract are byte-identical, and `built_at` is an input rather than a clock.

The pin's words are "ETL idempotent". The only test of that which cannot be argued with is sha256 of the two
FILES, not of their contents: a content digest would stay equal while the artifact the device downloads
changed on every build, and it is the file that the OTA manifest pins and the device verifies.

The two halves are separate assertions on purpose:

  * same input, same --built-at  -> the same bytes. Red the moment anything reads a clock, a random, or an
    unsorted dict on the build path.
  * same input, different --built-at -> different bytes, SAME meta.content_sha256. That is what makes the
    content digest committable as a golden while the file digest stays a per-build download checksum.

The literals below were measured once from the committed fixture and are typed out, not recomputed from the
builder: 7 ways, 79 segments.
"""
from __future__ import annotations

import pathlib
import sqlite3

from etl import corpus
from etl.contentdigest import file_sha256
from etl.corpuswriter import CorpusWriter
from etl.extractway import load_extract
from etl.segmenter import Segmenter

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
BUILT_AT = "2026-09-18T00:00:00Z"
LATER = "2026-09-19T00:00:00Z"

FIXTURE_WAYS = 7
FIXTURE_SEGMENTS = 79


def _build(tmp_path, name, built_at=BUILT_AT):
    out = tmp_path / name
    report = corpus.build(EXTRACT, out, built_at)
    return report, out


def test_two_builds_of_one_extract_are_byte_identical(tmp_path):
    first, a = _build(tmp_path, "a.sqlite")
    second, b = _build(tmp_path, "b.sqlite")
    assert first["ways"] == FIXTURE_WAYS
    assert first["segments"] == FIXTURE_SEGMENTS
    assert second["segments"] == FIXTURE_SEGMENTS
    assert a.stat().st_size == b.stat().st_size
    assert file_sha256(a) == file_sha256(b)
    assert first["file_sha256"] == second["file_sha256"]


def test_built_at_is_an_input_so_it_moves_the_file_and_not_the_content(tmp_path):
    first, a = _build(tmp_path, "a.sqlite", BUILT_AT)
    second, b = _build(tmp_path, "b.sqlite", LATER)
    assert file_sha256(a) != file_sha256(b)
    assert first["content_sha256"] == second["content_sha256"]


def test_built_at_reaches_meta_verbatim(tmp_path):
    _, out = _build(tmp_path, "a.sqlite")
    conn = sqlite3.connect(out)
    try:
        stamp = conn.execute("SELECT value FROM meta WHERE key = 'built_at'").fetchone()[0]
        version = conn.execute("SELECT value FROM meta WHERE key = 'corpus_version'").fetchone()[0]
    finally:
        conn.close()
    assert stamp == BUILT_AT
    assert version == "20260918T000000Z"


def test_corpus_version_can_be_overridden_without_touching_built_at(tmp_path):
    out = tmp_path / "a.sqlite"
    corpus.build(EXTRACT, out, BUILT_AT, corpus_version="sfbay-2026w38")
    conn = sqlite3.connect(out)
    try:
        rows = dict(conn.execute(
            "SELECT key, value FROM meta WHERE key IN ('built_at','corpus_version')").fetchall())
    finally:
        conn.close()
    assert rows == {"built_at": BUILT_AT, "corpus_version": "sfbay-2026w38"}


def test_the_writer_sorts_segments_before_inserting_them(tmp_path):
    """The other way a rebuild stops being byte-identical: the same rows inserted in a different order land
    on different pages, because sqlite hands pages out in insertion order. Fed the segmenter's output
    backwards, the writer must produce the identical assignment, so no caller's iteration order can reach
    the file. The file-hash test above would only ever report this as a hash mismatch with no name on it."""
    _, ways = load_extract(EXTRACT)
    segmenter = Segmenter()
    segments = []
    for way in ways:
        segments.extend(segmenter.cut(way.way_id, list(way.coords)))
    assert len(segments) == FIXTURE_SEGMENTS

    forward = CorpusWriter(tmp_path / "f.sqlite")
    try:
        a = [sid for sid, _ in forward.write_segments(segments)]
    finally:
        forward.close()
    backward = CorpusWriter(tmp_path / "b.sqlite")
    try:
        b = [sid for sid, _ in backward.write_segments(list(reversed(segments)))]
    finally:
        backward.close()

    assert a == sorted(a)
    assert a == b
    assert len(set(a)) == FIXTURE_SEGMENTS
