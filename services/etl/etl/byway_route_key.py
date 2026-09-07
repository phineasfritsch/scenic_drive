"""The Caltrans route key: why it exists, how the source gets it wrong, and what to do about that.

WHY A ROUTE KEY AT ALL. Distance cannot separate a byway from the road beside it. Measured on real OSM
geometry: I-280's two carriageways sit 25.2-30.5 m apart (median 27.7) while Junipero Serra Boulevard, the
frontage road, sits 29.3-97.1 m from the Caltrans SM-280 line (median 52.0). Those bands OVERLAP, so no
value of `byways.SNAP_TOLERANCE_M` admits every second carriageway and excludes every frontage road -
`test_a_frontage_road_is_no_further_off_than_a_second_carriageway` asserts that overlap so it stays a check
rather than a paragraph.

What separates them is the route number. A Caltrans row is a postmiled segment OF A NUMBERED STATE ROUTE
(`RTE`), so a way that does not claim that number is not that road whatever it runs beside. Measured over
three real corridors, 7.84 km of gate-clearing way was rejected and none of it was a genuine byway segment:
  I-280 vs Caltrans SM RTE=280 - 180 ways clear the 30% gate (82.70 km); the key rejects 6.70 km, every one
    of them Junipero Serra Boulevard or Skyline Boulevard.
  CA-35 vs Caltrans SM RTE=35 - 35 ways clear (40.00 km); it rejects 1.14 km, one `ref=I 280` way.
  US-101 vs Caltrans MRN RTE=101 - 18 ways clear (6.37 km), all `ref=US 101`; it rejects nothing.
Matching the NUMBER and not the prefix is not a shortcut: Caltrans numbers Interstate, US and state routes
in ONE namespace, which is why `RTE` is a bare number, so inside California the number identifies the route.
Outside California it does not, and nothing here knows that yet - `35` is a different road in every state.

WHY THAT IS NOT ENOUGH. `RTE` is wrong often enough to matter, and a wrong key is a SILENT TOTAL LOSS: the
row still HAS a key, so the keyless check in `byways.problems` never fires, and every way along the corridor
is rejected instead of one frontage road. Measured in the pinned pull:
  FID 181 - `CO=SCR RTE=221 Status=E`, `DYNSEGPM 'SCR 221 0.00 / SCR 221 17.70'`, LOCATION 'SR 9 Nr Bldr Ck
    to SR 9 NE of Big Basin SP', 2 parts, 1139 vertices, 27.90 km. That is STATE ROUTE 236, Big Basin Way,
    through Big Basin Redwoods State Park. There is no RTE=236 row anywhere in the 273; SR 221 is a 2.7-mile
    Napa freeway and the layer's other 221 row (FID 180) is exactly that; and the OSM ways under the line
    carry `ref=CA 236`. TWO INDEPENDENT OVERPASS PULLS, six weeks of OSM apart and from different mirrors,
    agree on what that costs: 303/306 real highway ways within 150 m of the corridor, 141/142 of them
    clearing the overlap gate, and 28.14/28.07 km of `ref=CA 236` Big Basin Way discarded because the key
    matches 0.00 km either time. (The second pull is a padded-bbox query - a superset of `around:150` - with
    the 150 m test applied locally; `tests/fixtures/byway_miskey_fixture.json` carries both pulls'
    provenance and the second one's full census.)
  It is not one row. Cross-checking each row's `RTE`/`CO` against its own `DYNSEGPM` string ("<CO> <RTE>
    <PM> / ...") finds 5 rows disagreeing on RTE - FID 14 (5 vs 7), 19 (10 vs 5), 44 (29 vs 28), 52 (36 vs
    35) and 265 (680 vs 580, an OD Bay Area row) - plus FID 233, whose DYNSEGPM omits the route number
    altogether ('SON 0.00 / SON 27.817'). Five more disagree on CO - FID 92, 178, 180 (RIV vs NAP, the Napa
    221 row), 197, 200 - and FID 226 differs only as an abbreviation (AM vs AMA). FID 181 is in NEITHER
    list, because both of its fields carry the same wrong number, so ~2% is the floor on DETECTABLE
    corruption rather than the rate.

THE REPAIR, AND WHY IT IS NOT "FALL BACK TO GEOMETRY". Dropping the key for a row nothing claims is the
obvious fix and it is wrong. Of the 53.46/53.54 km clearing the gate along FID 181 only 28.14/28.07 km is
Big Basin Way. The other ~25.4 km, by OSM highway class on the second pull: 13.43 km path (the
Skyline-to-the-Sea Trail and the park's trail network), 5.55 km residential (Boulder Creek's grid - Acorn
Drive, Fallen Leaf Drive, Saint Francis Drive), 5.03 km service (campground and park service roads), 0.59 km
track, 0.35 km footway, 0.18 km pedestrian, 0.09 km unclassified, 0.01 km steps. Geometry alone would hand
an eligible byway's bonus to a footpath and to a cul-de-sac.

What the corridor does say is which number it actually is. Along FID 181 the ways that carry a `ref` claim
`236` for 28143/28074 m and `9` for 197/196 m: 99.3% consensus on one number, and it is not the row's key.
So:
  CORROBORATED - some gate-clearing way claims the key. Nothing changes. This is the normal case and the
    one the frontage-road evidence above was measured on.
  REKEYED      - NO way claims the key, and one other number holds at least MIN_CONSENSUS_SHARE of the
    reffed length along the corridor and at least MIN_CONSENSUS_M of it. The entry is re-keyed to that
    number and reported. The corridor is still gated on a route number, so the footpaths stay out.
  UNCLAIMED    - nothing claims the key and the corridor does not agree on a replacement. The key STAYS
    (guessing is worse than scoring zero) and the entry is reported, because a corridor that can match
    nothing is a fact somebody has to see.
Every verdict except CORROBORATED is a line in `byways.problems`, and so is an entry that was never put
through `reconcile` at all: "no problems" must not be reachable by never looking, which is the exact way
the keyless check managed to be green while FID 181 lost 28 km.

COST. `reconcile` is O(entries x reffed ways x way_length/SAMPLE_STEP_M) with only a bounding-box reject to
save it. That is fine for the 865 Caltrans entries against a region's reffed ways and is not fine against
every way in a corpus; T-0030 should hand it the reffed ways only, which is all `claimed_lengths` reads.
"""
from __future__ import annotations

import math

from . import byways as bw
from . import snap

# Share of the REFFED length along a corridor that one route number has to hold before it may replace a key
# nothing claims. FID 181's corridor gives 99.3% to `236`; a corridor that cannot agree that strongly is not
# telling us anything and keeps the key it has.
MIN_CONSENSUS_SHARE = 0.80
# An absolute floor as well, so a 60 m reffed stub at a junction cannot re-key 28 km of corridor.
MIN_CONSENSUS_M = 1000.0

_M_PER_DEG_LAT = 110540.0
_M_PER_DEG_LON = 111320.0


def _bounds(line: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lats = [p[0] for p in line]
    lons = [p[1] for p in line]
    return min(lats), max(lats), min(lons), max(lons)


def _padded(line: list[tuple[float, float]], pad_m: float) -> tuple[float, float, float, float]:
    lo_lat, hi_lat, lo_lon, hi_lon = _bounds(line)
    d_lat = pad_m / _M_PER_DEG_LAT
    cos_lat = max(0.05, math.cos(math.radians((lo_lat + hi_lat) / 2)))
    d_lon = pad_m / (_M_PER_DEG_LON * cos_lat)
    return lo_lat - d_lat, hi_lat + d_lat, lo_lon - d_lon, hi_lon + d_lon


def _disjoint(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    """Whether two lat/lon boxes miss each other entirely.

    A safe reject: a polyline lies inside its own box, so if the boxes are disjoint every point of one way
    is outside the other's padded box and therefore further than the pad from the other line.
    """
    return a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2]


def claimed_lengths(entry: dict, ways: list[dict], tolerance_m: float = snap.SNAP_TOLERANCE_M,
                    min_overlap: float = snap.MIN_OVERLAP_FRACTION) -> dict[str, float]:
    """Metres of REFFED way, by route number, running along this entry's corridor.

    Only ways clearing the same overlap gate `byways.match` uses are counted, and only ways that name a
    route: an unreffed way says nothing about which number the corridor is, which is the whole reason
    geometry alone cannot repair a wrong key.
    """
    line = entry.get("geometry") or []
    if len(line) < 2:
        return {}
    box = _padded(line, tolerance_m)
    out: dict[str, float] = {}
    for way in ways:
        numbers = bw.route_numbers(way.get("ref"))
        if not numbers:
            continue
        geom = way.get("geometry") or []
        if len(geom) < 2 or _disjoint(box, _bounds(geom)):
            continue
        if snap.overlap_fraction(geom, line, tolerance_m) < min_overlap:
            continue
        metres = snap.length_m(geom)
        for number in numbers:
            out[number] = out.get(number, 0.0) + metres
    return out


def corridor_verdict(entry: dict, ways: list[dict], **kw) -> tuple[str, set[str], dict[str, float]]:
    """`(verdict, the routes to use, the metres each number claims)` for one entry.

    The verdicts are `byways.KEY_*`; see this module's docstring for what each one means and why UNCLAIMED
    keeps the key instead of falling back to geometry.
    """
    key = {str(r) for r in (entry.get("routes") or ())}
    if not key:
        return bw.KEY_UNKEYED, set(), {}
    claimed = claimed_lengths(entry, ways, **kw)
    if key & set(claimed):
        return bw.KEY_CORROBORATED, key, claimed
    total = sum(claimed.values())
    if total > 0:
        number, metres = max(claimed.items(), key=lambda kv: kv[1])
        if metres >= MIN_CONSENSUS_M and metres / total >= MIN_CONSENSUS_SHARE:
            return bw.KEY_REKEYED, {number}, claimed
    return bw.KEY_UNCLAIMED, key, claimed


def reconcile(entries: list[dict], ways: list[dict], **kw) -> list[dict]:
    """Every entry with its route key checked against the ways lying along it.

    Returns NEW entries - the input is not mutated - each carrying `byways.KEY_VERDICT`. A re-keyed entry
    also carries `key_was` (what Caltrans said) and `key_evidence_m` (the metres that outvoted it), so the
    repair is auditable from the entry rather than only from a log line.
    """
    out = []
    for entry in entries:
        verdict, routes, claimed = corridor_verdict(entry, ways, **kw)
        fixed = dict(entry)
        fixed[bw.KEY_VERDICT] = verdict
        if verdict == bw.KEY_REKEYED:
            fixed["key_was"] = sorted(entry.get("routes") or ())
            fixed["routes"] = routes
            fixed["key_evidence_m"] = round(max(claimed.values()), 1)
        out.append(fixed)
    return out
