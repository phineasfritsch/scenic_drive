"""The Curvature project's method, reimplemented to match its published numbers.

This is deliberately NOT an improved version. Curvature publishes per-way values for Vermont, and those
values are the oracle T-0025 exists to check us against - an external answer an agent cannot fabricate, the
same discipline that caught the wrong solar oracle in T-0011. An implementation that is cleaner but different
cannot be checked against anything, so where the original has a quirk this has the same quirk, and the quirk
is named.

Read against adamfranco/curvature at master:
  curvature/geomath.py                              distance_on_earth, rad_earth_m = 6373000
  curvature/radiusmath.py                           circum_circle_radius
  curvature/post_processors/add_segment_length_and_radius.py   MAX_RADIUS = 10000, min-of-two-triangles
  curvature/post_processors/add_segment_curvature.py           the four radius bands and weights
  curvature/post_processors/filter_segment_deflections.py      the gap_distance / 175 deflection filter
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

RAD_EARTH_M = 6373000  # geomath.py. Not WGS84's 6378137 - matching the oracle matters more than being right.
MAX_RADIUS = 10000.0
DEGENERATE_RADIUS = 10000.0  # radiusmath.py returns this for a zero-area or zero-length triangle

# add_segment_curvature.py, in the order it tests them. Strict `<`, and anything at or above 175 scores 0.
LEVELS = ((30.0, 4, 2.0), (60.0, 3, 1.6), (100.0, 2, 1.3), (175.0, 1, 1.0))
LEVEL_1_MAX_RADIUS = 175.0  # also the divisor in the deflection filter, which is why it is one constant
LOOK_AHEADS = (3, 4, 5, 6, 7)


def distance_on_earth(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """geomath.distance_on_unit_sphere * rad_earth_m, including its early-outs.

    The `cos > 1` clamp is theirs: for two points a few metres apart the spherical law of cosines loses
    enough precision to push the cosine past 1, and acos would raise. Reproduced rather than replaced with
    haversine, because replacing it changes every short segment's length and therefore every radius.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    d2r = math.pi / 180.0
    phi1 = (90.0 - lat1) * d2r
    phi2 = (90.0 - lat2) * d2r
    theta1 = lon1 * d2r
    theta2 = lon2 * d2r
    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + math.cos(phi1) * math.cos(phi2))
    if cos > 1:
        return 0.0
    return math.acos(cos) * RAD_EARTH_M


def circum_circle_radius(a: float, b: float, c: float) -> float:
    """radiusmath.circum_circle_radius, quirks included.

    Two of them matter. `math.fabs` inside the sqrt means a triangle inequality violation - which floating
    point produces for nearly-collinear points - yields a real number instead of a domain error, so the
    result is a very large radius rather than an exception. And ZeroDivisionError returns 10000, but a
    divider that is merely tiny rather than exactly zero does NOT: it returns something enormous, which
    later only gets capped if the segment happens to be the last one. Both are load-bearing for matching.
    """
    if a > 0 and b > 0 and c > 0:
        divider = math.sqrt(math.fabs((a + b + c) * (b + c - a) * (c + a - b) * (a + b - c)))
        if divider == 0:
            return DEGENERATE_RADIUS
        return (a * b * c) / divider
    return DEGENERATE_RADIUS


@dataclass
class Segment:
    """One node-to-node piece of a way. `start`/`end` are (lat, lon), as in the original."""
    start: tuple[float, float]
    end: tuple[float, float]
    length: float = 0.0
    radius: float = 0.0
    curvature_level: int = 0
    curvature: float = 0.0
    way_id: int | None = None


def segments_for(coords: list[tuple[float, float]], way_id: int | None = None) -> list[Segment]:
    """Consecutive node pairs, with their great-circle lengths."""
    out = []
    for start, end in zip(coords, coords[1:]):
        s = Segment(start=start, end=end, way_id=way_id)
        s.length = distance_on_earth(start[0], start[1], end[0], end[1])
        out.append(s)
    return out


def assign_radii(segments: list[Segment]) -> None:
    """add_segment_length_and_radius.calculate_segment_radii, in its exact order.

    The order is the algorithm. Each triangle's radius is written unconditionally onto the LATER segment and
    conditionally (only if smaller) onto the earlier one, so a segment ends up with the smaller of the two
    circumcircles it belongs to - but only because the later write is overwritten on the next pass. Writing
    this as an obvious `min(left, right)` gives different numbers for the first and last segments.

    Note also where MAX_RADIUS is applied: ONLY to the final segment, and only when it exceeds the cap.
    Interior segments can and do carry radii far above 10000.
    """
    if not segments:
        return
    if len(segments) == 1:
        segments[0].radius = MAX_RADIUS
        return
    for i, segment in enumerate(segments):
        nxt = i + 1
        if nxt < len(segments):
            next_segment = segments[nxt]
            base = distance_on_earth(segment.start[0], segment.start[1],
                                     next_segment.end[0], next_segment.end[1])
            radius = circum_circle_radius(segment.length, next_segment.length, base)
            if i == 0:
                segment.radius = radius
            elif segment.radius > radius:
                segment.radius = radius
            next_segment.radius = radius
        elif segment.radius > MAX_RADIUS:
            segment.radius = MAX_RADIUS


def assign_curvature(segments: list[Segment]) -> None:
    """add_segment_curvature.add_curvature_to_segment: the first band whose max radius the segment is under."""
    for s in segments:
        s.curvature_level = 0
        s.curvature = 0.0
        for max_radius, level, weight in LEVELS:
            if s.radius < max_radius:
                s.curvature_level = level
                s.curvature = s.length * weight
                break


def segment_heading(s: Segment) -> float:
    """filter_segment_deflections.get_segment_heading.

    `atan2(dlat, dlon)` on RAW degrees, not on a projection and not with the arguments in the conventional
    bearing order. It is a rough proxy for direction that is squashed by the cosine of the latitude, and it
    is what the published numbers were computed with.
    """
    return 180 + math.atan2(s.end[0] - s.start[0], s.end[1] - s.start[1]) * (180 / math.pi)


def filter_deflections(segments: list[Segment]) -> None:
    """filter_segment_deflections: zero out curvature that is a wobble between two straight runs.

    Two quirks reproduced deliberately. The comparison is a plain `abs(a - b)` on headings, NOT the
    wrap-aware `heading_diff` helper the same class defines and never calls on this path - so a pair
    straddling the 0/360 seam reads as a ~360 degree difference and is never filtered. And the zeroing
    loop covers `range(start, start + look_ahead)`, which includes the first straight segment itself.
    """
    for i in range(len(segments)):
        for look_ahead in LOOK_AHEADS:
            j = i + look_ahead
            if j >= len(segments):
                continue
            first, nxt = segments[i], segments[j]
            if (first.curvature_level and not getattr(first, "_filtered", False)) or \
               (nxt.curvature_level and not getattr(nxt, "_filtered", False)):
                continue
            heading_diff = abs(segment_heading(first) - segment_heading(nxt))
            gap = distance_on_earth(first.end[0], first.end[1], nxt.start[0], nxt.start[1])
            if abs(heading_diff) < gap / LEVEL_1_MAX_RADIUS:
                for k in range(i, j):
                    if segments[k].curvature_level:
                        segments[k]._filtered = True
                for k in range(i, j):
                    segments[k].curvature_level = 0
                    segments[k].curvature = 0.0


def way_curvature(coords: list[tuple[float, float]], way_id: int | None = None,
                  deflection_filter: bool = True) -> float:
    """The curvature of a single way in isolation: sum of its segments' weighted lengths.

    IN ISOLATION is the caveat that matters when comparing against the published values. Curvature runs the
    deflection filter over a whole COLLECTION - every way joined end to end - so a way that shares a
    collection with others can have segments zeroed by a straight run in its neighbour. Only single-way
    collections are directly comparable to this function; the oracle comparison filters to those.
    """
    segments = segments_for(coords, way_id)
    assign_radii(segments)
    assign_curvature(segments)
    if deflection_filter:
        filter_deflections(segments)
    return sum(s.curvature for s in segments)
