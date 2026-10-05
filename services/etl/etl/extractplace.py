"""The extract's optional `places` array, as `places` rows (T-0254 ruling R7).

    {"osm_type": "n"|"w"|"r", "osm_id": <int > 0>, "cls": "<non-empty>", "name": "<str>"|null,
     "lat": <deg>, "lon": <deg>}

The POI join that fills it from OSM is another task; until it lands, an extract with no `places` key yields no
rows, so every existing build is unchanged. place_id is segid.place_id and the e7 pair is geom.to_e7 - the
same derivation and the same rounding the ways get - so nothing here invents a number.
"""
from __future__ import annotations

import json

from . import geom
from .segid import place_id

# places.osm_id is a SQLite INTEGER, a signed 64-bit value; a larger id cannot be stored.
OSM_ID_MAX = 2**63 - 1


def load_places(path) -> list:
    """(place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7) rows, sorted by place_id. Refuses rather than
    skips a malformed place: a dropped destination is a search that silently never finds it."""
    with open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    raw_places = doc.get("places", []) if isinstance(doc, dict) else None
    if not isinstance(raw_places, list):
        raise ValueError(f"{path}: 'places' must be an array when present")
    rows = [_row(raw, str(path)) for raw in raw_places]
    seen = set()
    for row in rows:
        if row[0] in seen:
            raise ValueError(f"{path}: place {row[1]}/{row[2]} appears twice")
        seen.add(row[0])
    rows.sort()
    return rows


def _row(raw, path: str) -> tuple:
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: a place is an object, got {raw!r}")
    osm_type = raw.get("osm_type")
    if osm_type not in ("n", "w", "r"):
        raise ValueError(f"{path}: osm_type must be n, w or r, got {osm_type!r}")
    osm_id = raw.get("osm_id")
    if not isinstance(osm_id, int) or isinstance(osm_id, bool) or not 0 < osm_id <= OSM_ID_MAX:
        raise ValueError(f"{path}: osm_id must be a positive integer, got {osm_id!r}")
    cls = raw.get("cls")
    if not isinstance(cls, str) or not cls:
        raise ValueError(f"{path}: place {osm_type}/{osm_id}: cls must be a non-empty string, got {cls!r}")
    name = raw.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError(f"{path}: place {osm_type}/{osm_id}: name must be a string or null, got {name!r}")
    lat, lon = _degrees(raw, "lat", path), _degrees(raw, "lon", path)
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        raise ValueError(f"{path}: place {osm_type}/{osm_id}: out of range: lat {lat}, lon {lon}")
    return (place_id(osm_type, osm_id), osm_type, osm_id, cls, name, geom.to_e7(lon), geom.to_e7(lat))


def _degrees(raw: dict, key: str, path: str):
    """The JSON number itself, unconverted: float() of a huge JSON integer raises OverflowError, while the
    range comparison in _row orders an int against a float exactly."""
    value = raw.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{path}: {key} must be a number, got {value!r}")
    return value
