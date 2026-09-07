"""Designated scenic byways, snapped to our ways.

A byway flag is somebody else's judgement rather than ours: a public agency looked at a road and said it is
scenic. That makes it the second external oracle in the plan, after Curvature, and it is only worth having
if we use their judgement rather than re-deriving one.

WHAT CALTRANS `Status` MEANS. The FeatureServer publishes no coded-value domain for the field (`domain:
null`, checked live), so this comes from the programme's own documents, not from inference:

  E   ELIGIBLE. The LEGISLATURE has listed the route in Streets & Highways Code 263.1-263.8. S&H 263: "The
      state scenic highway system is hereby established and shall be composed of the highways specified in
      this article", and the listed routes are "either eligible for designation as state scenic highways or
      have been so designated". Caltrans's Scenic Highway Guidelines: "Legislative action establishes and
      amends this list" and "Additions and deletions can only be made through legislative action."
      Eligibility is a STATUTORY LISTING obtained by a bill. It is NOT a scenic assessment. The visual
      assessment - vividness, intactness, unity, "not more then one-quarter of the proposed scenic highway
      should be impacted by visual intrusions" - is STEP 1 OF THE NOMINATION, which a local governing body
      prepares AFTER the route is already eligible in order to apply for designation. An eligible-only route
      has never had one done.

  OD  OFFICIALLY DESIGNATED. Eligible, and then: the local governing body prepared the visual assessment and
      a Scenic Highway Proposal, Caltrans reviewed it, the body adopted a Corridor Protection Program
      limiting development, outdoor advertising and earthmoving, the District Scenic Highway Coordinator
      recommended designation, the District Director concurred, the State Scenic Highway Coordinator
      concurred, and "If the Caltrans Director approves the scenic highway recommendation, the route becomes
      an official State Scenic Highway." Every one of those steps can decline.

An earlier version of this file asserted the reverse - that E was "assessed on the landscape itself" and
that the E/OD difference was "administrative, not scenic". Both are false, and the weights below were
originally derived from them. This paragraph stays so the correction is not silently re-lost.

MEASURED, from the pinned pull (`inputs/manifest.yaml`, byways-caltrans.geojson):
  273 features, `Status` in {E: 207, OD: 66}, no other value.
  `DESIG_DATE` is set on all 66 OD rows and blank on 206 of the 207 E rows - designation is an event
    Caltrans records, eligibility is not. The OD dates run 1965..2007; only 7 fall after 1990.
  `MILES` is unusable: 0 or null on 206/207 E rows and 41/66 OD rows. Length here is computed from geometry.
  By centreline length OD is 2512.5 km of 12880.4 km, so 19.5% of the eligible system has ever been
    designated. Every OD route was eligible first, so that ratio is the base rate itself.

THE WEIGHTS, AND WHICH PART OF THEM IS A JUDGEMENT.
  OD = 0.15, the plan's number, unchanged: it is the only status that has cleared a substantive review.
  E  = 0.06, bracketed by two anchors, with the point between them chosen rather than derived:
       FLOOR 0.029 = 0.195 x 0.15. What an eligible route is worth if it is worth only its chance of ever
         clearing the second gate. Too harsh: most eligible routes never clear it because no local
         government ever filed a Corridor Protection Program, and having no local government to file
         correlates with being rural - which is what this product exists to find, not with being unscenic.
       CEILING 0.15, i.e. E == OD. Unsupportable: the scenic criteria are applied at DESIGNATION time, so an
         eligible-only route has never had them applied, and the listing is never revisited.
       0.06 is 40% of OD and about twice the measured base rate. IT IS A JUDGEMENT. The evidence fixes the
       bracket; it does not fix the point inside it, and no amount of further reading will.

THE CAP. The plan says "+0.15 byway, capped". `capped` governs E's TOTAL, not the bonus term: the six base
E terms already sum to 1.00, so a way at E_base 0.95 that is also designated must land at 1.0, not 1.10.
`apply_to_e` is that cap and it is the only one that binds. MAX_BONUS is the plan's per-term allowance,
enforced by a test over the whole status table - a `min(MAX_BONUS, ...)` at the call site could never bind
at these values and only looked like a check.

WHICH MATCH WINS. Status first, overlap only as the tiebreak. The overlap gate is where "is this the same
road" gets decided; once two entries have both cleared it the remaining question is which designation to
carry, and overlap fraction does not answer that - it measures how much of the OSM way a corridor covers,
which is a function of where OSM chose to split the way. So a way running 60% along a designated corridor
and 70% along an eligible one carries the designated one. This file used to document that and do the
opposite.

FRONTAGE ROADS, AND WHY THE TOLERANCE IS NOT THE LEVER. Measured on real OSM geometry: I-280's two
carriageways are 28-46 m apart, and real frontage roads - Junipero Serra Boulevard beside I-280, Redwood
Highway Frontage Road beside US-101 - sit 20-45 m from their mainline. Same distance band. No value of
SNAP_TOLERANCE_M separates them, so 60 m is not "proven safe"; it is the loosest value at which divided
carriageways still work, and the frontage-road problem has to be solved by something other than distance.

That something is the route key. A Caltrans row is a postmiled segment OF A NUMBERED STATE ROUTE (`RTE`), so
a way that does not claim to be that route is not that route, whatever it runs beside. `route_numbers` reads
the OSM `ref` tag and `match` requires an intersection. Measured over three real corridors:
  I-280 vs Caltrans SM RTE=280 - 180 ways clear the 30% gate (82.70 km). The route key rejects 6.70 km: 7
    ways whose ref names another route (Skyline Boulevard, Bunker Hill Drive, `CA 35`) and 14 with no ref at
    all, every one of them Junipero Serra Boulevard or Skyline Boulevard. Not one is an I-280 segment.
  CA-35 vs Caltrans SM RTE=35 - 35 ways clear (40.00 km). It rejects 1.14 km: one Junipero Serra Freeway
    way, `ref=I 280`, at overlap 0.301 - the mirror-image false positive.
  US-101 vs Caltrans MRN RTE=101 - 18 ways clear (6.37 km), all `ref=US 101`. It rejects nothing.
  Total 7.84 km rejected, none of it a genuine byway segment.
Matching the NUMBER rather than the prefix is not a shortcut: Caltrans numbers Interstate, US and state
routes in one namespace, which is why `RTE` is a bare number, so inside California the number identifies the
route. A suffixed ref such as `US 101 Business` yields no number on purpose - a business route is explicitly
not the mainline, and inheriting the mainline's designation is the failure being prevented.

LONG SEGMENTS. `overlap_fraction` samples, it does not integrate. Sampling one midpoint per OSM segment
credited a whole segment whenever its middle was near, so a single 2-node chord with both ends 530 m off the
byway and its midpoint on it scored 1.0. That is reachable: in the corridors measured above 2.33% of
inter-node segments exceed 200 m and the longest is 858 m. Segments are subdivided to at most
SAMPLE_STEP_M, which bounds the error - nothing further than tolerance + SAMPLE_STEP_M/2 can be credited.
"""
from __future__ import annotations

import math
import re

from .curvature import distance_on_earth

DESIGNATED_BONUS = 0.15
ELIGIBLE_BONUS = 0.06
# The plan's per-term allowance. Enforced by a test over every known status, not by a min() that cannot bind.
MAX_BONUS = 0.15
# E is a 0..1 score; the six base terms already sum to 1.00. This is what "capped" governs.
E_CEILING = 1.0

DESIGNATED = "OD"
ELIGIBLE = "E"
KNOWN_STATUS = frozenset({DESIGNATED, ELIGIBLE})

# How close a way has to run to a byway centreline to count as the same road. Byway geometry is digitised
# from route centrelines at a coarser scale than OSM and a divided highway's carriageways are ~30 m apart, so
# this cannot be tight. It does NOT separate a frontage road from a second carriageway - nothing about
# distance can, they occupy the same band - which is what the route key exists for.
SNAP_TOLERANCE_M = 60.0
# A way has to overlap the byway for a real distance, not touch it at a crossing. A cross street meeting a
# byway at a junction shares one node and should not inherit the designation.
MIN_OVERLAP_FRACTION = 0.30
# Longest piece of a way credited or discarded on one sample. Bounds the midpoint error to tolerance + 12.5 m.
SAMPLE_STEP_M = 25.0

# One `;`-separated part of an OSM `ref`: a network prefix and a bare number, nothing after it. `US 101` and
# `I-280` parse; `US 101 Business` deliberately does not.
_REF_PART = re.compile(r"^[A-Za-z]{1,4}\s*-?\s*(\d{1,3})$")


def status_bonus(status: str | None) -> float:
    """The E bonus for a byway status. Unknown or absent statuses score nothing rather than guessing."""
    if status == DESIGNATED:
        return DESIGNATED_BONUS
    if status == ELIGIBLE:
        return ELIGIBLE_BONUS
    return 0.0


def apply_to_e(base_e: float, bonus: float) -> float:
    """E with the byway bonus added, capped. THIS is what the plan's "capped" governs.

    The composition site in T-0029 must go through here. Adding the bonus to a base E of 0.95 without this
    yields 1.10, which is not a score.
    """
    return min(E_CEILING, base_e + bonus)


def unknown_statuses(statuses: list[str | None]) -> set[str]:
    """Statuses outside the known set.

    The field has no published domain, so Caltrans can add a value without telling anyone. If that happens
    every new segment silently scores zero, which reads as "not a byway" rather than "we do not understand
    this data" - so it has to be detectable.
    """
    return {s for s in statuses if s is not None and s not in KNOWN_STATUS}


def route_numbers(ref: str | None) -> set[str]:
    """Route numbers an OSM `ref` claims. `'I 280;CA 35'` -> `{'280', '35'}`, `'US 101 Business'` -> set()."""
    if not ref:
        return set()
    out = set()
    for part in ref.split(";"):
        m = _REF_PART.match(part.strip())
        if m:
            out.add(str(int(m.group(1))))
    return out


def route_matches(entry_routes, way_ref: str | None) -> bool:
    """Whether a way's `ref` lets it be this byway entry's route.

    An entry with no route key (the FHWA layer carries a trail name and no route number) cannot use this
    test, and falls back to geometry alone - a weaker mode, named here so it is not mistaken for the strong
    one. An entry WITH a route key rejects a way that does not name that number, including a way with no
    `ref` at all: measured on the I-280 corridor, every unreffed way clearing the overlap gate was a
    frontage or parallel road, not an I-280 segment.
    """
    if not entry_routes:
        return True
    return bool(set(entry_routes) & route_numbers(way_ref))


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


def _subdivisions(seg_m: float, step_m: float) -> int:
    """How many pieces one OSM segment is sampled in. At least one; never fewer than length/step."""
    if step_m <= 0:
        return 1
    return max(1, math.ceil(seg_m / step_m))


def overlap_fraction(way: list[tuple[float, float]], byway: list[tuple[float, float]],
                     tolerance_m: float = SNAP_TOLERANCE_M, step_m: float = SAMPLE_STEP_M) -> float:
    """Fraction of the way's LENGTH that runs within `tolerance_m` of the byway.

    By length, not by node count. OSM node density varies enormously - a curve is drawn with many nodes and a
    straight is drawn with two - so counting nodes would let a short curly section outvote a long straight
    one and would make the answer depend on how the road was mapped.

    Each OSM segment is cut into pieces of at most `step_m` and each piece is judged on its own midpoint, so
    a long chord that only brushes the byway in the middle is credited for the middle and not for its ends.
    """
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
            if distance_to_line_m(mid, byway) <= tolerance_m:
                near += piece
    return (near / total) if total else 0.0


def match(way: list[tuple[float, float]], byways: list[dict], way_ref: str | None = None,
          tolerance_m: float = SNAP_TOLERANCE_M,
          min_overlap: float = MIN_OVERLAP_FRACTION) -> dict | None:
    """The best byway match for a way, or None.

    Best by STATUS, then by overlap. Both are applied only to entries that have already cleared the overlap
    gate and the route key, so the question at this point is not "is this the same road" - that is settled -
    but "which designation does it carry", and the stronger evidence is the one worth carrying.
    """
    best = None
    best_key = None
    for entry in byways:
        line = entry.get("geometry") or []
        if len(line) < 2:
            continue
        if not route_matches(entry.get("routes"), way_ref):
            continue
        frac = overlap_fraction(way, line, tolerance_m)
        if frac < min_overlap:
            continue
        key = (status_bonus(entry.get("status")), frac)
        if best_key is None or key > best_key:
            best_key = key
            best = {"name": entry.get("name"), "status": entry.get("status"),
                    "source": entry.get("source"), "overlap": frac}
    return best


def bonus_for(way: list[tuple[float, float]], byways: list[dict], **kw) -> float:
    """The E bonus a way earns from byway designation. Add it to E through `apply_to_e`, never bare."""
    m = match(way, byways, **kw)
    return 0.0 if m is None else status_bonus(m["status"])


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
    keyless = sum(1 for b in byways if b.get("source") == "caltrans" and not b.get("routes"))
    if keyless:
        out.append(f"{keyless} Caltrans byway(s) have no route key - RTE is what tells a byway apart from "
                   f"the frontage road beside it, and without it they can only match on distance")
    return out
