"""`speed_fit`: how close a road's driving speed is to 65 km/h, from tags alone.

WHAT THIS PRODUCES. One of the four terms of the plan's drive mean M (plan:86), consumed by
`score.drive_mean(speed_fit=...)` with weight 0.20. The plan's whole specification of it is four words -
"`speed_fit` triangular at 65 km/h" (plan:89) - so everything else here is a ruling recorded in T-0162's
task log, and each ruling is pinned by a named test in `tests/test_speedfit.py`.

THE TRIANGLE. 1.0 at 65 km/h, falling linearly to 0.0 at 25 km/h and at 105 km/h. Symmetric, because with
no further qualification "triangular at 65" means "how far from 65 km/h" and nothing more: a 45 km/h and an
85 km/h road are both 0.5. 65 km/h is the speed at which a road is enjoyable to drive rather than merely
survived - a 30 km/h residential street is a crawl and a 110 km/h expressway is a transit corridor - and the
term deliberately says nothing about whether the road is pretty, which is E's six terms' business.

THIS OUTPUT IS ALREADY 0..1. It is mapped, never region-ranked: unlike photo density or furniture there is no
regional distribution to normalise against, because 65 km/h is an absolute claim about driving and not a
claim about how this road compares with its neighbours. Nothing downstream should rank it.

WHERE THE SPEED COMES FROM, in order: the way's `maxspeed` tag when it parses, otherwise the per-class
default table below. The table is LOCAL TO THIS MODULE on purpose. `services/routing/profiles/` is a
serial-only file another task owns, and the router's speeds answer a different question anyway (how long
will this edge take, which has to include the profile's own penalties); a scenic term that silently changed
because a routing profile was retuned would be the hardest kind of drift to find.

WHAT IS NOT HERE. No geometry, no raster, no container, no I/O, and no import of `tagfilter` - the table has
to stand on its own. `tests/test_speedfit.py` does import `tagfilter`, to require that every `highway` value
the extract keeps has an entry here.
"""
from __future__ import annotations

import math
import re

# plan:89. The apex is the plan's; both feet are T-0162's ruling R1.
APEX_KMH = 65.0
LOWER_FOOT_KMH = 25.0
UPPER_FOOT_KMH = 105.0

# The exact international mile, so `35 mph` is 56.32704 km/h and not a rounded 56.
MPH_TO_KMH = 1.609344

# `maxspeed=walk` is the one non-numeric value that IS a speed statement (R5). Its exact value is not
# load-bearing: every plausible walking pace is below LOWER_FOOT_KMH and therefore scores 0.0.
WALK_PACE_KMH = 5.0

# Present in real data and deliberately left unresolved (R3, R4). Named rather than left to fall through the
# number pattern, so that the decision is an identifier a test can be anchored on. `signals` states that the
# posted number changes, so there is no number to read. `none` is a German-network value; on a California
# way it is a mis-tag, and turning it into a confident 0.0 would fabricate evidence from a tag that carries
# none - where it is genuinely right the way is a motorway, which `score` zeroes on its class regardless.
NO_NUMBER_VALUES = frozenset({"signals", "none"})

# California posted limits, converted from mph and rounded to 5 km/h. One entry per `highway` value the Bay
# Area extract keeps (`tagfilter.WAY_CLASSES`); the test iterates that dict and fails if a value has no
# entry, so a class added to the filter cannot quietly arrive at the fallback below.
DEFAULT_SPEED_KMH: dict[str, float] = {
    "motorway": 105.0,        # 65 mph
    "motorway_link": 60.0,    # a ramp, not the freeway it leaves
    "trunk": 100.0,           # expressway
    "trunk_link": 55.0,
    "primary": 90.0,          # 55 mph
    "primary_link": 50.0,
    "secondary": 70.0,
    "secondary_link": 45.0,
    "tertiary": 60.0,
    "tertiary_link": 40.0,
    "unclassified": 55.0,     # rural two-lane with no posted sign
    "residential": 40.0,      # 25 mph
    "living_street": 20.0,
    "service": 25.0,
    "track": 25.0,
    "road": 50.0,             # OSM: classification unknown
}

# An unrecognised `highway` value gets the same number as `highway=road`, because "a class we do not know"
# and OSM's "classification unknown" are the same epistemic state (R7). A test pins the equality so the two
# cannot drift apart.
UNKNOWN_CLASS_SPEED_KMH = 50.0

# A bare number is km/h; `NN mph` and the redundant `NN km/h` are the two unit suffixes that occur. The
# space is optional and matching is case-insensitive. Everything else - country-implicit (`CA:urban`),
# conditional (`50 @ (22:00-06:00)`), multi-valued (`30;50`) - deliberately does not match (R2): each needs
# a resolver this term does not have, and a confidently wrong number is worse than the class default.
_MAXSPEED = re.compile(r"^(\d+(?:\.\d+)?)\s*(mph|km/h)?$", re.IGNORECASE)


def parse_maxspeed(raw: str | None) -> float | None:
    """The way's `maxspeed` in km/h, or None when the tag states no usable number.

    None is "ask the class default", never "slow": a way whose maxspeed we cannot read is not a way we know
    anything about. Zero and negative numbers are not speeds and return None too.
    """
    if raw is None:
        return None
    text = raw.strip().lower()
    if not text or text in NO_NUMBER_VALUES:
        return None
    if text == "walk":
        return WALK_PACE_KMH
    match = _MAXSPEED.match(text)
    if match is None:
        return None
    value = float(match.group(1))
    if not math.isfinite(value) or value <= 0.0:
        return None
    if match.group(2) == "mph":
        value *= MPH_TO_KMH
    return value


def default_speed_kmh(highway: str | None) -> float | None:
    """The table's speed for a `highway` class, or None if the class is not in the table.

    Returns None rather than the fallback so a caller that wants to know the difference can see it;
    `speed_kmh_for_tags` is the one that always produces a number.
    """
    return DEFAULT_SPEED_KMH.get(highway) if highway is not None else None


def speed_kmh_for_tags(*, highway: str | None, maxspeed: str | None = None) -> float:
    """The driving speed this way is scored on: the parsed tag, else the class default, else the fallback."""
    parsed = parse_maxspeed(maxspeed)
    if parsed is not None:
        return parsed
    default = default_speed_kmh(highway)
    return UNKNOWN_CLASS_SPEED_KMH if default is None else default


def speed_fit(speed_kmh: float) -> float:
    """The plan's triangle (plan:89), in 0..1. 1.0 at the apex, 0.0 at or beyond either foot.

    A non-finite speed scores 0.0. Infinity is genuinely above the upper foot; NaN cannot be placed on the
    triangle at all, and 0.0 is the answer whose error direction is "less scenic", which is the direction
    every other unresolvable case here already fails in.
    """
    if not math.isfinite(speed_kmh):
        return 0.0
    if speed_kmh <= LOWER_FOOT_KMH or speed_kmh >= UPPER_FOOT_KMH:
        return 0.0
    if speed_kmh <= APEX_KMH:
        return (speed_kmh - LOWER_FOOT_KMH) / (APEX_KMH - LOWER_FOOT_KMH)
    return (UPPER_FOOT_KMH - speed_kmh) / (UPPER_FOOT_KMH - APEX_KMH)


def speed_fit_for_tags(*, highway: str | None, maxspeed: str | None = None) -> float:
    """`score.drive_mean`'s `speed_fit` keyword for one way, from its tags alone.

    Always a float in 0..1: `score.out_of_range` (score.py:95) turns a missing term into a whole-row
    failure, so "no opinion" is not an option this far down the pipeline.
    """
    return speed_fit(speed_kmh_for_tags(highway=highway, maxspeed=maxspeed))
