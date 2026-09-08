"""Geometry for the corpus: e7 packing, canonical direction, and the one distance primitive the matcher uses.

Two things here are load-bearing beyond arithmetic.

`canonical` is the single largest churn saving in the whole pipeline and it is applied before anything is
measured. Hitting "Reverse Direction" in JOSM is one of the most common OSM edits; without canonicalisation
it moves every segment on a way from offset x to L-x, changing every bucket and therefore every segment id,
and every saved drive over that road breaks. With it, a reversal is free: the canonical polyline is
byte-identical, geom_sha256 matches, and the way never reaches the matcher. The closed-ring branch does the
same for a roundabout whose ring start node moved, which is an equally routine edit.

`point_to_polyline_m` is used at two scales - the 25 m match radius and the 10 % change threshold - and there
is deliberately only one of it. A second distance function gives two answers that each look right.
"""
from __future__ import annotations

import math
import struct

from .curvature import RAD_EARTH_M
from .terrain import resample

E7 = 1e7
DEG = math.pi / 180.0
PACK = struct.Struct("<ii")  # (lon_e7, lat_e7): little-endian so Swift reads a native Int32 array


def to_e7(value: float) -> int:
    return int(round(value * E7))


def key(coord: tuple[float, float]) -> tuple[int, int]:
    """A node's identity for ordering and comparison: quantised to e7, about 11 mm."""
    return (to_e7(coord[0]), to_e7(coord[1]))


def pack(coords: list[tuple[float, float]]) -> bytes:
    """(lat, lon) floats -> the geometry BLOB: little-endian int32 (lon_e7, lat_e7) pairs, 8 bytes a node."""
    return b"".join(PACK.pack(to_e7(lon), to_e7(lat)) for lat, lon in coords)


def unpack(blob: bytes) -> list[tuple[float, float]]:
    if len(blob) % 8:
        raise ValueError(f"geometry blob is {len(blob)} bytes, not a multiple of 8")
    return [(lat / E7, lon / E7) for lon, lat in PACK.iter_unpack(blob)]


def canonical(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """One polyline per line on the ground, whichever way the mapper drew it.

    A closed ring is rotated to its smallest node and then oriented by comparing the forward and reverse node
    sequences, so a ring start node moved by an editor produces the identical list.
    """
    if len(coords) < 2:
        return list(coords)
    if len(coords) > 3 and key(coords[0]) == key(coords[-1]):
        ring = list(coords[:-1])
        i = min(range(len(ring)), key=lambda j: key(ring[j]))
        rot = ring[i:] + ring[:i]
        fwd = [key(c) for c in rot[1:]]
        bwd = [key(c) for c in reversed(rot[1:])]
        if bwd < fwd:
            rot = [rot[0]] + list(reversed(rot[1:]))
        return rot + [rot[0]]
    return list(coords) if key(coords[0]) <= key(coords[-1]) else list(reversed(coords))


def is_closed(coords: list[tuple[float, float]]) -> bool:
    return len(coords) > 3 and key(coords[0]) == key(coords[-1])


def leg_mm(a: tuple[float, float], b: tuple[float, float]) -> int:
    """One node-to-node length in integer millimetres.

    There is exactly one distance function in this pipeline (curvature.distance_on_earth, which the Curvature
    oracle in T-0025 is checked against) and this is the only place it becomes a stored quantity. Integer mm
    from here on: no float ever decides a bucket.
    """
    from .curvature import distance_on_earth
    return int(round(distance_on_earth(a[0], a[1], b[0], b[1]) * 1000.0))


def cumulative_mm(coords: list[tuple[float, float]]) -> list[int]:
    """Cumulative arclength at each node, summed as Python ints strictly in canonical node order."""
    out = [0]
    for a, b in zip(coords, coords[1:]):
        out.append(out[-1] + leg_mm(a, b))
    return out


def interpolate(a: tuple[float, float], b: tuple[float, float], f: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _project(origin: tuple[float, float], p: tuple[float, float]) -> tuple[float, float]:
    """Local equirectangular metres about `origin`. At 25 m the projection error is far below a millimetre."""
    x = (p[1] - origin[1]) * math.cos(origin[0] * DEG) * DEG * RAD_EARTH_M
    y = (p[0] - origin[0]) * DEG * RAD_EARTH_M
    return (x, y)


def point_to_segment_m(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = _project(p, a)
    bx, by = _project(p, b)
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den <= 0.0:
        return math.hypot(ax, ay)
    t = -(ax * dx + ay * dy) / den
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(ax + dx * t, ay + dy * t)


def point_to_polyline_m(p: tuple[float, float], line: list[tuple[float, float]]) -> float:
    if len(line) == 1:
        return point_to_segment_m(p, line[0], line[0])
    return min(point_to_segment_m(p, a, b) for a, b in zip(line, line[1:]))


def off_fraction(a: list[tuple[float, float]], b: list[tuple[float, float]],
                 radius_m: float, step_m: float) -> float:
    """Fraction of A's samples that lie further than radius_m from polyline B."""
    samples = resample(a, step_m)
    if not samples:
        return 1.0
    off = sum(1 for p in samples if point_to_polyline_m(p, b) > radius_m)
    return off / len(samples)


def covered_fraction(a: list[tuple[float, float]], b: list[tuple[float, float]],
                     radius_m: float, step_m: float) -> float:
    """cov(A, B): the fraction of A that lies ON B. Directional; the matcher takes the min of both ways."""
    return 1.0 - off_fraction(a, b, radius_m, step_m)


def bearing(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Degrees clockwise from north. Computed in the matcher and NEVER stored: atan2 is not correctly
    rounded and differs between libm implementations, which would make the committed content digest
    platform dependent - fatal here, because ops/test runs this tier on the Windows host."""
    x, y = _project(a, b)
    return math.degrees(math.atan2(x, y)) % 360.0


def fold(delta_deg: float) -> float:
    """Direction-free angular difference: 170 deg apart is 10 deg of road, drawn the other way."""
    m = abs(delta_deg) % 180.0
    return min(m, 180.0 - m)
