"""The committed bundle file, apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (T-0270 rulings F3, F5, F6).

This is the SIZE GUARD: the file the app bundles is refused at or above `fallback.FALLBACK_BUDGET_BYTES`, the
ceiling the builder itself enforces. It is also what keeps a committed .sqlite honest (T-0175 R6's hazard):
the file's application_id, user_version, meta.schema_version and DDL hash must equal a corpus the shipping
builder makes NOW, so a schema bump without a rebuild of this file is red here by name. Opened read-only.

WHICH places it keeps is pinned, not only how many per class (rv1-t0270): the sorted (cls, osm_type, osm_id)
list by sha256 equality to a typed literal, and - when the gitignored LA input T-0266 measured is on disk - a
re-selection through the SHIPPING placeallow.select + fallback.choose must equal it row for row.
"""
from __future__ import annotations

import hashlib
import pathlib
import sqlite3

import pytest

from etl import contentdigest, corpus, fallback, placeallow, schema

ROOT = pathlib.Path(__file__).resolve().parents[3]
COMMITTED = ROOT / "apps" / "ios" / "ScenicDrive" / "Corpus" / "corpus-fallback.sqlite"
FULL_EXTRACT = pathlib.Path(__file__).parent / "fixtures" / "corpus_extract.json"

# The LA build quoted in the task Log (F2's caps over T-0266's 4773 places).
KEPT = {"beach": 56, "cafe": 50, "garden": 150, "museum": 150, "park": 400, "peak": 187, "town": 104,
        "trailhead": 99, "viewpoint": 102, "waterfall": 36}

# sha256 of one "cls osm_type osm_id\n" line per row over the file's sorted (cls, osm_type, osm_id) rows - its WHOLE kept set.
KEPT_SET_SHA256 = "79b7f563ffa24de909bbe7ffcf17889b2345c73c7066998403e42c5d4e7a3ba2"
# The measured input (T-0266's la-places.osm.xml, gitignored under services/etl/work/) and its sha256.
LA_PLACES = pathlib.Path("services") / "etl" / "work" / "t0266" / "la-places.osm.xml"
LA_PLACES_SHA256 = "a08035546fd5bab7ec199c65ab4cf703680416701c8d198cc304a1ccb9b830e9"


def checkouts():
    """This checkout, then - from a linked worktree, whose .git is a `gitdir:` file - the main checkout."""
    roots = [ROOT]
    dot_git = ROOT / ".git"
    if dot_git.is_file():
        gitdir = dot_git.read_text(encoding="utf-8").strip().removeprefix("gitdir:").strip()
        roots.append(pathlib.Path(gitdir).parents[2])
    return roots


def kept_rows(conn):
    return sorted(conn.execute("SELECT cls, osm_type, osm_id FROM places").fetchall())


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


def test_the_committed_fallback_keeps_exactly_the_ruled_places(conn):
    rows = kept_rows(conn)
    assert len(rows) == sum(KEPT.values())
    assert hashlib.sha256("".join("%s %s %d\n" % row for row in rows).encode()).hexdigest() == KEPT_SET_SHA256


def test_a_reselection_from_the_measured_la_input_is_the_committed_file(conn):
    found = [root / LA_PLACES for root in checkouts() if (root / LA_PLACES).is_file()]
    if not found:
        pytest.skip(f"the gitignored LA input {LA_PLACES.as_posix()} is absent from {[str(r) for r in checkouts()]};"
                    " the kept set is still pinned by KEPT_SET_SHA256")
    assert hashlib.sha256(found[0].read_bytes()).hexdigest() == LA_PLACES_SHA256
    places, _counts = placeallow.select(found[0])
    chosen = sorted((p["cls"], p["osm_type"], p["osm_id"]) for p in fallback.choose(places))
    assert chosen == kept_rows(conn)
