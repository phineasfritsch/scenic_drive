"""Two metre quantities `score.score` takes and nothing under `etl/` produced: tunnel metres, and metres
to the nearest motorway.

METRES, NOT MULTIPLIERS. `score.py` already owns both thresholds and both factors - tunnel > 300 m x0.15,
within 150 m of a motorway x0.7 (score.py:61-64, plan:85) - and they are stated there exactly once. This
module answers the two questions those lines ask and knows nothing about what the answers are worth. The
one thing it does assert about them is structural and lives in the tests: the search radius below has to be
comfortably larger than the distance `score` compares against, or the radius would be deciding the
multiplier by silently reporting `inf`.

THE TUNNEL VALUE SET IS AN ALLOWLIST, NOT A TRUTH TEST. `tunnel=no` is a real and common tag - it is how a
mapper records that a way under a building is NOT a tunnel - so `"tunnel" in tags` is wrong, and so is any
truthiness on the value. The accepted values are enumerated in `TUNNEL_VALUES` and pinned against literals
by `tests/test_proximity.py`, which is the only way a set like this stays honest. Two rulings inside it:
  * `culvert` is NOT accepted. On a waterway it means the water runs through a pipe; on a highway it is a
    mistag, and honouring it would take a scenic road down to x0.15 for a drainage pipe under it.
  * `avalanche_protector` IS accepted. A gallery is a roof over the road: the driver cannot see out of it,
    which is the only thing the multiplier is about.
`covered=yes` (arcades, galleries under buildings) is NOT read. It is a different key with a different
meaning and, if it is ever wanted, it is a decision with its own constant and its own test.

THE MOTORWAY SET IS IMPORTED, NEVER RESTATED. `byways.SCENIC_ZERO_CLASSES` is already the four values -
motorway, motorway_link, trunk, trunk_link - and `score.py` imports them from there for the same reason
(score.py:23-27): a copy would drift, both files would stay internally consistent, and the corpus would
carry two answers for one road. The tests pin the imported set against the four literals, so a change to the
meaning of that constant in `byways` fails here instead of silently widening "near a motorway".

HOW THE DISTANCE IS MEASURED, and the wrong way that this exists to rule out. The answer is the minimum
distance between two POLYLINES, not between a way's nodes and a polyline. OSM node density varies
enormously, and the nearest point of an encounter is usually in the middle of a long segment: in the
fixture's `nearest_point_inside_a_long_way_segment` a node-sampling implementation answers 884.90 m where
the true distance is 55.27 m - the difference between x0.7 and no penalty at all. So every segment of the
way is measured against every segment of the motorway, from both ends.

Two segments that cross are at distance 0, and no endpoint-to-segment distance sees that: the same fixture's
crossing pair reads 441.61 m from its four endpoints. The crossing test is therefore separate, and it is
done on the raw (lon, lat) numbers with no earth model at all - the projection to metres multiplies x by
111320*cos(lat) and y by 110540, a diagonal map with a positive determinant, which cannot change the SIGN
of a cross product. Collinear and touching pairs deliberately fall through to the endpoint distances, which
return 0.0 for them anyway.

WHAT IS NOT HERE. No spatial index: every candidate handed in is measured. The caller narrows the candidate
set - the corpus already carries an R-tree over segments - and passing a whole region's motorways to this
would be quadratic. Stated because the cost is the caller's to avoid, not a bound this module enforces.
"""
from __future__ import annotations

import math

from .byways import SCENIC_ZERO_CLASSES
from .sinuosity import require_geometry
from .snap import length_m, point_to_segment_m

# OSM `tunnel=` values that mean the driver is inside something. See the module docstring for the two
# rulings; pinned against literals in tests/test_proximity.py.
TUNNEL_VALUES = frozenset({"yes", "building_passage", "avalanche_protector"})

# The `highway=` values a way has to carry to be one of the things measured against. Imported, not restated.
MOTORWAY_CLASSES = SCENIC_ZERO_CLASSES

# Beyond this, `meters_to_nearest_motorway` reports `math.inf`, which is exactly `score.score`'s default for
# "no motorway near this way" (score.py:122). A REPORTING limit, not a search optimisation: nothing is
# pruned, the value is simply not a fact about this way any more. It has to stay well clear of the 150 m
# `score` compares against - the test asserts that relation rather than the number - and 1 km leaves room
# for a softer distance term later without making this constant load-bearing again.
MOTORWAY_SEARCH_RADIUS_M = 1000.0


def is_tunnel(tags: dict) -> bool:
    """Whether this way's tags put it inside a tunnel. `tunnel=no` and an absent key are both False."""
    value = tags.get("tunnel")
    if not isinstance(value, str):
        return False
    return value.strip().lower() in TUNNEL_VALUES


def tunnel_meters(coords: list[tuple[float, float]], tags: dict) -> float:
    """Metres of this way that are in a tunnel: its whole length, or 0.0.

    `tunnel=` is a way tag, so the answer is all-or-nothing per way - a road that enters a tunnel halfway
    along is two ways in OSM, and if it is not, the metres are wrong in the data and not here. Takes
    coordinates and tags rather than a way record: the record is T-0163's and does not exist yet, and
    guessing its attribute names would be a seam that compiles and does not fit.
    """
    require_geometry(coords, "tunnel_meters")
    return length_m(coords) if is_tunnel(tags) else 0.0


def is_motorway(tags: dict) -> bool:
    """Whether a way is one of the four classes proximity is measured to."""
    return tags.get("highway") in MOTORWAY_CLASSES


def _crosses(a: tuple[float, float], b: tuple[float, float],
             c: tuple[float, float], d: tuple[float, float]) -> bool:
    """Whether segment a-b properly crosses segment c-d, decided on (lon, lat) with no earth model.

    Proper crossing only: both pairs of cross products must have strictly opposite signs. Collinear or
    touching pairs are left to the endpoint distances, which already answer 0.0 for them.
    """
    def side(o, p, q):
        return (p[1] - o[1]) * (q[0] - o[0]) - (p[0] - o[0]) * (q[1] - o[1])

    d1, d2 = side(a, b, c), side(a, b, d)
    d3, d4 = side(c, d, a), side(c, d, b)
    return ((d1 > 0) != (d2 > 0) and d1 != 0 and d2 != 0
            and (d3 > 0) != (d4 > 0) and d3 != 0 and d4 != 0)


def segment_distance_m(a: tuple[float, float], b: tuple[float, float],
                       c: tuple[float, float], d: tuple[float, float]) -> float:
    """Minimum metres between two segments. 0.0 when they cross; otherwise at one of the four endpoints."""
    if _crosses(a, b, c, d):
        return 0.0
    return min(point_to_segment_m(a, c, d), point_to_segment_m(b, c, d),
               point_to_segment_m(c, a, b), point_to_segment_m(d, a, b))


def line_distance_m(line: list[tuple[float, float]], other: list[tuple[float, float]]) -> float:
    """Minimum metres between two polylines, over every pair of their segments."""
    require_geometry(line, "line_distance_m")
    require_geometry(other, "line_distance_m")
    return min(segment_distance_m(a, b, c, d)
               for a, b in zip(line, line[1:])
               for c, d in zip(other, other[1:]))


def meters_to_nearest_motorway(coords: list[tuple[float, float]],
                               motorways: list[list[tuple[float, float]]],
                               radius_m: float = MOTORWAY_SEARCH_RADIUS_M) -> float:
    """Metres from this way's geometry to the nearest of `motorways`, or `math.inf` beyond `radius_m`.

    `motorways` is a list of geometries already selected by the caller - `is_motorway` is here so the
    selection does not restate the four classes either. An empty list is not an error: it is a way with no
    motorway near it, which is `math.inf`. The radius is inclusive, so a motorway at exactly `radius_m`
    still reports its distance.
    """
    require_geometry(coords, "meters_to_nearest_motorway")
    nearest = math.inf
    for i, motorway in enumerate(motorways):
        require_geometry(motorway, f"meters_to_nearest_motorway motorway[{i}]")
        nearest = min(nearest, line_distance_m(coords, motorway))
    return nearest if nearest <= radius_m else math.inf
