"""The per-way scenic score: the plan's formula and nothing else.

WHAT IS AND IS NOT HERE. This module takes terms that are ALREADY normalised to 0..1 and returns the score.
It opens no raster, imports no GDAL, reads no PBF, rank-normalises nothing and touches no file. That is what
makes it testable in milliseconds against the same fixture `ScenicKit.SegmentScore` is held to, on a box with
no container - which is the entire point of the split (T-0154 out of T-0146). The producers for the terms
themselves, the region rank-normaliser and the `scenic_score` 0..10 column are T-0146 and are not here.

THE FORMULA (plan lines 78-87):

    score = M^0.35 * E^0.65
    M = 0.45*curv + 0.20*elev_gain + 0.20*speed_fit + 0.15*sinuosity
    E = 0.24*canopy + 0.22*relief + 0.16*(1-impervious) + 0.14*poi + 0.12*water + 0.12*(1-furniture)
        (+ the byway bonus, capped at 1)
    tunnel > 300 m -> x0.15 ; within 150 m of a motorway -> x0.7 ; absent surface on an unsurveyed class -> x0.8
    highway in {motorway, motorway_link, trunk, trunk_link} -> 0

The mean is GEOMETRIC and the exponents are the two most product-defining constants in the repository: a
curvy industrial road and a straight redwood road are different products, and an arithmetic mean says they
are the same thing. The substitution agrees with this formula whenever M and E are close, which is most
rows; `tests/test_score_contract.py` carries rows where they are deliberately far apart.

WHAT IS IMPORTED RATHER THAN RESTATED. The byway bonus per tier and the zero classes are decisions that were
reviewed in `byways.py` and are imported from it - `status_bonus`, `apply_to_e`, `SCENIC_ZERO_CLASSES`. A
constant copied here could drift from the one the byway matcher uses, and the drift would be invisible: both
files would be internally consistent and the corpus would carry two different answers for the same road. The
weights below are NOT in byways.py and are restated here against the plan.

THE ZERO CLASSES ARE NOT A GATE. A motorway scores 0 and is still routable - the freeway-shoulders design
needs both at once (CLAUDE.md, "Product invariants"). Safety gates - unpaved by positive evidence, private
access, track - live in the GraphHopper profile and in `ScenicKit.Gates`, never here. A `surface=gravel` row
is scored here exactly like any other; it is the gate's business to refuse it.
"""
from __future__ import annotations

import math

from .byways import SCENIC_ZERO_CLASSES, apply_to_e, status_bonus

# plan:78 - alpha on M, the rest on E. Scenery-led, because this is a car product.
DRIVE_EXPONENT = 0.35
SCENERY_EXPONENT = 0.65

# plan:86 - M, how the road drives.
CURVATURE_WEIGHT = 0.45
ELEVATION_GAIN_WEIGHT = 0.20
SPEED_FIT_WEIGHT = 0.20
SINUOSITY_WEIGHT = 0.15

# plan:87 - E, what the road goes past. These six sum to 1.00.
CANOPY_WEIGHT = 0.24
RELIEF_WEIGHT = 0.22
OPEN_GROUND_WEIGHT = 0.16
POI_WEIGHT = 0.14
WATER_WEIGHT = 0.12
QUIET_ROADSIDE_WEIGHT = 0.12

# plan:85 - the soft multipliers. Both boundaries are exclusive: 300 m of tunnel is not "longer than 300 m"
# and 150.0 m from a motorway is not "within 150 m". ScenicKit pins the same two boundaries by name in
# Tests/ScenicKitTests/SegmentScoreThresholdTests.swift.
TUNNEL_THRESHOLD_M = 300.0
TUNNEL_MULTIPLIER = 0.15
MOTORWAY_PROXIMITY_M = 150.0
MOTORWAY_PROXIMITY_MULTIPLIER = 0.7

# plan:84 - a missing surface tag on one of these is worth a small penalty and a flag to the driver. The
# plan's other half, "primary/secondary/tertiary with no surface tag are paved", is this set's complement
# and is expressed by omission, exactly as ScenicKit expresses it.
UNSURVEYED_CLASSES = frozenset({"unclassified", "residential"})
UNSURVEYED_MULTIPLIER = 0.8

UNIT_TERMS = ("curvature", "elevation_gain", "speed_fit", "sinuosity", "canopy", "relief", "impervious",
              "points_of_interest", "water", "furniture")


def drive_mean(*, curvature: float, elevation_gain: float, speed_fit: float, sinuosity: float) -> float:
    """M: how the road drives."""
    return (CURVATURE_WEIGHT * curvature
            + ELEVATION_GAIN_WEIGHT * elevation_gain
            + SPEED_FIT_WEIGHT * speed_fit
            + SINUOSITY_WEIGHT * sinuosity)


def scenery_mean(*, canopy: float, relief: float, impervious: float, points_of_interest: float,
                 water: float, furniture: float) -> float:
    """E before any byway bonus. `impervious` and `furniture` enter inverted: car parks are not scenery."""
    return (CANOPY_WEIGHT * canopy
            + RELIEF_WEIGHT * relief
            + OPEN_GROUND_WEIGHT * (1.0 - impervious)
            + POI_WEIGHT * points_of_interest
            + WATER_WEIGHT * water
            + QUIET_ROADSIDE_WEIGHT * (1.0 - furniture))


def out_of_range(terms: dict) -> list[str]:
    """The names of any 0..1 terms that are not in 0..1, or are not finite.

    Reported rather than clamped, and `score` returns None rather than a number. A term out of range is an
    ETL bug, and a plausible score computed from a wrong input is the hardest kind of error to find later.
    """
    bad = []
    for name in UNIT_TERMS:
        value = float(terms[name])
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            bad.append(name)
    return bad


def raises_surface_unknown_flag(*, highway: str, surface: str | None) -> bool:
    """Whether this way's missing surface tag should be told to the driver (plan:84).

    Separate from the score deliberately: the penalty is the formula's business and the flag is the hazard
    strip's, and a route can accumulate enough flagged distance to be worth a line on screen even when no
    single way scored badly for it.
    """
    return surface is None and highway in UNSURVEYED_CLASSES


def score(*, curvature: float, elevation_gain: float, speed_fit: float, sinuosity: float, canopy: float,
          relief: float, impervious: float, points_of_interest: float, water: float, furniture: float,
          highway: str, byway_status: str | None = None, surface: str | None = None,
          tunnel_meters: float = 0.0, meters_to_nearest_motorway: float = math.inf) -> float | None:
    """The scenic score for one way in 0..1, or None if a term is outside 0..1.

    `byway_status` is Caltrans's own value (`byways.DESIGNATED` / `byways.ELIGIBLE` / None), so the bonus is
    read by `byways.status_bonus` rather than decided here.
    """
    terms = {"curvature": curvature, "elevation_gain": elevation_gain, "speed_fit": speed_fit,
             "sinuosity": sinuosity, "canopy": canopy, "relief": relief, "impervious": impervious,
             "points_of_interest": points_of_interest, "water": water, "furniture": furniture}
    if out_of_range(terms):
        return None
    if math.isnan(tunnel_meters) or tunnel_meters < 0.0 or math.isinf(tunnel_meters):
        return None
    if math.isnan(meters_to_nearest_motorway) or meters_to_nearest_motorway < 0.0:
        return None

    # plan:83. Before anything else: no byway bonus and no multiplier can lift a motorway off zero.
    if highway in SCENIC_ZERO_CLASSES:
        return 0.0

    m = drive_mean(curvature=curvature, elevation_gain=elevation_gain, speed_fit=speed_fit,
                   sinuosity=sinuosity)
    e = scenery_mean(canopy=canopy, relief=relief, impervious=impervious,
                     points_of_interest=points_of_interest, water=water, furniture=furniture)
    e = apply_to_e(e, status_bonus(byway_status))

    # 0 ** positive is 0, which is what the geometric mean should say: a way with nothing going for it on
    # one axis scores nothing, however good the other axis is.
    value = (m ** DRIVE_EXPONENT) * (e ** SCENERY_EXPONENT)

    if tunnel_meters > TUNNEL_THRESHOLD_M:
        value *= TUNNEL_MULTIPLIER
    if meters_to_nearest_motorway < MOTORWAY_PROXIMITY_M:
        value *= MOTORWAY_PROXIMITY_MULTIPLIER
    if raises_surface_unknown_flag(highway=highway, surface=surface):
        value *= UNSURVEYED_MULTIPLIER

    return value
