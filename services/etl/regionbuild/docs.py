"""Pass 1: every tile of the plan documented by `python -m etl.waydoc`, against the REGION motorway set.

T-0208's pass1c.sh, per tile: `osmium cat` the tile to XML, `etl.waydoc --region <r> --window <tile>
--motorways <region motorway set>`, keep the WAYDOC count line, delete the XML. `--motorways` is R1b: a
way's distance to the nearest motorway is measured to the whole region's set, not to whatever motorways
landed in its tile, or a seam way carries the x0.7 multiplier in one tile and not the other.
"""
from __future__ import annotations

import subprocess

from . import sweep


def run(layout, names, jobs: int) -> int:
    layout.docs.mkdir(parents=True, exist_ok=True)
    if not layout.motorways.exists():
        print("DOCS REFUSED: no region motorway set at %s - run the motorways stage" % layout.motorways)
        return 2

    def document(tile: str) -> tuple:
        xml, doc = layout.tile_xml(tile), layout.doc_of(tile)
        subprocess.run(["osmium", "cat", str(layout.tile_pbf(tile)), "-o", str(xml), "--overwrite"],
                       capture_output=True)
        if not xml.exists() or xml.stat().st_size == 0:
            return False, "osmium cat produced nothing"
        line, output = sweep.count_line(
            sweep.python_module("etl.waydoc", "--input", xml, "--region", layout.region, "--window", tile,
                                "--motorways", layout.motorways, "--out", doc), "WAYDOC")
        xml.unlink()
        if line is None:
            doc.unlink(missing_ok=True)
            return False, "waydoc: %s" % output.strip().splitlines()[-1:]
        return True, line

    failed = sweep.run(names, layout.doc_of, document, jobs, "TILE")
    present = sum(1 for name in names if layout.doc_of(name).exists())
    print("DOCS END %d docs of %d tiles, %d failed %s" % (present, len(names), len(failed), " ".join(failed)),
          flush=True)
    return 1 if failed or present != len(names) else 0
