"""Pass 1's second half: every tile's raw ranked values into ONE region reference table.

T-0208's pass2_reference.py. Tiles are read in SORTED TILE ORDER, which is what makes the dedup rule
("first tile wins", region_reference.merge) deterministic rather than a race - `Pool.imap` yields in the
order it was given, so the parallelism changes no number. Nothing here computes a rank: it builds the
records `assemble` would build and asks `region_reference` for the values that belong in each curve.

A REFERENCE THAT IS SHORT OF ITS REGION CANNOT BE SEEN IN ANY OF ITS OWN NUMBERS. T-0208's first reference
was built over 125 documents when the plan had 152 (27 tiles never documented; `ls | wc -l` matched the
wrong list by coincidence). So this stage refuses, by tile name, when any tile of the plan has no document.
"""
from __future__ import annotations

import json
import multiprocessing
import pathlib
import time

from etl import assemble, region_reference

PROGRESS_EVERY = 20


def values_of(path: str) -> tuple:
    """One document's contribution: `{term: {way_id: raw value}}` and its own way count."""
    document = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    byway_entries = list(document.get("byways") or [])
    records = [assemble.record_from_row(row, byway_entries) for row in document["ways"]]
    return len(records), region_reference.raw_values(records)


def ordered_docs(layout, names) -> list:
    """The plan's documents in sorted FILE-NAME order - the order `sorted(glob('*-doc.json'))` gave T-0208."""
    return sorted((layout.doc_of(name) for name in names), key=lambda path: path.name)


def missing(layout, names) -> list:
    return sorted(name for name in names if not layout.doc_of(name).exists())


def run(layout, names, jobs: int) -> int:
    absent = missing(layout, names)
    if absent:
        print("REFERENCE REFUSED: %d tile(s) of the plan have no document: %s" % (len(absent), " ".join(absent)))
        return 2
    started = time.time()
    paths = [str(path) for path in ordered_docs(layout, names)]
    tables = []
    ways = 0
    if jobs > 1:
        with multiprocessing.Pool(jobs) as pool:
            results = list(_progress(pool.imap(values_of, paths, chunksize=1), started))
    else:
        results = list(_progress(map(values_of, paths), started))
    for count, table in results:
        ways += count
        tables.append(table)
    merged = region_reference.merge(tables)
    table = region_reference.table_of(merged)
    sha = region_reference.dump(table, layout.reference)
    print("REFERENCE docs=%d ways=%d unique=%d %s"
          % (len(tables), ways, len(merged["curvature"]),
             " ".join("%s=%d" % pair for pair in sorted(region_reference.counts(table).items()))), flush=True)
    print("REFERENCE sha256 %s  bytes %d  %.0fs" % (sha, layout.reference.stat().st_size, time.time() - started),
          flush=True)
    return 0


def _progress(results, started: float):
    ways = 0
    for index, (count, table) in enumerate(results):
        ways += count
        if index % PROGRESS_EVERY == 0:
            print("  reference %3d docs, %7d ways, %.0fs" % (index + 1, ways, time.time() - started), flush=True)
        yield count, table
