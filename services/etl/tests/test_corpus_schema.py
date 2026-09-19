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

import inspect
import pathlib
import re
import sqlite3

import pytest

from etl import corpus, schema, score
from etl.corpuswriter import CorpusWriter
from etl.segid import natural_id, place_id

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
BUILT_AT = "2026-09-18T00:00:00Z"

# schema_version -> sha256 of the normalised sqlite_schema read-back. One entry per version ever shipped.
# Changing ANY column, table, index or CHECK moves the hash and fails here until a new version is added.
DDL_SHA256_BY_VERSION = {
    1: "aeca01498f1f945f70b00175717ee7fd8ede4b7b243ebc16f273143ef331da3e",
    # 2 (T-0173): osm_features.paved INTEGER CHECK (paved IN (0,1)) became
    #             osm_features.surface INTEGER CHECK (surface IN (-1,0,1)). One column, one hash, one bump.
    #             Version 1 stays listed: a version ever shipped is never removed from this table.
    2: "c7a0463730a03b61e5a1800415aac2d4c4a6dd5384416d690e45f2cf80e2e5c8",
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


# The three states, typed out rather than imported from the module under test. -1 is the FLAG score.py:116
# raises, not "no tag": an absent tag on a class OUTSIDE score.UNSURVEYED_CLASSES is paved (T-0173 ruling R2).
UNKNOWN, UNPAVED, PAVED = -1, 0, 1

# One way per branch of the rule, from tests/fixtures/corpus_extract.json:
#   105 residential, no `surface` key        -> the absent tag on an unsurveyed class     -> -1
#   103 unclassified, surface=gravel         -> positive evidence, unsurveyed class loses -> 0
#   101 secondary,   no `surface` key        -> the complement, "expressed by omission"   -> 1
#   102 tertiary,    surface=cobblestone     -> a present tag that is not unpaved         -> 1
#   106 motorway,    no `surface` key        -> scores 0 and is still PAVED and routable  -> 1
EXPECTED_SURFACE_STATE = {101: PAVED, 102: PAVED, 103: UNPAVED, 105: UNKNOWN, 106: PAVED}


def test_a_residential_way_with_no_surface_tag_round_trips_as_unknown(tmp_path):
    """The brief's defect 1. A two-valued `paved` column cannot carry the UNSURVEYED state, so a residential
    way with no surface tag came back indistinguishable from a surveyed asphalt one - and score.py:116 plus
    the plan's hazard strip both need to tell them apart on the device."""
    conn = _built(tmp_path)
    try:
        states = dict(conn.execute(
            "SELECT way_id, surface FROM osm_features WHERE way_id IN (101,102,103,105,106)"))
    finally:
        conn.close()
    assert states[105] == UNKNOWN, "a residential way with no surface tag must be unknown, not paved"
    assert states == EXPECTED_SURFACE_STATE


def test_the_surface_column_refuses_a_fourth_state(tmp_path):
    """The domain is a CHECK, not a convention. Without it, -2 or 2 is storable and every reader downstream
    has to guess what it meant."""
    conn = sqlite3.connect(":memory:")
    try:
        schema.apply_schema(conn)
        for bad in (-2, 2, 7):
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO osm_features (way_id, cls, highway, name, surface, access_ok, oneway, "
                    "node_count, length_mm, geom_sha256) VALUES (1,'residential','residential',NULL,?,"
                    "1,0,2,1000,zeroblob(32))", (bad,))
    finally:
        conn.close()


def test_every_term_name_except_byway_is_a_parameter_of_score_score():
    """TERM_NAMES IS the on-device score contract (schema.py rule 6: the score is recomputed from terms_* at
    query time), so a name in it that `score.score` does not accept is a term the device cannot spend.

    `byway` is the one exception and it is an exception for a reason, not a carve-out: it is not a 0..1 term
    at all. `score.score` takes `byway_status`, Caltrans's own string, and `byways.status_bonus` turns it
    into the bonus applied to E - so the corpus stores the bonus under its own term id and the parameter it
    corresponds to is spelled differently on purpose.
    """
    keywords = set(inspect.signature(score.score).parameters)
    names = set(schema.TERM_NAMES.values())
    assert "byway" in names
    assert (names - {"byway"}) <= keywords, sorted(names - {"byway"} - keywords)
    # And the other direction: every 0..1 term the scorer takes has an id, or the corpus cannot carry it.
    assert set(score.UNIT_TERMS) <= names, sorted(set(score.UNIT_TERMS) - names)


def test_the_reserved_terms_name_their_producer_task_and_every_other_term_names_a_module():
    """RESERVED is typed out here as well as in etl/terms.py. Rebuilding it from the module under test would
    pass after any edit to that module, which is the one thing this assertion must not do.

    The second half is what keeps the list honest: the nine non-reserved terms each name a file that has to
    exist. The day T-0161 lands `sinuosity`, this test is red until the entry leaves RESERVED.
    """
    assert schema.RESERVED == {2: "T-0161", 107: "T-0164"}
    assert set(schema.RESERVED) <= set(schema.TERM_NAMES)
    etl_root = pathlib.Path(__file__).resolve().parents[1]
    for term_id, producer in sorted(schema.PRODUCERS.items()):
        assert term_id in schema.TERM_NAMES, term_id
        if term_id in schema.RESERVED:
            assert producer == schema.RESERVED[term_id]
            assert re.fullmatch(r"T-\d{4}|none filed", producer), (term_id, producer)
        else:
            assert (etl_root / producer).is_file(), f"{schema.TERM_NAMES[term_id]}: {producer} is missing"
    assert set(schema.PRODUCERS) == set(schema.TERM_NAMES)


def test_the_term_families_follow_the_odbl_split_and_the_ids_are_stable():
    """Ids are a permanent on-device contract, so they are pinned as literals here. Family is the ODbL line
    and nothing else: `points_of_interest` is Commons photo density (plan:89), not OSM, so it may not sit in
    the half CorpusWriter.add_term exists to protect."""
    assert schema.TERM_NAMES == {
        1: "curvature", 2: "sinuosity", 3: "speed_fit", 4: "furniture",
        101: "elevation_gain", 102: "relief", 103: "canopy", 104: "impervious", 105: "byway",
        106: "water", 107: "points_of_interest",
    }
    assert schema.OSM_TERM_IDS == {1, 2, 3, 4}
    assert schema.RASTER_TERM_IDS == {101, 102, 103, 104, 105, 106, 107}
    assert schema.OSM_TERM_IDS.isdisjoint(schema.RASTER_TERM_IDS)
