"""Viewpoints and peaks for destinations and the 'why this is pretty' line - NEVER the per-way score (T-0241).

    landmarks, counts = landmarks.select(path_to_osm_xml)
    names = landmarks.explain(route_points, landmarks)        # up to two names the route passes
    way_id = landmarks.nearest_way_id((lat, lon), ways)       # the column T-0379 stores

WHY NOT A SCORE TERM. The OSM POI probe (2026-09-25) measured every per-way landmark form pointing the wrong
way (AUC 0.30-0.475 over the owner's good vs busy roads; PCH carries 11.5 weight/km, Latigo 0.21). So no module
under etl/ but this one may name a landmark: tests/test_landmarks_route.py holds that whitelist.

THE RULES (T-0241 Log, ruled before code):
  R3  which objects: placeallow.allow_row, the ONE binding places also uses, restricted to KINDS - a viewpoint
      node or way, a peak node. A relation is never a landmark here.
  R4  an unnamed object is kept with name None; a blank name is None; access private/no is refused.
  R5  ele: a bare number or `<n> m` is metres, `<n> ft` is feet; 0.1 m; anything else is None, never guessed.
  R6  the point is placeallow.locate's (a way is the mean of its distinct nodes), at 5 dp.
  R7  within NEAR_M, inclusive. explain measures the landmark to the route polyline; nearest_way_id the
      landmark to each way, ties to the lower way id.
  R9  explain names at most MAX_NAMED named landmarks, ordered by where the route first comes nearest; a name
      repeated (casefold) is said once.
"""
from __future__ import annotations

import re

from . import geom, osmxml, placeallow

KINDS = ("viewpoint", "peak")
ELE_KEY = "ele"
COORD_DP = 5
ELE_DP = 1
FOOT_M = 0.3048
FOOT = "ft"
NEAR_M = 300.0
MAX_NAMED = 2
ELE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(m|ft)?")
COUNT_NAMES = ("landmarks", "named", "refused_access", "skipped_geometry")


def elevation_m(raw):
    """Metres to 0.1, or None. `851` and `851 m` are metres, `2792 ft` is feet; any other text is None."""
    if not isinstance(raw, str):
        return None
    match = ELE.fullmatch(raw.strip())
    if match is None:
        return None
    value = float(match.group(1))
    if match.group(2) == FOOT:
        value = value * FOOT_M
    return round(value, ELE_DP)


def kind_of(osm_type: str, tags: dict):
    """The landmark kind of one OSM object, or None. placeallow's first matching row decides (R3)."""
    row = placeallow.allow_row(osm_type, tags)
    if row is None or row.cls not in KINDS:
        return None
    return row.cls


def node_ids_of(osm_type: str, osm_id: int, ways: dict):
    if osm_type == "n":
        return [osm_id]
    if osm_type == "w":
        return ways.get(osm_id)
    return None


def select(path) -> tuple:
    """(landmarks, counts) from one OSM XML file. A landmark is {osm_type, osm_id, kind, name, ele_m, lat,
    lon}, sorted by (osm_type in n, w, r order, osm_id)."""
    counts = {name: 0 for name in COUNT_NAMES}
    nodes, ways, found = {}, {}, []
    for elem in osmxml.iter_top_level(path):
        osm_type = placeallow.KIND_TYPE.get(elem.tag)
        if osm_type is None:
            continue
        osm_id = int(elem.get("id"))
        if osm_type == "n":
            nodes[osm_id] = (float(elem.get("lat")), float(elem.get("lon")))
        elif osm_type == "w":
            ways[osm_id] = osmxml.refs_of(elem)
        tags = osmxml.tags_of(elem)
        kind = kind_of(osm_type, tags)
        if kind is None:
            continue
        if tags.get(placeallow.ACCESS_KEY) in placeallow.REFUSED_ACCESS:
            counts["refused_access"] += 1
            continue
        found.append((osm_type, osm_id, kind, placeallow.name_of(tags), elevation_m(tags.get(ELE_KEY))))

    landmarks = []
    for osm_type, osm_id, kind, name, ele_m in found:
        where = placeallow.locate(node_ids_of(osm_type, osm_id, ways) or [], nodes)
        if where is None:
            counts["skipped_geometry"] += 1
            continue
        lat, lon, _bbox = where
        landmarks.append({"osm_type": osm_type, "osm_id": osm_id, "kind": kind, "name": name, "ele_m": ele_m,
                          "lat": round(lat, COORD_DP), "lon": round(lon, COORD_DP)})
    landmarks.sort(key=lambda lm: ("nwr".index(lm["osm_type"]), lm["osm_id"]))
    counts["landmarks"] = len(landmarks)
    counts["named"] = sum(1 for lm in landmarks if lm["name"] is not None)
    return landmarks, counts


def nearest_way_id(point: tuple, ways):
    """The id of the way nearest `point` (lat, lon) within NEAR_M inclusive, ties to the lower id; else None.
    `ways` is an iterable of (way_id, [(lat, lon), ...])."""
    best = None
    for way_id, coords in ways:
        distance = geom.point_to_polyline_m(point, coords)
        if distance <= NEAR_M and (best is None or (distance, way_id) < best):
            best = (distance, way_id)
    return None if best is None else best[1]


def explain(route: list, landmarks: list) -> list:
    """Up to MAX_NAMED names of named landmarks within NEAR_M (inclusive) of the route polyline
    [(lat, lon), ...], in the order the route first comes nearest to each."""
    if not route:
        return []
    legs = list(zip(route, route[1:])) or [(route[0], route[0])]
    hits = []
    for lm in landmarks:
        if lm["name"] is None:
            continue
        point = (lm["lat"], lm["lon"])
        distance, leg = min((geom.point_to_segment_m(point, a, b), i) for i, (a, b) in enumerate(legs))
        if distance <= NEAR_M:
            hits.append((leg, distance, lm["osm_id"], lm["name"]))
    names, said = [], set()
    for _leg, _distance, _osm_id, name in sorted(hits):
        if name.casefold() in said:
            continue
        said.add(name.casefold())
        names.append(name)
    return names[:MAX_NAMED]
