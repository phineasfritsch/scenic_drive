"""T-0379: the landmarks table, written by the SHIPPING `etl.corpus.main` and read back whole.

The fixture (fixtures/corpus_extract_landmarks.json + fixtures/corpus_landmarks.osm.xml) is hand-placed around
nine ways: a 299 m and a 301 m landmark south of way 21 (and its twin 23, the tie), a landmark either side of a
0.01-degree latitude and a longitude cell line from the way it is nearest, a landmark beside the middle of a
two-node way spanning thirty cells east-west (107) and one north-south (110), an access=private viewpoint
(refused) and a closed viewpoint way. 108 sits where lon + MARGIN_DEG/cos(lat) falls just short of a cell line, so its nearest way (258 m east) is in the
LAST cell it reads; 109's way is 11 m south across a latitude cell line, in the FIRST cell it reads.
"""
from __future__ import annotations

import math
import pathlib
import sqlite3

import pytest

from etl import contentdigest, corpus, geom, landmarks, schema
from etl.extractway import load_extract

HERE = pathlib.Path(__file__).resolve().parent
EXTRACT = HERE / "fixtures" / "corpus_extract_landmarks.json"
OSM = HERE / "fixtures" / "corpus_landmarks.osm.xml"
BUILT_AT = "2026-10-16T00:00:00Z"
COLUMNS = ("osm_type", "osm_id", "kind", "name", "ele_dm", "lat_e5", "lon_e5", "nearest_way_id")
SELECT = "SELECT %s FROM landmarks ORDER BY osm_type, osm_id" % ", ".join(COLUMNS)
# One (row key, new value) per column, the digest test's perturbations: each changes exactly its column of one row
# and keeps that row's place in ORDER BY osm_type, osm_id, so a digest that drops the column cannot be moved by
# the row order instead. The key is perturbed in place too: w 201 -> n 201 stays last, n 101 -> n 100 stays first.
PERTURB = {
    "osm_type": (("w", 201), "'n'"),
    "osm_id": (("n", 101), "100"),
    "kind": (("n", 101), "'viewpoint'"),
    "name": (("n", 101), "NULL"),
    "ele_dm": (("n", 101), "NULL"),
    "lat_e5": (("n", 101), "0"),
    "lon_e5": (("n", 101), "0"),
    "nearest_way_id": (("n", 101), "NULL"),
}

# Typed out by hand from the fixture: 851 m -> 8510 dm; 2800 ft = 853.44 m -> 853.4 -> 8534 dm; the ring's
# point is the mean of its three distinct nodes at 5 dp. 101 ties ways 21 and 23 (one geometry) -> the lower.
EXPECTED = [
    ("n", 101, "peak", "Saddle Test Peak", 8510, 3400100, -11855000, 21),
    ("n", 102, "peak", None, 8534, 3399731, -11855000, 21),
    ("n", 103, "viewpoint", "Far Point", None, 3399729, -11855000, None),
    ("n", 104, "viewpoint", "Cell Edge Lat", None, 3401995, -11869500, 24),
    ("n", 105, "viewpoint", "Cell Edge Lon", None, 3405500, -11879995, 25),
    ("n", 107, "peak", "Long Way Peak", None, 3408500, -11875000, 26),
    ("n", 108, "viewpoint", "Lon Top Cell", None, 3407000, -11871208, 27),
    ("n", 109, "peak", "Lat Bottom Cell", 1000, 3404005, -11865000, 28),
    ("n", 110, "peak", "Long Lat Peak", None, 3405000, -11894950, 29),
    ("w", 201, "viewpoint", "Ring View", None, 3403003, -11864995, None),
]


def build(tmp_path, *extra) -> pathlib.Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    out = tmp_path / "corpus.sqlite"
    code = corpus.main(["--input", str(EXTRACT), "--out", str(out), "--built-at", BUILT_AT, *extra])
    assert code == 0
    return out


def table(path) -> list:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(SELECT).fetchall()
    finally:
        conn.close()


def recomputed() -> list:
    """landmarks.select + landmarks.nearest_way_id over EVERY extract way: no grid, no prefilter."""
    _region, ways = load_extract(str(EXTRACT))
    every = [(way.way_id, list(way.coords)) for way in ways]
    found, _counts = landmarks.select(str(OSM))
    rows = []
    for lm in found:
        ele = None if lm["ele_m"] is None else round(lm["ele_m"] * 10)
        rows.append((lm["osm_type"], lm["osm_id"], lm["kind"], lm["name"], ele, round(lm["lat"] * 1e5),
                     round(lm["lon"] * 1e5), landmarks.nearest_way_id((lm["lat"], lm["lon"]), every)))
    return sorted(rows, key=lambda row: (row[0], row[1]))


def test_the_shipped_build_stores_the_landmarks_table_whole(tmp_path):
    stored = table(build(tmp_path, "--landmarks-osm", str(OSM)))
    assert stored == EXPECTED
    assert stored == recomputed()


def test_without_landmarks_osm_the_table_exists_and_is_empty(tmp_path):
    assert table(build(tmp_path)) == []


@pytest.mark.parametrize("osm_id", [102, 103])
def test_the_stored_nearest_way_is_inclusive_at_near_m(tmp_path, monkeypatch, osm_id):
    row = next(r for r in EXPECTED if r[1] == osm_id)
    distance = geom.point_to_polyline_m((row[5] / 1e5, row[6] / 1e5), [(34.0, -118.6), (34.0, -118.5)])
    assert 299.0 < distance < 302.0
    monkeypatch.setattr(landmarks, "NEAR_M", distance)
    stored = {r[1]: r[7] for r in table(build(tmp_path / "at", "--landmarks-osm", str(OSM)))}
    assert stored[osm_id] == 21
    monkeypatch.setattr(landmarks, "NEAR_M", math.nextafter(distance, -math.inf))
    stored = {r[1]: r[7] for r in table(build(tmp_path / "below", "--landmarks-osm", str(OSM)))}
    assert stored[osm_id] is None


def test_the_landmarks_table_is_odbl_and_in_the_content_digest(tmp_path):
    assert "landmarks" in schema.ODBL_TABLES and schema.TABLE_LICENSES["landmarks"] == schema.ODBL_LICENSE
    assert [t for t, _ in contentdigest.SELECTS].index("landmarks") == \
        [t for t, _ in contentdigest.SELECTS].index("places") + 1
    conn = sqlite3.connect(str(build(tmp_path, "--landmarks-osm", str(OSM))))
    try:
        assert tuple(row[1] for row in conn.execute("PRAGMA table_info(landmarks)")) == COLUMNS
        assert tuple(PERTURB) == COLUMNS
        before = contentdigest.content_sha256(conn)
        rows = conn.execute(SELECT).fetchall()
        for column in COLUMNS:
            key, value = PERTURB[column]
            at = [row[:2] for row in rows].index(key)
            conn.execute("SAVEPOINT s")
            conn.execute("UPDATE landmarks SET %s = %s WHERE osm_type = ? AND osm_id = ?" % (column, value), key)
            after = conn.execute(SELECT).fetchall()
            assert len(after) == len(rows), column
            assert [i for i, (old, new) in enumerate(zip(rows, after)) if old != new] == [at], column
            assert [c for c, old, new in zip(COLUMNS, rows[at], after[at]) if old != new] == [column]
            assert contentdigest.content_sha256(conn) != before, column
            conn.execute("ROLLBACK TO s")
            conn.execute("RELEASE s")
        assert contentdigest.content_sha256(conn) == before
    finally:
        conn.close()


@pytest.mark.parametrize("statement", [
    "INSERT INTO landmarks VALUES ('r', 1, 'peak', NULL, NULL, 0, 0, NULL)",
    "INSERT INTO landmarks VALUES ('n', 0, 'peak', NULL, NULL, 0, 0, NULL)",
    "INSERT INTO landmarks VALUES ('n', 1, 'cafe', NULL, NULL, 0, 0, NULL)",
    "INSERT INTO landmarks VALUES ('n', 1, 'peak', NULL, NULL, 9000001, 0, NULL)",
    "INSERT INTO landmarks VALUES ('n', 1, 'peak', NULL, NULL, 0, -18000001, NULL)",
    "INSERT INTO landmarks VALUES ('n', 101, 'peak', NULL, NULL, 0, 0, NULL)",
])
def test_the_table_refuses_what_a_landmark_cannot_be(tmp_path, statement):
    conn = sqlite3.connect(str(build(tmp_path, "--landmarks-osm", str(OSM))))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(statement)
        conn.execute("INSERT INTO landmarks VALUES ('n', 1, 'peak', NULL, NULL, 9000000, -18000000, NULL)")
    finally:
        conn.close()
