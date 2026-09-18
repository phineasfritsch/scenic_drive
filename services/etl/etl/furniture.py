"""Street furniture per kilometre: the RAW count of the nodes that make a road feel urban.

WHAT THIS PRODUCES, AND WHAT IT DOES NOT. `score.scenery_mean` takes `furniture` in 0..1 and enters it
inverted, `0.12 * (1 - furniture)` (score.py:92, plan:87). This module emits neither a 0..1 value nor the
inversion: it emits an unbounded count per kilometre. The region rank-normaliser (T-0163) is the step
between, and it has to be, because "a lot of furniture" is a statement about this region's roads - twelve
lit crossings per kilometre is ordinary in San Francisco and extraordinary on Skyline. Normalising here
would either need a constant nobody can defend or quietly bake one region's distribution into every region.
So: no clamping, no scaling, no inversion, no `1 -` anywhere in this file.

WHY NODES AT ALL. Signals, stop signs, crossings, calming and bollards exist only at a point on the
carriageway, so they are nodes of the way, and they are the one piece of urbanness available from tags with
no raster and no land-use polygon. A road with a traffic signal every 200 m is a city street whatever the
canopy over it looks like.

WHAT IS COUNTED is the named set below and nothing else. WHAT IS DELIBERATELY NOT COUNTED, with the reason:

  * `barrier=gate`, `barrier=lift_gate`, `barrier=cycle_barrier` - access furniture, not urbanness. A locked
    gate is already a SAFETY gate in the routing profile (plan:81), and counting it here would penalise one
    rural tag twice, in two different terms, in opposite directions.
  * `highway=turning_circle`, `highway=passing_place`, `highway=mini_roundabout` - the geometry of narrow and
    rural roads. A passing place is evidence of the opposite of urban.
  * `highway=bus_stop`, `amenity=*`, `shop=*` - roadside land use, which is what `impervious` (score.py:89)
    and `points_of_interest` (score.py:91) are for. The same evidence must not enter E twice with two
    different signs.
  * `railway=level_crossing` - rural rail crossings are common and say nothing about a road being urban.

THE ONE KNOWN UNDERCOUNT, stated rather than discovered later: `highway=street_lamp`. A lamp mapped as a
separate node beside the carriageway - which many are - is not a node of the way, so it is not in this
function's input and, since the extract's filter keeps a way's referenced nodes and not its neighbours, not
in the extract either. Lamps that ARE way nodes count. The signal is kept in spite of this because lit
streets are the strongest "feels urban" evidence tags carry, and an undercount whose direction is uniform
still orders rows correctly once the region normaliser ranks them; dropping the tag loses the signal
outright. T-0162's log, R14/R15, records what a filter change would cost and which count it would move.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

# Accepted by key AND value. Each of these is a fixed value, so the set is enumerated and pinned by test.
FURNITURE_VALUES: dict[str, frozenset[str]] = {
    "highway": frozenset({"crossing", "stop", "street_lamp", "traffic_signals"}),
    "barrier": frozenset({"bollard"}),
}

# Accepted by key, WHATEVER the value (the Brief's `traffic_calming=*`). Enumerating the values would be
# worse than this: the wiki's list grows - table, hump, cushion, bump, chicane, rumble_strip and more - and
# an enumeration here would silently file each new type as "not urban". Every value of this key is calming.
FURNITURE_KEYS_ANY_VALUE = frozenset({"traffic_calming"})

# ...with one exception: OSM uses `=no` on these keys to state that a junction explicitly has NONE. It is
# the one value of an any-value key that means the opposite of the key.
ANY_VALUE_EXCEPTIONS = frozenset({"no"})

METRES_PER_KM = 1000.0


def is_furniture(tags: Mapping[str, str]) -> bool:
    """Whether one node's tags make it street furniture.

    Values are matched exactly, without case folding: OSM tag values are lowercase by convention and
    nothing between the extract and here rewrites them, so folding would only hide a mis-tagged value.
    """
    for key, values in FURNITURE_VALUES.items():
        if tags.get(key) in values:
            return True
    for key in FURNITURE_KEYS_ANY_VALUE:
        value = tags.get(key)
        if value and value not in ANY_VALUE_EXCEPTIONS:
            return True
    return False


def furniture_count(nodes: Iterable[Mapping[str, str]]) -> int:
    """How many of these nodes are street furniture.

    The unit counted is the NODE, not the matching tag. A raised crossing carries `highway=crossing` and
    `traffic_calming=table` on one node and counts once: adding up per-key matches would double-count
    precisely the most urban nodes, and the resulting rate would be a number with no unit.
    """
    return sum(1 for tags in nodes if is_furniture(tags))


def furniture_per_km(*, nodes: Iterable[Mapping[str, str]], length_m: float) -> float | None:
    """The raw rate for one way, or None when its length cannot carry a rate.

    Unbounded on purpose - see the module docstring; T-0163 ranks it and `score` inverts it after that.

    A length that is zero, negative or not finite returns None, never 0.0. Zero would state "this way is
    rural", which is a claim about a way that does not exist; None is "no opinion", and what a missing raw
    value does to a regional rank is the normaliser's decision, not this module's.
    """
    if not math.isfinite(length_m) or length_m <= 0.0:
        return None
    return furniture_count(nodes) / (length_m / METRES_PER_KM)
