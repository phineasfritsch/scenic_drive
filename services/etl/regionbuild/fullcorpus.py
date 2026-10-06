"""The `corpus` stage of a region build (T-0275): the FULL corpus - ways, segments, places - and its measurement.

    corpus    the pass-1 tile documents, FIRST TILE IN SORTED ORDER WINS (merge.py's rule), into ONE ways
              document <region>-corpus-doc.json of {way_id, tags, coords} - the only keys the adapter reads;
              then the SHIPPING `etl.extractadapter.main --places-osm <region>-places.osm.xml` into
              <region>-corpus-extract.json; then the SHIPPING `etl.corpus.main` into <region>-corpus.sqlite;
              then the file is measured whatever etl.corpus answered (T-0275 R4)

A seam way whose tags or coords differ between two tiles REFUSES the stage (merge.SEAM_REFUSED) and writes
nothing: `osmium extract -c` completes a border way, so two copies that disagree mean the tiles were cut from
different inputs. A plan tile with no document, or a store with no places stream, is refused (exit 2).

etl.corpus leaves an over-budget file ON DISK and exits BUDGET_EXIT (T-0206 R4); this stage measures that file
- rows per table, bytes against the budget, sqlite page and freelist stats, dbstat bytes per table where the
sqlite build has dbstat, the content digest - and returns etl.corpus's exit code. It picks no reduction.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import time

from etl import contentdigest, corpus, extractadapter

from .merge import SEAM_REFUSED

# T-0270's stamp: an INPUT, never a clock (P-DATA-01).
BUILT_AT = "2026-10-06T00:00:00Z"
REFUSED = 2
KEPT = ("way_id", "tags", "coords")
SHOWN = 10


def merged_ways(paths: list) -> tuple:
    """(ways by way_id, first tile wins; rows seen; seam way ids; disagreements) over the tile documents."""
    ways = {}
    seen = 0
    seam = set()
    differ = []
    for path in paths:
        for row in json.loads(path.read_text(encoding="utf-8"))["ways"]:
            seen += 1
            way = {key: row[key] for key in KEPT}
            way_id = int(way["way_id"])
            if way_id in ways:
                seam.add(way_id)
                if (ways[way_id]["tags"], ways[way_id]["coords"]) != (way["tags"], way["coords"]):
                    differ.append((way_id, path.name))
                continue
            ways[way_id] = way
    return ways, seen, seam, differ


def measure(path: pathlib.Path, budget: int) -> None:
    """The measurement lines over whatever corpus file exists (refused for size or not)."""
    conn = sqlite3.connect(str(path))
    try:
        names = [name for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        counts = " ".join("%s=%d" % (name, conn.execute('SELECT count(*) FROM "%s"' % name).fetchone()[0])
                          for name in names)
        print("CORPUS-ROWS %s" % counts, flush=True)
        size = path.stat().st_size
        pragma = [conn.execute("PRAGMA %s" % name).fetchone()[0]
                  for name in ("page_size", "page_count", "freelist_count")]
        print("CORPUS-FILE bytes=%d budget=%d over_by=%d page_size=%d page_count=%d freelist_count=%d"
              % (size, budget, size - budget, *pragma), flush=True)
        try:
            stat = conn.execute("SELECT name, sum(pgsize) FROM dbstat GROUP BY name "
                                "ORDER BY sum(pgsize) DESC, name").fetchall()
            print("CORPUS-DBSTAT %s" % " ".join("%s=%d" % pair for pair in stat), flush=True)
        except sqlite3.OperationalError:
            print("CORPUS-DBSTAT unavailable sqlite=%s" % sqlite3.sqlite_version, flush=True)
        content = contentdigest.content_sha256(conn)
    finally:
        conn.close()
    print("CORPUS-DIGEST content_sha256=%s file_sha256=%s" % (content, contentdigest.file_sha256(path)),
          flush=True)


def run(layout, names, jobs) -> int:
    del jobs
    absent = sorted(name for name in names if not layout.doc_of(name).exists())
    if absent:
        print("CORPUS REFUSED: %d tile(s) of the plan have no document: %s" % (len(absent), " ".join(absent)),
              flush=True)
        return REFUSED
    if not layout.places_xml.is_file():
        print("CORPUS REFUSED: no places stream %s (run the places stage)" % layout.places_xml, flush=True)
        return REFUSED
    for stale in (layout.corpus_doc, layout.corpus_extract, layout.corpus):
        if stale.exists():
            stale.unlink()

    begun = time.monotonic()
    files = sorted((layout.doc_of(name) for name in names), key=lambda path: path.name)
    ways, seen, seam, differ = merged_ways(files)
    if differ:
        print("CORPUS REFUSED tiles=%d ways=%d seam_ways=%d seam_differ=%d"
              % (len(files), len(ways), len(seam), len(differ)), flush=True)
        for way_id, tile in differ[:SHOWN]:
            print("   DIFFER way %d  (%s)" % (way_id, tile), flush=True)
        return SEAM_REFUSED
    document = {"region": layout.region, "ways": [ways[key] for key in sorted(ways)],
                "meta": {"window": layout.region, "source": "tile documents, first tile wins"}}
    del ways
    layout.corpus_doc.write_text(json.dumps(document, separators=(",", ":")) + "\n", encoding="utf-8",
                                 newline="\n")
    print("CORPUS-MERGE tiles=%d rows_seen=%d ways=%d seam_ways=%d seam_differ=0 doc_bytes=%d %.0fs"
          % (len(files), seen, len(document["ways"]), len(seam), layout.corpus_doc.stat().st_size,
             time.monotonic() - begun), flush=True)
    del document

    begun = time.monotonic()
    code = extractadapter.main(["--input", str(layout.corpus_doc), "--out", str(layout.corpus_extract),
                                "--region", layout.region, "--places-osm", str(layout.places_xml)])
    print("CORPUS-ADAPT exit=%d extract_bytes=%d %.0fs"
          % (code, layout.corpus_extract.stat().st_size if layout.corpus_extract.exists() else 0,
             time.monotonic() - begun), flush=True)
    if code != 0:
        return code

    begun = time.monotonic()
    code = corpus.main(["--input", str(layout.corpus_extract), "--out", str(layout.corpus),
                        "--built-at", BUILT_AT, "--region", layout.region])
    print("CORPUS-BUILD exit=%d %.0fs" % (code, time.monotonic() - begun), flush=True)
    if layout.corpus.exists():
        measure(layout.corpus, corpus.CORPUS_BUDGET_BYTES)
    return code
