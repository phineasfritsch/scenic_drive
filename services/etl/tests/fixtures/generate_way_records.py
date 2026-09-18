#!/usr/bin/env python
"""Generate `way_records_fixture.json`: one synthetic region of raw per-way terms, with its expected ranks.

WHAT THIS FIXTURE IS NOT. The landcover and terrain fixtures beside it are MEASURED - real ways, real
raster samples, nothing typed by hand. This one is the opposite and says so: every number in it is drawn
from a seeded generator, and no way_id here is a claim about a road. It exists to pin the NORMALISER's
arithmetic and the whole raw -> `normalise.normalise_region` -> `score.score` path over a population big
enough to have ties, both ends of every threshold and all four zero classes in it.

WHY THE EXPECTATION IS COMPUTED HERE, AND HOW IT IS DIFFERENT. `naive_rank` below counts, for one value,
every other way in the population that is below it and every one equal to it, and returns
`(below + 0.5*equal)/population`. That is the ruling's formula (T-0163 log, R2) evaluated pairwise: O(n^2),
no sort, no grouping, no way_id anywhere. `normalise.percentile_ranks` gets the same numbers from a single
pass over a sorted order, grouping equal values as it goes - which is where a tie rule and a sort key can be
wrong. Two algorithms, one formula: this file imports nothing from `etl` and does not know the module it is
an oracle for exists.

DETERMINISM. Seeded `random.Random(SEED)`, no iteration over unordered sets, floats emitted through
`json.dumps`, which uses `repr` - the shortest string that round-trips to the same double. Re-running must
leave `git diff` empty, and `test_way_records_fixture.py` rebuilds the document in memory and compares it
to the committed bytes, so a hand-edited fixture is a failing test rather than a silent one.

Run: python services/etl/tests/fixtures/generate_way_records.py
"""
from __future__ import annotations

import json
import pathlib
import random

SEED = 20260918
WAY_TARGET = 240
FIRST_WAY_ID = 700000000
OUT = pathlib.Path(__file__).resolve().parent / "way_records_fixture.json"

# JSON has no infinity literal and `allow_nan=False` refuses to invent one. "no motorway anywhere near" is
# infinity in the record, so the fixture spells it and the test translates it back.
INF = "Infinity"

# plan:83 - excluded from the ranking population and scored 0 by class. Restated, not imported: an oracle
# that imports its constants from the subject is not an oracle.
PLAN_ZERO_CLASSES = ("motorway", "motorway_link", "trunk", "trunk_link")
HIGHWAYS = ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
            "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street",
            "service")
SURFACES = (None, "asphalt", "concrete", "paved", "gravel")
BYWAY_STATUS = (None, "E", "OD")

# Producer units, and the range each is drawn from. curvature is a sum of weighted segment lengths
# (curvature.py:172), elevation_gain and relief are metres (terrain.py:85, :112), sinuosity is a ratio >= 1,
# furniture is a rate. The ranges only have to be wide enough that a rank is not degenerate.
RAW_RANGES = {
    "curvature": (0.0, 2000.0),
    "elevation_gain": (0.0, 1500.0),
    "relief": (0.0, 900.0),
    "sinuosity": (1.0, 2.6),
    "furniture": (0.0, 0.4),
}
RANKED_TERMS = tuple(RAW_RANGES)
MAPPED_TERMS = ("canopy", "impervious", "water", "speed_fit")

RAW_MID = {"curvature": 640.0, "elevation_gain": 300.0, "relief": 180.0, "sinuosity": 1.4,
           "furniture": 0.1}
MAPPED_MID = {"canopy": 0.5, "impervious": 0.25, "water": 0.1, "speed_fit": 0.6}


def naive_rank(value: float, population: list[float]) -> float:
    """The ruling's estimator, counted pairwise: the tie group's average rank mapped by (r - 0.5)/n."""
    below = 0
    equal = 0
    for other in population:
        if other < value:
            below += 1
        elif other == value:
            equal += 1
    return (below + 0.5 * equal) / len(population)


def way(index: int, highway: str, **kw) -> dict:
    """One fixture way: its WayRecord fields with RAW terms, and room for the expectation."""
    record = {"way_id": FIRST_WAY_ID + index, "highway": highway, "surface": None, "byway_status": None,
              "tunnel_meters": 0.0, "meters_to_nearest_motorway": INF, "points_of_interest": None}
    record.update(RAW_MID)
    record.update(MAPPED_MID)
    unknown = sorted(set(kw) - set(record))
    if unknown:
        raise SystemExit("way %d sets unknown field(s) %s" % (record["way_id"], unknown))
    record.update(kw)
    return {"id": "way-%04d" % index, "record": record}


def covering_ways() -> list[dict]:
    """The ways chosen by hand, one property at a time. A seeded draw cannot be relied on to hit these."""
    out: list[dict] = []

    def add(highway: str, **kw) -> None:
        out.append(way(len(out), highway, **kw))

    # Every highway class with and without a surface tag: the four zero classes, the two unsurveyed ones
    # whose absent surface is a x0.8 penalty (plan:84), and the rest.
    for highway in HIGHWAYS:
        for surface in (None, "asphalt"):
            add(highway, surface=surface)

    # A tie group on ONE term: four ways that share a curvature and differ everywhere else. The tie rule is
    # the whole reason these are here - all four must come out with the same curvature rank.
    for offset in range(4):
        add("secondary", curvature=777.0, elevation_gain=100.0 + offset, relief=50.0 + offset,
            sinuosity=1.2 + offset / 100.0, furniture=0.05 + offset / 100.0)
    # A tie group on EVERY ranked term: three ways that are identical to the ranker.
    for _ in range(3):
        add("tertiary", curvature=1234.5, elevation_gain=321.0, relief=99.0, sinuosity=1.75, furniture=0.2)

    # Alike but for the furniture rate (ruling R5): the busier roadside must score lower, and these two ways
    # are the only pair in the fixture that can show it without another term moving.
    add("secondary", curvature=900.0, elevation_gain=400.0, relief=200.0, sinuosity=1.5, furniture=0.0)
    add("secondary", curvature=900.0, elevation_gain=400.0, relief=200.0, sinuosity=1.5, furniture=0.4)

    # The extremes of the population: the region's floor and ceiling on every ranked term at once.
    add("primary", **{name: low for name, (low, _) in RAW_RANGES.items()})
    add("primary", **{name: high for name, (_, high) in RAW_RANGES.items()})

    # Each byway status, each side of the tunnel threshold, each side of the motorway-proximity threshold.
    for status in BYWAY_STATUS:
        add("secondary", byway_status=status)
    for metres in (0.0, 299.0, 300.0, 301.0, 900.0):
        add("tertiary", tunnel_meters=metres)
    for metres in (0.0, 149.0, 150.0, 151.0, INF):
        add("residential", meters_to_nearest_motorway=metres)

    # Each mapped term at both ends of 0..1: these are passed through, so the fixture has to carry rows
    # where a pass-through failure is visible in the score rather than averaged away.
    for term in MAPPED_TERMS:
        for level in (0.0, 1.0):
            add("unclassified", **{term: level})

    # `points_of_interest` set by hand on a few rows. T-0164 produces the real values; until then the record
    # carries None and the scorer is handed POI_ABSENT, and both paths need to be exercised.
    for value in (0.0, 0.25, 0.5, 0.75, 1.0):
        add("secondary", points_of_interest=value)

    # Every surface value against the classes plan:84 names and one it does not.
    for surface in SURFACES:
        for highway in ("residential", "unclassified", "tertiary"):
            add(highway, surface=surface)
    return out


def random_ways(rng: random.Random, start: int, count: int) -> list[dict]:
    """Interior values, rounded so their reprs stay short and exact."""
    tunnels = (0.0, 120.0, 299.0, 300.0, 301.0, 1400.0)
    distances = (0.0, 40.0, 149.0, 150.0, 151.0, 1200.0, INF)
    out: list[dict] = []
    for index in range(start, start + count):
        raw = {}
        for term, (low, high) in RAW_RANGES.items():
            draw = rng.random()
            if draw < 0.05:
                raw[term] = low
            elif draw < 0.10:
                # Deliberate repeats: a rank over 240 continuous draws would have no ties at all, and the
                # tie rule would then be exercised only by the hand-written groups above.
                raw[term] = round((low + high) / 2.0, 6)
            else:
                raw[term] = round(rng.uniform(low, high), 6)
        mapped = {term: round(rng.random(), 6) for term in MAPPED_TERMS}
        out.append(way(index, rng.choice(HIGHWAYS), surface=rng.choice(SURFACES),
                       byway_status=rng.choice(BYWAY_STATUS),
                       tunnel_meters=rng.choice(tunnels),
                       meters_to_nearest_motorway=rng.choice(distances), **raw, **mapped))
    return out


def expect(ways: list[dict]) -> None:
    """Stamp every way with the state it must come out in and, if it is scorable, its expected ranks."""
    population = [w for w in ways if w["record"]["highway"] not in PLAN_ZERO_CLASSES]
    ranks: dict = {}
    for term in RANKED_TERMS:
        values = [w["record"][term] for w in population]
        for w in population:
            ranks.setdefault(w["record"]["way_id"], {})[term] = naive_rank(w["record"][term], values)
    for w in ways:
        excluded = w["record"]["highway"] in PLAN_ZERO_CLASSES
        w["expected_state"] = "excluded" if excluded else "normalised"
        w["expected_ranks"] = None if excluded else ranks[w["record"]["way_id"]]


def build() -> dict:
    ways = covering_ways()
    covering = len(ways)
    if covering >= WAY_TARGET:
        raise SystemExit("the covering block alone is %d ways; raise WAY_TARGET" % covering)
    ways.extend(random_ways(random.Random(SEED), covering, WAY_TARGET - covering))
    ids = [w["record"]["way_id"] for w in ways]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate way_id(s) - the ranker refuses a region twice over one way")
    if len(ways) != WAY_TARGET:
        raise SystemExit("built %d ways, expected %d" % (len(ways), WAY_TARGET))
    expect(ways)
    population = sum(1 for w in ways if w["expected_state"] == "normalised")
    return {
        "generator": "services/etl/tests/fixtures/generate_way_records.py",
        "oracle": "naive_rank in the generator: (below + 0.5*equal)/population, counted pairwise, computed"
                  " by nothing in etl/",
        "note": "Synthetic. Every number is a seeded draw; no way_id here is a claim about a real road.",
        "seed": SEED,
        "rankedTerms": list(RANKED_TERMS),
        "mappedTerms": list(MAPPED_TERMS),
        "coveringWays": covering,
        "wayCount": len(ways),
        "populationCount": population,
        "excludedCount": len(ways) - population,
        "ways": ways,
    }


def render(doc: dict) -> bytes:
    """One way per line, so a diff names the ways that changed rather than the whole file."""
    head = {k: v for k, v in doc.items() if k != "ways"}
    lines = ["{"]
    for key, value in head.items():
        lines.append("  %s: %s," % (json.dumps(key), json.dumps(value, allow_nan=False)))
    lines.append('  "ways": [')
    body = [json.dumps(w, allow_nan=False, sort_keys=False) for w in doc["ways"]]
    lines.extend("    %s%s" % (b, "" if i == len(body) - 1 else ",") for i, b in enumerate(body))
    lines.append("  ]")
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> None:
    doc = build()
    OUT.write_bytes(render(doc))
    ways = doc["ways"]
    ties = 0
    for term in RANKED_TERMS:
        values = [w["record"][term] for w in ways if w["expected_ranks"] is not None]
        ties += len(values) - len(set(values))
    print("wrote %s" % OUT)
    print("ways=%d covering=%d random=%d" % (len(ways), doc["coveringWays"],
                                             len(ways) - doc["coveringWays"]))
    print("population=%d excluded=%d tied values across ranked terms=%d"
          % (doc["populationCount"], doc["excludedCount"], ties))
    print("distinct highway classes=%d  ways with a byway status=%d  ways with points_of_interest=%d"
          % (len({w["record"]["highway"] for w in ways}),
             sum(1 for w in ways if w["record"]["byway_status"] is not None),
             sum(1 for w in ways if w["record"]["points_of_interest"] is not None)))


if __name__ == "__main__":
    main()
