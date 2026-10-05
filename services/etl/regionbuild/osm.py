"""The osmium stages of a region build: the motorway set, the tile cut, and the XML/PBF conversions.

Each is the command T-0208 ran (its 17:26 extract entry and run_stage.sh), with the paths taken from the
layout. osmium is in the ETL image and nowhere else, which is why ops/etl-region runs the stages there.
"""
from __future__ import annotations

import hashlib
import subprocess

from . import tiles as tileplan

# proximity.MOTORWAY_CLASSES: the four classes waydoc measures a way's distance to (T-0208 R1b).
MOTORWAY_FILTER = "w/highway=motorway,motorway_link,trunk,trunk_link"
CHUNK = 1 << 20


def run(*command) -> str:
    """Run one osmium command, echo it, and return its stdout. A failure stops the stage."""
    command = [str(part) for part in command]
    print("RUN %s" % " ".join(command), flush=True)
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def way_count(path) -> int:
    return int(run("osmium", "fileinfo", "-e", "-g", "data.count.ways", path).strip())


def node_count(path) -> int:
    return int(run("osmium", "fileinfo", "-e", "-g", "data.count.nodes", path).strip())


def motorways(layout) -> int:
    """The region's whole motorway set, cut once, as the XML `waydoc --motorways` reads."""
    run("osmium", "tags-filter", layout.clip, MOTORWAY_FILTER, "-o", layout.motorways_pbf, "--overwrite")
    run("osmium", "cat", layout.motorways_pbf, "-o", layout.motorways, "--overwrite")
    print("MOTORWAYS ways=%d nodes=%d xml_bytes=%d"
          % (way_count(layout.motorways_pbf), node_count(layout.motorways_pbf), layout.motorways.stat().st_size),
          flush=True)
    return 0


def cut(layout, names) -> int:
    """Every tile of the plan out of the clip, `osmium extract -c`, complete_ways, a config at a time."""
    layout.tiles.mkdir(parents=True, exist_ok=True)
    paths = tileplan.write_configs(layout.region, names, layout.tiles, layout.configs)
    for path in paths:
        run("osmium", "extract", "-c", path, layout.clip, "--overwrite")
    counts = {name: way_count(layout.tile_pbf(name)) for name in names}
    empty = sorted(name for name, ways in counts.items() if ways == 0)
    print("TILES tiles=%d configs=%d ways=%d empty=%d"
          % (len(names), len(paths), sum(counts.values()), len(empty)), flush=True)
    for name in names:
        print("   TILE %-7s ways=%d" % (name, counts[name]), flush=True)
    return 1 if empty else 0


def to_xml(source, target) -> int:
    run("osmium", "cat", source, "-o", target, "--overwrite")
    print("XML %s bytes=%d" % (target.name, target.stat().st_size), flush=True)
    return 0


def to_pbf(source, target) -> int:
    run("osmium", "cat", source, "-o", target, "--overwrite")
    return sha(target)


def sha(path) -> int:
    """The artifact's name: sha256 and byte count, the two numbers the Log quotes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    print("SHA256 %s  bytes %d  %s" % (digest.hexdigest(), path.stat().st_size, path.name), flush=True)
    return 0
