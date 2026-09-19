"""`ops/sane` check 4 over the tagged extract, as numbers, plus the ranked read the human makes.

THE THREE CLAUSES (the plan's check 4, ruling R8 in T-0168's log; the third from T-0204's R1):

    null_score     ways that SHOULD carry a score and do not - a `highway` way that is neither
                   `scenic_refused` nor scored. Must be 0.
    gated_scored   ways the safety gates refuse, or motorway/trunk, carrying a score ABOVE 0. Must be 0.
    malformed      ways whose `scenic_score` is not an integer the router can hold, whose
                   `scenic_score_unit` is missing, not a number, outside 0..1 or does not quantise to the
                   integer beside it, or that claim to be refused AND scored at once. Must be 0.

Any one above zero exits 4 - `ops/sane`'s reserved code for corpus and graph bounds - and the numbers are
printed either way, because "the check passed" is not evidence and a count is.

THE RULES ARE IMPORTED, NEVER RESTATED. `gate_reason` IS `assemble.gate_reason` and `ZERO_CLASSES` IS
`byways.SCENIC_ZERO_CLASSES`, by identity, with a test asserting exactly that; the score's bounds are read
out of `tagwriter` at call time for the same reason (an int cannot be asserted with `is`, so the test moves
the writer's bound and requires this module to move with it). A second copy of a gate in the checker is how
the corpus and the check agree with each other while both are wrong about a road.

WHAT THIS MODULE DOES RESTATE, deliberately (T-0204 R1): that a shipped `scenic_score` must SATISFY the
0..10 integer contract. The writer clamps, so the writer cannot emit anything else - but this is the
INDEPENDENT ORACLE over the bytes that ship, and a hand-edited PBF, a second producer or a future writer is
exactly what it exists for. Before T-0204 a tertiary tagged 42 was counted as scored and ranked #1, a
motorway at -3 cleared the gate clause because `-3 > 0` is false, and `scenic_score=abc` was a traceback.

ONE ANSWER, BY CONSTRUCTION. `counts` and `top` do not each decide what a way is: `classify` decides, once,
and both ask it. Two halves that classify independently drift - `counts` used to call a refused-and-scored
way `refused` and skip it while `top` ranked it, which is two answers about one road.

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
COUNT_NAMES = ("null_score", "gated_scored", "malformed", "scored", "refused", "not_a_road")
REFUSAL_EXIT = 4
TOP_DEFAULT = 10
COORDINATE_PRECISION = 5
# The unit score's own bounds. `score.score` produces 0..1 and refuses anything else; this is the oracle
# saying so over the bytes that ship, the way the integer's bounds are said with `tagwriter`'s own numbers.
UNIT_MIN = 0.0
UNIT_MAX = 1.0

# The five things a way in the read-back file can be. Exactly one of them, decided in one place.
NOT_A_ROAD = "not_a_road"
REFUSED = "refused"
MALFORMED = "malformed"
NULL_SCORE = "null_score"
SCORED = "scored"

# An oracle that prints twelve thousand lines is an oracle nobody reads.
MALFORMED_REPORT_LIMIT = 20


def is_gated(tags: dict) -> bool:
    """Whether this way is one check-4's second clause forbids a score above 0 on."""
    return tags.get(HIGHWAY) in ZERO_CLASSES or gate_reason(tags) is not None


def integer_or_none(raw) -> int | None:
    """A tag value as an integer, or None if it is not one. Never raises - the caller names the way."""
    text = str(raw).strip()
    digits = text[1:] if text[:1] in "+-" else text
    return int(text) if digits.isascii() and digits.isdigit() else None


def unit_or_none(raw) -> float | None:
    """A tag value as the 0..1 unit score, or None if it is not a real number. Never raises.

    ASCII only, for the reason `integer_or_none` is: `float("٠.٥")` is 0.5 to Python and is not the
    byte sequence any producer of this file is allowed to write. NaN is not a number either - and a NaN that
    reached the ranking would compare false against every bound, so it would sort wherever the sort put it.
    """
    text = str(raw).strip()
    if not text.isascii():
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return None if number != number else number


def classify(way_id: int, tags: dict) -> tuple:
    """What this way is, as one of the five kinds, with a detail.

    The detail is the integer score for `scored`, the reason for `malformed`, and None otherwise. Both
    `counts` and `top` take their answer from here, so they cannot disagree about a road.

    THE UNIT IS PART OF THE CONTRACT (T-0204 R5), because the unit is the number the ranking - and this
    task's whole predicate - is read on. A scored way carries `scenic_score_unit`, it is a real number in
    0..1, and `tagwriter.quantise` of it IS the integer beside it. The quantiser is IMPORTED and called,
    never restated here: a second copy of the rounding is how the writer and the checker agree with each
    other while both are wrong about a road.
    """
    if not tags.get(HIGHWAY):
        return (NOT_A_ROAD, None)
    raw = tags.get(tagwriter.KEY_SCORE)
    refused = bool(tags.get(tagwriter.KEY_REFUSED))
    if raw is None:
        # Ruling R2 of T-0168: a refused way SHOULD have no score, so its absence is not a hole.
        return (REFUSED, None) if refused else (NULL_SCORE, None)
    if refused:
        return (MALFORMED, "refused and scored at once - a refused way carries no score (T-0168 R2)")
    value = integer_or_none(raw)
    if value is None:
        return (MALFORMED, "not an integer")
    if not tagwriter.SCORE_MIN <= value <= tagwriter.SCORE_MAX:
        return (MALFORMED, "outside the %d..%d the router holds"
                % (tagwriter.SCORE_MIN, tagwriter.SCORE_MAX))
    raw_unit = tags.get(tagwriter.KEY_UNIT)
    if raw_unit is None:
        return (MALFORMED, "scored with no %s - the ranking is read on the unit" % tagwriter.KEY_UNIT)
    unit = unit_or_none(raw_unit)
    if unit is None:
        return (MALFORMED, "%s=%s is not a number" % (tagwriter.KEY_UNIT, raw_unit))
    if not UNIT_MIN <= unit <= UNIT_MAX:
        return (MALFORMED, "%s=%s is outside %g..%g" % (tagwriter.KEY_UNIT, raw_unit, UNIT_MIN, UNIT_MAX))
    if tagwriter.quantise(unit) != value:
        return (MALFORMED, "%s=%s quantises to %d, not the %d beside it"
                % (tagwriter.KEY_UNIT, raw_unit, tagwriter.quantise(unit), value))
    return (SCORED, value)


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


def scan(path) -> tuple:
    """One pass: the three clauses with the populations they are drawn from, and the malformed ways by name."""
    found = {name: 0 for name in COUNT_NAMES}
    malformed = []
    for way_id, tags, _coords in read_ways(path):
        kind, detail = classify(way_id, tags)
        found[kind] += 1
        if kind == MALFORMED:
            malformed.append((way_id, tags.get(tagwriter.KEY_SCORE), detail))
        elif kind == SCORED and detail > 0 and is_gated(tags):
            found["gated_scored"] += 1
    return found, malformed


def counts(path) -> dict:
    """The clauses as numbers. `scan` does the work; this is the name the rest of the repo calls."""
    return scan(path)[0]


def count_line(found: dict) -> str:
    return "CHECK4 " + " ".join("%s=%d" % (name, found[name]) for name in COUNT_NAMES)


def malformed_lines(malformed: list) -> list:
    """Every malformed way named, capped, with the tail counted rather than dropped in silence."""
    shown = ["way %d %s=%s: %s" % (way_id, tagwriter.KEY_SCORE, raw, why)
             for way_id, raw, why in malformed[:MALFORMED_REPORT_LIMIT]]
    if len(malformed) > MALFORMED_REPORT_LIMIT:
        shown.append("... and %d more" % (len(malformed) - MALFORMED_REPORT_LIMIT))
    return shown


def refuses(found: dict) -> bool:
    return found["null_score"] > 0 or found["gated_scored"] > 0 or found["malformed"] > 0


def middle(coords: list) -> tuple:
    """One coordinate for a way: its middle node. A local file, so five decimals, not the server's two."""
    if not coords:
        return (float("nan"), float("nan"))
    return coords[len(coords) // 2]


def top(path, limit: int = TOP_DEFAULT) -> list:
    """The highest-scoring ways, best first, with what a human needs to recognise the road.

    Only ways `classify` calls `scored`: a malformed way cannot rank on a number the writer could not have
    written, and a way that claims to be refused does not appear in the read as one of the best roads.
    """
    rows = []
    for way_id, tags, coords in read_ways(path, with_coords=True):
        kind, detail = classify(way_id, tags)
        if kind != SCORED:
            continue
        unit = unit_or_none(tags[tagwriter.KEY_UNIT])
        lat, lon = middle(coords)
        rows.append({"way_id": way_id, "name": tags.get(NAME) or "", "highway": tags[HIGHWAY],
                     "lat": lat, "lon": lon, "scenic_score": detail, "scenic_score_unit": unit})
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
    found, malformed = scan(args.path)
    print(count_line(found))
    if args.top:
        print(format_top(top(args.path, args.top)))
    for line in malformed_lines(malformed):
        print(line, file=sys.stderr)
    if refuses(found):
        print("CHECK4 FAILS: null_score=%d gated_scored=%d malformed=%d - all three clauses must be 0"
              % (found["null_score"], found["gated_scored"], found["malformed"]), file=sys.stderr)
        return REFUSAL_EXIT
    return 0


if __name__ == "__main__":  # pragma: no cover - the module is exercised through `counts` and `top`
    sys.exit(main())
