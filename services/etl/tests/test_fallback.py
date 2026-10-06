"""The bundled fallback corpus (T-0270): `python -m etl.fallback`, through its shipping entry point.

Every build here runs `fallback.main([...])` - the command the committed file was built with - over an OSM XML
stream, and reads the rows back out of the sqlite it wrote. The selection is pinned two ways: by exact equality
over T-0266's allowlist fixture (every class under its cap, so the whole selection is kept), and at EVERY
per-class cap, one below, on and one above it, over streams this file writes (task Log, rulings F2/F3).
"""
from __future__ import annotations

import collections
import hashlib
import pathlib
import sqlite3

import pytest

from etl import corpus, fallback, geom, placeallow, schema
from etl.segid import place_id

from .test_placeallow import EXPECTED

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
ALLOWLIST_XML = FIXTURES / "places_allowlist.osm.xml"
FULL_EXTRACT = FIXTURES / "corpus_extract.json"
BUILT_AT = "2026-10-06T00:00:00Z"

# Ruling F2, typed out: the table is the rule, in its order - scenic first, cafes last.
RULED_CAPS = (
    ("viewpoint", 200), ("peak", 200), ("waterfall", 200), ("beach", 200), ("trailhead", 200),
    ("museum", 150), ("garden", 150), ("park", 400), ("town", 150), ("cafe", 50),
)
# One OSM node tag per class, each the class's own placeallow.ALLOWLIST row.
NODE_TAG = {"viewpoint": ("tourism", "viewpoint"), "peak": ("natural", "peak"),
            "waterfall": ("waterway", "waterfall"), "beach": ("natural", "beach"),
            "trailhead": ("highway", "trailhead"), "museum": ("tourism", "museum"),
            "garden": ("leisure", "garden"), "park": ("leisure", "park"), "town": ("place", "town"),
            "cafe": ("amenity", "cafe")}


def run(tmp_path, osm_xml, name="fallback.sqlite", built_at=BUILT_AT):
    out = tmp_path / name
    code = fallback.main(["--places-osm", str(osm_xml), "--out", str(out), "--built-at", built_at,
                          "--region", "la"])
    return code, out


def query(path, sql):
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def meta(path):
    return dict(query(path, "SELECT key, value FROM meta"))


def count_lines(out, selected_from, kept):
    """The command's whole stdout, recomputed from the file it wrote: the kept count per class in the ruled
    table's order (0 for a class with none), their sum, the file's size against the ruled literal, and both
    digests (content_sha256 as meta stores it, file_sha256 over the bytes)."""
    per_class = " ".join(f"{cls}={kept.get(cls, 0)}" for cls, _cap in RULED_CAPS)
    return (f"FALLBACK selected_from={selected_from} places={sum(kept.values())} {per_class}\n"
            f"FALLBACK bytes={out.stat().st_size} budget=1048576\n"
            f"FALLBACK content_sha256={meta(out)['content_sha256']}\n"
            f"FALLBACK file_sha256={hashlib.sha256(out.read_bytes()).hexdigest()}\n")


def nodes_xml(tmp_path, cls, n):
    key, value = NODE_TAG[cls]
    body = "".join(
        f'<node id="{i}" lat="34.{i:04d}" lon="-118.{i:04d}"><tag k="{key}" v="{value}"/>'
        f'<tag k="name" v="Fixture {cls} {i}"/></node>' for i in range(1, n + 1))
    path = tmp_path / f"{cls}-{n}.osm.xml"
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?><osm version="0.6">{body}</osm>', encoding="utf-8")
    return path


def test_the_cap_table_is_the_ruled_table():
    assert fallback.CAPS == RULED_CAPS


def test_the_cap_table_covers_exactly_the_allowlist_classes():
    assert sorted(cls for cls, _cap in fallback.CAPS) == sorted(placeallow.CLASSES)


def test_the_ceiling_is_the_ruled_literal():
    assert fallback.FALLBACK_BUDGET_BYTES == 1048576


def test_the_selection_over_the_allowlist_fixture_is_exact(tmp_path, capsys):
    code, out = run(tmp_path, ALLOWLIST_XML)
    assert code == 0
    printed = capsys.readouterr()
    assert printed.out == count_lines(out, 39, collections.Counter(cls for _t, _i, cls, *_rest in EXPECTED))
    assert printed.err == ""
    got = query(out, "SELECT place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7 FROM places ORDER BY place_id")
    want = sorted((place_id(t, i), t, i, cls, name, geom.to_e7(lon), geom.to_e7(lat))
                  for t, i, cls, name, lat, lon in EXPECTED)
    assert got == want
    assert len(got) == 39


BOUNDS = [(cls, n, min(n, cap)) for cls, cap in RULED_CAPS for n in (cap - 1, cap, cap + 1)]


@pytest.mark.parametrize("cls,n,kept", BOUNDS, ids=[f"{c}-{n}" for c, n, _k in BOUNDS])
def test_every_class_cap_holds_at_its_bound(tmp_path, capsys, cls, n, kept):
    code, out = run(tmp_path, nodes_xml(tmp_path, cls, n))
    assert code == 0
    assert capsys.readouterr().out == count_lines(out, n, {cls: kept})
    got = [r[0] for r in query(out, "SELECT osm_id FROM places ORDER BY place_id")]
    want = sorted(range(1, n + 1), key=lambda i: place_id("n", i))[:kept]
    assert got == want
    assert len(got) == kept
    assert query(out, f"SELECT cls, count(*) FROM places GROUP BY cls") == [(cls, kept)]


MALFORMED_BUILT_AT = ["2026-10-06", "2026-10-06T00:00:00", "2026-10-06 00:00:00Z", "2026-13-06T00:00:00Z", ""]


@pytest.mark.parametrize("built_at", MALFORMED_BUILT_AT)
def test_a_malformed_built_at_exits_2_and_writes_nothing(tmp_path, capsys, built_at):
    code, out = run(tmp_path, ALLOWLIST_XML, built_at=built_at)
    assert code == 2
    printed = capsys.readouterr()
    assert printed.out == ""
    assert printed.err == f"--built-at must be YYYY-MM-DDTHH:MM:SSZ, got {built_at!r}\n"
    assert not out.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == []


def test_a_class_outside_the_table_is_refused():
    with pytest.raises(ValueError, match="pub"):
        fallback.choose([{"osm_type": "n", "osm_id": 1, "cls": "pub", "name": "Neary's Pub",
                          "lat": 34.0, "lon": -118.0}])


def test_two_builds_of_one_input_are_byte_identical(tmp_path):
    _c1, one = run(tmp_path, ALLOWLIST_XML, name="one.sqlite")
    _c2, two = run(tmp_path, ALLOWLIST_XML, name="two.sqlite")
    digests = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (one, two)]
    assert digests[0] == digests[1]


def test_the_fallback_is_a_full_corpus_schema_with_no_ways(tmp_path):
    _code, out = run(tmp_path, ALLOWLIST_XML)
    full = tmp_path / "full.sqlite"
    corpus.build(FULL_EXTRACT, full, BUILT_AT)
    pragmas = "SELECT * FROM pragma_application_id, pragma_user_version"
    assert query(out, pragmas) == query(full, pragmas) == [(schema.APPLICATION_ID, schema.SCHEMA_VERSION)]
    tables = "SELECT type, name, sql FROM sqlite_schema ORDER BY type, name"
    assert query(out, tables) == query(full, tables)
    m, f = meta(out), meta(full)
    for key in ("schema_version", "min_app_build", "build_complete", "table_licenses", "attribution",
                "odbl_notice"):
        assert m[key] == f[key], key
    assert m["schema_version"] == str(schema.SCHEMA_VERSION)
    assert m["build_complete"] == "1"
    assert m["kind"] == "fallback"
    assert "kind" not in f
    assert m["region"] == "la"
    for table in ("osm_features", "segments", "segments_rtree", "segment_alias", "curated"):
        assert query(out, f"SELECT count(*) FROM {table}") == [(0,)], table
    assert query(out, "SELECT count(*) FROM places") == [(39,)]
    assert query(out, "SELECT count(*) FROM places_rtree") == [(39,)]
    assert query(out, "SELECT count(*) FROM places_fts") == [(39,)]
    assert m["count.places"] == "39"


def test_the_odbl_table_licenses_name_every_places_table(tmp_path):
    _code, out = run(tmp_path, ALLOWLIST_XML)
    licenses = dict(pair.split("=") for pair in meta(out)["table_licenses"].split(";"))
    assert licenses == schema.TABLE_LICENSES
    for table in ("places", "places_rtree", "places_fts"):
        assert licenses[table] == "ODbL-1.0"


def test_a_fallback_at_or_over_the_ceiling_is_refused_and_left_on_disk(tmp_path, monkeypatch):
    _code, probe = run(tmp_path, ALLOWLIST_XML, name="probe.sqlite")
    size = probe.stat().st_size
    monkeypatch.setattr(fallback, "FALLBACK_BUDGET_BYTES", size)
    code, out = run(tmp_path, ALLOWLIST_XML)
    assert code == corpus.BUDGET_EXIT
    assert out.stat().st_size == size
    monkeypatch.setattr(fallback, "FALLBACK_BUDGET_BYTES", size + 1)
    code, _out = run(tmp_path, ALLOWLIST_XML, name="under.sqlite")
    assert code == 0
