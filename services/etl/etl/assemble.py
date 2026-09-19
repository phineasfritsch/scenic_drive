"""The assembly: per-way producer outputs in, one scored table out.

WHAT THIS MODULE IS. The seam between the producers under `services/etl/etl/` and `score.score`. It reads a
committed JSON document of way rows, invokes each producer on the row's own raw inputs, builds a
`way_record.WayRecord` per way, hands the whole region to `normalise.normalise_region`, scores every
normalised record and returns a table. It opens no raster, reads no PBF and runs no container: running a
REAL extract - osmium, the DEM tiles, the `scenic_score` 0..10 column on the tagged output - is T-0168, and
the 2026-09-18T20:57:28Z scope cut in T-0146's log says why this half is the fixture half.

WHICH PRODUCER FEEDS WHICH FIELD (ruling R2 in T-0146's log). Invoked for real, from main:

    curvature                    curvature.way_curvature(coords, way_id)          curvature.py:172
    elevation_gain               terrain.elevation_gain(elevation_profile)        terrain.py:85
    relief                       terrain.relief(elevation_profile)                terrain.py:112
    furniture                    furniture.furniture_per_km(nodes=, length_m=)    furniture.py:85
    canopy/impervious/water      landcover.fractions(landcover_codes)             landcover.py:122
    speed_fit                    speedfit.speed_fit_for_tags(highway=, maxspeed=) speedfit.py:144
    byway_status                 byways.match(coords, byways, way_ref=)["status"] byways.py:194

TYPED LITERALS IN THE FIXTURE, named in `LITERAL_FIELDS` and in the document's own `literal_fields` key,
because their producer is on PR #94 and not on main: `sinuosity`, `tunnel_meters` and
`meters_to_nearest_motorway`. Nothing in this module measures those three, and a reader should not have to
infer it from an absence.

THE CLOSED-WAY PREDICATE IS TEMPORARY AND IS ONE LINE (ruling R3). `sinuosity.way_sinuosity` returns its
FLOOR for a closed way - the same 1.0 a straight two-node way gets - so a roundabout left in the sinuosity
ranking population is scored as the region's straightest road, and thousands of them move every other way's
rank (way_record.py's docstring; T-0146's 21:23:07Z note). The assembler must therefore set
`sinuosity_declined` itself. T-0161 (PR #94) has landed on main, so the temporary copy of the predicate this
module carried is DELETED and `CLOSED_ENDPOINT_M`, `endpoint_gap_m` and `is_closed_way` are imported from
`.sinuosity` - one definition of the closed-way predicate in the tree, which is what
`test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands` asserts by object identity.

THE COLUMN IS `score` AND NOT `scenic_score` (ruling R4). `Sources/ScenicKit/Scoring/ScoredEdge.swift:15`
reserves `scenic_score` for the `0...10` encoded value the router reads. This table carries `score.score`'s
own 0..1 number under `score.score`'s own name; the 0..10 column is T-0168's.

THE GATES ARE CLAUDE.md'S THREE, WHICH ARE FOUR BRANCHES (ruling R5, corrected for PR #102's review).
CLAUDE.md: "Hard gates are safety only: unpaved (positive evidence), private/no access, track."
`score.py:29-31` puts them in `ScenicKit.Gates` and out of the scorer, and nothing under
`services/etl/etl/` gated on tags before this module. So a gate here forces `score` to `GATE_SCORE` AFTER
the scorer has run and records `gate_reason`. THREE REASONS, FOUR RULES: "private/no access" is written in
`Gates.verdict` as two branches that return the one `GateReason.noAccess` - `access` in `closedAccess`
(Gates.swift:160) and `motor_vehicle = no` (Gates.swift:161) - which is what `GateReason.swift:31` names in
a single case. This module ported only the first until PR #102's review found the second missing, and a way
tagged `motor_vehicle=no` reached the corpus scored.

`Gates.verdict` has NINE refusal branches. FOUR are ported here. The FIVE that are not - `tracktype` at
grade3 or worse, `smoothness` worse than intermediate, a locked barrier, a ford, a refused `service` value
- are deliberately absent: a second full gate in Python is how two answers for one road reach the corpus,
and T-0146's scope is CLAUDE.md's three. That is a count, not an adjective: `test_assemble_wiring.py`
counts the branches in `Gates.swift` itself and asserts four ported plus five unported against it, and it
asserts each unported rule is still allowed here, so porting or adding one without moving the count is red.
`test_assemble.py` pins the two sets below against the literals in `Gates.swift` and the three reason names
against `GateReason.swift`'s cases, so they cannot drift apart in silence.

A MOTORWAY IS NOT GATED (ruling R7). It scores 0.0 by class inside `score.score` (score.py:139) and stays
routable - the freeway-shoulders design needs both at once. Its `gate_reason` is None, and the test says so
next to the 0.0, so no later edit can reach the right number by the wrong route.

A GATED WAY WITH A BROKEN TERM STAYS NULL. The gate overrides a NUMBER with 0.0; it does not override the
scorer's refusal to produce one. "This road is refused for safety" and "we do not know what this road is"
are different facts and the table keeps them apart.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

from . import byways, curvature, furniture, landcover, score, speedfit, terrain
from .normalise import normalise_region
from .sinuosity import CLOSED_ENDPOINT_M, endpoint_gap_m, is_closed_way
from .snap import length_m
from .way_record import POI_ABSENT_FLAG, SINUOSITY_DECLINED_FLAG, WayRecord

# Ruling R3, after T-0161: the closed-way predicate has ONE definition in the tree, `sinuosity`'s, and this
# module re-exports it rather than owning a second. `CLOSED_ENDPOINT_M` and `endpoint_gap_m` are deliberately
# bound here - `assemble.CLOSED_ENDPOINT_M` is `sinuosity.CLOSED_ENDPOINT_M`, by identity, and the tests say so.
__all__ = ["CLOSED_ENDPOINT_M", "endpoint_gap_m", "is_closed_way"]

# Gates.swift:80-82, verbatim. Positive evidence only: no surface tag is NOT unpaved.
UNPAVED_SURFACES = frozenset({"gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel"})
# Gates.swift:89, verbatim.
CLOSED_ACCESS = frozenset({"private", "no", "permit", "destination"})
TRACK_HIGHWAY = "track"
# Gates.swift:161, the other half of the `noAccess` rule. One value, not a set: `motor_vehicle=destination`
# and `=permit` are NOT refused there, and widening this to `CLOSED_ACCESS` would refuse roads ScenicKit
# routes - a gate that is stricter in the corpus than in the router is the same drift in the other
# direction.
MOTOR_VEHICLE_KEY = "motor_vehicle"
MOTOR_VEHICLE_REFUSED = "no"

# The snake_case of the `GateReason` cases these three rules refuse with (GateReason.swift:23, :26, :32).
GATE_UNPAVED_SURFACE = "unpaved_surface"
GATE_TRACK = "track"
GATE_NO_ACCESS = "no_access"
GATE_REASONS = (GATE_UNPAVED_SURFACE, GATE_TRACK, GATE_NO_ACCESS)
# What a refused way scores. Not None: the driver is not being told the road is unknown.
GATE_SCORE = 0.0

# The three fields no module under services/etl/etl/ produces yet (ruling R2). Read from the row as typed.
LITERAL_FIELDS = ("sinuosity", "tunnel_meters", "meters_to_nearest_motorway")
# score.py's own defaults (score.py:121-122), restated where a row may leave the field out.
DEFAULT_TUNNEL_M = 0.0
DEFAULT_MOTORWAY_DISTANCE_M = math.inf
# JSON has no literal for infinity; the scoring fixtures spell it this way and so does this one.
INFINITY = "Infinity"

MIN_COORDINATES = 2
LANDCOVER_TERMS = ("canopy", "impervious", "water")


def gate_reason(tags: dict) -> str | None:
    """Why this way is refused for SAFETY, by name, or None. FOUR rules, in `Gates.verdict`'s order.

    Four rules and three reasons: the last two are the two halves of ScenicKit's `noAccess`, and the order
    between them is `Gates.verdict`'s own (:160 then :161). It is not observable - both answer
    `GATE_NO_ACCESS` - and it is kept anyway, because `ops/route-autopsy` reads whichever reason fires
    first and the day a fifth rule lands between them the order stops being cosmetic.
    """
    surface = tags.get("surface")
    if surface is not None and surface in UNPAVED_SURFACES:
        return GATE_UNPAVED_SURFACE
    if tags.get("highway") == TRACK_HIGHWAY:
        return GATE_TRACK
    access = tags.get("access")
    if access is not None and access in CLOSED_ACCESS:
        return GATE_NO_ACCESS
    if tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED:
        return GATE_NO_ACCESS
    return None


def metres(value) -> float:
    """A distance from a JSON row, with this repository's spelling of infinity."""
    return math.inf if value == INFINITY else float(value)


def coordinates(row: dict) -> list:
    """The row's geometry as `(lat, lon)` pairs. Refuses a way that is not a line, by way_id."""
    coords = [(float(point[0]), float(point[1])) for point in row["coords"]]
    if len(coords) < MIN_COORDINATES:
        raise ValueError("way %s: needs at least %d coordinates, got %d"
                         % (row.get("way_id"), MIN_COORDINATES, len(coords)))
    return coords


def record_from_row(row: dict, byway_entries: list) -> WayRecord:
    """One way row -> one RAW `WayRecord`, every producer invoked (ruling R2). Refuses by way_id and field.

    Refusals rather than substitutions, for `furniture.py:88-94`'s reason: a rate of 0.0 on a way whose
    length could not carry one states "this way is rural", which is a claim about a way that does not exist.
    """
    way_id = row["way_id"]
    tags = dict(row.get("tags") or {})
    highway = tags.get("highway")
    if not highway:
        raise ValueError("way %s: no highway tag; the class decides the zero classes and the gate" % way_id)
    coords = coordinates(row)
    rate = furniture.furniture_per_km(nodes=list(row.get("furniture_nodes") or []),
                                      length_m=length_m(coords))
    if rate is None:
        raise ValueError("way %s: furniture_per_km declined; the way's length cannot carry a rate" % way_id)
    cover = landcover.fractions(list(row["landcover_codes"]))
    missing = [term for term in LANDCOVER_TERMS if term not in cover]
    if missing:
        raise ValueError("way %s: landcover buffer has no valid sample for %s"
                         % (way_id, ", ".join(missing)))
    profile = list(row["elevation_profile"])
    matched = byways.match(coords, byway_entries, way_ref=tags.get("ref"))
    return WayRecord(
        way_id=way_id,
        highway=highway,
        curvature=curvature.way_curvature(coords, way_id),
        elevation_gain=terrain.elevation_gain(profile),
        relief=terrain.relief(profile),
        sinuosity=float(row["sinuosity"]),
        furniture=rate,
        canopy=cover["canopy"],
        impervious=cover["impervious"],
        water=cover["water"],
        speed_fit=speedfit.speed_fit_for_tags(highway=highway, maxspeed=tags.get("maxspeed")),
        sinuosity_declined=is_closed_way(coords),
        surface=tags.get("surface"),
        byway_status=None if matched is None else matched["status"],
        tunnel_meters=metres(row.get("tunnel_meters", DEFAULT_TUNNEL_M)),
        meters_to_nearest_motorway=metres(row.get("meters_to_nearest_motorway",
                                                  DEFAULT_MOTORWAY_DISTANCE_M)),
    )


def score_record(record: WayRecord) -> float | None:
    """`score.score` over one normalised record. The seam the parity gate drives."""
    return score.score(**record.score_kwargs())


def unit_terms(record: WayRecord) -> dict:
    """The 0..1 terms the SCORE WAS COMPUTED FROM, by `score.UNIT_TERMS`'s own names.

    From `score_kwargs()` and not from the record's fields: `points_of_interest` is None on the record
    until T-0164 and `way_record.POI_ABSENT` in the call, and a table that carried the field would be
    reporting a term the scorer never saw.
    """
    kwargs = record.score_kwargs()
    return {name: kwargs[name] for name in score.UNIT_TERMS}


def scored_row(record: WayRecord, tags: dict) -> dict:
    """One normalised record -> one table row: the score, the gate, the terms and the explicit absences."""
    reason = gate_reason(tags)
    value = score_record(record)
    if reason is not None and value is not None:
        value = GATE_SCORE
    return {"way_id": record.way_id, "highway": record.highway, "score": value,
            "gate_reason": reason, "terms_state": record.terms_state,
            "terms": unit_terms(record), "flags": list(record.flags())}


def assemble(document: dict) -> list:
    """Every way of one region: producers -> `normalise_region` -> `score.score` -> the table.

    The whole region at once, because a rank is a statement about a population: a row that cannot be built
    refuses the run rather than being dropped, which would move every other way's rank by 1/n.
    """
    rows = list(document["ways"])
    byway_entries = list(document.get("byways") or [])
    records = [record_from_row(row, byway_entries) for row in rows]
    normalised = normalise_region(records)
    return [scored_row(record, dict(row.get("tags") or {}))
            for row, record in zip(rows, normalised)]


COUNT_NAMES = ("ways", "zero_class", "gated", SINUOSITY_DECLINED_FLAG, POI_ABSENT_FLAG, "null_score")


def counts(table: list) -> dict:
    """What the CLI prints. `null_score` is the one that must be zero (the plan's `ops/sane` check 4).

    The two flags are counted BY NAME rather than as one "flagged" total: they are different absences -
    a way that declined to answer sinuosity, and a term nothing produces yet - and a single total would
    hide T-0164 landing behind a number that did not move.
    """
    return {"ways": len(table),
            "zero_class": sum(1 for r in table if r["highway"] in byways.SCENIC_ZERO_CLASSES),
            "gated": sum(1 for r in table if r["gate_reason"] is not None),
            SINUOSITY_DECLINED_FLAG: sum(1 for r in table if SINUOSITY_DECLINED_FLAG in r["flags"]),
            POI_ABSENT_FLAG: sum(1 for r in table if POI_ABSENT_FLAG in r["flags"]),
            "null_score": sum(1 for r in table if r["score"] is None)}


def count_line(table: list) -> str:
    """`ASSEMBLE ways=8 zero_class=2 ...` - one line, the shape the ops wrappers print."""
    seen = counts(table)
    return "ASSEMBLE " + " ".join("%s=%d" % (name, seen[name]) for name in COUNT_NAMES)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.assemble", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="a way-record JSON document")
    parser.add_argument("--out", required=True, help="where to write the scored table")
    args = parser.parse_args(argv)
    document = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    table = assemble(document)
    pathlib.Path(args.out).write_text(json.dumps({"rows": table}, indent=2) + "\n", encoding="utf-8")
    print(count_line(table))
    return 0


if __name__ == "__main__":  # pragma: no cover - the module is exercised through `assemble`
    sys.exit(main())
