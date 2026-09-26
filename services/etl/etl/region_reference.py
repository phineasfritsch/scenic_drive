"""The ONE population a region's ranks are computed against, built once and handed to every chunk.

THE DEFECT THIS MODULE EXISTS FOR (T-0204's measurement, PR #113). `osmium extract` COMPLETES every way that
crosses a clip boundary, so a way on a tile edge is documented in both tiles. T-0204 scored the LA street
grid in two halves and found 190 such ways - and 160 of them carried DIFFERENT scores in the two halves
(Mulholland Drive 1533792498: 0.6988 against 0.7022). Nothing was wrong with the geometry. `normalise_region`
ranks a way against THE WAYS THAT LANDED IN THE SAME CLIP, so half a city is a different curve from the other
half, and a score that depends on the clip is not an index: the router would see a step at every seam.

`normalise.normalise_region` has taken a `reference` population since T-0163 and no caller ever passed one.
This module is what a caller passes: per ranked term, the SORTED list of that term's raw values over the
whole region's ranking population, computed once in a first pass over every tile and read back by
`etl.assemble --reference` in the second.

WHAT IS IN IT, AND WHY IT IS EXACTLY WHAT `normalise_region` WOULD HAVE RANKED (T-0208 R2). `raw_values`
takes the same two decisions the normaliser takes region-internally and takes them through the normaliser's
own functions, so the two can never drift apart:
  * `normalise.population_of` - the ZERO CLASSES (motorway, trunk and their links) are NOT in the curve.
    They score 0 by class, and 19,511 motorway ways would otherwise set the distribution for the back roads
    this product exists to find. They stay in the corpus, penalised and not excluded (CLAUDE.md).
  * `normalise.answering` - a way that DECLINED to measure a term (today only `sinuosity`, T-0161's closed
    ways) is out of THAT term's population and no other. Declining one term is not declining the road.
  * GATED ways ARE in it. The gate is applied in `assemble.scored_row` AFTER the score, so a gated way ranks
    like any other and is then set to `GATE_SCORE`; dropping it here would move every other way's rank.

THE DEDUP KEY IS `way_id`, AND THE RULE IS FIRST TILE WINS (T-0208 R1). The same way documented in two tiles
must be counted ONCE - counted twice it weights its own value double in the curve it is then ranked against.
`merge` takes the tables in the order it is given them, which the driver keeps in sorted tile order, so the
rule is deterministic rather than whichever tile finished first. The rule is only allowed to be arbitrary
because the two tiles agree: `waydoc.motorway_lines` removed the last clip-dependent producer input (R1b),
and the run MEASURES the agreement over every way documented twice rather than assuming it.

THE DIGEST IS OVER THE VALUES, NOT OVER THE FILE. `digest` hashes the canonical JSON of the sorted table, so
the number the Log quotes identifies the POPULATION: a table written with different whitespace is the same
reference, and a table in a different order is a different one.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from .normalise import answering, population_of, reference_refusals
from .way_record import RANKED_TERMS


def raw_values(records: list) -> dict:
    """`{term: {way_id: raw value}}` over the records that belong in each term's curve."""
    population = population_of(records)
    return {term: {record.way_id: float(getattr(record, term)) for record in answering(term, population)}
            for term in RANKED_TERMS}


def merge(tables: list) -> dict:
    """Several tiles' `raw_values` into one, deduplicated by `way_id`, FIRST TILE WINS."""
    out: dict = {term: {} for term in RANKED_TERMS}
    for table in tables:
        for term in RANKED_TERMS:
            for way_id, value in (table.get(term) or {}).items():
                out[term].setdefault(way_id, value)
    return out


def table_of(values: dict) -> dict:
    """`{term: {way_id: value}}` -> the reference: `{term: [values sorted ascending]}`.

    Sorted here and not at the ranker, so the thing that is written, hashed and quoted is the thing that is
    ranked against. `normalise_region` sorts defensively anyway; a reference that arrived unsorted would
    otherwise rank every way against a bisect over noise.
    """
    return {term: sorted(float(value) for value in (values.get(term) or {}).values())
            for term in RANKED_TERMS if values.get(term)}


def counts(table: dict) -> dict:
    """How many values each term's population holds - the count the Log quotes beside the digest."""
    return {term: len(table[term]) for term in sorted(table)}


def digest(table: dict) -> str:
    """The sha256 of the canonical serialisation of the table: the population's name."""
    return hashlib.sha256(canonical(table).encode("utf-8")).hexdigest()


def canonical(table: dict) -> str:
    return json.dumps(table, sort_keys=True, separators=(",", ":"))


def dump(table: dict, path) -> str:
    """Write the reference, refusing one `normalise_region` would refuse. Returns the digest.

    Refused HERE rather than four hours later in the second pass: `reference_refusals` is the same judge
    the normaliser uses, so a table that cannot be ranked against never becomes a file other runs read.
    """
    problems = reference_refusals(table)
    if problems:
        raise ValueError("reference refused: %s" % "; ".join(problems))
    if path is not None:
        pathlib.Path(path).write_text(canonical(table) + "\n", encoding="utf-8", newline="\n")
    return digest(table)


def load(path) -> dict:
    """Read a reference written by `dump`, refusing one that cannot be ranked against."""
    table = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    problems = reference_refusals(table)
    if problems:
        raise ValueError("reference refused: %s" % "; ".join(problems))
    return {term: [float(value) for value in values] for term, values in table.items()}
