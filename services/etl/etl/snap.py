"""Snapping an OSM way to a reference polyline: how close, and how much of it.

This is the geometry kernel under the byway overlay. It moved out of `byways` because that module carries
the record of what a Caltrans designation MEANS, which is prose that has to keep growing, and this is
arithmetic that should not - and because nothing here is about byways. `byways` re-exports every name below,
so `byways.overlap_fraction` and `byways.SNAP_TOLERANCE_M` still resolve.

THE THREE DECISIONS, each with the failure it prevents.

cos(latitude) in the distance. Without dividing the longitude difference by cos(latitude) an east-west road
at Bay Area latitudes reads 21% closer than it is and the tolerance silently becomes an ellipse. Flat-earth
is otherwise fine here: the distances being compared are tens of metres.

Overlap by LENGTH, not by node count. OSM node density varies enormously - a curve is drawn with many nodes
and a straight with two - so counting nodes would let a short curly section outvote a long straight one and
would make the answer depend on how the road was mapped.

SAMPLE_STEP_M, and the bound it buys. Judging one midpoint per OSM segment credited the WHOLE segment
whenever its middle was near, so a 2-node chord with both endpoints 530 m off the line and its midpoint on
it scored 1.0. That is reachable - 2.33% of inter-node segments in the corridors measured for this overlay
exceed 200 m and the longest is 858 m. Segments are cut into pieces of at most SAMPLE_STEP_M and each piece
is judged on its own midpoint, so nothing further than `tolerance + SAMPLE_STEP_M/2` can be credited as
near. That sentence is only worth having while the step is well under the tolerance, which is asserted.
"""
from __future__ import annotations

import math

from .curvature import distance_on_earth

# How close a way has to run to a reference centreline to count as the same road. Byway geometry is
# digitised from route centrelines at a coarser scale than OSM and a divided highway's carriageways are
# ~30 m apart, so this cannot be tight. It does NOT separate a frontage road from a second carriageway -
# nothing about distance can - which is what `byway_route_key` exists for.
SNAP_TOLERANCE_M = 60.0
# A way has to overlap for a real distance, not touch at a crossing. A cross street meeting a byway at a
# junction shares one node and should not inherit the designation.
MIN_OVERLAP_FRACTION = 0.30
# Longest piece of a way credited or discarded on one sample. Bounds the midpoint error to tolerance + 12.5 m.
SAMPLE_STEP_M = 25.0


def point_to_segment_m(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance from a point to a segment, in metres, in a local flat approximation."""
    lat0 = math.radians((a[0] + b[0]) / 2)
    kx = 111320.0 * math.cos(lat0)
    ky = 110540.0
    px, py = p[1] * kx, p[0] * ky
    ax, ay = a[1] * kx, a[0] * ky
    bx, by = b[1] * kx, b[0] * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def distance_to_line_m(point: tuple[float, float], line: list[tuple[float, float]]) -> float:
    """Distance from a point to the nearest part of a polyline."""
    if len(line) == 1:
        return distance_on_earth(point[0], point[1], line[0][0], line[0][1])
    return min(point_to_segment_m(point, a, b) for a, b in zip(line, line[1:]))


def _subdivisions(seg_m: float, step_m: float) -> int:
    """How many pieces one OSM segment is sampled in. At least one; never fewer than length/step."""
    if step_m <= 0:
        return 1
    return max(1, math.ceil(seg_m / step_m))


def overlap_fraction(way: list[tuple[float, float]], line: list[tuple[float, float]],
                     tolerance_m: float = SNAP_TOLERANCE_M, step_m: float = SAMPLE_STEP_M) -> float:
    """Fraction of the way's LENGTH that runs within `tolerance_m` of the reference polyline."""
    if len(way) < 2:
        return 0.0
    near = total = 0.0
    for a, b in zip(way, way[1:]):
        seg = distance_on_earth(a[0], a[1], b[0], b[1])
        if seg <= 0:
            continue
        total += seg
        n = _subdivisions(seg, step_m)
        piece = seg / n
        for i in range(n):
            t = (i + 0.5) / n
            mid = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if distance_to_line_m(mid, line) <= tolerance_m:
                near += piece
    return (near / total) if total else 0.0


def length_m(line: list[tuple[float, float]]) -> float:
    """Length of a polyline in metres."""
    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(line, line[1:]))
