#!/usr/bin/env python
"""Generate `segment_terms.json`, the one fixture both scorers are held to.

WHY THE EXPECTATION IS COMPUTED HERE. A fixture whose expected value comes from the code it checks proves
only that the code equals itself. `plan_score` below is a THIRD implementation: a deliberately naive,
line-by-line hand transcription of the plan's own formula block, written from
`~/.claude/plans/i-want-to-make-synthetic-twilight.md` lines 78-87 with the plan line cited beside each
term. It imports nothing from `services/etl/etl/score.py` and knows nothing about `ScenicKit`. It restates
every constant on purpose - an oracle that imports its constants from the subject is not an oracle.

THE ONE PLACE THE ORACLE DOES NOT FOLLOW THE PLAN'S TEXT is the byway bonus. The plan (line 87) writes a
single "+0.15 byway, capped"; the reviewed product decision (T-0028, six rounds) is TWO tiers, and it lives
in `services/etl/etl/byways.py:100` (`DESIGNATED_BONUS = 0.15`) and `:105` (`ELIGIBLE_BONUS = 0.06`). The
tiers are transcribed here as literals rather than imported, for the reason above. Every other difference
between an implementation and the plan is left alone for the differential to find.

DETERMINISM. Seeded `random.Random(SEED)`, no dict iteration over unordered sets, floats emitted through
`json.dumps`, which uses `repr` - the shortest string that round-trips to the same double - so Python and
Swift parse bit-identical values. Re-running this script on any machine must produce a byte-identical file.

Run: python Tests/Fixtures/scoring/generate.py
"""
from __future__ import annotations

import json
import math
import pathlib
import random

SEED = 20260918
ROW_TARGET = 1000
OUT = pathlib.Path(__file__).resolve().parent / "segment_terms.json"

# JSON has no infinity literal and `allow_nan=False` refuses to invent one. `SegmentTerms` uses
# `.infinity` for "no motorway anywhere near", so the fixture spells it and both readers translate it.
INF = "Infinity"

# plan:83 - these score 0 and are NOT gated; the router may still use them.
PLAN_ZERO_CLASSES = ("motorway", "motorway_link", "trunk", "trunk_link")
# plan:84 - absent surface here is a x0.8 penalty; on primary/secondary/tertiary it means "paved".
PLAN_UNSURVEYED_CLASSES = ("unclassified", "residential")

TIERS = ("none", "eligible", "designated")
HIGHWAYS = ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
            "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street",
            "service")
# `gravel` is here on purpose: the unpaved rule is a SAFETY GATE (plan:80), not the scorer's business, and
# a row whose surface is gravel must still be scored like any other.
SURFACES = (None, "asphalt", "concrete", "paved", "gravel")
UNIT_TERMS = ("curvature", "elevationGain", "speedFit", "sinuosity", "canopy", "relief", "impervious",
              "pointsOfInterest", "water", "furniture")

DEFAULTS = {
    "curvature": 0.5, "elevationGain": 0.5, "speedFit": 0.5, "sinuosity": 0.5, "canopy": 0.5,
    "relief": 0.5, "impervious": 0.5, "pointsOfInterest": 0.5, "water": 0.5, "furniture": 0.5,
    "bywayTier": "none", "highway": "residential", "surface": "asphalt", "tunnelMeters": 0.0,
    "metersToNearestMotorway": INF,
}


def motorway_distance(r: dict) -> float:
    """The row's `metersToNearestMotorway` as a double, translating the JSON infinity spelling."""
    v = r["metersToNearestMotorway"]
    return math.inf if v == INF else float(v)


def plan_score(r: dict) -> float:
    """The plan's formula, transcribed by hand. Naive on purpose: no helpers, no shared constants."""
    if r["highway"] in PLAN_ZERO_CLASSES:                                       # plan:83
        return 0.0

    m = (0.45 * r["curvature"] + 0.20 * r["elevationGain"]                      # plan:86
         + 0.20 * r["speedFit"] + 0.15 * r["sinuosity"])

    e = (0.24 * r["canopy"] + 0.22 * r["relief"] + 0.16 * (1.0 - r["impervious"])   # plan:87
         + 0.14 * r["pointsOfInterest"] + 0.12 * r["water"] + 0.12 * (1.0 - r["furniture"]))

    if r["bywayTier"] == "designated":                                          # byways.py:100
        e = min(1.0, e + 0.15)                                                  # plan:87 "capped"
    elif r["bywayTier"] == "eligible":                                          # byways.py:105
        e = min(1.0, e + 0.06)

    s = (m ** 0.35) * (e ** 0.65)                                               # plan:78

    if r["tunnelMeters"] > 300.0:                                               # plan:85
        s = s * 0.15
    if motorway_distance(r) < 150.0:                                            # plan:85, see the ruling
        s = s * 0.7                                                             # in the T-0154 task log
    if r["surface"] is None and r["highway"] in PLAN_UNSURVEYED_CLASSES:        # plan:84
        s = s * 0.8

    return s


def row(rid: str, **kw) -> dict:
    """One fixture row: an id, every input the score depends on, and the oracle's expectation."""
    unknown = set(kw) - set(DEFAULTS)
    if unknown:
        raise SystemExit("row %s sets unknown field(s) %s" % (rid, sorted(unknown)))
    r = {"id": rid}
    r.update(DEFAULTS)
    r.update(kw)
    r["expected"] = plan_score(r)
    return r


def covering_rows() -> list[dict]:
    """The rows chosen by hand, one property at a time. Random rows cannot be relied on to hit these."""
    out: list[dict] = []

    # Every highway class against every tier, with and without a surface tag. The four zero classes are
    # here three times each: a motorway that is also a designated byway must still score exactly 0.
    for hw in HIGHWAYS:
        for tier in TIERS:
            for surf in (None, "asphalt"):
                out.append(row("class-%s-%s-%s" % (hw, tier, "nosurface" if surf is None else surf),
                               highway=hw, bywayTier=tier, surface=surf))

    # Each unit term at 0 and at 1 with the others held at 0.5, and the three uniform rows.
    for term in UNIT_TERMS:
        for level in (0.0, 1.0):
            out.append(row("term-%s-%s" % (term, level), **{term: level}))
    for level in (0.0, 0.5, 1.0):
        out.append(row("uniform-%s" % level, **{t: level for t in UNIT_TERMS}))

    # M at zero with E high, and E at zero with M high: the geometric mean's whole point, and the rows an
    # arithmetic mean would get wrong. Both tiers of byway on the E-zero side, where the bonus is all of E.
    drive = {"curvature": 1.0, "elevationGain": 1.0, "speedFit": 1.0, "sinuosity": 1.0}
    scenery = {"canopy": 1.0, "relief": 1.0, "impervious": 0.0, "pointsOfInterest": 1.0, "water": 1.0,
               "furniture": 0.0}
    flat = {t: 0.0 for t in UNIT_TERMS}
    out.append(row("axis-drive-zero", **dict(flat, **scenery)))
    for tier in TIERS:
        out.append(row("axis-scenery-zero-%s" % tier, bywayTier=tier,
                       **dict(flat, impervious=1.0, furniture=1.0, **drive)))

    # The byway cap. saturated: E is already 1.00, so both tiers must land on exactly the same score.
    # below: E = 0.5, where the bonus is fully visible and the two tiers differ by 0.09 - this is the pair
    # `tiersAreNotTheSameNumber` reads, and the rows the whole differential turns on.
    # justunder: E = 0.94 base. MEASURED, not intended: +0.15 is capped to 1.0 and +0.06 lands on 1.0 too,
    # so this pair does NOT separate the tiers - it pins the cap at the boundary and nothing else. Said here
    # rather than fixed, because the fixture's bytes are quoted in T-0154's red run.
    for tier in TIERS:
        out.append(row("cap-saturated-%s" % tier, bywayTier=tier, **scenery))
        out.append(row("cap-below-%s" % tier, bywayTier=tier, canopy=0.5, relief=0.5, impervious=0.5,
                       pointsOfInterest=0.5, water=0.5, furniture=0.5))
        out.append(row("cap-justunder-%s" % tier, bywayTier=tier, canopy=1.0, relief=1.0, impervious=0.0,
                       pointsOfInterest=1.0, water=1.0, furniture=0.5))

    # Both sides of the tunnel threshold, including the nearest representable doubles either side of 300.
    for metres in (0.0, 1.0, 299.0, math.nextafter(300.0, 0.0), 300.0, math.nextafter(300.0, math.inf),
                   301.0, 1200.0):
        for tier in ("none", "eligible"):
            out.append(row("tunnel-%r-%s" % (metres, tier), tunnelMeters=metres, bywayTier=tier))

    # Both sides of the motorway-proximity threshold, same treatment. 150.0 exactly is NOT within 150 m.
    for metres in (0.0, 1.0, 149.0, math.nextafter(150.0, 0.0), 150.0, math.nextafter(150.0, math.inf),
                   151.0, 5000.0, INF):
        for tier in ("none", "designated"):
            out.append(row("motorway-%s-%s" % (metres, tier), metersToNearestMotorway=metres,
                           bywayTier=tier))

    # Both multipliers at once, on an unsurveyed class with no surface tag: x0.15 x 0.7 x 0.8 together.
    for hw in ("residential", "unclassified", "primary", "service"):
        for surf in (None, "asphalt"):
            out.append(row("stacked-%s-%s" % (hw, "nosurface" if surf is None else surf), highway=hw,
                           surface=surf, tunnelMeters=900.0, metersToNearestMotorway=80.0,
                           bywayTier="eligible"))

    # Every surface value against the two classes the x0.8 rule names, plus one it does not.
    for surf in SURFACES:
        for hw in ("residential", "unclassified", "tertiary"):
            out.append(row("surface-%s-%s" % ("nosurface" if surf is None else surf, hw), surface=surf,
                           highway=hw))

    return out


def random_rows(rng: random.Random, start: int, count: int) -> list[dict]:
    """Interior values, drawn once and rounded so their reprs stay short and exact in both languages."""
    tunnels = (0.0, 50.0, 299.0, 300.0, 301.0, 640.0, 1500.0)
    distances = (0.0, 25.0, 149.0, 150.0, 151.0, 900.0, INF)
    out: list[dict] = []
    for i in range(start, start + count):
        terms = {}
        for term in UNIT_TERMS:
            draw = rng.random()
            if draw < 0.06:
                terms[term] = 0.0
            elif draw < 0.12:
                terms[term] = 1.0
            else:
                terms[term] = round(rng.random(), 6)
        out.append(row("rand-%04d" % i,
                       highway=rng.choice(HIGHWAYS),
                       bywayTier=rng.choice(TIERS),
                       surface=rng.choice(SURFACES),
                       tunnelMeters=rng.choice(tunnels + (round(rng.uniform(0.0, 1800.0), 3),)),
                       metersToNearestMotorway=rng.choice(distances + (round(rng.uniform(0.0, 800.0), 3),)),
                       **terms))
    return out


def build() -> dict:
    rows = covering_rows()
    covering = len(rows)
    if covering >= ROW_TARGET:
        raise SystemExit("the covering block alone is %d rows; raise ROW_TARGET" % covering)
    rows.extend(random_rows(random.Random(SEED), 0, ROW_TARGET - covering))
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate row id(s) - an id is how a failure is named")
    if len(rows) != ROW_TARGET:
        raise SystemExit("built %d rows, expected %d" % (len(rows), ROW_TARGET))
    return {
        "generator": "Tests/Fixtures/scoring/generate.py",
        "oracle": "a hand transcription of the plan's formula (lines 78-87), computed by NEITHER scorer",
        "seed": SEED,
        "coveringRows": covering,
        "rowCount": len(rows),
        "rows": rows,
    }


def write(doc: dict) -> None:
    head = {k: v for k, v in doc.items() if k != "rows"}
    lines = ["{"]
    for key, value in head.items():
        lines.append("  %s: %s," % (json.dumps(key), json.dumps(value, allow_nan=False)))
    lines.append('  "rows": [')
    body = [", ".join("%s: %s" % (json.dumps(k), json.dumps(v, allow_nan=False)) for k, v in r.items())
            for r in doc["rows"]]
    lines.extend("    {%s}%s" % (b, "" if i == len(body) - 1 else ",") for i, b in enumerate(body))
    lines.append("  ]")
    lines.append("}")
    OUT.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def main() -> None:
    doc = build()
    write(doc)
    rows = doc["rows"]
    by_tier = {t: sum(1 for r in rows if r["bywayTier"] == t) for t in TIERS}
    zero = sum(1 for r in rows if r["highway"] in PLAN_ZERO_CLASSES)
    print("wrote %s" % OUT)
    print("rows=%d covering=%d random=%d" % (len(rows), doc["coveringRows"],
                                             len(rows) - doc["coveringRows"]))
    print("byway tiers: " + ", ".join("%s=%d" % (t, by_tier[t]) for t in TIERS))
    print("zero-class rows=%d  distinct highway classes=%d  nonzero expected=%d"
          % (zero, len({r["highway"] for r in rows}), sum(1 for r in rows if r["expected"] > 0.0)))


if __name__ == "__main__":
    main()
