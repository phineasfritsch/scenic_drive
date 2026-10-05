"""The places the shipping builder writes, and the FTS5 index the device searches them through (T-0254).

Every expected row is a typed literal. place_id is segid.place_id's value for the pair (asserted against the
function separately, so the literal and the derivation cannot drift together), and lon_e7 / lat_e7 are the
fixture's degrees x 1e7. Tests/PlaceStoreTests/PlaceStoreSearchTests types the same rows on the Swift side.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
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


# One malformed place, one field at a time. Each numeric bound is probed just outside on BOTH sides (the next
# representable double, which geom.to_e7 rounds back INTO the places CHECK range, so only _row can refuse it,
# and a value one e7 step out), each field with every JSON kind it must not accept. MISSING drops the key.
# The refusal is _row's own, naming the extract: segid.place_id's later osm_type refusal does not name it.
MISSING = object()
BASE_PLACE = {"osm_type": "n", "osm_id": 1, "cls": "cafe", "name": "x", "lat": 34.0, "lon": -118.0}
BASE_ROW = (5173841154655956702, "n", 1, "cafe", "x", -1180000000, 340000000)
OSM_ID_MAX = 2**63 - 1


def _out(bound, direction):
    return math.nextafter(bound, direction * math.inf)


def _refused(field, value, message, case):
    return pytest.param({field: value}, message, id=f"{field}-{case}")


REFUSED = [
    pytest.param(None, "object", id="place-null"),
    pytest.param([], "object", id="place-array"),
    pytest.param("cafe", "object", id="place-string"),
    *[_refused("osm_type", v, "osm_type", c) for v, c in [
        ("x", "x"), ("N", "upper"), ("", "empty"), ("node", "word"), (None, "null"), (1, "int"), (MISSING, "missing")]],
    *[_refused("osm_id", v, "osm_id", c) for v, c in [
        (0, "zero"), (-1, "negative"), (OSM_ID_MAX + 1, "above-int64"), (True, "bool"), (1.0, "float"),
        ("1", "str"), (None, "null"), (MISSING, "missing")]],
    *[_refused("cls", v, "cls", c) for v, c in [
        ("", "empty"), (None, "null"), (7, "int"), (True, "bool"), (["cafe"], "array"), (MISSING, "missing")]],
    *[_refused("name", v, "name", c) for v, c in [(7, "int"), (1.5, "float"), (True, "bool"), (["x"], "array")]],
    *[_refused(axis, v, "range", c) for axis, bound in (("lat", 90.0), ("lon", 180.0)) for v, c in [
        (_out(-bound, -1), "below-by-one-double"), (-bound - 1e-6, "below-by-1e-6"),
        (_out(bound, 1), "above-by-one-double"), (bound + 1e-6, "above-by-1e-6"),
        (10**400, "huge-int"), (math.nan, "nan"), (math.inf, "inf"), (-math.inf, "minus-inf")]],
    *[_refused(axis, v, f"{axis} must be a number", c) for axis in ("lat", "lon") for v, c in [
        (None, "null"), ("34.0", "str"), (True, "true"), (False, "false"), ([34.0], "array"), (MISSING, "missing")]],
]


def _write(tmp_path, places):
    path = tmp_path / "extract.json"
    path.write_text(json.dumps({"region": "r", "ways": [], "places": places}), encoding="utf-8")
    return path


def _place(bad):
    if not isinstance(bad, dict):
        return bad
    place = dict(BASE_PLACE, **bad)
    return {k: v for k, v in place.items() if v is not MISSING}


@pytest.mark.parametrize("bad, message", REFUSED)
def test_load_places_refuses_a_malformed_place(tmp_path, bad, message):
    path = _write(tmp_path, [_place(bad)])
    with pytest.raises(ValueError, match=f"^{re.escape(str(path))}: .*{message}"):
        load_places(path)


@pytest.mark.parametrize("good, row", [
    pytest.param({}, BASE_ROW, id="base"),
    pytest.param({"lat": -90.0}, BASE_ROW[:6] + (-900000000,), id="lat-exactly-minus-90"),
    pytest.param({"lat": 90.0}, BASE_ROW[:6] + (900000000,), id="lat-exactly-90"),
    pytest.param({"lon": -180.0}, BASE_ROW[:5] + (-1800000000, 340000000), id="lon-exactly-minus-180"),
    pytest.param({"lon": 180.0}, BASE_ROW[:5] + (1800000000, 340000000), id="lon-exactly-180"),
    pytest.param({"lat": 34, "lon": -118}, BASE_ROW, id="integer-degrees"),
    pytest.param({"osm_type": "w"}, (5743642779482680521, "w") + BASE_ROW[2:], id="osm_type-w"),
    pytest.param({"osm_type": "r"}, (3515391016931964866, "r") + BASE_ROW[2:], id="osm_type-r"),
    pytest.param({"osm_id": OSM_ID_MAX}, (3900070058368652169, "n", OSM_ID_MAX) + BASE_ROW[3:], id="osm_id-int64-max"),
    pytest.param({"cls": "c"}, BASE_ROW[:3] + ("c",) + BASE_ROW[4:], id="cls-one-char"),
    pytest.param({"name": None}, BASE_ROW[:4] + (None,) + BASE_ROW[5:], id="name-null"),
    pytest.param({"name": MISSING}, BASE_ROW[:4] + (None,) + BASE_ROW[5:], id="name-missing"),
])
def test_load_places_accepts_a_place_at_every_bound(tmp_path, good, row):
    assert load_places(_write(tmp_path, [_place(good)])) == [row]


def test_load_places_refuses_a_duplicate(tmp_path):
    place = {"osm_type": "n", "osm_id": 1, "cls": "cafe", "name": "x", "lat": 34.0, "lon": -118.0}
    path = tmp_path / "extract.json"
    path.write_text(json.dumps({"region": "r", "ways": [], "places": [place, place]}), encoding="utf-8")
    with pytest.raises(ValueError, match="twice"):
        load_places(path)
