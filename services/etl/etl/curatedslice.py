"""The approach road of each curated seed, judged against the scored ways (T-0183 rulings R3 and R4).

THE PREDICATE (the plan's Curation row): the approach road within 300 m has GATE=1 and score >= 0.5.
  * GATE=1 - there is no such tag. tagwriter writes `scenic_gate=<reason>` only on a GATED way and
    `scenic_refused` only on a way no producer could score, so a way passes the gate when it carries
    `scenic_score_unit` and neither of the other two.
  * score - `scenic_score_unit`, the exact value, never the integer `scenic_score`, whose round-half-up
    would pass a 0.45 way as a 5.
  * WHICH road - `approach_hint` is the approach road's exact OSM name, and the approach road is the NEAREST
    highway way within RADIUS_M carrying that name (ties by way_id). "Any way within 300 m" would pass an
    overlook whose own approach is a gated dirt road, beside a good one.

THE SLICE. The tagged PBF is not committed, so CI judges a committed slice of it: every highway way within
RADIUS_M of any seed, with its tags and geometry, the input's sha256 and the seed coordinates it was cut for.
The input is OSM XML read by the shipping etl.osmxml reader, because the ETL image has osmium-tool and no
pyosmium; the operator recipe is

    osmium extract -b <seed boxes> -s complete_ways <region>-tagged.osm.pbf -o clip.pbf
    osmium cat clip.pbf -o clip.osm.xml
    python -m etl.curatedslice --input clip.osm.xml --region la --out tests/fixtures/la_curated_approach.json

and prints `CURATED SLICE seeds=N ways=M`. Nothing here reads a clock; two runs over one input are
byte-identical.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

from . import curated, geom, osmxml

RADIUS_M = 300.0
MIN_UNIT = 0.5
KEPT_TAGS = ("highway", "name", "scenic_gate", "scenic_refused", "scenic_score_unit")


def distance_m(seed: dict, way: dict) -> float:
    return geom.point_to_polyline_m((seed["lon"], seed["lat"]), [tuple(c) for c in way["coords"]])


def passes(way: dict) -> bool:
    """GATE=1 and score >= MIN_UNIT, read off the way's own tags."""
    if way.get("scenic_gate") is not None or way.get("scenic_refused") is not None:
        return False
    try:
        unit = float(way.get("scenic_score_unit"))
    except (TypeError, ValueError):
        return False
    return unit >= MIN_UNIT


def approach(seed: dict, ways: list):
    """The nearest way within RADIUS_M named the seed's approach_hint, or None."""
    best = None
    for way in ways:
        if way.get("name") != seed["approach_hint"]:
            continue
        d = distance_m(seed, way)
        if d <= RADIUS_M and (best is None or (d, way["way_id"]) < best[:2]):
            best = (d, way["way_id"], way)
    return None if best is None else best[2]


def approach_ok(seed: dict, ways: list) -> bool:
    """The plan's predicate: the approach road exists within RADIUS_M and passes."""
    way = approach(seed, ways)
    return way is not None and passes(way)


def read_ways(path) -> list:
    """Every highway way of an OSM XML file with all its nodes present, as slice rows."""
    nodes, ways = {}, []
    for elem in osmxml.iter_top_level(path):
        if elem.tag == osmxml.NODE:
            nodes[int(elem.get("id"))] = (float(elem.get("lon")), float(elem.get("lat")))
        elif elem.tag == osmxml.WAY:
            tags = osmxml.tags_of(elem)
            refs = [int(r) for r in osmxml.refs_of(elem)]
            if "highway" not in tags or any(r not in nodes for r in refs) or not refs:
                continue
            row = {"way_id": int(elem.get("id")), "coords": [list(nodes[r]) for r in refs]}
            row.update({k: tags.get(k) for k in KEPT_TAGS})
            ways.append(row)
    return ways


def cut(ways: list, seeds: list) -> list:
    """The ways within RADIUS_M of at least one seed, by way_id."""
    kept = [w for w in ways if any(distance_m(s, w) <= RADIUS_M for s in seeds)]
    return sorted(kept, key=lambda w: w["way_id"])


def seed_points(seeds: list) -> dict:
    return {s["id"]: [s["lat"], s["lon"]] for s in seeds}


def encode(source_sha256: str, seeds: list, ways: list) -> str:
    doc = {"radius_m": RADIUS_M, "seeds": seed_points(seeds), "source_sha256": source_sha256, "ways": ways}
    return json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n"


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.curatedslice", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, type=Path, help="OSM XML clip of the region's tagged PBF")
    parser.add_argument("--region", required=True)
    parser.add_argument("--root", type=Path, default=None, help="regions/ directory (default: the checkout's)")
    parser.add_argument("--today", required=True, type=datetime.date.fromisoformat,
                        help="the date the curated file is judged at (an input: no clock is read)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        seeds = curated.load(args.region, args.today, args.root)
    except curated.CurationError as err:
        print("CURATED SLICE REFUSED: %s" % err, file=sys.stderr)
        return 2
    ways = cut(read_ways(args.input), seeds)
    sha = hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.out.write_text(encode(sha, seeds, ways), encoding="utf-8", newline="\n")
    print("CURATED SLICE seeds=%d ways=%d" % (len(seeds), len(ways)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
