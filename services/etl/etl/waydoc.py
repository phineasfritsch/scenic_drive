"""The clip -> the assembly's document: real geometry, real tags, real rasters, one row per road.

WHAT THIS IS. `etl.assemble` reads a JSON document of way rows and invokes every producer on them; until
this module there was no way to build that document out of an actual extract, so the assembly had only a
committed fixture (T-0146's half). This is the other half: `osmium cat` hands over the clip as XML, and this
walks it once, joins each way to its nodes, samples the DEM and WorldCover rasters through the same
`gdallocationinfo` seam `dem` and `landcover` already use, and writes the document `etl.assemble` consumes
UNEDITED - the assembly's contract does not move for this task.

THE REGION'S OWN TILES, NOT THE DEFAULT (rv2-pr106's carry-in). Elevation is sampled with
`tiles=dem.tiles_for_region(region_id)`. The default is every region we serve, and an LA point handed
sfbay's eight tiles is a silent None - absence by geography rather than by file, which no FileNotFoundError
can catch. The test asserts the tile set that reaches the sampler.

A ROW THAT CANNOT BE BUILT IS REFUSED BY NAME, NOT DROPPED. `assemble.assemble` refuses the whole region if
a row cannot be built, deliberately - dropping one moves every other way's rank by 1/n. So the refusals are
taken OUT of the population HERE, each with the producer and the reason that refused it, and travel in the
document's own `refused` list to `tagwriter`, which writes `scenic_refused=1` on those ways (ruling R2).
A way with no `highway` tag is neither: it is not a road, and it is counted as `not_a_road`.

THE LAND-COVER BUFFER FOLLOWS THE ROAD. `landcover.buffer_points` is a 150 m disc around ONE point; a way is
sampled every `LANDCOVER_STEP_M` = `landcover.BUFFER_M` metres, so the discs tile the road end to end
without a gap and without sampling the same ground twice. The 20 m grid inside the disc is
`landcover.BUFFER_STEP_M`, which was measured and argued in that module and is not re-decided here.

WHICH BYWAY ENTRIES TRAVEL. Only entries WITH a route key. `byways.route_matches` lets an entry with no
route key through on geometry alone - the weaker mode its own docstring names - and over tens of thousands
of ways that mode is also the slow path: every way would be measured against every unkeyed corridor. They
are dropped BY COUNT (`byways_no_route_key`), never in silence.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time

from . import byway_source, dem, fetch, landcover, osmxml, proximity, sinuosity, terrain
from .assemble import INFINITY
from .snap import length_m

ROOT = pathlib.Path(__file__).resolve().parents[1]
INPUTS = fetch.resolve_inputs_dir(ROOT)

HIGHWAY = "highway"
MIN_COORDINATES = 2
# The discs tile the road: one land-cover buffer every buffer-radius metres.
LANDCOVER_STEP_M = landcover.BUFFER_M
# How many raster reads one land-cover buffer is. Derived, never typed - it follows BUFFER_STEP_M.
LANDCOVER_SAMPLES_PER_POINT = len(landcover.buffer_points(34.0, -118.7))
# Ways per sampling batch. One gdallocationinfo process per tile per batch, so this trades processes against
# how many points are held at once; 500 ways is a few hundred thousand points, which is seconds and tens of MB.
CHUNK_WAYS = 500
METRES_PER_DEGREE = 111320.0

WHY_GEOMETRY = "geometry: fewer than %d nodes with coordinates in the clip" % MIN_COORDINATES
WHY_LENGTH = "furniture_per_km declined: the way has no length"
WHY_DEM = "dem: no elevation sample anywhere on the way"
WHY_LANDCOVER = "landcover: no valid sample in the buffer"
COUNT_NAMES = ("ways", "refused", "not_a_road", "byways", "byways_no_route_key")


def geometry(source):
    """One pass over the clip: node positions, the tags of the tagged nodes, and every way."""
    nodes: dict = {}
    node_tags: dict = {}
    ways: list = []
    for elem in osmxml.iter_top_level(source):
        if elem.tag == osmxml.NODE:
            node_id = int(elem.get("id"))
            nodes[node_id] = (float(elem.get("lat")), float(elem.get("lon")))
            tags = osmxml.tags_of(elem)
            if tags:
                node_tags[node_id] = tags
        elif elem.tag == osmxml.WAY:
            ways.append({"way_id": int(elem.get("id")), "tags": osmxml.tags_of(elem),
                         "refs": osmxml.refs_of(elem)})
    return nodes, node_tags, ways


def landcover_points(coords: list) -> list:
    """Every land-cover sample position for one way: a 150 m disc every 150 m along it."""
    out: list = []
    for lat, lon in terrain.resample(coords, step_m=LANDCOVER_STEP_M):
        out.extend(landcover.buffer_points(lat, lon))
    return out


def default_landcover(points: list) -> list:
    return landcover.sample_codes(points)


def bbox_of(line: list) -> tuple:
    lats = [p[0] for p in line]
    lons = [p[1] for p in line]
    return (min(lats), min(lons), max(lats), max(lons))


def within(a: tuple, b: tuple, radius_m: float) -> bool:
    """Whether two bounding boxes come within `radius_m` - the cheap reject before any real distance."""
    dlat = radius_m / METRES_PER_DEGREE
    dlon = dlat / max(math.cos(math.radians(a[0])), 1e-6)
    return not (a[2] + dlat < b[0] or b[2] + dlat < a[0] or a[3] + dlon < b[1] or b[3] + dlon < a[1])


def motorway_distance(coords: list, motorways: list) -> float:
    """Metres to the nearest motorway, with a bounding-box reject first.

    `proximity.meters_to_nearest_motorway` compares every segment pair, and a region's motorways against a
    region's ways is that product tens of thousands of times over. A motorway whose bounding box is further
    than the search radius cannot be the nearest one, and rejecting it changes no answer: beyond the radius
    the function returns infinity anyway.
    """
    box = bbox_of(coords)
    near = [line for line, line_box in motorways
            if within(box, line_box, proximity.MOTORWAY_SEARCH_RADIUS_M)]
    if not near:
        return math.inf
    return proximity.meters_to_nearest_motorway(coords, near)


def jsonable(value):
    """The same value with every set turned into a sorted list.

    `byway_source` keys its routes and admin orgs as SETS, which JSON cannot hold, and the document has to
    round-trip through a file to reach `etl.assemble`. Sorted rather than arbitrary order, because the
    document is an input to a byte-identical output (ruling R3).
    """
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def keep_byways(entries: list) -> tuple:
    """(entries with a route key, how many were dropped for not having one)."""
    kept = [jsonable(entry) for entry in entries if entry.get("routes")]
    return kept, len(entries) - len(kept)


def chunks(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def split(values: list, lengths: list) -> list:
    """`values` cut back into per-way lists of the given lengths, in order."""
    out = []
    at = 0
    for count in lengths:
        out.append(values[at:at + count])
        at += count
    return out


def row_for(way: dict, coords: list, node_tags: dict, profile: list, codes: list,
            motorways: list) -> dict:
    distance = motorway_distance(coords, motorways)
    return {"way_id": way["way_id"],
            "tags": way["tags"],
            "coords": [[lat, lon] for lat, lon in coords],
            "furniture_nodes": [node_tags[ref] for ref in way["refs"] if ref in node_tags],
            "landcover_codes": codes,
            "elevation_profile": profile,
            "sinuosity": sinuosity.way_sinuosity(coords),
            "tunnel_meters": proximity.tunnel_meters(coords, way["tags"]),
            "meters_to_nearest_motorway": INFINITY if math.isinf(distance) else distance}


def build(source, *, region_id: str, byway_entries=(), elevation=None, landcover=None,
          meta: dict | None = None, progress=None) -> dict:
    """The clip at `source` as the document `etl.assemble` reads. Pure wiring over the producers."""
    nodes, node_tags, ways = geometry(source)
    tiles = dem.tiles_for_region(region_id)
    sample_elevation = elevation or (lambda points: dem.sample_smoothed(points, tiles=tiles))
    sample_landcover = landcover or default_landcover

    roads: list = []
    refused: list = []
    not_a_road = 0
    for way in ways:
        if not way["tags"].get(HIGHWAY):
            not_a_road += 1
            continue
        coords = [nodes[ref] for ref in way["refs"] if ref in nodes]
        if len(coords) < MIN_COORDINATES:
            refused.append({"way_id": way["way_id"], "why": WHY_GEOMETRY})
        elif length_m(coords) <= 0.0:
            refused.append({"way_id": way["way_id"], "why": WHY_LENGTH})
        else:
            roads.append((way, coords))

    motorways = [(coords, bbox_of(coords)) for way, coords in roads
                 if proximity.is_motorway(way["tags"])]
    kept_byways, no_route_key = keep_byways(list(byway_entries))

    rows: list = []
    for batch in chunks(roads, CHUNK_WAYS):
        profiles = [terrain.resample(coords) for _way, coords in batch]
        buffers = [landcover_points(coords) for _way, coords in batch]
        heights = split(sample_elevation([p for points in profiles for p in points]),
                        [len(p) for p in profiles])
        codes = split(sample_landcover([p for points in buffers for p in points]),
                      [len(p) for p in buffers])
        for (way, coords), profile, cover in zip(batch, heights, codes):
            if all(value is None for value in profile):
                refused.append({"way_id": way["way_id"], "why": WHY_DEM})
            elif all(value is None for value in cover):
                refused.append({"way_id": way["way_id"], "why": WHY_LANDCOVER})
            else:
                rows.append(row_for(way, coords, node_tags, profile, cover, motorways))
        if progress:
            progress(len(rows), len(refused), len(roads))

    counts = {"ways": len(rows), "refused": len(refused), "not_a_road": not_a_road,
              "byways": len(kept_byways), "byways_no_route_key": no_route_key}
    document = {"region": region_id, "meta": dict(meta or {}), "ways": rows, "byways": kept_byways,
                "refused": refused, "counts": counts}
    document["meta"]["region"] = region_id
    return document


def count_line(counts: dict) -> str:
    return "WAYDOC " + " ".join("%s=%d" % (name, counts[name]) for name in COUNT_NAMES)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.waydoc", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the clip as OSM XML (osmium cat -o clip.osm.xml)")
    parser.add_argument("--region", required=True, help="the region whose DEM tiles are sampled")
    parser.add_argument("--window", default="", help="the bbox this clip was cut with, for the meta")
    parser.add_argument("--out", required=True, help="where to write the assembly document")
    parser.add_argument("--no-byways", action="store_true", help="build without the byway overlay")
    args = parser.parse_args(argv)

    entries = [] if args.no_byways else byway_source.load(INPUTS)
    started = time.time()

    def progress(rows, refusals, total):
        print("  waydoc %6d/%d rows, %d refused, %.0fs" % (rows + refusals, total, refusals,
                                                           time.time() - started), flush=True)

    document = build(pathlib.Path(args.input), region_id=args.region, byway_entries=entries,
                     meta={"window": args.window, "source": pathlib.Path(args.input).name,
                           "inputs": str(INPUTS)}, progress=progress)
    pathlib.Path(args.out).write_text(json.dumps(document) + "\n", encoding="utf-8", newline="\n")
    print(count_line(document["counts"]))
    return 0


if __name__ == "__main__":  # pragma: no cover - the module is exercised through `build`
    sys.exit(main())
