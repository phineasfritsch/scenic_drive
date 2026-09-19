"""`python -m etl.extractadapter` - a real waydoc into the extract `corpus.build` reads. The committed path.

    python -m etl.extractadapter --input work/la/window-doc.json --out window-extract.json [--region la]
    python -m etl.corpus --input window-extract.json --out corpus.sqlite --built-at 2026-09-18T00:00:00Z

WHAT THIS IS FOR. There were three shapes and no converter: `waydoc.build` writes {way_id, tags, coords}
per road, `extractway.load_extract` reads {id, cls, highway, access_ok, oneway, nodes, name?, surface?},
and `assemble` writes a third. So `corpus.build` had never been fed a real way by anything committed -
T-0206 measured all of LA through a throwaway in a gitignored work/ dir, which is exactly the kind of
adapter whose rules nobody reviews and no suite runs (T-0206 R1; this task's Brief).

IT INVENTS NOTHING. Every field below is read off the way's own OSM tags, and where a rule already exists
in this package it is CALLED, never restated: the classes are `tagfilter.WAY_CLASSES` inverted, the access
question is `accessrule.access_refused` - the same predicate `assemble.gate_reason` calls - and the three
surface states are `surface.surface_state`.

THE SURFACE COLUMN TRAVELS RAW (ruling R2). `extractway.RETIRED_WAY_KEYS` REFUSES an extract that carries a
pre-derived surface column, because the three states are derived from the tag AND the class together and a
converter that shipped its own answer would be a second copy of `surface.py`'s rule. So the raw tag value
travels and `ExtractWay.surface_state` decides. `surface_state` is called HERE only to COUNT the three
states on the count line: a count line whose numbers are measured is worth reading, one whose numbers are
asserted is decoration.

WHAT IS SKIPPED, AND LOUDLY. A way whose `highway` value is in no `WAY_CLASSES` entry cannot become an
`ExtractWay` - the reader refuses it by name - so it is skipped and COUNTED. It is not a hypothetical: the
osmium keep-pass keeps `nw/tourism=attraction`, and ways 1211805282 and 1211805283 (highway=footway,
"Universal CityWalk Hollywood") reached T-0206's eastern-grid document that way. Both carry
`motor_vehicle=no`; a skip that went silent would look exactly like two correctly refused roads.

WHAT IS REFUSED. A repeated `way_id` raises, naming the id. The throwaway dropped a repeat in silence, and
dropping one way moves every other way's rank by 1/n - the same argument `assemble.assemble` makes for
refusing a whole region rather than dropping a row.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .accessrule import access_refused
from .surface import SURFACE_PAVED, SURFACE_UNKNOWN, SURFACE_UNPAVED, surface_state
from .tagfilter import WAY_CLASSES

HIGHWAY_KEY = "highway"
NAME_KEY = "name"
SURFACE_KEY = "surface"
ONEWAY_KEY = "oneway"
JUNCTION_KEY = "junction"
REGION_KEY = "region"
META_KEY = "meta"

# The reporting classes, inverted once. Derived from `tagfilter`, never a second literal list: a class
# added there is adapted the same day, and a class removed there stops being adapted the same day.
HIGHWAY_TO_CLS = {highway: cls for cls, values in WAY_CLASSES.items() for highway in values}

# `oneway`'s value space, as the corpus's three-state column (ruling R2). Each of these three sets is a
# FINAL answer; any other value - `reversible`, `alternating`, or a typo - falls through to the roundabout
# implication and then to two-way, because a corpus with no time dimension must not claim a direction.
ONEWAY_FORWARD = frozenset({"yes", "true", "1"})
ONEWAY_REVERSE = frozenset({"-1", "reverse"})
ONEWAY_TWO_WAY = frozenset({"no", "false", "0"})
# OSM's roundabout is one-way by definition and is very often tagged with no `oneway` key at all (6 of the
# canyon window's 15). `junction=circular` is deliberately NOT here: a circular junction carries no such
# implication, and inventing one would send the router the wrong way round a two-way circle.
ROUNDABOUT = "roundabout"

FORWARD = 1
REVERSE = -1
TWO_WAY = 0

ACCESS_OK = 1
ACCESS_BLOCKED = 0

# `extractway.way_from_json` refuses fewer than two nodes by name; counted here so the two populations -
# what the clip held and what the corpus got - can be reconciled without reading a traceback.
MIN_COORDINATES = 2

COUNT_NAMES = ("ways", "skipped_class", "skipped_short", "access_blocked", "surface_unknown",
               "surface_unpaved", "surface_paved")
SURFACE_COUNTS = {SURFACE_UNKNOWN: "surface_unknown", SURFACE_UNPAVED: "surface_unpaved",
                  SURFACE_PAVED: "surface_paved"}


def oneway_flag(tags: dict) -> int:
    """1 forward, -1 against the way's drawn direction, 0 two-way. Ruling R2, value by value."""
    value = tags.get(ONEWAY_KEY)
    if value in ONEWAY_FORWARD:
        return FORWARD
    if value in ONEWAY_REVERSE:
        return REVERSE
    if value in ONEWAY_TWO_WAY:
        return TWO_WAY
    if tags.get(JUNCTION_KEY) == ROUNDABOUT:
        return FORWARD
    return TWO_WAY


def access_ok(tags: dict) -> int:
    """The corpus's `access_ok` column: 0 iff the tags refuse the public.

    Asked of the ACCESS rule alone, never derived from `assemble.gate_reason`, which returns the first
    rule that fires: way 1206170836 of the canyon window is `access=private` AND `surface=dirt`, and its
    gate reason is `unpaved_surface`, so a corpus built on that answer would mark it open to the public.
    """
    return ACCESS_BLOCKED if access_refused(tags) else ACCESS_OK


def name_of(tags: dict):
    """The way's name, or None. 7,623 of the canyon window's 11,740 ways have none."""
    name = tags.get(NAME_KEY)
    return name if isinstance(name, str) and name else None


def surface_of(tags: dict):
    """The RAW `surface` tag value, or None. Not the three-state column - see the module docstring."""
    value = tags.get(SURFACE_KEY)
    return value if isinstance(value, str) and value else None


def extract_way(way_id: int, tags: dict, coords: list) -> dict:
    """One row of the extract `extractway.load_extract` reads. Keys it treats as optional are omitted
    rather than written null, because `way_from_json` type-checks a present key."""
    highway = tags.get(HIGHWAY_KEY)
    row = {"id": way_id,
           "cls": HIGHWAY_TO_CLS[highway],
           "highway": highway,
           "access_ok": access_ok(tags),
           "oneway": oneway_flag(tags),
           "nodes": [[float(lat), float(lon)] for lat, lon in coords]}
    name = name_of(tags)
    if name is not None:
        row[NAME_KEY] = name
    value = surface_of(tags)
    if value is not None:
        row[SURFACE_KEY] = value
    return row


def region_of(doc: dict, region):
    """The region this document is about: the argument, else the document's own, else a refusal."""
    if region:
        return region
    for candidate in (doc.get(REGION_KEY), (doc.get(META_KEY) or {}).get(REGION_KEY)):
        if isinstance(candidate, str) and candidate:
            return candidate
    raise ValueError("the document names no region and --region was not given: a corpus whose region is "
                     "guessed is a corpus nobody can serve")


def adapt_document(doc: dict, *, region=None) -> tuple:
    """(the extract document, the counts). Pure: reads a parsed waydoc, opens nothing, writes nothing."""
    rows = doc.get("ways")
    if not isinstance(rows, list):
        raise ValueError("the document has no `ways` array; this reads etl.waydoc's own output")
    counts = {name: 0 for name in COUNT_NAMES}
    ways: list = []
    seen: set = set()
    for row in rows:
        tags = row.get("tags") or {}
        if tags.get(HIGHWAY_KEY) not in HIGHWAY_TO_CLS:
            counts["skipped_class"] += 1
            continue
        coords = row.get("coords") or []
        if len(coords) < MIN_COORDINATES:
            counts["skipped_short"] += 1
            continue
        way_id = int(row["way_id"])
        if way_id in seen:
            raise ValueError("way %d appears twice in the document: a repeated way is refused by name, "
                             "never dropped - dropping one moves every other way's rank" % way_id)
        seen.add(way_id)
        way = extract_way(way_id, tags, coords)
        counts["ways"] += 1
        counts["access_blocked"] += 1 if way["access_ok"] == ACCESS_BLOCKED else 0
        counts[SURFACE_COUNTS[surface_state(highway=way["highway"], surface=way.get(SURFACE_KEY))]] += 1
        ways.append(way)
    ways.sort(key=lambda w: w["id"])
    return {"region": region_of(doc, region), "ways": ways}, counts


def count_line(counts: dict) -> str:
    return "ADAPT " + " ".join("%s=%d" % (name, counts[name]) for name in COUNT_NAMES)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.extractadapter",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="a document written by `python -m etl.waydoc`")
    parser.add_argument("--out", required=True, help="the JSON extract `python -m etl.corpus` reads")
    parser.add_argument("--region", default=None, help="default: the document's own region")
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    document, counts = adapt_document(doc, region=args.region)
    pathlib.Path(args.out).write_text(json.dumps(document, separators=(",", ":")) + "\n",
                                      encoding="utf-8", newline="\n")
    print(count_line(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
