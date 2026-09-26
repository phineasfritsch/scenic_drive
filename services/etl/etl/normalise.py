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

A RANK IS A STATEMENT ABOUT ITS POPULATION, AND `reference` IS WHERE THAT POPULATION IS CHOSEN. By default
the population is the region's own scorable ways, which is what this module has always done and what
T-0163's ruling R1 decided. That default makes `scenic_score` REGION-RELATIVE: the least-flat road in a
table-flat region takes the same `relief` rank a Sierra pass takes in its own region, and the product
question that follows (whether plan:117's honest-failure floor can ever fire in a flat region) is filed
separately and is NOT decided here. `reference` is the seam for whichever way it is decided: pass
`{term: [values...]}` and those terms are ranked against the supplied distribution - a statewide sample, an
anchor corpus - instead of the region's own, with terms left out of the mapping keeping today's behaviour.
Semantics on purpose: the way's own value is counted INTO the reference population, so the estimator is the
same mid-rank formula and 0.0 and 1.0 stay unreachable. Ranking against a reference that excluded the way
itself would hand exactly 1.0 to any way above every reference value and exactly 0.0 to any way below every
one, and a scorable way on 0.0 is what ruling R2 exists to prevent.

A WAY THAT DECLINED TO ANSWER IS OUT OF THAT TERM'S POPULATION. `way_record.WayRecord.sinuosity_declined`
says the producer could not measure sinuosity (T-0161's closed way: zero straight-line distance, no ratio)
rather than measured a low one. Such ways are left out of the SINUOSITY population - thousands of
roundabouts sharing one floor value would move every other way's rank - and come back at
`way_record.DECLINED_RANK`, flagged. Their other four terms are ranked normally: declining one term is not
declining the road.

IDEMPOTENCE IS A REFUSAL, NOT A NO-OP. Normalising an already-normalised region is refused by way_id and
state: a second pass would rank the ranks, which is a well-defined and completely wrong operation (it
re-spaces the region and moves every score a little). P-DATA-01 is the plan's pin for ETL idempotence; this
module adds none of its own.
"""
from __future__ import annotations

import bisect
import math

from .way_record import DECLINED_RANK, RANKED_TERMS, RAW, WayRecord

# The ranked terms a way can DECLINE to answer, and the record field that says it did. Only sinuosity has
# one today (T-0161's closed ways); the mapping is here so a second term is a row, not a branch.
DECLINED_FIELD = {"sinuosity": "sinuosity_declined"}


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


def ranks_against(values: dict, reference: list) -> dict:
    """`{way_id: value}` -> `{way_id: rank}` against a SUPPLIED population instead of the region's own.

    The same mid-rank formula, evaluated over `reference` plus the way itself: `below` and `equal` are
    counted in the reference distribution, `equal` is then incremented for the way, and the divisor is
    `len(reference) + 1`. Counting the way in is what keeps the rank strictly inside 0..1 - see this
    module's docstring - and it is also why two ways with equal values get equal ranks here, while a way's
    rank no longer depends on its neighbours at all. That independence is the entire point of a reference.
    """
    population = len(reference) + 1
    out: dict = {}
    for way_id in ranked_order(values):
        value = values[way_id]
        below = sum(1 for other in reference if other < value)
        equal = sum(1 for other in reference if other == value) + 1
        out[way_id] = (below + 0.5 * equal) / population
    return out


def ranks_against_sorted(values: dict, reference: list) -> dict:
    """`ranks_against` over a reference that is already SORTED ASCENDING - the same numbers, in log time.

    `ranks_against` scans the whole reference for every way. Over the LA region's reference - about 550,000
    values a term - that is 3e11 comparisons a term, which is not slow, it is never. `bisect_left` is the
    count of reference values strictly BELOW the way's value and `bisect_right - bisect_left` the count
    EQUAL to it, which are exactly the two numbers the linear scan counts, so the arithmetic below is
    `ranks_against`'s arithmetic character for character: the way itself is counted into the equal group
    (`+ 1`) and the divisor is `len(reference) + 1`.

    The two are held together by a test, not by this paragraph: `tests/test_region_reference.py::
    test_the_bisect_rank_equals_ranks_against_value_for_value` compares them EXACTLY over a population with
    ties, a probe below every reference value, one above every one, and probes equal to the extremes.
    """
    population = len(reference) + 1
    out: dict = {}
    for way_id in ranked_order(values):
        value = values[way_id]
        below = bisect.bisect_left(reference, value)
        equal = bisect.bisect_right(reference, value) - below + 1
        out[way_id] = (below + 0.5 * equal) / population
    return out


def population_of(records: list) -> list:
    """The records a rank is computed over: the scorable ones. Zero classes are not in it (ruling R1)."""
    return [record for record in records if not record.is_zero_class]


def answering(term: str, records: list) -> list:
    """The records of `records` that MEASURED `term`. A way that declined is not in that term's curve."""
    field = DECLINED_FIELD.get(term)
    if field is None:
        return list(records)
    return [record for record in records if not getattr(record, field)]


def declined(term: str, record) -> bool:
    """Whether this record declined to answer `term`, by the field the record declares it in."""
    field = DECLINED_FIELD.get(term)
    return field is not None and bool(getattr(record, field))


def reference_refusals(reference) -> list[str]:
    """Why a supplied reference distribution cannot be ranked against, by term. Empty means it can."""
    out: list[str] = []
    if not isinstance(reference, dict):
        return ["reference %r is not a mapping of term -> values" % (reference,)]
    for term in sorted(set(reference) - set(RANKED_TERMS)):
        out.append("reference term %s is not one of %s" % (term, ", ".join(RANKED_TERMS)))
    for term in RANKED_TERMS:
        if term not in reference:
            continue
        values = reference[term]
        if not isinstance(values, (list, tuple)) or not values:
            out.append("reference %s is empty; a rank against nothing is not a rank" % term)
            continue
        for value in values:
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))):
                out.append("reference %s holds %r, which is not a finite number" % (term, value))
    return out


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


def normalise_region(records: list, reference: dict | None = None) -> list:
    """Every record of one region, ranked. Same records, same order, `raw` -> `normalised` / `excluded`.

    `reference` is an optional `{term: [values...]}` distribution to rank those terms against instead of
    the region's own scorable ways; the default, None, is the region's own population and is what every
    caller gets until the region-relativity question is decided (see this module's docstring). A term
    absent from the mapping keeps the default. Raises ValueError naming the way_ids and fields at fault if
    the region cannot be normalised - see `refusals` - or naming the terms at fault in `reference`. Returns
    a new list of new records: the input is untouched, so a caller that catches the refusal still has the
    region it started with.
    """
    problems = refusals(records)
    if reference is not None:
        problems = problems + reference_refusals(reference)
    if problems:
        raise ValueError("region refused: %s" % "; ".join(problems))
    population = population_of(records)
    ranks = {}
    for term in RANKED_TERMS:
        values = {record.way_id: getattr(record, term) for record in answering(term, population)}
        if reference is not None and term in reference:
            ranks[term] = ranks_against_sorted(values, sorted(reference[term]))
        else:
            ranks[term] = percentile_ranks(values)
    out = []
    for record in records:
        if record.is_zero_class:
            out.append(record.excluded_from_population())
        else:
            out.append(record.with_ranks({term: _rank_of(record, term, ranks) for term in RANKED_TERMS}))
    return out


def _rank_of(record, term: str, ranks: dict) -> float:
    """This way's value for `term` after normalisation: its rank, or the floor if it declined to answer.

    The lookup is deliberately a KeyError and not a `.get(way_id, DECLINED_RANK)`: a way missing from a
    term's ranks for any reason OTHER than declining is a bug in this module, and a default would write it
    into the corpus as the region's straightest road.
    """
    if declined(term, record):
        return DECLINED_RANK
    return ranks[term][record.way_id]
