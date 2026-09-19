"""`ops/sane` check 4 over the tagged extract, as two numbers, plus the ranked read the human makes.

THE TWO CLAUSES (the plan's check 4, ruling R8 in T-0168's log):

    null_score     ways that SHOULD carry a score and do not - a `highway` way that is neither
                   `scenic_refused` nor scored. Must be 0.
    gated_scored   ways the safety gates refuse, or motorway/trunk, carrying a score ABOVE 0. Must be 0.

Either one above zero exits 4 - `ops/sane`'s reserved code for corpus and graph bounds - and the numbers are
printed either way, because "the check passed" is not evidence and a count is.

THE RULES ARE IMPORTED, NEVER RESTATED. `gate_reason` IS `assemble.gate_reason` and `ZERO_CLASSES` IS
`byways.SCENIC_ZERO_CLASSES`, by identity, with a test asserting exactly that. A second copy of a gate in
the checker is how the corpus and the check agree with each other while both are wrong about a road.

WHAT IT READS. The file that SHIPS: the tagged PBF, read back out with `osmium cat -o readback.osm.xml`.
Checking the table in memory would only prove the table; the property is about the bytes GraphHopper
imports, and a tag lost in the PBF encode would pass a check of the table with nothing to show it.

THE TOP-10 IS NOT A VERDICT. `--top` prints the ranked ways with their names, classes and one coordinate so
a HUMAN can answer the plan's M2 exit clause - "8 of 10 are roads you'd drive". No agent makes that call.
"""
from __future__ import annotations

import argparse
import sys

from . import assemble, byways, osmxml, tagwriter

# Imported by identity. The tests assert `is`, not equality.
gate_reason = assemble.gate_reason
ZERO_CLASSES = byways.SCENIC_ZERO_CLASSES

HIGHWAY = "highway"
NAME = "name"
COUNT_NAMES = ("null_score", "gated_scored", "scored", "refused", "not_a_road")
REFUSAL_EXIT = 4
TOP_DEFAULT = 10
COORDINATE_PRECISION = 5


def is_gated(tags: dict) -> bool:
    """Whether this way is one check-4's second clause forbids a score above 0 on."""
    return tags.get(HIGHWAY) in ZERO_CLASSES or gate_reason(tags) is not None


def scored_value(tags: dict) -> int | None:
    raw = tags.get(tagwriter.KEY_SCORE)
    return None if raw is None else int(raw)


def read_ways(path, with_coords: bool = False):
    """Yield `(way_id, tags, coords)` for every way in the document, in file order.

    Nodes come before ways in an OSM file, so one pass serves both - the coordinates are collected on the
    way past. `with_coords` is False for the counts, where nothing needs geometry and 350 000 node
    positions would be held for nothing.
    """
    nodes: dict = {}
    for elem in osmxml.iter_top_level(path):
        if with_coords and elem.tag == osmxml.NODE:
            nodes[int(elem.get("id"))] = (float(elem.get("lat")), float(elem.get("lon")))
        elif elem.tag == osmxml.WAY:
            coords = [nodes[r] for r in osmxml.refs_of(elem) if r in nodes] if with_coords else []
            yield int(elem.get("id")), osmxml.tags_of(elem), coords


def counts(path) -> dict:
    """Both clauses and the three populations they are drawn from."""
    found = {name: 0 for name in COUNT_NAMES}
    for _way_id, tags, _coords in read_ways(path):
        if not tags.get(HIGHWAY):
            found["not_a_road"] += 1
            continue
        if tags.get(tagwriter.KEY_REFUSED):
            found["refused"] += 1
            continue
        value = scored_value(tags)
        if value is None:
            found["null_score"] += 1
            continue
        found["scored"] += 1
        if value > 0 and is_gated(tags):
            found["gated_scored"] += 1
    return found


def count_line(found: dict) -> str:
    return "CHECK4 " + " ".join("%s=%d" % (name, found[name]) for name in COUNT_NAMES)


def refuses(found: dict) -> bool:
    return found["null_score"] > 0 or found["gated_scored"] > 0


def middle(coords: list) -> tuple:
    """One coordinate for a way: its middle node. A local file, so five decimals, not the server's two."""
    if not coords:
        return (float("nan"), float("nan"))
    return coords[len(coords) // 2]


def top(path, limit: int = TOP_DEFAULT) -> list:
    """The highest-scoring ways, best first, with what a human needs to recognise the road."""
    rows = []
    for way_id, tags, coords in read_ways(path, with_coords=True):
        value = scored_value(tags)
        if value is None or not tags.get(HIGHWAY):
            continue
        unit = float(tags.get(tagwriter.KEY_UNIT, value) or 0.0)
        lat, lon = middle(coords)
        rows.append({"way_id": way_id, "name": tags.get(NAME) or "", "highway": tags[HIGHWAY],
                     "lat": lat, "lon": lon, "scenic_score": value, "scenic_score_unit": unit})
    rows.sort(key=lambda r: (-r["scenic_score"], -r["scenic_score_unit"], r["way_id"]))
    ranked = rows[:limit]
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
    return ranked


def format_top(rows: list) -> str:
    """The ranked list as the PR and the human read it."""
    out = ["%4s  %-10s  %-34s  %-13s  %-19s  %s"
           % ("rank", "way_id", "name", "highway", "coordinate", "scenic_score")]
    for row in rows:
        out.append("%4d  %-10d  %-34s  %-13s  %9.*f,%9.*f  %2d  (%.4f)"
                   % (row["rank"], row["way_id"], row["name"][:34], row["highway"],
                      COORDINATE_PRECISION, row["lat"], COORDINATE_PRECISION, row["lon"],
                      row["scenic_score"], row["scenic_score_unit"]))
    return "\n".join(out)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.scenecheck",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("path", help="the tagged extract as OSM XML (osmium cat -o readback.osm.xml)")
    parser.add_argument("--top", type=int, default=TOP_DEFAULT, help="how many ways to rank (0 for none)")
    args = parser.parse_args(argv)
    found = counts(args.path)
    print(count_line(found))
    if args.top:
        print(format_top(top(args.path, args.top)))
    if refuses(found):
        print("CHECK4 FAILS: null_score=%d gated_scored=%d - both clauses must be 0"
              % (found["null_score"], found["gated_scored"]), file=sys.stderr)
        return REFUSAL_EXIT
    return 0


if __name__ == "__main__":  # pragma: no cover - the module is exercised through `counts` and `top`
    sys.exit(main())
