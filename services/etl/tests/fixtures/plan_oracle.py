"""The oracle for `way_records_fixture.json`: the plan's own arithmetic, transcribed by hand.

WHAT THIS FILE IS. Two expectations, computed by NOTHING under test. `naive_rank` is the region percentile
rank (T-0163's ruling R2) counted pairwise; `plan_score` is the plan's formula block (lines 78-87)
transcribed line by line over those ranks. A fixture whose expected value comes from the code it checks
proves only that the code equals itself, so this module imports NOTHING - not `normalise`, not `score`, not
`way_record`, not the standard library - and restates every constant it needs. An oracle that imports its
constants from the subject is not an oracle.

It is a file of its own for the reason `generate_way_records.py` is: the generator builds a population and
this decides what the answers are, they are separate concerns, and together they are over the 300-line cap.
The generator loads it BY PATH, the same way `test_way_records_fixture.py` loads the generator, because
`tests/fixtures` is a data directory and not an importable package.

THE ONE PLACE THE TRANSCRIPTION DOES NOT FOLLOW THE PLAN'S TEXT is the byway bonus: the plan (line 87)
writes a single "+0.15 byway, capped", and the reviewed product decision (T-0028, six rounds) is TWO tiers,
`byways.py:100` (`DESIGNATED_BONUS = 0.15`) and `:105` (`ELIGIBLE_BONUS = 0.06`). Those two numbers are
transcribed here as literals, exactly as `Tests/Fixtures/scoring/generate.py` transcribes them. Every other
difference between an implementation and the plan is left alone for the differential to find.
"""
from __future__ import annotations

# JSON has no infinity literal, so the fixture spells "no motorway anywhere near" as this string and every
# reader translates it back. Restated here rather than imported from the generator.
INF = "Infinity"

# plan:83 - these score 0 and are NOT gated; the router may still use them (CLAUDE.md, product invariants).
PLAN_ZERO_CLASSES = ("motorway", "motorway_link", "trunk", "trunk_link")
# plan:84 - an absent surface tag on one of these is a x0.8 penalty; elsewhere it means "paved".
PLAN_UNSURVEYED_CLASSES = ("unclassified", "residential")
# Caltrans's own two status values and the reviewed per-tier bonus (byways.py:100, :105).
DESIGNATED, DESIGNATED_BONUS = "OD", 0.15
ELIGIBLE, ELIGIBLE_BONUS = "E", 0.06
# What the record hands the scorer for a `points_of_interest` T-0164 has not produced yet, and what a way
# that DECLINED to answer a ranked term gets instead of a rank.
POI_ABSENT = 0.0
DECLINED_FLOOR = 0.0
# The ranked terms, and the record field that says a way could not measure one. Only sinuosity has one
# today: T-0161's `way_sinuosity` returns its floor for a CLOSED way, where the straight-line distance is
# zero and the ratio is not a number. A floor is not a measurement, so it is not in the population.
RANKED_TERMS = ("curvature", "elevation_gain", "relief", "sinuosity", "furniture")
DECLINED_FIELD = {"sinuosity": "sinuosity_declined"}


def naive_rank(value: float, population: list) -> float:
    """The ruling's estimator, counted pairwise: the tie group's average rank mapped by (r - 0.5)/n.

    O(n^2), no sort, no grouping, no way_id anywhere. `normalise.percentile_ranks` gets the same numbers
    from one pass over a sorted order, grouping equal values as it goes - which is where a tie rule and a
    sort key can be wrong. Two algorithms, one formula; the fixture is where they are made to agree.
    """
    below = 0
    equal = 0
    for other in population:
        if other < value:
            below += 1
        elif other == value:
            equal += 1
    return (below + 0.5 * equal) / len(population)


def declines(record: dict, term: str) -> bool:
    """Whether this way declined to answer `term`, and is therefore out of that term's population."""
    field = DECLINED_FIELD.get(term)
    return field is not None and bool(record[field])


def plan_score(record: dict, ranks: dict) -> float:
    """The plan's formula over the naive ranks. Naive on purpose: no helpers, no shared constants.

    `ranks` holds this way's five RANKED terms; the four MAPPED terms (`canopy`, `impervious`, `water`,
    `speed_fit`) are read straight off the record, because they arrive in 0..1 and are passed through
    (T-0163's ruling R1). Getting that division wrong in either direction shows up here as a different
    number for most of the region, which is the point of scoring the whole fixture rather than sampling it.
    """
    if record["highway"] in PLAN_ZERO_CLASSES:                                      # plan:83
        return 0.0

    m = (0.45 * ranks["curvature"] + 0.20 * ranks["elevation_gain"]                 # plan:86
         + 0.20 * record["speed_fit"] + 0.15 * ranks["sinuosity"])

    poi = POI_ABSENT if record["points_of_interest"] is None else record["points_of_interest"]
    e = (0.24 * record["canopy"] + 0.22 * ranks["relief"]                           # plan:87
         + 0.16 * (1.0 - record["impervious"]) + 0.14 * poi
         + 0.12 * record["water"] + 0.12 * (1.0 - ranks["furniture"]))

    if record["byway_status"] == DESIGNATED:
        e = min(1.0, e + DESIGNATED_BONUS)                                          # plan:87 "capped"
    elif record["byway_status"] == ELIGIBLE:
        e = min(1.0, e + ELIGIBLE_BONUS)

    s = (m ** 0.35) * (e ** 0.65)                                                   # plan:78

    if record["tunnel_meters"] > 300.0:                                             # plan:85
        s = s * 0.15
    distance = record["meters_to_nearest_motorway"]
    if distance != INF and float(distance) < 150.0:                                 # plan:85
        s = s * 0.7
    if record["surface"] is None and record["highway"] in PLAN_UNSURVEYED_CLASSES:  # plan:84
        s = s * 0.8

    return s
