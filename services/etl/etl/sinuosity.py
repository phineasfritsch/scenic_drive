"""Raw sinuosity of one way: the path it travels over the straight line between its two ends.

WHAT THIS IS THE SEAM FOR. `score.drive_mean` takes `sinuosity` already normalised to 0..1 and weights it
0.15 (score.py:48). This module produces the RAW ratio, >= 1.0 and unbounded above, because the mapping to
0..1 is a RANK inside a region - the 90th-percentile way in the Bay Area is not the 90th-percentile way in
Kansas - and a module that saw one way could only ever normalise against a constant it invented. The region
rank-normaliser is T-0163. Nothing here clamps, caps or rescales.

ONE EARTH MODEL, BOTH HALVES OF THE RATIO. Numerator and denominator are both `snap.length_m`, which is
`curvature.distance_on_earth` (spherical, R = 6373000). That is not an aesthetic choice: a ratio whose two
halves came from two models would drift with latitude and would read as curvature. `snap.length_m([first,
last])` is the same call as the numerator's segments, so a two-node way returns exactly 1.0 rather than
1.0000000x, and a test can assert that without a tolerance.

THE CLOSED WAY IS ITS OWN ANSWER, NOT A DIVISION. A loop's endpoints are one point, so the ratio is a
division by zero; a way that nearly closes - a lasso, a cul-de-sac drawn out and back, the two arms of a
junction that were not snapped together - has a denominator of a few metres and a ratio in the HUNDREDS
(the fixture's `near_closed_lasso` is 4.2 km of path over a 5.03 m gap). That number is not a measurement of
anything: it is an artefact of where the digitiser stopped. Fed to a rank-normaliser it would take the top
of the region's range and push every genuinely sinuous road down, so the guard is what protects the term
rather than a nicety. `CLOSED_WAY_SINUOSITY` is the FLOOR, 1.0: a closed way is credited nothing here, and
its curviness is carried by `curvature.way_curvature`, which weighs 0.45 to this term's 0.15 and measures a
loop perfectly well. Declining to answer is 1.0, never `inf` and never a large number.

REFUSAL. Fewer than two coordinates is not a way and gets no value: `way_sinuosity` raises `ValueError`
naming the caller and the count. A default returned for malformed geometry is the failure this repository
exists to catch - it would score, it would look plausible, and nothing would ever print it.
"""
from __future__ import annotations

from .snap import length_m

# The floor of the raw scale, and the answer for a way whose two ends are the same place. 1.0 means "as
# straight as a way can be", which is a deliberate under-claim: see the docstring.
CLOSED_WAY_SINUOSITY = 1.0

# How near the two ends have to be to count as the same place. This is the width of a road junction, not a
# tolerance on the arithmetic: the case being caught is two end nodes that OSM did not snap together, or a
# loop drawn with a short stub, both of which sit within a few metres. Absolute metres rather than a
# fraction of the way's length, so the rule reads the same for a 40 m cul-de-sac and a 40 km loop.
CLOSED_ENDPOINT_M = 10.0

MIN_COORDINATES = 2


def require_geometry(coords: list[tuple[float, float]], caller: str) -> None:
    """Refuse a way that is not a line. `proximity` imports this rather than restating the message.

    Two modules with two spellings of one refusal is the drift this repository keeps catching: the message
    is what a log search finds, so there is exactly one of it.
    """
    n = len(coords)
    if n < MIN_COORDINATES:
        raise ValueError(f"{caller}: needs at least {MIN_COORDINATES} coordinates, got {n}")


def endpoint_gap_m(coords: list[tuple[float, float]]) -> float:
    """Metres between the way's first and last coordinate, on `snap`'s spherical model."""
    require_geometry(coords, "endpoint_gap_m")
    return length_m([coords[0], coords[-1]])


def is_closed_way(coords: list[tuple[float, float]]) -> bool:
    """Whether the way's two ends are the same place - exactly, or within `CLOSED_ENDPOINT_M`."""
    return endpoint_gap_m(coords) <= CLOSED_ENDPOINT_M


def way_sinuosity(coords: list[tuple[float, float]]) -> float:
    """Path length over end-to-end distance: 1.0 for a straight way, unbounded above, never below 1.0.

    `CLOSED_WAY_SINUOSITY` for a closed or nearly closed way. Named `way_sinuosity` to match
    `curvature.way_curvature`, the other per-way geometry term `score.drive_mean` consumes.
    """
    require_geometry(coords, "way_sinuosity")
    gap = endpoint_gap_m(coords)
    if gap <= CLOSED_ENDPOINT_M:
        return CLOSED_WAY_SINUOSITY
    return length_m(coords) / gap
