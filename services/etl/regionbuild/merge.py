"""Pass 3: the tiles' scored tables into the ONE table the writer tags from - and the seam, re-measured.

T-0208's pass3_merge.py. `osmium extract` completes a way that crosses a tile edge, so a way on a border is
scored in two tiles. Under one region reference and one region motorway set its two rows must carry the
SAME score; this is where that is counted rather than asserted. The merged table takes the FIRST TILE IN
SORTED TILE ORDER, the rule `region_reference.merge` takes, so the tagged PBF carries one row per way.

Where pass3_merge.py printed a disagreement and wrote the table anyway, this stage REFUSES (exit 3) and
writes nothing: a seam way with two scores is the defect T-0208 existed to end, and the artifact built
over it would be tagged from whichever tile sorted first.
"""
from __future__ import annotations

import collections
import json
import multiprocessing
import pathlib
import time

from etl import assemble

SEAM_REFUSED = 3
SHOWN = 10


def refusals_of(path: str) -> list:
    """One document's refusals - the only field of the (large) documents the writer needs."""
    return list(json.loads(pathlib.Path(path).read_text(encoding="utf-8")).get("refused") or [])


def merged_rows(paths: list) -> tuple:
    """(rows by way_id, first tile wins; ways seen more than once; disagreements) over the scored files."""
    rows = {}
    seen = collections.Counter()
    disagree = []
    for path in paths:
        for row in json.loads(path.read_text(encoding="utf-8"))["rows"]:
            way_id = row["way_id"]
            seen[way_id] += 1
            if way_id in rows:
                if rows[way_id]["score"] != row["score"]:
                    disagree.append((way_id, rows[way_id]["score"], row["score"], path.name))
                continue
            rows[way_id] = row
    return rows, [way_id for way_id, count in seen.items() if count > 1], disagree


def run(layout, names, jobs: int) -> int:
    started = time.time()
    absent = sorted(name for name in names if not layout.scored_of(name).exists())
    if absent:
        print("MERGE REFUSED: %d tile(s) of the plan are not scored: %s" % (len(absent), " ".join(absent)))
        return 2
    files = sorted((layout.scored_of(name) for name in names), key=lambda path: path.name)
    rows, seam, disagree = merged_rows(files)
    if disagree:
        print("MERGE REFUSED tiles=%d ways=%d seam_ways=%d seam_differ=%d"
              % (len(files), len(rows), len(seam), len(disagree)), flush=True)
        for entry in disagree[:SHOWN]:
            print("   DISAGREE way %d  %s vs %s  (%s)" % entry, flush=True)
        return SEAM_REFUSED
    table = [rows[way_id] for way_id in sorted(rows)]
    layout.merged_table.write_text(json.dumps({"rows": table}) + "\n", encoding="utf-8", newline="\n")

    docs = [str(path) for path in sorted((layout.doc_of(name) for name in names), key=lambda path: path.name)]
    if jobs > 1:
        with multiprocessing.Pool(jobs) as pool:
            batches = pool.map(refusals_of, docs)
    else:
        batches = [refusals_of(path) for path in docs]
    by_id = {}
    for entry in (entry for batch in batches for entry in batch):
        by_id.setdefault(entry["way_id"], entry)
    layout.merged_doc.write_text(
        json.dumps({"region": layout.region, "ways": [], "byways": [],
                    "refused": [by_id[key] for key in sorted(by_id)],
                    "meta": {"window": layout.region, "source": layout.clip.name}}) + "\n",
        encoding="utf-8", newline="\n")

    print("MERGE tiles=%d ways=%d seam_ways=%d seam_differ=%d refused=%d %.0fs"
          % (len(files), len(rows), len(seam), len(disagree), len(by_id), time.time() - started), flush=True)
    print("MERGE %s" % assemble.count_line(table), flush=True)
    print("MERGE table_bytes=%d document_bytes=%d"
          % (layout.merged_table.stat().st_size, layout.merged_doc.stat().st_size), flush=True)
    return 0
