"""The tag pass: the assembly's scored table onto the ways of the clip, as `scenic_*` tags.

THE QUANTISATION (ruling R1 in T-0168's log). `scenic_score` is `round-half-up(score x 10)` as an INTEGER
0..10, because GraphHopper's encoded value holds it in four bits. Half goes UP - `math.floor(x*10 + 0.5)`
and not `round`, which is half-to-even and would send 0.65 and 0.75 in opposite directions. The 0..1 value
travels beside it as `scenic_score_unit` so nothing downstream re-derives it from the integer.

A REFUSAL IS NEVER A SILENT 0 (ruling R2). 0 is a real score - it is what a motorway honestly carries
(CLAUDE.md, "Motorway/trunk ways carry scenic_score = 0 ... penalized, not hard-excluded"). A way whose
producer could not answer carries `scenic_refused=1` and `scenic_refused_why`, and NO `scenic_score`. A row
whose score came back None is the same fact reached a different way and is written the same way.

A WAY WITH NO `highway` TAG IS NOT A ROAD. The tag filter keeps park, beach and attraction polygons; they
are written through untouched - not scored, not refused - and `scenecheck` counts them as neither.

THE POPULATION IS CLOSED BOTH WAYS. A road in the file that is in neither the table nor the refused list
stops the run, and so does a table row for a way that is not in the file: a population that shrinks between
two stages with nothing to show for it is the failure this whole pipeline is built to make loud.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

from . import osmxml, score

SCORE_SCALE = 10
SCORE_MIN = 0
SCORE_MAX = 10
TERM_PRECISION = 4

PREFIX = "scenic_"
KEY_SCORE = PREFIX + "score"
KEY_UNIT = PREFIX + "score_unit"
KEY_REFUSED = PREFIX + "refused"
KEY_REFUSED_WHY = PREFIX + "refused_why"
KEY_GATE = PREFIX + "gate"
KEY_FLAGS = PREFIX + "flags"
REFUSED_VALUE = "1"
FLAG_SEPARATOR = ";"
HIGHWAY = "highway"

# A row the assembly scored None: a term was outside 0..1 and `score.score` refused to invent a number.
WHY_NULL_SCORE = "score: a term was outside 0..1"
COUNT_NAMES = ("ways", "scored", "refused", "gated", "not_a_road")


def quantise(value: float) -> int:
    """`score` in 0..1 -> `scenic_score` in 0..10, half UP, clamped to the range the router can hold."""
    number = float(value)
    if number != number:
        raise ValueError("scenic_score: the score is not a number")
    scaled = math.floor(number * SCORE_SCALE + 0.5)
    return max(SCORE_MIN, min(SCORE_MAX, scaled))


def fixed(value: float) -> str:
    """A term as a tag value, at one fixed precision - the same bytes on every run and every box."""
    return "%.*f" % (TERM_PRECISION, float(value))


def tags_for_row(row: dict) -> dict:
    """The tags a SCORED way carries, in the one order they are always written in."""
    out = {KEY_SCORE: str(quantise(row["score"])), KEY_UNIT: fixed(row["score"])}
    terms = row.get("terms") or {}
    for name in score.UNIT_TERMS:
        out[PREFIX + name] = fixed(terms[name])
    if row.get("gate_reason"):
        out[KEY_GATE] = row["gate_reason"]
    flags = list(row.get("flags") or [])
    if flags:
        out[KEY_FLAGS] = FLAG_SEPARATOR.join(flags)
    return out


def tags_for_refusal(why: str) -> dict:
    return {KEY_REFUSED: REFUSED_VALUE, KEY_REFUSED_WHY: why}


def write(source, out, rows: list, refusals: list) -> dict:
    """Copy the clip, adding the scenic tags. Returns the counts; refuses on any population disagreement."""
    scored = {int(r["way_id"]): r for r in rows}
    refused = {int(r["way_id"]): r["why"] for r in refusals}
    both = sorted(set(scored) & set(refused))
    if both:
        raise ValueError("way(s) %s are both scored and refused" % both)
    counts = {name: 0 for name in COUNT_NAMES}
    seen = set()
    with osmxml.Writer(out) as writer:
        for elem in osmxml.iter_top_level(source):
            if elem.tag == osmxml.WAY:
                _tag_way(elem, scored, refused, counts, seen)
            writer.write(elem)
    missing = sorted((set(scored) | set(refused)) - seen)
    if missing:
        raise ValueError("way(s) %s are in the scored table but not in %s" % (missing, source))
    return counts


def _tag_way(elem, scored: dict, refused: dict, counts: dict, seen: set) -> None:
    counts["ways"] += 1
    way_id = int(elem.get("id"))
    tags = osmxml.tags_of(elem)
    already = [k for k in tags if k.startswith(PREFIX)]
    if already:
        raise ValueError("way %d already carries %s - this file has been written once already"
                         % (way_id, already[0]))
    if not tags.get(HIGHWAY):
        counts["not_a_road"] += 1
        return
    if way_id in scored:
        row = scored[way_id]
        seen.add(way_id)
        if row.get("score") is None:
            osmxml.add_tags(elem, tags_for_refusal(WHY_NULL_SCORE))
            counts["refused"] += 1
            return
        osmxml.add_tags(elem, tags_for_row(row))
        counts["scored"] += 1
        if row.get("gate_reason"):
            counts["gated"] += 1
        return
    if way_id in refused:
        seen.add(way_id)
        osmxml.add_tags(elem, tags_for_refusal(refused[way_id]))
        counts["refused"] += 1
        return
    raise ValueError("way %d carries highway=%s and is in neither the scored table nor the refused list"
                     % (way_id, tags.get(HIGHWAY)))


def count_line(counts: dict) -> str:
    """`WRITE ways=6 scored=4 refused=1 gated=2 not_a_road=1` - one line, the shape the ops wrappers print."""
    return "WRITE " + " ".join("%s=%d" % (name, counts[name]) for name in COUNT_NAMES)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.tagwriter",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the clip as OSM XML (osmium cat -o clip.osm.xml)")
    parser.add_argument("--table", required=True, help="the scored table from etl.assemble")
    parser.add_argument("--document", required=True, help="the way document from etl.waydoc (its refusals)")
    parser.add_argument("--out", required=True, help="where to write the tagged OSM XML")
    args = parser.parse_args(argv)
    rows = json.loads(pathlib.Path(args.table).read_text(encoding="utf-8"))["rows"]
    document = json.loads(pathlib.Path(args.document).read_text(encoding="utf-8"))
    counts = write(pathlib.Path(args.input), pathlib.Path(args.out), rows, document.get("refused") or [])
    print(count_line(counts))
    return 0


if __name__ == "__main__":  # pragma: no cover - the module is exercised through `write`
    sys.exit(main())
