"""The three LA windows' top tens and the seam re-measure, read off THE TAGGED ARTIFACT.

T-0208's windows.sh + windows_top.py. Each window is cut out of `<region>-tagged.osm.pbf` with `osmium
extract -b` (complete_ways, the cut T-0168 and T-0204 made), read back with `osmium cat`, and ranked by
`etl.scenecheck.top` - the symbol `ops/sane` runs. Nothing is re-scored: a wrong number here is a wrong
number in the artifact. The grid window is still cut in two at -118.45 and merged by way_id, because that
seam is the one T-0204 measured (160 of 190 ways disagreeing); every overlapping way is listed with both
halves' units and `seam_differ` is the count that must be 0.

The JSON goes into the work store's windows/, never into tests/fixtures: a snapshot reference is
re-recorded only by a human-initiated commit (CLAUDE.md).
"""
from __future__ import annotations

import json

from etl import assemble, scenecheck

from . import osm

ALL = 10 ** 9
FIXTURE_ROWS = 25
WINDOWS = {"canyon": "-118.95,33.98,-118.55,34.15",
           "grid-a": "-118.55,33.98,-118.45,34.15",
           "grid-b": "-118.45,33.98,-118.35,34.15"}
NAMED = (1533792498, 399301293)
SEAM_MERGE = ("T-0208: osmium extract still completes every way crossing -118.45, so a way on the "
              "seam is READ BACK TWICE - but both reads are of ONE tagged file written from ONE "
              "region normalisation population, so the two halves AGREE and the union by way_id has "
              "nothing to choose between. T-0204's rule (take the MAX of the two clips) is gone with "
              "the disagreement it existed to arbitrate. seam_ways lists every overlapping way with "
              "both halves' units; seam_differ is the count that must be 0.")


def ranked(rows: list) -> list:
    out = sorted(rows, key=lambda r: (-r["scenic_score"], -r["scenic_score_unit"], r["way_id"]))
    for rank, row in enumerate(out, start=1):
        row["rank"] = rank
    return out


def run(layout, names, jobs: int) -> int:
    del names, jobs
    out = layout.windows
    out.mkdir(parents=True, exist_ok=True)
    for name, bbox in WINDOWS.items():
        osm.run("osmium", "extract", "-b", bbox, layout.tagged, "-o", out / ("win-%s.osm.pbf" % name),
                "--overwrite")
        osm.run("osmium", "cat", out / ("win-%s.osm.pbf" % name), "-o", out / ("win-%s.osm.xml" % name),
                "--overwrite")
    merged = json.loads(layout.merged_table.read_text(encoding="utf-8"))["rows"]
    by_id = {int(row["way_id"]): row for row in merged}
    print("MERGED %s" % assemble.count_line(merged), flush=True)

    def read(name: str) -> tuple:
        path = out / ("win-%s.osm.xml" % name)
        rows = scenecheck.top(path, ALL)
        found = scenecheck.counts(path)
        in_window = [by_id[way_id] for way_id, _tags, _coords in scenecheck.read_ways(path) if way_id in by_id]
        print("WINDOW %-7s %s  %s" % (name, WINDOWS[name], scenecheck.count_line(found)), flush=True)
        print("WINDOW %-7s %s" % (name, assemble.count_line(in_window)), flush=True)
        return rows, found, in_window

    def dump(name: str, rows: list, meta: dict) -> None:
        path = out / ("%s_top25.json" % name)
        path.write_text(json.dumps({"meta": meta, "rows": rows[:FIXTURE_ROWS]}, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
        print("FIXTURE %s rows=%d bytes=%d" % (path.name, min(FIXTURE_ROWS, len(rows)), path.stat().st_size),
              flush=True)

    canyon_rows, canyon_counts, canyon_pop = read("canyon")
    canyon = ranked(canyon_rows)
    show("canyon", canyon)
    dump("canyon", canyon,
         {"window": "the canyon window: osmium extract -b %s out of la-tagged.osm.pbf" % WINDOWS["canyon"],
          "produced_by": "etl.scenecheck.top over the whole-LA region-normalised artifact (T-0208)",
          "read_back_from": "services/etl/work/la/la-tagged.osm.pbf, window cut and osmium cat read-back",
          "scored": len(canyon), "check4": scenecheck.count_line(canyon_counts),
          "assemble": assemble.count_line(canyon_pop)})

    a_rows, a_counts, a_pop = read("grid-a")
    b_rows, b_counts, b_pop = read("grid-b")
    left = {row["way_id"]: row for row in a_rows}
    right = {row["way_id"]: row for row in b_rows}
    seam = [{"way_id": way_id, "name": left[way_id]["name"], "highway": left[way_id]["highway"],
             "grid_a": left[way_id]["scenic_score_unit"], "grid_b": right[way_id]["scenic_score_unit"]}
            for way_id in sorted(set(left) & set(right))]
    differ = [entry for entry in seam if entry["grid_a"] != entry["grid_b"]]
    print("SEAM overlapping=%d differ=%d" % (len(seam), len(differ)), flush=True)
    for entry in differ[:10]:
        print("   DIFFER way %(way_id)d %(name)s  a=%(grid_a).4f b=%(grid_b).4f" % entry, flush=True)
    for named in NAMED:
        entry = next((e for e in seam if e["way_id"] == named), None)
        print("   NAMED way %d %s" % (named, "absent from the overlap" if entry is None else
                                      "%s a=%.4f b=%.4f" % (entry["name"], entry["grid_a"], entry["grid_b"])),
              flush=True)

    grid = ranked(list({**right, **left}.values()))
    show("grid", grid)
    dump("grid", grid,
         {"window": "the mixed grid window: osmium extract -b -118.55,33.98,-118.35,34.15 out of "
                    "la-tagged.osm.pbf, cut in two at -118.45 (grid-a, grid-b) and merged over the union "
                    "by way_id",
          "produced_by": "etl.scenecheck.top over the whole-LA region-normalised artifact (T-0208)",
          "read_back_from": "services/etl/work/la/la-tagged.osm.pbf, two window cuts and osmium cat read-backs",
          "scored": len(grid),
          "check4_grid_a": scenecheck.count_line(a_counts), "check4_grid_b": scenecheck.count_line(b_counts),
          "assemble_grid_a": assemble.count_line(a_pop), "assemble_grid_b": assemble.count_line(b_pop),
          "seam_merge": SEAM_MERGE, "seam_ways": seam, "seam_differ": len(differ)})
    return 1 if differ else 0


def show(name: str, rows: list) -> None:
    print("TOPTEN %s" % name, flush=True)
    for row in rows[:10]:
        print("   %2d  %-10d  %-34s  %-12s  %d  (%.4f)"
              % (row["rank"], row["way_id"], row["name"][:34], row["highway"],
                 row["scenic_score"], row["scenic_score_unit"]), flush=True)
