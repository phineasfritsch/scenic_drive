"""T-0275: the region build makes the FULL corpus - ways, segments and places - from its seam-deduped tile docs.

WHAT THIS FILE BINDS TO. `ops/etl-region --local corpus` - the script the LA measurement ran (in the ETL image,
where it execs the same `python -m regionbuild`) - and `regionbuild.cli.main`, over the TWO-TILE seam fixture
(fixtures/seam_window_a.json and seam_window_b.json, 12 ways each, three byte-identical shared ways) and the
allowlist places stream fixtures/places_allowlist.osm.xml, put in the store where the `places` stage writes.

EXACT EQUALITY. The stage's corpus is compared, table by table and row by row, to the file the SHIPPING
`etl.corpus.build` writes from `etl.extractadapter.adapt_document` over the first-tile-wins documents and
`placeallow.select` over the same stream, composed here: the stage adds nothing and drops nothing. The row
counts are ALSO literals, measured on this fixture (the task Log quotes the run).
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys

from etl import contentdigest, corpus, extractadapter, placeallow
from regionbuild import cli, fullcorpus
from regionbuild.layout import Layout

HERE = pathlib.Path(__file__).resolve().parent
ENTRY = HERE.parents[2] / "ops" / "etl-region"
TILES = {"seam_window_a": HERE / "fixtures" / "seam_window_a.json",
         "seam_window_b": HERE / "fixtures" / "seam_window_b.json"}
PLACES = HERE / "fixtures" / "places_allowlist.osm.xml"
REGION = "la"
BUILT_AT = "2026-10-06T00:00:00Z"
MULHOLLAND = 1533792498
SEAM_REFUSED = 3
TABLES = ("osm_features", "segments", "segments_rtree", "places", "places_rtree", "meta", "term_defs",
          "id_collisions", "curated", "terms_osm", "terms_raster")
# Measured on this fixture (T-0275 Log): 21 distinct ways of 24 rows, 37 segments, the 39 places placeallow keeps.
ROW_COUNTS = {"osm_features": 21, "segments": 37, "segments_rtree": 37, "places": 39, "places_rtree": 39}


def store(root: pathlib.Path, *, places: bool = True, tiles=TILES) -> tuple:
    layout = Layout(root, REGION)
    layout.docs.mkdir(parents=True)
    for tile in tiles:
        shutil.copyfile(TILES[tile], layout.doc_of(tile))
    if places:
        shutil.copyfile(PLACES, layout.places_xml)
    tile_list = root / "tiles.txt"
    tile_list.write_text("\n".join(sorted(TILES)) + "\n", encoding="utf-8")
    return layout, tile_list


def entry(layout: Layout, tile_list: pathlib.Path) -> subprocess.CompletedProcess:
    bash = shutil.which("bash")
    assert bash, "no bash on PATH: ops/etl-region cannot be run"
    return subprocess.run([bash, ENTRY.as_posix(), "--local", "corpus", "--work", str(layout.work),
                           "--tile-list", str(tile_list)],
                          env={**os.environ, "PYTHON": pathlib.Path(sys.executable).as_posix()},
                          capture_output=True, text=True)


def first_tile_wins() -> list:
    """The documents' ways, first tile in sorted order wins - merge.py's rule - recomposed here."""
    ways = {}
    for tile in sorted(TILES):
        for row in json.loads(TILES[tile].read_text(encoding="utf-8"))["ways"]:
            ways.setdefault(int(row["way_id"]), {"way_id": row["way_id"], "tags": row["tags"],
                                                 "coords": row["coords"]})
    return [ways[key] for key in sorted(ways)]


def expected_corpus(tmp: pathlib.Path) -> pathlib.Path:
    extract, _ = extractadapter.adapt_document({"region": REGION, "ways": first_tile_wins()}, region=REGION)
    extract["places"], _ = placeallow.select(str(PLACES))
    source = tmp / "expected-extract.json"
    source.write_text(json.dumps(extract), encoding="utf-8")
    out = tmp / "expected.sqlite"
    corpus.build(str(source), str(out), BUILT_AT, region=REGION)
    return out


def rows(path: pathlib.Path, table: str) -> list:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT * FROM %s ORDER BY 1, 2" % table).fetchall()
    finally:
        conn.close()


def digest(path: pathlib.Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return contentdigest.content_sha256(conn)
    finally:
        conn.close()


def test_the_region_build_runs_corpus_last_after_fallback():
    assert cli.ALL == ("motorways", "tiles", "docs", "reference", "score", "merge", "toxml", "tag", "topbf",
                       "check", "places", "fallback", "corpus")
    assert cli.HANDLERS["corpus"] is fullcorpus.run
    assert "corpus" not in cli.PLANLESS
    assert fullcorpus.BUILT_AT == BUILT_AT


def test_the_corpus_is_the_shipping_chain_over_the_first_tile_wins_documents(tmp_path):
    layout, tile_list = store(tmp_path / "work")
    run = entry(layout, tile_list)
    assert run.returncode == 0, run.stdout + run.stderr
    expected = expected_corpus(tmp_path)
    for table in TABLES:
        assert rows(layout.corpus, table) == rows(expected, table), table
    assert digest(layout.corpus) == digest(expected)
    for table, count in ROW_COUNTS.items():
        assert len(rows(layout.corpus, table)) == count, table
    merge_line = [line for line in run.stdout.splitlines() if line.startswith("CORPUS-MERGE ")]
    assert len(merge_line) == 1 and " rows_seen=24 ways=21 seam_ways=3 seam_differ=0 " in merge_line[0], run.stdout


def test_two_corpus_runs_have_one_content_digest(tmp_path):
    layout, tile_list = store(tmp_path / "work")
    first = entry(layout, tile_list)
    assert first.returncode == 0, first.stdout + first.stderr
    once = (digest(layout.corpus), contentdigest.file_sha256(layout.corpus))
    second = entry(layout, tile_list)
    assert second.returncode == 0, second.stdout + second.stderr
    assert (digest(layout.corpus), contentdigest.file_sha256(layout.corpus)) == once


def test_a_seam_way_whose_coords_differ_refuses_and_writes_no_corpus(tmp_path):
    layout, tile_list = store(tmp_path / "work")
    before = entry(layout, tile_list)
    assert before.returncode == 0 and layout.corpus.exists(), before.stdout + before.stderr
    doc = json.loads(layout.doc_of("seam_window_b").read_text(encoding="utf-8"))
    row = next(row for row in doc["ways"] if int(row["way_id"]) == MULHOLLAND)
    row["coords"][0] = [row["coords"][0][0] + 0.001, row["coords"][0][1]]
    layout.doc_of("seam_window_b").write_text(json.dumps(doc), encoding="utf-8")
    run = entry(layout, tile_list)
    assert run.returncode == SEAM_REFUSED, run.stdout + run.stderr
    assert "CORPUS REFUSED" in run.stdout and str(MULHOLLAND) in run.stdout, run.stdout
    assert not layout.corpus.exists() and not layout.corpus_doc.exists()


def test_a_store_without_places_or_a_tile_doc_is_refused(tmp_path):
    for kwargs in ({"places": False}, {"tiles": ("seam_window_a",)}):
        layout, tile_list = store(tmp_path / ("work-" + "".join(sorted(kwargs))), **kwargs)
        run = entry(layout, tile_list)
        assert run.returncode == 2, (kwargs, run.stdout + run.stderr)
        assert "CORPUS REFUSED" in run.stdout and not layout.corpus.exists(), (kwargs, run.stdout)


def test_a_corpus_over_its_budget_is_measured_and_exits_budget_exit(tmp_path, monkeypatch, capsys):
    layout, tile_list = store(tmp_path / "work")
    monkeypatch.setattr(corpus, "CORPUS_BUDGET_BYTES", 1)
    code = cli.main(["corpus", "--work", str(layout.work), "--tile-list", str(tile_list), "--jobs", "1"])
    out = capsys.readouterr().out
    assert code == corpus.BUDGET_EXIT, out
    assert layout.corpus.exists()
    file_line = [line for line in out.splitlines() if line.startswith("CORPUS-FILE ")]
    size = layout.corpus.stat().st_size
    assert file_line == ["CORPUS-FILE bytes=%d budget=1 over_by=%d page_size=%d page_count=%d freelist_count=0"
                         % ((size, size - 1) + page_stats(layout.corpus))], out
    rows_line = [line for line in out.splitlines() if line.startswith("CORPUS-ROWS ")]
    assert len(rows_line) == 1 and " osm_features=%d " % ROW_COUNTS["osm_features"] in rows_line[0] + " ", out
    assert "CORPUS-DIGEST content_sha256=%s file_sha256=%s" % (
        digest(layout.corpus), contentdigest.file_sha256(layout.corpus)) in out.splitlines(), out


def page_stats(path: pathlib.Path) -> tuple:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("PRAGMA page_size").fetchone()[0], conn.execute("PRAGMA page_count").fetchone()[0]
    finally:
        conn.close()
