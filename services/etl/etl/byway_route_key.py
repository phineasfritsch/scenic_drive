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
    carry `ref=CA 236`. Two Overpass pulls six weeks of OSM apart and from different mirrors, both put
    through THIS repo's `snap`, agree on what that costs: 141 ways clear the overlap gate either time,
    53.46 km of way clears it, and 28.14 km of it is `ref=CA 236` Big Basin Way discarded because the key
    matches 0.00 km either time. The one thing that differs between the pulls is how many ways are in range
    at all - 302 and 306 within 150 m. (Pull a is `around:150`; pull b is a padded-bbox query, a superset,
    with the 150 m test applied locally. `tests/fixtures/byway_miskey_fixture.json` carries both pulls'
    provenance and pull b's full census.)
    AN EARLIER VERSION OF THIS PARAGRAPH RAN THAT AS A TWO-COLUMN TABLE - 141/142, 53.46/53.54,
    28.14/28.07, 28143/28074, 197/196 - and called it two independent pulls agreeing to a rounding. It is
    not. Every one of those pairs is `snap.distance_on_earth` against a hand-rolled flat-earth segment
    length in the scratch script that measured the census: THE INSTRUMENT, NOT THE DATA. Run either kernel
    over either pull and the numbers are identical to the digit. A second measurement that was never a
    second measurement is exactly the kind of corroboration this module exists to refuse, and it survived
    three rounds here because the test asserting the census asserted census fields against census fields
    and never ran the code.
  It is not one row. Cross-checking each row's `RTE`/`CO` against its own `DYNSEGPM` string ("<CO> <RTE>
    <PM> / ...") finds 5 rows disagreeing on RTE - FID 14 (5 vs 7), 19 (10 vs 5), 44 (29 vs 28), 52 (36 vs
    35) and 265 (680 vs 580, an OD Bay Area row) - plus FID 233, whose DYNSEGPM omits the route number
    altogether ('SON 0.00 / SON 27.817'). Five more disagree on CO - FID 92, 178, 180 (RIV vs NAP, the Napa
    221 row), 197, 200 - and FID 226 differs only as an abbreviation (AM vs AMA). FID 181 is in NEITHER
    list, because both of its fields carry the same wrong number, so ~2% is the floor on DETECTABLE
    corruption rather than the rate.
    WHICH field is wrong is not decidable from the disagreement, and guessing it backwards is easy: on
    FID 265 it is the DYNSEGPM. Its line is a 7.38 km north-south by 3.42 km east-west strip from Bernal
    Ave to the Contra Costa line, which is I-680 - so `RTE=680` is right and `ALA 580 ...` is wrong. That
    row is also the cheapest proof that the corroboration floor above is not theoretical: Caltrans's own
    RTE=580 row (FID 199) touches FID 265's line at 0.0 m, so had 265 been keyed 580 instead, real
    correctly-tagged I-580 ways at the crossing would have corroborated the wrong key.

THE REPAIR, AND WHY IT IS NOT "FALL BACK TO GEOMETRY". Dropping the key for a row nothing claims is the
obvious fix and it is wrong. Of the 53.46 km clearing the gate along FID 181 only 28.14 km is Big Basin
Way. The other 25.32 km, by OSM highway class: 13.46 km path (the Skyline-to-the-Sea Trail and the park's
trail network), 5.35 km residential (Boulder Creek's grid - Acorn Drive, Fallen Leaf Drive, Saint Francis
Drive), 5.04 km service (campground and park service roads), 0.59 km track, 0.35 km footway, 0.20 km
primary, 0.18 km pedestrian, 0.09 km unclassified, 0.04 km passing_place, 0.01 km steps. Geometry alone
would hand an eligible byway's bonus to a footpath and to a cul-de-sac.

What the corridor does say is which number it actually is. Along FID 181 the ways that carry a `ref` claim
`236` for 27569 m of running along the line and `9` for 126 m: 99.5% consensus on one number, and it is not
the row's key. So:
  CORROBORATED - the key holds evidence of its own and no other number outvotes it past the bar the re-key
    branch has to clear. Nothing changes and nothing is reported. This is the normal case and the one the
    frontage-road evidence above was measured on.
  REKEYED      - the key holds less than MIN_CONSENSUS_M, and another number holds more than the key, at
    least MIN_CONSENSUS_M, and at least MIN_CONSENSUS_SHARE of the reffed length along the corridor. The
    entry is re-keyed to that number - or to both, when a concurrency carries two of them past the bar -
    and reported. The corridor is still gated on a route number, so the footpaths stay out.
  CONTESTED    - the key holds at least MIN_CONSENSUS_M and another number STILL clears that bar over it.
    Two numbers with a real case each: the key stays and the entry is reported, because choosing between
    them on this evidence would be a guess.
  UNCLAIMED    - nothing claims the key and no number reaches the bar. The key STAYS (guessing is worse
    than scoring zero) and the entry is reported, because a corridor that can match nothing is a fact
    somebody has to see.
Every verdict except CORROBORATED is a line in `byways.problems`, and so is an entry that was never put
through `reconcile` at all: "no problems" must not be reachable by never looking, which is the exact way
the keyless check managed to be green while FID 181 lost 28 km.

ONE FLOOR, BOTH DIRECTIONS. An earlier version put MIN_CONSENSUS_M and MIN_CONSENSUS_SHARE on the re-key
branch ONLY and decided CORROBORATED on a bare membership test, `if key & set(claimed)`. That made the
failure above reachable through the very check that closes it: CHANGING the source's number needed a
kilometre of agreement, while KEEPING it and telling nobody needed 23 metres. Measured on FID 181's own
corridor and its own OSM ways, one 23.2 m way mis-tagged `ref=CA 221` and one 21.0 m way on the other part
- 44.2 m in total - turned 27.9 km of eligible byway back into a silent total loss, with `problems()`
saying nothing about it. It does not take an OSM error to reach, either: grid-hashing every Caltrans
centreline at the 60 m snap tolerance, 265 of the 865 entries (30.6%) have ANOTHER numbered state route
inside their own snap band, so for those a mis-key onto the neighbouring number is corroborated by that
neighbour's real, correctly tagged ways - and neighbouring numbers are exactly what the DYNSEGPM
disagreements above look like (5 vs 7, 10 vs 5, 29 vs 28, 36 vs 35, 680 vs 580). One threshold therefore
governs both branches: MIN_CONSENSUS_M is what it takes to say ANYTHING about a corridor, so a number
holding less than it can neither establish a key nor defend one.

WHAT A WAY VOTES WITH: its length ALONG THE CORRIDOR, never its whole length. A way is admitted at 30%
overlap, so up to 70% of it is somewhere else, and counting the whole thing lets the somewhere-else part
vote - by up to 3.3x. On this fixture, way 824667001 `ref=CA 9` overlaps FID 181 by 0.465 and was voting
133.3 m of CA 9 when only 62.0 m of it runs along the corridor. Over the whole 28 km corridor the
difference is 2% (236: 28143 m whole against 27569 m along, 9: 197 against 126), which is exactly what made
it latent - on a SHORT corridor the same inflation clears MIN_CONSENSUS_M on evidence that is not there: a
410 m slice of this corridor's own geometry was re-keyed on 1652.7 m of "consensus" from a way that runs
525.9 m along it. The denominator is the same quantity, summed over reffed ways with each WAY counted once
rather than once per number it names, so a concurrency no longer halves every share by voting twice into
its own denominator - which is what used to make MIN_CONSENSUS_SHARE unreachable, not just unmet, for a
corridor tagged `ref='CA 1;CA 35'` end to end.

COST. `reconcile` is O(entries x reffed ways x way_length/SAMPLE_STEP_M) with only a bounding-box reject to
save it. That is fine for the 865 Caltrans entries against a region's reffed ways and is not fine against
every way in a corpus; T-0030 should hand it the reffed ways only, which is all `_claims` reads.
"""
from __future__ import annotations

import math

from . import byways as bw
from . import snap

# Share of the REFFED length along a corridor that one route number has to hold before it outvotes the key.
# FID 181's corridor gives 99.5% to `236`; a corridor that cannot agree that strongly is not telling us
# anything and keeps the key it has.
MIN_CONSENSUS_SHARE = 0.80
# What it takes to say anything at all about a corridor, so a 60 m reffed stub at a junction can neither
# re-key 28 km of corridor nor - the round-3 blocker - corroborate a wrong key into silence. Both branches
# read it: a number under this floor can neither establish a key nor defend one.
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


def _claims(entry: dict, ways: list[dict], tolerance_m: float = snap.SNAP_TOLERANCE_M,
            min_overlap: float = snap.MIN_OVERLAP_FRACTION) -> tuple[dict[str, float], float]:
    """`(metres along this corridor by route number, metres of reffed way along this corridor)`.

    Only ways clearing the same overlap gate `byways.match` uses are counted, and only ways that name a
    route: an unreffed way says nothing about which number the corridor is, which is the whole reason
    geometry alone cannot repair a wrong key.

    Both numbers are the length running ALONG the corridor, never the way's whole length - see the module
    docstring. The second is the denominator of every share below and counts each WAY once, however many
    numbers its `ref` names, so a concurrency cannot deflate its own share by voting twice.
    """
    line = entry.get("geometry") or []
    if len(line) < 2:
        return {}, 0.0
    box = _padded(line, tolerance_m)
    out: dict[str, float] = {}
    reffed_m = 0.0
    for way in ways:
        numbers = bw.route_numbers(way.get("ref"))
        if not numbers:
            continue
        geom = way.get("geometry") or []
        if len(geom) < 2 or _disjoint(box, _bounds(geom)):
            continue
        along, whole = snap.overlap_m(geom, line, tolerance_m)
        if whole <= 0 or along / whole < min_overlap:
            continue
        reffed_m += along
        for number in numbers:
            out[number] = out.get(number, 0.0) + along
    return out, reffed_m


def claimed_lengths(entry: dict, ways: list[dict], **kw) -> dict[str, float]:
    """Metres of REFFED way, by route number, running along this entry's corridor."""
    return _claims(entry, ways, **kw)[0]


def _outvoting(claimed: dict[str, float], reffed_m: float, key: set[str], key_m: float) -> set[str]:
    """The numbers that beat the key on this corridor's own evidence.

    Not simply the largest: to outvote a key a number has to hold MORE than the key does, at least
    MIN_CONSENSUS_M, and at least MIN_CONSENSUS_SHARE of the reffed length along the corridor. Two numbers
    can clear that together only by being tagged on the same ways, which is a concurrency and is the truth
    about that corridor, so both are returned rather than one of them being picked arbitrarily.
    """
    return {n for n, m in claimed.items()
            if n not in key and m > key_m and m >= MIN_CONSENSUS_M and m >= MIN_CONSENSUS_SHARE * reffed_m}


def corridor_verdict(entry: dict, ways: list[dict], **kw) -> tuple[str, set[str], dict[str, float]]:
    """`(verdict, the routes to use, the metres each number claims)` for one entry.

    The verdicts are `byways.KEY_*`; see this module's docstring for what each one means, why UNCLAIMED
    keeps the key instead of falling back to geometry, and why CORROBORATED has to clear the same floor the
    re-key branch does rather than being decided on a bare membership test.
    """
    key = {str(r) for r in (entry.get("routes") or ())}
    if not key:
        return bw.KEY_UNKEYED, set(), {}
    claimed, reffed_m = _claims(entry, ways, **kw)
    key_m = sum(claimed.get(n, 0.0) for n in key)
    outvoting = _outvoting(claimed, reffed_m, key, key_m)
    if not outvoting:
        return (bw.KEY_CORROBORATED if key_m > 0 else bw.KEY_UNCLAIMED), key, claimed
    if key_m < MIN_CONSENSUS_M:
        return bw.KEY_REKEYED, outvoting, claimed
    return bw.KEY_CONTESTED, key, claimed


def reconcile(entries: list[dict], ways: list[dict], **kw) -> list[dict]:
    """Every entry with its route key checked against the ways lying along it.

    Returns NEW entries - the input is not mutated - each carrying `byways.KEY_VERDICT`. A re-keyed entry
    also carries `key_was` (what Caltrans said) and `key_evidence_m` (the metres that outvoted it), and any
    entry whose key was outvoted carries `key_claim_m` (what the key itself held), so the repair - and the
    fragment that nearly bought the wrong key its silence - is auditable from the entry rather than only
    from a log line.
    """
    out = []
    for entry in entries:
        verdict, routes, claimed = corridor_verdict(entry, ways, **kw)
        fixed = dict(entry)
        fixed[bw.KEY_VERDICT] = verdict
        if verdict in (bw.KEY_REKEYED, bw.KEY_CONTESTED):
            key = {str(r) for r in (entry.get("routes") or ())}
            fixed["key_claim_m"] = round(sum(claimed.get(n, 0.0) for n in key), 1)
            fixed["key_evidence_m"] = round(min(claimed[n] for n in routes) if verdict == bw.KEY_REKEYED
                                            else max(claimed[n] for n in claimed if n not in key), 1)
        if verdict == bw.KEY_REKEYED:
            fixed["key_was"] = sorted(entry.get("routes") or ())
            fixed["routes"] = routes
        out.append(fixed)
    return out
