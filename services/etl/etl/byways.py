"""Designated scenic byways, snapped to our ways.

A byway flag is worth +0.15 to E, capped. It is the one term in the score that is somebody else's judgement
rather than ours: a state agency looked at a road and said it is scenic. That makes it the second external
oracle in the plan, after Curvature - and it is only worth having if we use their judgement rather than
re-deriving one.

WHAT `Status` MEANS, because the service does not say and this decides two thirds of the data.

The Caltrans layer has 273 features with `Status` in {E: 207, OD: 66}, and NO published coded-value domain -
the field is undocumented in the service metadata, which names and describes itself only as
"eScenicHwys2014". The values are Eligible and Officially Designated, and per Caltrans's own scenic-highway
programme the difference between them is NOT scenic quality:

  ELIGIBLE is the legislative designation, assessed on the landscape itself - the breadth of what a traveller
  can see, the scenic quality of it, and how far development intrudes on the view.

  OFFICIALLY DESIGNATED is an eligible highway whose LOCAL GOVERNMENT additionally applied to Caltrans and
  adopted a Corridor Protection Program limiting development and outdoor advertising.

So an eligible highway has been assessed as scenic by the state; it simply has no city or county that did the
administrative work. Counting only OD would drop 207 of 273 segments for reasons that have nothing to do with
how the road looks - and would systematically drop rural corridors, which are the ones this product exists to
find, because they are the ones with no local government to file the paperwork.

Both therefore count. OD is weighted higher, because a protected corridor is evidence the road will STILL be
scenic when someone drives it, which is a different and also real thing.
"""
from __future__ import annotations

import math

from .curvature import distance_on_earth

# The weights the plan allots: a byway is worth +0.15 to E, capped so it cannot dominate.
DESIGNATED_BONUS = 0.15
ELIGIBLE_BONUS = 0.10
MAX_BONUS = 0.15

DESIGNATED = "OD"
ELIGIBLE = "E"
KNOWN_STATUS = frozenset({DESIGNATED, ELIGIBLE})

# How close a way has to run to a byway centreline to count as the same road. Byway geometry is digitised
# from route centrelines at a coarser scale than OSM, and a divided highway's two carriageways are ~30 m
# apart, so this cannot be tight. It cannot be loose either: at 100 m a frontage road collects the freeway's
# designation.
SNAP_TOLERANCE_M = 60.0
# A way has to overlap the byway for a real distance, not touch it at a crossing. A cross street meeting a
# byway at a junction shares one node and should not inherit the designation.
MIN_OVERLAP_FRACTION = 0.30


def status_bonus(status: str | None) -> float:
    """The E bonus for a byway status. Unknown or absent statuses score nothing rather than guessing."""
    if status == DESIGNATED:
        return DESIGNATED_BONUS
    if status == ELIGIBLE:
        return ELIGIBLE_BONUS
    return 0.0


def unknown_statuses(statuses: list[str | None]) -> set[str]:
    """Statuses outside the known set.

    The field has no published domain, so Caltrans can add a value without telling anyone. If that happens
    every new segment silently scores zero, which reads as "not a byway" rather than "we do not understand
    this data" - so it has to be detectable.
    """
    return {s for s in statuses if s is not None and s not in KNOWN_STATUS}


def point_to_segment_m(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance from a point to a segment, in metres, in a local flat approximation.

    Flat is fine here and spherical is not worth it: the distances are tens of metres, and the latitude
    correction is what actually matters. Without dividing the longitude difference by cos(latitude), an
    east-west road at this latitude reads 21% closer than it is, and the snap tolerance becomes directional.
    """
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


def overlap_fraction(way: list[tuple[float, float]], byway: list[tuple[float, float]],
                     tolerance_m: float = SNAP_TOLERANCE_M) -> float:
    """Fraction of the way's LENGTH that runs within `tolerance_m` of the byway.

    By length, not by node count. OSM node density varies enormously - a curve is drawn with many nodes and a
    straight is drawn with two - so counting nodes would let a short curly section outvote a long straight
    one and would make the answer depend on how the road was mapped.
    """
    if len(way) < 2:
        return 0.0
    near = total = 0.0
    for a, b in zip(way, way[1:]):
        seg = distance_on_earth(a[0], a[1], b[0], b[1])
        if seg <= 0:
            continue
        total += seg
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if distance_to_line_m(mid, byway) <= tolerance_m:
            near += seg
    return (near / total) if total else 0.0


def match(way: list[tuple[float, float]], byways: list[dict],
          tolerance_m: float = SNAP_TOLERANCE_M,
          min_overlap: float = MIN_OVERLAP_FRACTION) -> dict | None:
    """The best byway match for a way, or None.

    Best by overlap, then by status - a segment that runs along both an eligible and an officially
    designated corridor takes the designated one, because the stronger evidence is the one worth carrying.
    """
    best = None
    for entry in byways:
        line = entry.get("geometry") or []
        if len(line) < 2:
            continue
        frac = overlap_fraction(way, line, tolerance_m)
        if frac < min_overlap:
            continue
        key = (frac, status_bonus(entry.get("status")))
        if best is None or key > (best["overlap"], status_bonus(best.get("status"))):
            best = {"name": entry.get("name"), "status": entry.get("status"),
                    "source": entry.get("source"), "overlap": frac}
    return best


def bonus_for(way: list[tuple[float, float]], byways: list[dict], **kw) -> float:
    """The capped E bonus a way earns from byway designation."""
    m = match(way, byways, **kw)
    return 0.0 if m is None else min(MAX_BONUS, status_bonus(m["status"]))


def problems(byways: list[dict]) -> list[str]:
    """Structural checks on a parsed byway set, so a bad pull fails loudly rather than flagging nothing."""
    out = []
    if not byways:
        out.append("no byways parsed at all - an empty overlay flags nothing and looks like a clean run")
        return out
    unknown = unknown_statuses([b.get("status") for b in byways])
    if unknown:
        out.append(f"unrecognised Status values {sorted(unknown)} - the field has no published domain, "
                   f"so a new value scores zero and reads as 'not a byway'")
    empty = sum(1 for b in byways if len(b.get("geometry") or []) < 2)
    if empty:
        out.append(f"{empty} byway(s) have no usable geometry")
    if not any(b.get("status") == DESIGNATED for b in byways):
        out.append("no officially designated byways at all - the pull is probably filtered wrong")
    return out
