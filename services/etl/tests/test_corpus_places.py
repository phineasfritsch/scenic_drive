"""The places the shipping builder writes, and the FTS5 index the device searches them through (T-0254).

Every expected row is a typed literal. place_id is segid.place_id's value for the pair (asserted against the
function separately, so the literal and the derivation cannot drift together), and lon_e7 / lat_e7 are the
fixture's degrees x 1e7. Tests/PlaceStoreTests/PlaceStoreSearchTests types the same rows on the Swift side.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from etl import contentdigest, corpus, schema
from etl.extractplace import load_places
from etl.segid import place_id

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
PLACES_EXTRACT = FIXTURES / "corpus_extract_places.json"
WAYS_ONLY_EXTRACT = FIXTURES / "corpus_extract.json"
BUILT_AT = "2026-09-18T00:00:00Z"

# (place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7), place_id ascending - the table's own order.
PLACE_ROWS = [
    (3508864315908228945, "r", 3001, "park", "Malibu Creek State Park", -1187313000, 340985000),
    (5174888989237452560, "n", 1006, "viewpoint", None, -1186956000, 340784000),
    (5174890088749080771, "n", 1007, "pub", "Neary's Pub", -1184912000, 340195000),
    (5174891188260708982, "n", 1004, "cafe", "Café Tropical", -1182729000, 340872000),
    (5174892287772337193, "n", 1005, "cafe", "Rock Store", -1187539000, 341201000),
    (5174893387283965404, "n", 1002, "viewpoint", "Mulholland Dam", -1183256000, 341257000),
    (5174894486795593615, "n", 1003, "viewpoint", "Mulholland Scenic Overlook", -1183694000, 341308000),
    (5174896685818850037, "n", 1001, "viewpoint", "Mulholland", -1184103000, 341281000),
    (5739051218924217510, "w", 2001, "restaurant", "Saddle Peak Lodge", -1186597000, 340959000),
]

FTS5_SHADOWS = ("places_fts_config", "places_fts_data", "places_fts_docsize", "places_fts_idx")


def _build(tmp_path, extract=PLACES_EXTRACT, name="corpus.sqlite"):
    out = tmp_path / name
    corpus.build(extract, out, BUILT_AT)
    return out


def test_the_typed_place_ids_are_segid_place_id():
    assert [place_id(r[1], r[2]) for r in PLACE_ROWS] == [r[0] for r in PLACE_ROWS]


def test_the_shipping_builder_writes_every_extract_place(tmp_path):
    conn = sqlite3.connect(_build(tmp_path))
    try:
        rows = conn.execute(
            "SELECT place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7 FROM places ORDER BY place_id"
        ).fetchall()
        count = conn.execute("SELECT value FROM meta WHERE key = 'count.places'").fetchone()[0]
        rtree = conn.execute(
            "SELECT id, min_lon, max_lon, min_lat, max_lat FROM places_rtree ORDER BY id").fetchall()
    finally:
        conn.close()
    assert rows == PLACE_ROWS
    assert count == str(len(PLACE_ROWS))
    assert [r[0] for r in rtree] == [r[0] for r in PLACE_ROWS]


def test_places_fts_indexes_every_named_place_and_no_unnamed_one(tmp_path):
    conn = sqlite3.connect(_build(tmp_path))
    try:
        indexed = [r[0] for r in conn.execute("SELECT id FROM places_fts_docsize ORDER BY id")]
        hits = conn.execute(
            "SELECT rowid FROM places_fts WHERE places_fts MATCH ? ORDER BY bm25(places_fts), rowid",
            ('"mulholland"',)).fetchall()
        folded = conn.execute(
            "SELECT rowid FROM places_fts WHERE places_fts MATCH ?", ('"cafe"',)).fetchall()
        conn.execute("INSERT INTO places_fts (places_fts) VALUES ('integrity-check')")
    finally:
        conn.close()
    assert indexed == [r[0] for r in PLACE_ROWS if r[4] is not None]
    assert [h[0] for h in hits] == [5174896685818850037, 5174893387283965404, 5174894486795593615]
    assert folded == [(5174891188260708982,)]


def test_places_fts_is_in_the_ddl_odbl_and_out_of_the_ddl_hash_and_the_digest(tmp_path):
    conn = sqlite3.connect(_build(tmp_path))
    try:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_schema")}
    finally:
        conn.close()
    assert "places_fts" in schema.VIRTUAL_TABLES
    assert set(FTS5_SHADOWS) <= names
    assert set(FTS5_SHADOWS) <= schema.SHADOW_TABLES
    assert schema.TABLE_LICENSES["places_fts"] == schema.ODBL_LICENSE
    assert "places_fts" not in {table for table, _ in contentdigest.SELECTS}
    # Every table in the file is licensed, or is the sqlite-written shadow of a licensed virtual table.
    unlicensed = sorted(n for n in names if not n.startswith("sqlite_")
                        and n not in schema.TABLE_LICENSES and n not in schema.SHADOW_TABLES
                        and n not in _index_names())
    assert unlicensed == []


def _index_names():
    import re
    return set(re.findall(r"CREATE (?:UNIQUE )?INDEX (\w+)", "\n".join(schema.DDL)))


def test_a_rebuild_with_places_is_byte_identical(tmp_path):
    first = _build(tmp_path, name="a.sqlite")
    second = _build(tmp_path, name="b.sqlite")
    assert first.read_bytes() == second.read_bytes()


def test_an_extract_without_places_writes_none(tmp_path):
    conn = sqlite3.connect(_build(tmp_path, extract=WAYS_ONLY_EXTRACT))
    try:
        counts = [conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("places", "places_rtree", "places_fts_docsize")]
    finally:
        conn.close()
    assert counts == [0, 0, 0]


@pytest.mark.parametrize("bad, message", [
    ({"osm_type": "x"}, "osm_type"),
    ({"osm_id": 0}, "osm_id"),
    ({"name": 7}, "name"),
    ({"cls": ""}, "cls"),
    ({"lat": 91.0}, "range"),
])
def test_load_places_refuses_a_malformed_place(tmp_path, bad, message):
    place = {"osm_type": "n", "osm_id": 1, "cls": "cafe", "name": "x", "lat": 34.0, "lon": -118.0}
    place.update(bad)
    path = tmp_path / "extract.json"
    path.write_text(json.dumps({"region": "r", "ways": [], "places": [place]}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_places(path)


def test_load_places_refuses_a_duplicate(tmp_path):
    place = {"osm_type": "n", "osm_id": 1, "cls": "cafe", "name": "x", "lat": 34.0, "lon": -118.0}
    path = tmp_path / "extract.json"
    path.write_text(json.dumps({"region": "r", "ways": [], "places": [place, place]}), encoding="utf-8")
    with pytest.raises(ValueError, match="twice"):
        load_places(path)
