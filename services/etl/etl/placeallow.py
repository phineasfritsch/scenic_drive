"""The extract's `places` array from OSM: a typed allowlist, named features only, chains refused (T-0266).

    python -m etl.placeallow --expressions        the osmium tags-filter expressions, one per line
    osmium tags-filter -o places.osm.pbf la.osm.pbf $(python -m etl.placeallow --expressions)
    osmium cat places.osm.pbf -o places.osm.xml
    python -m etl.extractadapter --input <waydoc> --places-osm places.osm.xml --out <extract>

THE INPUT IS THE UNFILTERED REGION CLIP. The keep-pass clip (`tagfilter.keep_expressions`) holds none of the
cafe, museum, garden, trailhead or place tags, so the osmium pass above runs over `<region>.osm.pbf`. Its
expressions come from ALLOWLIST itself, so the filter and the selector cannot disagree about a tag. osmium
keeps the nodes a matching way refers to and the member ways (and their nodes) of a matching relation, which
is what lets an area be located here (measured on LA: every allowlisted way and relation complete).

THE RULES, each ruled in the task Log before code:
  R2  first ALLOWLIST row whose tag matches AND whose object types include the object's names its class;
      one object is one place. A peak drawn as a way is not a peak.
  R3  the `name` tag, stripped, non-empty - an unnamed place cannot be typed into search.
  R4  `access` private or no refuses the object, in every class.
  R5  a chain is refused: its brand:wikidata is a BLOCKLIST QID, or its brand casefolds to a BLOCKLIST
      brand, or its name's word tokens contain a BLOCKLIST phrase's tokens contiguously.
  R6  a node is its own point; a way the mean of its DISTINCT nodes; a relation the mean of the distinct
      nodes of its outer (or blank-role) member ways. 7 dp. Anything missing is skipped and counted.
  R7  a node inside the bbox (inclusive) of a same-class area whose name casefolds equal is the same
      feature: the node is kept, the area dropped and counted.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import NamedTuple

from . import osmxml

NAME_KEY = "name"
BRAND_KEY = "brand"
WIKIDATA_KEY = "brand:wikidata"
ACCESS_KEY = "access"
REFUSED_ACCESS = frozenset({"private", "no"})
OUTER_ROLES = frozenset({"outer", ""})
MEMBER = "member"
MEMBER_WAY = "way"
COORD_DP = 7
KIND_TYPE = {osmxml.NODE: "n", osmxml.WAY: "w", osmxml.RELATION: "r"}
TOKEN = re.compile(r"[^\W_]+")


class Allow(NamedTuple):
    key: str
    value: str
    types: str
    cls: str


class Chain(NamedTuple):
    brand: str
    wikidata: str
    phrase: str


# R2. ORDER IS THE RULE: an object carrying two allowlisted tags takes the first row's class.
ALLOWLIST = (
    Allow("tourism", "viewpoint", "nw", "viewpoint"),
    Allow("natural", "peak", "n", "peak"),
    Allow("waterway", "waterfall", "n", "waterfall"),
    Allow("natural", "beach", "nwr", "beach"),
    Allow("highway", "trailhead", "n", "trailhead"),
    Allow("tourism", "museum", "nwr", "museum"),
    Allow("amenity", "cafe", "nwr", "cafe"),
    Allow("leisure", "garden", "nwr", "garden"),
    Allow("leisure", "park", "nwr", "park"),
    Allow("place", "city", "n", "town"),
    Allow("place", "town", "n", "town"),
    Allow("place", "village", "n", "town"),
)

# R5. Every chain with >= 3 named cafes in the LA clip (task Log, 2026-10-05 measurement).
BLOCKLIST = (
    Chain("Starbucks", "Q37158", "starbucks"),
    Chain("The Coffee Bean & Tea Leaf", "Q1141384", "coffee bean"),
    Chain("Peet's Coffee", "Q1094101", "peet s"),
    Chain("It's Boba Time", "Q119951349", "boba time"),
    Chain("85°C", "Q4644852", "85 c"),
    Chain("Blue Bottle Coffee", "Q4928917", "blue bottle"),
    Chain("Ding Tea", "Q112123475", "ding tea"),
    Chain("Philz Coffee", "Q18156812", "philz"),
    Chain("Corner Bakery", "Q5171598", "corner bakery"),
    Chain("7 Leaves Cafe", "Q118480682", "7 leaves"),
    Chain("Le Pain Quotidien", "Q2046903", "le pain quotidien"),
    Chain("Sharetea", "Q64827032", "sharetea"),
    Chain("Joe & The Juice", "Q26221514", "joe the juice"),
    Chain("Kreation Organic", "Q113363083", "kreation"),
    Chain("Tapioca Express", "Q23462008", "tapioca express"),
    Chain("Dutch Bros. Coffee", "Q5317253", "dutch bros"),
    Chain("Quickly", "Q3771463", "quickly"),
    Chain("Tastea", "Q122328236", "tastea"),
)

CLASSES = tuple(dict.fromkeys(row.cls for row in ALLOWLIST))
COUNT_NAMES = ("places", "unnamed", "refused_access", "chain", "skipped_geometry", "deduped")


def keep_expressions() -> list:
    """One osmium tags-filter expression per ALLOWLIST row, e.g. `n/natural=peak`."""
    return ["%s/%s=%s" % (row.types, row.key, row.value) for row in ALLOWLIST]


def tokens(text: str) -> tuple:
    """Casefolded word tokens: every run of letters and digits. `Peet's` is (peet, s); `85°C` is (85, c)."""
    return tuple(TOKEN.findall(text.casefold()))


def allow_row(osm_type: str, tags: dict):
    for row in ALLOWLIST:
        if tags.get(row.key) == row.value and osm_type in row.types:
            return row
    return None


def name_of(tags: dict):
    name = (tags.get(NAME_KEY) or "").strip()
    return name or None


def contains_run(haystack: tuple, needle: tuple) -> bool:
    width = len(needle)
    return any(haystack[i:i + width] == needle for i in range(len(haystack) - width + 1))


def is_chain(tags: dict, name: str) -> bool:
    qid = tags.get(WIKIDATA_KEY)
    brand = (tags.get(BRAND_KEY) or "").casefold()
    words = tokens(name)
    for chain in BLOCKLIST:
        if qid == chain.wikidata or brand == chain.brand.casefold():
            return True
        if contains_run(words, tokens(chain.phrase)):
            return True
    return False


def locate(node_ids, nodes: dict):
    """(lat, lon, bbox) as the vertex mean of the DISTINCT node ids, or None when any node is absent."""
    distinct = list(dict.fromkeys(node_ids))
    if not distinct or any(n not in nodes for n in distinct):
        return None
    lats = [nodes[n][0] for n in distinct]
    lons = [nodes[n][1] for n in distinct]
    lat = round(sum(lats) / len(lats), COORD_DP)
    lon = round(sum(lons) / len(lons), COORD_DP)
    return lat, lon, (min(lats), max(lats), min(lons), max(lons))


def relation_nodes(member_ways, ways: dict):
    """The node ids of a relation's outer member ways, or None when one is absent (or there is none)."""
    if not member_ways or any(w not in ways for w in member_ways):
        return None
    return [n for w in member_ways for n in ways[w]]


def read(path) -> tuple:
    """(candidates, nodes, ways, counts) from one pass over the stream. A candidate is
    [osm_type, osm_id, cls, name, node ids | None, outer member way ids | None]."""
    counts = {name: 0 for name in COUNT_NAMES}
    nodes, ways, candidates = {}, {}, []
    for elem in osmxml.iter_top_level(path):
        osm_type = KIND_TYPE.get(elem.tag)
        if osm_type is None:
            continue
        osm_id = int(elem.get("id"))
        if osm_type == "n":
            nodes[osm_id] = (float(elem.get("lat")), float(elem.get("lon")))
        elif osm_type == "w":
            ways[osm_id] = osmxml.refs_of(elem)
        tags = osmxml.tags_of(elem)
        row = allow_row(osm_type, tags)
        if row is None:
            continue
        name = name_of(tags)
        if name is None:
            counts["unnamed"] += 1
            continue
        if tags.get(ACCESS_KEY) in REFUSED_ACCESS:
            counts["refused_access"] += 1
            continue
        if is_chain(tags, name):
            counts["chain"] += 1
            continue
        members = None
        if osm_type == "r":
            members = [int(m.get("ref")) for m in elem.findall(MEMBER)
                       if m.get("type") == MEMBER_WAY and (m.get("role") or "") in OUTER_ROLES]
        node_ids = [osm_id] if osm_type == "n" else ways.get(osm_id)
        candidates.append([osm_type, osm_id, row.cls, name, node_ids, members])
    return candidates, nodes, ways, counts


def select(path) -> tuple:
    """(places, counts): the extract's `places` array, sorted by (osm_type, osm_id), and the count line's
    numbers. Every place is {osm_type, osm_id, cls, name, lat, lon} - `extractplace.load_places`'s shape."""
    candidates, nodes, ways, counts = read(path)
    located = []
    for osm_type, osm_id, cls, name, node_ids, members in candidates:
        if osm_type == "r":
            node_ids = relation_nodes(members, ways)
        where = locate(node_ids or [], nodes)
        if where is None:
            counts["skipped_geometry"] += 1
            continue
        located.append((osm_type, osm_id, cls, name, where))

    points = {}
    for osm_type, _osm_id, cls, name, (lat, lon, _bbox) in located:
        if osm_type == "n":
            points.setdefault((cls, name.casefold()), []).append((lat, lon))
    places = []
    for osm_type, osm_id, cls, name, (lat, lon, bbox) in located:
        if osm_type != "n" and any(bbox[0] <= p_lat <= bbox[1] and bbox[2] <= p_lon <= bbox[3]
                                   for p_lat, p_lon in points.get((cls, name.casefold()), ())):
            counts["deduped"] += 1
            continue
        places.append({"osm_type": osm_type, "osm_id": osm_id, "cls": cls, "name": name,
                       "lat": lat, "lon": lon})
    places.sort(key=lambda p: ("nwr".index(p["osm_type"]), p["osm_id"]))
    counts["places"] = len(places)
    for cls in CLASSES:
        counts[cls] = sum(1 for p in places if p["cls"] == cls)
    return places, counts


def count_line(counts: dict) -> str:
    return "PLACES " + " ".join("%s=%d" % (name, counts[name]) for name in COUNT_NAMES + CLASSES)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.placeallow", description=__doc__.splitlines()[0])
    parser.add_argument("--expressions", action="store_true", help="print the osmium expressions")
    parser.add_argument("--input", default=None, help="an OSM XML stream; prints the count line")
    args = parser.parse_args(argv)
    if args.expressions:
        print("\n".join(keep_expressions()))
    if args.input is not None:
        print(count_line(select(args.input)[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
