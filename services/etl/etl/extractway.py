"""ExtractWay: one way as the corpus builder consumes it, and the JSON extract reader that produces them.

This slice's input is a committed JSON extract, not a PBF. osmium lives only inside the WSL image and this
tier of the suite runs on the host interpreter, so a PBF reader here would be a module nobody on this box
could execute. The JSON shape is deliberately the post-`tags-filter` shape - class already assigned, access
and surface already decided - so the real `osmium extract -> osm2pgsql --flex` path can be bolted in front of
it later without the builder changing at all.

The reader validates rather than trusts. Every field that reaches a CHECK constraint in schema.DDL is
checked here with the file name and the way id in the message, because a constraint violation 40 000 rows
into an INSERT names a row number and nothing a human can act on.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import geom
from .tagfilter import WAY_CLASSES

REQUIRED_WAY_KEYS = ("id", "cls", "highway", "paved", "access_ok", "oneway", "nodes")


@dataclass(frozen=True)
class ExtractWay:
    """One filtered OSM way. `coords` is already canonical - see geom.canonical."""

    way_id: int
    cls: str
    highway: str
    name: str | None
    paved: int
    access_ok: int
    oneway: int
    coords: tuple

    @property
    def node_count(self) -> int:
        return len(self.coords)

    @property
    def geom_sha256(self) -> bytes:
        """sha256 of the CANONICAL packed geometry. A way redrawn in the other direction hashes the same,
        which is what keeps a JOSM "Reverse Direction" out of the matcher entirely."""
        return hashlib.sha256(geom.pack(list(self.coords))).digest()

    @property
    def length_mm(self) -> int:
        return geom.cumulative_mm(list(self.coords))[-1]

    @property
    def is_closed(self) -> bool:
        return geom.is_closed(list(self.coords))


def _require(raw: dict, path: str) -> None:
    missing = [k for k in REQUIRED_WAY_KEYS if k not in raw]
    if missing:
        raise ValueError(f"{path}: way {raw.get('id', '?')} is missing {', '.join(missing)}")


def _flag(value, field: str, allowed: tuple, path: str, way_id) -> int:
    if value not in allowed:
        raise ValueError(f"{path}: way {way_id}: {field} must be one of {allowed}, got {value!r}")
    return int(value)


def way_from_json(raw: dict, path: str) -> ExtractWay:
    _require(raw, path)
    way_id = raw["id"]
    if not isinstance(way_id, int) or way_id <= 0:
        raise ValueError(f"{path}: way id must be a positive int, got {way_id!r}")
    cls = raw["cls"]
    if cls not in WAY_CLASSES:
        raise ValueError(f"{path}: way {way_id}: unknown class {cls!r}")
    highway = raw["highway"]
    if highway not in WAY_CLASSES[cls]:
        raise ValueError(f"{path}: way {way_id}: highway={highway!r} is not in class {cls!r}")
    nodes = raw["nodes"]
    if not isinstance(nodes, list) or len(nodes) < 2:
        raise ValueError(f"{path}: way {way_id}: needs at least 2 nodes, got {len(nodes) if nodes else 0}")
    coords = []
    for node in nodes:
        if not isinstance(node, list) or len(node) != 2:
            raise ValueError(f"{path}: way {way_id}: a node is [lat, lon], got {node!r}")
        lat, lon = float(node[0]), float(node[1])
        if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
            raise ValueError(f"{path}: way {way_id}: node out of range: {node!r}")
        coords.append((lat, lon))
    canon = geom.canonical(coords)
    name = raw.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError(f"{path}: way {way_id}: name must be a string or absent, got {name!r}")
    return ExtractWay(
        way_id=way_id,
        cls=cls,
        highway=highway,
        name=name,
        paved=_flag(raw["paved"], "paved", (0, 1), path, way_id),
        access_ok=_flag(raw["access_ok"], "access_ok", (0, 1), path, way_id),
        oneway=_flag(raw["oneway"], "oneway", (-1, 0, 1), path, way_id),
        coords=tuple(canon),
    )


def load_extract(path) -> tuple[str, list]:
    """(region, ways sorted by way_id). Sorted here, once, so no later loop has to remember to."""
    with open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict) or "ways" not in doc:
        raise ValueError(f"{path}: expected an object with a 'ways' array")
    region = doc.get("region")
    if not isinstance(region, str) or not region:
        raise ValueError(f"{path}: 'region' must be a non-empty string")
    ways = [way_from_json(raw, str(path)) for raw in doc["ways"]]
    seen = set()
    for way in ways:
        if way.way_id in seen:
            raise ValueError(f"{path}: way {way.way_id} appears twice")
        seen.add(way.way_id)
    ways.sort(key=lambda w: w.way_id)
    return region, ways
