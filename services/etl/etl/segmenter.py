"""One way's canonical polyline -> its 100 m segments. Integers only; no float ever decides a bucket.

A way of length L yields n = max(1, L // 100_000) segments. Segment k spans [k*100_000, (k+1)*100_000)
except the last, which absorbs the remainder and is therefore 100-200 m long. A 7 m tail segment would be an
id whose existence flips with a millimetre of geometry change - the worst possible churn source - so the
remainder is merged rather than emitted.

Therefore offset_mm == k * 100_000 exactly, and the plan's `round(offset_m/100)` is implemented as integer
half-up. Python's built-in round() is BANNED on this path: it is banker's rounding on a float
(round(0.5) == 0, round(1.5) == 2) applied to a sum of great-circle legs whose last ulp can move between
builds. `assert bucket == k` fires if a future segmenter stops cutting on exact marks, instead of every id
silently shifting.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from . import geom

SEGMENT_LEN_MM = 100_000
BUCKET_HALF_MM = SEGMENT_LEN_MM // 2


def bucket_for(offset_mm: int) -> int:
    """Integer half-up. 49_999 -> 0, 50_000 -> 1, 50_001 -> 1."""
    return (offset_mm + BUCKET_HALF_MM) // SEGMENT_LEN_MM


@dataclass(frozen=True)
class Segment:
    way_id: int
    bucket: int
    offset_mm: int
    length_mm: int
    coords: tuple  # ((lat, lon), ...) in canonical direction

    @property
    def geometry(self) -> bytes:
        return geom.pack(list(self.coords))

    @property
    def box_e7(self) -> tuple:
        lons = [geom.to_e7(c[1]) for c in self.coords]
        lats = [geom.to_e7(c[0]) for c in self.coords]
        return (min(lons), min(lats), max(lons), max(lats))

    def mid_e7(self, mid: tuple) -> tuple:
        """Midpoint clamped into the segment's own e7 box.

        The clamp is real but tiny: e7 rounding of an interpolated point can land one unit (11 mm) outside
        the box its own endpoints rounded to, and `segments` CHECKs mid inside min/max. Clamping by 11 mm on
        a value used for display and for rtree centroid distance changes nothing measurable; letting the
        CHECK fire on one way in a million would stop a whole region's build.
        """
        min_lon, min_lat, max_lon, max_lat = self.box_e7
        lon = min(max(geom.to_e7(mid[1]), min_lon), max_lon)
        lat = min(max(geom.to_e7(mid[0]), min_lat), max_lat)
        return (lon, lat)


class Segmenter:
    """Cuts one way. Stateless apart from the segment length, which is a constant the tests read."""

    def __init__(self, segment_len_mm: int = SEGMENT_LEN_MM):
        self.segment_len_mm = segment_len_mm

    def cut(self, way_id: int, coords: list) -> list:
        canon = geom.canonical([tuple(c) for c in coords])
        if len(canon) < 2:
            raise ValueError(f"way {way_id}: needs at least 2 nodes, got {len(canon)}")
        cum = geom.cumulative_mm(canon)
        total = cum[-1]
        if total <= 0:
            raise ValueError(f"way {way_id}: zero length after canonicalisation")
        n = max(1, total // self.segment_len_mm)
        out = []
        for k in range(n):
            start = k * self.segment_len_mm
            end = total if k == n - 1 else (k + 1) * self.segment_len_mm
            bucket = bucket_for(start)
            assert bucket == k, f"way {way_id}: bucket {bucket} != k {k} - cuts are no longer on exact marks"
            out.append(Segment(way_id=way_id, bucket=bucket, offset_mm=start, length_mm=end - start,
                               coords=tuple(_slice(canon, cum, start, end))))
        return out


def _point_at(coords: list, cum: list, target_mm: int) -> tuple:
    """The point target_mm along the polyline. f is an integer/integer division: deterministic."""
    if target_mm <= 0:
        return coords[0]
    if target_mm >= cum[-1]:
        return coords[-1]
    i = bisect.bisect_right(cum, target_mm) - 1
    span = cum[i + 1] - cum[i]
    if span <= 0:
        return coords[i]
    return geom.interpolate(coords[i], coords[i + 1], (target_mm - cum[i]) / span)


def _slice(coords: list, cum: list, start_mm: int, end_mm: int) -> list:
    pts = [_point_at(coords, cum, start_mm)]
    for i, c in enumerate(cum):
        if start_mm < c < end_mm:
            pts.append(coords[i])
    pts.append(_point_at(coords, cum, end_mm))
    out = [pts[0]]
    for p in pts[1:]:
        if geom.key(p) != geom.key(out[-1]):
            out.append(p)
    if len(out) < 2:  # a slice shorter than one e7 step; keep both ends so the blob stays >= 16 bytes
        out = [pts[0], pts[-1]]
    return out


def midpoint(segment: Segment) -> tuple:
    """The point at length_mm // 2 along the segment, in (lat, lon)."""
    cum = geom.cumulative_mm(list(segment.coords))
    return _point_at(list(segment.coords), cum, cum[-1] // 2)
