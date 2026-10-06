"""The committed bundle file, apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (T-0270 rulings F3, F5, F6).

This is the SIZE GUARD: the file the app bundles is refused at or above `fallback.FALLBACK_BUDGET_BYTES`, the
ceiling the builder itself enforces. It is also what keeps a committed .sqlite honest (T-0175 R6's hazard):
the file's application_id, user_version, meta.schema_version and DDL hash must equal a corpus the shipping
builder makes NOW, so a schema bump without a rebuild of this file is red here by name. Opened read-only.
"""
from __future__ import annotations

import pathlib
import sqlite3

import pytest

from etl import contentdigest, corpus, fallback, schema

ROOT = pathlib.Path(__file__).resolve().parents[3]
COMMITTED = ROOT / "apps" / "ios" / "ScenicDrive" / "Corpus" / "corpus-fallback.sqlite"
FULL_EXTRACT = pathlib.Path(__file__).parent / "fixtures" / "corpus_extract.json"

# The LA build quoted in the task Log (F2's caps over T-0266's 4773 places).
KEPT = {"beach": 56, "cafe": 50, "garden": 150, "museum": 150, "park": 400, "peak": 187, "town": 104,
        "trailhead": 99, "viewpoint": 102, "waterfall": 36}


@pytest.fixture(scope="module")
def conn():
    handle = sqlite3.connect(f"file:{COMMITTED.as_posix()}?mode=ro", uri=True)
    yield handle
    handle.close()


def meta(conn):
    return dict(conn.execute("SELECT key, value FROM meta").fetchall())


def test_the_committed_fallback_is_under_the_ceiling():
    assert COMMITTED.is_file()
    assert COMMITTED.stat().st_size < fallback.FALLBACK_BUDGET_BYTES


def test_the_committed_fallback_is_a_finished_fallback_corpus(conn):
    assert conn.execute("PRAGMA application_id").fetchone()[0] == schema.APPLICATION_ID
    assert conn.execute("PRAGMA user_version").fetchone()[0] == schema.SCHEMA_VERSION
    m = meta(conn)
    assert m["schema_version"] == str(schema.SCHEMA_VERSION)
    assert m["build_complete"] == "1"
    assert m["kind"] == fallback.KIND
    assert m["region"] == "la"
    assert m["table_licenses"] == ";".join(f"{t}={schema.TABLE_LICENSES[t]}" for t in sorted(schema.TABLE_LICENSES))
    assert m["attribution"] == schema.ATTRIBUTION
    assert m["odbl_notice"] == schema.ODBL_NOTICE
    assert m["content_sha256"] == contentdigest.content_sha256(conn)


def test_the_committed_fallback_ddl_is_the_shipping_ddl(conn, tmp_path):
    full = tmp_path / "full.sqlite"
    corpus.build(FULL_EXTRACT, full, "2026-10-06T00:00:00Z")
    fresh = sqlite3.connect(f"file:{full.as_posix()}?mode=ro", uri=True)
    try:
        assert schema.ddl_sha256(conn) == schema.ddl_sha256(fresh)
    finally:
        fresh.close()


def test_the_committed_fallback_holds_the_ruled_selection_and_no_ways(conn):
    assert dict(conn.execute("SELECT cls, count(*) FROM places GROUP BY cls").fetchall()) == KEPT
    assert all(n <= cap for (cls, cap), n in zip(fallback.CAPS, (KEPT[c] for c, _ in fallback.CAPS)))
    for table in ("osm_features", "segments", "segments_rtree"):
        assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0, table
    assert conn.execute("SELECT count(*) FROM places_fts").fetchone()[0] == sum(KEPT.values())
    assert conn.execute("SELECT count(*) FROM places_rtree").fetchone()[0] == sum(KEPT.values())
