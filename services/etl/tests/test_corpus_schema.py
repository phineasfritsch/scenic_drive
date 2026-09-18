"""The DDL hash is pinned to schema_version, the segment id is pinned to a hand-worked literal, and the two
terms tables are physically separate and empty.

The plan's OTA row: a device downloads a corpus only when `schema_version == PlaceStore.schemaVersion`, and
"ETL bumps schema_version on any DDL change (pytest asserts DDL-hash <-> version)". That sentence is this
file. Without it, adding a column is a silent, shipping, cross-version data corruption: the device's reader
binds columns by position, the manifest still says version 1, and the download is allowed.

The pinned hash covers only the schema rows this repository writes. rtree's shadow tables
(segments_rtree_node/_rowid/_parent) carry CREATE TABLE text sqlite generates, and binding schema_version to
the sqlite build that ran the ETL would invalidate every device's corpus on a toolchain bump with no DDL diff
to point at. See the task Log, ruling R6.
"""
from __future__ import annotations

import pathlib
import sqlite3

import pytest

from etl import corpus, schema
from etl.corpuswriter import CorpusWriter
from etl.segid import natural_id, place_id

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
BUILT_AT = "2026-09-18T00:00:00Z"

# schema_version -> sha256 of the normalised sqlite_schema read-back. One entry per version ever shipped.
# Changing ANY column, table, index or CHECK moves the hash and fails here until a new version is added.
DDL_SHA256_BY_VERSION = {
    1: "aeca01498f1f945f70b00175717ee7fd8ede4b7b243ebc16f273143ef331da3e",
}

# FNV-1a 64 over way_id big-endian 8 bytes || bucket big-endian 4 bytes, masked to 63 bits.
# way_id = 1, bucket = 0, key = 00 00 00 00 00 00 00 01 00 00 00 00:
#   h0 = 0xcbf29ce484222325; x7 zero bytes -> 0x778b1a14b6876aa7; xor 0x01, x prime -> 0xa8c7f732281a3812;
#   x4 zero bytes -> 0x47b8cdaf9fc0fa32; & 0x7fffffffffffffff -> the literal below.
SEGMENT_ID_1_0 = 5168106726590839346


def _built(tmp_path):
    out = tmp_path / "corpus.sqlite"
    corpus.build(EXTRACT, out, BUILT_AT)
    return sqlite3.connect(out)


def test_ddl_hash_matches_the_pinned_schema_version():
    conn = sqlite3.connect(":memory:")
    try:
        assert schema.SCHEMA_VERSION in DDL_SHA256_BY_VERSION
        assert schema.apply_schema(conn) == DDL_SHA256_BY_VERSION[schema.SCHEMA_VERSION]
    finally:
        conn.close()


def test_a_built_corpus_carries_the_same_schema_version_in_meta_and_in_the_header(tmp_path):
    conn = _built(tmp_path)
    try:
        meta = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
        application_id = conn.execute("PRAGMA application_id").fetchone()[0]
    finally:
        conn.close()
    assert meta == str(schema.SCHEMA_VERSION)
    assert user_version == schema.SCHEMA_VERSION
    assert application_id == schema.APPLICATION_ID


def test_segment_id_is_fnv1a64_over_the_big_endian_key():
    assert natural_id(1, 0) == SEGMENT_ID_1_0
    assert natural_id(1, 1) != SEGMENT_ID_1_0
    assert natural_id(2, 0) != SEGMENT_ID_1_0
    # A node and a way with the same numeric id must not collide: 9-byte key against a 12-byte key.
    assert place_id("n", 1) != natural_id(1, 0)
    assert 0 < natural_id(1, 0) < (1 << 63)


def test_no_autoindex_survived_into_the_built_file(tmp_path):
    """Rule 2 of schema.py, asserted rather than trusted: an inline UNIQUE renumbers rootpages invisibly."""
    conn = _built(tmp_path)
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_schema WHERE name LIKE 'sqlite_autoindex%'")]
        sequence = conn.execute(
            "SELECT count(*) FROM sqlite_schema WHERE name = 'sqlite_sequence'").fetchone()[0]
    finally:
        conn.close()
    assert names == []
    assert sequence == 0


def test_terms_tables_are_declared_physically_separate_and_empty_this_slice(tmp_path):
    """T-0030 ships zero term rows; T-0146 assembles them. `term_defs` IS populated - a vocabulary is not a
    term value, and the ODbL half is unreadable without it."""
    conn = _built(tmp_path)
    try:
        counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("terms_osm", "terms_raster", "term_defs", "places", "curated")}
        foreign_keys = conn.execute("PRAGMA foreign_key_list(terms_raster)").fetchall()
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    finally:
        conn.close()
    assert counts["terms_osm"] == 0
    assert counts["terms_raster"] == 0
    assert counts["places"] == 0
    assert counts["curated"] == 0
    assert counts["term_defs"] == len(schema.TERM_NAMES)
    assert foreign_keys == []
    assert meta["count.terms_osm"] == "0"
    assert meta["count.terms_raster"] == "0"


def test_the_odbl_half_can_be_dropped_without_taking_our_half_with_it(tmp_path):
    """P-DATA-01's second clause. A FOREIGN KEY from terms_raster into segments would make this either fail
    or leave a broken schema, which is why the DDL has none."""
    conn = _built(tmp_path)
    try:
        for table in schema.ODBL_TABLES:
            conn.execute(f"DROP TABLE {table}")
        rows = conn.execute("SELECT count(*) FROM terms_raster").fetchone()[0]
        defs = conn.execute("SELECT count(*) FROM term_defs").fetchone()[0]
    finally:
        conn.close()
    assert rows == 0
    assert defs == len(schema.TERM_NAMES)


def test_the_writer_refuses_a_raster_term_in_the_odbl_table(tmp_path):
    writer = CorpusWriter(tmp_path / "x.sqlite")
    try:
        with pytest.raises(ValueError, match="not in family"):
            writer.add_term("osm", 1, 101, 0.5)
        with pytest.raises(ValueError, match="not in family"):
            writer.add_term("raster", 1, 1, 0.5)
    finally:
        writer.close()
    assert schema.OSM_TERM_IDS.isdisjoint(schema.RASTER_TERM_IDS)


def test_the_rtree_holds_one_box_per_segment_and_contains_it(tmp_path):
    conn = _built(tmp_path)
    try:
        mismatched = conn.execute(
            "SELECT count(*) FROM segments s JOIN segments_rtree r ON r.id = s.segment_id "
            "WHERE r.min_lon > s.min_lon_e7 / 1e7 OR r.max_lon < s.max_lon_e7 / 1e7 "
            "OR r.min_lat > s.min_lat_e7 / 1e7 OR r.max_lat < s.max_lat_e7 / 1e7").fetchone()[0]
        orphans = conn.execute(
            "SELECT count(*) FROM segments_rtree r LEFT JOIN segments s ON s.segment_id = r.id "
            "WHERE s.segment_id IS NULL").fetchone()[0]
        unboxed = conn.execute(
            "SELECT count(*) FROM segments s LEFT JOIN segments_rtree r ON r.id = s.segment_id "
            "WHERE r.id IS NULL").fetchone()[0]
    finally:
        conn.close()
    assert (mismatched, orphans, unboxed) == (0, 0, 0)


def test_meta_carries_every_required_key_and_the_attribution(tmp_path):
    conn = _built(tmp_path)
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    finally:
        conn.close()
    assert schema.REQUIRED_META_KEYS <= set(meta)
    assert meta["attribution"] == schema.ATTRIBUTION
    assert meta["odbl_notice"] == schema.ODBL_NOTICE
    assert meta["build_complete"] == "1"
    assert len(meta["content_sha256"]) == 64
    assert f"osm_features={schema.ODBL_LICENSE}" in meta["table_licenses"]
    assert f"terms_raster={schema.OWN_LICENSE}" in meta["table_licenses"]
