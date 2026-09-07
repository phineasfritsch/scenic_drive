"""The three conditions that decide which oracle ways the five-step method is comparable on.

This module exists because agent/reviewer-30 found the fixture could not be regenerated: `oracle.build` wrote
a file whose selection had actually been done by throwaway scripts in a temp directory, and the intermediates
were gone. A fixture nobody can rebuild is not evidence, it is a number someone once produced - which is the
same failure as an oracle regenerated from our own output, one level up.

The conditions, and why each excludes what it does:

  1. SINGLE-WAY COLLECTION. Curvature runs its deflection filter across a whole collection - every way in it
     joined end to end - so a way sharing a collection with others can have segments zeroed by a straight run
     in a neighbour. Handled in `oracle.single_way_collections`.
  2. GEOMETRY IDENTICAL to the KML's own <coordinates>. Each Placemark carries the geometry Curvature
     actually computed over; OSM has moved since. 726 of 3297 ways differ, and those agree 29.6% of the time
     against 90.4% for unchanged geometry - so comparing them compares two different roads.
  3. NO SQUASH EXPOSURE. processing_chains/adams_default.sh runs six squash post-processors after the five
     steps this repo implements. A way carrying a junction=roundabout/circular, traffic_calming or
     parking:lane tag, or within 30 m of a tagged node, has had its published value modified by a step we do
     not implement.

Excluding on 3 is the one that could be argued into a cherry-pick, so it is defined by the SOURCE of the
squashes rather than by which ways happen to disagree: the tag list here is read off adams_default.sh. That
principle is only worth anything if it is applied strictly - see WAY_TAGS for the one place it was not, and
what it cost.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from . import curvature as cv
from . import oracle

# From adams_default.sh's squash_curvature_near_tagged_nodes invocations.
NODE_TAGS: dict[str, set[str] | None] = {
    "highway": {"stop", "give_way", "traffic_signals", "crossing", "mini_roundabout", "traffic_calming"},
    "traffic_calming": None,   # any value
    "barrier": None,
}
# From squash_curvature_for_tagged_ways and squash_curvature_for_ways: tag -> the values that trigger a
# squash, or None for "any value". Value-restricted because the SOURCE is value-restricted; matching the bare
# presence of the key excludes ways the published pipeline never touched.
WAY_TAGS: dict[str, set[str] | None] = {
    "junction": {"roundabout", "circular"},   # --tag junction --values roundabout,circular
    "traffic_calming": None,
}
# `oneway` is deliberately absent, and its absence is the correction of a real defect. The only processor in
# adams_default.sh that reads it is `squash_curvature_near_way_tag_change`, which squashes where the tag
# CHANGES BETWEEN ADJACENT WAYS IN A COLLECTION. Condition 1 admits only single-way collections, so there is
# no adjacent way and that processor structurally cannot fire on anything in this fixture's universe.
# Excluding on it dropped 77 of 264 no-squash exclusions for a mechanism that cannot reach them
# (agent/reviewer-30, who counted it). The module's stated principle - exclusions defined by the SOURCE of
# the squashes - was not actually true here: `oneway` was generalised from "this tag name appears somewhere
# in adams_default.sh" to "this tag marks a way as squash-exposed", which is a different and weaker claim.
# A tag belongs here only if a processor that can reach a SINGLE-WAY collection reads it.
WAY_TAG_PREFIXES = ("parking:lane",)   # broader than the source's value-restricted regex; 0 ways affected

SQUASH_RADIUS_M = 30.0        # every one of those steps uses --distance 30
GEOMETRY_TOL_M = 1.0          # a node that moved less than a metre is the same node re-rounded
CELL_DEG = 0.0005             # ~55 m of latitude; a grid, so the proximity test is not O(ways x nodes)


def load_export(path: Path) -> tuple[dict[int, list[tuple[float, float]]], dict[int, dict], list[tuple[float, float]]]:
    """Read `osmium export -f geojsonseq --add-unique-id=type_id` output.

    Returns way coordinates as (lat, lon) - osmium writes [lon, lat] and mixing them silently halves every
    distance at this latitude - plus way properties, plus the coordinates of every node carrying a squash tag.
    """
    ways: dict[int, list[tuple[float, float]]] = {}
    props: dict[int, dict] = {}
    tagged: list[tuple[float, float]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().rstrip(",")
            if not line.startswith("{"):
                continue
            try:
                feature = json.loads(line)
            except json.JSONDecodeError:
                continue
            ident = str(feature.get("id") or "")
            geom = feature.get("geometry") or {}
            p = feature.get("properties") or {}
            if ident.startswith("w") and geom.get("type") == "LineString":
                wid = int(ident[1:])
                ways[wid] = [(lat, lon) for lon, lat in geom["coordinates"]]
                props[wid] = p
            elif ident.startswith("n") and geom.get("type") == "Point":
                for key, values in NODE_TAGS.items():
                    v = p.get(key)
                    if v is not None and (values is None or v in values):
                        lon, lat = geom["coordinates"]
                        tagged.append((lat, lon))
                        break
    return ways, props, tagged


def node_grid(nodes: list[tuple[float, float]]) -> dict[tuple[int, int], list[tuple[float, float]]]:
    grid: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for lat, lon in nodes:
        grid.setdefault((int(lat / CELL_DEG), int(lon / CELL_DEG)), []).append((lat, lon))
    return grid


def near_tagged_node(coords, grid) -> bool:
    for lat, lon in coords:
        cy, cx = int(lat / CELL_DEG), int(lon / CELL_DEG)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for nlat, nlon in grid.get((cy + dy, cx + dx), ()):
                    if cv.distance_on_earth(lat, lon, nlat, nlon) <= SQUASH_RADIUS_M:
                        return True
    return False


def way_is_squash_tagged(props: dict) -> bool:
    for key, values in WAY_TAGS.items():
        if key not in props:
            continue
        if values is None or str(props[key]).strip().lower() in values:
            return True
    return any(k.startswith(WAY_TAG_PREFIXES) for k in props)


def same_geometry(ours, theirs, tol_m: float = GEOMETRY_TOL_M) -> bool:
    if len(ours) != len(theirs):
        return False
    return all(cv.distance_on_earth(a[0], a[1], b[0], b[1]) <= tol_m for a, b in zip(ours, theirs))


def eligible(export: Path, kmz: Path = oracle.KMZ):
    """Every way passing all three conditions, with the counts at each stage so the funnel is inspectable."""
    published = oracle.single_way_collections(kmz)
    kml_geom = oracle.kml_geometry(kmz)
    ways, props, tagged = load_export(export)
    grid = node_grid(tagged)

    stages = {"single_way": len(published), "have_geometry": 0, "geometry_identical": 0, "no_squash": 0}
    kept = []
    for way_id, meta in sorted(published.items()):
        ours = ways.get(way_id)
        theirs = kml_geom.get(way_id)
        if not ours or not theirs or len(ours) < 3:
            continue
        stages["have_geometry"] += 1
        if not same_geometry(ours, theirs):
            continue
        stages["geometry_identical"] += 1
        if way_is_squash_tagged(props.get(way_id, {})) or near_tagged_node(ours, grid):
            continue
        stages["no_squash"] += 1
        kept.append({
            "way_id": way_id,
            "name": meta["name"],
            "surface": meta["surface"],
            "oracle_curvature": meta["curvature"],
            "coords": [[round(lat, 7), round(lon, 7)] for lat, lon in ours],
        })
    return kept, stages


def build(fixture: Path, export: Path, kmz: Path = oracle.KMZ, cap: int = 400, seed: int = 20260907):
    kept, stages = eligible(export, kmz)
    sampled = list(kept)
    random.Random(seed).shuffle(sampled)
    sampled = sorted(sampled[:cap], key=lambda w: w["way_id"])
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(json.dumps({
        "source": "https://kml.roadcurvature.com/north_america/us/vermont.c_300.kmz",
        "source_sha256": "3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046",
        "osm_source": "https://download.geofabrik.de/north-america/us/vermont-latest.osm.pbf",
        "rebuild_with": "ops/etl-curvature-fixture",
        "selection": [
            "single-way collections only: Curvature's deflection filter runs across a whole collection",
            "geometry identical to the KML's own <coordinates> within 1 m: OSM has moved since the KMZ",
            "no squash post-processor in adams_default.sh can reach it: no junction=roundabout/circular, "
            "traffic_calming or parking:lane tag, and no tagged node within 30 m",
            f"deterministic sample of {cap} from {len(kept)} eligible, seed {seed}",
        ],
        "funnel": stages,
        "ways": sampled,
    }, indent=1) + "\n", encoding="utf-8", newline="\n")
    return len(sampled), stages
