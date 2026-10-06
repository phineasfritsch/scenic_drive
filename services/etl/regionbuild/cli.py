"""`python -m regionbuild <stage>`: the region build that made la-tagged.osm.pbf, one stage per call.

    motorways  the region's motorway/trunk set, cut once (waydoc --motorways reads it)
    tiles      the tile plan cut out of the clip, osmium extract -c
    docs       pass 1: etl.waydoc per tile, N at a time, resume by file presence
    reference  the ONE region reference over every tile's raw values; refuses a plan tile with no doc
    score      pass 2: etl.assemble --reference per tile, N at a time, resume by file presence
    merge      pass 3: one row per way, first tile wins; refuses (exit 3) when a seam way disagrees
    toxml      the clip to OSM XML
    tag        etl.tagwriter over the clip XML with the merged table and the merged refusals
    topbf      the tagged XML to <region>-tagged.osm.pbf, then its sha256 and size
    sha        the sha256 and size of <region>-tagged.osm.pbf
    check      osmium read-back of the artifact and python -m etl.scenecheck over it (CHECK4)
    windows    the three LA windows cut out of the artifact and ranked (T-0208's fixtures, into the store)
    places     the allowlist osmium pass over the unfiltered clip <region>.osm.pbf (T-0266), see places.py
    fallback   the places corpus the app bundles, into the store and to its bundle path (T-0270)
    corpus     the FULL corpus from the tile documents, first tile wins, measured (T-0275), see fullcorpus.py
    all        motorways through corpus, stopping at the first stage that does not exit 0

ops/etl-region is the entry point: it runs this inside the ETL image, or with --local on the host.
"""
from __future__ import annotations

import argparse
import pathlib
import os
import sys
import time

from . import docs, fullcorpus, merge, osm, places, reference, scoring, tiles, windows
from .layout import Layout
from .sweep import count_line, python_module

ALL = ("motorways", "tiles", "docs", "reference", "score", "merge", "toxml", "tag", "topbf", "check",
       "places", "fallback", "corpus")
STAGES = ALL + ("sha", "windows", "all")
# The places stages read the clip whole: no tile plan, so a region without one reaches its own refusal.
PLANLESS = ("places", "fallback")
WORK_ENV = "SCENIC_REGION_WORK"


def tag(layout, names, jobs) -> int:
    del names, jobs
    line, output = count_line(python_module("etl.tagwriter", "--input", layout.clip_xml,
                                            "--table", layout.merged_table, "--document", layout.merged_doc,
                                            "--out", layout.tagged_xml), "WRITE")
    print(line if line is not None else "TAG FAILED %s" % output.strip(), flush=True)
    return 0 if line is not None else 1


def check(layout, names, jobs) -> int:
    del names, jobs
    osm.to_xml(layout.tagged, layout.readback)
    line, output = count_line(python_module("etl.scenecheck", layout.readback, "--top", "0"), "CHECK4")
    print(line if line is not None else "CHECK FAILED %s" % output.strip(), flush=True)
    return 0 if line is not None else 1


HANDLERS = {
    "motorways": lambda layout, names, jobs: osm.motorways(layout),
    "tiles": lambda layout, names, jobs: osm.cut(layout, names),
    "docs": docs.run,
    "reference": reference.run,
    "score": scoring.run,
    "merge": merge.run,
    "toxml": lambda layout, names, jobs: osm.to_xml(layout.clip, layout.clip_xml),
    "tag": tag,
    "topbf": lambda layout, names, jobs: osm.to_pbf(layout.tagged_xml, layout.tagged),
    "sha": lambda layout, names, jobs: osm.sha(layout.tagged),
    "check": check,
    "windows": windows.run,
    "places": places.osmium_pass,
    "fallback": places.bundle,
    "corpus": fullcorpus.run,
}


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(prog="python -m regionbuild", description=__doc__.splitlines()[0])
    out.add_argument("stage", choices=STAGES)
    out.add_argument("--work", default=os.environ.get(WORK_ENV),
                     help="the work store (default $%s): the clip in, every stage's output" % WORK_ENV)
    out.add_argument("--region", default="la", help="the region whose tile plan is built (default la)")
    out.add_argument("--jobs", type=int, default=8, help="tiles at a time in docs/score, pool size elsewhere")
    out.add_argument("--tile-list", default=None, help="a file of tile names to build instead of the plan")
    out.add_argument("--bundle-root", default=None,
                     help="where fallback resolves the bundle path (default the checkout, /repo in the image)")
    return out


def main(argv: list | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.work:
        print("regionbuild: no work store - pass --work or set $%s" % WORK_ENV, file=sys.stderr)
        return 2
    layout = Layout(pathlib.Path(args.work), args.region)
    if args.tile_list:
        names = tiles.read_list(args.tile_list)
    elif args.stage in PLANLESS:
        names = []
    else:
        names = tiles.plan(args.region)
    for stage in (ALL if args.stage == "all" else (args.stage,)):
        begun = time.monotonic()
        print("STAGE %s start tiles=%d work=%s" % (stage, len(names), layout.work), flush=True)
        if stage == "fallback":
            code = places.bundle(layout, names, args.jobs, args.bundle_root)
        else:
            code = HANDLERS[stage](layout, names, args.jobs)
        print("STAGE %s exit=%d %.0fs" % (stage, code, time.monotonic() - begun), flush=True)
        if code != 0:
            return code
    return 0
