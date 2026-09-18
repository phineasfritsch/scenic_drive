"""Region percentile rank: the producers' units in, the 0..1 terms `score.score` consumes out.

WHAT IS RANKED AND WHAT IS NOT (ruling R1 in T-0163's log; plan:89 and T-0146's brief disagreed). A term
that arrives UNBOUNDED - `curvature` as a sum of weighted segment lengths, `elevation_gain` and `relief` in
metres, `sinuosity` as a ratio, `furniture` as a rate - becomes its rank among the region's SCORABLE ways.
A term that arrives as a measured fraction (`canopy`, `impervious`, `water`) or as a designed 0..1 function
(`speed_fit`, triangular at 65 km/h) is passed through: ranking it would throw away the only absolute scale
in the mean, and two regions' canopy fractions are already comparable while their curvature sums are not.
The lists live in `way_record` (`RANKED_TERMS`, `MAPPED_TERMS`) and are asserted against `score.UNIT_TERMS`.

THE ESTIMATOR, and why this one (ruling R2). plan:89 says "rank-normalized" and names no estimator. This is
the mid-rank form:

    rank(v) = (ways below v + 0.5 x ways equal to v) / population

which is the tie group's average 1-based rank mapped to 0..1 by `(r - 0.5) / n`. One formula answers all
three of the cases the brief separates, with no branch to get wrong:
  * TIES take the average rank, because every member of the group sees the same `below` and `equal`.
  * A POPULATION OF ONE gets 0.5 - `(0 + 0.5x1)/1`. The only scorable way in a region is its own median;
    calling it the best road in the region (1.0) or the worst (0.0) would both be inventions.
  * AN ALL-EQUAL POPULATION gets 0.5 for every way, by the same arithmetic.
  * The divisor is the population size, which is >= 1 wherever a rank is computed, so there is no division
    by zero to guard. An EMPTY population ranks nothing and returns `{}`.
A rank is therefore never exactly 0.0 or 1.0 (the extremes are `0.5/n` and `1 - 0.5/n`), which keeps
CLAUDE.md's invariant true of the corpus: ranking alone cannot zero a scorable way's score, and only
motorway and trunk carry 0.

DETERMINISM. Ways are ordered by (value, `way_id`) - `ranked_order` - so the ranks do not depend on the
order rows arrive in. Two rows with equal values get the same rank whichever way the sort breaks the tie, so
the `way_id` in the key is not what makes the numbers right; it is what makes them REPRODUCIBLE, and
`ranked_order` is public so a test can assert it directly instead of hoping a rank would have moved.

THE ZERO CLASSES ARE EXCLUDED FROM THE POPULATION, NOT DROPPED. They score 0 by class (score.py:139) and
15k motorway segments would otherwise set the curve for the back roads this product exists to find. They
come back in the returned list, in their original position, in the `excluded` state - see `way_record`'s
docstring for why that state exists rather than a pass-through.

IDEMPOTENCE IS A REFUSAL, NOT A NO-OP. Normalising an already-normalised region is refused by way_id and
state: a second pass would rank the ranks, which is a well-defined and completely wrong operation (it
re-spaces the region and moves every score a little). P-DATA-01 is the plan's pin for ETL idempotence; this
module adds none of its own.
"""
from __future__ import annotations

from .way_record import RANKED_TERMS, RAW, WayRecord


def ranked_order(values: dict) -> list:
    """The way_ids of `values`, ordered by value then way_id. The order every rank is computed in."""
    return sorted(values, key=lambda way_id: (values[way_id], way_id))


def percentile_ranks(values: dict) -> dict:
    """`{way_id: value}` -> `{way_id: rank in 0..1}` by the mid-rank formula in this module's docstring.

    One pass over `ranked_order`, grouping equal values: `below` is the number of ways before the group and
    `equal` its size, so the whole group takes one rank. The generator behind
    `tests/fixtures/way_records_fixture.json` computes the same numbers by counting every pair instead -
    two algorithms, one formula, and the fixture is where they are made to agree.
    """
    population = len(values)
    if population == 0:
        return {}
    order = ranked_order(values)
    out: dict = {}
    start = 0
    while start < population:
        end = start
        while end + 1 < population and values[order[end + 1]] == values[order[start]]:
            end += 1
        equal = end - start + 1
        rank = (start + 0.5 * equal) / population
        for index in range(start, end + 1):
            out[order[index]] = rank
        start = end + 1
    return out


def population_of(records: list) -> list:
    """The records a rank is computed over: the scorable ones. Zero classes are not in it (ruling R1)."""
    return [record for record in records if not record.is_zero_class]


def refusals(records: list) -> list[str]:
    """Why this region cannot be normalised, by way_id and field name. Empty means it can.

    A region is refused whole rather than per row: a rank is a statement about a population, so one bad row
    silently dropped changes every other row's answer by 1/n.
    """
    out: list[str] = []
    seen: dict = {}
    for record in records:
        if not isinstance(record, WayRecord):
            out.append("%r is not a WayRecord" % (record,))
            continue
        if record.terms_state != RAW:
            out.append("way %s: terms_state is %s, not %s - ranking a rank re-spaces the region"
                       % (record.way_id, record.terms_state, RAW))
        for problem in record.problems():
            out.append("way %s: %s" % (record.way_id, problem))
        if record.way_id in seen:
            # Two rows for one way would sit in the ranking population twice, weighting it double and
            # putting one arbitrary row's terms in the output dict. Neither is visible in the result.
            out.append("way %s: appears twice in the region" % (record.way_id,))
        seen[record.way_id] = True
    return out


def normalise_region(records: list) -> list:
    """Every record of one region, ranked. Same records, same order, `raw` -> `normalised` / `excluded`.

    Raises ValueError naming the way_ids and fields at fault if the region cannot be normalised - see
    `refusals`. Returns a new list of new records: the input is untouched, so a caller that catches the
    refusal still has the region it started with.
    """
    problems = refusals(records)
    if problems:
        raise ValueError("region refused: %s" % "; ".join(problems))
    population = population_of(records)
    ranks = {term: percentile_ranks({record.way_id: getattr(record, term) for record in population})
             for term in RANKED_TERMS}
    out = []
    for record in records:
        if record.is_zero_class:
            out.append(record.excluded_from_population())
        else:
            out.append(record.with_ranks({term: ranks[term][record.way_id] for term in RANKED_TERMS}))
    return out
